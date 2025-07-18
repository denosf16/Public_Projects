import os
import sys
import time
import re
import pandas as pd
from concurrent.futures import ThreadPoolExecutor, as_completed
from nba_api.stats.endpoints import PlayerGameLogs, ShotChartDetail
from nba_api.stats.library.http import NBAStatsHTTP
from requests.exceptions import RequestException

# Set NBA API headers to avoid silent failures
NBAStatsHTTP.headers = {
    'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/90.0.4430.93 Safari/537.36',
    'Referer': 'https://www.nba.com/',
    'Accept-Encoding': 'gzip, deflate, br',
    'Accept-Language': 'en-US,en;q=0.9',
    'Origin': 'https://www.nba.com',
    'Connection': 'keep-alive'
}

# Add root path for imports
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))
from scripts.etl_logger import log_message

# Output directory
BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
OUTPUT_DIR = os.path.join(BASE_DIR, 'data', 'indiv_shots')
os.makedirs(OUTPUT_DIR, exist_ok=True)

SEASON = "2023-24"
MAX_WORKERS = 4
RETRY_LIMIT = 2
SLEEP_BETWEEN_CALLS = 1.0  # seconds

def fetch_shot_data(player_id, player_name, game_id, season, retry=0):
    try:
        shot_df = ShotChartDetail(
            player_id=player_id,
            team_id=None,
            game_id=game_id,
            season_nullable=season,
            season_type_all_star="Regular Season"
        ).get_data_frames()[0]
        time.sleep(SLEEP_BETWEEN_CALLS)
        return shot_df

    except Exception as e:
        if retry < RETRY_LIMIT:
            time.sleep(SLEEP_BETWEEN_CALLS * (2 + retry))
            return fetch_shot_data(player_id, player_name, game_id, season, retry + 1)
        else:
            log_message(f"❌ Shot fetch failed for {player_name} / Game {game_id}: {e}")
            return None

def extract_player_shots(player_id, group):
    player_name = re.sub(r'\W+', '_', group["PLAYER_NAME"].iloc[0])
    outfile = os.path.join(OUTPUT_DIR, f"{player_id}_{player_name}.csv")

    if os.path.exists(outfile):
        log_message(f"⏭ Skipping {player_name} — already downloaded.")
        return

    all_shots = []
    for _, row in group.iterrows():
        shots = fetch_shot_data(
            player_id=int(row["PLAYER_ID"]),
            player_name=player_name,
            game_id=row["GAME_ID"],
            season=SEASON
        )
        if shots is not None and not shots.empty:
            all_shots.append(shots)

    if all_shots:
        combined = pd.concat(all_shots, ignore_index=True)
        combined.to_csv(outfile, index=False)
        log_message(f"✅ Saved {combined.shape[0]} shots for {player_name} to {outfile}")
    else:
        log_message(f"⚠️ No shots recorded for {player_name}")

def safe_load_game_logs(season, retries=3):
    for attempt in range(retries):
        try:
            return PlayerGameLogs(season_nullable=season, season_type_nullable="Regular Season").get_data_frames()[0]
        except Exception as e:
            log_message(f"⚠️ Game log attempt {attempt+1} failed: {e}")
            time.sleep(2 * (attempt + 1))
    raise RuntimeError(f"❌ Failed to retrieve game logs after {retries} attempts")

def extract_all_shots():
    try:
        log_message(f"🔄 Starting parallel shot extraction for {SEASON}...")
        logs = safe_load_game_logs(SEASON)
        grouped = logs.groupby("PLAYER_ID")

        with ThreadPoolExecutor(max_workers=MAX_WORKERS) as executor:
            futures = [executor.submit(extract_player_shots, pid, group) for pid, group in grouped]
            for future in as_completed(futures):
                try:
                    future.result()
                except Exception as e:
                    log_message(f"⚠️ Threaded extraction error: {e}")

        log_message("✅ Shot extraction complete.")

    except Exception as e:
        log_message(f"🔥 Fatal error during shot extraction: {e}")
        raise

if __name__ == "__main__":
    extract_all_shots()




