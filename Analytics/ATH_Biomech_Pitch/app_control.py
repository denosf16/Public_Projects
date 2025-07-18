import streamlit as st
from app import Home, Data_Cleaning, Feature_Selection, Model_Training, Evaluate, Predict

PAGES = {
    "🏠 Home": Home,
    "🧼 Data Cleaning": Data_Cleaning,
    "🧠 Feature Selection": Feature_Selection,
    "🔧 Model Training": Model_Training,
    "📊 Evaluate": Evaluate,
    "🤖 Predict": Predict,
}

st.sidebar.title("Navigation")
selection = st.sidebar.radio("Go to", list(PAGES.keys()))
PAGES[selection].show()
# Predict.py � auto-created by setup script
