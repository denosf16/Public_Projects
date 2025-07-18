import os
import json
import pandas as pd
import pyodbc

# Configuration paths
CONFIG_PATH = os.path.join("config", "expected_schema.json")
OUTPUT_PATH = r"C:\Repos\NBA_Shot\reports"

# SQL Server connection details
SERVER_NAME = "RAMSEY_BOLTON\\SQLEXPRESS"
DRIVER = "ODBC Driver 17 for SQL Server"

def get_connection(database="NBA_Shots"):
    """Returns the connection to the SQL Server database."""
    conn_str = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER_NAME};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)

def get_table_schema(conn, table_name):
    """Fetch the schema for a specific table (columns and data types)."""
    query = f"""
    SELECT 
        COLUMN_NAME,
        DATA_TYPE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = '{table_name}'
    """
    df = pd.read_sql(query, conn)
    return df

def get_primary_foreign_keys(conn, table_name):
    """Fetch primary and foreign key details for the table."""
    query = f"""
    SELECT 
        k.COLUMN_NAME,
        k.CONSTRAINT_NAME,
        c.CONSTRAINT_TYPE
    FROM INFORMATION_SCHEMA.KEY_COLUMN_USAGE k
    JOIN INFORMATION_SCHEMA.TABLE_CONSTRAINTS c 
        ON k.CONSTRAINT_NAME = c.CONSTRAINT_NAME
    WHERE k.TABLE_NAME = '{table_name}' AND c.TABLE_NAME = '{table_name}'
    """
    df = pd.read_sql(query, conn)
    return df

def get_indexes(conn, table_name):
    """Fetch indexed columns for the table."""
    query = f"""
    SELECT 
        i.name AS index_name, 
        c.name AS column_name
    FROM sys.indexes i
    INNER JOIN sys.index_columns ic ON i.object_id = ic.object_id
    INNER JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
    WHERE i.object_id = OBJECT_ID('{table_name}')
    """
    df = pd.read_sql(query, conn)
    return df

def create_table_output(conn, table_name):
    """Create output dataframe with schema and relational information."""
    # Get the table schema (columns and data types)
    schema_df = get_table_schema(conn, table_name)

    # Initialize the list to store results
    results = []

    # Fetch primary/foreign keys and indexes
    primary_foreign_df = get_primary_foreign_keys(conn, table_name)
    indexes_df = get_indexes(conn, table_name)

    # Loop through the schema and add relational info
    for _, row in schema_df.iterrows():
        column = row['COLUMN_NAME']
        data_type = row['DATA_TYPE']
        
        # Initialize relational columns
        p_key = 0
        f_key = 0
        idx = 0

        # Check for Primary/Foreign Key and Indexes
        if column in primary_foreign_df['COLUMN_NAME'].values:
            p_key = 1

        if column in primary_foreign_df['COLUMN_NAME'].values and \
            primary_foreign_df.loc[primary_foreign_df['COLUMN_NAME'] == column, 'CONSTRAINT_TYPE'].values[0] == "FOREIGN KEY":
            f_key = 1

        if column in indexes_df['column_name'].values:
            idx = 1

        # Append the result
        results.append({
            "TABLE": table_name,
            "COLUMN": column,
            "DATA TYPE": data_type,
            "P KEY": p_key,
            "F KEY": f_key,
            "IDX": idx
        })

    # Convert results to a DataFrame
    return pd.DataFrame(results)

def get_expected_data_type(column, table_name):
    """Fetch the expected data type for a column from the config."""
    with open(CONFIG_PATH, "r") as f:
        expected_schema = json.load(f)

    if table_name in expected_schema and column in expected_schema[table_name]:
        return expected_schema[table_name][column]["data_type"]
    else:
        # Return 'Unknown' if the column is not found in the expected schema
        return "Unknown"

def save_to_excel(df, table_name):
    """Save the results to an Excel file."""
    # Create folder if it doesn't exist
    folder_path = os.path.join(OUTPUT_PATH, table_name)
    os.makedirs(folder_path, exist_ok=True)
    
    # Save to Excel
    file_path = os.path.join(folder_path, "schema_check.xlsx")
    df.to_excel(file_path, index=False)

def run_checks_for_all_tables():
    """Run schema check for all tables and save results to Excel."""
    tables = ["player_info_analysis", "player_shot_logs", "team_info", "player_game_logs"]
    conn = get_connection()

    for table in tables:
        # Run schema check for each table
        table_output = create_table_output(conn, table)
        
        # Save results to Excel
        save_to_excel(table_output, table)

    conn.close()

if __name__ == "__main__":
    run_checks_for_all_tables()








