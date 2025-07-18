# scripts/db_connect.py

import pyodbc
import os

SERVER_NAME = "RAMSEY_BOLTON\\SQLEXPRESS"
DRIVER = "ODBC Driver 17 for SQL Server"

def get_connection(database="NBA_Shots"):
    """
    Connect to the specified database (default: NBA_Shots).
    """
    conn_str = (
        f"DRIVER={{{DRIVER}}};"
        f"SERVER={SERVER_NAME};"
        f"DATABASE={database};"
        "Trusted_Connection=yes;"
    )
    return pyodbc.connect(conn_str)

def get_master_connection():
    """
    Connect to the master database (used to create NBA_Shots if it doesn't exist).
    """
    return get_connection("master")

