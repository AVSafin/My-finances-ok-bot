
import sqlite3
import json
from typing import Dict, Any
import datetime

class Storage:
    def __init__(self):
        self.conn = sqlite3.connect('finance_bot.db')
        self._init_db()
        self._add_default_credits()

    def _init_db(self):
        """Initialize database and create tables if they don't exist"""
        with self.conn:
            self.conn.execute("""
                CREATE TABLE IF NOT EXISTS user_data
                (user_id TEXT PRIMARY KEY, data TEXT)
            """)
    
    def _add_default_credits(self):
        """Add default credits for new users"""
        default_credits = {
            "loans": [
                {
                    "name": "Ипотека | Сбербанк | 15 число | 3,000,000 руб.",
                    "bank": "🟢 Сбербанк",
                    "category": "Ипотека",
                    "amount": 3000000,
                    "rate": 7.9,
                    "term": 240,
                    "payment_day": 15,
                    "date": "2024-03-15"
                },
                {
                    "name": "Автокредит | ВТБ | 10 число | 1,500,000 руб.",
                    "bank": "🔵 ВТБ",
                    "category": "Автокредит",
                    "amount": 1500000,
                    "rate": 8.5,
                    "term": 60,
                    "payment_day": 10,
                    "date": "2023-10-10"
                }
            ]
        }
        self.default_data = default_credits

    def get_user_data(self, user_id: str) -> dict:
        """Get data for specific user"""
        with self.conn:
            result = self.conn.execute(
                "SELECT data FROM user_data WHERE user_id = ?", 
                (str(user_id),)
            ).fetchone()
            return json.loads(result[0]) if result else self.default_data

    def update_user_data(self, user_id: str, data: dict):
        """Update data for specific user"""
        with self.conn:
            self.conn.execute(
                """INSERT OR REPLACE INTO user_data (user_id, data) 
                   VALUES (?, ?)""",
                (str(user_id), json.dumps(data))
            )
