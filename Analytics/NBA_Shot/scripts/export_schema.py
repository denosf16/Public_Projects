# scripts/export_schema.py

import os
import json
import pyodbc
import pandas as pd

CONFIG_DIR = os.path.join(os.path.dirname(__file__), "..", "config")
os.makedirs(CONFIG_DIR, exist_ok=True)
CONFIG_PATH = os.path.join(CONFIG_DIR, "expected_schema.json")

# Connection string (update if needed)
conn_str = (
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=RAMSEY_BOLTON\\SQLEXPRESS;"
    "DATABASE=NBA_Shots;"
    "Trusted_Connection=yes;"
)

def export_schema():
    conn = pyodbc.connect(conn_str)
    query = """
        SELECT 
            TABLE_SCHEMA,
            TABLE_NAME,
            COLUMN_NAME,
            DATA_TYPE,
            IS_NULLABLE,
            ORDINAL_POSITION
        FROM INFORMATION_SCHEMA.COLUMNS
        WHERE TABLE_SCHEMA = 'dbo'
        ORDER BY TABLE_NAME, ORDINAL_POSITION
    """
    df = pd.read_sql(query, conn)

    schema_dict = {}
    for table, group in df.groupby("TABLE_NAME"):
        table_key = f"dbo.{table}"
        schema_dict[table_key] = {}
        for _, row in group.iterrows():
            schema_dict[table_key][row["COLUMN_NAME"]] = {
                "data_type": row["DATA_TYPE"],
                "is_nullable": row["IS_NULLABLE"],
                "ordinal_position": row["ORDINAL_POSITION"]
            }

    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(schema_dict, f, indent=4)

    print(f"✅ Schema exported to {CONFIG_PATH}")

if __name__ == "__main__":
    export_schema()
