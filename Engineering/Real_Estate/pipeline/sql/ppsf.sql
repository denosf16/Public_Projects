SELECT 
  has_aircon_and_heat,
  AVG(price_per_sqft) AS avg_pps
FROM pricing
GROUP BY has_aircon_and_heat;
