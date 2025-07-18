-- List tables and row counts
SELECT 
    t.name AS table_name,
    s.name AS schema_name,
    p.rows AS row_count
FROM sys.tables t
JOIN sys.schemas s ON t.schema_id = s.schema_id
JOIN sys.partitions p ON t.object_id = p.object_id
WHERE p.index_id IN (0,1)
GROUP BY t.name, s.name, p.rows;

-- Show table columns
SELECT 
    TABLE_NAME, COLUMN_NAME, DATA_TYPE, IS_NULLABLE
FROM INFORMATION_SCHEMA.COLUMNS
WHERE TABLE_NAME IN ('pricing', 'event_log');

-- Show indexes
SELECT 
    t.name AS table_name,
    i.name AS index_name,
    i.type_desc AS index_type,
    c.name AS column_name
FROM sys.indexes i
JOIN sys.index_columns ic ON i.object_id = ic.object_id AND i.index_id = ic.index_id
JOIN sys.columns c ON ic.object_id = c.object_id AND ic.column_id = c.column_id
JOIN sys.tables t ON i.object_id = t.object_id
WHERE t.name IN ('pricing')
ORDER BY t.name, i.name;

