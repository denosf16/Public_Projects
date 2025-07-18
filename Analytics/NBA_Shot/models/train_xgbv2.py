import pandas as pd
import numpy as np
import os
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import log_loss, accuracy_score
from sklearn.utils.class_weight import compute_sample_weight
from model_config import load_split_data, save_model
import warnings
warnings.filterwarnings("ignore", category=UserWarning, module="xgboost")


# --- Load data ---
X_train, X_val, X_test, y_train, y_val, y_test, meta_train, meta_val, meta_test = load_split_data()

# --- Feature Engineering ---
bins = [0, 5, 10, 15, 20, 25, 100]
labels = ["0-5", "5-10", "10-15", "15-20", "20-25", "25+"]

for df in [X_train, X_val, X_test]:
    # Add DIST_BIN as categorical
    df["DIST_BIN"] = pd.cut(df["SHOT_DIST"], bins=bins, labels=labels)

    # Add interaction term
    df["DIST_x_DEF"] = df["SHOT_DIST"] * df["CLOSE_DEF_DIST"]

# --- One-hot encode DIST_BIN ---
X_train = pd.get_dummies(X_train, columns=["DIST_BIN"], drop_first=True)
X_val = pd.get_dummies(X_val, columns=["DIST_BIN"], drop_first=True)
X_test = pd.get_dummies(X_test, columns=["DIST_BIN"], drop_first=True)

# --- Ensure column alignment across all sets ---
X_val = X_val.reindex(columns=X_train.columns, fill_value=0)
X_test = X_test.reindex(columns=X_train.columns, fill_value=0)

# --- Sample Weights from DIST_BIN ---
dist_bins_train = pd.cut(X_train["SHOT_DIST"], bins=bins, labels=labels)
sample_weights = compute_sample_weight(class_weight="balanced", y=dist_bins_train.astype(str))

# --- Hyperparameter Grid ---
param_grid = {
    "n_estimators": [100, 200],
    "max_depth": [4, 6],
    "learning_rate": [0.05, 0.1],
    "subsample": [0.8, 1.0],
    "colsample_bytree": [0.8, 1.0],
    "min_child_weight": [1, 10]
}

# --- Initialize and Search ---
xgb = XGBClassifier(
    objective="binary:logistic",
    use_label_encoder=False,
    eval_metric="logloss",
    random_state=42
)

search = GridSearchCV(
    estimator=xgb,
    param_grid=param_grid,
    scoring="neg_log_loss",
    cv=5,
    verbose=1,
    n_jobs=-1
)

search.fit(X_train, y_train, sample_weight=sample_weights)

# --- Evaluate Best Model ---
best_model = search.best_estimator_
best_params = search.best_params_

y_val_probs = best_model.predict_proba(X_val)[:, 1]
y_val_preds = best_model.predict(X_val)

val_loss = log_loss(y_val, y_val_probs)
val_acc = accuracy_score(y_val, y_val_preds)

print("\n✅ XGBoost (v2) Grid Search Complete")
print(f"Best Params: {best_params}")
print(f"Log Loss (val): {val_loss:.4f}")
print(f"Accuracy  (val): {val_acc:.4f}")

# --- Save Model ---
save_model(best_model, "xgb_model_v2.pkl")

# --- Save Feature Importances ---
importances = pd.Series(best_model.feature_importances_, index=X_train.columns)
importances.sort_values(ascending=False).to_csv("output/xgb_v2_feature_importance.csv")
print("📊 Feature importances saved to output/xgb_v2_feature_importance.csv")

