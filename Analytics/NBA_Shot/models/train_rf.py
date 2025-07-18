import os
import pandas as pd
import numpy as np
from sklearn.ensemble import RandomForestClassifier
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import log_loss, accuracy_score
from model_config import load_split_data, save_model

# --- Load Data ---
X_train, X_val, X_test, y_train, y_val, y_test, meta_train, meta_val, meta_test = load_split_data()

# --- Feature Engineering ---
for df in [X_train, X_val, X_test]:
    df["CLOCK_TOUCH"] = df["SHOT_CLOCK"] * df["TOUCH_TIME"]
    df["HEIGHT_CLOSE"] = df["HEIGHT_DIFFERENTIAL"] * df["CLOSE_DEF_DIST"]

# --- Selected Features (refined from VIF + MI + RF importance) ---
selected_features = [
    "SHOT_DIST",
    "SHOT_CLOCK",
    "CLOSE_DEF_DIST",
    "TOUCH_TIME",               # Using TOUCH_TIME over DRIBBLES
    "HEIGHT_DIFFERENTIAL",
    "CLOCK_TOUCH",              # Interaction
    "HEIGHT_CLOSE"              # Interaction
]

# --- Define Full Grid ---
param_grid = {
    "n_estimators": [100, 200, 300, 500],
    "max_depth": [5, 10, 15, None],
    "min_samples_leaf": [1, 5, 10, 25, 50],
    "max_features": ["sqrt", "log2"]
}

# --- Grid Search ---
rf = RandomForestClassifier(random_state=42)
search = GridSearchCV(
    estimator=rf,
    param_grid=param_grid,
    scoring="neg_log_loss",
    cv=5,
    verbose=1,
    n_jobs=-1
)

search.fit(X_train[selected_features], y_train)

# --- Best Estimator & Params ---
best_rf = search.best_estimator_
best_params = search.best_params_

# --- Evaluate on Validation Set ---
y_val_probs = best_rf.predict_proba(X_val[selected_features])[:, 1]
y_val_preds = best_rf.predict(X_val[selected_features])

val_loss = log_loss(y_val, y_val_probs)
val_acc = accuracy_score(y_val, y_val_preds)

print("\n✅ Random Forest (v3, Grid Search) Complete")
print(f"Best Params: {best_params}")
print(f"Log Loss (val): {val_loss:.4f}")
print(f"Accuracy  (val): {val_acc:.4f}")

# --- Save Model ---
save_model(best_rf, "rf_model_v3.pkl")

# --- Save Feature Importances ---
importances = pd.Series(best_rf.feature_importances_, index=selected_features).sort_values(ascending=False)
os.makedirs("output", exist_ok=True)
importances.to_csv("output/rf_v3_feature_importance.csv")
print("\n📊 Top Features:\n", importances.head(10))


