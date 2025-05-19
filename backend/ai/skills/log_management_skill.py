import os
import logging
import json
from typing import Optional, List, Dict, Any
from uuid import UUID
import semantic_kernel as sk
from semantic_kernel.skill_definition import sk_function
from azure.cosmos import CosmosClient, PartitionKey
from datetime import datetime

from ..models.subjective_input import (
    LogEntry, 
    LogEntryCreate, 
    LogEntryUpdate, 
    LogEntryTag,
    LogEntryType
)

class LogManagementSkill:
    """Semantic Kernel skill for managing CEO log entries in the database."""
    
    def __init__(self):
        self.logger = logging.getLogger("log_management_skill")
        self.setup_cosmos_db()
    
    def setup_cosmos_db(self):
        """Initialize Azure Cosmos DB connection"""
        try:
            # Get connection info from environment variables
            cosmos_endpoint = os.getenv("AZURE_COSMOS_ENDPOINT")
            cosmos_key = os.getenv("AZURE_COSMOS_KEY")
            cosmos_database = os.getenv("AZURE_COSMOS_DATABASE")
            
            # Initialize Cosmos client
            self.cosmos_client = CosmosClient(cosmos_endpoint, cosmos_key)
            self.database = self.cosmos_client.get_database_client(cosmos_database)
            
            # Get container
            self.log_container = self.database.get_container_client("log_entries")
            
            self.logger.info("Cosmos DB connection established for LogManagementSkill")
        except Exception as e:
            self.logger.error(f"Error setting up Cosmos DB for LogManagementSkill: {str(e)}")
            # Using in-memory storage as fallback for development
            self.log_entries = []
            self.logger.warning("Using in-memory storage as fallback for LogManagementSkill")
    
    @sk_function(
        description="Create a new log entry in the database",
        name="create_log_entry"
    )
    async def create_log_entry(self, content: str, context: sk.SKContext) -> str:
        """Create a new CEO log entry in the database."""
        try:
            # Get parameters from context
            user_id = context.variables.get("user_id")
            entry_type = context.variables.get("entry_type", LogEntryType.OTHER.value)
            tags_json = context.variables.get("tags", "[]")
            
            # Parse tags
            tags_list = json.loads(tags_json)
            tags = []
            for tag_data in tags_list:
                if isinstance(tag_data, dict):
                    # Handle tag objects with additional metadata
                    tag_type = tag_data.get("type", "custom")
                    reference_id = tag_data.get("reference_id")
                    if reference_id:
                        reference_id = UUID(reference_id)
                    
                    tags.append(LogEntryTag(
                        name=tag_data["name"],
                        type=tag_type,
                        reference_id=reference_id
                    ))
                else:
                    # Handle simple tag strings
                    tags.append(LogEntryTag(
                        name=tag_data,
                        type="custom"
                    ))
            
            # Create new log entry
            entry = LogEntry(
                content=content,
                entry_type=LogEntryType(entry_type),
                tags=tags,
                user_id=UUID(user_id)
            )
            
            # Save to Cosmos DB
            if hasattr(self, 'log_container'):
                entry_dict = entry.dict()
                # Convert UUID to string for Cosmos
                entry_dict["id"] = str(entry.id)
                entry_dict["user_id"] = str(entry.user_id)
                for i, tag in enumerate(entry_dict["tags"]):
                    entry_dict["tags"][i]["id"] = str(tag["id"])
                    if tag["reference_id"]:
                        entry_dict["tags"][i]["reference_id"] = str(tag["reference_id"])
                
                await self.log_container.create_item(entry_dict)
            else:
                # Fallback to in-memory storage
                self.log_entries.append(entry)
                
            self.logger.info(f"Created log entry with ID: {entry.id}")
            return str(entry.id)
        except Exception as e:
            self.logger.error(f"Error creating log entry: {str(e)}")
            raise
    
    @sk_function(
        description="Get a log entry by ID",
        name="get_log_entry"
    )
    async def get_log_entry(self, entry_id: str) -> str:
        """Get a log entry by ID and return it as JSON."""
        try:
            if hasattr(self, 'log_container'):
                query = f"SELECT * FROM c WHERE c.id = '{entry_id}'"
                items = list(self.log_container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                
                if not items:
                    return "{}"
                
                # Return the entry as JSON
                return json.dumps(items[0])
            else:
                # Fallback to in-memory storage
                for entry in self.log_entries:
                    if str(entry.id) == entry_id:
                        # Convert to dict and handle UUID conversion
                        entry_dict = entry.dict()
                        entry_dict["id"] = str(entry.id)
                        entry_dict["user_id"] = str(entry.user_id)
                        for i, tag in enumerate(entry_dict["tags"]):
                            entry_dict["tags"][i]["id"] = str(tag["id"])
                            if tag["reference_id"]:
                                entry_dict["tags"][i]["reference_id"] = str(tag["reference_id"])
                        
                        return json.dumps(entry_dict)
                return "{}"
        except Exception as e:
            self.logger.error(f"Error getting log entry: {str(e)}")
            return "{}"
    
    @sk_function(
        description="Update a log entry with AI-generated results",
        name="update_log_entry_ai_results"
    )
    async def update_log_entry_ai_results(self, entry_id: str, context: sk.SKContext) -> str:
        """Update a log entry with AI-generated tags, summary, and insights."""
        try:
            # Get parameters from context
            ai_tags_json = context.variables.get("ai_tags", "[]")
            ai_summary = context.variables.get("ai_summary", "")
            ai_insights_json = context.variables.get("ai_insights", "[]")
            
            # Parse JSON arrays
            ai_tags = json.loads(ai_tags_json)
            ai_insights = json.loads(ai_insights_json)
            
            # Get the entry
            if hasattr(self, 'log_container'):
                query = f"SELECT * FROM c WHERE c.id = '{entry_id}'"
                items = list(self.log_container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                
                if not items:
                    return "false"
                
                # Get the entry and update it
                entry_dict = items[0]
                entry_dict["ai_generated_tags"] = ai_tags
                entry_dict["ai_summary"] = ai_summary
                entry_dict["ai_insights"] = ai_insights
                entry_dict["updated_at"] = datetime.now().isoformat()
                
                # Save back to Cosmos DB
                await self.log_container.replace_item(
                    item=entry_id,
                    body=entry_dict
                )
            else:
                # Fallback to in-memory storage
                for i, entry in enumerate(self.log_entries):
                    if str(entry.id) == entry_id:
                        self.log_entries[i].ai_generated_tags = ai_tags
                        self.log_entries[i].ai_summary = ai_summary
                        self.log_entries[i].ai_insights = ai_insights
                        self.log_entries[i].updated_at = datetime.now()
                        break
                else:
                    return "false"
            
            self.logger.info(f"Updated log entry AI results for ID: {entry_id}")
            return "true"
        except Exception as e:
            self.logger.error(f"Error updating log entry AI results: {str(e)}")
            return "false"
    
    @sk_function(
        description="List log entries for a user with optional filtering",
        name="list_log_entries"
    )
    async def list_log_entries(self, user_id: str, context: sk.SKContext) -> str:
        """List log entries for a user with optional filtering and pagination."""
        try:
            # Get optional parameters from context
            limit = int(context.variables.get("limit", "20"))
            offset = int(context.variables.get("offset", "0"))
            entry_type = context.variables.get("entry_type", None)
            tag = context.variables.get("tag", None)
            
            if hasattr(self, 'log_container'):
                # Build query based on filters
                query = f"SELECT * FROM c WHERE c.user_id = '{user_id}'"
                
                if entry_type:
                    query += f" AND c.entry_type = '{entry_type}'"
                
                if tag:
                    query += f" AND ARRAY_CONTAINS(c.tags, {{'name': '{tag}'}})"
                
                # Add sorting and pagination
                query += f" ORDER BY c.created_at DESC OFFSET {offset} LIMIT {limit}"
                
                items = list(self.log_container.query_items(
                    query=query,
                    enable_cross_partition_query=True
                ))
                
                # Return the entries as JSON
                return json.dumps(items)
            else:
                # Fallback to in-memory storage
                filtered_entries = [e for e in self.log_entries if str(e.user_id) == user_id]
                
                if entry_type:
                    filtered_entries = [e for e in filtered_entries if e.entry_type.value == entry_type]
                
                if tag:
                    filtered_entries = [e for e in filtered_entries if any(t.name == tag for t in e.tags)]
                
                # Sort by created_at descending
                filtered_entries.sort(key=lambda e: e.created_at, reverse=True)
                
                # Apply pagination
                paginated_entries = filtered_entries[offset:offset + limit]
                
                # Convert to dict and handle UUID conversion
                result = []
                for entry in paginated_entries:
                    entry_dict = entry.dict()
                    entry_dict["id"] = str(entry.id)
                    entry_dict["user_id"] = str(entry.user_id)
                    for i, tag in enumerate(entry_dict["tags"]):
                        entry_dict["tags"][i]["id"] = str(tag["id"])
                        if tag["reference_id"]:
                            entry_dict["tags"][i]["reference_id"] = str(tag["reference_id"])
                    
                    result.append(entry_dict)
                
                return json.dumps(result)
        except Exception as e:
            self.logger.error(f"Error listing log entries: {str(e)}")
            return "[]"