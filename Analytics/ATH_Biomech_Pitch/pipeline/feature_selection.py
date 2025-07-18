import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns

from sklearn.ensemble import RandomForestRegressor
from sklearn.feature_selection import mutual_info_regression
from sklearn.linear_model import LassoCV, LinearRegression
from sklearn.preprocessing import StandardScaler
from sklearn.metrics import r2_score

from utils import config

# ------------------------------
# 🔹 Paths & Setup
# ------------------------------
eda_dir = os.path.join(config.OUTPUT_PATH, "eda_data")
plot_dir = os.path.join(eda_dir, "plots")
hist_path = os.path.join(plot_dir, "histograms")
scatter_path = os.path.join(plot_dir, "scatterplots")

for path in [eda_dir, plot_dir, hist_path, scatter_path]:
    os.makedirs(path, exist_ok=True)

df = pd.read_csv(os.path.join(config.DATA_PATH, "pitch_data_cleaned.csv"))

# Preserve metadata for later
metadata_cols = ["session_pitch", "user", "session_mass_kg", "session_height_m", "age_yrs", "playing_level", "p_throws"]
metadata_df = df[metadata_cols] if all(col in df.columns for col in metadata_cols) else pd.DataFrame()

# Drop them for feature selection
df = df.drop(columns=metadata_cols, errors="ignore")

# ------------------------------
# 🔹 Correlation Filter
# ------------------------------
numeric_cols = df.select_dtypes(include=["number"]).columns.tolist()
corr_matrix = df[numeric_cols].corr()
target_corr = corr_matrix["pitch_speed_mph"].drop("pitch_speed_mph")
high_corr_vars = target_corr[abs(target_corr) >= 0.1].index.tolist()

# Heatmap
heatmap_vars = high_corr_vars + ["pitch_speed_mph"]
plt.figure(figsize=(12, 10))
sns.heatmap(corr_matrix.loc[heatmap_vars, heatmap_vars], cmap="coolwarm", square=True, linewidths=0.5,
            cbar_kws={"shrink": 0.8}, xticklabels=True, yticklabels=True)
plt.xticks(rotation=90)
plt.yticks(rotation=0)
plt.title("Correlation Heatmap (|corr| ≥ 0.1)", fontsize=14, pad=10)
plt.tight_layout()
plt.savefig(os.path.join(plot_dir, "correlation_heatmap.png"))
plt.close()

# ------------------------------
# 🔹 Score Variables (RF, MI, LASSO)
# ------------------------------
X = df[high_corr_vars].dropna()
y = df.loc[X.index, "pitch_speed_mph"]

rf = RandomForestRegressor(n_estimators=2500, random_state=42).fit(X, y)
rf_scores = pd.Series(rf.feature_importances_, index=X.columns)

mi_scores = pd.Series(mutual_info_regression(X, y, random_state=42), index=X.columns)

scaler = StandardScaler()
X_scaled = scaler.fit_transform(X)
lasso = LassoCV(cv=5, random_state=42).fit(X_scaled, y)
lasso_coefs = pd.Series(np.abs(lasso.coef_), index=X.columns)

rf_norm = rf_scores / rf_scores.max()
mi_norm = mi_scores / mi_scores.max()
lasso_norm = lasso_coefs / lasso_coefs.max() if lasso_coefs.max() > 0 else lasso_coefs

ensemble_score = 0.4 * rf_norm + 0.4 * mi_norm + 0.2 * lasso_norm

score_df = pd.DataFrame({
    "RF": rf_norm,
    "MI": mi_norm,
    "LASSO": lasso_norm,
    "Ensemble_Score": ensemble_score
}).sort_values(by="Ensemble_Score", ascending=False)

# ------------------------------
# 🔹 Correlation Clustering
# ------------------------------
corr_subset = df[score_df.index].corr().abs()
correlated_groups, used = [], set()
threshold = 0.85

for col in corr_subset.columns:
    if col in used:
        continue
    group = corr_subset.index[(corr_subset[col] > threshold) & (corr_subset.index != col)].tolist()
    if group:
        group.append(col)
        correlated_groups.append(list(set(group)))
        used.update(group)

selected_vars = [
    score_df.loc[group].sort_values("Ensemble_Score", ascending=False).index[0]
    for group in correlated_groups
]

grouped_vars = set(v for g in correlated_groups for v in g)
ungrouped = [v for v in score_df.index if v not in grouped_vars and score_df.loc[v, "Ensemble_Score"] >= 0.1]
selected_vars.extend(ungrouped)
selected_vars = sorted(set(selected_vars))

# ------------------------------
# 🔹 Save Final Feature Set (+ Metadata)
# ------------------------------
final_df = df[["pitch_speed_mph"] + selected_vars]
if not metadata_df.empty:
    final_df = final_df.join(metadata_df.loc[final_df.index])

final_df.to_csv(os.path.join(eda_dir, "selected_features.csv"), index=False)

# ------------------------------
# 🔹 EDA Plots
# ------------------------------
for var in selected_vars:
    # Scatter
    plt.figure()
    sns.regplot(data=final_df, x=var, y="pitch_speed_mph", scatter_kws={'alpha': 0.5}, line_kws={'color': 'red'})
    plt.title(f"{var} vs. Pitch Speed")
    plt.tight_layout()
    plt.savefig(os.path.join(scatter_path, f"scatter_{var}.png"))
    plt.close()

    # Histogram
    plt.figure()
    sns.histplot(final_df[var], kde=True, bins=30)
    plt.title(f"Distribution of {var}")
    plt.tight_layout()
    plt.savefig(os.path.join(hist_path, f"hist_{var}.png"))
    plt.close()

# ------------------------------
# 🔹 Corr + R² Enhancement
# ------------------------------
corrs, r2_vals = [], []
for var in score_df.index:
    if var in final_df.columns:
        x = final_df[var].values.reshape(-1, 1)
        y = final_df["pitch_speed_mph"].values
        lin_model = LinearRegression().fit(x, y)
        y_pred = lin_model.predict(x)
        r2_vals.append(r2_score(y, y_pred))
        corrs.append(np.corrcoef(final_df[var], y)[0, 1])
    else:
        r2_vals.append(np.nan)
        corrs.append(np.nan)

score_df["Correlation"] = corrs
score_df["R2"] = r2_vals
score_df.to_csv(os.path.join(eda_dir, "feature_scores.csv"))

print("✅ Feature selection and EDA export complete.")




