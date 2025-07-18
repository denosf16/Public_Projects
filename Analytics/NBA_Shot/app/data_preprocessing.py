import streamlit as st
import pandas as pd
import matplotlib.pyplot as plt
import os

# --- File paths ---
DATA_PATH = r"C:\Repos\NBA_Shot\data\cleaned_shots.csv"
PLOT_DIR = r"C:\Repos\NBA_Shot\output\plots"
DIST_BUCKET_PATH = r"C:\Repos\NBA_Shot\output\make_pct_by_dist_bucket.csv"

# --- Cache CSV loads ---
@st.cache_data
def load_cleaned_data():
    return pd.read_csv(DATA_PATH)

@st.cache_data
def load_dist_bucket():
    return pd.read_csv(DIST_BUCKET_PATH)

# --- Filtering logic ---
def apply_filters(df):
    return df[
        (df["TOUCH_TIME"] >= 0) &
        (df["DRIBBLES"] <= 24) &
        (df["CLOSE_DEF_DIST"] <= 30)
    ]

def app():
    st.title("📊 Data Exploration: Shot Context & Outcomes")

    # --- Load & Filter Data ---
    original_df = load_cleaned_data()
    df = apply_filters(original_df)
    cleaned_count = df.shape[0]
    removed_rows = original_df.shape[0] - cleaned_count

    # --- Section: Filters Applied ---
    st.subheader("📎 Filters Applied")
    st.markdown(f"""
    The following filters were applied to clean the dataset:
    - 🔻 Removed rows where `TOUCH_TIME < 0` (invalid negative values)
    - 🔻 Removed rows where `DRIBBLES > 24` (more than one dribble per second is unrealistic)
    - 🔻 Removed rows where `CLOSE_DEF_DIST > 30` (likely no defender interaction)

    **Total rows removed:** `{removed_rows:,}`  
    **Remaining rows:** `{cleaned_count:,}`
    """)

    # --- Section: Summary Statistics ---
    st.subheader("📈 Shot Outcome Summary")
    total = len(df)
    made = df["SHOT_MADE"].sum()
    missed = total - made
    made_pct = round(made / total * 100, 1)

    made_2 = df[(df["PTS_TYPE"] == 2) & (df["SHOT_MADE"])].shape[0]
    missed_2 = df[(df["PTS_TYPE"] == 2) & (~df["SHOT_MADE"])].shape[0]
    made_3 = df[(df["PTS_TYPE"] == 3) & (df["SHOT_MADE"])].shape[0]
    missed_3 = df[(df["PTS_TYPE"] == 3) & (~df["SHOT_MADE"])].shape[0]

    pct_2 = round(made_2 / (made_2 + missed_2) * 100, 1)
    pct_3 = round(made_3 / (made_3 + missed_3) * 100, 1)

    col1, col2, col3 = st.columns(3)
    with col1:
        st.metric("✅ Shots Made", f"{made:,}")
        st.metric("❌ Shots Missed", f"{missed:,}")
        st.metric("📌 FG%", f"{made_pct:.1f}%")
    with col2:
        st.metric("2PT Made", made_2)
        st.metric("2PT Missed", missed_2)
        st.metric("2PT FG%", f"{pct_2:.1f}%")
    with col3:
        st.metric("3PT Made", made_3)
        st.metric("3PT Missed", missed_3)
        st.metric("3PT FG%", f"{pct_3:.1f}%")

    # --- Section: Top Player Stats ---
    st.subheader("🎯 Top Player Shot Stats")
    player_stats = df.groupby("PLAYER_NAME").agg(
        total_shots=("SHOT_MADE", "count"),
        made_shots=("SHOT_MADE", "sum"),
        shot_pct=("SHOT_MADE", "mean"),
        avg_shot_dist=("SHOT_DIST", "mean"),
        made_2pt=("PTS_TYPE", lambda x: ((x == 2) & df.loc[x.index, "SHOT_MADE"]).sum()),
        att_2pt=("PTS_TYPE", lambda x: (x == 2).sum()),
        made_3pt=("PTS_TYPE", lambda x: ((x == 3) & df.loc[x.index, "SHOT_MADE"]).sum()),
        att_3pt=("PTS_TYPE", lambda x: (x == 3).sum()),
    ).reset_index()

    player_stats["fg_pct"] = (player_stats["shot_pct"] * 100).round(1)
    player_stats["2pt_pct"] = (player_stats["made_2pt"] / player_stats["att_2pt"] * 100).round(1)
    player_stats["3pt_pct"] = (player_stats["made_3pt"] / player_stats["att_3pt"] * 100).round(1)

    leaderboard = player_stats[[
        "PLAYER_NAME", "total_shots", "made_shots", "fg_pct",
        "avg_shot_dist", "made_2pt", "att_2pt", "2pt_pct",
        "made_3pt", "att_3pt", "3pt_pct"
    ]].sort_values("total_shots", ascending=False)

    st.dataframe(leaderboard.head(15), use_container_width=True)

    if st.checkbox("Show full player leaderboard"):
        st.dataframe(leaderboard, use_container_width=True)

    # --- Section: Shot % by Distance Bucket ---
    st.subheader("🎯 Shot Make% by Distance Bucket")
    dist_bucket = load_dist_bucket()
    st.dataframe(dist_bucket, use_container_width=True)

    # --- Section: Histogram Viewer ---
    st.subheader("📊 Variable Distribution")
    options = ["SHOT_DIST", "CLOSE_DEF_DIST", "TOUCH_TIME", "DRIBBLES",
               "SHOT_CLOCK", "SHOOTER_HEIGHT", "DEFENDER_HEIGHT", "HEIGHT_DIFFERENTIAL"]
    selected = st.selectbox("Choose a variable", options)

    img_path = os.path.join(PLOT_DIR, f"hist_{selected}.png")
    if os.path.exists(img_path):
        st.image(img_path, caption=f"{selected} distribution", use_container_width=True)
        st.caption(f"Mean: {df[selected].mean():.2f} | Std: {df[selected].std():.2f}")
    else:
        st.warning("Histogram not found.")




