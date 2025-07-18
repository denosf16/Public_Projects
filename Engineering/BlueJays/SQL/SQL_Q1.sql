SELECT game_date, COUNT(*) AS g_played
FROM Games
GROUP BY game_date
ORDER BY game_date

-- How many games were played on each day?

-- Uses COUNT to count the total number of games per date, 
-- then GROUP BY game_date to ensure one row per date, 
-- then ORDER BY to sort results chronologically.
