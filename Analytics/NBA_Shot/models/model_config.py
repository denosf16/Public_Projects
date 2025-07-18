import os
import pandas as pd
from sklearn.model_selection import train_test_split

# --- Paths ---
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__)))
DATA_PATH = os.path.join(BASE_DIR, "..", "data", "cleaned_shots.csv")
SPLIT_DIR = os.path.join(BASE_DIR, "data")
MODEL_DIR = os.path.join(BASE_DIR, "trained")

os.makedirs(SPLIT_DIR, exist_ok=True)
os.makedirs(MODEL_DIR, exist_ok=True)

# --- Column Config ---
FEATURES = [
    "SHOT_DIST", "CLOSE_DEF_DIST", "TOUCH_TIME", "SHOT_CLOCK", "HEIGHT_DIFFERENTIAL",
    "HAS_HEIGHT_ADVANTAGE", "LOW_CLOCK", "LONG_TOUCH", "HIGH_DRIBBLE"
]

# For diagnostics and eval_visual grouping
META_COLS = [
    "SHOT_EVENT_ID", "SHOT_DIST", "CLOSE_DEF_DIST", "TOUCH_TIME", "SHOT_CLOCK",
    "HEIGHT_DIFFERENTIAL", "HAS_HEIGHT_ADVANTAGE", "LOW_CLOCK"
]

TARGET = "SHOT_MADE"

# --- Hyperparameters ---
RF_PARAMS = {
    "n_estimators": 200,
    "min_samples_leaf": 100,
    "max_depth": 3,
    "max_features": "sqrt",
    "random_state": 42
}

LOGREG_PARAMS = {
    "penalty": "l2",
    "solver": "liblinear",
    "max_iter": 1000,
    "random_state": 42
}

# --- Split & Save ---
def prepare_data(test_size=0.2, val_size=0.15, stratify=True, seed=42):
    df = pd.read_csv(DATA_PATH)

    # --- Derived Binary Flags ---
    df["HAS_HEIGHT_ADVANTAGE"] = (df["HEIGHT_DIFFERENTIAL"] >= 5).astype(int)
    df["LOW_CLOCK"] = (df["SHOT_CLOCK"] <= 5).astype(int)
    df["LONG_TOUCH"] = (df["TOUCH_TIME"] >= 10).astype(int)
    df["HIGH_DRIBBLE"] = (df["DRIBBLES"] >= 5).astype(int)

    # --- Ensure target is numeric ---
    df["SHOT_MADE"] = df["SHOT_MADE"].astype(int)

    # --- Define input + metadata ---
    X_full = df[FEATURES + ["SHOT_EVENT_ID"]]
    y_full = df[[TARGET] + META_COLS]  # This becomes the "meta" payload in model_eval

    # Step 1: Train+Val vs Test
    strat = y_full[TARGET] if stratify else None
    X_temp, X_test, y_temp, y_test = train_test_split(
        X_full, y_full, test_size=test_size, stratify=strat, random_state=seed
    )

    # Step 2: Train vs Val
    val_ratio = val_size / (1 - test_size)
    strat_temp = y_temp[TARGET] if stratify else None
    X_train, X_val, y_train, y_val = train_test_split(
        X_temp, y_temp, test_size=val_ratio, stratify=strat_temp, random_state=seed
    )

    # Save features and enriched y (with meta)
    for name, X, y in [
        ("train", X_train, y_train),
        ("val", X_val, y_val),
        ("test", X_test, y_test)
    ]:
        X.to_csv(os.path.join(SPLIT_DIR, f"X_{name}.csv"), index=False)
        y.to_csv(os.path.join(SPLIT_DIR, f"y_{name}.csv"), index=False)

    print("✅ Splits saved with SHOT_EVENT_ID + all diagnostics in y_*.csv")

# --- Load Split Data ---
def load_split_data():
    def load_set(name):
        X = pd.read_csv(os.path.join(SPLIT_DIR, f"X_{name}.csv"))
        y_df = pd.read_csv(os.path.join(SPLIT_DIR, f"y_{name}.csv"))
        y = y_df[TARGET].values.ravel()
        meta = y_df[META_COLS]
        return X.drop(columns=["SHOT_EVENT_ID"]), y, meta

    X_train, y_train, meta_train = load_set("train")
    X_val, y_val, meta_val = load_set("val")
    X_test, y_test, meta_test = load_set("test")

    return X_train, X_val, X_test, y_train, y_val, y_test, meta_train, meta_val, meta_test

# --- Save/Load Model ---
def save_model(model, filename):
    import joblib
    path = os.path.join(MODEL_DIR, filename)
    joblib.dump(model, path)
    print(f"✅ Model saved to {path}")

def load_model(filename):
    import joblib
    return joblib.load(os.path.join(MODEL_DIR, filename))

# --- Run standalone ---
if __name__ == "__main__":
    prepare_data()




