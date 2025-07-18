import streamlit as st
import pandas as pd
import numpy as np
import os
import matplotlib.pyplot as plt
import seaborn as sns
from app import structure

def show():
    st.title("🧼 Data Cleaning + Diagnostics")

    # ----------------------------
    # 📘 Cleaning Pipeline Summary (Wrapped in expander)
    # ----------------------------
    with st.expander("🧼 Cleaning Pipeline Summary"):
        st.markdown("""
        This dataset merges pitch-level biomechanical data with player metadata using a shared `session_pitch` key. Cleaning and diagnostics steps include:

        1. **Missing Value Imputation**  
        → A custom helper applies ML-based imputation (e.g., KNN or Random Forest) to preserve interaction structure.

        2. **Normality Testing (Shapiro-Wilk)**  
        → All numeric features were tested for normality (p > 0.05 = Gaussian).

        3. **Outlier Flagging**  
        → Z-Score method used for Gaussian columns; IQR used for non-Gaussian ones.  
        → No rows were dropped; `_outlier` flags were appended instead.

        4. **Outputs**  
        → Cleaned dataset saved to `data/pitch_data_cleaned.csv`  
        → Normality + outlier summaries written to `outputs/eda_data/`
        """)

    st.markdown("---")

    # ----------------------------
    # 📂 Load Data + Diagnostics
    # ----------------------------
    try:
        df = pd.read_csv(os.path.join(structure.BASE_DIR, "data", "pitch_data_cleaned.csv"))
        normality_df = structure.load_normality_summary()
        outliers_df = structure.load_outlier_counts()
    except Exception as e:
        st.error(f"Error loading data or diagnostics: {e}")
        return

    # ----------------------------
    # 🔍 Explore Variable Distribution
    # ----------------------------
    st.subheader("🔍 Explore Variable Distribution")

    numeric_cols = df.select_dtypes(include='number').columns.tolist()
    selected_var = st.selectbox("Select a variable", options=sorted(numeric_cols))
    plot_type = st.radio("Choose plot type", options=["Histogram", "Scatterplot"], horizontal=True)

    fig, ax = plt.subplots()

    try:
        if plot_type == "Histogram":
            sns.histplot(df[selected_var], bins=40, kde=True, ax=ax, color="steelblue")
            ax.set_title(f"Histogram: {selected_var}")
            st.pyplot(fig)

        elif plot_type == "Scatterplot":
            if "pitch_speed_mph" in df.columns:
                sns.set_theme(style="whitegrid")
                sns.regplot(
                    data=df,
                    x=selected_var,
                    y="pitch_speed_mph",
                    ax=ax,
                    scatter_kws={"color": "#1f77b4", "alpha": 0.6},
                    line_kws={"color": "red", "linestyle": "-", "linewidth": 2},
                    ci=95
                )
                ax.set_title(f"{selected_var} vs. Pitch Speed", fontsize=14)
                ax.set_xlabel(selected_var)
                ax.set_ylabel("pitch_speed_mph")
                st.pyplot(fig)
            else:
                st.warning("`pitch_speed_mph` not found — scatterplot unavailable.")
    except Exception as e:
        st.warning(f"Could not generate plot: {e}")

    st.markdown("---")

    # ----------------------------
    # 📊 Distribution + Outlier Summary
    # ----------------------------
    st.subheader("📊 Distribution + Outlier Summary")

    with st.expander("📄 Normality Results (Shapiro-Wilk)"):
        normality_df["p_value"] = normality_df["p_value"].round(6)
        st.dataframe(normality_df)

    with st.expander("🚩 Outlier Counts"):
        st.dataframe(outliers_df)

    with st.expander("📥 Download Cleaned Data"):
        st.download_button(
            label="Download `pitch_data_cleaned.csv`",
            data=df.to_csv(index=False),
            file_name="pitch_data_cleaned.csv",
            mime="text/csv"
        )
