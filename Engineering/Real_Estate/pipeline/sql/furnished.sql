SELECT TOP 3 furnishingstatus, COUNT(*) AS count
FROM pricing
GROUP BY furnishingstatus
ORDER BY count DESC;
