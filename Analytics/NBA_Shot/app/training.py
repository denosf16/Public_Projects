import streamlit as st
import pandas as pd
import plotly.express as px

def app():
    st.title("🧪 Model Training & Selection Overview")

    # --- Introduction ---
    st.markdown("""
    This page summarizes the model development process for predicting shot success (`SHOT_MADE`) using contextual and defender-related features.
    
    The modeling pipeline followed the supervised learning framework:
    > **Data Cleaning → Feature Engineering → Model Training → Evaluation → Deployment**
    
    We compare four model families trained offline:
    
    - **Logistic Regression (v2)**: A linear, interpretable baseline with interaction terms  
    - **Random Forest (v3)**: A bagging-based tree ensemble capturing nonlinearities and interactions  
    - **XGBoost (v1)**: A boosting model tuned on raw + interaction features  
    - **XGBoost (v2)**: A bin-weighted variant accounting for distance-based class imbalance  
    """)

    st.markdown("---")
    st.subheader("📐 Model Equations and Strategy")

    col1, col2 = st.columns(2)

    with col1:
        st.markdown("""
        #### Logistic Regression (v2)
        Linear model with log-odds formulation:
        $$
        P(\\text{SHOT\\_MADE}=1) = \\frac{1}{1 + e^{- (\\beta_0 + \\sum \\beta_i X_i)}}
        $$
        - Includes manually engineered terms:
          - `SCxTT = SHOT_CLOCK × TOUCH_TIME`
          - `CDxHD = CLOSE_DEF_DIST × HEIGHT_DIFFERENTIAL`
        - Grid-searched over penalty type (`l1`, `l2`) and regularization strength (`C`)
        """)

    with col2:
        st.markdown("""
        #### Random Forest (v3)
        Ensemble of bootstrapped decision trees:
        $$
        P(\\text{SHOT\\_MADE}=1) = \\frac{1}{T} \\sum_{t=1}^{T} h_t(X)
        $$
        - Feature space included:
          - `TOUCH_TIME`, `HEIGHT_DIFFERENTIAL`, `CLOCK_TOUCH`, `HEIGHT_CLOSE`
        - Hyperparameters tuned:
          - `n_estimators`, `max_depth`, `min_samples_leaf`, `max_features`
        """)

    st.markdown("""
    #### XGBoost (v1 & v2)
    Gradient-boosted trees with additive updates:
    $$
    F_m(x) = F_{m-1}(x) + \\eta \\cdot h_m(x)
    $$
    - v1: Added `DIST_x_CLOSE_DEF` interaction  
    - v2: Applied one-hot encoding to `SHOT_DIST` bins + `DIST_x_DEF` interaction  
    - Used `class_weight='balanced'` by bin to mitigate distance imbalance  
    """)

    st.markdown("---")
    st.subheader("📊 Model Evaluation: Log Loss")

    try:
        results_df = pd.read_csv("output/model_results.csv")
        st.dataframe(results_df, use_container_width=True)

        fig = px.bar(
            results_df,
            x="Model", y="Log Loss", color="Model",
            title="Model Comparison: Log Loss (Lower = Better)",
            text_auto=".3f"
        )
        st.plotly_chart(fig, use_container_width=True)
    except FileNotFoundError:
        st.warning("⚠️ Model results not found. Please run training scripts.")

    st.markdown("---")
    st.subheader("🎛️ Hyperparameter Tuning Strategy")

    st.markdown("""
    All models were tuned using **GridSearchCV** with 5-fold cross-validation and `neg_log_loss` scoring.
    
    | Model          | Key Hyperparameters                             | Selection Basis                     |
    |----------------|--------------------------------------------------|-------------------------------------|
    | Logistic Reg.  | `C`, `penalty`, `solver`                         | Best out-of-sample log loss         |
    | Random Forest  | `n_estimators`, `max_depth`, `min_samples_leaf` | Balance of stability and flexibility |
    | XGBoost (v1/v2)| `learning_rate`, `depth`, `colsample_bytree`     | Best in class when tuned properly   |
    
    📌 Hyperparameters control **model capacity** and the **bias–variance tradeoff**. Grid search ensures reproducibility and robustness (see `train_log.py`, `train_rf.py`, `train_xgbv2.py`).
    """)

    st.markdown("---")
    st.subheader("🧠 Modeling Philosophy & Tradeoffs")

    st.markdown("""
    - **Logistic Regression**  
      ✅ Interpretable  
      ✅ Coefficients show directional influence  
      ❌ Cannot model nonlinear effects or interactions unless manually added
    
    - **Random Forest**  
      ✅ Robust to overfitting with enough trees  
      ✅ Captures nonlinear patterns + interactions automatically  
      ❌ Requires careful tuning (depth, leaf size)
    
    - **XGBoost**  
      ✅ Best performance in many structured data tasks  
      ✅ Additive corrections help learn subtle signal  
      ❌ Requires binning/weighting to handle imbalanced contexts
    
    **Why multiple models?**  
    Because interpretability, generalization, and performance aren’t always aligned.
    
    👉 We retain all trained models and compare their behavior in the evaluation stage.
    """)

    st.markdown("---")
    st.subheader("📌 Pipeline Architecture")

    st.markdown("""
    ```
    [Raw Shot Logs]
          ↓
    [Data Cleaning + Filtering]
          ↓
    [Feature Engineering]
          ↓
    [Model Training]
          ↓
    [Evaluation & Diagnostics]
          ↓
    [Court-Level Visualization]
    ```

    All models are trained offline and version-controlled (`logreg_model_v2.pkl`, `rf_model_v3.pkl`, `xgb_model_v2.pkl`) and are loaded into this app for evaluation only.
    """)

    st.success("Navigate to **Model Evaluation** to explore confusion matrices, ROC curves, calibration, and grouped shot context accuracy.")



