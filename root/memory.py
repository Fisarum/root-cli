import sqlite3
import json
import hashlib
import time
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from dataclasses import dataclass, asdict

MEMORY_DIR = Path.home() / ".root"
MEMORY_DB = MEMORY_DIR / "memory.db"


@dataclass
class CommandHistory:
    """Stores command execution history with context and outcomes."""
    query: str
    command: str
    context: dict
    success: bool
    execution_time: float
    timestamp: float
    user_edited: bool = False
    risk_level: str = "safe"  # safe, moderate, dangerous


@dataclass
class UserPreference:
    """Stores learned user preferences."""
    pattern: str
    preference: dict
    confidence: float
    usage_count: int
    last_updated: float


@dataclass
class LearnedPattern:
    """Stores learned command patterns."""
    query_pattern: str
    command_template: str
    success_rate: float
    usage_count: int
    context_requirements: dict


class MemoryManager:
    """Manages persistent memory and learning for the Root CLI agent."""
    
    def __init__(self):
        self._init_db()
    
    def _init_db(self):
        """Initialize SQLite database with required tables."""
        MEMORY_DIR.mkdir(exist_ok=True)
        
        with sqlite3.connect(MEMORY_DB) as conn:
            conn.executescript("""
                CREATE TABLE IF NOT EXISTS command_history (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query TEXT NOT NULL,
                    command TEXT NOT NULL,
                    context TEXT NOT NULL,
                    success BOOLEAN NOT NULL,
                    execution_time REAL NOT NULL,
                    timestamp REAL NOT NULL,
                    user_edited BOOLEAN DEFAULT FALSE,
                    risk_level TEXT DEFAULT 'safe',
                    query_hash TEXT UNIQUE,
                    command_hash TEXT
                );
                
                CREATE TABLE IF NOT EXISTS user_preferences (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    pattern TEXT NOT NULL UNIQUE,
                    preference TEXT NOT NULL,
                    confidence REAL DEFAULT 0.5,
                    usage_count INTEGER DEFAULT 1,
                    last_updated REAL NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS learned_patterns (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    query_pattern TEXT NOT NULL UNIQUE,
                    command_template TEXT NOT NULL,
                    success_rate REAL DEFAULT 0.5,
                    usage_count INTEGER DEFAULT 1,
                    context_requirements TEXT,
                    created_at REAL NOT NULL,
                    last_used REAL NOT NULL
                );
                
                CREATE TABLE IF NOT EXISTS session_stats (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    session_start REAL NOT NULL,
                    commands_executed INTEGER DEFAULT 0,
                    commands_successful INTEGER DEFAULT 0,
                    user_corrections INTEGER DEFAULT 0,
                    mode TEXT DEFAULT 'cautious'
                );
                
                CREATE INDEX IF NOT EXISTS idx_query_hash ON command_history(query_hash);
                CREATE INDEX IF NOT EXISTS idx_timestamp ON command_history(timestamp);
                CREATE INDEX IF NOT EXISTS idx_pattern ON user_preferences(pattern);
            """)
    
    def store_command(self, history: CommandHistory) -> None:
        """Store a command execution in memory."""
        query_hash = self._hash_string(history.query)
        command_hash = self._hash_string(history.command)
        
        with sqlite3.connect(MEMORY_DB) as conn:
            conn.execute("""
                INSERT OR REPLACE INTO command_history 
                (query, command, context, success, execution_time, timestamp, 
                 user_edited, risk_level, query_hash, command_hash)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """, (
                history.query, history.command, json.dumps(history.context),
                history.success, history.execution_time, history.timestamp,
                history.user_edited, history.risk_level, query_hash, command_hash
            ))
    
    def get_similar_commands(self, query: str, limit: int = 5) -> List[CommandHistory]:
        """Find similar commands from history based on query similarity."""
        query_hash = self._hash_string(query)
        
        with sqlite3.connect(MEMORY_DB) as conn:
            cursor = conn.execute("""
                SELECT query, command, context, success, execution_time, 
                       timestamp, user_edited, risk_level
                FROM command_history 
                WHERE query_hash = ? OR (
                    length(query) - length(replace(lower(query), lower(?), '')) > 0
                )
                ORDER BY timestamp DESC, success DESC
                LIMIT ?
            """, (query_hash, query, limit))
            
            results = []
            for row in cursor.fetchall():
                results.append(CommandHistory(
                    query=row[0],
                    command=row[1],
                    context=json.loads(row[2]),
                    success=bool(row[3]),
                    execution_time=row[4],
                    timestamp=row[5],
                    user_edited=bool(row[6]),
                    risk_level=row[7]
                ))
            return results
    
    def learn_preference(self, pattern: str, preference: dict) -> None:
        """Learn or update a user preference."""
        with sqlite3.connect(MEMORY_DB) as conn:
            cursor = conn.execute("""
                SELECT confidence, usage_count FROM user_preferences 
                WHERE pattern = ?
            """, (pattern,))
            
            existing = cursor.fetchone()
            current_time = time.time()
            
            if existing:
                confidence, count = existing
                # Update confidence using weighted average
                new_confidence = (confidence * count + 1.0) / (count + 1)
                new_count = count + 1
                
                conn.execute("""
                    UPDATE user_preferences 
                    SET preference = ?, confidence = ?, usage_count = ?, last_updated = ?
                    WHERE pattern = ?
                """, (json.dumps(preference), new_confidence, new_count, current_time, pattern))
            else:
                conn.execute("""
                    INSERT INTO user_preferences 
                    (pattern, preference, confidence, usage_count, last_updated)
                    VALUES (?, ?, ?, ?, ?)
                """, (pattern, json.dumps(preference), 1.0, 1, current_time))
    
    def get_preference(self, pattern: str) -> Optional[UserPreference]:
        """Get a learned user preference."""
        with sqlite3.connect(MEMORY_DB) as conn:
            cursor = conn.execute("""
                SELECT pattern, preference, confidence, usage_count, last_updated
                FROM user_preferences 
                WHERE pattern = ?
            """, (pattern,))
            
            row = cursor.fetchone()
            if row:
                return UserPreference(
                    pattern=row[0],
                    preference=json.loads(row[1]),
                    confidence=row[2],
                    usage_count=row[3],
                    last_updated=row[4]
                )
            return None
    
    def learn_pattern(self, query_pattern: str, command_template: str, 
                     success: bool, context_requirements: dict = None) -> None:
        """Learn a successful command pattern."""
        current_time = time.time()
        
        with sqlite3.connect(MEMORY_DB) as conn:
            cursor = conn.execute("""
                SELECT success_rate, usage_count FROM learned_patterns 
                WHERE query_pattern = ?
            """, (query_pattern,))
            
            existing = cursor.fetchone()
            
            if existing:
                current_rate, count = existing
                # Update success rate using weighted average
                new_success = (current_rate * count + (1.0 if success else 0.0)) / (count + 1)
                new_count = count + 1
                
                conn.execute("""
                    UPDATE learned_patterns 
                    SET command_template = ?, success_rate = ?, usage_count = ?, 
                        last_used = ?, context_requirements = ?
                    WHERE query_pattern = ?
                """, (command_template, new_success, new_count, current_time,
                      json.dumps(context_requirements or {}), query_pattern))
            else:
                conn.execute("""
                    INSERT INTO learned_patterns 
                    (query_pattern, command_template, success_rate, usage_count, 
                     context_requirements, created_at, last_used)
                    VALUES (?, ?, ?, ?, ?, ?, ?)
                """, (query_pattern, command_template, 1.0 if success else 0.0, 1,
                      json.dumps(context_requirements or {}), current_time, current_time))
    
    def get_best_pattern(self, query: str, context: dict) -> Optional[LearnedPattern]:
        """Get the best matching learned pattern for a query."""
        with sqlite3.connect(MEMORY_DB) as conn:
            cursor = conn.execute("""
                SELECT query_pattern, command_template, success_rate, usage_count, 
                       context_requirements, last_used
                FROM learned_patterns 
                WHERE success_rate > 0.7
                ORDER BY success_rate DESC, usage_count DESC, last_used DESC
                LIMIT 10
            """)
            
            best_match = None
            best_score = 0.0
            
            for row in cursor.fetchall():
                pattern = row[0]
                # Simple pattern matching - can be enhanced with NLP
                if self._pattern_matches(pattern, query):
                    score = row[2] * (1 + row[3] * 0.1)  # success_rate + usage_bonus
                    if score > best_score:
                        best_score = score
                        best_match = LearnedPattern(
                            query_pattern=row[0],
                            command_template=row[1],
                            success_rate=row[2],
                            usage_count=row[3],
                            context_requirements=json.loads(row[4])
                        )
            
            return best_match
    
    def start_session(self, mode: str = "cautious") -> int:
        """Start a new session and return session ID."""
        current_time = time.time()
        
        with sqlite3.connect(MEMORY_DB) as conn:
            cursor = conn.execute("""
                INSERT INTO session_stats (session_start, mode)
                VALUES (?, ?)
            """, (current_time, mode))
            return cursor.lastrowid
    
    def update_session_stats(self, session_id: int, successful: bool = False, 
                           user_correction: bool = False) -> None:
        """Update session statistics."""
        with sqlite3.connect(MEMORY_DB) as conn:
            if successful:
                conn.execute("""
                    UPDATE session_stats 
                    SET commands_executed = commands_executed + 1,
                        commands_successful = commands_successful + 1
                    WHERE id = ?
                """, (session_id,))
            else:
                conn.execute("""
                    UPDATE session_stats 
                    SET commands_executed = commands_executed + 1
                    WHERE id = ?
                """, (session_id,))
            
            if user_correction:
                conn.execute("""
                    UPDATE session_stats 
                    SET user_corrections = user_corrections + 1
                    WHERE id = ?
                """, (session_id,))
    
    def get_session_summary(self, session_id: int) -> dict:
        """Get summary statistics for a session."""
        with sqlite3.connect(MEMORY_DB) as conn:
            cursor = conn.execute("""
                SELECT session_start, commands_executed, commands_successful, 
                       user_corrections, mode
                FROM session_stats 
                WHERE id = ?
            """, (session_id,))
            
            row = cursor.fetchone()
            if row:
                return {
                    "session_start": row[0],
                    "commands_executed": row[1],
                    "commands_successful": row[2],
                    "user_corrections": row[3],
                    "mode": row[4],
                    "success_rate": row[2] / max(row[1], 1)
                }
            return {}
    
    def _hash_string(self, text: str) -> str:
        """Create a consistent hash for a string."""
        return hashlib.sha256(text.encode()).hexdigest()[:16]
    
    def _pattern_matches(self, pattern: str, query: str) -> bool:
        """Simple pattern matching - can be enhanced."""
        pattern_words = set(pattern.lower().split())
        query_words = set(query.lower().split())
        
        # Check if at least 50% of pattern words are in query
        intersection = pattern_words & query_words
        return len(intersection) >= len(pattern_words) * 0.5


# Global memory manager instance
_memory_manager = None

def get_memory_manager() -> MemoryManager:
    """Get the global memory manager instance."""
    global _memory_manager
    if _memory_manager is None:
        _memory_manager = MemoryManager()
    return _memory_manager
