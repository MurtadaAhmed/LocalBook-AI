"""
get_connection(): connects to the chat_history.db
init_db(): establishes the connection and create two tables, one for the notebooks, and one for the messages
create_notebook(name: str): create notebook and returns its ID or returns existing notebook ID.
get_all_notebooks(): returns all the created notebooks ordered by the newest ones.
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

def create_notebook(name: str):
    """creates new notebook and returns its ID. if it already exists, return the existing ID"""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("INSERT INTO notebooks (name) VALUES (?)", (name,))
        conn.commit()
        notebook_id = cursor.lastrowid
    except sqlite3.IntegrityError:
        cursor.execute("SELECT id FROM notebooks WHERE name = ?", (name, ))
        notebook_id = cursor.fetchone()[0]
    finally:
        conn.close()
    return notebook_id

def get_all_notebooks():
    """return all notebooks ordered by the newest ones"""
    conn = get_connection()
    curser = conn.cursor()
    curser.execute("SELECT id, name, created_at FROM notebooks ORDER BY created_at DESC")
    notebooks = curser.fetchall()
    conn.close()
    return notebooks

def delete_notebook(notebook_id: int):
    ...

def save_message(notebook_id: int, role: str, content: str):
    ...

def get_messages_by_notebook(notebook_id: int):
    ...

