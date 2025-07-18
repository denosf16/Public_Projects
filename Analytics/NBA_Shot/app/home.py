import streamlit as st
import sys
import os

# Set page-wide config
st.set_page_config(
    page_title="NBA Shot Analytics",
    page_icon="🏀",
    layout="wide",
    initial_sidebar_state="expanded"
)

# 🔧 Ensure project root is in the Python module path
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# Import sibling modules
import sql_observability
import data_preprocessing
import feature_engineering
import training
import evaluation
import reflection  # ✅ NEW: Import reflection module

PAGES = {
    "Home": None,  # handled specially
    "SQL Observability": sql_observability.app,
    "Data Preprocessing": data_preprocessing.app,
    "Feature Engineering": feature_engineering.app,
    "Model Training": training.app,
    "Model Evaluation": evaluation.app,
    "Model Reflection": reflection.app  # ✅ NEW: Add to nav
}

def home_page():
    st.title("🏀 NBA Shot Analytics Dashboard")
    st.markdown(
        """
        Welcome to the NBA Shot Analytics project! This platform guides you through the entire analytics workflow—from raw data ingestion and cleaning, to feature engineering, model training, evaluation, and pipeline observability.

        Use the sidebar menu to navigate between modules:
        - **SQL Observability**
        - **Data Preprocessing**
        - **Feature Engineering**
        - **Model Training**
        - **Model Evaluation**
        - **Model Reflection** (Insights & Next Steps)
        """
    )
    st.markdown("---")
    st.subheader("Project Highlights")
    st.write(
        """
        - End-to-end NBA shot analytics pipeline  
        - SQL Server backend with robust ETL monitoring  
        - Modular Python code for data, features, and modeling  
        - Interactive dashboards via Streamlit  
        - Model diagnostics, calibration, spatial overlays, and error analysis
        """
    )
    st.markdown("---")
    st.info("Select a page from the sidebar to begin your workflow.")

def main():
    st.sidebar.title("Navigation")
    choice = st.sidebar.radio("Go to", list(PAGES.keys()))

    if choice == "Home":
        home_page()
    else:
        PAGES[choice]()

if __name__ == "__main__":
    main()






