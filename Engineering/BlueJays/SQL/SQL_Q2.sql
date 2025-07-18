SELECT AVG(
    CASE 
        WHEN g.home_team_id = t.team_id THEN CAST(l.home_runs AS FLOAT)
        WHEN g.away_team_id = t.team_id THEN CAST(l.away_runs AS FLOAT)
    END
) AS avg_blue_jays_8th_inning_runs
FROM Linescore l
JOIN Games g ON l.game_id = g.game_id
JOIN Teams t ON g.home_team_id = t.team_id OR g.away_team_id = t.team_id
WHERE t.team_name = 'Toronto Blue Jays' 
AND l.inning = 8;

-- What is the average number of runs that the Blue Jays scored in the 8th inning?

-- Joins linescore to games and teams tables to ensure team information is available; 
-- uses a CASE statement to check whether Toronto was the home or away team; 
-- uses AVG to compute the average number of runs scored in the 8th inning; 
-- uses WHERE to filter the team to Toronto, and the inning to 8.


-- NOTE: used AS FLOAT because home/away runs are stored as INT, wondering your thoughts on whether or not that column should actually be numeric







