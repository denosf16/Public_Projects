import os
import pandas as pd
import numpy as np
import joblib
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats
from sklearn.metrics import (
    mean_squared_error,
    mean_absolute_error,
    median_absolute_error,
    r2_score
)
from utils import config

# ------------------------------
# 🔹 Load Validation and Test Data
# ------------------------------
data_val = pd.read_csv(os.path.join(config.DATA_PATH, "val.csv"))
data_test = pd.read_csv(os.path.join(config.DATA_PATH, "test.csv"))

# ------------------------------
# 🔹 Define Paths and Setup
# ------------------------------
plot_base = os.path.join(config.OUTPUT_PATH, "plots", "diagnostics")
metrics_path = os.path.join(config.OUTPUT_PATH, "models", "model_metrics.csv")
os.makedirs(plot_base, exist_ok=True)
os.makedirs(os.path.dirname(metrics_path), exist_ok=True)

metrics = []
techniques = ["rf", "elasticnet", "gam", "mlp"]
model_types = ["force_model", "upper_body_model", "lower_body_model", "full_model"]

# ------------------------------
# 🔹 Evaluation Function
# ------------------------------
def evaluate_model(model_name, technique, model, X_val, y_val, X_test, y_test):
    val_pred = model.predict(X_val)
    test_pred = model.predict(X_test)

    # 🔸 Compute metrics
    val_r2 = r2_score(y_val, val_pred)
    val_rmse = np.sqrt(mean_squared_error(y_val, val_pred))
    val_mae = mean_absolute_error(y_val, val_pred)
    val_medae = median_absolute_error(y_val, val_pred)

    test_r2 = r2_score(y_test, test_pred)
    test_rmse = np.sqrt(mean_squared_error(y_test, test_pred))
    test_mae = mean_absolute_error(y_test, test_pred)
    test_medae = median_absolute_error(y_test, test_pred)

    print(f"✅ {model_name} ({technique}) | Val R²: {val_r2:.3f} | Test R²: {test_r2:.3f}")

    metrics.append({
        "Model": model_name,
        "Technique": technique,
        "Technique_Model": f"{technique}_{model_name}",
        "Val_R2": val_r2,
        "Val_RMSE": val_rmse,
        "Val_MAE": val_mae,
        "Val_MedianAE": val_medae,
        "Test_R2": test_r2,
        "Test_RMSE": test_rmse,
        "Test_MAE": test_mae,
        "Test_MedianAE": test_medae
    })

    # 🔹 Save predictions
    pred_df = pd.DataFrame({
        "val_actual": y_val,
        "val_pred": val_pred,
        "test_actual": y_test,
        "test_pred": test_pred
    })

    # 🔹 Create diagnostic plot + output folder
    plot_path = os.path.join(plot_base, model_name, technique)
    os.makedirs(plot_path, exist_ok=True)
    pred_df.to_csv(os.path.join(plot_path, "predictions.csv"), index=False)

    # 🔸 Residual Histogram
    residuals = y_test - test_pred
    plt.figure()
    sns.histplot(residuals, kde=True)
    plt.title(f"{model_name} ({technique}) — Test Residuals")
    plt.xlabel("Residuals")
    plt.tight_layout()
    plt.savefig(os.path.join(plot_path, "residuals.png"))
    plt.close()

    # 🔸 Predicted vs Actual
    plt.figure()
    sns.scatterplot(x=y_test, y=test_pred, alpha=0.7)
    plt.plot([y_test.min(), y_test.max()], [y_test.min(), y_test.max()], 'r--')
    plt.title(f"{model_name} ({technique}) — Predicted vs Actual")
    plt.xlabel("Actual Pitch Speed")
    plt.ylabel("Predicted Pitch Speed")
    plt.tight_layout()
    plt.savefig(os.path.join(plot_path, "pred_vs_actual.png"))
    plt.close()

    # 🔸 Q-Q Plot
    plt.figure()
    stats.probplot(residuals, dist="norm", plot=plt)
    plt.title(f"{model_name} ({technique}) — Q-Q Plot")
    plt.tight_layout()
    plt.savefig(os.path.join(plot_path, "qq_plot.png"))
    plt.close()

    # 🔸 Residuals vs Fitted
    plt.figure()
    sns.scatterplot(x=test_pred, y=residuals)
    plt.axhline(0, linestyle="--", color="red")
    plt.xlabel("Fitted Values")
    plt.ylabel("Residuals")
    plt.title(f"{model_name} ({technique}) — Residuals vs Fitted")
    plt.tight_layout()
    plt.savefig(os.path.join(plot_path, "residuals_vs_fitted.png"))
    plt.close()

# ------------------------------
# 🔹 Loop Through All Models
# ------------------------------
for technique in techniques:
    model_dir = os.path.join(config.OUTPUT_PATH, "models", technique)

    for model_name in model_types:
        model_file = os.path.join(model_dir, f"{model_name}.joblib")
        feature_file = os.path.join(model_dir, f"{model_name}_importance.csv")

        if not os.path.exists(model_file):
            print(f"⚠️ Skipping {model_name} ({technique}) — model not found")
            continue
        if not os.path.exists(feature_file):
            print(f"⚠️ Skipping {model_name} ({technique}) — features not found")
            continue

        model = joblib.load(model_file)
        features = pd.read_csv(feature_file)["Feature"].tolist()

        try:
            X_val = data_val[features]
            X_test = data_test[features]

            # Align feature order if applicable
            if hasattr(model, "feature_names_in_"):
                X_val = X_val[model.feature_names_in_]
                X_test = X_test[model.feature_names_in_]

            y_val = data_val["pitch_speed_mph"]
            y_test = data_test["pitch_speed_mph"]

            evaluate_model(model_name, technique, model, X_val, y_val, X_test, y_test)

        except KeyError as e:
            print(f"❌ Feature mismatch in val/test for {model_name} ({technique}): {e}")

# ------------------------------
# 🔹 Save Final Metrics
# ------------------------------
pd.DataFrame(metrics).to_csv(metrics_path, index=False)
print("📊 Evaluation metrics saved to models/model_metrics.csv")




