import sqlite3
from datetime import datetime

DB_NAME = "memory.db"

# ✅ Initialize database and tables
def init_db():
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        # Table for message history
        c.execute('''
            CREATE TABLE IF NOT EXISTS memory (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id TEXT,
                role TEXT,  -- 'user' or 'assistant'
                message TEXT,
                timestamp DATETIME DEFAULT CURRENT_TIMESTAMP
            )
        ''')
        conn.commit()

# ✅ Append a message to memory
def append_user_message(user_id, role, message):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            "INSERT INTO memory (user_id, role, message) VALUES (?, ?, ?)",
            (user_id, role, message)
        )
        conn.commit()

# ✅ Get the last N messages for a user
def get_user_context(user_id, limit=5):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute(
            "SELECT role, message FROM memory WHERE user_id = ? ORDER BY timestamp DESC LIMIT ?",
            (user_id, limit)
        )
        rows = c.fetchall()
        return list(reversed([{"role": row[0], "message": row[1]} for row in rows]))

# ✅ Clear memory (optional)
def clear_user_memory(user_id):
    with sqlite3.connect(DB_NAME) as conn:
        c = conn.cursor()
        c.execute("DELETE FROM memory WHERE user_id = ?", (user_id,))
        conn.commit()

# ✅ Initialize the DB when this file is imported
init_db()
