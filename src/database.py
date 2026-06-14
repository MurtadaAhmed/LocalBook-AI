"""
get_connection(): connects to the chat_history.db
init_db(): establishes the connection and create two tables, one for the notebooks, and one for the messages
"""

import sqlite3
import os

DB_PATH = "storage/chat_history.db"

def get_connection():
    """Create database connection and return it"""
    os.makedirs(os.path.dirname(DB_PATH), exist_ok=True)
    return sqlite3.connect(DB_PATH, check_same_thread=False)

def init_db():
    conn = get_connection()
    cursor = conn.cursor()

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS notebooks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT UNIQUE NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    )
    ''')

    cursor.execute('''
    CREATE TABLE IF NOT EXISTS messages (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        notebook_id INTEGER NOT NULL,
        role TEXT NOT NULL,
        content TEXT NOT NULL,
        timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        FOREIGN KEY (notebook_id) REFERENCES notebooks (id) ON DELETE CASCADE 
    )
    ''')

    conn.commit()
    conn.close()

init_db()
