"""
Analytics and AI content analysis utilities
"""
import os
import re
import json
import logging
from typing import List, Dict, Any
from openai import AzureOpenAI
from .models import AIAnalysisResult, SentimentType, CEOLogEntry

logger = logging.getLogger(__name__)

# Azure OpenAI client
_openai_client = None


def get_openai_client():
    """Get or create Azure OpenAI client"""
    global _openai_client
    
    if not _openai_client:
        endpoint = os.environ.get("AZURE_OPENAI_ENDPOINT")
        key = os.environ.get("AZURE_OPENAI_KEY")
        
        if endpoint and key:
            _openai_client = AzureOpenAI(
                azure_endpoint=endpoint,
                api_key=key,
                api_version="2024-02-15-preview"
            )
            logger.info("Azure OpenAI client initialized")
    
    return _openai_client


def analyze_content(content: str) -> AIAnalysisResult:
    """Analyze content using local rules (fallback when AI not available)"""
    words = content.lower().split()
    word_count = len(words)
    
    # Sentiment analysis
    positive_words = ["success", "achieve", "excellent", "great", "positive", "win", 
                     "breakthrough", "opportunity", "growth"]
    negative_words = ["concern", "worry", "issue", "problem", "fail", "loss", 
                     "difficult", "risk", "threat"]
    
    positive_count = sum(1 for word in words if word in positive_words)
    negative_count = sum(1 for word in words if word in negative_words)
    
    if positive_count > negative_count:
        sentiment = SentimentType.POSITIVE
        confidence = min(0.9, 0.5 + (positive_count / word_count))
    elif negative_count > positive_count:
        sentiment = SentimentType.NEGATIVE
        confidence = min(0.9, 0.5 + (negative_count / word_count))
    else:
        sentiment = SentimentType.NEUTRAL
        confidence = 0.5
    
    # Generate tags
    tag_keywords = {
        "strategy": ["strategic", "plan", "goal", "objective", "vision", "roadmap"],
        "risk": ["risk", "threat", "concern", "issue", "problem", "challenge"],
        "opportunity": ["opportunity", "potential", "growth", "expand", "possibility"],
        "team": ["team", "people", "staff", "employee", "culture", "talent"],
        "market": ["market", "customer", "client", "competitor", "industry"],
        "financial": ["revenue", "cost", "budget", "profit", "financial", "expense"],
        "innovation": ["innovation", "technology", "digital", "transform", "new", "ai"],
        "urgent": ["urgent", "immediate", "asap", "critical", "priority"]
    }
    
    generated_tags = []
    for tag, keywords in tag_keywords.items():
        if any(keyword in content.lower() for keyword in keywords):
            generated_tags.append(tag)
    
    # Generate summary (first 50 words or first 2 sentences)
    sentences = re.split(r'[.!?]+', content)
    sentences = [s.strip() for s in sentences if s.strip()]
    summary = sentences[0] if sentences else content
    if len(summary.split()) > 50:
        summary = ' '.join(summary.split()[:50]) + '...'
    
    # Extract themes
    themes = []
    if "strategy" in generated_tags:
        themes.append("Strategic Planning")
    if "risk" in generated_tags:
        themes.append("Risk Management")
    if "opportunity" in generated_tags:
        themes.append("Growth Opportunities")
    if "team" in generated_tags:
        themes.append("Team Development")
    if "innovation" in generated_tags:
        themes.append("Digital Transformation")
    
    # Extract action items and risks
    action_items = []
    risks = []
    opportunities = []
    
    for sentence in sentences[:5]:  # Check first 5 sentences
        sentence_lower = sentence.lower()
        if any(word in sentence_lower for word in ["need to", "must", "should", "will", "plan to"]):
            action_items.append(sentence)
        if any(word in sentence_lower for word in ["risk", "threat", "concern", "challenge"]):
            risks.append(sentence)
        if any(word in sentence_lower for word in ["opportunity", "potential", "growth", "expand"]):
            opportunities.append(sentence)
    
    # General insights
    insights = []
    if sentiment == SentimentType.POSITIVE and "opportunity" in generated_tags:
        insights.append("Positive outlook on growth opportunities identified")
    if sentiment == SentimentType.NEGATIVE and "risk" in generated_tags:
        insights.append("Risk concerns require immediate attention")
    if "urgent" in generated_tags:
        insights.append("Time-sensitive matters need prioritization")
    
    return AIAnalysisResult(
        sentiment=sentiment,
        confidence=confidence,
        summary=summary,
        generatedTags=generated_tags,
        themes=themes,
        insights=insights,
        actionItems=action_items[:5],
        risks=risks[:5],
        opportunities=opportunities[:5],
        isUrgent="urgent" in generated_tags
    )


def analyze_content_with_ai(content: str) -> AIAnalysisResult:
    """Analyze content using Azure OpenAI"""
    client = get_openai_client()
    
    if not client:
        # Fallback to local analysis
        return analyze_content(content)
    
    try:
        deployment = os.environ.get("AZURE_OPENAI_DEPLOYMENT", "gpt-4")
        
        response = client.chat.completions.create(
            model=deployment,
            messages=[
                {
                    "role": "system",
                    "content": """You are an AI assistant analyzing CEO log entries. Extract the following in JSON format:
                    - sentiment: "positive", "negative", or "neutral"
                    - confidence: number between 0 and 1
                    - summary: concise summary in 30-50 words
                    - generatedTags: array of relevant tags
                    - themes: array of strategic themes
                    - insights: array of key insights
                    - actionItems: array of action items mentioned
                    - risks: array of risks identified
                    - opportunities: array of opportunities mentioned
                    - isUrgent: boolean indicating if urgent action is needed"""
                },
                {
                    "role": "user",
                    "content": f'Analyze this CEO log entry: "{content}"'
                }
            ],
            temperature=0.3,
            max_tokens=1000,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return AIAnalysisResult(**result)
        
    except Exception as e:
        logger.error(f"AI analysis failed: {e}")
        # Fallback to local analysis
        return analyze_content(content)


def calculate_relevance(entry: dict, search_query: str = None) -> float:
    """Calculate relevance score for search results"""
    if not search_query:
        return 1.0
    
    score = 0.0
    query = search_query.lower()
    
    # Content match
    content = entry.get('logEntry', {}).get('content', '').lower()
    if query in content:
        score += 0.5
        # Bonus for exact phrase match
        if len(query.split()) > 1:
            score += 0.3
    
    # Summary match
    summary = entry.get('analysis', {}).get('summary', '').lower()
    if query in summary:
        score += 0.3
    
    # Tag match
    tags = entry.get('tags', [])
    matching_tags = [tag for tag in tags if query in tag.lower() or tag.lower() in query]
    score += len(matching_tags) * 0.2
    
    # Theme match
    themes = entry.get('strategicThemes', [])
    matching_themes = [theme for theme in themes if query in theme.lower() or theme.lower() in query]
    score += len(matching_themes) * 0.15
    
    # Recency boost (entries from last 7 days)
    from datetime import datetime, timedelta
    try:
        entry_date = datetime.fromisoformat(entry.get('timestamp', '').replace('Z', '+00:00'))
        if datetime.utcnow() - entry_date < timedelta(days=7):
            score += 0.1
    except:
        pass
    
    # Importance boost
    if entry.get('analysis', {}).get('isUrgent', False):
        score += 0.15
    if entry.get('analysis', {}).get('hasActionItems', False):
        score += 0.1
    
    return min(1.0, score)