SELECT 
  CASE 
    WHEN price < 3000000 THEN 'Low'
    WHEN price BETWEEN 3000000 AND 6000000 THEN 'Medium'
    ELSE 'High'
  END AS price_bucket,
  COUNT(*) AS count
FROM pricing
GROUP BY 
  CASE 
    WHEN price < 3000000 THEN 'Low'
    WHEN price BETWEEN 3000000 AND 6000000 THEN 'Medium'
    ELSE 'High'
  END;
