import streamlit as st
import pandas as pd
import os
from PIL import Image

# --- Config ---
AVAILABLE_MODELS = ["logreg_v2", "rf_v1", "rf_v3", "xgb_v2"]
CONFUSION_PATH = "output/confusion_matrix"
RESIDUAL_PATH = "output/residual_analysis"
QQ_PATH = "output/qq_plots"
ACTUAL_PRED_PATH = "output/actual_pred"
COURT_PATH = "output/court_overlay"
CALIBRATION_PATH = "output/calibration_curves"
GROUPED_PATH = "output/group_eval"

# --- Helper ---
def load_image(path):
    return Image.open(path) if os.path.exists(path) else None

def get_filename(base, model):
    return f"{base}_{model}.png"

# --- App ---
def app():
    st.title("📊 Model Evaluation & Diagnostics")

    # ============================
    # SECTION 1: Global Comparison
    # ============================
    st.header("📈 Global Model Comparison")

    try:
        df = pd.read_csv("output/model_results.csv")
        df = df[df["Model"].str.contains("v2|v3|v1")]
        st.dataframe(df, use_container_width=True)
    except FileNotFoundError:
        st.warning("model_results.csv not found.")

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("📉 ROC Curve Overlay")
        roc_img = load_image(os.path.join(GROUPED_PATH, "roc_curves.png"))
        if roc_img:
            st.image(roc_img, caption="ROC Curves for All Models", use_container_width=True)

    with col2:
        st.subheader("🧪 Calibration Curve")
        cal_img = load_image(os.path.join(CALIBRATION_PATH, "calibration_curves.png"))
        if cal_img:
            st.image(cal_img, caption="Calibration Curve Overview", use_container_width=True)

    st.subheader("📊 Grouped Evaluation (Distance / Context)")
    try:
        grouped_df = pd.read_csv(os.path.join(GROUPED_PATH, "grouped_eval.csv"))
        st.dataframe(grouped_df, use_container_width=True)
    except:
        st.warning("grouped_eval.csv not found.")

    barplot_img = load_image(os.path.join(GROUPED_PATH, "grouped_eval.png"))
    if barplot_img:
        st.image(barplot_img, caption="Grouped Accuracy / AUC", use_container_width=True)

    # ============================
    # SECTION 2: Per-Model Diagnostics
    # ============================
    st.header("🧬 Individual Model Diagnostics")

    selected_model = st.selectbox("Choose a model", AVAILABLE_MODELS)

    st.subheader("🧾 Confusion Matrix")
    cm_path = os.path.join(CONFUSION_PATH, get_filename("confusion_matrix", selected_model))
    cm_img = load_image(cm_path)
    if cm_img:
        st.image(cm_img, caption=f"Confusion Matrix: {selected_model}", use_container_width=True)

    st.subheader("📊 Diagnostic Plots")
    tabs = st.tabs(["Residual Histogram", "QQ Plot", "Actual vs. Predicted", "Residual vs. Shot Distance"])

    with tabs[0]:
        img = load_image(os.path.join(RESIDUAL_PATH, get_filename("residual_hist", selected_model)))
        if img:
            st.image(img, caption="Residual Histogram", use_container_width=True)
        else:
            st.warning("Residual histogram not available.")

    with tabs[1]:
        img = load_image(os.path.join(QQ_PATH, get_filename("qq", selected_model)))
        if img:
            st.image(img, caption="QQ Plot", use_container_width=True)
        else:
            st.warning("QQ plot not available.")

    with tabs[2]:
        img = load_image(os.path.join(ACTUAL_PRED_PATH, get_filename("actual_vs_pred", selected_model)))
        if img:
            st.image(img, caption="Actual vs. Predicted", use_container_width=True)
        else:
            st.warning("Actual vs. predicted plot not available.")

    with tabs[3]:
        img = load_image(os.path.join(RESIDUAL_PATH, get_filename("residual_vs_distance", selected_model)))
        if img:
            st.image(img, caption="Residuals vs. SHOT_DIST", use_container_width=True)
        else:
            st.warning("Residual vs. SHOT_DIST plot not available.")

    # ============================
    # SECTION 3: Court Visualizations
    # ============================
    st.header("🏀 Court-Based Shot Visualizations")

    court_tabs = st.tabs(["1D Shot Map", "Court Overlay Heatmaps"])

    with court_tabs[0]:
        col1, col2 = st.columns(2)
        img1 = load_image(os.path.join(ACTUAL_PRED_PATH, "shot_map_actual.png"))
        img2 = load_image(os.path.join(ACTUAL_PRED_PATH, "shot_map_predicted.png"))
        if img1:
            col1.image(img1, caption="Actual FG% by Distance", use_container_width=True)
        if img2:
            col2.image(img2, caption="Predicted FG% by Distance", use_container_width=True)

    with court_tabs[1]:
        st.markdown("FG% Probability Overlays (Full Court View)")
        heatmap_cols = st.columns(2)
        overlays = [
            ("court_logreg_v2_prob.png", "Logistic Regression (v2)"),
            ("court_rf_v3_prob.png", "Random Forest (v3)"),
            ("court_xgb_v2_prob.png", "XGBoost (v2)"),
            ("court_y_true.png", "Actual Makes"),
        ]

        for i, (fname, label) in enumerate(overlays):
            img = load_image(os.path.join(COURT_PATH, fname))
            if img:
                with heatmap_cols[i % 2]:
                    st.image(img, caption=label, use_container_width=True)


