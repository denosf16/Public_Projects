SELECT 
  (
    COUNT(*) * SUM(CAST(area AS FLOAT) * CAST(price AS FLOAT)) 
    - SUM(CAST(area AS FLOAT)) * SUM(CAST(price AS FLOAT))
  ) /
  (
    SQRT(COUNT(*) * SUM(POWER(CAST(area AS FLOAT), 2)) - POWER(SUM(CAST(area AS FLOAT)), 2)) *
    SQRT(COUNT(*) * SUM(POWER(CAST(price AS FLOAT), 2)) - POWER(SUM(CAST(price AS FLOAT)), 2))
  ) AS correlation
FROM pricing;

