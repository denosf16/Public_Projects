SELECT 
    t.name AS TableName,
    ind.name AS IndexName,
    ind.type_desc AS IndexType,
    STRING_AGG(col.name, ', ') WITHIN GROUP (ORDER BY ic.key_ordinal) AS IndexedColumns,
    ind.is_unique AS IsUnique
FROM 
    sys.tables t
INNER JOIN 
    sys.indexes ind ON t.object_id = ind.object_id
INNER JOIN 
    sys.index_columns ic ON ind.object_id = ic.object_id AND ind.index_id = ic.index_id
INNER JOIN 
    sys.columns col ON ic.object_id = col.object_id AND ic.column_id = col.column_id
WHERE 
    ind.is_primary_key = 0
    AND t.is_ms_shipped = 0
    AND ind.name IS NOT NULL
GROUP BY 
    t.name, ind.name, ind.type_desc, ind.is_unique
ORDER BY 
    t.name, ind.name;
