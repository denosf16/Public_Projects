import pandas as pd
import inspect
import os
import traceback
from datetime import datetime
import pyodbc

# -------------------------------
# Log Helper
# -------------------------------
def log_event(conn, table_name, event_type, description, source_script=None):
    if source_script is None:
        source_script = get_caller_filename()

    cursor = conn.cursor()
    cursor.execute("""
    INSERT INTO event_log (table_name, type, timestamp, description, source_script)
    VALUES (?, ?, GETDATE(), ?, ?)
""", (table_name, event_type, description, source_script))
    conn.commit()
    cursor.close()

# -------------------------------
# Utility: Caller File
# -------------------------------
def get_caller_filename():
    try:
        frame = inspect.stack()[2]
        path = frame.filename
        return os.path.basename(path)
    except Exception:
        return "unknown"

# -------------------------------
# 1. Source Load
# -------------------------------
def log_source_load(conn, df, source_path, table_name):
    description = f"Loaded {len(df)} rows from {os.path.basename(source_path)}"
    log_event(conn, table_name, "source_load", description)

# -------------------------------
# 2. Null Check
# -------------------------------
def log_null_check(conn, df, required_cols, table_name):
    nulls = [col for col in required_cols if df[col].isnull().any()]
    if nulls:
        desc = f"Nulls found in required fields: {nulls}"
    else:
        desc = "No nulls detected in required columns"
    log_event(conn, table_name, "null_check", desc)

# -------------------------------
# 3. Transformation Log
# -------------------------------
def log_transformation(conn, transformed_cols, table_name):
    desc = f"Transformed columns: {transformed_cols}"
    log_event(conn, table_name, "transformation", desc)

# -------------------------------
# 4. Schema Validation
# -------------------------------
def check_schema(df: pd.DataFrame, expected_schema: dict):
    actual_cols = df.columns.tolist()
    expected_cols = list(expected_schema.keys())

    if actual_cols != expected_cols:
        return False, f"Column mismatch:\nExpected: {expected_cols}\nFound: {actual_cols}"
    
    for col, dtype in expected_schema.items():
        actual_dtype = str(df[col].dtype)
        if actual_dtype != dtype:
            return False, f"Type mismatch in '{col}': expected {dtype}, found {actual_dtype}"
    
    return True, "Schema validation passed"

def log_schema_validation(conn, passed_msg, table_name):
    log_event(conn, table_name, "schema_validation", passed_msg)

# -------------------------------
# 5. Row Insertion
# -------------------------------
def log_row_insertion(conn, inserted_count, table_name):
    desc = f"{inserted_count} rows inserted into {table_name} table."
    log_event(conn, table_name, "row_insertion", desc)

# -------------------------------
# 6. Row Count Check
# -------------------------------
def log_row_count_check(conn, before, after, table_name):
    delta = after - before
    desc = f"Pre-insert: {before}, Post-insert: {after}, Delta: {delta}"
    log_event(conn, table_name, "row_count_check", desc)

# -------------------------------
# 7. Error Logging
# -------------------------------
def log_error(conn, table_name, stage, err):
    desc = f"Error in stage {stage}: {str(err)}"
    log_event(conn, table_name, "error", desc)
