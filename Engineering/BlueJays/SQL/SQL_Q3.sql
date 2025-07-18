WITH RankedGames AS (
    SELECT game_date, game_id, (home_score + away_score) AS total_runs,
           ROW_NUMBER() OVER (PARTITION BY game_date ORDER BY game_id) AS rank
    FROM Games
    WHERE (home_score + away_score) = (
        SELECT MAX(home_score + away_score)
        FROM Games g2
        WHERE g2.game_date = Games.game_date
    )
)
SELECT game_date, game_id, total_runs
FROM RankedGames
WHERE rank = 1
ORDER BY game_date;

  
  -- What was the gamePK and number of runs of the highest scoring games on each date?

  -- Uses a CTE to compute total runs per game using home_score and away_score; 
  -- A subquery identifies the MAX total runs per date;
  -- uses ROW_NUMBER + PARTITION BY to rank games on each date; 
  -- uses WHERE rank = 1 to ensure only one game per date is shown. 
