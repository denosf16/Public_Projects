WITH LeadAfter8 AS (
    SELECT g.game_id, g.home_team_id, g.away_team_id,
           l.home_runs AS home_runs_after_8, 
           l.away_runs AS away_runs_after_8,
           g.home_score, g.away_score
    FROM Games g
    JOIN Linescore l ON g.game_id = l.game_id
    WHERE l.inning = 8
    AND ABS(l.home_runs - l.away_runs) BETWEEN 1 AND 3
)
SELECT COUNT(*) AS games_won,
       (COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM LeadAfter8), 0)) AS win_percentage
FROM LeadAfter8
WHERE (home_runs_after_8 > away_runs_after_8 AND home_score > away_score)
   OR (away_runs_after_8 > home_runs_after_8 AND away_score > home_score);


-- How often did teams win when leading by 3 runs or fewer entering the 9th inning?

-- CTE filters games where teams led by 1-3 runs after the 8th inning; 
-- WHERE allows us to filter for games that meet the criteria defined in the CTE
-- uses COUNT to determine the total number of those games (denominator); 
-- a second COUNT to count games where the team held on to win

WITH CumulativeAfter8 AS (
    SELECT g.game_id, g.home_team_id, g.away_team_id,
           SUM(l.home_runs) AS home_runs_after_8, 
           SUM(l.away_runs) AS away_runs_after_8,
           g.home_score, g.away_score
    FROM Games g
    JOIN Linescore l ON g.game_id = l.game_id
    WHERE l.inning <= 8
    GROUP BY g.game_id, g.home_team_id, g.away_team_id, g.home_score, g.away_score
),
FilteredGames AS (
    SELECT *,
           ABS(home_runs_after_8 - away_runs_after_8) AS run_differential
    FROM CumulativeAfter8
    WHERE ABS(home_runs_after_8 - away_runs_after_8) BETWEEN 1 AND 3
)
SELECT COUNT(*) AS games_won,
       (COUNT(*) * 100.0 / NULLIF((SELECT COUNT(*) FROM FilteredGames), 0)) AS win_percentage
FROM FilteredGames
WHERE (home_runs_after_8 > away_runs_after_8 AND home_score > away_score)
   OR (away_runs_after_8 > home_runs_after_8 AND away_score > home_score);
