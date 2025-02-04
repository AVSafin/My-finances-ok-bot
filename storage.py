
import psycopg2
import os
import datetime
import logging

class Storage:
    def __init__(self):
        try:
            database_url = os.environ['DATABASE_URL']
            self.conn = psycopg2.connect(database_url)
            self.is_postgres = True
        except (KeyError, psycopg2.Error) as e:
            logging.warning("PostgreSQL connection failed, falling back to SQLite")
            import sqlite3
            self.conn = sqlite3.connect('finance_bot.db')
            self.is_postgres = False
        
        self._init_db()
        self._add_default_credits()

    def _init_db(self):
        """Initialize database and create tables if they don't exist"""
        with self.conn:
            with self.conn.cursor() as cur:
                # Create loans table
                cur.execute("""
                    CREATE TABLE IF NOT EXISTS loans (
                        id SERIAL PRIMARY KEY,
                        user_id TEXT NOT NULL,
                        name TEXT NOT NULL,
                        bank TEXT NOT NULL,
                        category TEXT NOT NULL,
                        amount DECIMAL NOT NULL,
                        rate DECIMAL NOT NULL,
                        term INTEGER NOT NULL,
                        payment_day INTEGER NOT NULL,
                        start_date DATE NOT NULL
                    )
                """)

    def _add_default_credits(self):
        """Add default credits for new users"""
        default_credits = [
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
        self.default_data = default_credits

    def get_user_data(self, user_id: str) -> dict:
        """Get loans for specific user"""
        with self.conn:
            with self.conn.cursor() as cur:
                cur.execute(
                    """SELECT name, bank, category, amount, rate, term, 
                              payment_day, start_date 
                       FROM loans WHERE user_id = %s""", 
                    (str(user_id),)
                )
                rows = cur.fetchall()
                if not rows:
                    # Return default credits for new users
                    return {"loans": self.default_data}
                
                loans = []
                for row in rows:
                    loans.append({
                        "name": row[0],
                        "bank": row[1],
                        "category": row[2],
                        "amount": float(row[3]),
                        "rate": float(row[4]),
                        "term": row[5],
                        "payment_day": row[6],
                        "date": row[7].strftime("%Y-%m-%d")
                    })
                return {"loans": loans}

    def update_user_data(self, user_id: str, data: dict):
        """Update loans for specific user"""
        try:
            with self.conn:
                with self.conn.cursor() as cur:
                    # First delete existing loans for user
                    cur.execute("DELETE FROM loans WHERE user_id = %s", (str(user_id),))
                    
                    # Insert new loans
                    for loan in data.get("loans", []):
                        cur.execute(
                            """INSERT INTO loans 
                               (user_id, name, bank, category, amount, rate, term, 
                                payment_day, start_date)
                               VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)""",
                            (str(user_id), loan["name"], loan["bank"], 
                             loan["category"], loan["amount"], loan["rate"], 
                             loan["term"], loan["payment_day"], 
                             datetime.datetime.strptime(loan["date"], "%Y-%m-%d").date())
                        )
        except psycopg2.Error as e:
            logging.error(f"Database error: {e}")
            raise Exception("Ошибка при сохранении данных")
