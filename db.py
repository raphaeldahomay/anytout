import os
import sqlite3
from flask import current_app

def init_db(db_path):

    os.makedirs(os.path.dirname(db_path), exist_ok=True)

    conn = sqlite3.connect(db_path)
    cursor = conn.cursor()

    cursor.execute("PRAGMA foreign_keys = ON;")

    cursor.executescript("""
    CREATE TABLE IF NOT EXISTS credentials (
        user_id INTEGER PRIMARY KEY AUTOINCREMENT,
        username VARCHAR(255) UNIQUE NOT NULL,
        pwd_hash VARCHAR(255) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
    );

    CREATE TABLE IF NOT EXISTS thoughts (
        tout_id INTEGER PRIMARY KEY AUTOINCREMENT,
        user_id INTEGER,
        thoughts VARCHAR(50) NOT NULL,
        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
        like_s INTEGER DEFAULT 0,
        FOREIGN KEY (user_id) REFERENCES credentials(user_id)
    );

    CREATE TABLE IF NOT EXISTS likes (
        user_id INTEGER NOT NULL,
        tout_id INTEGER NOT NULL,
        PRIMARY KEY (user_id, tout_id),
        FOREIGN KEY (user_id) REFERENCES credentials(user_id),
        FOREIGN KEY (tout_id) REFERENCES thoughts(tout_id)
    );
    """)

    conn.commit()
    conn.close()


def get_db_connection():

    conn = sqlite3.connect(current_app.config["DATABASE"])
    conn.row_factory = sqlite3.Row

    conn.execute("PRAGMA foreign_keys = ON;")

    return conn