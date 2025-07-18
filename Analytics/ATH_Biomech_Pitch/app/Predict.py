import os
import pandas as pd
import numpy as np
import joblib
import streamlit as st
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import r2_score
from utils import config
from app import structure

# ----------------------------
# 🔧 Paths and Setup
# ----------------------------
TEST_PATH = os.path.join(config.DATA_PATH, "test.csv")
MODEL_BASE = os.path.join(config.OUTPUT_PATH, "models")
DEFAULT_TECHNIQUE = "rf"
DEFAULT_VARIANT = "full_model"
techniques = structure.list_techniques()
variants = structure.list_model_variants()

# ----------------------------
# 📊 Plotting Functions
# ----------------------------
def plot_actual_vs_pred(y_true, y_pred, title):
    fig, ax = plt.subplots()
    ax.scatter(y_true, y_pred, alpha=0.6)
    ax.plot([y_true.min(), y_true.max()], [y_true.min(), y_true.max()], "r--")
    ax.set_xlabel("Actual")
    ax.set_ylabel("Predicted")
    ax.set_title(title)
    return fig

def plot_residuals(y_true, y_pred, title):
    residuals = y_true - y_pred
    fig, ax = plt.subplots()
    ax.scatter(y_pred, residuals, alpha=0.5)
    ax.axhline(0, color='red', linestyle='--')
    ax.set_xlabel("Predicted")
    ax.set_ylabel("Residuals")
    ax.set_title(title)
    return fig

def plot_error_histogram(y_true, y_pred, title):
    errors = y_true - y_pred
    fig, ax = plt.subplots()
    ax.hist(errors, bins=30, alpha=0.7)
    ax.set_title(title)
    ax.set_xlabel("Prediction Error")
    ax.set_ylabel("Frequency")
    return fig

def plot_kde_overlay(y_true, y_pred, title):
    fig, ax = plt.subplots()
    sns.kdeplot(y_true, label="Actual", ax=ax)
    sns.kdeplot(y_pred, label="Predicted", ax=ax)
    ax.set_title(title)
    ax.legend()
    return fig

def plot_r2_bar(df, group_col):
    fig, ax = plt.subplots()
    sns.barplot(data=df, x="Group", y="R²", ax=ax)
    ax.set_title(f"R² by {group_col}")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    return fig

def plot_boxplot_by_group(df, group_col):
    fig, ax = plt.subplots()
    sns.boxplot(data=df, x=group_col, y="pitch_speed_mph", color="lightblue", width=0.5)
    sns.boxplot(data=df, x=group_col, y="preds", color="orange", width=0.3)
    ax.set_title(f"Actual vs Predicted by {group_col}")
    ax.set_ylabel("Fastball Velocity")
    ax.set_xticklabels(ax.get_xticklabels(), rotation=45)
    return fig

# ----------------------------
# 🔮 Prediction Logic
# ----------------------------
def make_prediction(variant, technique):
    model_path = os.path.join(MODEL_BASE, technique, f"{variant}.joblib")
    encoded_file = os.path.join(MODEL_BASE, technique, f"{variant}_encoded_features.pkl")

    if not os.path.exists(model_path) or not os.path.exists(encoded_file):
        st.error(f"Missing model or encoded features for {technique} - {variant}")
        return None

    df = pd.read_csv(TEST_PATH)
    features = structure.get_model_features(variant)
    df = df.dropna(subset=features + ["pitch_speed_mph"])
    X = pd.get_dummies(df[features])
    encoded_features = joblib.load(encoded_file)
    X = X.reindex(columns=encoded_features, fill_value=0).astype(float)
    y = df["pitch_speed_mph"]
    model = joblib.load(model_path)
    preds = model.predict(X)

    return df.assign(preds=preds), r2_score(y, preds)

# ----------------------------
# 🧠 Streamlit Page
# ----------------------------
def show():
    st.title("🤖 Predict Fastball Velocity")
    st.markdown("Use trained models to predict fastball velocity on unseen biomechanical test data.")
    with st.expander("📊 Prediction Summary"):
         st.markdown("""
 Model predictions are evaluated across **groups of interest** to assess fairness and consistency in performance.

 **How it works:**
 - The trained model (`rf` + `full_model` by default) predicts fastball velocity on a held-out test set.
 - Predictions are broken down by **throwing hand (`p_throws`)** and **playing level (`playing_level`)**.
 - Each group is visualized with:
  - **Actual vs. Predicted Plot**: Alignment of predictions to true values.
  - **Residual Plot**: Checks for bias or trends in prediction errors.
  - **Prediction Error Histogram**: Shows distribution of error magnitudes.
  - **KDE Overlay**: Compares prediction distributions against true values.

 **Group Summary:**
 - An **R² leaderboard** ranks groups by prediction accuracy.
 - **Bar chart** and **boxplot** help compare performance across group conditions.

 This breakdown ensures the model performs reliably for different player types, highlighting areas for refinement or further training data.
 """)

    model_variant = st.selectbox("Model Variant", variants, index=variants.index(DEFAULT_VARIANT))
    technique = st.selectbox("Technique", techniques, index=techniques.index(DEFAULT_TECHNIQUE))

    st.markdown("---")
    st.header("🔍 Group-Level Evaluation (Always Enabled)")
    st.caption("Choose which group to evaluate prediction accuracy by. All plots reflect per-group performance.")

    group_col = st.radio("Group By", ["p_throws", "playing_level"], horizontal=True)
    result = make_prediction(model_variant, technique)

    if result:
        df, global_r2 = result
        st.success(f"✅ Global R²: `{global_r2:.3f}`")

        if group_col not in df.columns:
            st.warning(f"{group_col} not found in test data.")
            return

        group_r2_data = []

        for group_val in sorted(df[group_col].dropna().unique()):
            sub_df = df[df[group_col] == group_val]
            if len(sub_df) < 5:
                continue

            r2 = r2_score(sub_df["pitch_speed_mph"], sub_df["preds"])
            group_r2_data.append({"Group": group_val, "R²": round(r2, 3)})

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"##### {group_val} — Act. vs. Pred.")
                st.pyplot(plot_actual_vs_pred(sub_df["pitch_speed_mph"], sub_df["preds"], f"{group_val} — A vs P"))
            with col2:
                st.markdown(f"##### {group_val} — Residuals")
                st.pyplot(plot_residuals(sub_df["pitch_speed_mph"], sub_df["preds"], f"{group_val} — Residuals"))

            col3, col4 = st.columns(2)
            with col3:
                st.markdown(f"##### {group_val} — Pred. Error Hist.")
                st.pyplot(plot_error_histogram(sub_df["pitch_speed_mph"], sub_df["preds"], f"{group_val} — Error Hist"))
            with col4:
                st.markdown(f"##### {group_val} — KDE Overlay")
                st.pyplot(plot_kde_overlay(sub_df["pitch_speed_mph"], sub_df["preds"], f"{group_val} — KDE"))

        if group_r2_data:
            st.markdown("---")
            st.header("📈 Group Performance Summary")
            st.caption("R² leaderboard and comparisons for selected group.")

            leaderboard_df = pd.DataFrame(group_r2_data).sort_values("R²", ascending=False).reset_index(drop=True)
            st.markdown("##### R² Leaderboard")
            st.dataframe(leaderboard_df, use_container_width=True)

            col1, col2 = st.columns(2)
            with col1:
                st.markdown(f"##### R² by {group_col}")
                st.pyplot(plot_r2_bar(leaderboard_df, group_col="Group"))
            with col2:
                st.markdown(f"##### Act. vs Pred. Boxplot by {group_col}")
                st.pyplot(plot_boxplot_by_group(df, group_col=group_col))

            st.download_button("📥 Download Group R² Table", data=leaderboard_df.to_csv(index=False), file_name="group_r2_summary.csv")









