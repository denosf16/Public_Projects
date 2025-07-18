import os
import sys
import pandas as pd
import hashlib
from datetime import datetime

# Add project root to sys.path for absolute imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.db_connect import get_connection
from scripts.etl_logger import log_message, log_to_db

# --- Config
INPUT_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "shot_logs.csv"))
BATCH_SIZE = 10000

def generate_id(row):
    # Includes row index to guarantee uniqueness
    base_str = f"{row.name}_{row['PLAYER_ID']}_{row['GAME_ID']}"
    return hashlib.sha1(base_str.encode()).hexdigest()[:12]

def compute_time_remaining(clock, period, is_ot):
    if is_ot:
        return 0
    try:
        minutes, seconds = map(int, str(clock).split(":"))
        seconds_left_q = minutes * 60 + seconds
        elapsed = (period - 1) * 720 + (720 - seconds_left_q)
        return 2880 - elapsed
    except:
        return 0

def transform_data():
    log_message("🛠️ Transforming shot logs...")
    log_to_db("player_shot_logs", "transform", "success", error_level="info", source_script="transform_and_load_shots.py")

    df = pd.read_csv(INPUT_PATH)

    # --- Parse GAME_DATE and split MATCHUP
    df[["GAME_DATE", "MATCHUP"]] = df["MATCHUP"].str.split(" - ", expand=True)
    df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], format="%b %d, %Y", errors="coerce")

    # --- SHOT_CLOCK: fill blanks with 0.0
    df["SHOT_CLOCK"] = pd.to_numeric(df["SHOT_CLOCK"], errors="coerce").fillna(0.0)

    # --- OT and TIME_REMAINING
    df["OT"] = df["PERIOD"].apply(lambda x: 1 if x >= 5 else 0)
    df["TIME_REMAINING"] = df.apply(lambda row: compute_time_remaining(row["GAME_CLOCK"], row["PERIOD"], row["OT"]), axis=1)

    # --- SHOT_MADE
    df["SHOT_MADE"] = df["SHOT_RESULT"].str.lower().map({"made": 1, "missed": 0}).fillna(0).astype(bool)

    # --- Drop unnecessary columns
    cols_to_drop = ["MATCHUP_CLEAN", "PERIOD", "GAME_CLOCK", "SHOT_RESULT", "SHOT_NUMBER", "FINAL_MARGIN"]
    df.drop(columns=[col for col in cols_to_drop if col in df.columns], inplace=True, errors='ignore')

    # --- Reorder and capitalize
    desired_order = [
        "player_name", "player_id", "GAME_DATE", "GAME_ID", "MATCHUP", "TIME_REMAINING", "OT", "SHOT_MADE",
        "FGM", "PTS", "PTS_TYPE", "CLOSEST_DEFENDER", "CLOSEST_DEFENDER_PLAYER_ID","CLOSE_DEF_DIST",
        "SHOT_DIST", "TOUCH_TIME", "DRIBBLES", "SHOT_CLOCK", "LOCATION", "W"
    ]
    df = df[[col for col in desired_order if col in df.columns]]
    df.columns = [col.upper() for col in df.columns]

    # --- Generate primary key
    df["SHOT_EVENT_ID"] = df.apply(generate_id, axis=1)

    # --- Final column order
    cols = ["SHOT_EVENT_ID"] + [col for col in df.columns if col != "SHOT_EVENT_ID"]
    return df[cols]

def load_data(df):
    try:
        log_message("🚚 Inserting shot logs into SQL Server...")

        df["OT"] = df["OT"].astype(bool)
        df["SHOT_MADE"] = df["SHOT_MADE"].astype(bool)

        # Safety check before insert
        if not df["SHOT_EVENT_ID"].is_unique:
            raise ValueError("❌ SHOT_EVENT_IDs are not unique! Aborting insert.")

        rows = df.where(pd.notnull(df), None).values.tolist()

        conn = get_connection()
        cursor = conn.cursor()

        insert_stmt = """
            INSERT INTO player_shot_logs (
                SHOT_EVENT_ID, PLAYER_NAME, PLAYER_ID, GAME_DATE, GAME_ID, MATCHUP, TIME_REMAINING, OT, SHOT_MADE,
                FGM, PTS, PTS_TYPE, CLOSEST_DEFENDER, CLOSEST_DEFENDER_PLAYER_ID, CLOSE_DEF_DIST,
                SHOT_DIST, TOUCH_TIME, DRIBBLES, SHOT_CLOCK, LOCATION, W
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?
            )
        """

        for i in range(0, len(rows), BATCH_SIZE):
            batch = rows[i:i + BATCH_SIZE]
            cursor.executemany(insert_stmt, batch)
            conn.commit()
            log_message(f"✅ Inserted rows {i} to {i + len(batch) - 1}")

        cursor.close()
        conn.close()

        log_message("🏁 Shot logs successfully loaded into player_shot_logs")
        log_to_db("player_shot_logs", "batch_insert", "success", error_level="info", source_script="transform_and_load_shots.py")

    except Exception as e:
        log_message(f"🔥 Error loading shot logs: {e}")
        log_to_db("player_shot_logs", "batch_insert", "failure", error_level="critical", source_script="transform_and_load_shots.py")
        raise

if __name__ == "__main__":
    df_transformed = transform_data()
    load_data(df_transformed)



