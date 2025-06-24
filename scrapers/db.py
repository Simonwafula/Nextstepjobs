# backend/scraping/db.py

import sqlite3, logging
from config import DB_PATH, TABLE_NAME

logging.basicConfig(level=logging.INFO)

class Database:
    def __init__(self, db_path: str = DB_PATH, table: str = TABLE_NAME):
        self.db_path = db_path
        self.table   = table
        self.conn    = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self._ensure_table()

    def close(self):
        if self.conn:
            self.conn.close()

    def _ensure_table(self):
        sql = f'''
        CREATE TABLE IF NOT EXISTS {self.table} (
            id         INTEGER PRIMARY KEY AUTOINCREMENT,
            full_link  TEXT    UNIQUE,
            title      TEXT,
            content    TEXT
        )'''
        self.conn.execute(sql)
        self.conn.commit()
        logging.info(f"Ensured table `{self.table}` exists in {self.db_path}")

    def batch_insert(self, rows):
        """
        rows: iterable of (title, full_link, content)
        """
        cursor = self.conn.cursor()
        inserted = 0
        for title, link, content in rows:
            try:
                cursor.execute(f'''
                    INSERT OR IGNORE INTO {self.table} (title, full_link, content)
                    VALUES (?, ?, ?)
                ''', (title, link, content))
                if cursor.rowcount:
                    inserted += 1
            except sqlite3.Error as e:
                logging.error(f"DB error for {title}: {e}")
        self.conn.commit()
        logging.info(f"Inserted {inserted} new rows into {self.table}")
        return inserted
