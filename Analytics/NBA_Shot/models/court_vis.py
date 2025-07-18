import os
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from matplotlib.patches import Arc

# --- Load Data ---
df = pd.read_csv("output/model_test_predictions.csv")

# --- Simulated Coordinates ---
np.random.seed(42)
df["x"] = np.random.uniform(-15, 15, size=len(df))  # horizontal jitter only
df["y"] = df["SHOT_DIST"]  # use shot distance as vertical placement

# --- Draw Halfcourt ---
def draw_court_with_lines(y_lines=[5, 15, 25], ax=None):
    if ax is None:
        fig, ax = plt.subplots(figsize=(9, 9))

    # Court outline and markings
    ax.plot([-250, 250], [-40, -40], 'k-')   # Baseline
    ax.plot([-250, -250], [-40, 430], 'k-')  # Sideline left
    ax.plot([250, 250], [-40, 430], 'k-')    # Sideline right
    ax.plot([-30, 30], [-10, -10], 'k-')     # Backboard
    ax.plot([-80, -80], [-40, 150], 'k-')
    ax.plot([80, 80], [-40, 150], 'k-')
    ax.plot([-80, 80], [150, 150], 'k-')
    ax.plot([-60, -60], [-40, 150], 'k-')
    ax.plot([60, 60], [-40, 150], 'k-')
    ax.plot([220, 220], [-40, 35], 'k-')
    ax.plot([-220, -220], [-40, 35], 'k-')

    # Arcs
    arcs = [
        Arc((0, 0), 444.34, 444.34, theta1=8, theta2=172),
        Arc((0, 150), 120, 120, theta1=0, theta2=180),
        Arc((0, 150), 120, 120, theta1=180, theta2=360, linestyle="--"),
        Arc((0, 0), 15, 15, theta1=0, theta2=360),
        Arc((0, 7.5), 80, 80, theta1=0, theta2=180),
        Arc((0, 430), 120, 120, theta1=180, theta2=360)
    ]
    for arc in arcs:
        ax.add_patch(arc)

    # Distance lines
    for y in y_lines:
        ax.axhline(y=y, color="gray", linestyle="--", linewidth=0.8)
        ax.text(22, y, f"{y} ft", va="center", fontsize=9, color="gray")

    ax.set_xlim(-25, 25)
    ax.set_ylim(-5, 35)
    ax.set_aspect(1)
    ax.axis("off")
    return ax

# --- Shot Map Plot ---
def plot_shot_map(df, value_col, title, filename):
    fig, ax = plt.subplots(figsize=(9, 9))
    ax = draw_court_with_lines(ax=ax)

    sc = ax.scatter(
        df["x"], df["y"], c=df[value_col],
        cmap="RdBu_r", s=20, edgecolor="none", alpha=0.6
    )
    cbar = plt.colorbar(sc, ax=ax, shrink=0.75)
    cbar.set_label(value_col.replace("_", " ").title())
    plt.title(title)
    plt.tight_layout()
    os.makedirs("output", exist_ok=True)
    plt.savefig(f"output/{filename}", dpi=300)
    plt.close()
    print(f"✅ Saved: output/{filename}")

# --- Run Visuals ---
plot_shot_map(df, "y_true", "Actual Makes", "court_y_true.png")
plot_shot_map(df, "rf_v3_prob", "Predicted FG% (RF v3)", "court_rf_v3_prob.png")
plot_shot_map(df, "xgb_v1_prob", "Predicted FG% (XGB v1)", "court_xgb_v1_prob.png")
plot_shot_map(df, "xgb_v2_prob", "Predicted FG% (XGB v2)", "court_xgb_v2_prob.png")
plot_shot_map(df, value_col="logreg_v2_prob", title="Predicted FG% (LogReg v2)", filename="court_logreg_v2_prob.png")

