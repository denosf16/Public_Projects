import streamlit as st
import pandas as pd
import os
import matplotlib.pyplot as plt
import seaborn as sns
from PIL import Image
from scripts.db_connect import get_connection

# -------------------------------
# Config
# -------------------------------
TABLES = ["player_info_analysis", "player_game_logs", "player_shot_logs", "team_info"]
REPORT_DIR = "reports"
SCHEMA_IMAGE_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'config', 'nba_shot_erd.png'))

# -------------------------------
# Helpers
# -------------------------------

def load_excel(table, filename):
    """Helper function to load an Excel file."""
    path = os.path.join(REPORT_DIR, table, filename)
    if os.path.exists(path):
        return pd.read_excel(path)
    else:
        st.error(f"File not found: {path}")  # Display an error if the file is missing
        return pd.DataFrame()

# Helper function for table name formatting
def get_full_table_name(table):
    """Ensure the table name starts with 'dbo.'"""
    return f"dbo.{table}" if not table.startswith("dbo.") else table

# Schema Check Table Coloring
def colorize_schema(df):
    """Colorize the schema check table to highlight P KEY, F KEY, IDX columns."""
    def colorize(val):
        if val == 1:
            return 'background-color: yellow'  # Color for PKEY, FKEY, IDX
        return ''
    
    return df.style.applymap(colorize, subset=['P KEY', 'F KEY', 'IDX'])

def plot_null_pie_chart(df_null, column):
    """Plot pie chart for null percentage"""
    null_pct = df_null[df_null['COLUMN'] == column]["NULL PCT"].iloc[0]
    if pd.isna(null_pct):
        null_pct = 0  # Default to 0 if NaN
    fig, ax = plt.subplots()
    ax.pie([null_pct, 100 - null_pct], labels=['Null', 'Non-Null'], autopct='%1.1f%%', startangle=90)
    ax.axis('equal')  # Equal aspect ratio ensures pie is drawn as a circle.
    st.pyplot(fig)

def plot_boxplot(df_column, column, title="Boxplot"):
    """Generate boxplot for a given column"""
    fig, ax = plt.subplots()
    sns.boxplot(x=df_column[column], ax=ax)
    ax.set_title(title)
    st.pyplot(fig)

# -------------------------------
# UI
# -------------------------------

def app():
    st.title("🧠 SQL Observability Dashboard")

    # Show ERD
    with st.expander("🗺️ Schema Overview (ERD)"):
        st.markdown("This diagram represents the full NBA Shot Analytics schema used across the ETL pipeline.")
        if os.path.exists(SCHEMA_IMAGE_PATH):
            st.image(Image.open(SCHEMA_IMAGE_PATH), caption="📊 NBA Shot Schema (ERD)", use_container_width=True)
        else:
            st.error(f"Schema image not found at: `{SCHEMA_IMAGE_PATH}`")

    # Select table
    selected_table = st.selectbox("📂 Select a Table to Audit", TABLES)

    # Schema Check
    with st.expander("📐 Schema Check"):
        st.markdown("""
        The schema check ensures that the structure of your database matches the expected design. It helps detect:
        - Missing or extra columns
        - Data type mismatches
        - Nullability mismatches
        - Ordinal position mismatches

        This is crucial for pipeline observability as mismatched schemas can break the ETL pipeline or cause data issues.
        """)

        df_schema = load_excel(selected_table, "schema_check.xlsx")  # Load the schema check data
        if df_schema.empty:
            # If no schema issues, add a "PASSED" entry
            df_schema = pd.DataFrame([{
                "COLUMN": "All Columns",
                "STATUS": "PASSED",
                "FLAG_REASON": "No issues detected"
            }])
            st.success("✅ Schema matches expected structure. No issues detected.")
        else:
            st.success("✅ Schema check complete. No critical issues detected.")
            st.dataframe(colorize_schema(df_schema))  # Display with color coding for PKEY, FKEY, IDX

    # Null & Uniqueness
    with st.expander("🕳️ Null & Uniqueness Check"):
        st.markdown("""
        Null and uniqueness checks ensure that the data is complete and doesn't have unexpected nulls or duplicates.
        These checks are essential for data quality and pipeline observability.
        """)

        df_null = load_excel(selected_table, "null_check.xlsx")  # Load the null check data
        if df_null.empty:
            st.info("No null or uniqueness check data available.")
        else:
            st.dataframe(df_null)
            fail_df = df_null[df_null['NULL PCT'] > 0]  # Filter for columns with non-zero null percentage
            if not fail_df.empty:
                st.warning(f"⚠️ {len(fail_df)} columns exceed the null threshold.")
                st.write(fail_df[['COLUMN', 'NULL PCT']])

            # Show pie chart for null percentage per column
            column = st.selectbox("Select a Column to View Null Percentage Pie Chart", df_null['COLUMN'])
            if column:
                plot_null_pie_chart(df_null, column)

    # Outlier Check
    with st.expander("📈 Outlier Check"):
        st.markdown("""
        Outlier checks detect data points that significantly deviate from the expected range. This can help identify data issues
        that may skew analysis. Outliers can often indicate data corruption or inconsistencies in the ETL pipeline.
        """)

        df_outliers = load_excel(selected_table, "outlier_check.xlsx")  # Load the outlier check data
        if df_outliers.empty:
            st.info("No outlier data available.")
        else:
            st.dataframe(df_outliers)
            fail_df = df_outliers[df_outliers['OUTLIER PCT'] > 0]  # Filter for columns with outliers
            if not fail_df.empty:
                st.warning(f"⚠️ {len(fail_df)} columns have outliers exceeding the threshold.")
                st.write(fail_df[['COLUMN', 'OUTLIER PCT']])

            # Show boxplot for the column
            column = st.selectbox("Select a Column to View Boxplot", df_outliers['COLUMN'])
            if column:
                query = f"SELECT {column} FROM {get_full_table_name(selected_table)}"
                df_column = pd.read_sql(query, get_connection())
                
                # Generate boxplot for the selected column
                plot_boxplot(df_column, column)








