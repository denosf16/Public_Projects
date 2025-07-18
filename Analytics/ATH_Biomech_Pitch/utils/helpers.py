import os
import pandas as pd
from sklearn.experimental import enable_iterative_imputer  # noqa
from sklearn.impute import IterativeImputer

# Optional: Load global paths if needed
try:
    from utils import config
except ImportError:
    config = None

# 🔹 Safe CSV Reader
def safe_read_csv(filepath):
    if os.path.exists(filepath):
        print(f"📂 Reading file: {filepath}")
        return pd.read_csv(filepath)
    else:
        print(f"❌ File not found: {filepath}")
        return None

# 🔹 Iterative Imputer (Replacement for MissForest)
def impute_missing_values(df):
    print("🔄 Running Iterative Imputer...")

    df['imputed_flag'] = df.isnull().any(axis=1).astype(int)

    numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
    df_numeric = df[numeric_cols]

    imputer = IterativeImputer(random_state=123, max_iter=10)
    df_imputed_array = imputer.fit_transform(df_numeric)

    df[numeric_cols] = df_imputed_array

    if df.isnull().sum().sum() > 0:
        print("❌ Imputation failed — missing values remain:")
        print(df.isnull().sum()[df.isnull().sum() > 0])
    else:
        print("✅ Imputation complete. No missing values remain.")

    return df

# 🔹 Test Block
if __name__ == "__main__":
    if config is not None:
        df = safe_read_csv(os.path.join(config.DATA_PATH, "pitch_poi.csv"))
        if df is not None:
            df = impute_missing_values(df)
            print(df.head())

