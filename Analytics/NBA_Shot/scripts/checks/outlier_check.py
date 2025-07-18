import os
import pandas as pd
import pyodbc

# Configuration paths
OUTPUT_PATH = r"C:\Repos\NBA_Shot\reports"

# SQL Server connection details
SERVER_NAME = "RAMSEY_BOLTON\\SQLEXPRESS"
DRIVER = "ODBC Driver 17 for SQL Server"

# Columns to exclude from outlier checks
EXCLUDED_COLUMNS = {
    "player_game_logs": ["SEASON_YEAR", "PLAYER_ID", "GAME_ID", "TEAM_ID", "DRAFT_YEAR", "DRAFT_ROUND", "DRAFT_NUMBER"],
    "player_info": ["PLAYER_ID", "DRAFT_YEAR", "DRAFT_ROUND", "DRAFT_NUMBER", "TEAM_ID"],
    "player_info_analysis": ["PLAYER_ID", "DRAFT_YEAR", "DRAFT_ROUND", "DRAFT_NUMBER", "TEAM_ID"],
    "player_shot_logs": ["PLAYER_ID", "GAME_ID", "CLOSEST_DEFENDER_PLAYER_ID"],
    "team_info": ["TEAM_ID"]
}

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

def check_outliers_iqr(conn, table_name):
    """
    Detects outliers in each numeric column using the IQR method.
    Saves a DataFrame with table, column, outlier_count, outlier_pct in the respective folder.
    """
    # Get schema details (column names, nullability)
    schema = get_table_schema(conn, table_name)
    
    # Prepare a list to store results
    results = []

    # Query to fetch all data from the table
    data_query = f"SELECT * FROM {table_name}"
    df = pd.read_sql(data_query, conn)

    # Get the columns to exclude for the current table
    excluded_columns = EXCLUDED_COLUMNS.get(table_name, [])

    # Loop through each numeric column
    for _, row in schema.iterrows():
        column = row['COLUMN_NAME']
        is_nullable = 1 if row['IS_NULLABLE'] == 'YES' else 0
        
        if column in excluded_columns:
            continue  # Skip columns in the excluded list

        if df[column].dtype in ['int64', 'float64']:  # Only check numeric columns
            # Calculate Q1 (25th percentile) and Q3 (75th percentile) for IQR
            Q1 = df[column].quantile(0.25)
            Q3 = df[column].quantile(0.75)
            IQR = Q3 - Q1

            # Calculate the lower and upper bounds for outliers
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR

            # Detect outliers: values outside the [lower_bound, upper_bound] range
            outliers = ((df[column] < lower_bound) | (df[column] > upper_bound)).sum()
            total = len(df[column].dropna())
            outlier_pct = (outliers / total) * 100 if total > 0 else 0

            # Prepare result row
            result = {
                "TABLE": table_name,
                "COLUMN": column,
                "OUTLIERS CT": outliers,
                "OUTLIER PCT": round(outlier_pct, 2)  # Percentage formatted to 2 decimal places
            }
            results.append(result)

    # Convert the results to a DataFrame
    result_df = pd.DataFrame(results)

    # Save to Excel in the respective table folder
    save_outlier_to_excel(result_df, table_name)

def save_outlier_to_excel(df, table_name):
    """Save the results to an Excel file in the respective folder."""
    # Create the folder for the table if it doesn't exist
    folder_path = os.path.join(OUTPUT_PATH, table_name)
    os.makedirs(folder_path, exist_ok=True)  # Ensure the folder is created
    
    # Define the file path for the outlier check results
    file_path = os.path.join(folder_path, "outlier_check.xlsx")
    
    # Write data to Excel, creating the file if it doesn't exist, or append if it does
    with pd.ExcelWriter(file_path, engine='openpyxl', mode='w') as writer:
        df.to_excel(writer, index=False, header=True, sheet_name='Outlier Check')

def run_outlier_checks_for_all_tables():
    """Run outlier check for all tables and save results to Excel."""
    # List of tables to analyze
    tables = ["team_info", "player_game_logs", "player_info_analysis", "player_shot_logs"]
    
    conn = get_connection()  # Connect to the database

    for table in tables:
        # Run outlier check for each table
        check_outliers_iqr(conn, table)

    conn.close()  # Close the connection

if __name__ == "__main__":
    run_outlier_checks_for_all_tables()


