# db.py
import psycopg2
from psycopg2.extras import RealDictCursor
import os
import getpass

class DatabaseConnection:
    def __init__(self, host=None, database=None, user=None,
                 password=None, port=None, use_password_prompt=False):
        self.host = host or os.getenv('DB_HOST', 'localhost')
        self.database = database or os.getenv('DB_NAME', 'faq_db')   # <-- your DB
        self.user = user or os.getenv('DB_USER', 'zeno')             # <-- your role
        self.password = password or os.getenv('DB_PASSWORD', '')
        self.port = port or int(os.getenv('DB_PORT', 5432))
        self.use_password_prompt = use_password_prompt
        self.connection = None

        if not self.password and self.use_password_prompt:
            self.password = getpass.getpass(f"Enter password for database user '{self.user}': ")

    def connect(self):
        try:
            self.connection = psycopg2.connect(
                host=self.host,
                database=self.database,
                user=self.user,
                password=self.password,
                port=self.port
            )
            print(f"Connected to PostgreSQL database: {self.database}")
            return True
        except psycopg2.Error as e:
            print(f"Error connecting to PostgreSQL: {e}")
            return False

    def disconnect(self):
        if self.connection:
            self.connection.close()
            print("Database connection closed.")

    def execute_query(self, query, params=None):
        if not self.connection:
            raise Exception("Database not connected.")
        with self.connection.cursor(cursor_factory=RealDictCursor) as cursor:
            cursor.execute(query, params)
            return [dict(row) for row in cursor.fetchall()]

    def execute_update(self, query, params=None):
        if not self.connection:
            raise Exception("Database not connected.")
        try:
            with self.connection.cursor() as cursor:
                cursor.execute(query, params)
                self.connection.commit()
                return cursor.rowcount
        except psycopg2.Error as e:
            self.connection.rollback()
            print(f"Error executing update: {e}")
            raise
