import os
import pandas as pd
import numpy as np
from pygam import LinearGAM, s
from sklearn.metrics import mean_squared_error, r2_score
import joblib

from utils import config

# ------------------------------
# 🔹 Paths
# ------------------------------
data_path = os.path.join(config.DATA_PATH, "train.csv")
model_path = os.path.join(config.OUTPUT_PATH, "models", "gam")
os.makedirs(model_path, exist_ok=True)

# ------------------------------
# 🔹 Load Data
# ------------------------------
df = pd.read_csv(data_path)
y = df["pitch_speed_mph"]

# ------------------------------
# 🔹 Define Feature Sets
# ------------------------------
model_inputs = {
    "force_model": [
        "lead_grf_z_max"
    ],
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

# ------------------------------
# 🔹 Train + Save GAM Models
# ------------------------------
for model_name, features in model_inputs.items():
    missing = [f for f in features if f not in df.columns]
    if missing:
        print(f"⚠️ Skipping {model_name} — missing: {missing}")
        continue

    X = df[features].values

    # Define spline terms
    terms = s(0)
    for i in range(1, X.shape[1]):
        terms += s(i)

    # Fit model
    gam = LinearGAM(terms).fit(X, y)
    y_pred = gam.predict(X)

    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))
    print(f"✅ {model_name} — R²: {r2:.3f} | RMSE: {rmse:.2f}")

    # Save model
    joblib.dump(gam, os.path.join(model_path, f"{model_name}.joblib"))

    # Save EDOF + Lambda summary
    summary_df = pd.DataFrame({
        "Feature": features,
        "Lambda": gam.lam,
        "EDOF": gam.statistics_["edof"]
    })
    summary_df.to_csv(os.path.join(model_path, f"{model_name}_summary.csv"), index=False)

    # ✅ Save features used for evaluation
    pd.DataFrame({"Feature": features}).to_csv(
        os.path.join(model_path, f"{model_name}_importance.csv"), index=False
    )

print("🎯 GAM training complete.")




