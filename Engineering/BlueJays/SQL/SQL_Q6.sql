WITH CumulativeLeads AS (
    SELECT 
        g.game_id, 
        g.game_date, 
        l.inning, 
        SUM(l.home_runs) OVER (PARTITION BY g.game_id ORDER BY l.inning) 
            - SUM(l.away_runs) OVER (PARTITION BY g.game_id ORDER BY l.inning) 
            AS home_cumulative_lead,
        SUM(l.away_runs) OVER (PARTITION BY g.game_id ORDER BY l.inning) 
            - SUM(l.home_runs) OVER (PARTITION BY g.game_id ORDER BY l.inning) 
            AS away_cumulative_lead,
        g.home_score, g.away_score,
        g.home_team_id, g.away_team_id
    FROM Games g
    JOIN Linescore l ON g.game_id = l.game_id
),
MaxLeads AS (
    SELECT 
        game_id, 
        game_date, 
        MAX(home_cumulative_lead) AS max_home_lead,
        MAX(away_cumulative_lead) AS max_away_lead,
        MAX(home_score) AS final_home_score,
        MAX(away_score) AS final_away_score,
        MAX(home_team_id) AS home_team,
        MAX(away_team_id) AS away_team
    FROM CumulativeLeads
    GROUP BY game_id, game_date
),
BlownLeads AS (
    SELECT 
        game_id, game_date,
        CASE 
            WHEN max_home_lead > 0 AND final_home_score < final_away_score THEN max_home_lead
            WHEN max_away_lead > 0 AND final_away_score < final_home_score THEN max_away_lead
            ELSE NULL
        END AS blown_lead
    FROM MaxLeads
    WHERE (max_home_lead > 0 AND final_home_score < final_away_score) 
       OR (max_away_lead > 0 AND final_away_score < final_home_score)
)
SELECT TOP 100 game_id, game_date, blown_lead
FROM BlownLeads
ORDER BY blown_lead DESC;

-- What was the largest blown lead in 2023?

-- Uses window functions (SUM (), OVER ()) within a CTE to compute inning by inning cumulative lead; 
-- CTE join our games tbale with linescore to get inning by inning date
-- a CTE extracts the maximum lead held per game using MAX; 
-- a final CTE filters games where the leading team ended up losing;
-- uses ORDER BY pointed at the blown_leads CTE to rank results from largest blown lead to smallest
