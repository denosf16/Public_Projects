import os
import sys
import pyodbc

# Ensure scripts folder is importable
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from scripts.etl_logger import log_message
from scripts.db_connect import get_connection

def create_tables():
    try:
        conn = get_connection()
        cursor = conn.cursor()

        # --- ETL LOG EVENTS ---
        cursor.execute("""
        IF OBJECT_ID('etl_log_events', 'U') IS NULL
        CREATE TABLE etl_log_events (
            log_id INT IDENTITY PRIMARY KEY,
            table_name VARCHAR(100),
            column_name VARCHAR(100),
            change_type VARCHAR(50),
            org_val VARCHAR(MAX),
            new_val VARCHAR(MAX),
            row_id VARCHAR(100),
            log_status VARCHAR(20),
            error_level VARCHAR(20),
            log_timestamp DATETIME,
            source_script VARCHAR(100)
        );
        """)

        # --- TEAM INFO ---
        cursor.execute("""
        IF OBJECT_ID('team_info', 'U') IS NULL
        CREATE TABLE team_info (
            TEAM_ID BIGINT PRIMARY KEY,
            TEAM_NAME VARCHAR(100),
            TEAM_ABBREVIATION VARCHAR(10),
            TEAM_CITY VARCHAR(50),
            TEAM_CONFERENCE VARCHAR(10),
            TEAM_DIVISION VARCHAR(20),
            MIN_YEAR INT,
            MAX_YEAR INT
        );
        """)

        # --- PLAYER INFO ---
        cursor.execute("""
        IF OBJECT_ID('player_info', 'U') IS NULL
        CREATE TABLE player_info (
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
            TEAM_NAME VARCHAR(100),
            FOREIGN KEY (TEAM_ID) REFERENCES team_info(TEAM_ID)
        );
        """)

        # --- PLAYER GAME LOGS ---
        cursor.execute("""
        IF OBJECT_ID('player_game_logs', 'U') IS NULL
        CREATE TABLE player_game_logs (
            SEASON_YEAR VARCHAR(10),
            PLAYER_ID INT NOT NULL,
            PLAYER_NAME VARCHAR(100),
            NICKNAME VARCHAR(100),
            TEAM_ID INT,
            TEAM_ABBREVIATION VARCHAR(5),
            TEAM_NAME VARCHAR(100),
            GAME_ID VARCHAR(20) NOT NULL,
            GAME_DATE DATETIME,
            MATCHUP VARCHAR(20),
            WL CHAR(1),
            MIN FLOAT,
            FGM INT,
            FGA INT,
            FG_PCT FLOAT,
            FG3M INT,
            FG3A INT,
            FG3_PCT FLOAT,
            FTM INT,
            FTA INT,
            FT_PCT FLOAT,
            OREB INT,
            DREB INT,
            REB INT,
            AST INT,
            TOV INT,
            STL INT,
            BLK INT,
            BLKA INT,
            PF INT,
            PFD INT,
            PTS INT,
            PLUS_MINUS FLOAT,
            NBA_FANTASY_PTS FLOAT,
            DD2 BIT,
            TD3 BIT,
            WNBA_FANTASY_PTS FLOAT,
            GP_RANK INT,
            W_RANK INT,
            L_RANK INT,
            W_PCT_RANK INT,
            MIN_RANK INT,
            FGM_RANK INT,
            FGA_RANK INT,
            FG_PCT_RANK INT,
            FG3M_RANK INT,
            FG3A_RANK INT,
            FG3_PCT_RANK INT,
            FTM_RANK INT,
            FTA_RANK INT,
            FT_PCT_RANK INT,
            OREB_RANK INT,
            DREB_RANK INT,
            REB_RANK INT,
            AST_RANK INT,
            TOV_RANK INT,
            STL_RANK INT,
            BLK_RANK INT,
            BLKA_RANK INT,
            PF_RANK INT,
            PFD_RANK INT,
            PTS_RANK INT,
            PLUS_MINUS_RANK INT,
            NBA_FANTASY_PTS_RANK INT,
            DD2_RANK INT,
            TD3_RANK INT,
            WNBA_FANTASY_PTS_RANK INT,
            AVAILABLE_FLAG BIT,
            MIN_SEC VARCHAR(10),
            PRIMARY KEY (PLAYER_ID, GAME_ID),
            FOREIGN KEY (PLAYER_ID) REFERENCES player_info(PLAYER_ID)
        );
        """)

        # --- PLAYER SHOT LOGS ---
        cursor.execute("""
        IF OBJECT_ID('player_shot_logs', 'U') IS NULL
        CREATE TABLE player_shot_logs (
            SHOT_EVENT_ID VARCHAR(12) PRIMARY KEY,
            PLAYER_NAME VARCHAR(50),
            PLAYER_ID INT,
            GAME_DATE DATE,
            GAME_ID VARCHAR(20),
            MATCHUP VARCHAR(25),
            TIME_REMAINING INT,
            OT BIT,
            SHOT_MADE BIT,
            FGM INT,
            PTS INT,
            PTS_TYPE INT,
            CLOSEST_DEFENDER VARCHAR(50),
            CLOSEST_DEFENDER_PLAYER_ID INT,
            SHOT_DIST FLOAT,
            TOUCH_TIME FLOAT,
            DRIBBLES INT,
            SHOT_CLOCK FLOAT,
            LOCATION CHAR(1),
            W CHAR(1),
            FOREIGN KEY (PLAYER_ID) REFERENCES player_info(PLAYER_ID)
        );
        """)

        conn.commit()
        cursor.close()
        conn.close()
        log_message("✅ Tables created or verified successfully in NBA_Shots database.")

    except Exception as e:
        log_message(f"❌ Error creating tables: {e}")

if __name__ == "__main__":
    create_tables()


