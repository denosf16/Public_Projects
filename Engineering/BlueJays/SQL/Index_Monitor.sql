--EXEC sp_rename 'PK__Games__FFE11FCFB1B661A0', 'PK_Games', 'OBJECT';
--EXEC sp_rename 'PK__Linescor__35843AF24078FC51', 'PK_Linescore', 'OBJECT';
--EXEC sp_rename 'PK__Logs__9E2397E0CEB05F7E', 'PK_Logs', 'OBJECT';

SELECT 
    OBJECT_NAME(s.object_id) AS TableName,
    i.name AS IndexName,
    user_seeks, user_scans, user_lookups, user_updates
FROM sys.dm_db_index_usage_stats AS s
JOIN sys.indexes AS i ON s.object_id = i.object_id AND s.index_id = i.index_id
WHERE OBJECT_NAME(s.object_id) IN ('Games', 'Linescore', 'Logs');



