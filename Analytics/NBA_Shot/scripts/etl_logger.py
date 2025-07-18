# scripts/etl_logger.py

import os
from datetime import datetime
from scripts.db_connect import get_connection

# ----------- Terminal + File Logging -----------

LOG_DIR = os.path.join(os.path.dirname(__file__), "..", "logs")
os.makedirs(LOG_DIR, exist_ok=True)
LOG_PATH = os.path.join(LOG_DIR, "etl.log")

def log_message(message: str):
    """
    Logs a timestamped message to both the terminal and logs/etl.log file.
    """
    timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    full_message = f"[{timestamp}] {message}"
    print(full_message)
    with open(LOG_PATH, "a", encoding="utf-8") as log_file:
        log_file.write(full_message + "\n")

# ----------- SQL Table Logging -----------

def log_to_db(
    table_name,
    change_type,
    log_status,
    error_level="na",
    column_name=None,
    org_val=None,
    new_val=None,
    row_id=None,
    source_script=None
):
    """
    Inserts a row into the etl_log_events SQL table.
    """
    try:
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
            INSERT INTO etl_log_events (
                table_name, column_name, change_type,
                org_val, new_val, row_id,
                log_status, error_level, log_timestamp, source_script
            )
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, GETDATE(), ?)
        """, (
            table_name, column_name, change_type,
            str(org_val) if org_val is not None else None,
            str(new_val) if new_val is not None else None,
            str(row_id) if row_id is not None else None,
            log_status, error_level, source_script
        ))

        conn.commit()
        cursor.close()
        conn.close()

    except Exception as e:
        log_message(f"❌ Failed to write log to DB: {e}")


