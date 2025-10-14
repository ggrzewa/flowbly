SELECT 
    sg.cluster_name,
    sg.group_name,
    sg.phrases_count,
    string_agg(sgm.phrase, ', ' ORDER BY sgm.phrase) as assigned_phrases
FROM semantic_groups sg
LEFT JOIN semantic_group_members sgm ON sg.id = sgm.group_id
GROUP BY sg.id, sg.cluster_name, sg.group_name, sg.phrases_count
ORDER BY sg.cluster_name, sg.group_name; 