-- =====================================================
-- TABELE MODUŁU KLASTROWANIA SEMANTYCZNEGO (MODUŁ 1)
-- =====================================================

-- Tabela główna dla klastrów semantycznych 
CREATE TABLE IF NOT EXISTS semantic_clusters (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    seed_keyword_id UUID REFERENCES keywords(id) ON DELETE CASCADE,
    cluster_name VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    total_phrases INTEGER DEFAULT 0,
    embedding_model VARCHAR(100) DEFAULT 'text-embedding-3-small',
    embedding_dimensions INTEGER DEFAULT 512,
    clustering_algorithm VARCHAR(50) DEFAULT 'hdbscan',
    quality_score DECIMAL(4,3), -- -1.000 do 1.000 (silhouette score)
    processing_metadata JSONB DEFAULT '{}', -- koszty, czas, tokeny użyte
    error_message TEXT,
    module_1_completed_at TIMESTAMP WITH TIME ZONE
);

-- Tabela dla grup w ramach klastra (wyniki HDBSCAN)
CREATE TABLE IF NOT EXISTS semantic_groups (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    semantic_cluster_id UUID REFERENCES semantic_clusters(id) ON DELETE CASCADE,
    group_number INTEGER, -- -1 dla noise, 0+ dla grup
    group_label VARCHAR(255), -- nazwa grupy wygenerowana przez AI
    phrases_count INTEGER DEFAULT 0,
    avg_similarity_score DECIMAL(4,3),
    representative_phrase TEXT, -- najbardziej reprezentatywna fraza
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela dla poszczególnych fraz w grupach
CREATE TABLE IF NOT EXISTS semantic_group_members (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    group_id UUID REFERENCES semantic_groups(id) ON DELETE CASCADE,
    phrase TEXT NOT NULL,
    source_table VARCHAR(100), -- 'keyword_relations', 'autocomplete_suggestions', etc.
    source_id UUID, -- ID z tabeli źródłowej
    embedding_vector DECIMAL(8,6)[], -- wektor embeddingu (512 wymiarów)
    similarity_to_centroid DECIMAL(4,3), -- podobieństwo do centrum grupy
    is_representative BOOLEAN DEFAULT FALSE, -- czy fraza reprezentuje grupę
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Dodaj kolumnę intent_data do semantic_groups jeśli nie istnieje
ALTER TABLE semantic_groups 
ADD COLUMN IF NOT EXISTS intent_data JSONB;

-- Index dla szybszego query po intent_data
CREATE INDEX IF NOT EXISTS idx_semantic_groups_intent_data ON semantic_groups USING GIN (intent_data);

-- =====================================================
-- INDEKSY DLA WYDAJNOŚCI
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_semantic_clusters_seed_keyword ON semantic_clusters(seed_keyword_id);
CREATE INDEX IF NOT EXISTS idx_semantic_clusters_status ON semantic_clusters(processing_status);
CREATE INDEX IF NOT EXISTS idx_semantic_groups_cluster ON semantic_groups(semantic_cluster_id);
CREATE INDEX IF NOT EXISTS idx_semantic_groups_number ON semantic_groups(group_number);
CREATE INDEX IF NOT EXISTS idx_semantic_members_group ON semantic_group_members(group_id);
CREATE INDEX IF NOT EXISTS idx_semantic_members_source ON semantic_group_members(source_table, source_id);

-- =====================================================
-- FUNKCJE WYZWALACZE (TRIGGERS)
-- =====================================================

-- Trigger do automatycznej aktualizacji updated_at
CREATE OR REPLACE FUNCTION update_semantic_clusters_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_semantic_clusters_updated_at
    BEFORE UPDATE ON semantic_clusters
    FOR EACH ROW
    EXECUTE FUNCTION update_semantic_clusters_updated_at();

-- =====================================================
-- KOMENTARZE DO DOKUMENTACJI
-- =====================================================

COMMENT ON TABLE semantic_clusters IS 'Główna tabela klastrów semantycznych - Moduł 1';
COMMENT ON TABLE semantic_groups IS 'Grupy semantyczne w ramach klastra (wyniki HDBSCAN)';
COMMENT ON TABLE semantic_group_members IS 'Poszczególne frazy przypisane do grup semantycznych';

COMMENT ON COLUMN semantic_clusters.quality_score IS 'Silhouette score (-1 do 1) - jakość klastrowania';
COMMENT ON COLUMN semantic_groups.group_number IS '-1 = noise/niesklasyfikowane, 0+ = grupy semantyczne';
COMMENT ON COLUMN semantic_group_members.embedding_vector IS 'Wektor embeddingu OpenAI (text-embedding-3-small, 512 wymiarów)';
COMMENT ON COLUMN semantic_group_members.similarity_to_centroid IS 'Cosine similarity do centrum grupy (0-1)';

-- =====================================================
-- ZAPYTANIA TESTOWE
-- =====================================================

-- Test istnienia tabel
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE tablename IN ('semantic_clusters', 'semantic_groups', 'semantic_group_members')
ORDER BY tablename; 