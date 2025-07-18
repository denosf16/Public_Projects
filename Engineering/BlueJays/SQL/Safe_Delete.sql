USE MLB_StatsAPI;

-- 1️ Delete all Linescore records first (depends on Games)
DELETE FROM Linescore;

-- 2️ Delete all Games (depends on Teams and Venues)
DELETE FROM Games;

-- 3️ Delete all Teams and Venues (independent tables)
DELETE FROM Teams;
DELETE FROM Venues;

-- 4️Delete all logs if needed
DELETE FROM Logs;

DBCC CHECKIDENT ('Linescore', RESEED, 1);
DBCC CHECKIDENT ('Logs', RESEED, 1);
