import os
import pandas as pd
import numpy as np
from scipy.stats import shapiro
from utils import config, helpers

# ------------------------------
# 🔹 File Paths
# ------------------------------
meta_file = os.path.join(config.DATA_PATH, "pitch_meta.csv")
poi_file = os.path.join(config.DATA_PATH, "pitch_poi.csv")
output_file = os.path.join(config.DATA_PATH, "pitch_data_cleaned.csv")

eda_data_path = os.path.join(config.OUTPUT_PATH, "eda_data")
os.makedirs(eda_data_path, exist_ok=True)

# ------------------------------
# 🔹 Read and Merge Data
# ------------------------------
pitch_meta = pd.read_csv(meta_file)
pitch_poi = pd.read_csv(poi_file)

meta_cols = ["session_pitch", "user", "session_mass_kg", "session_height_m", "age_yrs", "playing_level"]
pitch_meta_selected = pitch_meta[meta_cols]

pitch_data = pd.merge(pitch_poi, pitch_meta_selected, on="session_pitch", how="left")

# ------------------------------
# 🔹 Impute Missing Values
# ------------------------------
pitch_data_imputed = helpers.impute_missing_values(pitch_data)

# ------------------------------
# 🔹 Normality Testing
# ------------------------------
numeric_cols = pitch_data_imputed.select_dtypes(include=["number"]).columns.tolist()
normality_results = {
    col: shapiro(pitch_data_imputed[col].dropna())[1] if pitch_data_imputed[col].notna().sum() > 3 else np.nan
    for col in numeric_cols
}
normality_df = pd.DataFrame({
    "Variable": list(normality_results.keys()),
    "P_Value": list(normality_results.values())
})
normality_df["Normal_Distribution"] = normality_df["P_Value"] > 0.05

# ------------------------------
# 🔹 Outlier Detection
# ------------------------------
def detect_z_outliers(x):
    z_scores = (x - np.nanmean(x)) / np.nanstd(x)
    return np.abs(z_scores) > 3

def detect_iqr_outliers(x):
    q1 = np.nanquantile(x, 0.25)
    q3 = np.nanquantile(x, 0.75)
    iqr = q3 - q1
    return (x < (q1 - 1.5 * iqr)) | (x > (q3 + 1.5 * iqr))

outlier_flags = {}
for col in numeric_cols:
    is_normal = normality_df.loc[normality_df["Variable"] == col, "Normal_Distribution"].values[0]
    method = detect_z_outliers if is_normal else detect_iqr_outliers
    outlier_flags[f"{col}_outlier"] = method(pitch_data_imputed[col])

outliers_df = pd.DataFrame(outlier_flags)
pitch_data_imputed = pd.concat([pitch_data_imputed, outliers_df], axis=1)

# ------------------------------
# 🔹 Save Outputs
# ------------------------------
pitch_data_imputed.to_csv(output_file, index=False)

# Save diagnostics to eda_data/
normality_df.to_csv(os.path.join(eda_data_path, "normality_summary.csv"), index=False)
outliers_df.sum().reset_index(name="Outlier_Count").to_csv(os.path.join(eda_data_path, "outlier_counts.csv"), index=False)

print("✅ Cleaned data and EDA diagnostics saved.")



