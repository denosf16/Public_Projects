import streamlit as st
import pandas as pd
import os
from app import structure

def show():
    st.title("🏠 Bio-Mech Velocity Dashboard")
    st.markdown("Built by **Sam Denomme** — Modeling fastball velocity using biomechanics data.")

    # ----------------------------
    # 📘 Summary + Purpose (Wrapped in Expander)
    # ----------------------------
    with st.expander("📘 Summary + Purpose"):
        st.markdown("""
        Developed a multi-model framework to estimate fastball velocity using biomechanical inputs derived from markerless motion capture. Across four modeling techniques—Random Forest, ElasticNet, GAM, and MLP—this system quantifies the mechanical contributors to pitch speed through force generation, energy transfer, and sequencing metrics.

        Each model variant captures a different biomechanical domain (e.g., ground reaction force, lower body rotation, upper body torque), with the full model integrating these components holistically. Feature selection relied on a combination of Random Forest importance, Maximal Information Coefficient (MIC) for non-linear effects, and VIF-based multicollinearity filtering.

        This approach serves as both a diagnostic and prescriptive tool—identifying inefficiencies, tracking development, and highlighting mechanical levers for velocity gains.
        """)

    st.markdown("---")

    # ----------------------------
    # 📊 Dataset Overview
    # ----------------------------
    st.subheader("📊 Dataset Overview")

    try:
        data = structure.load_cleaned_data()
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Total Pitches", f"{len(data):,}")
        with col2:
            st.metric("Unique Users", f"{data['user'].nunique():,}")
        with col3:
            st.metric("Total Features", f"{data.select_dtypes(include='number').shape[1]:,}")
    except Exception as e:
        st.error(f"Error loading cleaned data: {e}")
        return

    st.markdown("---")

    # ----------------------------
    # 🎛 Select Model Configuration
    # ----------------------------
    st.subheader("🧭 Select Model Configuration")

    model_variants = structure.list_model_variants()
    default_index = model_variants.index("full_model") if "full_model" in model_variants else 0
    model_variant = st.selectbox("Select Model Variant", model_variants, index=default_index, key="home_model_variant")
    technique = st.selectbox("Select Technique", structure.list_techniques(), key="home_technique")

    st.session_state["model_variant"] = model_variant
    st.session_state["technique"] = technique

    st.markdown("---")

    # ----------------------------
    # 🎯 Model Performance (Based on Filters)
    # ----------------------------
    st.subheader("🎯 Model Performance")

    try:
        model_metrics = structure.load_model_metrics()
        filtered = model_metrics[
            (model_metrics["model_variant"] == model_variant) &
            (model_metrics["technique"] == technique) &
            (model_metrics["split"] == "test")
        ]

        if not filtered.empty:
            row = filtered.iloc[0]

            def colorize(val, good, okay, inverse=False):
                if inverse:
                    if val <= good: return "green"
                    elif val <= okay: return "orange"
                    return "red"
                else:
                    if val >= good: return "green"
                    elif val >= okay: return "orange"
                    return "red"

            r2_val = row["r2"]
            rmse_val = row["rmse"]
            mae_val = row["mae"]

            r2_color = colorize(r2_val, 0.70, 0.50)
            rmse_color = colorize(rmse_val, 2.5, 3.5, inverse=True)
            mae_color = colorize(mae_val, 2, 3, inverse=True)

            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown("<h5 style='text-align:center;'>R²</h5>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='text-align:center; color:{r2_color};'>{r2_val:.2f}</h2>", unsafe_allow_html=True)
            with col2:
                st.markdown("<h5 style='text-align:center;'>RMSE</h5>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='text-align:center; color:{rmse_color};'>{rmse_val:.2f}</h2>", unsafe_allow_html=True)
            with col3:
                st.markdown("<h5 style='text-align:center;'>MAE</h5>", unsafe_allow_html=True)
                st.markdown(f"<h2 style='text-align:center; color:{mae_color};'>{mae_val:.2f}</h2>", unsafe_allow_html=True)
        else:
            st.warning("No matching results for the selected model + technique.")
    except Exception as e:
        st.warning(f"Could not load model metrics: {e}")

    st.markdown("---")

