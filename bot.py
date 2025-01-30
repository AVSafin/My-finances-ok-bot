from handlers.forecast.actions import (
    calculate_daily_balance_start,
    ask_balance,
    ask_salary_day,
    daily_balance_handler,
)

import sqlite3

class Storage:
    def __init__(self, db_name='credits.db'):
        self.conn = sqlite3.connect(db_name)
        self.cursor = self.conn.cursor()
        self.create_tables()
        self.add_default_credits()

    def create_tables(self):
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS users (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                name TEXT
            )
        ''')
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS credits (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                type TEXT,
                amount REAL,
                FOREIGN KEY (user_id) REFERENCES users(id)
            )
        ''')
        self.conn.commit()

    def add_default_credits(self):
        self.cursor.execute("INSERT INTO users (name) VALUES ('Default User')")
        user_id = self.cursor.lastrowid
        self.cursor.execute("INSERT INTO credits (user_id, type, amount) VALUES (?, ?, ?)", (user_id, 'Loan', 1000.00))
        self.cursor.execute("INSERT INTO credits (user_id, type, amount) VALUES (?, ?, ?)", (user_id, 'Savings', 500.00))
        self.conn.commit()

    def close(self):
        self.conn.close()


# Initialize storage
storage = Storage()

# Example usage (replace with your actual forecast handling logic)
# ...  (rest of the code) ...

# Close the database connection when finished
storage.close()