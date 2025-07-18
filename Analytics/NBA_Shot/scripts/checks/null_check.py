import os
import pandas as pd
import pyodbc

# Configuration paths
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
        DATA_TYPE,
        IS_NULLABLE
    FROM INFORMATION_SCHEMA.COLUMNS
    WHERE TABLE_NAME = '{table_name}'
    """
    df = pd.read_sql(query, conn)
    return df

def check_nulls(conn, table_name):
    """
    Calculates the % nulls per column for a given table.
    Flags columns where null % exceeds the threshold.
    Saves a DataFrame with table, column, is_nullable, null_rows, null_pct in the respective folder.
    """
    # Get schema details (column names, nullability)
    schema = get_table_schema(conn, table_name)
    
    # Prepare a list to store results
    results = []

    for _, row in schema.iterrows():
        column = row['COLUMN_NAME']
        is_nullable = 1 if row['IS_NULLABLE'] == 'YES' else 0

        # Query to calculate null count and total row count for each column
        null_query = f"""
            SELECT COUNT(*) AS total_rows,
                   SUM(CASE WHEN [{column}] IS NULL THEN 1 ELSE 0 END) AS nulls
            FROM {table_name}
        """
        df = pd.read_sql(null_query, conn)
        total = df.loc[0, 'total_rows']
        nulls = df.loc[0, 'nulls']
        null_pct = nulls / total if total > 0 else 0

        # Prepare result row
        result = {
            "TABLE": table_name,
            "COLUMN": column,
            "NULLABLE": is_nullable,
            "NULL CT": nulls,
            "NULL PCT": round(null_pct * 100, 2)  # Percentage formatted to 2 decimal places
        }
        
        results.append(result)

    # Convert the results to a DataFrame
    result_df = pd.DataFrame(results)

    # Save to Excel in the respective table folder
    save_to_excel(result_df, table_name)

def save_to_excel(df, table_name):
    """Save the results to an Excel file in the respective folder."""
    # Create the folder for the table if it doesn't exist
    folder_path = os.path.join(OUTPUT_PATH, table_name)
    os.makedirs(folder_path, exist_ok=True)  # Ensure the folder is created
    
    # Define the file path for the null check results
    file_path = os.path.join(folder_path, "null_check.xlsx")
    
    # Write data to Excel, creating the file if it doesn't exist, or append if it does
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
        df.to_excel(writer, index=False, header=True, sheet_name='Null Check')

def run_checks_for_all_tables():
    """Run null check for all tables and save results to Excel."""
    # List of tables to analyze
    tables = ["team_info", "player_game_logs", "player_info_analysis", "player_shot_logs"]
    
    conn = get_connection()  # Connect to the database

    for table in tables:
        # Run null check for each table
        check_nulls(conn, table)

    conn.close()  # Close the connection

if __name__ == "__main__":
    run_checks_for_all_tables()











