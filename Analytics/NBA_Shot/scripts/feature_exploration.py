# scripts/feature_exploration.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
import os
from sklearn.ensemble import RandomForestClassifier
from sklearn.feature_selection import mutual_info_classif
from statsmodels.stats.outliers_influence import variance_inflation_factor

# --- File Paths ---
DATA_PATH = r"C:\Repos\NBA_Shot\data\cleaned_shots.csv"
OUTPUT_DIR = r"C:\Repos\NBA_Shot\output\feature_relationships"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# --- Load & Clean ---
df = pd.read_csv(DATA_PATH)
df = df[df["TOUCH_TIME"] >= 0]
df = df[df["DRIBBLES"] <= 24]
df = df[df["CLOSE_DEF_DIST"] <= 30]
df["SHOT_MADE"] = df["SHOT_MADE"].astype(bool)

# --- Feature List ---
features = [
    "SHOT_DIST", "CLOSE_DEF_DIST", "TOUCH_TIME", "DRIBBLES",
    "SHOT_CLOCK", "SHOOTER_HEIGHT", "DEFENDER_HEIGHT", "HEIGHT_DIFFERENTIAL"
]

# --- Derived Flags ---
df["HAS_HEIGHT_ADVANTAGE"] = df["HEIGHT_DIFFERENTIAL"] >= 5
df["LOW_CLOCK"] = df["SHOT_CLOCK"] <= 5
df["LONG_TOUCH"] = df["TOUCH_TIME"] >= 10
df["HIGH_DRIBBLE"] = df["DRIBBLES"] >= 5
binary_flags = ["HAS_HEIGHT_ADVANTAGE", "LOW_CLOCK", "LONG_TOUCH", "HIGH_DRIBBLE"]

# --- Plotting: Logistic, Binned, Violin for Continuous Features ---
for feature in features:
    print(f"🔍 {feature}")

    logistic_path = os.path.join(OUTPUT_DIR, f"{feature}_logistic.png")
    binned_path = os.path.join(OUTPUT_DIR, f"{feature}_binned.png")
    violin_path = os.path.join(OUTPUT_DIR, f"{feature}_violin.png")

    if not os.path.exists(logistic_path):
        plt.figure(figsize=(6, 4))
        sns.regplot(x=feature, y="SHOT_MADE", data=df, logistic=True, lowess=False, scatter_kws={"alpha": 0.2, "s": 10})
        plt.title(f"P(SHOT_MADE) vs {feature} (Logistic Fit)")
        plt.tight_layout()
        plt.savefig(logistic_path)
        plt.close()

    if not os.path.exists(binned_path):
        try:
            df["BIN"] = pd.cut(df[feature], bins=20)
            bin_means = df.groupby("BIN")["SHOT_MADE"].mean().reset_index()
            bin_centers = [interval.mid for interval in bin_means["BIN"]]

            plt.figure(figsize=(6, 4))
            plt.plot(bin_centers, bin_means["SHOT_MADE"], marker="o")
            plt.title(f"Binned FG% vs {feature}")
            plt.tight_layout()
            plt.savefig(binned_path)
            plt.close()
        except Exception as e:
            print(f"❌ Binning failed for {feature}: {e}")

    if not os.path.exists(violin_path):
        plt.figure(figsize=(6, 4))
        sns.violinplot(x="SHOT_MADE", y=feature, data=df)
        plt.title(f"{feature} Distribution by SHOT_MADE")
        plt.tight_layout()
        plt.savefig(violin_path)
        plt.close()

# --- Binary Feature Plots (Grouped Bar + Violin) ---
for flag in binary_flags:
    binned_path = os.path.join(OUTPUT_DIR, f"{flag}_binned.png")
    violin_path = os.path.join(OUTPUT_DIR, f"{flag}_violin.png")

    if not os.path.exists(binned_path):
        fg_mean = df.groupby(flag)["SHOT_MADE"].mean().reset_index()
        plt.figure(figsize=(5, 4))
        sns.barplot(x=flag, y="SHOT_MADE", data=fg_mean)
        plt.title(f"FG% by {flag}")
        plt.tight_layout()
        plt.savefig(binned_path)
        plt.close()

    if not os.path.exists(violin_path):
        plt.figure(figsize=(6, 4))
        sns.violinplot(x="SHOT_MADE", y=flag, data=df)
        plt.title(f"{flag} Distribution by SHOT_MADE")
        plt.tight_layout()
        plt.savefig(violin_path)
        plt.close()

# --- Stacked Bar Charts for Binary Flags ---
for flag in binary_flags:
    stacked_path = os.path.join(OUTPUT_DIR, f"{flag}_stacked_bar.png")
    if not os.path.exists(stacked_path):
        ctab = pd.crosstab(df[flag], df["SHOT_MADE"], normalize='index')
        ctab.plot(kind='bar', stacked=True, colormap='coolwarm', figsize=(6, 4))
        plt.title(f"Stacked Shot Outcome by {flag}")
        plt.ylabel("Proportion")
        plt.xlabel(flag)
        plt.legend(title="SHOT_MADE", labels=["Missed", "Made"])
        plt.tight_layout()
        plt.savefig(stacked_path)
        plt.close()

# --- Interaction Plot: HEIGHT_DIFFERENTIAL × CLOSE_DEF_DIST ---
interaction_path = os.path.join(OUTPUT_DIR, "interaction_heatmap.png")
if not os.path.exists(interaction_path):
    df["HEIGHT_BIN"] = pd.cut(df["HEIGHT_DIFFERENTIAL"], bins=6)
    df["DEF_DIST_BIN"] = pd.cut(df["CLOSE_DEF_DIST"], bins=6)
    heatmap_df = df.groupby(["HEIGHT_BIN", "DEF_DIST_BIN"])["SHOT_MADE"].mean().unstack()
    plt.figure(figsize=(8, 6))
    sns.heatmap(heatmap_df, annot=True, fmt=".2f", cmap="YlGnBu")
    plt.title("P(SHOT_MADE) by HEIGHT_DIFFERENTIAL × CLOSE_DEF_DIST")
    plt.tight_layout()
    plt.savefig(interaction_path)
    plt.close()

# --- Correlation Matrix ---
corr_path = os.path.join(OUTPUT_DIR, "correlation_matrix.png")
if not os.path.exists(corr_path):
    corr_df = df[features].corr()
    plt.figure(figsize=(10, 8))
    sns.heatmap(corr_df, annot=True, fmt=".2f", cmap="coolwarm", square=True)
    plt.title("Correlation Matrix")
    plt.tight_layout()
    plt.savefig(corr_path)
    plt.close()

# --- Mutual Information ---
mi_scores = mutual_info_classif(df[features], df["SHOT_MADE"])
mi_df = pd.DataFrame({"Feature": features, "MI_Score": mi_scores})
mi_df.to_csv(os.path.join(OUTPUT_DIR, "mutual_information_scores.csv"), index=False)

# --- Random Forest Feature Importance ---
rf = RandomForestClassifier(n_estimators=100, random_state=42)
rf.fit(df[features], df["SHOT_MADE"])
rf_df = pd.DataFrame({"Feature": features, "RF_Importance": rf.feature_importances_})
rf_df.to_csv(os.path.join(OUTPUT_DIR, "rf_feature_importance.csv"), index=False)

# --- VIF Diagnostics ---
X_vif = df[features].dropna()
vif_df = pd.DataFrame()
vif_df["Feature"] = X_vif.columns
vif_df["VIF"] = [variance_inflation_factor(X_vif.values, i) for i in range(X_vif.shape[1])]
vif_df.to_csv(os.path.join(OUTPUT_DIR, "vif_scores.csv"), index=False)

print("✅ All visualizations, statistics, and interaction plots saved to:", OUTPUT_DIR)

