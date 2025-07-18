# ----------------------------------------
# 1. Imports and Config
# ----------------------------------------
import pandas as pd
import numpy as np
import pyodbc
import sys
import os

# Add project root to path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from pipeline.observability import (
    log_source_load,
    log_null_check,
    log_transformation,
    check_schema,
    log_schema_validation,
    log_row_insertion,
    log_row_count_check,
    log_error,
    log_event
)

# ----------------------------------------
# 2. SQL Connections (Local + Azure)
# ----------------------------------------
conn_local = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=RAMSEY_BOLTON\\SQLEXPRESS;"
    "DATABASE=RealEstate;"
    "Trusted_Connection=yes;"
)
cursor_local = conn_local.cursor()
cursor_local.fast_executemany = True

conn_cloud = pyodbc.connect(
    "DRIVER={ODBC Driver 17 for SQL Server};"
    "SERVER=ws-dev-sample-01.database.windows.net;"
    "DATABASE=RealEstate;"
    "UID=azure-admin;"
    "PWD=Slowhall123!;"
)
cursor_cloud = conn_cloud.cursor()
cursor_cloud.fast_executemany = True

try:
    # ----------------------------------------
    # 3. Load CSV
    # ----------------------------------------
    file_path = r"C:\Repos\WS_Dev\data\housing.csv"
    df = pd.read_csv(file_path)
    df.columns = df.columns.str.lower().str.replace(" ", "_")
    log_source_load(conn_local, df, file_path, "pricing")
    log_source_load(conn_cloud, df, file_path, "pricing")

    # ----------------------------------------
    # 4. Null Check
    # ----------------------------------------
    required_cols = ['price', 'area', 'bedrooms', 'bathrooms', 'stories', 'parking']
    log_null_check(conn_local, df, required_cols, "pricing")
    log_null_check(conn_cloud, df, required_cols, "pricing")

    # ----------------------------------------
    # 5. Transform Data
    # ----------------------------------------
    yes_no_cols = ['mainroad', 'guestroom', 'basement', 'hotwaterheating', 'airconditioning', 'prefarea']
    df[yes_no_cols] = df[yes_no_cols].apply(lambda col: col.map(lambda x: str(x).lower() == "yes"))
    df["price_per_sqft"] = df["price"] / df["area"]
    df["has_aircon_and_heat"] = df["airconditioning"] & df["hotwaterheating"]
    transformed_cols = yes_no_cols + ["price_per_sqft", "has_aircon_and_heat"]
    log_transformation(conn_local, transformed_cols, "pricing")
    log_transformation(conn_cloud, transformed_cols, "pricing")

    final_cols = [
        'price', 'area', 'bedrooms', 'bathrooms', 'stories',
        'mainroad', 'guestroom', 'basement', 'hotwaterheating', 'airconditioning',
        'parking', 'prefarea', 'furnishingstatus', 'price_per_sqft', 'has_aircon_and_heat'
    ]
    df = df[final_cols]

    # ----------------------------------------
    # 6. Schema Validation
    # ----------------------------------------
    expected_schema = {
        'price': 'int64',
        'area': 'int64',
        'bedrooms': 'int64',
        'bathrooms': 'int64',
        'stories': 'int64',
        'mainroad': 'bool',
        'guestroom': 'bool',
        'basement': 'bool',
        'hotwaterheating': 'bool',
        'airconditioning': 'bool',
        'parking': 'int64',
        'prefarea': 'bool',
        'furnishingstatus': 'object',
        'price_per_sqft': 'float64',
        'has_aircon_and_heat': 'bool'
    }

    valid, message = check_schema(df, expected_schema)
    if valid:
        log_schema_validation(conn_local, message, "pricing")
        log_schema_validation(conn_cloud, message, "pricing")
    else:
        raise ValueError(message)

    # ----------------------------------------
    # 7. Insert into Both SQL Servers
    # ----------------------------------------

    # Clear existing rows in both tables before inserting new ones
    cursor_local.execute("DELETE FROM pricing")
    conn_local.commit()
    log_event(conn_local, "pricing", "truncate", "Cleared existing rows before insert")

    cursor_cloud.execute("DELETE FROM pricing")
    conn_cloud.commit()
    log_event(conn_cloud, "pricing", "truncate", "Cleared existing rows before insert")

    # Prepare insert statement
    insert_sql = """
        INSERT INTO pricing (
            price, area, bedrooms, bathrooms, stories,
            mainroad, guestroom, basement, hotwaterheating, airconditioning,
            parking, prefarea, furnishingstatus, price_per_sqft, has_aircon_and_heat
        ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
    """

    # Count rows before insert
    cursor_local.execute("SELECT COUNT(*) FROM pricing")
    before_local = cursor_local.fetchone()[0]
    cursor_cloud.execute("SELECT COUNT(*) FROM pricing")
    before_cloud = cursor_cloud.fetchone()[0]

    # Insert
    cursor_local.executemany(insert_sql, df.values.tolist())
    conn_local.commit()

    cursor_cloud.executemany(insert_sql, df.values.tolist())
    conn_cloud.commit()

    # Count rows after insert
    cursor_local.execute("SELECT COUNT(*) FROM pricing")
    after_local = cursor_local.fetchone()[0]
    cursor_cloud.execute("SELECT COUNT(*) FROM pricing")
    after_cloud = cursor_cloud.fetchone()[0]

    # Log insert counts
    log_row_insertion(conn_local, after_local - before_local, "pricing")
    log_row_insertion(conn_cloud, after_cloud - before_cloud, "pricing")
    log_row_count_check(conn_local, before_local, after_local, "pricing")
    log_row_count_check(conn_cloud, before_cloud, after_cloud, "pricing")

except Exception as e:
    log_error(conn_local, "pricing", "etl_pricing", str(e))
    log_error(conn_cloud, "pricing", "etl_pricing", str(e))
    raise

finally:
    cursor_local.close()
    conn_local.close()
    cursor_cloud.close()
    conn_cloud.close()
