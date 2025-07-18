SELECT 
    t.name AS TableName,
    c.name AS ColumnName,
    ty.name AS DataType,
    c.max_length AS MaxLength,
    c.is_nullable AS IsNullable
FROM 
    sys.columns c
JOIN 
    sys.tables t ON c.object_id = t.object_id
JOIN 
    sys.types ty ON c.user_type_id = ty.user_type_id
ORDER BY 
    t.name, c.column_id;
