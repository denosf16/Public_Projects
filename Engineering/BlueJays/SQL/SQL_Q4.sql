SELECT t.team_name, 
       SUM(CASE WHEN g.home_team_id = t.team_id AND g.home_score > g.away_score THEN 1 
                WHEN g.away_team_id = t.team_id AND g.away_score > g.home_score THEN 1 ELSE 0 END) AS wins,
       SUM(CASE WHEN g.home_team_id = t.team_id AND g.home_score < g.away_score THEN 1 
                WHEN g.away_team_id = t.team_id AND g.away_score < g.home_score THEN 1 ELSE 0 END) AS losses
FROM Games g
JOIN Teams t ON g.home_team_id = t.team_id OR g.away_team_id = t.team_id
WHERE t.division = 'American League East'
GROUP BY t.team_name
ORDER BY wins DESC;


-- What were the final win/loss standings of the AL East?

-- Joins games and teams tables to retrieve team and division information; 
-- uses WHERE to filter for AL EAST teams; 
-- uses a SUM(CASE WHEN) to calculate wins and losses per team; 
-- GROUP BY team name to aggregate results on a per team basis; 
-- lastly an ORDER BY DESC to get the correct order of standings.