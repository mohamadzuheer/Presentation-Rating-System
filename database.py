import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'presentation_rating.db')

def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    conn = get_db()
    c = conn.cursor()

    c.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS presentations (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            presenter_id INTEGER NOT NULL,
            status TEXT NOT NULL DEFAULT 'open',
            started_at TEXT,
            closed_at TEXT
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS ratings (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            presentation_id INTEGER NOT NULL,
            presenter_id INTEGER NOT NULL,
            rater_id INTEGER NOT NULL,
            rating_score INTEGER NOT NULL,
            submitted_at TEXT,
            UNIQUE(presentation_id, rater_id)
        )
    ''')

    c.execute('''
        CREATE TABLE IF NOT EXISTS session_status (
            id INTEGER PRIMARY KEY,
            is_active INTEGER NOT NULL DEFAULT 0,
            current_presentation_id INTEGER,
            current_presenter_id INTEGER
        )
    ''')

    # Ensure exactly one row in session_status
    c.execute('SELECT COUNT(*) FROM session_status')
    if c.fetchone()[0] == 0:
        c.execute('INSERT INTO session_status (id, is_active) VALUES (1, 0)')

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
