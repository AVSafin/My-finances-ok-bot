import sqlite3
from datetime import datetime

class Database:
    def __init__(self, db_path):
        self.db_path = db_path
        self.conn = None
        self.cursor = None

    def connect(self):
        self.conn = sqlite3.connect(self.db_path)
        self.cursor = self.conn.cursor()

    def close(self):
        if self.conn:
            self.conn.close()

    def create_tables(self):
        self.connect()
        self.cursor.execute("""
        CREATE TABLE IF NOT EXISTS loans (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            loan_amount REAL,
            loan_rate REAL,
            loan_term INTEGER,
            bank TEXT,
            loan_type TEXT,
            user_id INTEGER
        )
        """)
        self.cursor.execute("""
            CREATE TABLE IF NOT EXISTS payments (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                loan_id INTEGER,
                payment_date TEXT,
                payment_amount REAL,
                FOREIGN KEY (loan_id) REFERENCES loans(id)
            )
        """)
        self.conn.commit()
        self.close()


    def add_loan(self, loan_amount, loan_rate, loan_term, bank, loan_type, user_id):
        self.connect()
        self.cursor.execute("""
            INSERT INTO loans (loan_amount, loan_rate, loan_term, bank, loan_type, user_id)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (loan_amount, loan_rate, loan_term, bank, loan_type, user_id))
        loan_id = self.cursor.lastrowid
        self.conn.commit()
        self.close()
        return loan_id

    def add_payment(self, loan_id, payment_date, payment_amount):
        self.connect()
        self.cursor.execute("""
            INSERT INTO payments (loan_id, payment_date, payment_amount)
            VALUES (?, ?, ?)
        """, (loan_id, payment_date, payment_amount))
        self.conn.commit()
        self.close()

    def get_upcoming_payments(self, user_id):
            self.connect()
            self.cursor.execute("""
                SELECT p.payment_date, p.payment_amount, l.bank, l.loan_type
                FROM payments p
                JOIN loans l ON p.loan_id = l.id
                WHERE l.user_id = ? AND p.payment_date >= ?
                ORDER BY p.payment_date
                LIMIT 2
            """, (user_id, datetime.now().strftime("%Y-%m-%d")))
            payments = self.cursor.fetchall()
            self.close()
            return payments
