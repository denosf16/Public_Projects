import streamlit as st
from graphviz import Digraph
import json
import os

# ---------------------
# Table classification
# ---------------------
FACT_TABLES = ["player_game_logs", "player_shot_logs"]
DIM_TABLES = ["team_info", "dbo_player_info_analysis"]

IMPORTANT_COLUMNS = {
    "dbo_player_info_analysis": ["PLAYER_ID", "PLAYER_NAME", "HEIGHT_INCHES", "POSITION"],
    "player_game_logs": ["PLAYER_ID", "PLAYER_NAME", "GAME_ID", "PTS", "BLK", "STL", "TOV", "AST", "REB"],
    "player_shot_logs": ["SHOT_EVENT_ID", "PLAYER_ID", "PLAYER_NAME", "SHOT_MADE", "CLOSEST_DEFENDER", "SHOT_DIST", "TOUCH_TIME", "DRIBBLES", "SHOT_CLOCK"],
    "team_info": ["TEAM_ID", "TEAM_NAME"]
}

PRIMARY_KEYS = {
    "dbo_player_info_analysis": ["PLAYER_ID"],
    "player_game_logs": ["PLAYER_ID", "GAME_ID"],
    "player_shot_logs": ["SHOT_EVENT_ID"],
    "team_info": ["TEAM_ID"]
}

TABLE_RELATIONSHIPS = {
    "dbo_player_info_analysis": {"TEAM_ID": "team_info.TEAM_ID"},
    "player_game_logs": {
        "PLAYER_ID": "dbo_player_info_analysis.PLAYER_ID",
        "TEAM_ID": "team_info.TEAM_ID"
    },
    "player_shot_logs": {
        "PLAYER_ID": "dbo_player_info_analysis.PLAYER_ID"
    }
}

SCHEMA_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "config", "expected_schema.json"))

# ---------------------
# Schema loading
# ---------------------
def load_schema(json_path=SCHEMA_PATH):
    with open(json_path, "r") as f:
        raw = json.load(f)
    parsed = {}
    for table, cols in raw.items():
        short_table = table.split(".")[-1]
        parsed[short_table] = [
            {
                "name": col,
                "pos": meta["ordinal_position"],
                "is_pk": col in PRIMARY_KEYS.get(short_table, []),
                "is_important": col in IMPORTANT_COLUMNS.get(short_table, [])
            }
            for col, meta in sorted(cols.items(), key=lambda x: x[1]["ordinal_position"])
        ]
    return parsed

# ---------------------
# Graph construction
# ---------------------
def render_schema():
    dot = Digraph("ERD", format="png")
    dot.attr(rankdir="TB", fontsize="10", fontname="Verdana")

    schema = load_schema()

    # --- Center Core Table ---
    dot.node("dbo_player_info_analysis",
             _node_label("dbo_player_info_analysis", schema["dbo_player_info_analysis"]),
             shape="record", style="filled", fillcolor="#ccf2ff")

    # --- Cluster: Reference Tables (blue) ---
    with dot.subgraph(name="cluster_ref") as ref:
        ref.attr(label="📘 Reference Tables", color="blue")
        for table in ["team_info", "player_info"]:
            if table in schema:
                ref.node(table, _node_label(table, schema[table]), shape="record", style="filled", fillcolor="#ccf2ff")

    # --- Cluster: Fact Logs (orange) ---
    with dot.subgraph(name="cluster_facts") as facts:
        facts.attr(label="📦 Fact Logs", color="darkorange")
        for table in ["player_game_logs", "player_shot_logs"]:
            if table in schema:
                facts.node(table, _node_label(table, schema[table]), shape="record", style="filled", fillcolor="#ffeed6")

    # --- Cluster: Metadata/Logs (gray) ---
    with dot.subgraph(name="cluster_meta") as meta:
        meta.attr(label="🧪 Metadata / ETL", color="gray")
        for table in ["etl_log_events"]:
            if table in schema:
                meta.node(table, _node_label(table, schema[table]), shape="record", style="filled", fillcolor="#f0f0f0")

    # --- Edges: FK Relationships ---
    for src_table, fks in TABLE_RELATIONSHIPS.items():
        for fk_col, ref in fks.items():
            ref_table, ref_col = ref.split(".")
            # Add minlen and constraint to space groups apart
            dot.edge(src_table, ref_table,
                     label=f"{fk_col} → {ref_col}",
                     minlen="2", constraint="true")

    return dot

# ---------------------
# Label formatting
# ---------------------
def _node_label(table, columns):
    lines = []
    for col in columns:
        label = col["name"]
        if col["is_pk"]:
            label = f"🗝 {label}"
        elif col["is_important"]:
            label = f"⭐ {label}"
        lines.append(label)
    return "{" + table + "|" + r"\l".join(lines) + r"\l}"

# ---------------------
# Streamlit UI
# ---------------------
def app():
    st.title("🗺️ Schema Visualizer")
    st.markdown(
        """
        This diagram visualizes the relationships across key SQL tables used in the NBA Shot Analytics project.

        - **🗝** Primary Key  
        - **⭐** Important/Monitored Column  
        - **🎯 Orange = Fact Table**, **📘 Blue = Dimension Table**
        """
    )

    dot = render_schema()
    st.graphviz_chart(dot)

    with st.expander("📘 Column Legend by Table"):
        for table, cols in IMPORTANT_COLUMNS.items():
            st.markdown(f"**{table}**: {', '.join(cols)}")

    with st.expander("🎨 Color Legend"):
        st.markdown("""
        - 🟧 **Fact Table** (orange): player-level logs  
        - 🟦 **Dimension Table** (blue): metadata about players or teams  
        - ⬜️ **Neutral Table** (gray): other utility or log tables  
        """)




