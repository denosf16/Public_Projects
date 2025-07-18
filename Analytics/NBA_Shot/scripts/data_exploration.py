# scripts/data_exploration.py

import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from scipy.stats import skew, kurtosis
import os

# --- File paths ---
INPUT_PATH = r"C:\Repos\NBA_Shot\data\cleaned_shots.csv"
OUTPUT_DIR = r"C:\Repos\NBA_Shot\output"
PLOT_DIR = os.path.join(OUTPUT_DIR, "plots")
os.makedirs(PLOT_DIR, exist_ok=True)

# --- Load Data ---
df = pd.read_csv(INPUT_PATH)
df['SHOT_MADE'] = df['SHOT_MADE'].astype(bool)

# --- Dataset Overview ---
print(f"✅ Dataset shape: {df.shape}")
print(df.info())

# Apply all recommended filters
df = df[df["TOUCH_TIME"] >= 0]
df = df[df["DRIBBLES"] <= 24]
df = df[df["CLOSE_DEF_DIST"] <= 30]

# --- Unique Players ---
player_counts = df['PLAYER_NAME'].value_counts()
print(f"\n✅ Unique players: {len(player_counts)}")
print(player_counts.head(10))

# --- Shot Outcomes ---
print("\n✅ Shot Outcome Breakdown")
print(f"Total Made Shots: {df['SHOT_MADE'].sum()}")
print(f"Total Missed Shots: {(~df['SHOT_MADE']).sum()}")

# --- Breakdown by PTS_TYPE ---
made_2pt = df[(df['PTS_TYPE'] == 2) & (df['SHOT_MADE'])].shape[0]
missed_2pt = df[(df['PTS_TYPE'] == 2) & (~df['SHOT_MADE'])].shape[0]
made_3pt = df[(df['PTS_TYPE'] == 3) & (df['SHOT_MADE'])].shape[0]
missed_3pt = df[(df['PTS_TYPE'] == 3) & (~df['SHOT_MADE'])].shape[0]

print(f"2PT - Made: {made_2pt}, Missed: {missed_2pt}")
print(f"3PT - Made: {made_3pt}, Missed: {missed_3pt}")

# --- Histogram Analysis ---
numeric_cols = [
    "SHOT_DIST", "CLOSE_DEF_DIST", "TOUCH_TIME", "DRIBBLES",
    "SHOT_CLOCK", "SHOOTER_HEIGHT", "DEFENDER_HEIGHT", "HEIGHT_DIFFERENTIAL"
]

for col in numeric_cols:
    plt.figure(figsize=(6, 4))
    df[col].hist(bins=30)
    skew_val = skew(df[col].dropna())
    kurt_val = kurtosis(df[col].dropna())
    plt.title(f"{col} (Skew: {round(skew_val, 2)}, Kurtosis: {round(kurt_val, 2)})")
    plt.xlabel(col)
    plt.ylabel("Frequency")
    plt.grid(True)
    plt.tight_layout()
    plt.savefig(os.path.join(PLOT_DIR, f"hist_{col}.png"))
    plt.close()

# --- Grouped Summary by PLAYER_NAME ---
grouped_summary = df.groupby("PLAYER_NAME").agg(
    total_shots=("SHOT_MADE", "count"),
    made_shots=("SHOT_MADE", "sum"),
    avg_shot_dist=("SHOT_DIST", "mean"),
    avg_close_def_dist=("CLOSE_DEF_DIST", "mean")
).sort_values("total_shots", ascending=False)

grouped_summary.to_csv(os.path.join(OUTPUT_DIR, "grouped_by_player.csv"))
print("✅ Saved grouped summary to grouped_by_player.csv")

# --- Bivariate Plot: SHOT_DIST vs CLOSE_DEF_DIST ---
plt.figure(figsize=(7, 5))
sns.scatterplot(data=df, x="SHOT_DIST", y="CLOSE_DEF_DIST", hue="SHOT_MADE", alpha=0.6)
plt.title("SHOT_DIST vs. CLOSE_DEF_DIST by SHOT_MADE")
plt.tight_layout()
plt.savefig(os.path.join(PLOT_DIR, "scatter_dist_vs_def.png"))
plt.close()

# --- Shot % by Distance Bucket ---
df["DIST_BUCKET"] = pd.cut(df["SHOT_DIST"], bins=[0, 5, 10, 15, 20, 25, 30, 35], right=False)
bucket_summary = df.groupby("DIST_BUCKET")["SHOT_MADE"].agg(["count", "sum"])
bucket_summary["make_pct"] = (bucket_summary["sum"] / bucket_summary["count"]).round(3)
bucket_summary.to_csv(os.path.join(OUTPUT_DIR, "make_pct_by_dist_bucket.csv"))

print("✅ Exported all summaries and plots.")
