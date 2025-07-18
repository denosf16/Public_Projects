SELECT 
  AVG(price) AS avg_price
FROM pricing
WHERE bedrooms >= 4
  AND bathrooms >= 1
  AND mainroad = 1
  AND airconditioning = 1
  AND parking >= 1
  AND furnishingstatus = 'semi-furnished';
