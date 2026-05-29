import sqlite3
import os

DB_PATH = os.path.join(os.path.dirname(__file__), 'presentation_rating.db')
DEFAULT_ADMIN_NAME = os.environ.get('DEFAULT_ADMIN_NAME', 'admin')
DEFAULT_ADMIN_PASSWORD = os.environ.get('DEFAULT_ADMIN_PASSWORD', 'admin123')
DEFAULT_STUDENT_PASSWORD = os.environ.get('DEFAULT_STUDENT_PASSWORD', 'student123')

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
            problem_clarity INTEGER,
            market_potential INTEGER,
            uniqueness_insight INTEGER,
            feasibility INTEGER,
            pitch_delivery INTEGER,
            work_interest INTEGER,
            weighted_score REAL,
            submitted_at TEXT,
            UNIQUE(presentation_id, rater_id)
        )
    ''')

    c.execute("PRAGMA table_info(ratings)")
    rating_columns = {row[1] for row in c.fetchall()}
    rubric_columns = {
        'problem_clarity': 'INTEGER',
        'market_potential': 'INTEGER',
        'uniqueness_insight': 'INTEGER',
        'feasibility': 'INTEGER',
        'pitch_delivery': 'INTEGER',
        'work_interest': 'INTEGER',
        'weighted_score': 'REAL'
    }
    for column, column_type in rubric_columns.items():
        if column not in rating_columns:
            c.execute(f'ALTER TABLE ratings ADD COLUMN {column} {column_type}')

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

    c.execute(
        '''
        INSERT INTO users (name, password, role)
        VALUES (?, ?, 'admin')
        ON CONFLICT(name) DO UPDATE SET
            password = excluded.password,
            role = 'admin'
        ''',
        (DEFAULT_ADMIN_NAME, DEFAULT_ADMIN_PASSWORD)
    )

    c.execute('SELECT COUNT(*) FROM users WHERE role = ?', ('student',))
    if c.fetchone()[0] == 0:
        for i in range(1, 11):
            c.execute(
                'INSERT OR IGNORE INTO users (name, password, role) VALUES (?, ?, ?)',
                (f'Student {i:03d}', DEFAULT_STUDENT_PASSWORD, 'student')
            )

    conn.commit()
    conn.close()
    print("Database initialized successfully.")

if __name__ == '__main__':
    init_db()
