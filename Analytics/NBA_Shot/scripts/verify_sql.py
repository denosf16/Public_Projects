import os
import pandas as pd
import numpy as np
import json
import sys
import warnings

# Suppress unnecessary warnings
warnings.filterwarnings("ignore", message="pandas only supports SQLAlchemy", category=UserWarning)

# Add project root to Python module path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))
from scripts.db_connect import get_connection

# ------------------------------
# Config
# ------------------------------
primary_keys = {
    "player_info_analysis": ["PLAYER_ID"],
    "player_game_logs": ["PLAYER_ID", "GAME_ID"],
    "player_shot_logs": ["SHOT_EVENT_ID"],
    "team_info": ["TEAM_ID"]
}

SCHEMA_PATH = os.path.join("config", "expected_schema.json")
REPORT_DIR = os.path.join("reports")
Z_THRESHOLD = 3.0
NULL_THRESHOLD = 0.2

# ------------------------------
# Helpers
# ------------------------------
def ensure_dir(path):
    if not os.path.exists(path):
        os.makedirs(path)

def get_full_table_name(table):
    return f"dbo.{table}" if not table.startswith("dbo.") else table

# ------------------------------
# 1. Schema Check
# ------------------------------
def run_schema_check(conn, table, expected_schema):
    query = f"""
    SELECT COLUMN_NAME, DATA_TYPE, IS_NULLABLE, ORDINAL_POSITION
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = '{table}'
    """
    df = pd.read_sql(query, conn)
    df = df.set_index("COLUMN_NAME")

    table_key = get_full_table_name(table)
    expected_cols = expected_schema.get(table_key, {})

    results = []
    for col, meta in expected_cols.items():
        if col not in df.index:
            results.append({"column": col, "status": "FAIL", "flag_reason": "Missing column"})
            continue

        actual = df.loc[col]
        if meta["data_type"].lower() != actual.DATA_TYPE.lower():
            results.append({"column": col, "status": "FAIL", "flag_reason": f"Type mismatch (expected {meta['data_type']})"})
        if meta["is_nullable"].lower() != actual.IS_NULLABLE.lower():
            results.append({"column": col, "status": "FAIL", "flag_reason": f"Nullability mismatch (expected {meta['is_nullable']})"})
        if "ordinal_position" in meta and int(meta["ordinal_position"]) != int(actual.ORDINAL_POSITION):
            results.append({"column": col, "status": "WARNING", "flag_reason": f"Ordinal mismatch (expected {meta['ordinal_position']})"})

    for col in df.index:
        if col not in expected_cols:
            results.append({"column": col, "status": "WARNING", "flag_reason": "Unexpected column"})

    # If no issues, add a "PASSED" row
    if not results:
        results.append({"column": "All Columns", "status": "PASSED", "flag_reason": "No issues detected"})

    return pd.DataFrame(results)

# ------------------------------
# 2. Null & Uniqueness Check
# ------------------------------
def run_null_check(conn, table, cols, pk):
    selected = ', '.join(f"[{c}]" for c in cols)
    query = f"SELECT {selected} FROM {get_full_table_name(table)}"
    df = pd.read_sql(query, conn)

    results = []
    for col in cols:
        null_pct = df[col].isna().mean()
        status = "FAIL" if null_pct > NULL_THRESHOLD else "PASS"
        reason = f"{round(null_pct*100, 2)}% null" if status == "FAIL" else None
        results.append({"column": col, "status": status, "flag_reason": reason})

    if pk:
        dupes = df.duplicated(subset=pk).sum()
        status = "FAIL" if dupes > 0 else "PASS"
        results.append({"column": ", ".join(pk), "status": status, "flag_reason": f"{dupes} duplicate keys" if status == "FAIL" else None})

    return pd.DataFrame(results)

# ------------------------------
# 3. Outlier Check
# ------------------------------
def run_outlier_check(conn, table, cols):
    selected = ', '.join(f"[{c}]" for c in cols)
    query = f"SELECT {selected} FROM {get_full_table_name(table)}"
    df = pd.read_sql(query, conn)

    results = []
    for col in cols:
        if not pd.api.types.is_numeric_dtype(df[col]):
            continue
        series = df[col].dropna()
        if len(series) < 2:
            continue
        z = np.abs((series - series.mean()) / series.std(ddof=0))
        outliers = (z > Z_THRESHOLD).sum()
        status = "FAIL" if outliers > 0 else "PASS"
        reason = f"{outliers} outliers > {Z_THRESHOLD} sigma" if status == "FAIL" else None
        results.append({"column": col, "status": status, "flag_reason": reason})

    return pd.DataFrame(results)

# ------------------------------
# Main Driver
# ------------------------------
def main():
    conn = get_connection()
    with open(SCHEMA_PATH, "r") as f:
        expected_schema = json.load(f)

    for table, pk in primary_keys.items():
        print(f"\n🔍 Verifying: {table}")
        folder = os.path.join(REPORT_DIR, table)
        ensure_dir(folder)

        # Get all columns for null and outlier checks
        query = f"SELECT TOP 0 * FROM {get_full_table_name(table)}"
        all_cols = pd.read_sql(query, conn).columns.tolist()

        # Run checks
        schema_df = run_schema_check(conn, table, expected_schema)
        schema_df.to_csv(os.path.join(folder, "schema_check.csv"), index=False)

        null_df = run_null_check(conn, table, all_cols, pk)
        null_df.to_csv(os.path.join(folder, "null_check.csv"), index=False)

        outlier_df = run_outlier_check(conn, table, all_cols)
        outlier_df.to_csv(os.path.join(folder, "outlier_check.csv"), index=False)

        print(f"✅ Completed: {table}")

if __name__ == "__main__":
    main()
