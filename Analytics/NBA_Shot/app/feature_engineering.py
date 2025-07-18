import streamlit as st
import pandas as pd
import os
import plotly.express as px
from PIL import Image

# --- File Paths ---
PLOT_DIR = r"C:\Repos\NBA_Shot\output\feature_relationships"
CSV_DIR = PLOT_DIR

# --- Available Features ---
features = [
    "SHOT_DIST", "CLOSE_DEF_DIST", "TOUCH_TIME", "DRIBBLES", "SHOT_CLOCK",
    "SHOOTER_HEIGHT", "DEFENDER_HEIGHT", "HEIGHT_DIFFERENTIAL",
    "HAS_HEIGHT_ADVANTAGE", "LOW_CLOCK", "LONG_TOUCH", "HIGH_DRIBBLE",
    "HEIGHT_DIFFERENTIAL × CLOSE_DEF_DIST"
]

# --- Verdicts Dictionary ---
verdicts = {
    "SHOT_DIST": [
        ("Predictive?", "✅ Yes", "Clear inverse trend from logistic fit"),
        ("Interaction Value?", "⚠️ Moderate", "Stronger with HEIGHT_DIFFERENTIAL"),
        ("Modeling Use?", "✅ Keep", "High MI and RF scores")
    ],
    "CLOSE_DEF_DIST": [
        ("Predictive?", "✅ Slight", "Weak solo predictor, better in interaction"),
        ("Interaction Value?", "✅ Strong", "Improved with HEIGHT_DIFFERENTIAL"),
        ("Modeling Use?", "✅ Keep", "Used in height × distance heatmap")
    ],
    "TOUCH_TIME": [
        ("Predictive?", "✅ Moderate", "Inverse relationship with FG%"),
        ("Interaction Value?", "⚠️ Possible", "Overlaps with DRIBBLES / SHOT_CLOCK"),
        ("Modeling Use?", "✅ Keep", "Choose over DRIBBLES due to interpretability")
    ],
    "DRIBBLES": [
        ("Predictive?", "⚠️ Low", "Similar trend to TOUCH_TIME"),
        ("Interaction Value?", "⚠️ Moderate", "Redundant with TOUCH_TIME"),
        ("Modeling Use?", "❌ Drop", "High collinearity (VIF > 10)")
    ],
    "SHOT_CLOCK": [
        ("Predictive?", "✅ Strong", "Clear positive trend with FG%"),
        ("Interaction Value?", "✅ Strong", "Pairs well with TOUCH_TIME / DRIBBLES"),
        ("Modeling Use?", "✅ Keep", "High RF score, low correlation with others")
    ],
    "SHOOTER_HEIGHT": [
        ("Predictive?", "❌ Weak", "Minimal separation in distributions"),
        ("Interaction Value?", "⚠️ Indirect", "Already captured by HEIGHT_DIFFERENTIAL"),
        ("Modeling Use?", "❌ Drop", "Redundant with HEIGHT_DIFFERENTIAL")
    ],
    "DEFENDER_HEIGHT": [
        ("Predictive?", "❌ Weak", "Flat trends and overlapping distributions"),
        ("Interaction Value?", "⚠️ Maybe", "Only useful in special cases"),
        ("Modeling Use?", "❌ Drop", "Better handled by HEIGHT_DIFFERENTIAL")
    ],
    "HEIGHT_DIFFERENTIAL": [
        ("Predictive?", "✅ Very strong", "Best height-based feature"),
        ("Interaction Value?", "✅ Strong", "Combines well with CLOSE_DEF_DIST"),
        ("Modeling Use?", "✅ Keep", "Drop raw height features in favor of this")
    ],
    "HAS_HEIGHT_ADVANTAGE": [
        ("Predictive?", "✅ Binary signal", "Binned FG% supports predictive value"),
        ("Interaction Value?", "⚠️ Limited", "Captures a simple form of height benefit"),
        ("Modeling Use?", "✅ Keep", "Useful for interpretability or subgroup analysis")
    ],
    "LOW_CLOCK": [
        ("Predictive?", "✅ High", "Late clock shots have poor efficiency"),
        ("Interaction Value?", "✅ Good", "Pairs well with TOUCH_TIME or DRIBBLES"),
        ("Modeling Use?", "✅ Keep", "Easy to interpret, meaningful threshold")
    ],
    "LONG_TOUCH": [
        ("Predictive?", "✅ Moderate", "Flag for iso possessions / over-dribbling"),
        ("Interaction Value?", "⚠️ Possible", "Could be redundant with TOUCH_TIME"),
        ("Modeling Use?", "✅ Optional", "Good for interpretability or interaction splits")
    ],
    "HIGH_DRIBBLE": [
        ("Predictive?", "⚠️ Low", "Similar to LONG_TOUCH"),
        ("Interaction Value?", "⚠️ Limited", "Redundant unless transformed"),
        ("Modeling Use?", "✅ Optional", "Retain if model supports threshold features")
    ],
    "HEIGHT_DIFFERENTIAL × CLOSE_DEF_DIST": [
        ("Predictive?", "✅ Strong", "FG% increases when shooter is taller and defender is distant"),
        ("Interaction Value?", "✅ Very high", "Classic conditional interaction: height helps more with space"),
        ("Modeling Use?", "✅ Include as interaction", "Heatmap shows non-additive synergy, ideal for tree-based models")
    ]
}

# --- Cached CSV Loads ---
@st.cache_data
def load_csv_scores():
    try:
        mi = pd.read_csv(os.path.join(CSV_DIR, "mutual_information_scores.csv"))
        rf = pd.read_csv(os.path.join(CSV_DIR, "rf_feature_importance.csv"))
        vif = pd.read_csv(os.path.join(CSV_DIR, "vif_scores.csv"))
        return mi, rf, vif
    except:
        return None, None, None

# --- Load Plot Helper ---
def load_plot(name):
    path = os.path.join(PLOT_DIR, name)
    if os.path.exists(path):
        return Image.open(path)
    return None

# --- Streamlit App ---
def app():
    st.title("🧠 Feature Engineering Viewer")
    selected = st.sidebar.selectbox("Select Feature", features)

    # --- Verdict Table ---
    st.subheader("📋 Summary Verdict")
    if selected in verdicts:
        df_verdict = pd.DataFrame(verdicts[selected], columns=["Question", "Verdict", "Explanation"])
        st.dataframe(df_verdict, use_container_width=True)
    else:
        st.info("No verdict notes loaded for this feature yet.")

    # --- Insight Box ---
    st.subheader("🧠 Modeling Insight")
    insights = {
        "SHOT_DIST": "Strong negative predictor. Consider binning for non-linearity.",
        "CLOSE_DEF_DIST": "Weak solo effect, better with height interactions.",
        "HEIGHT_DIFFERENTIAL": "Most predictive height-based feature."
    }
    if selected in insights:
        st.success(insights[selected])

    # --- Visual Tabs ---
    st.subheader("📊 Diagnostics")
    tabs = st.tabs(["Logistic Fit", "Binned FG%", "Violin Plot", "Stacked Bar"])

    with tabs[0]:
        if selected not in ["HAS_HEIGHT_ADVANTAGE", "LOW_CLOCK", "LONG_TOUCH", "HIGH_DRIBBLE"]:
            img = load_plot(f"{selected}_logistic.png")
            if img:
                st.image(img, caption="Logistic Fit")
            else:
                st.warning("No logistic fit available.")
        else:
            st.info("Binary features do not use logistic fits.")

    with tabs[1]:
        img = load_plot(f"{selected}_binned.png")
        if img:
            st.image(img, caption="Binned FG%")
        else:
            st.warning("No binned plot available.")

    with tabs[2]:
        img = load_plot(f"{selected}_violin.png")
        if img:
            st.image(img, caption="Violin Plot")
        else:
            st.warning("No violin plot available.")

    with tabs[3]:
        if selected in ["HAS_HEIGHT_ADVANTAGE", "LOW_CLOCK", "LONG_TOUCH", "HIGH_DRIBBLE"]:
            img = load_plot(f"{selected}_stacked_bar.png")
            if img:
                st.image(img, caption="Stacked Bar Chart")
            else:
                st.warning("No stacked bar chart available.")
        else:
            st.info("Stacked bar only available for binary flags.")

    # --- Interaction Heatmap ---
    if selected in ["HEIGHT_DIFFERENTIAL", "CLOSE_DEF_DIST", "HEIGHT_DIFFERENTIAL × CLOSE_DEF_DIST"]:
        st.subheader("🔥 Interaction: HEIGHT_DIFFERENTIAL × CLOSE_DEF_DIST")
        img = load_plot("interaction_heatmap.png")
        if img:
            st.image(img, caption="2D Interaction Heatmap")
            st.caption("This heatmap shows how FG% varies with combined effects of defender distance and height advantage.")
        else:
            st.warning("No interaction heatmap found.")

    # --- Feature Ranking Section ---
    st.subheader("📈 Feature Scores")
    mi, rf, _ = load_csv_scores()

    if mi is not None and rf is not None:
        df_all = mi.merge(rf, on="Feature")
        df_all_long = df_all.melt(id_vars="Feature", var_name="Metric", value_name="Score")
        df_all_long["Metric"] = df_all_long["Metric"].replace({
            "MI_Score": "Mutual Information",
            "RF_Importance": "Random Forest Importance"
        })

        fig = px.bar(
            df_all_long,
            x="Score", y="Feature", color="Metric", barmode="group",
            title="Feature Importance Scores",
            height=500
        )
        st.plotly_chart(fig, use_container_width=True)

        # --- Sortable Verdict Table ---
        st.subheader("📋 Feature Verdict Summary")
        verdict_rows = []
        for _, row in df_all.iterrows():
            f = row["Feature"]
            mi_score = row["MI_Score"]
            rf_score = row["RF_Importance"]

            if rf_score > 0.15 and mi_score > 0.01:
                verdict = "✅ Strong in both"
            elif rf_score > 0.1:
                verdict = "✅ RF-only"
            elif mi_score > 0.01:
                verdict = "✅ MI-only"
            else:
                verdict = "❌ Weak"

            verdict_rows.append({
                "Feature": f,
                "MI Score": round(mi_score, 4),
                "RF Importance": round(rf_score, 4),
                "Verdict": verdict
            })

        df_verdict_summary = pd.DataFrame(verdict_rows).sort_values(by="RF Importance", ascending=False)
        st.dataframe(df_verdict_summary, use_container_width=True)
    else:
        st.info("📁 MI or RF scores not found. Check CSV export path.")

