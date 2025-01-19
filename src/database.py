import json
import sqlite3
from datetime import datetime
import os

class Database:

    reset_db = False
    reset_conversations = True
    #reset_db = True

    def __init__(self, persona_config):
        db_file=f"db/sql/{persona_config['persona']['name'].lower()}.db"
        # Make the folders if they don't exist
        os.makedirs(os.path.dirname(db_file), exist_ok=True)
        self.conn = sqlite3.connect(db_file)
        self.create_tables()

    def create_tables(self):
        cursor = self.conn.cursor()
        # Create users table
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS conversation_history (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                role TEXT NOT NULL,
                content TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

    def put_conversation_history(self, role, content):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO conversation_history (role, content)
            VALUES (?, ?)
        ''', (role, content))

    def get_conversation_history(self, num_entries=10):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM conversation_history
            ORDER BY created_at DESC
            LIMIT ?
        ''', (num_entries,))
        entries = cursor.fetchall()
        # convert entries into a list of dictionaries
        entries_list = []
        for entry in entries:
            entries_list.append({
                'role': entry[1],
                'content': entry[2],
                'created_at': entry[3]
            })
        return entries_list
