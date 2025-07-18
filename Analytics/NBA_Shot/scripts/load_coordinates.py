import pandas as pd
import time
import os
from nba_api.stats.endpoints import ShotChartDetail, CommonAllPlayers

def get_2014_15_player_ids():
    """Get all player IDs who played in the 2014-15 season."""
    df = CommonAllPlayers(is_only_current_season=0, season="2014-15").get_data_frames()[0]
    df = df[df['ROSTERSTATUS'] == 1]  # Only players who were on a roster
    return df[['PERSON_ID', 'DISPLAY_FIRST_LAST']].values.tolist()

def get_shotchart(player_id, season='2014-15'):
    try:
        response = ShotChartDetail(
            team_id=0,
            player_id=player_id,
            season_type_all_star='Regular Season',
            season_nullable=season,
            context_measure_simple='FGA'
        )
        df = response.get_data_frames()[0]
        return df
    except Exception as e:
        print(f"❌ Error fetching player {player_id}: {e}")
        return pd.DataFrame()

if __name__ == "__main__":
    output_path = r"C:\Repos\NBA_Shot\data\corresponding_coordinates.csv"
    season = "2014-15"
    all_data = []
    players = get_2014_15_player_ids()

    print(f"🔁 Starting download for {len(players)} players...")

    for i, (pid, name) in enumerate(players):
        print(f"[{i+1}/{len(players)}] ⛹️  {name} (ID: {pid})")
        df = get_shotchart(pid, season)
        if not df.empty:
            df["PLAYER_ID"] = pid
            df["PLAYER_NAME"] = name
            all_data.append(df)
        time.sleep(1.2)  # Slow down to avoid rate limits

    if all_data:
        final_df = pd.concat(all_data, ignore_index=True)
        os.makedirs(os.path.dirname(output_path), exist_ok=True)
        final_df.to_csv(output_path, index=False)
        print(f"✅ Saved {len(final_df)} total shots to {output_path}")
    else:
        print("⚠️ No shot data collected.")


