import json
import re
from typing import List, Dict, Any, Optional
from semantic_kernel.functions import kernel_function # Updated import
# from semantic_kernel.orchestration.sk_context import SKContext # Old way

class StrategicContextRetrieverSkill:
    """
    Semantic Kernel skill for retrieving strategic context for SWOT/TOWS analysis
    by fetching relevant subjective and objective data from various data sources.
    """
    
    @kernel_function(
        description="Fetches relevant subjective notes from CEO's Log.",
        name="fetch_relevant_subjective_notes"
    )
    async def fetch_relevant_subjective_notes(
        self, 
        topic: str
        # context: SKContext # Old way
    ) -> str:
        """
        Fetches relevant subjective notes from the CEO's Log related to the analysis topic
        using semantic search via Azure AI Search.
        :param topic: The topic for which to fetch subjective notes.
        :return: A string containing formatted subjective notes or an error message.
        """
        try:
            from ..kernel_service import kernel_service # Local import
            
            if not topic:
                return "Error: No topic provided for subjective context search."
            
            collection = "ceo_log_entries"
            results = await kernel_service.recall(collection, topic, limit=5)
            
            if not results:
                fallback_keywords = self._generate_related_keywords(topic)
                for keyword in fallback_keywords:
                    fallback_results = await kernel_service.recall(collection, keyword, limit=3)
                    if fallback_results:
                        results.extend(fallback_results)
                if not results:
                    return f"No relevant CEO's Log entries found for '{topic}'. Consider adding log entries related to this topic."
            
            formatted_snippets = []
            for i, entry in enumerate(results, 1):
                metadata = entry.metadata or {} # Ensure metadata is not None
                date = metadata.get("date", "Unknown date")
                title = metadata.get("title", f"Log Entry {i}")
                content = entry.text
                
                if len(content) > 300:
                    content = self._extract_relevant_sentences(content, topic, max_sentences=3)
                
                snippet = f"Date: {date}\nTitle: {title}\nContent: {content}"
                formatted_snippets.append(snippet)
            
            return "\n\n".join(formatted_snippets)
        except Exception as e:
            # Log exception e
            return f"Error retrieving subjective context: {str(e)}"
    
    @kernel_function(
        description="Fetches relevant objective data from business metrics.",
        name="fetch_relevant_objective_data"
    )
    async def fetch_relevant_objective_data(
        self, 
        topic: str
        # context: SKContext # Old way
    ) -> str:
        """
        Fetches relevant objective data from business metrics, KPIs, and documents
        related to the analysis topic.
        :param topic: The topic for which to fetch objective data.
        :return: A string containing formatted objective data or an error message.
        """
        try:
            from ..kernel_service import kernel_service # Local import
            
            if not topic:
                return "Error: No topic provided for objective data search."
            
            kpi_data = await self._fetch_relevant_kpis(topic, kernel_service)
            dataset_data = await self._fetch_relevant_datasets(topic, kernel_service)
            document_data = await self._fetch_relevant_documents(topic, kernel_service)
            
            all_data_parts = []
            if kpi_data: all_data_parts.extend(["Key Performance Indicators:", kpi_data])
            if dataset_data: all_data_parts.extend(["Business Data Insights:", dataset_data])
            if document_data: all_data_parts.extend(["From Business Documents:", document_data])
            
            if not all_data_parts:
                fallback_data = await self._generate_industry_benchmarks(topic, kernel_service)
                if fallback_data:
                    all_data_parts.extend(["Industry Benchmarks (for reference):", fallback_data])
                else:
                    return f"No relevant objective data found for '{topic}'. Consider uploading relevant business documents or KPIs."
            
            return "\n\n".join(all_data_parts)
        except Exception as e:
            # Log exception e
            return f"Error retrieving objective data: {str(e)}"
    
    async def _fetch_relevant_kpis(self, topic: str, kernel_service) -> Optional[str]:
        try:
            collection = "business_kpis"
            kpi_results = await kernel_service.recall(collection, topic, limit=3)
            if not kpi_results: return None
            
            kpi_items = []
            for kpi in kpi_results:
                metadata = kpi.metadata or {}
                name = metadata.get("name", "KPI")
                value = metadata.get("value", "N/A")
                trend = metadata.get("trend", "")
                kpi_items.append(f"- {name}: {value}" + (f" ({trend})" if trend else ""))
            return "\n".join(kpi_items)
        except Exception: return None # Log exception
    
    async def _fetch_relevant_datasets(self, topic: str, kernel_service) -> Optional[str]:
        try:
            collection = "business_datasets"
            dataset_results = await kernel_service.recall(collection, topic, limit=2)
            if not dataset_results: return None
            
            dataset_items = []
            for dataset in dataset_results:
                metadata = dataset.metadata or {}
                name = metadata.get("name", "Dataset")
                key_finding = dataset.text
                if len(key_finding) > 200:
                    key_finding = self._extract_relevant_sentences(key_finding, topic, max_sentences=2)
                dataset_items.append(f"- {name}: {key_finding}")
            return "\n".join(dataset_items)
        except Exception: return None # Log exception

    async def _fetch_relevant_documents(self, topic: str, kernel_service) -> Optional[str]:
        try:
            collection = "business_documents"
            document_results = await kernel_service.recall(collection, topic, limit=2)
            if not document_results: return None
            
            document_items = []
            for document in document_results:
                metadata = document.metadata or {}
                title = metadata.get("title", "Document")
                excerpt = document.text
                if len(excerpt) > 200:
                    excerpt = self._extract_relevant_sentences(excerpt, topic, max_sentences=2)
                document_items.append(f"- From {title}: {excerpt}")
            return "\n".join(document_items)
        except Exception: return None # Log exception
    
    async def _generate_industry_benchmarks(self, topic: str, kernel_service) -> Optional[str]:
        try:
            prompt = f"""Generate 3-4 realistic industry benchmarks or metrics relevant to the topic: "{topic}".
            Format each as a bullet point with:
            - The name of the metric
            - A realistic value
            - Brief context about the benchmark (1 sentence)
            Each benchmark should be business-oriented and helpful for a SWOT analysis."""
            
            result_str = await kernel_service.generate_completion(prompt, max_tokens=200)
            if not result_str: return None # Check if generate_completion returns None or empty on failure

            lines = result_str.strip().split("\n")
            benchmarks = [line for line in lines if line.strip().startswith("-")]
            if not benchmarks: benchmarks = [f"- {line.strip()}" for line in lines if line.strip()] # Fallback parsing
            if not benchmarks: return None
            
            disclaimer = "Note: These are general industry benchmarks. For specific data, upload relevant documents."
            return "\n".join(benchmarks) + f"\n\n{disclaimer}"
        except Exception: return None # Log exception
    
    def _generate_related_keywords(self, topic: str) -> List[str]:
        words = re.findall(r'\w+', topic.lower())
        stopwords = {'the', 'and', 'or', 'of', 'to', 'in', 'for', 'on', 'with', 'as', 'at', 'by'}
        keywords = [w for w in words if w not in stopwords and len(w) > 2]
        business_terms = ["strategy", "market", "growth", "performance", "revenue"]
        # Ensure keywords list is not empty before list comprehension
        if not keywords: return business_terms # Or some other default
        return keywords + [f"{k} {term}" for k in keywords[:2] for term in business_terms[:3]]
    
    def _extract_relevant_sentences(self, text: str, topic: str, max_sentences: int = 3) -> str:
        sentences = re.split(r'(?<=[.!?])\s+', text)
        topic_words = set(re.findall(r'\w+', topic.lower()))
        if not topic_words: return " ".join(sentences[:max_sentences]) # Handle empty topic

        sentence_scores = []
        for sentence in sentences:
            sentence_words = set(re.findall(r'\w+', sentence.lower()))
            score = len(topic_words.intersection(sentence_words))
            sentence_scores.append((sentence, score))
        
        sentence_scores.sort(key=lambda x: x[1], reverse=True)
        top_scored_sentences = [s[0] for s in sentence_scores[:max_sentences]]
        
        # Maintain original order of the selected top sentences
        ordered_top_sentences = [s for s in sentences if s in top_scored_sentences]
        return " ".join(ordered_top_sentences)
