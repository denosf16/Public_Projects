SELECT DISTINCT
  PERCENTILE_CONT(0.5) WITHIN GROUP (ORDER BY price_per_sqft)
  OVER () AS median_pps
FROM pricing;

