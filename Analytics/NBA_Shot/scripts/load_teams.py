import os
import sys
import time
import pandas as pd
from nba_api.stats.endpoints import TeamInfoCommon

# Make scripts importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.db_connect import get_connection
from scripts.etl_logger import log_message, log_to_db

def extract_team_info_to_csv():
    try:
        team_ids = [
            1610612737, 1610612738, 1610612739, 1610612740, 1610612741,
            1610612742, 1610612743, 1610612744, 1610612745, 1610612746,
            1610612747, 1610612748, 1610612749, 1610612750, 1610612751,
            1610612752, 1610612753, 1610612754, 1610612755, 1610612756,
            1610612757, 1610612758, 1610612759, 1610612760, 1610612761,
            1610612762, 1610612763, 1610612764, 1610612765, 1610612766
        ]

        rows = []
        for team_id in team_ids:
            try:
                team_info = TeamInfoCommon(team_id=team_id).get_data_frames()[0]
                if not team_info.empty:
                    rows.append(team_info.iloc[0])
                time.sleep(1.5)  # Rate limiting prevention
            except Exception as e:
                log_message(f"⚠️ Timeout or error for team_id {team_id}: {e}")

        df = pd.DataFrame(rows)
        df = df.rename(columns={
            'TEAM_ID': 'TEAM_ID',
            'TEAM_CITY': 'TEAM_CITY',
            'TEAM_NAME': 'TEAM_NAME',
            'TEAM_ABBREVIATION': 'TEAM_ABBREVIATION',
            'TEAM_CONFERENCE': 'TEAM_CONFERENCE',
            'TEAM_DIVISION': 'TEAM_DIVISION',
            'MIN_YEAR': 'MIN_YEAR',
            'MAX_YEAR': 'MAX_YEAR'
        })

        output_path = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "data", "team_info.csv"))
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        df.to_csv(output_path, index=False)
        log_message(f"📁 Exported team_info to {output_path}")
        return output_path

    except Exception as e:
        log_message(f"❌ Failed to extract team data: {e}")
        raise

def load_teams_from_csv(csv_path):
    try:
        df = pd.read_csv(csv_path)

        conn = get_connection()
        cursor = conn.cursor()

        cursor.execute("DELETE FROM team_info;")
        log_message("🧹 Deleted all rows from team_info table.")

        inserted = 0

        for _, row in df.iterrows():
            try:
                cursor.execute("""
                    INSERT INTO team_info (
                        TEAM_ID, TEAM_NAME, TEAM_ABBREVIATION, TEAM_CITY,
                        TEAM_CONFERENCE, TEAM_DIVISION, MIN_YEAR, MAX_YEAR
                    ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    int(row['TEAM_ID']), row['TEAM_NAME'], row['TEAM_ABBREVIATION'], row['TEAM_CITY'],
                    row['TEAM_CONFERENCE'], row['TEAM_DIVISION'], int(row['MIN_YEAR']), int(row['MAX_YEAR'])
                ))
                log_to_db(
                    table_name="team_info",
                    change_type="insert",
                    log_status="success",
                    row_id=str(row['TEAM_ID']),
                    source_script="load_teams.py"
                )
                inserted += 1

            except Exception as row_err:
                log_message(f"❌ Insert failed for TEAM_ID {row['TEAM_ID']}: {row_err}")
                log_to_db(
                    table_name="team_info",
                    change_type="insert",
                    log_status="failure",
                    error_level="critical",
                    row_id=str(row['TEAM_ID']),
                    org_val=str(row.to_dict()),
                    source_script="load_teams.py"
                )

        conn.commit()
        cursor.close()
        conn.close()

        log_message(f"✅ Inserted {inserted} rows into team_info.")

    except Exception as e:
        log_message(f"❌ Fatal error loading team_info from CSV: {e}")
        log_to_db(
            table_name="team_info",
            change_type="bulk_insert",
            log_status="failure",
            error_level="critical",
            source_script="load_teams.py"
        )

if __name__ == "__main__":
    csv_file = extract_team_info_to_csv()
    load_teams_from_csv(csv_file)

