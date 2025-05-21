import os
import uuid
import logging
import json
import asyncio
import aiofiles
from typing import List, Dict, Any, Optional, Union
from datetime import datetime
from tempfile import NamedTemporaryFile
from uuid import UUID

import pandas as pd
from PyPDF2 import PdfReader
from fastapi import UploadFile, HTTPException, status
from azure.storage.blob.aio import BlobServiceClient, ContainerClient, BlobClient
from azure.storage.blob import ContentSettings
from azure.cosmos.aio import CosmosClient, DatabaseProxy, ContainerProxy
from azure.cosmos import PartitionKey, exceptions
from azure.core.exceptions import ResourceExistsError

from ..models.objective_data import (
    KPI, 
    KPICreate, 
    DataSet, 
    DataSetCreate, 
    DataPoint, 
    DataPointCreate,
    DataCategory,
    DataSourceType
)
from ..ai.kernel_service import kernel_service

class ObjectiveDataService:
    """Service for managing objective data operations with Azure integrations"""
    
    def __init__(self):
        # Set up logging
        self.logger = logging.getLogger("objective_data_service")
        
        # Initialize Azure Blob Storage client
        self.blob_connection_string = os.getenv("AZURE_STORAGE_CONNECTION_STRING")
        self.blob_container_name = os.getenv("AZURE_BLOB_CONTAINER_NAME", "objective-data")
        self.blob_service_client = None
        self.blob_container_client = None
        
        # Initialize Cosmos DB client
        self.cosmos_endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
        self.cosmos_key = os.getenv("AZURE_COSMOS_KEY")
        self.cosmos_db_name = os.getenv("AZURE_COSMOS_DATABASE", "stratos")
        self.cosmos_datasets_container = os.getenv("AZURE_COSMOS_DATASETS_CONTAINER", "datasets")
        self.cosmos_kpis_container = os.getenv("AZURE_COSMOS_KPIS_CONTAINER", "kpis")
        self.cosmos_datapoints_container = os.getenv("AZURE_COSMOS_DATAPOINTS_CONTAINER", "datapoints")
        
        self.cosmos_client = None
        self.database = None
        self.datasets_container = None
        self.kpis_container = None
        self.datapoints_container = None
        
        # Initialize once for caching metadata during processing
        self.token_limit_for_chunks = 512  # Target token size for optimal embedding chunks
        
    async def initialize_blob_storage(self):
        """Initialize Azure Blob Storage client asynchronously"""
        if self.blob_service_client is None and self.blob_connection_string:
            try:
                self.blob_service_client = BlobServiceClient.from_connection_string(
                    conn_str=self.blob_connection_string
                )
                # Get container client
                self.blob_container_client = self.blob_service_client.get_container_client(
                    self.blob_container_name
                )
                
                # Check if container exists, create if it doesn't
                container_exists = False
                async for container in self.blob_service_client.list_containers():
                    if container.name == self.blob_container_name:
                        container_exists = True
                        break
                
                if not container_exists:
                    await self.blob_service_client.create_container(self.blob_container_name)
                    self.logger.info(f"Created new Azure Blob Storage container: {self.blob_container_name}")
                else:
                    self.logger.info(f"Connected to existing Azure Blob Storage container: {self.blob_container_name}")
                
                return True
            except Exception as e:
                self.logger.error(f"Error initializing Azure Blob Storage: {str(e)}")
                self.blob_service_client = None
                self.blob_container_client = None
                return False
        return self.blob_service_client is not None
        
    async def initialize_cosmos_db(self):
        """Initialize Azure Cosmos DB client asynchronously"""
        if self.cosmos_client is None and self.cosmos_endpoint and self.cosmos_key:
            try:
                self.cosmos_client = CosmosClient(
                    url=self.cosmos_endpoint,
                    credential=self.cosmos_key
                )
                
                # Try to get database, create if it doesn't exist
                self.database = self.cosmos_client.get_database_client(self.cosmos_db_name)
                database_properties = await self.database.read()
                
                if not database_properties:
                    self.database = await self.cosmos_client.create_database(
                        id=self.cosmos_db_name
                    )
                    self.logger.info(f"Created new Cosmos DB database: {self.cosmos_db_name}")
                else:
                    self.logger.info(f"Connected to existing Cosmos DB database: {self.cosmos_db_name}")
                
                # Initialize container clients and create if they don't exist
                await self._init_container(self.cosmos_datasets_container, "/id")
                await self._init_container(self.cosmos_kpis_container, "/id")
                await self._init_container(self.cosmos_datapoints_container, "/dataset_id")
                
                return True
            except Exception as e:
                self.logger.error(f"Error initializing Cosmos DB: {str(e)}")
                self.cosmos_client = None
                self.database = None
                self.datasets_container = None
                self.kpis_container = None
                self.datapoints_container = None
                return False
        return self.cosmos_client is not None
        
    async def _init_container(self, container_id: str, partition_key_path: str) -> ContainerProxy:
        """Initialize a Cosmos DB container"""
        try:
            # Check if container exists
            container = self.database.get_container_client(container_id)
            
            try:
                await container.read()
                self.logger.info(f"Connected to existing container: {container_id}")
            except exceptions.CosmosResourceNotFoundError:
                # Create the container
                container = await self.database.create_container(
                    id=container_id,
                    partition_key=PartitionKey(path=partition_key_path)
                )
                self.logger.info(f"Created new container: {container_id}")
            
            # Set appropriate container
            if container_id == self.cosmos_datasets_container:
                self.datasets_container = container
            elif container_id == self.cosmos_kpis_container:
                self.kpis_container = container
            elif container_id == self.cosmos_datapoints_container:
                self.datapoints_container = container
                
            return container
            
        except Exception as e:
            self.logger.error(f"Error initializing container {container_id}: {str(e)}")
            raise
    
    ############################################################
    # Helper Methods for File Processing
    ############################################################
    
    async def _upload_to_blob_storage(self, file: UploadFile, dataset_id: str) -> str:
        """
        Upload a file to Azure Blob Storage
        
        Args:
            file: FastAPI UploadFile object
            dataset_id: Unique ID for the dataset
            
        Returns:
            The blob URL
        """
        # Ensure blob storage is initialized
        if not await self.initialize_blob_storage():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Blob storage connection not available"
            )
        
        try:
            # Generate blob name using dataset_id and original filename
            original_filename = file.filename
            file_extension = original_filename.split('.')[-1] if '.' in original_filename else ''
            blob_name = f"{dataset_id}.{file_extension}" if file_extension else str(dataset_id)
            
            # Get blob client
            blob_client = self.blob_container_client.get_blob_client(blob_name)
            
            # Set content type based on file extension
            content_type = "application/octet-stream"  # Default
            if file_extension.lower() == 'pdf':
                content_type = "application/pdf"
            elif file_extension.lower() == 'csv':
                content_type = "text/csv"
            elif file_extension.lower() in ['xlsx', 'xls']:
                content_type = "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            elif file_extension.lower() == 'json':
                content_type = "application/json"
                
            # Read file content
            file_content = await file.read()
            
            # Upload to blob storage
            await blob_client.upload_blob(
                data=file_content, 
                overwrite=True,
                content_settings=ContentSettings(content_type=content_type)
            )
            
            # Return blob URL
            return blob_client.url
            
        except Exception as e:
            self.logger.error(f"Error uploading to blob storage: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to upload file: {str(e)}"
            )
    
    async def _download_blob_to_temp(self, blob_url: str) -> str:
        """
        Download a blob to a temporary file
        
        Args:
            blob_url: The URL of the blob to download
            
        Returns:
            Path to the temporary file
        """
        # Ensure blob storage is initialized
        if not await self.initialize_blob_storage():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, 
                detail="Blob storage connection not available"
            )
        
        try:
            # Extract blob name from URL
            blob_name = blob_url.split('/')[-1]
            
            # Get blob client
            blob_client = self.blob_container_client.get_blob_client(blob_name)
            
            # Create a temporary file
            temp_file = NamedTemporaryFile(delete=False)
            temp_file_path = temp_file.name
            temp_file.close()
            
            # Download blob to temp file
            download_stream = await blob_client.download_blob()
            
            async with aiofiles.open(temp_file_path, 'wb') as file:
                data = await download_stream.readall()
                await file.write(data)
            
            return temp_file_path
            
        except Exception as e:
            self.logger.error(f"Error downloading blob: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to download file: {str(e)}"
            )
    
    async def _parse_pdf_content(self, file_path: str, dataset_id: str, dataset_name: str) -> List[Dict[str, Any]]:
        """
        Parse content from a PDF file with semantic chunking
        
        Args:
            file_path: Path to the PDF file
            dataset_id: ID of the dataset
            dataset_name: Name of the dataset
            
        Returns:
            List of content chunks with metadata
        """
        try:
            # Open the PDF
            reader = PdfReader(file_path)
            content_chunks = []
            total_pages = len(reader.pages)
            
            # Add a metadata/overview chunk for the full document
            toc_text = f"Document: {dataset_name}\nTotal pages: {total_pages}\n"
            if hasattr(reader, 'outline') and reader.outline:
                toc_text += "Table of Contents:\n"
                # Format outline/bookmarks if available
                for item in reader.outline:
                    if isinstance(item, dict) and '/Title' in item:
                        toc_text += f"- {item['/Title']}\n"
            
            # Add metadata chunk
            content_chunks.append({
                "content": toc_text,
                "metadata": {
                    "dataset_id": dataset_id,
                    "dataset_name": dataset_name,
                    "chunk_type": "metadata",
                    "content_type": "pdf_overview",
                    "page_count": total_pages,
                    "source_type": "pdf"
                }
            })
            
            # Process each page
            for i, page in enumerate(reader.pages):
                text = page.extract_text()
                
                # Skip empty pages
                if not text or text.strip() == "":
                    continue
                
                # Estimate token count (rough approximation: 4 chars ≈ 1 token)
                estimated_tokens = len(text) / 4
                
                # If page is small enough, keep it as one chunk
                if estimated_tokens <= self.token_limit_for_chunks:
                    content_chunks.append({
                        "content": text,
                        "metadata": {
                            "dataset_id": dataset_id,
                            "dataset_name": dataset_name,
                            "page": i + 1,
                            "chunk_type": "content",
                            "source_type": "pdf",
                            "total_pages": total_pages
                        }
                    })
                else:
                    # Split into chunks using semantic boundaries
                    chunks = self._create_semantic_chunks(
                        text, 
                        self.token_limit_for_chunks, 
                        f"Page {i+1} of {total_pages}"
                    )
                    
                    # Add each chunk with appropriate metadata
                    for chunk_idx, chunk in enumerate(chunks):
                        content_chunks.append({
                            "content": chunk,
                            "metadata": {
                                "dataset_id": dataset_id,
                                "dataset_name": dataset_name,
                                "page": i + 1,
                                "chunk_index": chunk_idx + 1,
                                "total_chunks_in_page": len(chunks),
                                "chunk_type": "content",
                                "source_type": "pdf",
                                "total_pages": total_pages
                            }
                        })
            
            return content_chunks
            
        except Exception as e:
            self.logger.error(f"Error parsing PDF: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse PDF: {str(e)}"
            )

    def _create_semantic_chunks(self, text: str, target_token_size: int, context: str = "") -> List[str]:
        """
        Split text into semantic chunks suitable for embedding
        
        Args:
            text: Text to split
            target_token_size: Target size in tokens
            context: Contextual information to aid in logging
            
        Returns:
            List of text chunks
        """
        # Approximate tokens: ~4 characters per token for English text
        target_char_size = target_token_size * 4
        
        chunks = []
        paragraphs = text.split('\n\n')
        current_chunk = []
        current_size = 0
        
        for paragraph in paragraphs:
            paragraph = paragraph.strip()
            if not paragraph:
                continue
                
            paragraph_size = len(paragraph)
            
            # If adding this paragraph would exceed the target size
            if current_size + paragraph_size > target_char_size and current_chunk:
                # Save current chunk and start a new one
                chunks.append('\n\n'.join(current_chunk))
                current_chunk = [paragraph]
                current_size = paragraph_size
            else:
                # Add paragraph to current chunk
                current_chunk.append(paragraph)
                current_size += paragraph_size
                
                # If a single paragraph is too large, need to split by sentences
                if current_size > target_char_size * 1.5:
                    large_chunk = '\n\n'.join(current_chunk)
                    current_chunk = []
                    current_size = 0
                    
                    # Split by sentence boundaries
                    sentences = []
                    # Simple sentence boundary detection (periods followed by space or newline)
                    sentence_fragments = []
                    current_fragment = ""
                    
                    for char in large_chunk:
                        current_fragment += char
                        if char in ['.', '!', '?'] and (len(current_fragment) > 20):  # Avoid splitting on abbreviations
                            sentences.append(current_fragment)
                            current_fragment = ""
                            
                    if current_fragment:
                        sentences.append(current_fragment)
                    
                    # Group sentences into chunks
                    sentence_chunk = []
                    sentence_chunk_size = 0
                    
                    for sentence in sentences:
                        sentence_size = len(sentence)
                        if sentence_chunk_size + sentence_size > target_char_size and sentence_chunk:
                            chunks.append(' '.join(sentence_chunk))
                            sentence_chunk = [sentence]
                            sentence_chunk_size = sentence_size
                        else:
                            sentence_chunk.append(sentence)
                            sentence_chunk_size += sentence_size
                    
                    if sentence_chunk:
                        chunks.append(' '.join(sentence_chunk))
        
        # Add the last chunk if any exists
        if current_chunk:
            chunks.append('\n\n'.join(current_chunk))
        
        # If we still have very large chunks, force-split them
        final_chunks = []
        for chunk in chunks:
            if len(chunk) > target_char_size * 1.5:
                self.logger.warning(f"Force-splitting large chunk in {context} (size: {len(chunk)} chars)")
                # Split by character count with some overlap
                overlap = 100  # characters of overlap
                for i in range(0, len(chunk), target_char_size - overlap):
                    end = min(i + target_char_size, len(chunk))
                    final_chunks.append(chunk[i:end])
            else:
                final_chunks.append(chunk)
        
        return final_chunks
    
    async def _parse_spreadsheet_content(self, file_path: str, file_format: str, dataset_id: str, dataset_name: str) -> List[Dict[str, Any]]:
        """
        Parse content from a spreadsheet file (CSV or Excel)
        
        Args:
            file_path: Path to the spreadsheet file
            file_format: Format of the file ('csv' or 'excel')
            dataset_id: ID of the dataset
            dataset_name: Name of the dataset
            
        Returns:
            List of content chunks with metadata
        """
        try:
            # Read the file into a pandas DataFrame
            if file_format == 'csv':
                df = pd.read_csv(file_path)
                sheets = {"Sheet1": df}  # Single sheet for CSV
            elif file_format == 'excel':
                xl = pd.ExcelFile(file_path)
                sheets = {sheet_name: xl.parse(sheet_name) for sheet_name in xl.sheet_names}
            else:
                raise ValueError(f"Unsupported file format: {file_format}")
            
            content_chunks = []
            
            # Create an overall dataset metadata chunk
            sheet_names = list(sheets.keys())
            overview = (
                f"Dataset: {dataset_name}\n"
                f"Format: {file_format.upper()}\n"
                f"Sheet count: {len(sheets)}\n"
                f"Sheet names: {', '.join(sheet_names)}\n"
            )
            
            # Add metadata chunk for the dataset
            content_chunks.append({
                "content": overview,
                "metadata": {
                    "dataset_id": dataset_id,
                    "dataset_name": dataset_name,
                    "chunk_type": "metadata",
                    "content_type": "spreadsheet_overview",
                    "source_type": file_format
                }
            })
                
            for sheet_name, sheet_df in sheets.items():
                # Add headers description
                columns = sheet_df.columns.tolist()
                headers_description = f"Sheet: {sheet_name}\nColumns: {', '.join(str(col) for col in columns)}"
                
                # Add overall sheet stats
                row_count = len(sheet_df)
                col_count = len(sheet_df.columns)
                data_types = {col: str(dtype) for col, dtype in sheet_df.dtypes.items()}
                stats_text = (
                    f"Sheet statistics: {row_count} rows, {col_count} columns.\n"
                    f"Data types: {', '.join([f'{col}: {dtype}' for col, dtype in data_types.items()])}\n"
                )
                
                # Include sample values for each column (first few non-null values)
                sample_values = {}
                for col in sheet_df.columns:
                    non_null_values = sheet_df[col].dropna()
                    if len(non_null_values) > 0:
                        samples = non_null_values.iloc[:3].tolist()
                        sample_values[col] = [str(s)[:50] + ('...' if len(str(s)) > 50 else '') for s in samples]
                    else:
                        sample_values[col] = ["<no data>"]
                
                sample_text = "Sample values:\n"
                for col, samples in sample_values.items():
                    sample_text += f"  {col}: {', '.join(samples)}\n"
                
                # Create a chunk for the sheet description and structure
                sheet_info = f"{headers_description}\n{stats_text}\n{sample_text}"
                content_chunks.append({
                    "content": sheet_info,
                    "metadata": {
                        "dataset_id": dataset_id,
                        "dataset_name": dataset_name,
                        "sheet": sheet_name,
                        "chunk_type": "metadata",
                        "content_type": "sheet_structure",
                        "source_type": file_format,
                        "row_count": row_count,
                        "column_count": col_count
                    }
                })
                
                # Convert sheet to textual representation
                # For small sheets, include the full data
                if row_count <= 100:
                    sheet_text = sheet_df.to_string(index=False)
                    content_chunks.append({
                        "content": sheet_text,
                        "metadata": {
                            "dataset_id": dataset_id,
                            "dataset_name": dataset_name,
                            "sheet": sheet_name,
                            "chunk_type": "data",
                            "content_type": "full_data",
                            "source_type": file_format,
                            "row_count": row_count
                        }
                    })
                else:
                    # For larger sheets, split into chunks by rows
                    chunk_size = 100  # rows per chunk
                    for i in range(0, row_count, chunk_size):
                        end_idx = min(i+chunk_size, row_count)
                        chunk_df = sheet_df.iloc[i:end_idx]
                        chunk_text = chunk_df.to_string(index=False)
                        
                        # Check if the text is too large for embedding
                        estimated_tokens = len(chunk_text) / 4
                        if estimated_tokens > self.token_limit_for_chunks:
                            # Further split based on columns if necessary
                            num_cols = len(chunk_df.columns)
                            if num_cols > 4:  # Only split if we have enough columns
                                mid_point = num_cols // 2
                                # Split columns and create two chunks
                                left_chunk = chunk_df.iloc[:, :mid_point].to_string(index=False)
                                right_chunk = chunk_df.iloc[:, mid_point:].to_string(index=False)
                                
                                # Add left columns chunk
                                content_chunks.append({
                                    "content": left_chunk,
                                    "metadata": {
                                        "dataset_id": dataset_id,
                                        "dataset_name": dataset_name,
                                        "sheet": sheet_name,
                                        "chunk_type": "data",
                                        "content_type": "partial_data",
                                        "rows": f"{i+1}-{end_idx}",
                                        "columns": f"1-{mid_point}",
                                        "source_type": file_format
                                    }
                                })
                                
                                # Add right columns chunk
                                content_chunks.append({
                                    "content": right_chunk,
                                    "metadata": {
                                        "dataset_id": dataset_id,
                                        "dataset_name": dataset_name,
                                        "sheet": sheet_name,
                                        "chunk_type": "data",
                                        "content_type": "partial_data",
                                        "rows": f"{i+1}-{end_idx}",
                                        "columns": f"{mid_point+1}-{num_cols}",
                                        "source_type": file_format
                                    }
                                })
                            else:
                                # Just add the potentially large chunk
                                content_chunks.append({
                                    "content": chunk_text,
                                    "metadata": {
                                        "dataset_id": dataset_id,
                                        "dataset_name": dataset_name,
                                        "sheet": sheet_name,
                                        "chunk_type": "data",
                                        "content_type": "data_subset",
                                        "rows": f"{i+1}-{end_idx}",
                                        "source_type": file_format
                                    }
                                })
                        else:
                            # Add the chunk as is
                            content_chunks.append({
                                "content": chunk_text,
                                "metadata": {
                                    "dataset_id": dataset_id,
                                    "dataset_name": dataset_name,
                                    "sheet": sheet_name,
                                    "chunk_type": "data",
                                    "content_type": "data_subset",
                                    "rows": f"{i+1}-{end_idx}",
                                    "source_type": file_format
                                }
                            })
                
                # Add summary statistics for numerical columns
                num_cols = sheet_df.select_dtypes(include=['number']).columns
                if len(num_cols) > 0:
                    stats_df = sheet_df[num_cols].describe().round(2)
                    stats_text = stats_df.to_string()
                    
                    content_chunks.append({
                        "content": f"Statistical summary for {sheet_name}:\n{stats_text}",
                        "metadata": {
                            "dataset_id": dataset_id,
                            "dataset_name": dataset_name,
                            "sheet": sheet_name,
                            "chunk_type": "metadata",
                            "content_type": "statistics",
                            "source_type": file_format
                        }
                    })
            
            return content_chunks
            
        except Exception as e:
            self.logger.error(f"Error parsing spreadsheet: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to parse spreadsheet: {str(e)}"
            )
    
    async def _trigger_ai_indexing(self, dataset_id: str, content_chunks: List[Dict[str, Any]], dataset_metadata: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate embeddings and index content in Azure AI Search
        
        Args:
            dataset_id: ID of the dataset
            content_chunks: List of content chunks to index
            dataset_metadata: Additional metadata about the dataset
            
        Returns:
            Dictionary with indexing results
        """
        try:
            collection_name = f"dataset-{dataset_id}"
            dataset_name = dataset_metadata.get("name", "Unknown Dataset")
            
            self.logger.info(f"Starting AI indexing for dataset {dataset_id} ({dataset_name}) - {len(content_chunks)} chunks")
            
            # Process chunks in batches to avoid overwhelming the service
            batch_size = 10
            total_chunks = len(content_chunks)
            successful_chunks = 0
            failed_chunks = 0
            
            for i in range(0, total_chunks, batch_size):
                batch_end = min(i + batch_size, total_chunks)
                batch = content_chunks[i:batch_end]
                
                # Process each chunk in the batch asynchronously
                indexing_tasks = []
                
                for j, chunk in enumerate(batch):
                    # Create a unique ID for each chunk
                    chunk_idx = i + j
                    chunk_id = f"{dataset_id}-chunk-{chunk_idx}"
                    
                    # Get the content and metadata
                    content = chunk["content"]
                    metadata = chunk["metadata"].copy()
                    
                    # Add additional dataset metadata
                    metadata["dataset_id"] = dataset_id
                    metadata["dataset_name"] = dataset_name
                    metadata["category"] = dataset_metadata.get("category")
                    # Add new fields to AI Search metadata
                    metadata["tags"] = dataset_metadata.get("tags", [])
                    metadata["linked_strategic_elements"] = dataset_metadata.get("linked_strategic_elements", [])
                    metadata["index_timestamp"] = datetime.now().isoformat()
                    metadata["chunk_id"] = chunk_id
                    
                    # Convert metadata to string for description
                    metadata_str = json.dumps(metadata)
                    
                    # Remember the chunk in semantic memory
                    task = kernel_service.remember(
                        collection=collection_name,
                        key=chunk_id,
                        text=content,
                        description=metadata_str
                    )
                    indexing_tasks.append(task)
                
                # Wait for the current batch to complete
                batch_results = await asyncio.gather(*indexing_tasks, return_exceptions=True)
                
                # Process results
                for result in batch_results:
                    if isinstance(result, Exception) or result is False:
                        failed_chunks += 1
                        self.logger.error(f"Failed to index chunk: {str(result) if isinstance(result, Exception) else 'Unknown error'}")
                    else:
                        successful_chunks += 1
                
                # Log progress for large datasets
                if total_chunks > 20 and (batch_end % 20 == 0 or batch_end == total_chunks):
                    self.logger.info(f"Indexing progress: {batch_end}/{total_chunks} chunks processed")
            
            # Prepare indexing results
            indexing_results = {
                "status": "completed" if failed_chunks == 0 else "partial",
                "total_chunks": total_chunks,
                "indexed_chunks": successful_chunks,
                "failed_chunks": failed_chunks,
                "success_rate": round((successful_chunks / total_chunks) * 100, 2) if total_chunks > 0 else 0,
                "completed_at": datetime.now().isoformat()
            }
            
            self.logger.info(f"AI indexing completed for dataset {dataset_id} - Results: {indexing_results}")
            
            return indexing_results
            
        except Exception as e:
            self.logger.error(f"Error in AI indexing for dataset {dataset_id}: {str(e)}")
            return {
                "status": "failed",
                "error": str(e),
                "total_chunks": len(content_chunks),
                "indexed_chunks": 0,
                "failed_chunks": len(content_chunks),
                "success_rate": 0,
                "completed_at": datetime.now().isoformat()
            }
    
    async def _delete_from_ai_search(self, dataset_id: str) -> bool:
        """
        Delete all indexed content for a dataset from Azure AI Search
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            Boolean indicating success
        """
        try:
            collection_name = f"dataset-{dataset_id}"
            
            # Approach 1: If using collection per dataset, try to delete the collection
            # Note: This might not be directly supported through the kernel API, may need custom method
            
            # Approach 2: If using single collection with dataset_id field, delete all matching items
            # This approach requires getting all keys for the dataset and deleting each one
            
            # Try to get all memory keys for this dataset
            search_query = f"dataset_id:{dataset_id}"
            max_results = 1000  # Large number to try to get all results
            
            try:
                # Search for all items with this dataset_id
                results = await kernel_service.recall(
                    collection=collection_name,
                    query="*",  # Get all entries
                    limit=max_results
                )
                
                if results:
                    # Delete each item
                    delete_tasks = []
                    for result in results:
                        # Extract key from the MemoryQueryResult
                        if hasattr(result, 'id'):
                            key = result.id
                            # Use remove_async if available
                            if hasattr(kernel_service.memory, 'remove_async'):
                                task = kernel_service.memory.remove_async(collection_name, key)
                                delete_tasks.append(task)
                            # Alternatively, try remove_information_async
                            elif hasattr(kernel_service.memory, 'remove_information_async'):
                                task = kernel_service.memory.remove_information_async(collection_name, key)
                                delete_tasks.append(task)
                    
                    # Wait for all deletion tasks to complete
                    if delete_tasks:
                        await asyncio.gather(*delete_tasks, return_exceptions=True)
                        
                    self.logger.info(f"Deleted {len(delete_tasks)} indexed items for dataset {dataset_id}")
                else:
                    self.logger.info(f"No indexed items found for dataset {dataset_id}")
            
            except Exception as inner_e:
                self.logger.error(f"Error deleting indexed items for dataset {dataset_id}: {str(inner_e)}")
                
                # As a fallback, try to delete the entire collection
                try:
                    # Delete the collection directly from the underlying storage
                    memory_store = kernel_service.memory.storage
                    if hasattr(memory_store, 'delete_collection_async'):
                        await memory_store.delete_collection_async(collection_name)
                        self.logger.info(f"Deleted collection {collection_name} from AI Search")
                    elif hasattr(memory_store, 'delete_index_async'):
                        await memory_store.delete_index_async(collection_name)
                        self.logger.info(f"Deleted index {collection_name} from AI Search")
                    else:
                        self.logger.warning(f"Unable to delete collection/index {collection_name} - method not available")
                        return False
                except Exception as collection_e:
                    self.logger.error(f"Error deleting collection {collection_name}: {str(collection_e)}")
                    return False
            
            return True
            
        except Exception as e:
            self.logger.error(f"Error deleting from AI Search for dataset {dataset_id}: {str(e)}")
            return False
    
    ############################################################
    # Public API Methods - Dataset Operations
    ############################################################
    
    async def process_uploaded_file(self, file: UploadFile, dataset_data: DataSetCreate) -> DataSet:
        """
        Process an uploaded file: save to blob storage and create dataset record
        
        Args:
            file: The uploaded file
            dataset_data: Dataset creation data
            
        Returns:
            The created dataset
        """
        # Generate a new dataset ID
        dataset_id = str(uuid.uuid4())
        
        try:
            # Upload file to blob storage
            blob_url = await self._upload_to_blob_storage(file, dataset_id)
            
            # Ensure Cosmos DB is initialized
            if not await self.initialize_cosmos_db():
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Database connection not available"
                )
            
            # Create dataset record
            # dataset_data is DataSetCreate, which now includes tags and linked_strategic_elements
            current_time = datetime.now()
            
            dataset = DataSet(
                id=UUID(dataset_id),
                name=dataset_data.name,
                description=dataset_data.description,
                category=dataset_data.category,
                source_type=dataset_data.source_type,
                source_details=dataset_data.source_details,
                data_format=dataset_data.data_format,
                tags=dataset_data.tags, # Pass through tags
                linked_strategic_elements=dataset_data.linked_strategic_elements, # Pass through links
                file_path=blob_url,
                import_date=current_time,
                created_at=current_time,
                updated_at=current_time,
                metadata={ # Initial metadata
                    "original_filename": file.filename,
                    "ai_indexed": False,
                    "size_bytes": file.size if file else 0, # Handle if file is None (though not in this method)
                    "processing_status": "pending"
                }
            )
            
            # Convert to dict for DB, ensuring UUIDs are strings if model stores them as UUID
            dataset_db_dict = dataset.model_dump() # Changed to model_dump()
            dataset_db_dict["id"] = str(dataset.id) # id is already UUID from default_factory
            # tags and linked_strategic_elements are already in correct format from model
            
            # Save to Cosmos DB
            # This line seems to be duplicated, the one above already prepares dataset_db_dict
            # await self.datasets_container.create_item(body=dataset_db_dict) 
            
            # Save to Cosmos DB
            # Assuming the intent was to use dataset_db_dict which has id as string
            await self.datasets_container.create_item(body=dataset_db_dict) # Using the prepared dict
            
            # Start background task for parsing and indexing
            asyncio.create_task(self._process_file_background(dataset))
            
            return dataset
            
        except Exception as e:
            self.logger.error(f"Error processing uploaded file: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to process file: {str(e)}"
            )
    
    async def _process_file_background(self, dataset: DataSet) -> None:
        """
        Background task to process a file: parse content and generate embeddings
        
        Args:
            dataset: The dataset record
        """
        try:
            # Update status to "processing"
            await self.update_dataset_metadata(
                dataset.id,
                {
                    "processing_status": "processing",
                    "processing_started_at": datetime.now().isoformat()
                }
            )
            
            # Download file to temp location
            temp_file_path = await self._download_blob_to_temp(dataset.file_path)
            
            # Parse content based on file format
            content_chunks = []
            dataset_name = dataset.name
            # dataset_dict = dataset.model_dump() # Changed to model_dump(), though not immediately used here
            
            if dataset.data_format == 'csv':
                content_chunks = await self._parse_spreadsheet_content(
                    temp_file_path, 
                    'csv', 
                    str(dataset.id),
                    dataset_name
                )
            elif dataset.data_format == 'excel':
                content_chunks = await self._parse_spreadsheet_content(
                    temp_file_path, 
                    'excel', 
                    str(dataset.id),
                    dataset_name
                )
            elif dataset.data_format == 'pdf':
                content_chunks = await self._parse_pdf_content(
                    temp_file_path, 
                    str(dataset.id),
                    dataset_name
                )
            else:
                self.logger.warning(f"Unsupported file format for parsing: {dataset.data_format}")
                await self.update_dataset_metadata(
                    dataset.id,
                    {
                        "processing_status": "failed",
                        "processing_error": f"Unsupported file format: {dataset.data_format}",
                        "processing_completed_at": datetime.now().isoformat()
                    }
                )
                # Clean up temp file
                os.unlink(temp_file_path)
                return
            
            # Update metadata with content chunks count
            await self.update_dataset_metadata(
                dataset.id,
                {
                    "content_chunks": len(content_chunks),
                    "parsed_at": datetime.now().isoformat(),
                    "processing_status": "indexing"
                }
            )
            
            # Generate embeddings and index in Azure AI Search
            indexing_results = await self._trigger_ai_indexing(
                str(dataset.id), 
                content_chunks,
                { # Pass dataset metadata for indexing context
                    "name": dataset.name,
                    "category": dataset.category.value if dataset.category else None,
                    "tags": dataset.tags,
                    "linked_strategic_elements": dataset.linked_strategic_elements
                }
            )
            
            # Update dataset with indexing results
            await self.update_dataset_metadata(
                dataset.id,
                {
                    "ai_indexed": indexing_results["status"] in ["completed", "partial"],
                    "indexed_chunks": indexing_results["indexed_chunks"],
                    "failed_chunks": indexing_results["failed_chunks"],
                    "indexing_success_rate": indexing_results["success_rate"],
                    "last_indexed": indexing_results["completed_at"],
                    "processing_status": "completed" if indexing_results["status"] != "failed" else "failed",
                    "processing_completed_at": datetime.now().isoformat()
                }
            )
            
            # Clean up temp file
            os.unlink(temp_file_path)
            
        except Exception as e:
            self.logger.error(f"Error in background processing for dataset {dataset.id}: {str(e)}")
            # Update metadata with error
            await self.update_dataset_metadata(
                dataset.id,
                {
                    "processing_status": "failed",
                    "processing_error": str(e),
                    "processing_failed_at": datetime.now().isoformat()
                }
            )
    
    async def create_dataset(self, dataset_data: DataSetCreate) -> DataSet:
        """
        Create a new dataset record (without file upload)
        
        Args:
            dataset_data: Dataset creation data
            
        Returns:
            The created dataset
        """
        # Ensure Cosmos DB is initialized
        if not await self.initialize_cosmos_db():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
            
        dataset_id = uuid.uuid4()
        current_time = datetime.now()
        
        # DataSetCreate now includes tags and linked_strategic_elements
        dataset = DataSet(
            id=dataset_id,
            name=dataset_data.name,
            description=dataset_data.description,
            category=dataset_data.category,
            source_type=dataset_data.source_type,
            source_details=dataset_data.source_details,
            data_format=dataset_data.data_format,
            tags=dataset_data.tags,
            linked_strategic_elements=dataset_data.linked_strategic_elements,
            created_at=current_time,
            updated_at=current_time
            # file_path and import_date would typically be None or set if applicable
        )
        
        dataset_db_dict = dataset.model_dump() # Changed to model_dump()
        dataset_db_dict["id"] = str(dataset.id)

        # Save to Cosmos DB
        await self.datasets_container.create_item(body=dataset_db_dict)
        
        return dataset
    
    async def get_dataset(self, dataset_id: UUID) -> Optional[DataSet]:
        """
        Get a dataset by ID
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            Dataset or None if not found
        """
        # Ensure Cosmos DB is initialized
        if not await self.initialize_cosmos_db():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        try:
            item = await self.datasets_container.read_item(
                item=str(dataset_id),
                partition_key=str(dataset_id)
            )
            return DataSet(**item)
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"Error getting dataset {dataset_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get dataset: {str(e)}"
            )
    
    async def list_datasets(
        self, 
        limit: int = 20, 
        offset: int = 0, 
        category: Optional[DataCategory] = None, 
        source_type: Optional[DataSourceType] = None
    ) -> List[DataSet]:
        """
        List datasets with optional filtering
        
        Args:
            limit: Maximum number of datasets to return
            offset: Number of datasets to skip
            category: Filter by category
            source_type: Filter by source type
            
        Returns:
            List of datasets
        """
        # Ensure Cosmos DB is initialized
        if not await self.initialize_cosmos_db():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        try:
            # Build query
            query = "SELECT * FROM c"
            parameters = []
            
            if category or source_type:
                query += " WHERE "
                conditions = []
                
                if category:
                    conditions.append("c.category = @category")
                    parameters.append({"name": "@category", "value": category.value})
                
                if source_type:
                    conditions.append("c.source_type = @source_type")
                    parameters.append({"name": "@source_type", "value": source_type.value})
                
                query += " AND ".join(conditions)
            
            # Add ORDER BY and pagination
            query += f" ORDER BY c.created_at DESC OFFSET {offset} LIMIT {limit}"
            
            # Execute query
            items = []
            async for item in self.datasets_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ):
                items.append(item)
            
            return [DataSet(**item) for item in items]
            
        except Exception as e:
            self.logger.error(f"Error listing datasets: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list datasets: {str(e)}"
            )
    
    async def update_dataset(self, dataset_id: UUID, dataset_data: dict) -> Optional[DataSet]:
        """
        Update a dataset
        
        Args:
            dataset_id: ID of the dataset
            dataset_data: Dictionary of fields to update
            
        Returns:
            Updated dataset or None if not found
        """
        # Ensure Cosmos DB is initialized
        if not await self.initialize_cosmos_db():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        try:
            # Get existing dataset
            existing = await self.get_dataset(dataset_id)
            if not existing:
                return None
            
            # Update fields
            existing_dict = existing.model_dump() # Changed to model_dump()
            existing_dict.update(dataset_data)
            existing_dict["updated_at"] = datetime.now()
            
            # Save back to Cosmos DB
            updated = await self.datasets_container.replace_item(
                item=str(dataset_id),
                body=existing_dict
            )
            
            return DataSet(**updated)
            
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"Error updating dataset {dataset_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update dataset: {str(e)}"
            )
    
    async def update_dataset_metadata(self, dataset_id: UUID, metadata_updates: dict) -> Optional[DataSet]:
        """
        Update only the metadata field of a dataset
        
        Args:
            dataset_id: ID of the dataset
            metadata_updates: Dictionary of metadata fields to update
            
        Returns:
            Updated dataset or None if not found
        """
        # Ensure Cosmos DB is initialized
        if not await self.initialize_cosmos_db():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        try:
            # Get existing dataset
            existing = await self.get_dataset(dataset_id)
            if not existing:
                return None
            
            # Update metadata
            existing_dict = existing.model_dump() # Changed to model_dump()
            if not existing_dict.get("metadata"):
                existing_dict["metadata"] = {}
            
            existing_dict["metadata"].update(metadata_updates)
            existing_dict["updated_at"] = datetime.now()
            
            # Save back to Cosmos DB
            updated = await self.datasets_container.replace_item(
                item=str(dataset_id),
                body=existing_dict
            )
            
            return DataSet(**updated)
            
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"Error updating dataset metadata {dataset_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update dataset metadata: {str(e)}"
            )
    
    async def delete_dataset(self, dataset_id: UUID) -> bool:
        """
        Delete a dataset and its related data/files
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            Boolean indicating success
        """
        # Ensure blob storage and Cosmos DB are initialized
        if not await self.initialize_cosmos_db():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        try:
            # First, get the dataset to check for file path
            dataset = await self.get_dataset(dataset_id)
            if not dataset:
                return False
            
            deletion_results = {
                "cosmos": False,
                "blob": False,
                "datapoints": False,
                "ai_search": False
            }
            
            # Delete from Cosmos DB
            try:
                await self.datasets_container.delete_item(
                    item=str(dataset_id),
                    partition_key=str(dataset_id)
                )
                deletion_results["cosmos"] = True
            except Exception as cosmos_e:
                self.logger.error(f"Error deleting dataset {dataset_id} from Cosmos DB: {str(cosmos_e)}")
            
            # If there's a file, delete from blob storage
            if dataset.file_path and await self.initialize_blob_storage():
                try:
                    # Extract blob name from URL
                    blob_name = dataset.file_path.split('/')[-1]
                    blob_client = self.blob_container_client.get_blob_client(blob_name)
                    await blob_client.delete_blob()
                    deletion_results["blob"] = True
                except Exception as blob_e:
                    self.logger.error(f"Error deleting blob for dataset {dataset_id}: {str(blob_e)}")
            
            # Delete related datapoints
            try:
                # Query for all datapoints with this dataset_id
                query = "SELECT * FROM c WHERE c.dataset_id = @dataset_id"
                parameters = [{"name": "@dataset_id", "value": str(dataset_id)}]
                
                datapoints_to_delete = []
                async for item in self.datapoints_container.query_items(
                    query=query,
                    parameters=parameters,
                    partition_key=str(dataset_id)
                ):
                    datapoints_to_delete.append(item)
                
                # Delete each datapoint
                for item in datapoints_to_delete:
                    await self.datapoints_container.delete_item(
                        item=item["id"],
                        partition_key=str(dataset_id)
                    )
                
                deletion_results["datapoints"] = True
                self.logger.info(f"Deleted {len(datapoints_to_delete)} datapoints for dataset {dataset_id}")
            except Exception as dp_e:
                self.logger.error(f"Error deleting datapoints for dataset {dataset_id}: {str(dp_e)}")
            
            # Delete from AI Search
            try:
                ai_search_result = await self._delete_from_ai_search(str(dataset_id))
                deletion_results["ai_search"] = ai_search_result
            except Exception as ai_e:
                self.logger.error(f"Error deleting AI Search data for dataset {dataset_id}: {str(ai_e)}")
            
            # Log overall deletion results
            self.logger.info(f"Dataset {dataset_id} deletion results: {deletion_results}")
            
            # If we successfully deleted from Cosmos DB, consider the operation successful
            # The other deletions are best-effort
            return deletion_results["cosmos"]
            
        except exceptions.CosmosResourceNotFoundError:
            return False
        except Exception as e:
            self.logger.error(f"Error deleting dataset {dataset_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete dataset: {str(e)}"
            )
    
    async def analyze_dataset(self, dataset_id: UUID) -> Dict[str, Any]:
        """
        Analyze a dataset and generate insights
        
        Args:
            dataset_id: ID of the dataset
            
        Returns:
            Dictionary of analysis results
        """
        # Get the dataset
        dataset = await self.get_dataset(dataset_id)
        if not dataset:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Dataset not found"
            )
        
        # Search for content with kernel_service
        collection_name = f"dataset-{dataset_id}"
        query = "Dataset overview and key insights"
        
        try:
            results = await kernel_service.recall(collection_name, query, limit=10)
            
            if not results:
                return {
                    "status": "no_data",
                    "message": "No indexed content found for this dataset"
                }
            
            # Extract content from search results
            contents = [result.text for result in results]
            combined_content = "\n\n".join(contents)
            
            # Generate insights using LLM
            prompt = f"""
            You are a data analyst helping to extract insights from a dataset. 
            Here's a sample of the dataset content:
            
            {combined_content}
            
            Please provide:
            1. A brief overview of what this dataset contains
            2. 3-5 key insights from the data
            3. Potential strategic implications for the business
            
            Format the response as JSON with the following structure:
            {{
                "overview": "Description of the dataset",
                "insights": ["Insight 1", "Insight 2", "Insight 3"],
                "implications": ["Implication 1", "Implication 2"]
            }}
            """
            
            # Call the LLM for analysis
            response = await kernel_service.generate_completion(prompt, max_tokens=1500)
            
            # Try to parse as JSON
            try:
                analysis_results = json.loads(response)
            except json.JSONDecodeError:
                # If not valid JSON, return the raw text
                analysis_results = {
                    "status": "partial_success",
                    "raw_analysis": response
                }
            
            # Save insights to dataset
            if "insights" in analysis_results and isinstance(analysis_results["insights"], list):
                await self.update_dataset(
                    dataset_id,
                    {"insights": analysis_results["insights"]}
                )
            
            return analysis_results
            
        except Exception as e:
            self.logger.error(f"Error analyzing dataset {dataset_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to analyze dataset: {str(e)}"
            )
    
    ############################################################
    # Public API Methods - KPI Operations
    ############################################################
    
    async def create_kpi(self, kpi_data: KPICreate) -> KPI:
        """
        Create a new KPI
        
        Args:
            kpi_data: KPI creation data
            
        Returns:
            The created KPI
        """
        # Ensure Cosmos DB is initialized
        if not await self.initialize_cosmos_db():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        try:
            # Create KPI record
            kpi_id = uuid.uuid4()
            kpi_dict = kpi_data.model_dump() # Changed to model_dump()
            
            # Convert string IDs to UUIDs
            if "linked_goals" in kpi_dict and kpi_dict["linked_goals"]:
                kpi_dict["linked_goals"] = [UUID(goal_id) for goal_id in kpi_dict["linked_goals"]]
            
            current_time = datetime.now()
            kpi_dict.update({
                "id": kpi_id,
                "trend": "stable",  # Default trend
                "created_at": current_time,
                "updated_at": current_time
            })
            
            kpi = KPI(**kpi_dict)
            
            # Save to Cosmos DB
            await self.kpis_container.create_item(body=kpi.model_dump()) # Changed to model_dump()
            
            return kpi
            
        except Exception as e:
            self.logger.error(f"Error creating KPI: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create KPI: {str(e)}"
            )
    
    async def get_kpi(self, kpi_id: UUID) -> Optional[KPI]:
        """
        Get a KPI by ID
        
        Args:
            kpi_id: ID of the KPI
            
        Returns:
            KPI or None if not found
        """
        # Ensure Cosmos DB is initialized
        if not await self.initialize_cosmos_db():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        try:
            item = await self.kpis_container.read_item(
                item=str(kpi_id),
                partition_key=str(kpi_id)
            )
            return KPI(**item)
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"Error getting KPI {kpi_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to get KPI: {str(e)}"
            )
    
    async def list_kpis(
        self, 
        limit: int = 20, 
        offset: int = 0, 
        category: Optional[DataCategory] = None, 
        goal_id: Optional[UUID] = None
    ) -> List[KPI]:
        """
        List KPIs with optional filtering
        
        Args:
            limit: Maximum number of KPIs to return
            offset: Number of KPIs to skip
            category: Filter by category
            goal_id: Filter by linked goal ID
            
        Returns:
            List of KPIs
        """
        # Ensure Cosmos DB is initialized
        if not await self.initialize_cosmos_db():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        try:
            # Build query
            query = "SELECT * FROM c"
            parameters = []
            
            if category or goal_id:
                query += " WHERE "
                conditions = []
                
                if category:
                    conditions.append("c.category = @category")
                    parameters.append({"name": "@category", "value": category.value})
                
                if goal_id:
                    conditions.append("ARRAY_CONTAINS(c.linked_goals, @goal_id)")
                    parameters.append({"name": "@goal_id", "value": str(goal_id)})
                
                query += " AND ".join(conditions)
            
            # Add ORDER BY and pagination
            query += f" ORDER BY c.created_at DESC OFFSET {offset} LIMIT {limit}"
            
            # Execute query
            items = []
            async for item in self.kpis_container.query_items(
                query=query,
                parameters=parameters,
                enable_cross_partition_query=True
            ):
                items.append(item)
            
            return [KPI(**item) for item in items]
            
        except Exception as e:
            self.logger.error(f"Error listing KPIs: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list KPIs: {str(e)}"
            )
    
    async def update_kpi(self, kpi_id: UUID, kpi_data: dict) -> Optional[KPI]:
        """
        Update a KPI
        
        Args:
            kpi_id: ID of the KPI
            kpi_data: Dictionary of fields to update
            
        Returns:
            Updated KPI or None if not found
        """
        # Ensure Cosmos DB is initialized
        if not await self.initialize_cosmos_db():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        try:
            # Get existing KPI
            existing = await self.get_kpi(kpi_id)
            if not existing:
                return None
            
            # Handle linked_goals conversion if present
            if "linked_goals" in kpi_data and kpi_data["linked_goals"]:
                kpi_data["linked_goals"] = [UUID(goal_id) for goal_id in kpi_data["linked_goals"] 
                                           if isinstance(goal_id, str)]
            
            # Update fields
            existing_dict = existing.model_dump() # Changed to model_dump()
            existing_dict.update(kpi_data)
            existing_dict["updated_at"] = datetime.now()
            
            # Detect trend if current_value changed
            if "current_value" in kpi_data and existing.current_value != kpi_data["current_value"]:
                if kpi_data["current_value"] > existing.current_value:
                    existing_dict["trend"] = "up"
                elif kpi_data["current_value"] < existing.current_value:
                    existing_dict["trend"] = "down"
                else:
                    existing_dict["trend"] = "stable"
            
            # Save back to Cosmos DB
            updated = await self.kpis_container.replace_item(
                item=str(kpi_id),
                body=existing_dict
            )
            
            return KPI(**updated)
            
        except exceptions.CosmosResourceNotFoundError:
            return None
        except Exception as e:
            self.logger.error(f"Error updating KPI {kpi_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to update KPI: {str(e)}"
            )
    
    async def delete_kpi(self, kpi_id: UUID) -> bool:
        """
        Delete a KPI
        
        Args:
            kpi_id: ID of the KPI
            
        Returns:
            Boolean indicating success
        """
        # Ensure Cosmos DB is initialized
        if not await self.initialize_cosmos_db():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        try:
            await self.kpis_container.delete_item(
                item=str(kpi_id),
                partition_key=str(kpi_id)
            )
            return True
        except exceptions.CosmosResourceNotFoundError:
            return False
        except Exception as e:
            self.logger.error(f"Error deleting KPI {kpi_id}: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to delete KPI: {str(e)}"
            )
    
    ############################################################
    # Public API Methods - Data Point Operations
    ############################################################
    
    async def create_datapoint(self, datapoint_data: DataPointCreate) -> DataPoint:
        """
        Create a new data point
        
        Args:
            datapoint_data: Data point creation data
            
        Returns:
            The created data point
        """
        # Ensure Cosmos DB is initialized
        if not await self.initialize_cosmos_db():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        try:
            # Convert string dataset_id to UUID
            dataset_id = UUID(datapoint_data.dataset_id)
            
            # Check if dataset exists
            dataset = await self.get_dataset(dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found"
                )
            
            # Create data point record
            datapoint_id = uuid.uuid4()
            datapoint_dict = datapoint_data.model_dump() # Changed to model_dump()
            current_time = datetime.now()
            
            datapoint_dict.update({
                "id": datapoint_id,
                "dataset_id": dataset_id,
                "created_at": current_time,
                "updated_at": current_time
            })
            
            datapoint = DataPoint(**datapoint_dict)
            
            # Save to Cosmos DB
            await self.datapoints_container.create_item(body=datapoint.model_dump()) # Changed to model_dump()
            
            return datapoint
            
        except Exception as e:
            self.logger.error(f"Error creating data point: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create data point: {str(e)}"
            )
    
    async def list_datapoints(
        self, 
        dataset_id: UUID, 
        limit: int = 100, 
        offset: int = 0
    ) -> List[DataPoint]:
        """
        List data points for a dataset
        
        Args:
            dataset_id: ID of the dataset
            limit: Maximum number of data points to return
            offset: Number of data points to skip
            
        Returns:
            List of data points
        """
        # Ensure Cosmos DB is initialized
        if not await self.initialize_cosmos_db():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        try:
            # Build query
            query = "SELECT * FROM c WHERE c.dataset_id = @dataset_id"
            parameters = [{"name": "@dataset_id", "value": str(dataset_id)}]
            
            # Add ORDER BY and pagination
            query += f" ORDER BY c.timestamp DESC OFFSET {offset} LIMIT {limit}"
            
            # Execute query
            items = []
            async for item in self.datapoints_container.query_items(
                query=query,
                parameters=parameters,
                partition_key=str(dataset_id)
            ):
                items.append(item)
            
            return [DataPoint(**item) for item in items]
            
        except Exception as e:
            self.logger.error(f"Error listing data points: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to list data points: {str(e)}"
            )
    
    async def create_batch_datapoints(
        self, 
        dataset_id: UUID, 
        datapoints: List[Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Create multiple data points in batch
        
        Args:
            dataset_id: ID of the dataset
            datapoints: List of data point data dictionaries
            
        Returns:
            Dictionary with operation results
        """
        # Ensure Cosmos DB is initialized
        if not await self.initialize_cosmos_db():
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Database connection not available"
            )
        
        try:
            # Check if dataset exists
            dataset = await self.get_dataset(dataset_id)
            if not dataset:
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail="Dataset not found"
                )
            
            # Process each data point
            created_points = []
            failures = []
            
            for dp_data in datapoints:
                try:
                    # Create DataPointCreate instance
                    dp_create = DataPointCreate(
                        dataset_id=str(dataset_id),
                        timestamp=dp_data.get("timestamp"),
                        dimension=dp_data.get("dimension", {}),
                        metrics=dp_data.get("metrics", {})
                    )
                    
                    # Create the data point
                    datapoint = await self.create_datapoint(dp_create)
                    created_points.append(str(datapoint.id))
                except Exception as e:
                    failures.append({
                        "data": dp_data,
                        "error": str(e)
                    })
            
            return {
                "success": True,
                "created_count": len(created_points),
                "created_ids": created_points,
                "failures": failures,
                "dataset_id": str(dataset_id)
            }
            
        except Exception as e:
            self.logger.error(f"Error creating batch data points: {str(e)}")
            raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail=f"Failed to create batch data points: {str(e)}"
            )
