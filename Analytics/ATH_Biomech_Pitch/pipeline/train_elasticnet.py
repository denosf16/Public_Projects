import os
import pandas as pd
import numpy as np
from sklearn.linear_model import ElasticNetCV
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.metrics import mean_squared_error, r2_score
import joblib

from utils import config

# ------------------------------
# 🔹 Paths
# ------------------------------
data_path = os.path.join(config.DATA_PATH, "train.csv")
model_path = os.path.join(config.OUTPUT_PATH, "models", "elasticnet")
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
# 🔹 Train + Save Models
# ------------------------------
for model_name, features in model_inputs.items():
    missing = [f for f in features if f not in df.columns]
    if missing:
        print(f"⚠️ Skipping {model_name} — missing: {missing}")
        continue

    X = df[features]

    # Scale + Fit
    scaler = StandardScaler()
    X_scaled = scaler.fit_transform(X)

    model = ElasticNetCV(cv=5, random_state=42)
    model.fit(X_scaled, y)
    y_pred = model.predict(X_scaled)

    r2 = r2_score(y, y_pred)
    rmse = np.sqrt(mean_squared_error(y, y_pred))

    print(f"✅ {model_name} — R²: {r2:.3f} | RMSE: {rmse:.2f}")

    # Save model + scaler pipeline
    pipeline = Pipeline([
        ("scaler", scaler),
        ("elasticnet", model)
    ])
    joblib.dump(pipeline, os.path.join(model_path, f"{model_name}.joblib"))

    # Save coefficients
    coef_df = pd.DataFrame({
        "Feature": features,
        "Coefficient": model.coef_
    }).sort_values(by="Coefficient", key=abs, ascending=False)
    coef_df.to_csv(os.path.join(model_path, f"{model_name}_coefficients.csv"), index=False)

    # ✅ Save features used for later evaluation
    pd.DataFrame({"Feature": features}).to_csv(
        os.path.join(model_path, f"{model_name}_importance.csv"), index=False
    )

print("🎯 ElasticNet training complete.")




