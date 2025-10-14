-- =====================================================
-- NAPRAWA TABELI semantic_group_members
-- =====================================================

-- Sprawdź czy tabela istnieje
SELECT table_name, column_name, data_type 
FROM information_schema.columns 
WHERE table_name = 'semantic_group_members' 
ORDER BY ordinal_position;

-- Jeśli tabela istnieje ale ma złe kolumny, usuń ją i utwórz ponownie
DROP TABLE IF EXISTS semantic_group_members CASCADE;

-- Utwórz tabelę z poprawną strukturą
CREATE TABLE semantic_group_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID REFERENCES semantic_groups(id) ON DELETE CASCADE,
    phrase TEXT NOT NULL,
    source_table VARCHAR(100), -- 'keyword_relations', 'autocomplete_suggestions', etc.
    source_id VARCHAR(100), -- ID z tabeli źródłowej (może być UUID lub string)
    embedding_vector DECIMAL(8,6)[], -- wektor embeddingu (512 wymiarów)
    similarity_to_centroid DECIMAL(4,3), -- podobieństwo do centrum grupy
    is_representative BOOLEAN DEFAULT FALSE, -- czy fraza reprezentuje grupę
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dodaj indeksy
CREATE INDEX idx_semantic_members_group ON semantic_group_members(group_id);
CREATE INDEX idx_semantic_members_source ON semantic_group_members(source_table, source_id);
CREATE INDEX idx_semantic_members_representative ON semantic_group_members(is_representative);

-- Sprawdź czy tabela została utworzona poprawnie
SELECT 
    t.table_name,
    c.column_name,
    c.data_type,
    c.is_nullable
FROM information_schema.tables t
JOIN information_schema.columns c ON t.table_name = c.table_name
WHERE t.table_name = 'semantic_group_members'
ORDER BY c.ordinal_position;

-- Test relacji
SELECT 
    tc.constraint_name,
    tc.constraint_type,
    kcu.column_name,
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu ON tc.constraint_name = kcu.constraint_name
LEFT JOIN information_schema.constraint_column_usage ccu ON tc.constraint_name = ccu.constraint_name
WHERE tc.table_name = 'semantic_group_members';

COMMENT ON TABLE semantic_group_members IS 'Poszczególne frazy przypisane do grup semantycznych - Moduł 1';
COMMENT ON COLUMN semantic_group_members.group_id IS 'Referencja do semantic_groups.id';
COMMENT ON COLUMN semantic_group_members.embedding_vector IS 'Wektor embeddingu OpenAI (text-embedding-3-small, 512 wymiarów)';
COMMENT ON COLUMN semantic_group_members.similarity_to_centroid IS 'Cosine similarity do centrum grupy (0-1)';
COMMENT ON COLUMN semantic_group_members.is_representative IS 'TRUE jeśli fraza jest reprezentatywna dla grupy'; 