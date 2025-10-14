-- =====================================================
-- TABELE MODUŁU ARCHITECTURE GENERATOR (MODUŁ 3)
-- =====================================================

-- Tabela główna dla architektur stron
CREATE TABLE IF NOT EXISTS architectures (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    semantic_cluster_id UUID REFERENCES semantic_clusters(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL, -- np. "Pompy Ciepła - SILO Architecture"
    architecture_type VARCHAR(50) NOT NULL, -- 'silo' lub 'clusters'
    seed_keyword VARCHAR(255) NOT NULL,
    domain VARCHAR(255) DEFAULT 'example.com',
    hierarchy JSONB NOT NULL, -- hierarchia z LLM (pillar, categories, subcategories)
    total_pages INTEGER DEFAULT 0,
    max_depth INTEGER DEFAULT 0, -- głębokość architektury (0 = pillar, 1 = category, 2 = subcategory)
    cross_links_count INTEGER DEFAULT 0, -- liczba strategic bridges
    seo_score INTEGER DEFAULT 0, -- wynik SEO (0-100)
    processing_status VARCHAR(50) DEFAULT 'pending', -- pending, processing, completed, failed
    processing_time DECIMAL(10,3) DEFAULT 0, -- czas generowania w sekundach
    user_id UUID, -- dla przyszłego systemu użytkowników
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela dla poszczególnych stron w architekturze
CREATE TABLE IF NOT EXISTS architecture_pages (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    architecture_id UUID REFERENCES architectures(id) ON DELETE CASCADE,
    name VARCHAR(255) NOT NULL, -- nazwa strony
    url_path VARCHAR(500) NOT NULL, -- ścieżka URL (np. "/pompy-ciepla/koszty/")
    url_slug VARCHAR(255) NOT NULL, -- slug (np. "koszty")
    page_type VARCHAR(50) NOT NULL, -- 'pillar', 'category', 'subcategory', 'cluster_page'
    parent_page_id UUID REFERENCES architecture_pages(id) ON DELETE SET NULL,
    depth_level INTEGER DEFAULT 0, -- 0=pillar, 1=category, 2=subcategory
    target_keywords TEXT[], -- docelowe słowa kluczowe dla tej strony
    estimated_content_length INTEGER DEFAULT 1500, -- szacowana długość treści w słowach
    cluster_name VARCHAR(255), -- nazwa klastra semantycznego (jeśli applicable)
    cluster_phrase_count INTEGER DEFAULT 0, -- liczba fraz w klasterze
    business_intent VARCHAR(50), -- 'informational', 'commercial', 'local', 'transactional'
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela dla planów internal linking
CREATE TABLE IF NOT EXISTS architecture_links (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    architecture_id UUID REFERENCES architectures(id) ON DELETE CASCADE,
    from_page_id UUID REFERENCES architecture_pages(id) ON DELETE CASCADE,
    to_page_id UUID REFERENCES architecture_pages(id) ON DELETE CASCADE,
    link_type VARCHAR(50) NOT NULL, -- 'upward_category', 'upward_pillar', 'strategic_bridge'
    anchor_text VARCHAR(255) NOT NULL, -- proponowany tekst linku
    placement TEXT[] DEFAULT '{}', -- gdzie umieścić link (breadcrumb, content_intro, sidebar, etc.)
    link_context TEXT, -- kontekst/uzasadnienie dla linku
    similarity_score DECIMAL(4,3), -- dla strategic bridges (cosine similarity)
    bridge_rationale TEXT, -- uzasadnienie strategic bridge
    semantic_relationship VARCHAR(50), -- typ relacji semantycznej
    priority INTEGER DEFAULT 1, -- 1=high (vertical), 2=medium (bridges), 3=low
    frequency VARCHAR(50) DEFAULT '1-2_per_article', -- częstotliwość dla strategic bridges
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela dla struktur nawigacji
CREATE TABLE IF NOT EXISTS architecture_navigation (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    architecture_id UUID REFERENCES architectures(id) ON DELETE CASCADE,
    nav_type VARCHAR(50) NOT NULL, -- 'main_menu', 'breadcrumb_templates', 'sidebar_navigation', 'mobile_menu'
    structure JSONB NOT NULL, -- struktura nawigacji w JSON
    max_depth INTEGER DEFAULT 3,
    mobile_friendly BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Tabela dla notatek implementacyjnych
CREATE TABLE IF NOT EXISTS architecture_implementations (
    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
    architecture_id UUID REFERENCES architectures(id) ON DELETE CASCADE,
    category VARCHAR(100) NOT NULL, -- 'wordpress_tips', 'technical_seo', 'content_strategy', 'seo_recommendations'
    recommendations TEXT[] NOT NULL, -- lista rekomendacji
    platform VARCHAR(50) DEFAULT 'general', -- 'wordpress', 'shopify', 'general'
    difficulty_level VARCHAR(20) DEFAULT 'medium', -- 'easy', 'medium', 'hard'
    estimated_hours DECIMAL(4,1) DEFAULT 5.0, -- szacowany czas implementacji
    priority INTEGER DEFAULT 2, -- 1=high, 2=medium, 3=low
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- =====================================================
-- INDEKSY DLA WYDAJNOŚCI
-- =====================================================

CREATE INDEX IF NOT EXISTS idx_architectures_cluster ON architectures(semantic_cluster_id);
CREATE INDEX IF NOT EXISTS idx_architectures_type ON architectures(architecture_type);
CREATE INDEX IF NOT EXISTS idx_architectures_user ON architectures(user_id);
CREATE INDEX IF NOT EXISTS idx_architectures_status ON architectures(processing_status);
CREATE INDEX IF NOT EXISTS idx_architectures_created ON architectures(created_at DESC);

CREATE INDEX IF NOT EXISTS idx_architecture_pages_arch ON architecture_pages(architecture_id);
CREATE INDEX IF NOT EXISTS idx_architecture_pages_parent ON architecture_pages(parent_page_id);
CREATE INDEX IF NOT EXISTS idx_architecture_pages_type ON architecture_pages(page_type);
CREATE INDEX IF NOT EXISTS idx_architecture_pages_depth ON architecture_pages(depth_level);
CREATE INDEX IF NOT EXISTS idx_architecture_pages_cluster ON architecture_pages(cluster_name);

CREATE INDEX IF NOT EXISTS idx_architecture_links_arch ON architecture_links(architecture_id);
CREATE INDEX IF NOT EXISTS idx_architecture_links_from ON architecture_links(from_page_id);
CREATE INDEX IF NOT EXISTS idx_architecture_links_to ON architecture_links(to_page_id);
CREATE INDEX IF NOT EXISTS idx_architecture_links_type ON architecture_links(link_type);
CREATE INDEX IF NOT EXISTS idx_architecture_links_priority ON architecture_links(priority);

CREATE INDEX IF NOT EXISTS idx_architecture_nav_arch ON architecture_navigation(architecture_id);
CREATE INDEX IF NOT EXISTS idx_architecture_nav_type ON architecture_navigation(nav_type);

CREATE INDEX IF NOT EXISTS idx_architecture_impl_arch ON architecture_implementations(architecture_id);
CREATE INDEX IF NOT EXISTS idx_architecture_impl_category ON architecture_implementations(category);
CREATE INDEX IF NOT EXISTS idx_architecture_impl_priority ON architecture_implementations(priority);

-- =====================================================
-- FUNKCJE WYZWALACZE (TRIGGERS)
-- =====================================================

-- Trigger do automatycznej aktualizacji updated_at
CREATE OR REPLACE FUNCTION update_architectures_updated_at()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ language 'plpgsql';

CREATE TRIGGER trigger_architectures_updated_at
    BEFORE UPDATE ON architectures
    FOR EACH ROW
    EXECUTE FUNCTION update_architectures_updated_at();

-- =====================================================
-- VIEWS DLA ŁATWIEJSZEGO QUERY
-- =====================================================

-- View dla kompletnych architektur z podstawowymi statystykami
CREATE OR REPLACE VIEW architecture_summary AS
SELECT 
    a.id,
    a.name,
    a.architecture_type,
    a.seed_keyword,
    a.domain,
    a.total_pages,
    a.max_depth,
    a.cross_links_count,
    a.seo_score,
    a.processing_status,
    a.processing_time,
    a.created_at,
    a.updated_at,
    sc.cluster_name as source_cluster_name,
    sc.total_phrases as source_total_phrases,
    sc.quality_score as source_quality_score,
    COUNT(ap.id) as actual_page_count,
    COUNT(al.id) as actual_link_count
FROM architectures a
LEFT JOIN semantic_clusters sc ON a.semantic_cluster_id = sc.id
LEFT JOIN architecture_pages ap ON a.id = ap.architecture_id
LEFT JOIN architecture_links al ON a.id = al.architecture_id
GROUP BY a.id, sc.cluster_name, sc.total_phrases, sc.quality_score;

-- View dla hierarchii stron (drzewo)
CREATE OR REPLACE VIEW architecture_page_hierarchy AS
WITH RECURSIVE page_tree AS (
    -- Poziom 0: Pillar pages
    SELECT 
        ap.id,
        ap.architecture_id,
        ap.name,
        ap.url_path,
        ap.page_type,
        ap.depth_level,
        ap.parent_page_id,
        ap.name as path_name,
        0 as tree_level
    FROM architecture_pages ap
    WHERE ap.parent_page_id IS NULL
    
    UNION ALL
    
    -- Poziomy rekursywne: kategorie i subkategorie
    SELECT 
        ap.id,
        ap.architecture_id,
        ap.name,
        ap.url_path,
        ap.page_type,
        ap.depth_level,
        ap.parent_page_id,
        pt.path_name || ' > ' || ap.name as path_name,
        pt.tree_level + 1 as tree_level
    FROM architecture_pages ap
    INNER JOIN page_tree pt ON ap.parent_page_id = pt.id
)
SELECT * FROM page_tree
ORDER BY architecture_id, tree_level, name;

-- =====================================================
-- KOMENTARZE DO DOKUMENTACJI
-- =====================================================

COMMENT ON TABLE architectures IS 'Główna tabela architektur stron - Moduł 3 Architecture Generator';
COMMENT ON TABLE architecture_pages IS 'Poszczególne strony w architekturze (pillar, categories, subcategories)';
COMMENT ON TABLE architecture_links IS 'Plan internal linking (vertical links + strategic bridges z embeddingami)';
COMMENT ON TABLE architecture_navigation IS 'Struktury nawigacji (menu, breadcrumbs, sidebar)';
COMMENT ON TABLE architecture_implementations IS 'Notatki i rekomendacje implementacyjne z priorytetami';

COMMENT ON COLUMN architectures.architecture_type IS 'silo = rygorystyczne bez cross-links, clusters = elastyczne z strategic bridges';
COMMENT ON COLUMN architectures.seo_score IS 'Automatyczny wynik SEO (0-100) na podstawie best practices';
COMMENT ON COLUMN architecture_pages.page_type IS 'pillar, category, subcategory, cluster_page';
COMMENT ON COLUMN architecture_pages.business_intent IS 'informational, commercial, local, transactional dla content strategy';
COMMENT ON COLUMN architecture_links.link_type IS 'upward_category, upward_pillar, strategic_bridge';
COMMENT ON COLUMN architecture_links.similarity_score IS 'Cosine similarity z embeddingów (0.0-1.0) dla strategic bridges';
COMMENT ON COLUMN architecture_links.priority IS '1=high (vertical), 2=medium (bridges), 3=low';

-- =====================================================
-- ZAPYTANIA TESTOWE
-- =====================================================

-- Test istnienia tabel
SELECT 
    schemaname,
    tablename,
    tableowner
FROM pg_tables 
WHERE tablename LIKE 'architecture%'
ORDER BY tablename;

-- Test foreign keys
SELECT 
    tc.table_name, 
    kcu.column_name, 
    ccu.table_name AS foreign_table_name,
    ccu.column_name AS foreign_column_name 
FROM 
    information_schema.table_constraints AS tc 
    JOIN information_schema.key_column_usage AS kcu
      ON tc.constraint_name = kcu.constraint_name
    JOIN information_schema.constraint_column_usage AS ccu
      ON ccu.constraint_name = tc.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY' 
    AND tc.table_name LIKE 'architecture%'
ORDER BY tc.table_name, kcu.column_name;

-- Test views
SELECT count(*) as architecture_summary_count FROM architecture_summary;
SELECT count(*) as page_hierarchy_count FROM architecture_page_hierarchy; 