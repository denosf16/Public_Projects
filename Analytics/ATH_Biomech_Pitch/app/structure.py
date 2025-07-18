# structure.py

import os
import pandas as pd

# ----------------------------
# 🔹 Project Paths
# ----------------------------
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA_DIR = os.path.join(BASE_DIR, "data")
OUTPUT_PATH = os.path.join(BASE_DIR, "outputs")
EDA_PATH = os.path.join(OUTPUT_PATH, "eda_data")
MODEL_PATH = os.path.join(OUTPUT_PATH, "models")
PLOT_PATH = os.path.join(EDA_PATH, "plots")

# ----------------------------
# 🔹 Load Core Datasets
# ----------------------------
def load_cleaned_data():
    return pd.read_csv(os.path.join(DATA_DIR, "pitch_data_cleaned.csv"))

def load_model_metrics():
    path = os.path.join(MODEL_PATH, "model_metrics.csv")
    df = pd.read_csv(path)
    if "Val_R2" in df.columns and "model_variant" not in df.columns:
        df = df.rename(columns={
            "Model": "model_variant",
            "Technique": "technique",
            "Test_R2": "r2",
            "Test_RMSE": "rmse",
            "Test_MAE": "mae"
        })
        df["split"] = "test"
    return df

# ----------------------------
# 🔹 Feature Selection Files
# ----------------------------
def load_feature_scores():
    df = pd.read_csv(os.path.join(EDA_PATH, "feature_scores.csv"))
    df.columns = [col.lower().strip() for col in df.columns]
    return df

def load_selected_features():
    return pd.read_csv(os.path.join(EDA_PATH, "selected_features.csv"))

def load_vif():
    return pd.read_csv(os.path.join(EDA_PATH, "vif_results.csv"))

# ----------------------------
# 🔹 Diagnostics
# ----------------------------
def load_normality_summary():
    df = pd.read_csv(os.path.join(EDA_PATH, "normality_summary.csv"))
    df.columns = [col.lower().strip() for col in df.columns]
    return df

def load_outlier_counts():
    df = pd.read_csv(os.path.join(EDA_PATH, "outlier_counts.csv"))
    if list(df.columns) == ["index", 0]:
        df.columns = ["variable", "outlier_count"]
    if "variable" not in df.columns:
        df = df.rename(columns={df.columns[0]: "variable", df.columns[1]: "outlier_count"})
    if "%_outliers" not in df.columns:
        try:
            total_rows = len(load_cleaned_data())
            df["%_outliers"] = (df["outlier_count"] / total_rows) * 100
        except:
            df["%_outliers"] = None
    return df

# ----------------------------
# 🔹 Plot Utilities
# ----------------------------
def get_eda_plot(var_name, kind="histogram"):
    if kind == "histogram":
        return os.path.join(PLOT_PATH, "histograms", f"{var_name}.png")
    elif kind == "scatterplot":
        return os.path.join(PLOT_PATH, "scatterplots", f"{var_name}.png")
    elif kind == "image":
        return os.path.join(PLOT_PATH, f"{var_name}.png")

# ----------------------------
# 🔹 Model Variant & Feature Mapping (Whitelist)
# ----------------------------
def list_model_variants():
    return ["force_model", "upper_body_model", "lower_body_model", "full_model"]

def get_model_features(model_variant):
    model_inputs = {
        "force_model": ["lead_grf_z_max"],
        "upper_body_model": [
            "max_shoulder_internal_rotational_velo",
            "max_shoulder_external_rotation",
            "max_shoulder_horizontal_abduction",
            "elbow_transfer_fp_br"
        ],
        "lower_body_model": [
            "max_torso_rotational_velo",
            "max_rotation_hip_shoulder_separation",
            "pelvis_anterior_tilt_fp",
            "max_cog_velo_x",
            "lead_knee_extension_from_fp_to_br",
            "lead_knee_transfer_fp_br",
            "rear_hip_generation_pkh_fp"
        ],
        "full_model": [
            "lead_grf_z_max",
            "max_shoulder_internal_rotational_velo", "max_shoulder_external_rotation",
            "max_shoulder_horizontal_abduction", "elbow_transfer_fp_br",
            "max_torso_rotational_velo", "max_rotation_hip_shoulder_separation",
            "pelvis_anterior_tilt_fp", "max_cog_velo_x",
            "lead_knee_extension_from_fp_to_br", "lead_knee_transfer_fp_br",
            "rear_hip_generation_pkh_fp"
        ]
    }
    return model_inputs[model_variant]

# ----------------------------
# 🔹 Available Techniques
# ----------------------------
def list_techniques():
    return ["rf", "elasticnet", "gam", "mlp"]

# ----------------------------
# ✅ Model Path Helper
# ----------------------------
def get_model_path(technique, variant, filename=None):
    path = os.path.join(MODEL_PATH, technique)
    return os.path.join(path, filename) if filename else path

# ----------------------------
# ✅ Save Cross-Validation Results
# ----------------------------
def save_cv_results(variant, technique, r2, r2_std, rmse, rmse_std):
    path = os.path.join(MODEL_PATH, "cv_summary.csv")
    new_row = pd.DataFrame([{
        "model_variant": variant,
        "technique": technique,
        "r2_mean": r2,
        "r2_std": r2_std,
        "rmse_mean": rmse,
        "rmse_std": rmse_std
    }])
    if os.path.exists(path):
        existing = pd.read_csv(path)
        existing = existing[~((existing["model_variant"] == variant) & (existing["technique"] == technique))]
        df = pd.concat([existing, new_row], ignore_index=True)
    else:
        df = new_row
    df.to_csv(path, index=False)

# ----------------------------
# ✅ Load Model Metadata/Importance
# ----------------------------
def load_model_info(technique, variant, info_type="importance"):
    path = os.path.join(MODEL_PATH, technique, f"{variant}_{info_type}.csv")
    if os.path.exists(path):
        return pd.read_csv(path)
    else:
        return pd.DataFrame()






