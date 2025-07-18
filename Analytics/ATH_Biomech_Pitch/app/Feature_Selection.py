import os
import pandas as pd
import streamlit as st
from app import structure

def show():
    st.title("🧠 Feature Selection")

    # ----------------------------
    # 📘 Summary Description
    # ----------------------------
    with st.expander("📘 Process Overview", expanded=True):
        st.markdown("""
        This page summarizes the feature selection pipeline used to identify biomechanical predictors of fastball velocity:

        1. **Correlation Filtering** (`|r| > 0.1`)  
           Pearson correlation used to filter biomechanically relevant predictors.

        2. **Multi-Method Scoring**  
           - Random Forest (2500 trees)  
           - Mutual Information (non-linear)  
           - Lasso Regression (sparse selection)  
           → Combined via a weighted ensemble score.

        3. **Correlation Clustering** (`|r| > 0.85`)  
           Groups redundant variables; top performer per group retained.

        4. **Final Outputs**  
           - `selected_features.csv`: Final model input set  
           - `feature_scores.csv`: Scoring + correlation/R²  
           - Histograms and scatterplots for all final variables
        """)

    st.markdown("---")

    # ----------------------------
    # 📊 Feature Score Table
    # ----------------------------
    st.subheader("📊 Feature Scoring Table")

    try:
        df = structure.load_feature_scores()
        df.columns = [c.lower() for c in df.columns]

        sort_col = st.selectbox("Sort by", options=["ensemble_score", "rf", "mi", "lasso", "correlation", "r2"], index=0)
        df_sorted = df.sort_values(by=sort_col, ascending=False)

        st.dataframe(df_sorted.style.format({
            "ensemble_score": "{:.3f}",
            "rf": "{:.3f}",
            "mi": "{:.3f}",
            "lasso": "{:.3f}",
            "correlation": "{:.3f}",
            "r2": "{:.3f}"
        }), use_container_width=True)

        st.download_button(
            label="📥 Download feature_scores.csv",
            data=df_sorted.to_csv(index=False),
            file_name="feature_scores.csv",
            mime="text/csv"
        )
    except Exception as e:
        st.error(f"Error loading feature scores: {e}")

    st.markdown("---")

    # ----------------------------
    # 📈 Visual Summaries
    # ----------------------------
    st.subheader("📈 Visual Summary")

    summary_plot = st.selectbox("Select visual summary", [
        "Correlation Heatmap (|r| ≥ 0.1)",
        "Random Forest Importance",
        "Mutual Information (MIC)"
    ])

    plot_key = {
        "Correlation Heatmap (|r| ≥ 0.1)": "correlation_heatmap",
        "Random Forest Importance": "rf_importance",
        "Mutual Information (MIC)": "mi_importance"
    }[summary_plot]

    plot_path = structure.get_eda_plot(plot_key, kind="image")
    if os.path.exists(plot_path):
        st.image(plot_path, caption=summary_plot, use_container_width=True)
    else:
        st.warning(f"{summary_plot} plot not found.")





