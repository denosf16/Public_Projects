# scripts/create_db.py

import os
import sys
import pyodbc

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.etl_logger import log_message
from scripts.db_connect import get_master_connection

def create_database(db_name="NBA_Shots"):
    try:
        conn = get_master_connection()
        conn.autocommit = True  # 🧠 This line is the fix!
        cursor = conn.cursor()

        cursor.execute(f"""
            IF NOT EXISTS (
                SELECT name FROM sys.databases WHERE name = ?
            )
            BEGIN
                CREATE DATABASE [{db_name}];
            END
        """, db_name)

        cursor.close()
        conn.close()

        log_message(f"✅ Database '{db_name}' created or already exists.")

    except Exception as e:
        log_message(f"❌ Error creating database '{db_name}': {e}")

if __name__ == "__main__":
    create_database()



