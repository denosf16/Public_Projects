SELECT 
  airconditioning,
  AVG(price) AS avg_price
FROM pricing
GROUP BY airconditioning;
