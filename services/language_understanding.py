"""
Language Understanding Module for Mommy AI
Handles intent recognition, entity extraction, sentiment analysis, and NLP preprocessing
"""

import re
import json
from collections import Counter
from typing import Dict, List, Tuple, Optional, Any
from dataclasses import dataclass, asdict
import sqlite3
from datetime import datetime


@dataclass
class Intent:
    """Represents a recognized intent from user input"""
    name: str
    confidence: float
    entities: Dict[str, Any]
    original_query: str
    processed_query: str


class LanguageUnderstanding:
    """
    Core language understanding engine for Mommy AI
    Provides NLP preprocessing, intent recognition, and entity extraction
    """

    def __init__(self, base_path: str = "."):
        """Initialize language understanding system"""
        self.base_path = base_path
        self.intent_patterns = self._initialize_intent_patterns()
        self.entity_extractors = self._initialize_entity_extractors()
        self.sentiment_words = self._initialize_sentiment_words()
        self.processed_queries = {}
        
        # Statistics tracking
        self.query_stats = {
            "total_queries": 0,
            "recognized_intents": 0,
            "extracted_entities": 0,
            "sentiment_detected": 0
        }

    def _initialize_intent_patterns(self) -> Dict[str, List[Tuple[str, float]]]:
        """
        Initialize intent recognition patterns
        Format: intent_name -> [(regex_pattern, confidence), ...]
        """
        return {
            "greeting": [
                (r"^(hello|hi|hey|greetings|good morning|good afternoon|good evening|howdy)", 0.95),
                (r"^how are you", 0.90),
            ],
            "question": [
                (r"^\s*\?", 0.85),
                (r"^(what|where|when|why|how|who|which)", 0.80),
                (r"^(can you|could you|would you|will you|do you)", 0.75),
            ],
            "statement": [
                (r"^(i|me|we|my|our)", 0.70),
                (r"\.$", 0.60),
            ],
            "command": [
                (r"^(please|tell me|show me|give me|do|make|create|send)", 0.85),
                (r"^(help|assist|support)", 0.80),
            ],
            "emotional": [
                (r"(sad|happy|angry|frustrated|excited|worried|scared|lonely)", 0.85),
                (r"(love|hate|adore|despise|like|dislike)", 0.80),
            ],
            "request_help": [
                (r"^(help|assist|support|need help|can you help)", 0.90),
                (r"(struggling|stuck|confused|don't know)", 0.85),
            ],
            "casual_chat": [
                (r"^(so|anyway|btw|by the way|you know)", 0.70),
                (r"(haha|lol|hehe)", 0.75),
            ],
            "goodbye": [
                (r"(bye|goodbye|see you|later|farewell|catch you)", 0.95),
                (r"^(talk to you later|talk later)", 0.90),
            ],
        }

    def _initialize_entity_extractors(self) -> Dict[str, callable]:
        """Initialize entity extraction functions"""
        return {
            "time_reference": self._extract_time_reference,
            "person_name": self._extract_person_name,
            "emotion": self._extract_emotion,
            "number": self._extract_number,
            "url": self._extract_url,
            "email": self._extract_email,
        }

    def _initialize_sentiment_words(self) -> Dict[str, Dict[str, List[str]]]:
        """Initialize sentiment lexicon"""
        return {
            "positive": {
                "high": ["love", "adore", "amazing", "wonderful", "fantastic", "excellent", "perfect"],
                "medium": ["good", "nice", "like", "enjoy", "great", "wonderful"],
                "low": ["okay", "fine", "alright", "decent", "acceptable"],
            },
            "negative": {
                "high": ["hate", "despise", "terrible", "awful", "horrible", "disgusting"],
                "medium": ["bad", "dislike", "annoying", "frustrating", "disappointing"],
                "low": ["meh", "eh", "not great", "lacking", "wanting"],
            },
        }

    def preprocess_query(self, query: str) -> str:
        """
        Preprocess raw user query
        - Normalize whitespace
        - Convert to lowercase for processing
        - Remove excessive punctuation
        """
        # Store original for reference
        processed = query.strip()
        
        # Normalize whitespace
        processed = re.sub(r'\s+', ' ', processed)
        
        # Keep original case info but work with lowercase for matching
        return processed

    def tokenize(self, query: str) -> List[str]:
        """Split query into tokens"""
        # Remove punctuation but keep words
        tokens = re.findall(r'\b\w+\b', query.lower())
        return tokens

    def remove_stopwords(self, tokens: List[str]) -> List[str]:
        """Remove common stopwords"""
        stopwords = {
            'the', 'a', 'an', 'and', 'or', 'but', 'in', 'on', 'at', 'to', 'for',
            'of', 'with', 'by', 'from', 'is', 'are', 'was', 'were', 'be', 'been',
            'have', 'has', 'had', 'do', 'does', 'did', 'will', 'would', 'could',
            'should', 'may', 'might', 'must', 'can', 'it', 'its', 'that', 'this'
        }
        return [token for token in tokens if token not in stopwords]

    def recognize_intent(self, query: str) -> Intent:
        """
        Recognize primary intent from user query
        Returns Intent object with confidence and entities
        """
        processed = self.preprocess_query(query)
        query_lower = processed.lower()
        
        best_intent = None
        best_confidence = 0.0
        
        # Match against intent patterns
        for intent_name, patterns in self.intent_patterns.items():
            for pattern, confidence in patterns:
                if re.search(pattern, query_lower, re.IGNORECASE):
                    if confidence > best_confidence:
                        best_intent = intent_name
                        best_confidence = confidence
        
        # Default to "statement" if no clear intent
        if best_intent is None:
            best_intent = "statement"
            best_confidence = 0.5
        
        # Extract entities
        entities = self._extract_entities(processed)
        
        intent = Intent(
            name=best_intent,
            confidence=best_confidence,
            entities=entities,
            original_query=query,
            processed_query=processed
        )
        
        self.query_stats["total_queries"] += 1
        self.query_stats["recognized_intents"] += 1
        
        return intent

    def _extract_entities(self, query: str) -> Dict[str, Any]:
        """Extract entities from query"""
        entities = {}
        
        for entity_type, extractor in self.entity_extractors.items():
            result = extractor(query)
            if result:
                entities[entity_type] = result
                self.query_stats["extracted_entities"] += 1
        
        return entities

    def _extract_time_reference(self, query: str) -> Optional[Dict]:
        """Extract time references (today, tomorrow, next week, etc.)"""
        time_refs = {
            "today": r"\btoday\b",
            "tomorrow": r"\btomorrow\b",
            "yesterday": r"\byesterday\b",
            "tonight": r"\btonight\b",
            "this week": r"\bthis week\b",
            "next week": r"\bnext week\b",
            "later": r"\blater\b",
            "soon": r"\bsoon\b",
        }
        
        for time_type, pattern in time_refs.items():
            if re.search(pattern, query, re.IGNORECASE):
                return {"type": "time_reference", "value": time_type}
        
        return None

    def _extract_person_name(self, query: str) -> Optional[Dict]:
        """Extract person names (simple approach - capitalized words)"""
        # Look for capitalized words that aren't at sentence start
        tokens = query.split()
        names = []
        
        for i, token in enumerate(tokens):
            # Check if word is capitalized and not at start or common words
            if token and token[0].isupper() and i > 0 and token not in ['I', 'The', 'My']:
                # Remove punctuation
                clean_token = re.sub(r'[^\w]', '', token)
                if len(clean_token) > 1:
                    names.append(clean_token)
        
        if names:
            return {"type": "person_name", "values": names}
        return None

    def _extract_emotion(self, query: str) -> Optional[Dict]:
        """Extract emotional content"""
        query_lower = query.lower()
        emotions = []
        
        # Check emotion words
        emotion_keywords = {
            "sad": r"\b(sad|depressed|unhappy|down|blue|lonely)\b",
            "happy": r"\b(happy|cheerful|joyful|glad|excited|thrilled)\b",
            "angry": r"\b(angry|furious|mad|upset|annoyed)\b",
            "worried": r"\b(worried|anxious|nervous|scared|afraid)\b",
            "tired": r"\b(tired|exhausted|weary|fatigued)\b",
            "confused": r"\b(confused|lost|bewildered|puzzled)\b",
        }
        
        for emotion, pattern in emotion_keywords.items():
            if re.search(pattern, query_lower):
                emotions.append(emotion)
        
        if emotions:
            return {"type": "emotion", "values": emotions}
        return None

    def _extract_number(self, query: str) -> Optional[Dict]:
        """Extract numbers from query"""
        numbers = re.findall(r'\d+', query)
        if numbers:
            return {"type": "number", "values": [int(n) for n in numbers]}
        return None

    def _extract_url(self, query: str) -> Optional[Dict]:
        """Extract URLs from query"""
        urls = re.findall(r'https?://\S+', query)
        if urls:
            return {"type": "url", "values": urls}
        return None

    def _extract_email(self, query: str) -> Optional[Dict]:
        """Extract email addresses from query"""
        emails = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', query)
        if emails:
            return {"type": "email", "values": emails}
        return None

    def analyze_sentiment(self, query: str) -> Dict[str, Any]:
        """
        Analyze sentiment of query
        Returns: sentiment type (positive/negative/neutral) with confidence
        """
        query_lower = query.lower()
        tokens = self.tokenize(query)
        
        positive_score = 0.0
        negative_score = 0.0
        
        # Score positive words
        for level, words in self.sentiment_words["positive"].items():
            weight = {"high": 3.0, "medium": 2.0, "low": 1.0}[level]
            for word in words:
                if word in tokens:
                    positive_score += weight
        
        # Score negative words
        for level, words in self.sentiment_words["negative"].items():
            weight = {"high": 3.0, "medium": 2.0, "low": 1.0}[level]
            for word in words:
                if word in tokens:
                    negative_score += weight
        
        # Determine sentiment
        total = positive_score + negative_score
        if total == 0:
            sentiment = "neutral"
            confidence = 0.5
        elif positive_score > negative_score:
            sentiment = "positive"
            confidence = min(positive_score / total, 1.0)
        else:
            sentiment = "negative"
            confidence = min(negative_score / total, 1.0)
        
        if sentiment != "neutral":
            self.query_stats["sentiment_detected"] += 1
        
        return {
            "sentiment": sentiment,
            "confidence": confidence,
            "positive_score": positive_score,
            "negative_score": negative_score,
        }

    def extract_keywords(self, query: str) -> List[str]:
        """
        Extract important keywords from query
        Removes stopwords and returns meaningful tokens
        """
        tokens = self.tokenize(query)
        keywords = self.remove_stopwords(tokens)
        return keywords

    def get_query_summary(self, query: str) -> Dict[str, Any]:
        """
        Generate comprehensive summary of user query
        Combines all analysis: intent, entities, sentiment, keywords
        """
        intent = self.recognize_intent(query)
        sentiment = self.analyze_sentiment(query)
        keywords = self.extract_keywords(query)
        
        return {
            "original_query": query,
            "processed_query": intent.processed_query,
            "intent": {
                "name": intent.name,
                "confidence": intent.confidence,
            },
            "entities": intent.entities,
            "sentiment": sentiment,
            "keywords": keywords,
            "tokens_count": len(self.tokenize(query)),
            "extracted_count": len(intent.entities),
        }

    def suggest_response_style(self, query_summary: Dict) -> str:
        """
        Suggest response style based on query analysis
        Helps Mommy AI choose appropriate tone/style
        """
        intent = query_summary["intent"]["name"]
        sentiment = query_summary["sentiment"]["sentiment"]
        
        # Response style mapping
        style_map = {
            ("greeting", "neutral"): "friendly_and_warm",
            ("greeting", "positive"): "enthusiastic",
            ("question", "neutral"): "informative",
            ("question", "negative"): "empathetic_and_helpful",
            ("emotional", "positive"): "celebratory",
            ("emotional", "negative"): "supportive_and_caring",
            ("command", "neutral"): "helpful_and_efficient",
            ("request_help", "negative"): "compassionate_and_reassuring",
            ("casual_chat", "positive"): "playful_and_engaging",
            ("goodbye", "positive"): "warm_and_affectionate",
        }
        
        key = (intent, sentiment)
        return style_map.get(key, "balanced_and_thoughtful")

    def get_statistics(self) -> Dict[str, Any]:
        """Return language understanding statistics"""
        return {
            "total_queries_processed": self.query_stats["total_queries"],
            "intents_recognized": self.query_stats["recognized_intents"],
            "entities_extracted": self.query_stats["extracted_entities"],
            "sentiments_detected": self.query_stats["sentiment_detected"],
            "recognition_rate": (
                self.query_stats["recognized_intents"] / self.query_stats["total_queries"]
                if self.query_stats["total_queries"] > 0 else 0.0
            ),
        }

    def reset_statistics(self):
        """Reset all statistics"""
        self.query_stats = {
            "total_queries": 0,
            "recognized_intents": 0,
            "extracted_entities": 0,
            "sentiment_detected": 0
        }


# Example usage and testing
if __name__ == "__main__":
    lu = LanguageUnderstanding()
    
    # Test queries
    test_queries = [
        "Hello! How are you today?",
        "I'm feeling really sad and lonely",
        "Can you help me with my homework?",
        "That's amazing! I love this!",
        "What time is tomorrow?",
        "Bye! See you later!",
    ]
    
    print("=" * 60)
    print("LANGUAGE UNDERSTANDING MODULE - TEST RESULTS")
    print("=" * 60)
    
    for query in test_queries:
        print(f"\nQuery: {query}")
        summary = lu.get_query_summary(query)
        print(f"  Intent: {summary['intent']['name']} ({summary['intent']['confidence']:.2f})")
        print(f"  Sentiment: {summary['sentiment']['sentiment']} ({summary['sentiment']['confidence']:.2f})")
        print(f"  Keywords: {', '.join(summary['keywords'])}")
        print(f"  Entities: {summary['entities']}")
        style = lu.suggest_response_style(summary)
        print(f"  Suggested Style: {style}")
    
    print("\n" + "=" * 60)
    print("STATISTICS")
    print("=" * 60)
    stats = lu.get_statistics()
    for key, value in stats.items():
        print(f"{key}: {value}")
