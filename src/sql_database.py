import json
import sqlite3
from datetime import datetime
import os

class SQLDatabase:

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
            CREATE TABLE IF NOT EXISTS utterances (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                speaker TEXT NOT NULL,
                utterance TEXT NOT NULL,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        ''')

        # Long Term Memory State
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lmt_state (
                name TEXT PRIMARY KEY,
                boundary_check_counter INTEGER NOT NULL,
                boundary_group_counter INTEGER NOT NULL
            )
        ''')

        cursor.execute('''
            CREATE TABLE IF NOT EXISTS lmt_topics (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                topic TEXT NOT NULL,
                start_utterance_id TEXT NOT NULL,
                end_utterance_id TEXT NOT NULL
            )
        ''')
        self.conn.commit()


    # Utterances
    def store_utterance(self, speaker, utterance):
        cursor = self.conn.cursor()
        cursor.execute('''
            INSERT INTO utterances (speaker, utterance)
            VALUES (?, ?)
        ''', (speaker, utterance))
        self.conn.commit()

    def retreive_utterances(self, num_entries=10):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM utterances
            ORDER BY created_at DESC
            LIMIT ?
        ''', (num_entries,))
        entries = cursor.fetchall()
        # convert entries into a list of dictionaries
        entries_list = []
        for entry in entries:
            entries_list.append({
                'speaker': entry[1],
                'utterance': entry[2],
                'created_at': entry[3]
            })
        return entries_list

    # Long Term Memory
    # LTM: State
    def retreive_ltm_state(self):
        cursor = self.conn.cursor()
        cursor.execute('''
            SELECT * FROM lmt_state WHERE name = 'state'
        ''')
        state = cursor.fetchone()
        return state

    # LTM: Update and existing lmt_state or create a new one
    def store_ltm_state(self, boundary_check_counter, boundary_group_counter):
        cursor = self.conn.cursor()
        cursor.execute(f'''
            INSERT INTO lmt_state (name, boundary_check_counter, boundary_group_counter)
            VALUES ('state', {boundary_check_counter}, {boundary_group_counter} )
            ON CONFLICT (name) DO UPDATE SET
            boundary_check_counter = {boundary_check_counter},
            boundary_group_counter = {boundary_group_counter}
        ''')
        self.conn.commit()

    # LTM: Topic Boundaries
    def store_topic_boundary(self, topic, start_utterance_id, end_utterance_id):
        cursor = self.conn.cursor()
        cursor.execute(f'''
            INSERT INTO lmt_topics (topic, start_utterance_id, end_utterance_id)
            VALUES ({topic}, {start_utterance_id}, {end_utterance_id})''')
        self.conn.commit()
