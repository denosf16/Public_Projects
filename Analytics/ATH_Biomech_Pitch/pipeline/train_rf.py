import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestRegressor
from sklearn.metrics import mean_squared_error, r2_score
import joblib

from utils import config

# ------------------------------
# 🔹 Paths
# ------------------------------
data_path = os.path.join(config.DATA_PATH, "train.csv")
model_path = os.path.join(config.OUTPUT_PATH, "models", "rf")
os.makedirs(model_path, exist_ok=True)

# ------------------------------
# 🔹 Load Train Data
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
# 🔹 Train + Save RF Models
# ------------------------------
for model_name, features in model_inputs.items():
    missing = [f for f in features if f not in df.columns]
    if missing:
        print(f"⚠️ Skipping {model_name} — missing: {missing}")
        continue

    X = df[features]

    model = RandomForestRegressor(n_estimators=1000, random_state=42)
    model.fit(X, y)
    y_pred = model.predict(X)

    r2 = r2_score(y, y_pred)
    mse = mean_squared_error(y, y_pred)
    rmse = np.sqrt(mse)

    print(f"✅ {model_name} — R²: {r2:.3f} | RMSE: {rmse:.2f}")


    # Save model
    joblib.dump(model, os.path.join(model_path, f"{model_name}.joblib"))

    # Save feature importances
    importances = pd.DataFrame({
        "Feature": features,
        "Importance": model.feature_importances_
    }).sort_values(by="Importance", ascending=False)

    importances.to_csv(os.path.join(model_path, f"{model_name}_importance.csv"), index=False)

print("🎯 RF training complete.")



