import os
import pandas as pd
import numpy as np
import joblib
from sklearn.metrics import r2_score
from utils import config

# ------------------------------
# 🔹 Load Test Data
# ------------------------------
data_test = pd.read_csv(os.path.join(config.DATA_PATH, "test.csv"))

# ------------------------------
# 🔹 Define Paths
# ------------------------------
base_path = os.path.join(config.OUTPUT_PATH, "predictions")
global_by_model_path = os.path.join(base_path, "global", "by_model")
metrics_path = os.path.join(base_path, "global", "metrics")
grouped_base_path = os.path.join(base_path, "grouped")

for p in [global_by_model_path, metrics_path, grouped_base_path]:
    os.makedirs(p, exist_ok=True)

# ------------------------------
# 🔹 Model & Grouping Setup
# ------------------------------
techniques = ["rf", "elasticnet", "gam", "mlp"]
model_types = ["force_model", "upper_body_model", "lower_body_model", "full_model"]
group_vars = ["user", "playing_level", "p_throws"]

# ------------------------------
# 🔹 Store Metrics + Predictions
# ------------------------------
metrics = []
pred_df = data_test.copy()

# ------------------------------
# 🔹 Predict + Save Helper
# ------------------------------
def predict_model(model_name, technique, model, features):
    try:
        X = pred_df[features]
        if hasattr(model, "feature_names_in_"):
            X = X[model.feature_names_in_]
        preds = model.predict(X)
        colname = f"{model_name}_{technique}_pred"
        pred_df[colname] = preds
        r2 = r2_score(pred_df["pitch_speed_mph"], preds)
        metrics.append({
            "Model": model_name,
            "Technique": technique,
            "Test_R2": r2
        })
        print(f"✅ {model_name} ({technique}) — Test R²: {r2:.3f}")
    except Exception as e:
        print(f"❌ Error predicting {model_name} ({technique}): {e}")

# ------------------------------
# 🔹 Loop Over Models + Techniques
# ------------------------------
for technique in techniques:
    model_dir = os.path.join(config.OUTPUT_PATH, "models", technique)

    for model_name in model_types:
        model_file = os.path.join(model_dir, f"{model_name}.joblib")

        # Try all known feature file suffixes
        for suffix in ["_importance.csv", "_coefficients.csv", "_summary.csv", "_info.csv"]:
            features_file = os.path.join(model_dir, f"{model_name}{suffix}")
            if os.path.exists(features_file):
                break
        else:
            print(f"⚠️ Skipping {model_name} ({technique}) — no feature file found")
            continue

        if not os.path.exists(model_file):
            print(f"⚠️ Skipping {model_name} ({technique}) — model not found")
            continue

        model = joblib.load(model_file)
        features = pd.read_csv(features_file)["Feature"].tolist()

        # Global predictions
        predict_model(model_name, technique, model, features)

        # Group-wise predictions
        for group_col in group_vars:
            if group_col not in pred_df.columns:
                print(f"⚠️ Skipping group by '{group_col}' — column not found.")
                continue

            for group_val in pred_df[group_col].dropna().unique():
                group_data = pred_df[pred_df[group_col] == group_val].copy()
                if hasattr(model, "feature_names_in_"):
                    try:
                        group_data_X = group_data[model.feature_names_in_]
                    except KeyError:
                        continue
                else:
                    group_data_X = group_data[features]

                try:
                    group_data[f"{model_name}_{technique}_pred"] = model.predict(group_data_X)
                    out_dir = os.path.join(grouped_base_path, group_col, str(group_val), model_name)
                    os.makedirs(out_dir, exist_ok=True)
                    out_file = os.path.join(out_dir, f"{technique}_predictions.csv")
                    group_data.to_csv(out_file, index=False)
                except Exception as e:
                    print(f"❌ Error predicting group {group_val} — {model_name} ({technique}): {e}")

# ------------------------------
# 🔹 Save Combined Output
# ------------------------------
pred_df.to_csv(os.path.join(global_by_model_path, "all_predictions.csv"), index=False)
pd.DataFrame(metrics).to_csv(os.path.join(metrics_path, "model_r2_scores.csv"), index=False)

print("🎯 Subgroup and global predictions complete.")


