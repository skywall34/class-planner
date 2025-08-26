import sqlite3
import aiosqlite
from typing import Optional
import os

DATABASE_PATH = "data/geneacademy.db"

def create_database():
    """Create database and all tables if they don't exist."""
    os.makedirs(os.path.dirname(DATABASE_PATH), exist_ok=True)
    
    conn = sqlite3.connect(DATABASE_PATH)
    cursor = conn.cursor()
    
    # Sessions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS sessions (
            id TEXT PRIMARY KEY,
            user_ip TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            status TEXT CHECK(status IN ('active', 'processing', 'completed', 'error'))
        )
    """)
    
    # Documents table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS documents (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            original_text TEXT,
            file_name TEXT,
            file_type TEXT,
            uploaded_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    # Generated content table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS generated_content (
            id TEXT PRIMARY KEY,
            document_id TEXT,
            content_type TEXT CHECK(content_type IN ('summary', 'ebook', 'revised')),
            duration TEXT CHECK(duration IN ('week', 'multi_week', 'semester')),
            content_markdown TEXT,
            version INTEGER DEFAULT 1,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            accuracy_score REAL,
            FOREIGN KEY (document_id) REFERENCES documents(id)
        )
    """)
    
    # Agent logs table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS agent_logs (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            session_id TEXT,
            agent_type TEXT,
            input_data TEXT,
            output_data TEXT,
            processing_time REAL,
            timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
        )
    """)
    
    # Revision history table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS revision_history (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            content_id TEXT,
            user_feedback TEXT,
            revised_content TEXT,
            revision_number INTEGER,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            FOREIGN KEY (content_id) REFERENCES generated_content(id)
        )
    """)
    
    conn.commit()
    conn.close()

async def get_database():
    """Get async database connection."""
    return await aiosqlite.connect(DATABASE_PATH)

class DatabaseManager:
    def __init__(self):
        self.db_path = DATABASE_PATH
    
    async def create_session(self, session_id: str, user_ip: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO sessions (id, user_ip, status) VALUES (?, ?, 'active')",
                (session_id, user_ip)
            )
            await db.commit()
    
    async def update_session_status(self, session_id: str, status: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE sessions SET status = ?, updated_at = CURRENT_TIMESTAMP WHERE id = ?",
                (status, session_id)
            )
            await db.commit()
    
    async def save_document(self, doc_id: str, session_id: str, text: str, filename: str, filetype: str):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO documents (id, session_id, original_text, file_name, file_type) VALUES (?, ?, ?, ?, ?)",
                (doc_id, session_id, text, filename, filetype)
            )
            await db.commit()
    
    async def save_generated_content(self, content_id: str, doc_id: str, content_type: str, 
                                   duration: str, content: str, accuracy_score: float = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO generated_content (id, document_id, content_type, duration, content_markdown, accuracy_score) VALUES (?, ?, ?, ?, ?, ?)",
                (content_id, doc_id, content_type, duration, content, accuracy_score)
            )
            await db.commit()
    
    async def log_agent_activity(self, session_id: str, agent_type: str, input_data: str, 
                               output_data: str, processing_time: float):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO agent_logs (session_id, agent_type, input_data, output_data, processing_time) VALUES (?, ?, ?, ?, ?)",
                (session_id, agent_type, input_data, output_data, processing_time)
            )
            await db.commit()
    
    async def get_session_status(self, session_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("SELECT status FROM sessions WHERE id = ?", (session_id,))
            result = await cursor.fetchone()
            return result[0] if result else None
    
    async def get_generated_content(self, session_id: str):
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT gc.content_markdown, gc.accuracy_score, gc.content_type, gc.duration
                FROM generated_content gc
                JOIN documents d ON gc.document_id = d.id
                WHERE d.session_id = ?
                ORDER BY gc.created_at DESC
                LIMIT 1
            """, (session_id,))
            result = await cursor.fetchone()
            if result:
                return {
                    'content': result[0],
                    'accuracy_score': result[1],
                    'content_type': result[2],
                    'duration': result[3]
                }
            return None