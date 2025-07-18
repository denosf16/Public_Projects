import os
import sys
import pandas as pd
from datetime import datetime, timedelta
from nba_api.stats.endpoints import PlayerGameLogs

# Allow absolute import from project root
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.db_connect import get_connection
from scripts.etl_logger import log_message, log_to_db

def convert_min_sec(val):
    try:
        parts = str(val).split(':')
        if len(parts) == 3:
            return str(timedelta(hours=int(parts[0]), minutes=int(parts[1]), seconds=int(parts[2])))
        elif len(parts) == 2:
            return str(timedelta(minutes=int(parts[0]), seconds=int(parts[1])))
    except:
        return None
    return None

def extract_and_load_game_logs(season="2023-24", batch_size=1000):
    try:
        log_message(f"🔄 Extracting player game logs for {season} season...")

        # --- Extract from NBA API ---
        df = PlayerGameLogs(season_nullable=season, season_type_nullable="Regular Season").get_data_frames()[0]
        log_message(f"✅ Retrieved {df.shape[0]} rows.")

        # --- Save to CSV ---
        output_dir = os.path.join(os.path.dirname(__file__), "..", "data")
        os.makedirs(output_dir, exist_ok=True)
        output_path = os.path.join(output_dir, "player_game_logs.csv")
        df.to_csv(output_path, index=False)
        log_message(f"📁 Saved game logs to {output_path}")

        # --- Standardize Fields ---
        df["GAME_DATE"] = pd.to_datetime(df["GAME_DATE"], errors="coerce")
        df["MIN"] = pd.to_numeric(df["MIN"], errors="coerce").round(2)
        df["MIN_SEC"] = df["MIN_SEC"].apply(convert_min_sec).fillna("00:00:00")

        # --- Safety Check ---
        expected_cols = 69
        actual_cols = df.shape[1]
        assert actual_cols == expected_cols, f"❌ DataFrame has {actual_cols} columns, expected {expected_cols}"

        conn = get_connection()
        cursor = conn.cursor()
        log_message(f"🚚 Beginning batch insert of {len(df)} rows into [player_game_logs]...")

        insert_stmt = """
            INSERT INTO player_game_logs (
                SEASON_YEAR, PLAYER_ID, PLAYER_NAME, NICKNAME, TEAM_ID, TEAM_ABBREVIATION, TEAM_NAME,
                GAME_ID, GAME_DATE, MATCHUP, WL, MIN, FGM, FGA, FG_PCT, FG3M, FG3A, FG3_PCT,
                FTM, FTA, FT_PCT, OREB, DREB, REB, AST, TOV, STL, BLK, BLKA, PF, PFD, PTS,
                PLUS_MINUS, NBA_FANTASY_PTS, DD2, TD3, WNBA_FANTASY_PTS,
                GP_RANK, W_RANK, L_RANK, W_PCT_RANK, MIN_RANK, FGM_RANK, FGA_RANK, FG_PCT_RANK,
                FG3M_RANK, FG3A_RANK, FG3_PCT_RANK, FTM_RANK, FTA_RANK, FT_PCT_RANK,
                OREB_RANK, DREB_RANK, REB_RANK, AST_RANK, TOV_RANK, STL_RANK, BLK_RANK, BLKA_RANK,
                PF_RANK, PFD_RANK, PTS_RANK, PLUS_MINUS_RANK, NBA_FANTASY_PTS_RANK,
                DD2_RANK, TD3_RANK, WNBA_FANTASY_PTS_RANK, AVAILABLE_FLAG, MIN_SEC
            ) VALUES (
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?,
                ?, ?, ?
            )
        """

        rows = df.where(pd.notnull(df), None).values.tolist()

        for i in range(0, len(rows), batch_size):
            batch = rows[i:i+batch_size]

            for j, row in enumerate(batch):
                if len(row) != expected_cols:
                    raise ValueError(f"❌ Row {i+j} has {len(row)} columns, expected {expected_cols}")

            cursor.executemany(insert_stmt, batch)
            conn.commit()
            log_message(f"✅ Inserted rows {i} to {i+len(batch)-1}")

        cursor.close()
        conn.close()
        log_message(f"🏁 Successfully inserted {len(df)} rows into [player_game_logs].")

    except Exception as e:
        log_message(f"🔥 Fatal error in etl_player_game_logs.py: {e}")
        log_to_db("player_game_logs", "full_etl", "failure", error_level="critical", source_script="etl_player_game_logs.py")
        raise

if __name__ == "__main__":
    extract_and_load_game_logs()



