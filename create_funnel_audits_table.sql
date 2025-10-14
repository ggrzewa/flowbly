-- TABELA FUNNEL AUDITS dla inteligentnego systemu audytu lejka sprzedażowego
-- Module 3: Architecture Generator - Universal Funnel Assessment

CREATE TABLE funnel_audits (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    architecture_id UUID REFERENCES architectures(id),
    seed_keyword TEXT NOT NULL,
    should_optimize_for_funnel BOOLEAN NOT NULL,
    reasoning TEXT,
    commercial_potential TEXT,
    user_journey_exists BOOLEAN,
    funnel_stages_identified JSONB,
    suggested_approach TEXT,
    confidence_score DECIMAL(3,2),
    funnel_suggestions JSONB,
    ai_processing_time DECIMAL(8,3),
    audit_status TEXT DEFAULT 'completed',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- Indeksy dla wydajności
CREATE INDEX idx_funnel_audits_architecture_id ON funnel_audits(architecture_id);
CREATE INDEX idx_funnel_audits_should_optimize ON funnel_audits(should_optimize_for_funnel);
CREATE INDEX idx_funnel_audits_seed_keyword ON funnel_audits(seed_keyword);
CREATE INDEX idx_funnel_audits_created_at ON funnel_audits(created_at);

-- Komentarze do dokumentacji
COMMENT ON TABLE funnel_audits IS 'AI-powered audit results for customer journey optimization potential';
COMMENT ON COLUMN funnel_audits.should_optimize_for_funnel IS 'AI decision whether keyword has customer journey potential';
COMMENT ON COLUMN funnel_audits.commercial_potential IS 'Assessment: high/medium/low/none';
COMMENT ON COLUMN funnel_audits.funnel_stages_identified IS 'Array of identified stages: awareness, consideration, decision';
COMMENT ON COLUMN funnel_audits.suggested_approach IS 'Either customer_psychology_linking or semantic_linking';
COMMENT ON COLUMN funnel_audits.funnel_suggestions IS 'Detailed AI suggestions for funnel optimization'; 