import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from sklearn.metrics import confusion_matrix, ConfusionMatrixDisplay, roc_curve, auc
from sklearn.calibration import calibration_curve

# --- Load Predictions ---
data_path = r"C:\Repos\NBA_Shot\output"
preds_df = pd.read_csv(os.path.join(data_path, "model_test_predictions.csv"))
model_results = pd.read_csv(os.path.join(data_path, "model_results.csv"))

# --- Identify Models Automatically ---
models = sorted([col.replace("_prob", "") for col in preds_df.columns if col.endswith("_prob")])

# --- 1. Confusion Matrices ---
for model in models:
    cm = confusion_matrix(preds_df["y_true"], preds_df[f"{model}_pred"])
    disp = ConfusionMatrixDisplay(confusion_matrix=cm)
    disp.plot(cmap="Blues")
    plt.title(f"Confusion Matrix - {model}")
    plt.savefig(os.path.join(data_path, f"confusion_matrix_{model}.png"))
    plt.close()

# --- 2. ROC Curve Overlay ---
plt.figure(figsize=(8, 6))
for model in models:
    fpr, tpr, _ = roc_curve(preds_df["y_true"], preds_df[f"{model}_prob"])
    plt.plot(fpr, tpr, label=f"{model} (AUC = {auc(fpr, tpr):.3f})")
plt.plot([0, 1], [0, 1], "k--", label="Chance")
plt.title("ROC Curves - All Models")
plt.xlabel("False Positive Rate")
plt.ylabel("True Positive Rate")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(data_path, "roc_curves.png"))
plt.close()

# --- 3. Calibration Curve (RF v3 + XGB v2 only) ---
plt.figure(figsize=(6, 6))
for model in ["rf_v3", "xgb_v2"]:
    prob_true, prob_pred = calibration_curve(preds_df["y_true"], preds_df[f"{model}_prob"], n_bins=10)
    plt.plot(prob_pred, prob_true, marker="o", label=model)
plt.plot([0, 1], [0, 1], linestyle="--", color="gray", label="Perfect")
plt.xlabel("Predicted Probability")
plt.ylabel("Observed Frequency")
plt.title("Calibration Curve")
plt.legend()
plt.tight_layout()
plt.savefig(os.path.join(data_path, "calibration_curves.png"))
plt.close()

# --- 4. Grouped Evaluation ---
def group_eval(df, group_name, condition):
    subset = df[condition]
    metrics = {}
    for model in models:
        acc = np.mean(subset[f"{model}_pred"] == subset["y_true"])
        fpr, tpr, _ = roc_curve(subset["y_true"], subset[f"{model}_prob"])
        metrics[model] = {"Accuracy": acc, "AUC": auc(fpr, tpr)}
    return pd.DataFrame(metrics).T.reset_index().rename(columns={"index": "Model"}).assign(Group=group_name)

# Shot distance bins
bins = [0, 5, 10, 15, 20, 25, 30, 100]
labels = ["0-5", "5-10", "10-15", "15-20", "20-25", "25-30", "30+"]
preds_df["SHOT_DIST_BIN"] = pd.cut(preds_df["SHOT_DIST"], bins=bins, labels=labels)

grouped_dfs = []

# By distance bins
for label in labels:
    grouped_dfs.append(group_eval(preds_df, f"DIST_{label}", preds_df["SHOT_DIST_BIN"] == label))

# Shot context groups
grouped_dfs.append(group_eval(preds_df, "Wide Open", preds_df["CLOSE_DEF_DIST"] > 8))
grouped_dfs.append(group_eval(preds_df, "Contested", preds_df["CLOSE_DEF_DIST"] < 3))
grouped_dfs.append(group_eval(preds_df, "Clutch", preds_df["LOW_CLOCK"] == 1))
grouped_dfs.append(group_eval(preds_df, "Mismatch", preds_df["HAS_HEIGHT_ADVANTAGE"] == 1))

grouped_df = pd.concat(grouped_dfs, ignore_index=True)
grouped_df.to_csv(os.path.join(data_path, "grouped_eval.csv"), index=False)

# --- Grouped Accuracy Plot ---
plt.figure(figsize=(12, 6))
sns.barplot(data=grouped_df, x="Group", y="Accuracy", hue="Model")
plt.xticks(rotation=45)
plt.title("Model Accuracy by Shot Context")
plt.tight_layout()
plt.savefig(os.path.join(data_path, "grouped_eval.png"))
plt.close()

# --- 5. 1D Shot Map by Distance (RF v3 Pred vs Actual) ---
distance_bins = np.linspace(0, 30, 61)
preds_df["DIST_BIN"] = pd.cut(preds_df["SHOT_DIST"], bins=distance_bins, labels=False)
dist_group = preds_df.groupby("DIST_BIN").agg(
    actual_mean=("y_true", "mean"),
    predicted_mean=("rf_v3_prob", "mean")
).reset_index()
dist_group["DIST_FEET"] = distance_bins[:-1] + 0.25

for col, label in zip(["actual_mean", "predicted_mean"], ["actual", "predicted"]):
    plt.figure(figsize=(10, 4))
    sns.heatmap([dist_group[col].values], cmap="RdBu_r", cbar=True, xticklabels=5, yticklabels=False)
    plt.title(f"Expected Shot Probability by Distance ({label.title()})")
    plt.xlabel("Distance (ft)")
    plt.tight_layout()
    plt.savefig(os.path.join(data_path, f"shot_map_{label}.png"))
    plt.close()

print("✅ eval_visual.py complete. All visualizations saved to /output")


