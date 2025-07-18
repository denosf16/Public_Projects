import os
import pandas as pd
from sklearn.metrics import log_loss, accuracy_score, roc_auc_score
from model_config import load_split_data, load_model

# --- Load All 7 Models ---
logreg_model_v1 = load_model("logreg_model.pkl")
logreg_model_v2 = load_model("logreg_model_v2.pkl")
rf_model_v1     = load_model("rf_model.pkl")
rf_model_v2     = load_model("rf_model_v2.pkl")
rf_model_v3     = load_model("rf_model_v3.pkl")
xgb_model_v1    = load_model("xgb_model.pkl")
xgb_model_v2    = load_model("xgb_model_v2.pkl")

# --- Load Data ---
X_train, X_val, X_test, y_train, y_val, y_test, meta_train, meta_val, meta_test = load_split_data()
X_test_orig = X_test.copy()  # keep original for logreg and early RF

# --- Feature Engineering for Logistic and RF Models ---
X_test_orig["SCxTT"] = X_test_orig["SHOT_CLOCK"] * X_test_orig["TOUCH_TIME"]
X_test_orig["CDxHD"] = X_test_orig["CLOSE_DEF_DIST"] * X_test_orig["HEIGHT_DIFFERENTIAL"]
X_test_orig["CLOCK_TOUCH"] = X_test_orig["SHOT_CLOCK"] * X_test_orig["TOUCH_TIME"]
X_test_orig["HEIGHT_CLOSE"] = X_test_orig["HEIGHT_DIFFERENTIAL"] * X_test_orig["CLOSE_DEF_DIST"]
X_test_orig["DIST_x_CLOSE_DEF"] = X_test_orig["SHOT_DIST"] * X_test_orig["CLOSE_DEF_DIST"]

logreg_features = ["SHOT_DIST", "SHOT_CLOCK", "HEIGHT_DIFFERENTIAL", "SCxTT", "CDxHD"]
rf_features_v1_v2 = ["SHOT_DIST", "SHOT_CLOCK", "HEIGHT_DIFFERENTIAL", "CLOCK_TOUCH", "HEIGHT_CLOSE"]
rf_features_v3 = [
    "SHOT_DIST", "SHOT_CLOCK", "CLOSE_DEF_DIST", "TOUCH_TIME",
    "HEIGHT_DIFFERENTIAL", "CLOCK_TOUCH", "HEIGHT_CLOSE"
]
xgb_features_v1 = [
    "SHOT_DIST", "CLOSE_DEF_DIST", "TOUCH_TIME", "SHOT_CLOCK",
    "HEIGHT_DIFFERENTIAL", "DIST_x_CLOSE_DEF"
]

# --- Preprocess for XGBoost v2 ---
X_test = X_test.copy()
X_test["DIST_x_DEF"] = X_test["SHOT_DIST"] * X_test["CLOSE_DEF_DIST"]

bins = [0, 5, 10, 15, 20, 25, 100]
labels = ["0-5", "5-10", "10-15", "15-20", "20-25", "25+"]
X_test["DIST_BIN"] = pd.cut(X_test["SHOT_DIST"], bins=bins, labels=labels)
X_test["HAS_HEIGHT_ADVANTAGE"] = (X_test["HEIGHT_DIFFERENTIAL"] >= 5).astype(int)
X_test["LOW_CLOCK"] = (X_test["SHOT_CLOCK"] <= 5).astype(int)
X_test["LONG_TOUCH"] = (X_test["TOUCH_TIME"] >= 10).astype(int)
X_test["HIGH_DRIBBLE"] = 0

X_test = pd.get_dummies(X_test, columns=["DIST_BIN"], drop_first=True)

# Align to trained features
xgb_features_v2 = xgb_model_v2.get_booster().feature_names
X_test = X_test.reindex(columns=xgb_features_v2, fill_value=0)

# --- Evaluation Helper ---
def evaluate(model, X, y_true):
    y_probs = model.predict_proba(X)[:, 1]
    y_preds = model.predict(X)
    return {
        "Log Loss": log_loss(y_true, y_probs),
        "Accuracy": accuracy_score(y_true, y_preds),
        "AUC": roc_auc_score(y_true, y_probs)
    }, y_preds, y_probs

# --- Evaluate All Models ---
results = []

# Include metadata for downstream evaluation
cols_to_keep = [
    "SHOT_EVENT_ID", "SHOT_DIST", "CLOSE_DEF_DIST", "TOUCH_TIME", "SHOT_CLOCK",
    "HEIGHT_DIFFERENTIAL", "HAS_HEIGHT_ADVANTAGE", "LOW_CLOCK"
]
preds_df = meta_test[cols_to_keep].copy()
preds_df["y_true"] = y_test

models = [
    ("Logistic Regression (v1)", logreg_model_v1, logreg_features, "logreg_v1"),
    ("Logistic Regression (v2)", logreg_model_v2, logreg_features, "logreg_v2"),
    ("Random Forest (v1)", rf_model_v1, rf_features_v1_v2, "rf_v1"),
    ("Random Forest (v2)", rf_model_v2, rf_features_v1_v2, "rf_v2"),
    ("Random Forest (v3)", rf_model_v3, rf_features_v3, "rf_v3"),
    ("XGBoost (v1)", xgb_model_v1, xgb_features_v1, "xgb_v1"),
    ("XGBoost (v2)", xgb_model_v2, xgb_features_v2, "xgb_v2"),
]

for label, model, features, prefix in models:
    X_input = X_test[features] if prefix == "xgb_v2" else X_test_orig[features]
    metrics, preds, probs = evaluate(model, X_input, y_test)
    results.append({"Model": label, **metrics})
    preds_df[f"{prefix}_prob"] = probs
    preds_df[f"{prefix}_pred"] = preds

# --- Save Outputs ---
os.makedirs("output", exist_ok=True)
pd.DataFrame(results).to_csv("output/model_results.csv", index=False)
preds_df.to_csv("output/model_test_predictions.csv", index=False)

# --- Print Summary ---
print("\n✅ Model Evaluation Complete")
print(pd.DataFrame(results).to_string(index=False))
print("\nPredictions saved to output/model_test_predictions.csv")






