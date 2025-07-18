# models/eval_diagnostics.py

import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import scipy.stats as stats

# --- Config ---
DATA_PATH = "output/model_test_predictions.csv"
OUTPUT_DIR = "output"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Load Data ---
df = pd.read_csv(DATA_PATH)

# --- Infer available models ---
model_prefixes = sorted([col.replace("_prob", "") for col in df.columns if col.endswith("_prob")])
print(f"✅ Found models for diagnostics: {model_prefixes}")

# --- Run diagnostics per model ---
for model in model_prefixes:
    prob_col = f"{model}_prob"
    pred_col = f"{model}_pred"

    if prob_col not in df.columns or "y_true" not in df.columns:
        print(f"⚠️ Skipping {model} — required columns missing")
        continue

    # Compute residuals
    df[f"{model}_residual"] = df["y_true"] - df[prob_col]
    residuals = df[f"{model}_residual"]

    # --- 1. Histogram of Residuals ---
    plt.figure(figsize=(8, 5))
    sns.histplot(residuals, bins=40, kde=True, color="skyblue")
    plt.title(f"Residual Histogram — {model.upper()}")
    plt.xlabel("Residual (y_true - predicted prob)")
    plt.ylabel("Count")
    plt.axvline(0, color="red", linestyle="--")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/residual_hist_{model}.png")
    plt.close()

    # --- 2. QQ Plot ---
    plt.figure(figsize=(6, 6))
    stats.probplot(residuals, dist="norm", plot=plt)
    plt.title(f"QQ Plot of Residuals — {model.upper()}")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/qq_{model}.png")
    plt.close()

    # --- 3. Actual vs Predicted ---
    plt.figure(figsize=(8, 6))
    sns.scatterplot(x=prob_col, y="y_true", data=df, alpha=0.2)
    sns.regplot(x=prob_col, y="y_true", data=df, scatter=False, color="red")
    plt.xlabel("Predicted Probability")
    plt.ylabel("Actual Outcome")
    plt.title(f"Actual vs Predicted — {model.upper()}")
    plt.tight_layout()
    plt.savefig(f"{OUTPUT_DIR}/actual_vs_pred_{model}.png")
    plt.close()

    # --- 4. Residuals vs SHOT_DIST ---
    if "SHOT_DIST" in df.columns:
        plt.figure(figsize=(8, 6))
        sns.scatterplot(x="SHOT_DIST", y=residuals, data=df, alpha=0.2)
        sns.regplot(x="SHOT_DIST", y=residuals, data=df, scatter=False, color="red")
        plt.axhline(0, color="black", linestyle="--")
        plt.title(f"Residuals vs Shot Distance — {model.upper()}")
        plt.xlabel("SHOT_DIST (ft)")
        plt.ylabel("Residual")
        plt.tight_layout()
        plt.savefig(f"{OUTPUT_DIR}/residual_vs_distance_{model}.png")
        plt.close()

    print(f"✅ Diagnostics completed for {model}")

print("\n🎯 All diagnostic plots saved to /output")

