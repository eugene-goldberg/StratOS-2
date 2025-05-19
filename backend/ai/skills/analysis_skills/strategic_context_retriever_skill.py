import json
import re
from typing import List, Dict, Any, Optional
from semantic_kernel.skill_definition import sk_function, sk_function_context_parameter

class StrategicContextRetrieverSkill:
    """
    Semantic Kernel skill for retrieving strategic context for SWOT/TOWS analysis
    by fetching relevant subjective and objective data from various data sources
    """
    
    @sk_function(
        description="Fetches relevant subjective notes from CEO's Log",
        name="fetch_relevant_subjective_notes"
    )
    async def fetch_relevant_subjective_notes(self, topic: str, context) -> str:
        """
        Fetches relevant subjective notes from the CEO's Log related to the analysis topic
        using semantic search via Azure AI Search
        """
        try:
            from ..kernel_service import kernel_service
            
            if not topic:
                return "Error: No topic provided for subjective context search."
            
            # Define the collection to search in
            collection = "ceo_log_entries"
            
            # Search for log entries relevant to the topic
            results = await kernel_service.recall(collection, topic, limit=5)
            
            # If no results found, try a more general search with related keywords
            if not results:
                # Generate related keywords for the search
                fallback_keywords = self._generate_related_keywords(topic)
                
                # Try searching with each fallback keyword
                for keyword in fallback_keywords:
                    fallback_results = await kernel_service.recall(collection, keyword, limit=3)
                    if fallback_results:
                        results.extend(fallback_results)
                
                # If still no results, return a helpful message
                if not results:
                    return f"No relevant CEO's Log entries found for '{topic}'. Consider adding log entries related to this topic to provide better context for the analysis."
            
            # Process and format the results
            formatted_snippets = []
            for i, entry in enumerate(results, 1):
                # Extract metadata
                metadata = entry.metadata or {}
                date = metadata.get("date", "Unknown date")
                title = metadata.get("title", f"Log Entry {i}")
                
                # Extract and format content
                content = entry.text
                
                # For long content, extract the most relevant sentences (up to 3)
                if len(content) > 300:
                    content = self._extract_relevant_sentences(content, topic, max_sentences=3)
                
                # Format the snippet
                snippet = f"Date: {date}\nTitle: {title}\nContent: {content}"
                formatted_snippets.append(snippet)
            
            # Join all snippets with a separator
            return "\n\n".join(formatted_snippets)
        except Exception as e:
            return f"Error retrieving subjective context: {str(e)}"
    
    @sk_function(
        description="Fetches relevant objective data from business metrics",
        name="fetch_relevant_objective_data"
    )
    async def fetch_relevant_objective_data(self, topic: str, context) -> str:
        """
        Fetches relevant objective data from business metrics, KPIs, and documents
        related to the analysis topic
        """
        try:
            from ..kernel_service import kernel_service
            
            if not topic:
                return "Error: No topic provided for objective data search."
            
            # Try multiple data sources in order of specificity
            
            # 1. Try to get KPIs from the database
            kpi_data = await self._fetch_relevant_kpis(topic, kernel_service)
            
            # 2. Try to get relevant datasets and their key findings
            dataset_data = await self._fetch_relevant_datasets(topic, kernel_service)
            
            # 3. Try to get relevant business documents
            document_data = await self._fetch_relevant_documents(topic, kernel_service)
            
            # Combine all data sources
            all_data = []
            
            if kpi_data:
                all_data.append("Key Performance Indicators:")
                all_data.append(kpi_data)
            
            if dataset_data:
                all_data.append("Business Data Insights:")
                all_data.append(dataset_data)
            
            if document_data:
                all_data.append("From Business Documents:")
                all_data.append(document_data)
            
            # If no data was found from any source, provide a fallback with industry benchmarks
            if not all_data:
                fallback_data = await self._generate_industry_benchmarks(topic, kernel_service)
                if fallback_data:
                    all_data.append("Industry Benchmarks (for reference):")
                    all_data.append(fallback_data)
                else:
                    return f"No relevant objective data found for '{topic}'. Consider uploading business documents or KPIs related to this topic to provide better context for the analysis."
            
            # Combine all data with proper formatting
            return "\n\n".join(all_data)
        except Exception as e:
            return f"Error retrieving objective data: {str(e)}"
    
    async def _fetch_relevant_kpis(self, topic: str, kernel_service) -> Optional[str]:
        """Fetch relevant KPIs from the database related to the topic"""
        try:
            # Search for KPIs in memory or database
            collection = "business_kpis"
            kpi_results = await kernel_service.recall(collection, topic, limit=3)
            
            if not kpi_results:
                return None
            
            # Format KPI results
            kpi_items = []
            for kpi in kpi_results:
                metadata = kpi.metadata or {}
                name = metadata.get("name", "KPI")
                value = metadata.get("value", "N/A")
                trend = metadata.get("trend", "")
                
                kpi_item = f"- {name}: {value}" + (f" ({trend})" if trend else "")
                kpi_items.append(kpi_item)
            
            return "\n".join(kpi_items)
        except Exception:
            return None
    
    async def _fetch_relevant_datasets(self, topic: str, kernel_service) -> Optional[str]:
        """Fetch relevant datasets and their findings related to the topic"""
        try:
            # Search for datasets in memory
            collection = "business_datasets"
            dataset_results = await kernel_service.recall(collection, topic, limit=2)
            
            if not dataset_results:
                return None
            
            # Format dataset results
            dataset_items = []
            for dataset in dataset_results:
                metadata = dataset.metadata or {}
                name = metadata.get("name", "Dataset")
                key_finding = dataset.text
                
                if len(key_finding) > 200:
                    key_finding = self._extract_relevant_sentences(key_finding, topic, max_sentences=2)
                
                dataset_items.append(f"- {name}: {key_finding}")
            
            return "\n".join(dataset_items)
        except Exception:
            return None
    
    async def _fetch_relevant_documents(self, topic: str, kernel_service) -> Optional[str]:
        """Fetch relevant business documents related to the topic"""
        try:
            # Search for documents in memory
            collection = "business_documents"
            document_results = await kernel_service.recall(collection, topic, limit=2)
            
            if not document_results:
                return None
            
            # Format document results
            document_items = []
            for document in document_results:
                metadata = document.metadata or {}
                title = metadata.get("title", "Document")
                excerpt = document.text
                
                if len(excerpt) > 200:
                    excerpt = self._extract_relevant_sentences(excerpt, topic, max_sentences=2)
                
                document_items.append(f"- From {title}: {excerpt}")
            
            return "\n".join(document_items)
        except Exception:
            return None
    
    async def _generate_industry_benchmarks(self, topic: str, kernel_service) -> Optional[str]:
        """Generate industry benchmarks as a fallback when no objective data is found"""
        try:
            # Use LLM to generate relevant industry benchmarks
            prompt = f"""Generate 3-4 realistic industry benchmarks or metrics relevant to the topic: "{topic}".
            Format each as a bullet point with:
            - The name of the metric
            - A realistic value
            - Brief context about the benchmark (1 sentence)
            
            Each benchmark should be business-oriented and helpful for a SWOT analysis.
            """
            
            result = await kernel_service.generate_completion(prompt, max_tokens=200)
            
            # Clean up the result to ensure it's properly formatted
            lines = result.strip().split("\n")
            benchmarks = [line for line in lines if line.strip() and line.strip().startswith("-")]
            
            if not benchmarks:
                # Try to parse differently if we didn't get the expected format
                benchmarks = [f"- {line.strip()}" for line in lines if line.strip()]
            
            if not benchmarks:
                return None
            
            # Add a disclaimer
            disclaimer = "Note: These are general industry benchmarks that may help provide context. For more specific data, consider uploading relevant business documents."
            return "\n".join(benchmarks) + f"\n\n{disclaimer}"
        except Exception:
            return None
    
    def _generate_related_keywords(self, topic: str) -> List[str]:
        """Generate related keywords for fallback searches"""
        # Split the topic into words
        words = re.findall(r'\w+', topic.lower())
        
        # Filter out common stopwords
        stopwords = {'the', 'and', 'or', 'of', 'to', 'in', 'for', 'on', 'with', 'as', 'at', 'by'}
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        
        # Return the main keywords and some business-related terms
        business_terms = ["strategy", "market", "growth", "performance", "revenue"]
        
        # Combine original keywords with business terms
        return keywords + [f"{k} {term}" for k in keywords[:2] for term in business_terms[:3]]
    
    def _extract_relevant_sentences(self, text: str, topic: str, max_sentences: int = 3) -> str:
        """Extract the most relevant sentences from a longer text based on keyword matching"""
        # Split the text into sentences
        sentences = re.split(r'(?<=[.!?])\s+', text)
        
        # Generate keywords from the topic
        topic_words = set(re.findall(r'\w+', topic.lower()))
        
        # Score sentences based on keyword matches
        sentence_scores = []
        for sentence in sentences:
            sentence_words = set(re.findall(r'\w+', sentence.lower()))
            score = len(topic_words.intersection(sentence_words))
            sentence_scores.append((sentence, score))
        
        # Sort sentences by score (descending)
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        
        # Get the top sentences
        top_sentences = [s[0] for s in sentence_scores[:max_sentences]]
        
        # Ensure we maintain the original order of sentences for coherence
        ordered_top_sentences = [s for s in sentences if s in top_sentences]
        
        return " ".join(ordered_top_sentences)