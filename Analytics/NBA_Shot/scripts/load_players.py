import os
import sys
import pandas as pd
import time
from nba_api.stats.endpoints import CommonAllPlayers, CommonPlayerInfo

# Enable script imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.db_connect import get_connection
from scripts.etl_logger import log_message, log_to_db

def parse_int(val):
    try:
        return int(val) if str(val).isdigit() else 0
    except:
        return 0

def load_players():
    try:
        # Step 1: Extract current season players
        all_players = CommonAllPlayers(is_only_current_season=1, season="2023-24").get_data_frames()[0]
        player_ids = all_players['PERSON_ID'].tolist()

        rows = []
        for pid in player_ids:
            try:
                player_info = CommonPlayerInfo(player_id=pid).get_data_frames()[0]
                row = player_info.iloc[0]

                # Parse height
                height_raw = row['HEIGHT']
                if pd.notna(height_raw) and '-' in str(height_raw):
                    ft, inch = height_raw.split('-')
                    height_in = int(ft) * 12 + int(inch)
                else:
                    height_in = None

                # Parse birthdate
                birth_date = pd.to_datetime(row['BIRTHDATE'], errors='coerce')
                birth_date_str = birth_date.strftime('%Y-%m-%d') if not pd.isna(birth_date) else None

                # Handle missing team
                team_id = int(row['TEAM_ID']) if row['TEAM_ID'] != 0 else 0
                team_name = row['TEAM_NAME'] if pd.notna(row['TEAM_NAME']) and row['TEAM_NAME'].strip() else "FREE AGENT"

                rows.append({
                    'PLAYER_ID': row['PERSON_ID'],
                    'PLAYER_NAME': row['DISPLAY_FIRST_LAST'],
                    'BIRTHDATE': birth_date_str,
                    'HEIGHT_INCHES': float(height_in) if height_in is not None else None,
                    'COUNTRY': row['COUNTRY'],
                    'DRAFT_YEAR': parse_int(row['DRAFT_YEAR']),
                    'DRAFT_ROUND': parse_int(row['DRAFT_ROUND']),
                    'DRAFT_NUMBER': parse_int(row['DRAFT_NUMBER']),
                    'POSITION': row['POSITION'],
                    'TEAM_ID': team_id,
                    'TEAM_NAME': team_name
                })

                log_message(f"✅ Enriched PLAYER_ID {pid} | Team: {team_name}")
                time.sleep(1.5)

            except Exception as e:
                log_message(f"⚠️ Skipped PLAYER_ID {pid} due to error: {e}")

        df = pd.DataFrame(rows)

        # Step 2: Export CSV
        output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "player_info.csv"))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        log_message(f"📁 Exported player_info to {output_path}")

        # Step 3: Load into SQL
        conn = get_connection()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM player_info;")
        log_message("🧹 Cleared all rows from player_info table.")

        inserted = 0
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO player_info (
                        PLAYER_ID, PLAYER_NAME, BIRTHDATE, HEIGHT_INCHES,
                        COUNTRY, DRAFT_YEAR, DRAFT_ROUND, DRAFT_NUMBER,
                        POSITION, TEAM_ID, TEAM_NAME
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(row['PLAYER_ID']), row['PLAYER_NAME'], row['BIRTHDATE'], row['HEIGHT_INCHES'],
                    row['COUNTRY'], row['DRAFT_YEAR'], row['DRAFT_ROUND'], row['DRAFT_NUMBER'],
                    row['POSITION'], row['TEAM_ID'], row['TEAM_NAME']
                ))

                log_to_db("player_info", "insert", "success", str(row['PLAYER_ID']), source_script="load_players.py")
                inserted += 1

            except Exception as row_err:
                log_message(f"❌ Insert failed for PLAYER_ID {row['PLAYER_ID']}: {row_err}")
                log_to_db(
                    "player_info", "insert", "failure",
                    row_id=str(row['PLAYER_ID']),
                    error_level="critical",
                    org_val=str(row.to_dict()),
                    source_script="load_players.py"
                )

        conn.commit()
        cursor.close()
        conn.close()
        log_message(f"✅ Inserted {inserted} players into player_info.")

    except Exception as e:
        log_message(f"❌ Fatal error in load_players.py: {e}")
        log_to_db(
            "player_info", "bulk_insert", "failure",
            error_level="critical",
            source_script="load_players.py"
        )

if __name__ == "__main__":
    load_players()







