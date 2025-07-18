SELECT 
  CAST(SUM(CAST(mainroad AS INT)) * 100.0 / COUNT(*) AS DECIMAL(5,2)) AS mainroad_pct
FROM pricing;
