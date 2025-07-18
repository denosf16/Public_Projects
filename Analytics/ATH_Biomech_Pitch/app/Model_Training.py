import os
import time
import pandas as pd
import numpy as np
import streamlit as st
import joblib
from sklearn.metrics import mean_squared_error, r2_score
from sklearn.model_selection import cross_val_score, KFold

from app import structure
from utils import config

# ----------------------------
# 🔧 Paths
# ----------------------------
DATA_PATH = os.path.join(config.DATA_PATH, "train.csv")

# ----------------------------
# 📜 Feature Definitions
# ----------------------------
def get_variable_definitions():
    return {
        "lead_grf_z_max": "Peak vertical ground reaction force from the lead leg (push-off)",
        "max_shoulder_internal_rotational_velo": "Max angular velocity of shoulder internal rotation during pitch",
        "max_shoulder_external_rotation": "Max shoulder external rotation angle during cocking phase",
        "max_shoulder_horizontal_abduction": "Max horizontal abduction of shoulder (scapular loading)",
        "elbow_transfer_fp_br": "Elbow extension velocity transferred from foot plant to ball release",
        "max_torso_rotational_velo": "Max angular velocity of torso rotation",
        "max_rotation_hip_shoulder_separation": "Max angular separation between hips and shoulders (separation timing)",
        "pelvis_anterior_tilt_fp": "Anterior tilt angle of pelvis at foot plant",
        "max_cog_velo_x": "Max horizontal velocity of center of gravity (CoG)",
        "lead_knee_extension_from_fp_to_br": "Change in lead knee extension angle from foot plant to release",
        "lead_knee_transfer_fp_br": "Velocity of lead knee extension from foot plant to ball release",
        "rear_hip_generation_pkh_fp": "Power from rear hip rotation from peak knee height to foot plant"
    }

# ----------------------------
# 🧐 Cross-Validation Helpers
# ----------------------------
def evaluate_cv_model(model, X, y, variant, technique):
    cv = KFold(n_splits=5, shuffle=True, random_state=42)
    r2_scores = cross_val_score(model, X, y, scoring="r2", cv=cv)
    rmse_scores = np.sqrt(-1 * cross_val_score(model, X, y, scoring="neg_mean_squared_error", cv=cv))

    structure.save_cv_results(
        variant=variant,
        technique=technique,
        r2=np.mean(r2_scores),
        r2_std=np.std(r2_scores),
        rmse=np.mean(rmse_scores),
        rmse_std=np.std(rmse_scores),
    )

def evaluate_gam_cv(X, y, variant, technique, model, features):
    from pygam import LinearGAM

    r2_scores = []
    rmse_scores = []

    kf = KFold(n_splits=5, shuffle=True, random_state=42)
    for train_idx, test_idx in kf.split(X):
        X_train, X_test = X[train_idx], X[test_idx]
        y_train, y_test = y[train_idx], y[test_idx]

        model_cv = LinearGAM(model.terms).fit(X_train, y_train)
        preds = model_cv.predict(X_test)

        r2_scores.append(r2_score(y_test, preds))
        rmse_scores.append(np.sqrt(mean_squared_error(y_test, preds)))

    structure.save_cv_results(
        variant=variant,
        technique=technique,
        r2=np.mean(r2_scores),
        r2_std=np.std(r2_scores),
        rmse=np.mean(rmse_scores),
        rmse_std=np.std(rmse_scores),
    )

    summary_df = pd.DataFrame({
        "Feature": features,
        "EDOF": model.statistics_['edof'],
        "Lambda": model.lam
    })
    info_path = structure.get_model_path(technique, variant, f"{variant}_summary.csv")
    summary_df.to_csv(info_path, index=False)

def train_and_save_model(variant, technique):
    from sklearn.ensemble import RandomForestRegressor
    from sklearn.linear_model import ElasticNetCV
    from sklearn.pipeline import Pipeline
    from sklearn.preprocessing import StandardScaler
    from sklearn.neural_network import MLPRegressor
    from pygam import LinearGAM, s

    df = pd.read_csv(DATA_PATH)
    features = structure.get_model_features(variant)

    # Filter + one-hot encode
    X = df[features].copy()
    X = pd.get_dummies(X, drop_first=True)
    X = X.select_dtypes(include=[np.number]).dropna()
    y = df.loc[X.index, "pitch_speed_mph"]

    start_time = time.time()
    model, r2, rmse = None, None, None

    if technique == "rf":
        model = RandomForestRegressor(n_estimators=1000, random_state=42)
        model.fit(X, y)
        y_pred = model.predict(X)
        evaluate_cv_model(model, X, y, variant, technique)

    elif technique == "elasticnet":
        elasticnet = ElasticNetCV(cv=5, random_state=42)
        model = Pipeline([
            ("scaler", StandardScaler()),
            ("elasticnet", elasticnet)
        ])
        model.fit(X, y)
        y_pred = model.predict(X)
        evaluate_cv_model(model, X, y, variant, technique)

    elif technique == "gam":
        terms = s(0)
        for i in range(1, X.shape[1]):
            terms += s(i)
        model = LinearGAM(terms).fit(X.values, y.values)
        y_pred = model.predict(X)
        evaluate_gam_cv(X.values, y.values, variant, technique, model, features)

    elif technique == "mlp":
        mlp = MLPRegressor(hidden_layer_sizes=(64, 32), max_iter=1000, random_state=42)
        model = Pipeline([
            ("scaler", StandardScaler()),
            ("mlp", mlp)
        ])
        model.fit(X, y)
        y_pred = model.predict(X)
        evaluate_cv_model(model, X, y, variant, technique)

    else:
        st.error("❌ Unsupported technique.")
        return None, None, None, None

    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    duration = time.time() - start_time

    # Save model
    model_path = structure.get_model_path(technique, variant, f"{variant}.joblib")
    os.makedirs(os.path.dirname(model_path), exist_ok=True)
    joblib.dump(model, model_path)

    # 🔐 Save encoded feature column order
    encoded_features_path = structure.get_model_path(technique, variant, f"{variant}_encoded_features.pkl")
    joblib.dump(X.columns.tolist(), encoded_features_path)

    return model, r2, rmse, duration

def train_all_models():
    results = []
    for variant in structure.list_model_variants():
        for technique in structure.list_techniques():
            try:
                model, r2, rmse, duration = train_and_save_model(variant, technique)
                results.append({
                    "Model Variant": variant,
                    "Technique": technique,
                    "R²": round(r2, 3),
                    "RMSE": round(rmse, 2),
                    "Train Time (s)": round(duration, 2)
                })
            except Exception as e:
                results.append({
                    "Model Variant": variant,
                    "Technique": technique,
                    "R²": "ERROR",
                    "RMSE": "ERROR",
                    "Train Time (s)": str(e)
                })
    return pd.DataFrame(results)

# ----------------------------
# 🔷 Streamlit Page
# ----------------------------
def show():
    st.title("⚙️ Model Training")
    st.markdown("Train biomechanically driven models to predict **fastball velocity** using selected variants and techniques.")

    with st.expander("📘 Modeling Summary", expanded=True):
        st.markdown("""
        This module implements machine learning techniques to predict fastball velocity from biomechanical features.

        - **Variants**: Force, Lower Body, Upper Body, Full  
        - **Techniques**:
            - **Random Forest**: Nonlinear ensemble with feature importance  
            - **ElasticNet**: Sparse, interpretable linear model  
            - **GAM (pyGAM)**: Smooth spline-based model with non-linear flexibility  
            - **MLP**: Multi-layer perceptron (neural net)

        All models are trained on preprocessed and scaled data where applicable.  
        Models are saved to `outputs/models/` for downstream use.
        """)

    st.markdown("---")
    st.subheader("🧠 Model Configuration")

    model_variant = st.selectbox("Model Variant", structure.list_model_variants())
    technique = st.selectbox("Technique", structure.list_techniques())

    features = structure.get_model_features(model_variant)
    data = structure.load_cleaned_data()
    df_filtered = data.dropna(subset=features + ["pitch_speed_mph"])
    df_filtered = df_filtered[features + ["pitch_speed_mph"]].select_dtypes(include=[np.number])

    st.markdown(f"- 📌 **Features used**: {len(df_filtered.columns) - 1}")
    st.markdown(f"- 📦 **Training samples**: {df_filtered.shape[0]}")

    with st.expander("🧾 Feature Definitions"):
        st.markdown("Definitions for biomechanical variables used in this model variant:")
        var_defs = get_variable_definitions()
        for var in features:
            desc = var_defs.get(var, "No definition available.")
            st.markdown(f"- **{var}**: {desc}")

    try:
        cv_summary = pd.read_csv(os.path.join(structure.MODEL_PATH, "cv_summary.csv"))
        recent = cv_summary[
            (cv_summary["model_variant"] == model_variant) &
            (cv_summary["technique"] == technique)
        ]
        if not recent.empty:
            st.markdown("### 📊 Last Cross-Validation Summary")
            st.dataframe(recent[["r2_mean", "r2_std", "rmse_mean", "rmse_std"]], use_container_width=True)
    except Exception:
        pass

    st.markdown("---")

    if st.button("🚀 Train Selected Model"):
        with st.spinner("Training in progress..."):
            model, r2, rmse, duration = train_and_save_model(model_variant, technique)

        if model:
            st.success("✅ Model training complete.")
            st.markdown(f"- ⏱️ Training time: `{duration:.2f}` sec")
            st.markdown(f"- 📈 R²: `{r2:.3f}`")
            st.markdown(f"- 📉 RMSE: `{rmse:.2f}`")
            st.toast(f"{technique.upper()} model for {model_variant} saved!", icon="💾")
        else:
            st.error("❌ Training failed.")

    st.markdown("---")
    st.subheader("🚀 Train All Models")

    if st.button("Train All Variants and Techniques"):
        with st.spinner("Training all models... this may take a few minutes."):
            summary_df = train_all_models()

        st.success("✅ All models trained.")

        if not summary_df.empty:
            best_model = summary_df.loc[summary_df['R²'].replace('ERROR', -np.inf).astype(float).idxmax()]
            st.markdown(f"**🏆 Best Model:** `{best_model['Technique']}` on `{best_model['Model Variant']}` → R²: `{best_model['R²']}`")

        st.dataframe(summary_df, use_container_width=True)










