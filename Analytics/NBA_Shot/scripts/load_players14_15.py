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


def parse_height(height_str):
    try:
        if pd.notna(height_str) and '-' in str(height_str):
            ft, inch = height_str.split('-')
            return int(ft) * 12 + int(inch)
    except:
        pass
    return None


def safe_float(val):
    try:
        val = float(val)
        return val if pd.notna(val) and abs(val) < 1000 else None
    except:
        return None


def load_players_analysis():
    try:
        # Step 1: Extract historical 2014-15 season players
        all_players = CommonAllPlayers(is_only_current_season=0, season="2014-15").get_data_frames()[0]
        all_players = all_players[all_players['ROSTERSTATUS'] == 1]
        player_ids = all_players['PERSON_ID'].tolist()

        rows = []
        for pid in player_ids:
            try:
                player_info = CommonPlayerInfo(player_id=pid).get_data_frames()[0]
                row = player_info.iloc[0]

                height_in = parse_height(row['HEIGHT'])
                birth_date = pd.to_datetime(row['BIRTHDATE'], errors='coerce')
                birth_date_str = birth_date.strftime('%Y-%m-%d') if not pd.isna(birth_date) else None

                team_id = int(row['TEAM_ID']) if row['TEAM_ID'] != 0 else 0
                team_name = row['TEAM_NAME'] if pd.notna(row['TEAM_NAME']) and row['TEAM_NAME'].strip() else "FREE AGENT"

                rows.append({
                    'PLAYER_ID': row['PERSON_ID'],
                    'PLAYER_NAME': row['DISPLAY_FIRST_LAST'],
                    'BIRTHDATE': birth_date_str,
                    'HEIGHT_INCHES': safe_float(height_in),
                    'COUNTRY': row['COUNTRY'],
                    'DRAFT_YEAR': parse_int(row['DRAFT_YEAR']),
                    'DRAFT_ROUND': parse_int(row['DRAFT_ROUND']),
                    'DRAFT_NUMBER': parse_int(row['DRAFT_NUMBER']),
                    'POSITION': row['POSITION'],
                    'TEAM_ID': team_id,
                    'TEAM_NAME': team_name
                })

                log_message(f"✅ [2014-15] Enriched PLAYER_ID {pid} | Team: {team_name}")
                time.sleep(1.5)

            except Exception as e:
                log_message(f"⚠️ [2014-15] Skipped PLAYER_ID {pid} due to error: {e}")

        df = pd.DataFrame(rows)

        # Export for inspection
        output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "player_info_analysis.csv"))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        log_message(f"📁 Exported player_info_analysis to {output_path}")

        # Step 2: Insert into SQL Server
        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("""
        IF OBJECT_ID('dbo_player_info_analysis', 'U') IS NULL
        CREATE TABLE dbo_player_info_analysis (
            PLAYER_ID INT PRIMARY KEY,
            PLAYER_NAME VARCHAR(100),
            BIRTHDATE DATE,
            HEIGHT_INCHES FLOAT,
            COUNTRY VARCHAR(50),
            DRAFT_YEAR INT NOT NULL,
            DRAFT_ROUND INT NOT NULL,
            DRAFT_NUMBER INT NOT NULL,
            POSITION VARCHAR(30),
            TEAM_ID BIGINT,
            TEAM_NAME VARCHAR(100)
        );
        """)

        cursor.execute("DELETE FROM dbo_player_info_analysis;")
        log_message("🧹 Cleared all rows from dbo_player_info_analysis table.")

        inserted = 0
        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO dbo_player_info_analysis (
                        PLAYER_ID, PLAYER_NAME, BIRTHDATE, HEIGHT_INCHES,
                        COUNTRY, DRAFT_YEAR, DRAFT_ROUND, DRAFT_NUMBER,
                        POSITION, TEAM_ID, TEAM_NAME
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(row['PLAYER_ID']), row['PLAYER_NAME'], row['BIRTHDATE'], safe_float(row['HEIGHT_INCHES']),
                    row['COUNTRY'], row['DRAFT_YEAR'], row['DRAFT_ROUND'], row['DRAFT_NUMBER'],
                    row['POSITION'], row['TEAM_ID'], row['TEAM_NAME']
                ))

                log_to_db("dbo_player_info_analysis", "insert", "success", str(row['PLAYER_ID']), source_script="load_players_analysis.py")
                inserted += 1

            except Exception as row_err:
                log_message(f"❌ Insert failed for PLAYER_ID {row['PLAYER_ID']}: {row_err}")
                log_to_db(
                    "dbo_player_info_analysis", "insert", "failure",
                    row_id=str(row['PLAYER_ID']),
                    error_level="critical",
                    org_val=str(row.to_dict()),
                    source_script="load_players_analysis.py"
                )

        conn.commit()
        cursor.close()
        conn.close()
        log_message(f"✅ Inserted {inserted} players into dbo_player_info_analysis.")

    except Exception as e:
        log_message(f"❌ Fatal error in load_players_analysis.py: {e}")
        log_to_db(
            "dbo_player_info_analysis", "bulk_insert", "failure",
            error_level="critical",
            source_script="load_players_analysis.py"
        )


if __name__ == "__main__":
    load_players_analysis()

