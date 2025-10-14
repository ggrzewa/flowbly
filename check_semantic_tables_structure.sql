-- Sprawdzenie struktury tabeli semantic_groups
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'semantic_groups'
ORDER BY ordinal_position;

-- Sprawdzenie struktury tabeli semantic_group_members  
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'semantic_group_members'
ORDER BY ordinal_position;

-- Sprawdzenie struktury tabeli semantic_clusters
SELECT column_name, data_type, is_nullable
FROM information_schema.columns 
WHERE table_name = 'semantic_clusters'
ORDER BY ordinal_position; 