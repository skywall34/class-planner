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
    
    # Check if we need to migrate the generated_content table
    cursor.execute("PRAGMA table_info(generated_content)")
    columns = [column[1] for column in cursor.fetchall()]
    
    if 'duration' in columns and 'user_prompt' not in columns:
        # Need to migrate from duration to user_prompt
        print("Migrating database: renaming duration to user_prompt...")
        cursor.execute("ALTER TABLE generated_content RENAME TO generated_content_old")
        
        # Create new table with updated schema
        cursor.execute("""
            CREATE TABLE generated_content (
                id TEXT PRIMARY KEY,
                document_id TEXT,
                content_type TEXT CHECK(content_type IN ('summary', 'ebook', 'revised')),
                user_prompt TEXT,
                content_markdown TEXT,
                version INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accuracy_score REAL,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
        
        # Copy data from old table, setting empty user_prompt for existing records
        cursor.execute("""
            INSERT INTO generated_content (id, document_id, content_type, user_prompt, content_markdown, version, created_at, accuracy_score)
            SELECT id, document_id, content_type, 
                   '' as user_prompt,
                   content_markdown, version, created_at, accuracy_score
            FROM generated_content_old
        """)
        
        # Drop old table
        cursor.execute("DROP TABLE generated_content_old")
        print("Database migration completed.")
    elif 'generated_content' not in [table[0] for table in cursor.execute("SELECT name FROM sqlite_master WHERE type='table'").fetchall()]:
        # Table doesn't exist, create it with new schema
        cursor.execute("""
            CREATE TABLE generated_content (
                id TEXT PRIMARY KEY,
                document_id TEXT,
                content_type TEXT CHECK(content_type IN ('summary', 'ebook', 'revised')),
                user_prompt TEXT,
                content_markdown TEXT,
                version INTEGER DEFAULT 1,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                accuracy_score REAL,
                FOREIGN KEY (document_id) REFERENCES documents(id)
            )
        """)
    
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
    
    # Processing events table for SSE
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS processing_events (
            id TEXT PRIMARY KEY,
            session_id TEXT,
            event_type TEXT,
            event_data TEXT,
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            acknowledged BOOLEAN DEFAULT FALSE,
            FOREIGN KEY (session_id) REFERENCES sessions(id)
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
                                   user_prompt: str, content: str, accuracy_score: float = None):
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "INSERT INTO generated_content (id, document_id, content_type, user_prompt, content_markdown, accuracy_score) VALUES (?, ?, ?, ?, ?, ?)",
                (content_id, doc_id, content_type, user_prompt, content, accuracy_score)
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
                SELECT gc.content_markdown, gc.accuracy_score, gc.content_type, gc.user_prompt
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
                    'user_prompt': result[3]
                }
            return None
    
    async def add_processing_event(self, event_id: str, session_id: str, event_type: str, event_data: dict):
        """Add a processing event for SSE streaming"""
        async with aiosqlite.connect(self.db_path) as db:
            import json
            await db.execute(
                "INSERT INTO processing_events (id, session_id, event_type, event_data) VALUES (?, ?, ?, ?)",
                (event_id, session_id, event_type, json.dumps(event_data))
            )
            await db.commit()
    
    async def get_unacknowledged_events(self, session_id: str):
        """Get all unacknowledged events for a session"""
        async with aiosqlite.connect(self.db_path) as db:
            cursor = await db.execute("""
                SELECT id, event_type, event_data, created_at 
                FROM processing_events 
                WHERE session_id = ? AND acknowledged = FALSE 
                ORDER BY created_at ASC
            """, (session_id,))
            results = await cursor.fetchall()
            
            events = []
            for row in results:
                import json
                events.append({
                    'id': row[0],
                    'event_type': row[1],
                    'event_data': json.loads(row[2]),
                    'created_at': row[3]
                })
            
            return events
    
    async def acknowledge_event(self, event_id: str):
        """Mark an event as acknowledged"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute(
                "UPDATE processing_events SET acknowledged = TRUE WHERE id = ?",
                (event_id,)
            )
            await db.commit()
    
    async def cleanup_old_events(self, hours_old: int = 24):
        """Clean up old acknowledged events"""
        async with aiosqlite.connect(self.db_path) as db:
            await db.execute("""
                DELETE FROM processing_events 
                WHERE acknowledged = TRUE 
                AND datetime(created_at) < datetime('now', '-{} hours')
            """.format(hours_old))
            await db.commit()