import pandas as pd
from sklearn.linear_model import LogisticRegression
from sklearn.preprocessing import StandardScaler
from sklearn.pipeline import Pipeline
from sklearn.model_selection import GridSearchCV
from sklearn.metrics import log_loss, accuracy_score
from model_config import load_split_data, save_model

# --- Load Data ---
X_train, X_val, X_test, y_train, y_val, y_test, meta_train, meta_val, meta_test = load_split_data()

# --- Selected Features + Manual Interactions ---
def engineer_features(df):
    df = df.copy()
    df["SCxTT"] = df["SHOT_CLOCK"] * df["TOUCH_TIME"]
    df["CDxHD"] = df["CLOSE_DEF_DIST"] * df["HEIGHT_DIFFERENTIAL"]
    return df[["SHOT_DIST", "SHOT_CLOCK", "HEIGHT_DIFFERENTIAL", "SCxTT", "CDxHD"]]

X_train_fe = engineer_features(X_train)
X_val_fe   = engineer_features(X_val)

# --- Define Pipeline ---
pipeline = Pipeline([
    ("scaler", StandardScaler()),
    ("logreg", LogisticRegression(max_iter=1000))  # max_iter helps convergence
])

# --- Grid Search Parameters ---
param_grid = {
    "logreg__C": [0.01, 0.1, 1, 10],
    "logreg__penalty": ["l1", "l2"],
    "logreg__solver": ["liblinear", "saga"]
}

# --- Grid Search ---
grid = GridSearchCV(pipeline, param_grid, cv=5, scoring="neg_log_loss", n_jobs=-1, verbose=1)
grid.fit(X_train_fe, y_train)

# --- Best Model ---
best_model = grid.best_estimator_
best_params = grid.best_params_

# --- Evaluate on Validation ---
y_val_probs = best_model.predict_proba(X_val_fe)[:, 1]
y_val_preds = best_model.predict(X_val_fe)

val_loss = log_loss(y_val, y_val_probs)
val_acc = accuracy_score(y_val, y_val_preds)

# --- Output Results ---
print("\n✅ Logistic Regression Grid Search Complete")
print(f"Best Params: {best_params}")
print(f"Log Loss (val): {val_loss:.4f}")
print(f"Accuracy  (val): {val_acc:.4f}")

# --- Save Best Model ---
save_model(best_model, "logreg_model_v2.pkl")



