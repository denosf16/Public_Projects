import os
# Root directory
ROOT_DIR = os.path.dirname(os.path.abspath(__file__))

# Subfolders
DATA_DIR = os.path.join(ROOT_DIR, "data")
PBP_DIR = os.path.join(DATA_DIR, "pbp_by_season")
WEEKLY_STATS_DIR = os.path.join(DATA_DIR, "weekly_data")
SEASONAL_STATS_DIR = os.path.join(DATA_DIR, "seasonal_data")
ROSTERS_DIR = os.path.join(DATA_DIR, "seasonal_rosters")
COMBINE_DIR = os.path.join(DATA_DIR, "combine_data")
DRAFT_DIR = os.path.join(DATA_DIR, "draft_picks")
TEAM_DIR = os.path.join(DATA_DIR, "team_info")
ID_MAP_DIR = os.path.join(DATA_DIR, "id_mappings")
DRAFT_VALUE_DIR = os.path.join(DATA_DIR, "draft_values")
SUMMARY_PATH = os.path.join(DATA_DIR, "parquet_summary.csv")
