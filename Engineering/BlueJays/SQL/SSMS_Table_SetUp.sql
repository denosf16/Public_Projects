USE MLB_StatsAPI;

CREATE TABLE Teams (
    team_id INT PRIMARY KEY,
    team_name VARCHAR(100) NOT NULL,
    team_abbr VARCHAR(10) NOT NULL,
    league VARCHAR(50) NOT NULL,
    division VARCHAR(50) NOT NULL
);

CREATE TABLE Venues (
    venue_id INT PRIMARY KEY,
    venue_name VARCHAR(100) NOT NULL,
    location VARCHAR(100) NOT NULL
);

CREATE TABLE Games (
    game_id INT PRIMARY KEY,
    game_date DATE NOT NULL,
    home_team_id INT NOT NULL REFERENCES Teams(team_id),
    away_team_id INT NOT NULL REFERENCES Teams(team_id),
    home_score INT,
    away_score INT,
    venue_id INT NOT NULL REFERENCES Venues(venue_id)
);

CREATE TABLE Linescore (
    linescore_id INT IDENTITY(1,1) PRIMARY KEY,
    game_id INT NOT NULL REFERENCES Games(game_id) ON DELETE CASCADE,
    inning INT NOT NULL,
    home_runs INT,
    away_runs INT,
    home_hits INT,
    away_hits INT,
    home_errors INT,
    away_errors INT,
    home_lob INT,
    away_lob INT
);

CREATE TABLE Logs (
    log_id INT IDENTITY(1,1) PRIMARY KEY,
    log_timestamp DATETIME NOT NULL,
    log_category VARCHAR(50) NOT NULL,
    log_message VARCHAR(MAX) NOT NULL
);

-- Index on Games table for team lookups
CREATE NONCLUSTERED INDEX idx_games_home_team ON Games(home_team_id);
CREATE NONCLUSTERED INDEX idx_games_away_team ON Games(away_team_id);
CREATE NONCLUSTERED INDEX idx_games_date ON Games(game_date);

-- Index on Linescore for fast game lookups
CREATE NONCLUSTERED INDEX idx_linescore_game_id ON Linescore(game_id);

-- Index on Logs to speed up timestamp-based queries
CREATE NONCLUSTERED INDEX idx_logs_timestamp ON Logs(log_timestamp);



