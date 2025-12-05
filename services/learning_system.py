#!/usr/bin/env python3
"""
Mommy AI Learning System
Allows Mommy AI to learn and absorb knowledge from Gemini and Ollama responses
to eventually become independent of external LLMs.

Architecture:
1. Response Capture: Store all LLM responses with context
2. Knowledge Refinement: Extract patterns and generalizations
3. Confidence Scoring: Track reliability of learned knowledge
4. Independence Tracking: Monitor how often local knowledge is used
5. Graduation System: Detect when Mommy AI can operate independently
"""

import json
import os
import sqlite3
from datetime import datetime
from typing import Dict, Any, List, Optional
import logging

logger = logging.getLogger(__name__)


class LearningSystem:
    """Manages Mommy AI's learning and knowledge absorption from LLMs."""

    def __init__(self, base_path: str = "services"):
        self.base_path = base_path
        self.db_path = os.path.join(base_path, "mommy_ai_learning.db")
        self.learned_knowledge_file = os.path.join(base_path, "learned_knowledge.json")
        self.independence_file = os.path.join(base_path, "independence_score.json")
        
        self._initialize_database()
        self._load_learned_knowledge()
        self._load_independence_score()
        
        logger.info("Learning system initialized")

    def _initialize_database(self):
        """Create or verify the learning database schema."""
        if not os.path.exists(self.db_path):
            logger.info(f"Creating learning database at {self.db_path}")
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Captured responses table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS captured_responses (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    user_query TEXT NOT NULL,
                    llm_response TEXT NOT NULL,
                    source_model TEXT NOT NULL,
                    user_name TEXT,
                    confidence REAL DEFAULT 0.5,
                    effectiveness_rating INTEGER DEFAULT 0,
                    learned BOOLEAN DEFAULT 0
                )
            """)
            
            # Learned facts table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS learned_facts (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    topic TEXT NOT NULL,
                    fact TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    frequency INTEGER DEFAULT 1,
                    learned_from TEXT,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP,
                    usage_count INTEGER DEFAULT 0
                )
            """)
            
            # Query patterns table (for generalizations)
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS query_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT NOT NULL,
                    response_template TEXT NOT NULL,
                    success_rate REAL DEFAULT 0.5,
                    usage_count INTEGER DEFAULT 0,
                    timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
                )
            """)
            
            # Independence metrics table
            cursor.execute("""
                CREATE TABLE IF NOT EXISTS independence_metrics (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    date DATE DEFAULT CURRENT_DATE,
                    queries_handled_locally INTEGER DEFAULT 0,
                    queries_needed_llm INTEGER DEFAULT 0,
                    gemini_calls INTEGER DEFAULT 0,
                    ollama_calls INTEGER DEFAULT 0,
                    average_confidence REAL DEFAULT 0.5
                )
            """)
            
            conn.commit()
            conn.close()
            logger.info("Learning database schema verified")
        except sqlite3.Error as e:
            logger.error(f"Error initializing learning database: {e}")

    def _load_learned_knowledge(self):
        """Load previously learned knowledge from file."""
        try:
            if os.path.exists(self.learned_knowledge_file):
                with open(self.learned_knowledge_file, 'r', encoding='utf-8') as f:
                    self.learned_knowledge = json.load(f)
                    logger.info(f"Loaded {len(self.learned_knowledge)} learned knowledge topics")
            else:
                self.learned_knowledge = {}
        except Exception as e:
            logger.error(f"Error loading learned knowledge: {e}")
            self.learned_knowledge = {}

    def _save_learned_knowledge(self):
        """Persist learned knowledge to file."""
        try:
            with open(self.learned_knowledge_file, 'w', encoding='utf-8') as f:
                json.dump(self.learned_knowledge, f, indent=2, ensure_ascii=False)
        except Exception as e:
            logger.error(f"Error saving learned knowledge: {e}")

    def _load_independence_score(self):
        """Load current independence score."""
        try:
            if os.path.exists(self.independence_file):
                with open(self.independence_file, 'r', encoding='utf-8') as f:
                    score_data = json.load(f)
                    self.independence_score = score_data.get("score", 0.0)
                    self.independence_level = score_data.get("level", "novice")
            else:
                self.independence_score = 0.0
                self.independence_level = "novice"
        except Exception as e:
            logger.error(f"Error loading independence score: {e}")
            self.independence_score = 0.0
            self.independence_level = "novice"

    def _save_independence_score(self):
        """Persist independence score."""
        try:
            with open(self.independence_file, 'w', encoding='utf-8') as f:
                json.dump({
                    "score": self.independence_score,
                    "level": self.independence_level,
                    "timestamp": datetime.now().isoformat()
                }, f, indent=2)
        except Exception as e:
            logger.error(f"Error saving independence score: {e}")

    def capture_response(self, user_query: str, llm_response: str, source_model: str, 
                        user_name: str = "unknown") -> int:
        """
        Capture and store an LLM response for learning.
        
        Args:
            user_query: The user's question
            llm_response: The LLM's response
            source_model: Which model provided the response (gemini/ollama)
            user_name: Who asked the question
        
        Returns:
            The ID of the captured response
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO captured_responses 
                (user_query, llm_response, source_model, user_name)
                VALUES (?, ?, ?, ?)
            """, (user_query, llm_response, source_model, user_name))
            
            conn.commit()
            response_id = cursor.lastrowid
            conn.close()
            
            logger.info(f"Captured response #{response_id} from {source_model}")
            return response_id
        except sqlite3.Error as e:
            logger.error(f"Error capturing response: {e}")
            return -1

    def extract_knowledge(self, response_id: int, user_query: str, llm_response: str) -> Dict[str, Any]:
        """
        Extract learnable facts from an LLM response.
        Break down responses into digestible knowledge units.
        
        Returns: Dict of extracted facts and patterns
        """
        extracted = {
            "facts": [],
            "patterns": [],
            "topics": []
        }
        
        try:
            # Simple topic extraction (in production, use NLP)
            response_lower = llm_response.lower()
            query_lower = user_query.lower()
            
            # Extract main topics from query
            common_topics = [
                "rules", "discipline", "behavior", "emotion", "comfort", "reward",
                "consequence", "support", "care", "love", "trust", "safety"
            ]
            
            found_topics = [t for t in common_topics if t in query_lower or t in response_lower]
            extracted["topics"] = found_topics
            
            # Store extracted knowledge
            for topic in found_topics:
                if topic not in self.learned_knowledge:
                    self.learned_knowledge[topic] = {
                        "facts": [],
                        "confidence": 0.3,
                        "sources": []
                    }
                
                # Add response as a fact
                self.learned_knowledge[topic]["facts"].append({
                    "query": user_query,
                    "response": llm_response[:500],  # Store first 500 chars
                    "timestamp": datetime.now().isoformat()
                })
                
                # Increase confidence based on repeated exposure
                self.learned_knowledge[topic]["confidence"] = min(
                    1.0,
                    self.learned_knowledge[topic]["confidence"] + 0.1
                )
                
                if "gemini" not in self.learned_knowledge[topic]["sources"]:
                    self.learned_knowledge[topic]["sources"].append("gemini")
            
            self._save_learned_knowledge()
            logger.info(f"Extracted knowledge on topics: {found_topics}")
            
        except Exception as e:
            logger.error(f"Error extracting knowledge: {e}")
        
        return extracted

    def record_learned_fact(self, topic: str, fact: str, source_model: str, confidence: float = 0.5) -> bool:
        """
        Record a specific fact that Mommy AI has learned.
        
        Args:
            topic: What the fact is about
            fact: The actual fact
            source_model: Which LLM provided it
            confidence: How confident we are (0.0 to 1.0)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            cursor.execute("""
                INSERT INTO learned_facts (topic, fact, learned_from, confidence)
                VALUES (?, ?, ?, ?)
            """, (topic, fact, source_model, confidence))
            
            conn.commit()
            conn.close()
            
            logger.info(f"Recorded fact on {topic} with {confidence:.2%} confidence")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error recording learned fact: {e}")
            return False

    def record_query_pattern(self, pattern: str, response_template: str, success: bool) -> bool:
        """
        Record a query pattern that Mommy AI has learned to handle.
        
        Args:
            pattern: The query pattern (e.g., "greeting", "emotional_support")
            response_template: The response template for this pattern
            success: Whether the response was well-received
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Check if pattern exists
            cursor.execute("SELECT id, success_rate, usage_count FROM query_patterns WHERE pattern = ?", (pattern,))
            result = cursor.fetchone()
            
            if result:
                pattern_id, old_success_rate, usage_count = result
                new_usage_count = usage_count + 1
                new_success_rate = (old_success_rate * usage_count + (1.0 if success else 0.0)) / new_usage_count
                
                cursor.execute("""
                    UPDATE query_patterns 
                    SET success_rate = ?, usage_count = ?
                    WHERE id = ?
                """, (new_success_rate, new_usage_count, pattern_id))
            else:
                success_rate = 1.0 if success else 0.0
                cursor.execute("""
                    INSERT INTO query_patterns (pattern, response_template, success_rate, usage_count)
                    VALUES (?, ?, ?, ?)
                """, (pattern, response_template, success_rate, 1))
            
            conn.commit()
            conn.close()
            logger.info(f"Recorded pattern '{pattern}' with success={success}")
            return True
        except sqlite3.Error as e:
            logger.error(f"Error recording query pattern: {e}")
            return False

    def can_handle_locally(self, user_query: str, min_confidence: float = 0.6) -> tuple[bool, Optional[str]]:
        """
        Check if Mommy AI can handle a query with learned knowledge.
        
        Returns: (can_handle, response_or_template)
        """
        try:
            query_lower = user_query.lower()
            
            # Check learned facts
            for topic, data in self.learned_knowledge.items():
                if topic in query_lower and data["confidence"] >= min_confidence:
                    if data["facts"]:
                        # Return the most recent fact
                        most_recent_fact = data["facts"][-1]
                        return True, most_recent_fact["response"]
            
            # Check patterns
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            cursor.execute("""
                SELECT response_template, success_rate FROM query_patterns 
                WHERE success_rate >= ? 
                ORDER BY success_rate DESC 
                LIMIT 1
            """, (min_confidence,))
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                template, success_rate = result
                return True, template
            
            return False, None
        except Exception as e:
            logger.error(f"Error checking local handling capability: {e}")
            return False, None

    def update_independence_metrics(self, handled_locally: bool, llm_used: Optional[str] = None):
        """
        Track whether Mommy AI is becoming more independent.
        
        Args:
            handled_locally: Did Mommy AI handle the query with learned knowledge?
            llm_used: If not local, which LLM was used (gemini/ollama/None)
        """
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get or create today's metrics
            today = datetime.now().date().isoformat()
            cursor.execute("""
                SELECT id, queries_handled_locally, queries_needed_llm, average_confidence
                FROM independence_metrics
                WHERE date = ?
            """, (today,))
            
            result = cursor.fetchone()
            
            if result:
                metric_id, local_count, llm_count, avg_conf = result
                if handled_locally:
                    local_count += 1
                else:
                    llm_count += 1
                
                cursor.execute("""
                    UPDATE independence_metrics
                    SET queries_handled_locally = ?, queries_needed_llm = ?
                    WHERE id = ?
                """, (local_count, llm_count, metric_id))
            else:
                if handled_locally:
                    cursor.execute("""
                        INSERT INTO independence_metrics 
                        (date, queries_handled_locally, queries_needed_llm)
                        VALUES (?, ?, ?)
                    """, (today, 1, 0))
                else:
                    cursor.execute("""
                        INSERT INTO independence_metrics 
                        (date, queries_handled_locally, queries_needed_llm)
                        VALUES (?, ?, ?)
                    """, (today, 0, 1))
            
            conn.commit()
            conn.close()
            
            # Update independence score
            self._update_independence_score()
            
        except sqlite3.Error as e:
            logger.error(f"Error updating independence metrics: {e}")

    def _update_independence_score(self):
        """Calculate current independence score based on metrics."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Get last 7 days of metrics
            cursor.execute("""
                SELECT 
                    SUM(queries_handled_locally) as local,
                    SUM(queries_needed_llm) as llm
                FROM independence_metrics
                WHERE date >= date('now', '-7 days')
            """)
            
            result = cursor.fetchone()
            conn.close()
            
            if result:
                local, llm = result
                local = local or 0
                llm = llm or 0
                
                total = local + llm
                if total > 0:
                    self.independence_score = min(1.0, local / total)
                
                # Update level
                if self.independence_score < 0.2:
                    self.independence_level = "novice"
                elif self.independence_score < 0.4:
                    self.independence_level = "apprentice"
                elif self.independence_score < 0.6:
                    self.independence_level = "intermediate"
                elif self.independence_score < 0.8:
                    self.independence_level = "advanced"
                else:
                    self.independence_level = "independent"
                
                self._save_independence_score()
                logger.info(f"Independence score updated: {self.independence_score:.2%} ({self.independence_level})")
        
        except Exception as e:
            logger.error(f"Error updating independence score: {e}")

    def get_status_report(self) -> Dict[str, Any]:
        """Get a comprehensive status report on Mommy AI's learning."""
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Count captured responses
            cursor.execute("SELECT COUNT(*) FROM captured_responses")
            captured_count = cursor.fetchone()[0]
            
            # Count learned facts
            cursor.execute("SELECT COUNT(DISTINCT topic) FROM learned_facts")
            topics_learned = cursor.fetchone()[0]
            
            # Get patterns
            cursor.execute("SELECT COUNT(*) FROM query_patterns WHERE success_rate > 0.7")
            reliable_patterns = cursor.fetchone()[0]
            
            # Get today's metrics
            today = datetime.now().date().isoformat()
            cursor.execute("""
                SELECT queries_handled_locally, queries_needed_llm
                FROM independence_metrics
                WHERE date = ?
            """, (today,))
            
            today_result = cursor.fetchone()
            local_today = today_result[0] if today_result else 0
            llm_today = today_result[1] if today_result else 0
            
            conn.close()
            
            return {
                "independence_score": self.independence_score,
                "independence_level": self.independence_level,
                "total_responses_captured": captured_count,
                "topics_learned": topics_learned,
                "reliable_patterns": reliable_patterns,
                "queries_handled_locally_today": local_today,
                "queries_needed_llm_today": llm_today,
                "known_knowledge_topics": list(self.learned_knowledge.keys())
            }
        except Exception as e:
            logger.error(f"Error generating status report: {e}")
            return {}


if __name__ == "__main__":
    # Test the learning system
    learning = LearningSystem()
    
    # Simulate capturing a response
    response_id = learning.capture_response(
        "How should I comfort a sad person?",
        "Comfort requires empathy. Listen, validate their feelings, offer physical comfort if appropriate.",
        "gemini",
        "hailey"
    )
    
    # Extract knowledge from it
    knowledge = learning.extract_knowledge(
        response_id,
        "How should I comfort a sad person?",
        "Comfort requires empathy. Listen, validate their feelings, offer physical comfort if appropriate."
    )
    
    # Record a pattern
    learning.record_query_pattern(
        "comfort_request",
        "I understand you're feeling sad. Let me help you feel better.",
        success=True
    )
    
    # Update metrics
    learning.update_independence_metrics(handled_locally=False, llm_used="gemini")
    learning.update_independence_metrics(handled_locally=True, llm_used=None)
    learning.update_independence_metrics(handled_locally=True, llm_used=None)
    
    # Get status
    print(json.dumps(learning.get_status_report(), indent=2))
