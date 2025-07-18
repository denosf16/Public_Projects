# models/train_xgb.py

import os
import pandas as pd
from xgboost import XGBClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import log_loss, accuracy_score
from model_config import load_split_data, save_model

# --- Load Data ---
X_train, X_val, X_test, y_train, y_val, y_test, meta_train, meta_val, meta_test = load_split_data()

# --- Feature Engineering ---
for df in [X_train, X_val, X_test]:
    df["DIST_x_CLOSE_DEF"] = df["SHOT_DIST"] * df["CLOSE_DEF_DIST"]

selected_features = [
    "SHOT_DIST", "CLOSE_DEF_DIST", "TOUCH_TIME", "SHOT_CLOCK", "HEIGHT_DIFFERENTIAL",
    "DIST_x_CLOSE_DEF"
]

# --- Define Param Grid ---
param_grid = {
    "n_estimators": [100, 200, 300],
    "max_depth": [3, 5, 7],
    "learning_rate": [0.01, 0.05, 0.1],
    "subsample": [0.8, 1.0],
    "colsample_bytree": [0.8, 1.0],
    "min_child_weight": [1, 5, 10]
}

# --- Grid Search ---
xgb = XGBClassifier(
    objective="binary:logistic",
    use_label_encoder=False,
    eval_metric="logloss",
    random_state=42,
    verbosity=0
)

search = GridSearchCV(
    estimator=xgb,
    param_grid=param_grid,
    scoring="neg_log_loss",
    cv=5,
    n_jobs=-1,
    verbose=1
)

search.fit(X_train[selected_features], y_train)

# --- Best Model ---
best_xgb = search.best_estimator_
best_params = search.best_params_

# --- Evaluate on Validation Set ---
y_val_probs = best_xgb.predict_proba(X_val[selected_features])[:, 1]
y_val_preds = best_xgb.predict(X_val[selected_features])

val_loss = log_loss(y_val, y_val_probs)
val_acc = accuracy_score(y_val, y_val_preds)

print("\n✅ XGBoost Grid Search Complete")
print(f"Best Params: {best_params}")
print(f"Log Loss (val): {val_loss:.4f}")
print(f"Accuracy  (val): {val_acc:.4f}")

# --- Save Model ---
save_model(best_xgb, "xgb_model.pkl")

# --- Feature Importances ---
importance_df = pd.DataFrame({
    "feature": selected_features,
    "importance": best_xgb.feature_importances_
}).sort_values(by="importance", ascending=False)

os.makedirs("output", exist_ok=True)
importance_df.to_csv("output/xgb_feature_importance.csv", index=False)
print("📊 Feature importances saved to output/xgb_feature_importance.csv")
