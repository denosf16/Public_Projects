import argparse #command line arguements 
import requests #fetches data from StatsAPI
import csv # writes fetched data into CSV files
import os # file paths and directory creation
import datetime 
import pyodbc # connects to SQL server for DB operations
from datetime import timedelta # deals with date and time operations

# ---------------------- #
#  COMMAND LINE ARGUMENTS #
# ---------------------- #
parser = argparse.ArgumentParser(description="Fetch MLB game data and store in SQL Server or export as CSV.")
parser.add_argument("--start_date", required=True, help="Start date in YYYY-MM-DD format")
parser.add_argument("--end_date", required=False, help="End date in YYYY-MM-DD format (optional)")
parser.add_argument("--csv", action="store_true", help="Enable CSV export")
args = parser.parse_args()

START_DATE = datetime.datetime.strptime(args.start_date, "%Y-%m-%d")
END_DATE = datetime.datetime.strptime(args.end_date, "%Y-%m-%d") if args.end_date else START_DATE
EXPORT_CSV = args.csv

# Allows us to define a start and end date in our cmd line
# Allows us to add a --csv flag to trigger CSV export
# Converts input dates into datetime objects; if --end date is missing, defaults to start date
# Exports to CSV if --csv is provided in cmd line

BASE_EXPORT_DIR = r"C:\Users\denos\OneDrive\Projects\BlueJays\data_exports" ## Change to your own path if testing

DB_SERVER = "RAMSEY_BOLTON\\SQLEXPRESS" ## Change to your own if testing (to be clear my server name is a game of thrones RAMS pun)
DB_NAME = "MLB_StatsAPI" ## Create before running
DB_CONN_STRING = f"DRIVER={{SQL Server}};SERVER={DB_SERVER};DATABASE={DB_NAME};Trusted_Connection=yes;"

# Sets export directory and SQL connectors

# ---------------------- #
#  LOGGING FUNCTION      #
# ---------------------- #
def log_message(category, message):
    """Logs messages to console and database."""
    timestamp = datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')
    log_entry = f"[{timestamp}] {category}: {message}"
    print(log_entry)

    try:
        conn = pyodbc.connect(DB_CONN_STRING)
        cursor = conn.cursor()
        cursor.execute("INSERT INTO Logs (log_timestamp, log_category, log_message) VALUES (?, ?, ?)",
                       datetime.datetime.now(), category, message)
        conn.commit()
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Failed to log to database: {e}")

# Logs messages with timestamps, stores logs in LOGS table in MSS
# Handles logging failures gracefully

# ---------------------- #
#  SAFE CONVERSIONS      #
# ---------------------- #
def safe_int(value):
    """Safely converts a value to an integer or returns None."""
    try:
        return int(float(value)) if value not in [None, "", " ", "nan", "NaN"] else None
    except (ValueError, TypeError):
        return None
    
# Converts API values to INT, handling missing or invalid inputs. Upon initial review of API content, no decimals will be needed for this exercise... upon further review I was wrong (SQL Q2 math requires a float)

# ---------------------- #
#  SAVE TO CSV FUNCTION  #
# ---------------------- #
def save_to_csv(base_folder, filename, data, headers):
    """Writes data to a CSV file within the specified folder."""
    filepath = os.path.join(base_folder, filename)
    file_exists = os.path.isfile(filepath)

    with open(filepath, mode="a", newline="") as f:
        writer = csv.writer(f)
        if not file_exists:
            writer.writerow(headers)  # Write headers only if file does not exist
        writer.writerows(data)
        
# Ensures CSV files are saved in the correct directory
# Appends data to an existing CSV or writes a new one with headers

# ---------------------- #
#  DATA INSERT FUNCTIONS #
# ---------------------- #
def insert_team(cursor, team, inserted_teams, teams_data):
    """Insert team if it doesn't already exist. Track inserted teams for summary logging and CSV export."""
    team_id = safe_int(team.get("id"))
    team_name = team.get("name", "UNKNOWN").strip()
    team_abbr = team.get("abbreviation", team_name[:3].upper())

    league = team.get("league", {}).get("name") or "Unknown League"
    division = team.get("division", {}).get("name") or "Unknown Division"

    cursor.execute("SELECT COUNT(1) FROM Teams WHERE team_id = ?", (team_id,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO Teams (team_id, team_name, team_abbr, league, division) VALUES (?, ?, ?, ?, ?)",
                       (team_id, team_name, team_abbr, league, division))
        inserted_teams.add(team_id)
        teams_data.add((team_id, team_name, team_abbr, league, division))

# Extracts team ID, abbreviation, league, division
# If missing, assigns default values 
# Prevents duplicate team inserts

def insert_venue(cursor, venue, inserted_venues, venues_data):
    """Insert venue if it doesn't already exist. Track inserted venues for summary logging and CSV export."""
    venue_id = safe_int(venue.get("id"))
    venue_name = venue.get("name", "UNKNOWN").strip()
    location = venue.get("location", {}).get("city", "Unknown City") + ", " + venue.get("location", {}).get("state", "Unknown State")

    cursor.execute("SELECT COUNT(1) FROM Venues WHERE venue_id = ?", (venue_id,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO Venues (venue_id, venue_name, location) VALUES (?, ?, ?)",
                       (venue_id, venue_name, location))
        inserted_venues.add(venue_id)
        venues_data.add((venue_id, venue_name, location))

# Extracts venue ID, name, location
# If missing, assigns default values
# Prevents duplicate venue inserts        

def insert_game(cursor, game, games_data):
    """Insert game into the database if it doesn't already exist, and track for CSV export."""
    game_id = safe_int(game.get("gamePk"))
    game_date = game.get("officialDate")
    home_team_id = safe_int(game["teams"]["home"]["team"].get("id"))
    away_team_id = safe_int(game["teams"]["away"]["team"].get("id"))
    home_score = safe_int(game["teams"]["home"].get("score"))
    away_score = safe_int(game["teams"]["away"].get("score"))
    venue_id = safe_int(game.get("venue", {}).get("id"))

    if home_score is None and away_score is None:
        log_message("WARNING", f"Skipping Game ID {game_id} - No valid scores.")
        return

    cursor.execute("SELECT COUNT(1) FROM Games WHERE game_id = ?", (game_id,))
    if cursor.fetchone()[0] == 0:
        cursor.execute("INSERT INTO Games (game_id, game_date, home_team_id, away_team_id, home_score, away_score, venue_id) "
                       "VALUES (?, ?, ?, ?, ?, ?, ?)", 
                       (game_id, game_date, home_team_id, away_team_id, home_score, away_score, venue_id))
        games_data.append((game_id, game_date, home_team_id, away_team_id, home_score, away_score, venue_id))

# Extracts game ID, game_date, team ID's, and scores
# If a game's scores are missing (NULL), it is skipped - to avoid logging rainouts
# Ensures the game is not a duplicate

def insert_linescore(cursor, game, linescore_data):
    """Insert linescore into the database and track for CSV export."""
    game_id = safe_int(game.get("gamePk"))

    cursor.execute("SELECT COUNT(1) FROM Games WHERE game_id = ?", (game_id,))
    if cursor.fetchone()[0] == 0:
        log_message("WARNING", f"Skipping Linescore for Game {game_id} - Game not found in Games table.")
        return

    sorted_innings = sorted(game.get("linescore", {}).get("innings", []), key=lambda x: safe_int(x.get("num")))

    for inning in sorted_innings:
        inning_num = safe_int(inning.get("num"))
        home_runs = safe_int(inning["home"].get("runs"))
        away_runs = safe_int(inning["away"].get("runs"))
        home_hits = safe_int(inning["home"].get("hits"))
        away_hits = safe_int(inning["away"].get("hits"))
        home_errors = safe_int(inning["home"].get("errors"))
        away_errors = safe_int(inning["away"].get("errors"))
        home_lob = safe_int(inning["home"].get("leftOnBase"))
        away_lob = safe_int(inning["away"].get("leftOnBase"))

        cursor.execute("INSERT INTO Linescore (game_id, inning, home_runs, away_runs, home_hits, away_hits, home_errors, away_errors, home_lob, away_lob) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)",
            (game_id, inning_num, home_runs, away_runs, home_hits, away_hits, home_errors, away_errors, home_lob, away_lob))
        
        linescore_data.append((game_id, inning_num, home_runs, away_runs, home_hits, away_hits, home_errors, away_errors, home_lob, away_lob))

# Extracts game ID and verifies it exists
# Loops through each inning, capturing RUNS, HITS, ERRORS, LOB Stats
# Logs a warning if game ID does not exist in games
# Defaults missing numerical values to NULL 

# ---------------------- #
#  MAIN SCRIPT          #
# ---------------------- #
def main():
    conn = pyodbc.connect(DB_CONN_STRING)
    cursor = conn.cursor()

    inserted_teams = set()
    inserted_venues = set()
    teams_data = set()
    venues_data = set()
    games_data = []
    linescore_data = []

    folder_name = f"{START_DATE.strftime('%Y%m%d')}_{END_DATE.strftime('%Y%m%d')}"
    export_folder = os.path.join(BASE_EXPORT_DIR, folder_name)
    os.makedirs(export_folder, exist_ok=True)

# Create a single folder for the entire date range instead of per-day folders

    for date in (START_DATE + timedelta(n) for n in range((END_DATE - START_DATE).days + 1)):
        date_str = date.strftime("%Y-%m-%d")
        url = f"https://statsapi.mlb.com/api/v1/schedule?sportId=1&date={date_str}&hydrate=linescore,team,venue"
        response = requests.get(url).json()

        if not response.get("dates") or not response["dates"][0].get("games"):
            log_message("WARNING", f"No games found for {date_str}. Skipping.")
            continue

# Creates an export folder for all dates in the range
# Iterates through each day, requests MLB data, and processes it

        games_data_api = response["dates"][0]["games"]

        # First pass: Insert Teams & Venues
        for game in games_data_api:
            insert_team(cursor, game["teams"]["home"]["team"], inserted_teams, teams_data)
            insert_team(cursor, game["teams"]["away"]["team"], inserted_teams, teams_data)
            insert_venue(cursor, game["venue"], inserted_venues, venues_data)

        conn.commit()  # Commit Teams & Venues before inserting Games

        # Second pass: Insert Games & Linescore
        for game in games_data_api:
            insert_game(cursor, game, games_data)
            insert_linescore(cursor, game, linescore_data)

        conn.commit()

    # Save CSVs if required
    if EXPORT_CSV:
        save_to_csv(export_folder, "Teams.csv", teams_data, ["team_id", "team_name", "team_abbr", "league", "division"])
        save_to_csv(export_folder, "Venues.csv", venues_data, ["venue_id", "venue_name", "location"])
        save_to_csv(export_folder, "Games.csv", games_data, ["game_id", "game_date", "home_team_id", "away_team_id", "home_score", "away_score", "venue_id"])
        save_to_csv(export_folder, "Linescore.csv", linescore_data, ["game_id", "inning", "home_runs", "away_runs", "home_hits", "away_hits", "home_errors", "away_errors", "home_lob", "away_lob"])
        log_message("SUMMARY", f"CSV files saved in {export_folder}")

    # Log summary
    if inserted_teams:
        log_message("SUMMARY", f"Inserted {len(inserted_teams)} new teams.")
    if inserted_venues:
        log_message("SUMMARY", f"Inserted {len(inserted_venues)} new venues.")

    cursor.close()
    conn.close()

if __name__ == "__main__":
    main()


