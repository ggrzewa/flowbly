"""
COMPREHENSIVE CONTENT SCAFFOLD GENERATOR - MODULE 5
Generuje mega-szczegółowe scaffoldy wykorzystujące wszystkie dane z M1/M3/M4
Psychology-driven, funnel-optimized, strategically linked content scaffolding
"""

import json
import logging
import os
from typing import Dict, List, Optional, Any
from datetime import datetime
import numpy as np
from openai import OpenAI, AsyncOpenAI
from anthropic import AsyncAnthropic

logger = logging.getLogger(__name__)

class ContentScaffoldGenerator:
    """
    COMPREHENSIVE CONTENT SCAFFOLD GENERATOR - MODULE 5
    
    Generuje ultra-szczegółowe scaffoldy z pełną persistence i strukturą:
    - Ultra-comprehensive context pack z wszystkich modułów (M1/M3/M4)
    - Enforced JSON schema z konkretnymi word counts
    - Psychology reasoning dla każdego strategic link
    - Media plan z exact placement i alt-texts
    - TODO gaps dla missing research data
    - UX elements z breadcrumbs i navigation
    - Tone restrictions z readability guidelines
    - Full Supabase persistence z metadata
    """
    
    def __init__(self, supabase_client):
        """Initialize with Supabase client and AI providers"""
        self.supabase = supabase_client
        
        # AI Provider & Models (env-driven) - jak w innych modułach
        self.ai_provider = os.getenv("AI_PROVIDER", "openai").lower()
        self.openai_model = os.getenv("AI_MODEL_OPENAI", "gpt-4o")
        self.claude_model = os.getenv("AI_MODEL_CLAUDE", "claude-sonnet-4-20250514")
        self.gpt5_model = os.getenv("AI_MODEL_GPT5", "gpt-5")
        self.gpt5_reasoning_effort = os.getenv("GPT5_REASONING_EFFORT", "medium")
        self.gpt5_verbosity = os.getenv("GPT5_VERBOSITY", "medium")
        
        # Initialize AI clients
        self._init_ai_clients()
        
        # Ensure content_scaffolds table exists
        self._ensure_scaffolds_table()
        
        logger.info(f"🧠 [SCAFFOLD] ContentScaffoldGenerator initialized")
        logger.info(f"🔧 [CONFIG] AI_PROVIDER={self.ai_provider}")
        logger.info(f"🔧 [CONFIG] AI_MODEL_OPENAI={self.openai_model}")
        logger.info(f"🔧 [CONFIG] AI_MODEL_CLAUDE={self.claude_model}")
        logger.info(f"🔧 [CONFIG] AI_MODEL_GPT5={self.gpt5_model}")
        logger.info(f"🔧 [CONFIG] GPT5_REASONING_EFFORT={self.gpt5_reasoning_effort}")
    
    def _init_ai_clients(self):
        """Inicjalizuje klientów AI (OpenAI + Claude) - jak w innych modułach"""
        try:
            # OpenAI client
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.openai_client = AsyncOpenAI(api_key=openai_key)
                logger.info(f"✅ OpenAI client initialized (model={self.openai_model})")
            else:
                self.openai_client = None
                logger.warning("⚠️ OpenAI API key not found")
            
            # Claude client
            claude_key = os.getenv("ANTHROPIC_API_KEY")
            if claude_key:
                self.claude_client = AsyncAnthropic(api_key=claude_key)
                logger.info(f"✅ Claude client initialized (model={self.claude_model})")
            else:
                self.claude_client = None
                logger.warning("⚠️ Claude API key not found")
                
        except Exception as e:
            logger.error(f"❌ AI client initialization failed: {str(e)}")
            self.openai_client = None
            self.claude_client = None
    
    def _ensure_scaffolds_table(self):
        """Ensure content_scaffolds table exists with proper structure"""
        try:
            # Test if table exists by querying it
            test_query = self.supabase.table('content_scaffolds').select('id').limit(1).execute()
            logger.info("✅ [SCAFFOLD] content_scaffolds table exists")
        except Exception as e:
            logger.warning(f"⚠️ [SCAFFOLD] content_scaffolds table may not exist: {e}")
            logger.info("💡 [SCAFFOLD] Create table with: CREATE TABLE content_scaffolds (id UUID PRIMARY KEY DEFAULT gen_random_uuid(), brief_id UUID REFERENCES content_briefs(id), scaffold_data JSONB, word_distribution JSONB, media_plan JSONB, ux_elements JSONB, tone_restrictions JSONB, todo_gaps JSONB, placement_guidance JSONB, total_tokens INTEGER, generation_status VARCHAR DEFAULT 'pending', completeness_score FLOAT, created_at TIMESTAMP DEFAULT NOW(), updated_at TIMESTAMP DEFAULT NOW());")

    async def generate_and_save_scaffold(self, brief_id: str) -> Dict:
        """
        GŁÓWNA METODA - Generuje i zapisuje kompletny scaffold z pełną persistence
        """
        logger.info(f"🎯 [SCAFFOLD] Starting generate_and_save_scaffold for brief: {brief_id}")
        
        try:
            # 1. Ustawy status na 'generating'
            await self._update_scaffold_status(brief_id, 'generating', 0)
            
            # 2. Buduj Context Pack v2 (przycięty, stabilny)
            logger.info(f"🔍 [SCAFFOLD] Building Context Pack v2...")
            context_pack = self.build_context_pack_v2(brief_id)
            context_size = len(json.dumps(context_pack))
            
            # 3. Generuj scaffold v2 (ścisły schema + guard-rails)
            logger.info(f"🧠 [SCAFFOLD] Generating scaffold V2 (strict schema)...")
            scaffold_result = await self.generate_scaffold_v2(context_pack)
            # Global hardening top-level po generacji (gdyby przyszły złe typy)
            if not isinstance(scaffold_result, dict):
                scaffold_result = {"content_sections": []}
            for key in [
                'content_sections','faq_integration_strategy','cta_placement_strategy',
                'media_plan','todo_gaps','placement_guidance'
            ]:
                val = scaffold_result.get(key)
                scaffold_result[key] = val if isinstance(val, list) else []
            for key in ['scaffold_meta','ux','ux_elements','writer_guidance','tone_restrictions']:
                val = scaffold_result.get(key)
                scaffold_result[key] = val if isinstance(val, dict) else {}
            scaffold_result = self._normalize_scaffold_shape(scaffold_result)
            # Sanity: ensure all sections are dicts
            if any(not isinstance(x, dict) for x in scaffold_result.get("content_sections", [])):
                scaffold_result = self._normalize_scaffold_shape(scaffold_result)
                # If still bad, coerce
                coerced = []
                for i, sec in enumerate(scaffold_result.get("content_sections", [])):
                    if isinstance(sec, dict):
                        coerced.append(sec)
                    elif isinstance(sec, str):
                        coerced.append({
                            "h2": sec, "target_word_count": 0, "intro_snippet": "",
                            "why_it_matters": "", "next_step": "", "section_objectives": [],
                            "key_ideas": [], "subsections": [], "questions_to_answer": [],
                            "data_points": [], "suggested_sources": [], "keywords_focus": {},
                            "media_plan": [], "psychology_integration": {}, "strategic_linking": [], "todo_gaps": []
                        })
                    else:
                        coerced.append({
                            "h2": f"Sekcja {i+1}", "target_word_count": 0, "intro_snippet": "",
                            "why_it_matters": "", "next_step": "", "section_objectives": [],
                            "key_ideas": [], "subsections": [], "questions_to_answer": [],
                            "data_points": [], "suggested_sources": [], "keywords_focus": {},
                            "media_plan": [], "psychology_integration": {}, "strategic_linking": [], "todo_gaps": []
                        })
                scaffold_result["content_sections"] = coerced
            scaffold_result = self._hydrate_links_into_sections(scaffold_result, context_pack, per_section_min=2)
            
            # 4. Waliduj i wzbogać scaffold
            validated_scaffold = self._validate_and_enrich_scaffold(scaffold_result, context_pack)
            
            # 4.5. Generuj writer-friendly template
            writer_template = self.generate_writer_friendly_scaffold(validated_scaffold, context_pack)
            validated_scaffold['writer_template'] = writer_template
            
            # 5. Oblicz metadata (doklej context_pack do metadanych do zapisu)
            metadata = self._calculate_scaffold_metadata(validated_scaffold, context_pack, context_size)
            metadata['context_pack_data'] = context_pack
            
            # 6. Zapisz do Supabase
            save_result = await self._save_scaffold_to_database(brief_id, validated_scaffold, metadata)
            
            # 7. Ustaw status na 'completed'
            await self._update_scaffold_status(brief_id, 'completed', metadata['completeness_score'])
            
            logger.info(f"✅ [SCAFFOLD] Scaffold generated and saved: {save_result['scaffold_id']}")
            
            return {
                "success": True,
                "scaffold_id": save_result['scaffold_id'],
                "scaffold_data": validated_scaffold,
                "metadata": metadata,
                "context_pack_size": context_size,
                "database_saved": True
            }
            
        except Exception as e:
            logger.error(f"❌ [SCAFFOLD] Error in generate_and_save_scaffold: {str(e)}")
            await self._update_scaffold_status(brief_id, 'failed', 0, str(e))
            raise

    def get_ultra_comprehensive_context_pack(self, brief_id: str) -> Dict:
        """
        Buduje ultra-kompletny ContextPack z WSZYSTKICH dostępnych danych
        ~20-30KB JSON z pełnym kontekstem
        """
        logger.info(f"🔍 [SCAFFOLD] Building ultra-comprehensive context pack for brief: {brief_id}")
        
        try:
            # 1. Pobierz podstawowe dane briefu
            brief_response = self.supabase.table('content_briefs').select('*').eq('id', brief_id).execute()
            if not brief_response.data:
                raise ValueError(f"Content brief not found: {brief_id}")
            
            brief = brief_response.data[0]
            logger.info(f"📋 [SCAFFOLD] Brief loaded: {brief.get('h1_title', 'Unknown')}")
            
            # 2. Pobierz dane architektury
            architecture_id = brief.get('architecture_id')
            architecture = None
            if architecture_id:
                arch_response = self.supabase.table('architectures').select('*').eq('id', architecture_id).execute()
                if arch_response.data:
                    architecture = arch_response.data[0]
                    logger.info(f"🏗️ [SCAFFOLD] Architecture loaded: {architecture_id}")
            
            # 3. Pobierz semantic cluster
            semantic_cluster = None
            if architecture:
                cluster_id = architecture.get('semantic_cluster_id')
                if cluster_id:
                    cluster_response = self.supabase.table('semantic_clusters').select('*').eq('id', cluster_id).execute()
                    if cluster_response.data:
                        semantic_cluster = cluster_response.data[0]
                        logger.info(f"🧠 [SCAFFOLD] Semantic cluster loaded: {cluster_id}")
            
            # 4. Pobierz linki strategiczne
            strategic_bridges = []
            funnel_links = []
            hierarchy_links = []
            
            if architecture_id:
                links_response = self.supabase.table('architecture_links').select(
                    '*, from_page:architecture_pages!architecture_links_from_page_id_fkey(*), to_page:architecture_pages!architecture_links_to_page_id_fkey(*)'
                ).eq('architecture_id', architecture_id).execute()
                
                if links_response.data:
                    for link in links_response.data:
                        if link.get('link_type') == 'bridge':
                            strategic_bridges.append(link)
                        elif link.get('link_type') == 'funnel':
                            funnel_links.append(link)
                        elif link.get('link_type') == 'hierarchy':
                            hierarchy_links.append(link)
                    
                    logger.info(f"🔗 [SCAFFOLD] Links loaded: {len(strategic_bridges)} bridges, {len(funnel_links)} funnel, {len(hierarchy_links)} hierarchy")
            
            # 5. Pobierz content opportunities
            content_opportunities = []
            if architecture_id:
                try:
                    arch_data = architecture.get('architecture_data', {}) if architecture else {}
                    if isinstance(arch_data, str):
                        arch_data = json.loads(arch_data)
                    content_opportunities = arch_data.get('content_opportunities', [])
                    logger.info(f"💡 [SCAFFOLD] Content opportunities loaded: {len(content_opportunities)}")
                except (json.JSONDecodeError, TypeError):
                    logger.warning("⚠️ [SCAFFOLD] Could not parse content opportunities")
            
            # 6. Parse complex JSON fields
            h2_structure = self._safe_json_parse(brief.get('h2_structure'), [])
            h3_structure = self._safe_json_parse(brief.get('h3_structure'), {})
            keyword_density = self._safe_json_parse(brief.get('keyword_density_targets'), {})
            tone_guidelines = self._safe_json_parse(brief.get('tone_guidelines'), {})
            faq_questions = self._safe_json_parse(brief.get('faq_questions'), [])
            
            logger.info(f"📊 [SCAFFOLD] Parsed data: {len(h2_structure)} H2s, {len(faq_questions)} FAQs")
            
            # MEGA-KOMPLETNY ContextPack
            context_pack = {
                "page_meta": {
                    "page_id": brief.get('page_id'),
                    "brief_id": brief.get('id'),
                    "url_pattern": brief.get('url_pattern'),
                    "h1_title": brief.get('h1_title'),
                    "content_intent": brief.get('content_intent'),
                    "word_count_target": brief.get('word_count_target', 2000),
                    "content_difficulty": brief.get('content_difficulty'),
                    "target_audience": brief.get('target_audience'),
                    "page_type": brief.get('page_type'),
                    "business_objectives": brief.get('business_objectives') or []
                },
                
                "comprehensive_structure": {
                    "h1": brief.get('h1_title'),
                    "h2_structure": h2_structure,
                    "h3_structure": h3_structure,
                    "content_flow_logic": self._analyze_content_flow(h2_structure),
                    "section_word_distribution": self._calculate_section_lengths(h2_structure, brief.get('word_count_target', 2000))
                },
                
                "advanced_keywords": {
                    "primary_keywords": brief.get('primary_keywords') or [],
                    "semantic_keywords": brief.get('semantic_keywords') or [],
                    "related_keywords": brief.get('related_keywords') or [],
                    "cluster_phrases": self._get_cluster_phrases_with_scores(semantic_cluster),
                    "density_targets": keyword_density,
                    "keyword_intent_mapping": self._map_keywords_to_intent(brief.get('primary_keywords', []), brief.get('content_intent')),
                    "competitive_gaps": self._identify_keyword_gaps(semantic_cluster),
                    "semantic_relationships": self._build_semantic_graph(semantic_cluster)
                },
                
                "psychology_intelligence": {
                    "funnel_stage": tone_guidelines.get('funnel_stage', 'awareness'),
                    "customer_mindset": tone_guidelines.get('customer_mindset', ''),
                    "emotional_journey": tone_guidelines.get('emotional_journey', ''),
                    "psychology_triggers_used": tone_guidelines.get('psychology_triggers_used', []),
                    "pain_points_addressed": tone_guidelines.get('pain_points_addressed', []),
                    "psychology_enhanced_tone": tone_guidelines.get('psychology_enhanced_tone', ''),
                    "writer_instructions": tone_guidelines.get('writer_instructions', {}),
                    "cognitive_biases_to_leverage": self._map_triggers_to_biases(tone_guidelines.get('psychology_triggers_used', [])),
                    "emotional_hooks_per_section": self._distribute_emotional_hooks(h2_structure, tone_guidelines),
                    "persuasion_techniques": self._select_persuasion_techniques(brief.get('content_intent'), tone_guidelines.get('funnel_stage'))
                },
                
                "strategic_linking_intelligence": {
                    "bridges": [
                        {
                            "type": "bridge",
                            "anchor": link.get('anchor_text'),
                            "url": self._extract_link_url(link),
                            "placement": link.get('placement'),
                            "similarity": link.get('similarity_score', 0),
                            "rationale": link.get('rationale'),
                            "priority": link.get('priority'),
                            "semantic_relevance": self._calculate_semantic_relevance(link, h2_structure),
                            "optimal_context": self._suggest_link_context(link, brief.get('content_intent'))
                        }
                        for link in strategic_bridges
                    ],
                    "funnel_links": [
                        {
                            "type": "funnel", 
                            "anchor": link.get('anchor_text'),
                            "url": self._extract_link_url(link),
                            "placement": link.get('placement'),
                            "funnel_stage": link.get('funnel_stage'),
                            "rationale": link.get('rationale'),
                            "priority": link.get('priority'),
                            "conversion_value": self._estimate_conversion_value(link),
                            "psychology_angle": self._suggest_psychology_angle_for_link(link, tone_guidelines)
                        }
                        for link in funnel_links
                    ],
                    "hierarchy_links": [
                        {
                            "type": "hierarchy",
                            "anchor": link.get('anchor_text'), 
                            "url": self._extract_link_url(link),
                            "placement": link.get('placement'),
                            "priority": link.get('priority'),
                            "navigation_value": "high",
                            "seo_value": self._calculate_seo_link_value(link)
                        }
                        for link in hierarchy_links
                    ]
                },
                
                "content_opportunities_enhanced": [
                    {
                        "source": opp.get('source'),
                        "question_or_topic": opp.get('question') or opp.get('topic') or opp.get('question_or_topic'),
                        "decision": opp.get('decision'),
                        "priority": opp.get('priority'),
                        "rationale": opp.get('rationale'),
                        "target_section": self._map_opportunity_to_section_advanced(opp, h2_structure),
                        "content_angle": self._suggest_content_angle(opp, brief.get('content_intent')),
                        "psychology_integration": self._map_opportunity_to_psychology(opp, tone_guidelines),
                        "search_volume_potential": self._estimate_opportunity_value(opp),
                        "implementation_guidance": self._provide_implementation_guidance(opp, brief.get('content_intent'))
                    }
                    for opp in content_opportunities
                ],
                
                "faq_intelligence": [
                    {
                        "question": faq.get('question', ''),
                        "priority": faq.get('priority', 'medium'),
                        "source": faq.get('source', ''),
                        "rationale": faq.get('rationale', ''),
                        "psychology_context": faq.get('psychology_context', ''),
                        "target_section": self._map_faq_to_section_advanced(faq, h2_structure),
                        "answer_strategy": self._develop_answer_strategy(faq, brief.get('content_intent')),
                        "keyword_integration": self._suggest_faq_keyword_usage(faq, brief.get('primary_keywords', [])),
                        "linking_opportunities": self._identify_faq_linking_opportunities(faq, strategic_bridges),
                        "schema_markup": self._generate_faq_schema_hint(faq)
                    }
                    for faq in faq_questions
                ]
            }
            
            logger.info(f"✅ [SCAFFOLD] Ultra-comprehensive context pack built: {len(json.dumps(context_pack))} chars")
            return context_pack
            
        except Exception as e:
            logger.error(f"❌ [SCAFFOLD] Error building context pack: {str(e)}")
            raise


    def build_context_pack_v2(self, brief_id: str) -> Dict:
        """Buduje Context Pack v2 (~30KB), tnie listy i usuwa null-e."""
        try:
            base = self.get_ultra_comprehensive_context_pack(brief_id)
        except Exception:
            # EDGE: brak briefu lub danych – zbuduj minimalny kontekst bez fantazji
            return {
                'project': {},
                'page': {
                    'id': None, 'name': None, 'url_path': None, 'page_type': None,
                    'depth_level': None, 'target_keywords': [], 'estimated_content_length': 0,
                    'has_faq_section': False, 'cluster_name': None, 'cluster_phrase_count': 0,
                    'paa_questions': [], 'ai_overview_topics': [], 'breadcrumb_path': [], 'siblings': []
                },
                'brief': {
                    'id': brief_id, 'h1_title': None, 'word_count_target': 0,
                    'content_intent': None, 'content_difficulty': None, 'quality_score': None,
                    'primary_keywords': [], 'related_keywords': [], 'keyword_density_targets': {},
                    'h2_structure': [], 'h3_structure': [], 'tone_guidelines': {},
                    'target_audience': None, 'faq_questions': [], 'cta_recommendations': []
                },
                'links': {'hierarchy': [], 'bridges': [], 'funnel': [], 'instructions': []},
                'navigation': {'main': {}, 'sidebar': {}, 'mobile': {}, 'max_depth': 0},
                'keywords': {'primary': [], 'related': [], 'seed': None},
                'serp': {'results_meta': {}, 'top_competitors': [], 'paa': [], 'related_searches': []},
                'opportunities': [], 'implementation_tips': []
            }
        # Przytnij listy zgodnie ze specyfikacją
        def cut(arr, n):
            try:
                return (arr or [])[:n]
            except Exception:
                return []
        # Project
        project = base.get('project') or {}
        # Page/Brief/Navi/Links/Keywords/SERP/Opportunities/Tips z istniejącego base:
        page_meta = base.get('page_meta') or {}
        brief = {
            'id': page_meta.get('brief_id'),
            'h1_title': page_meta.get('h1_title'),
            'word_count_target': page_meta.get('word_count_target'),
            'content_intent': page_meta.get('content_intent'),
            'content_difficulty': None,
            'quality_score': None,
            'primary_keywords': cut(base.get('advanced_keywords', {}).get('primary_keywords'), 6),
            'related_keywords': cut(base.get('advanced_keywords', {}).get('related_keywords'), 10),
            'keyword_density_targets': base.get('advanced_keywords', {}).get('density_targets'),
            'h2_structure': cut(base.get('comprehensive_structure', {}).get('h2_structure'), 8),
            'h3_structure': cut(list((base.get('comprehensive_structure', {}).get('h3_structure') or {}).values()), 16),
            'tone_guidelines': base.get('psychology_intelligence'),
            'target_audience': page_meta.get('target_audience'),
            'faq_questions': cut(base.get('faq_intelligence'), 6),
            'cta_recommendations': None
        }
        links = base.get('strategic_linking_intelligence', {}) or {}
        navigation = base.get('navigation') or {}
        keywords = {
            'primary': cut(base.get('advanced_keywords', {}).get('primary_keywords'), 6),
            'related': cut(base.get('advanced_keywords', {}).get('related_keywords'), 10),
            'semantic': cut(base.get('advanced_keywords', {}).get('semantic_keywords'), 10),
            'seed': base.get('page_meta', {}).get('seed_keyword')
        }
        serp = base.get('serp') or {}
        ctx = {
            'project': project,
            'page': {
                'id': page_meta.get('page_id'),
                'name': page_meta.get('h1_title'),
                'url_path': page_meta.get('url_pattern'),
                'page_type': page_meta.get('page_type'),
                'depth_level': None,
                'target_keywords': cut(keywords.get('primary'), 8),
                'estimated_content_length': page_meta.get('word_count_target'),
                'has_faq_section': bool(brief['faq_questions']),
                'cluster_name': None,
                'cluster_phrase_count': None,
                'paa_questions': cut([{'question': q.get('question')} for q in (base.get('faq_intelligence') or [])], 6),
                'ai_overview_topics': cut([o.get('question_or_topic') for o in (base.get('content_opportunities_enhanced') or [])], 6),
                'breadcrumb_path': [],
                'siblings': []
            },
            'brief': brief,
            'links': {
                'hierarchy_links': cut(links.get('hierarchy_links') or [], 20),
                'bridges':         cut(links.get('bridges') or [], 8),
                'funnel_links':    cut(links.get('funnel_links') or [], 8),
                'instructions':    cut(base.get('linking_instructions') or [], 10)
            },
            'strategic_linking_intelligence': links,
            # Dodatkowy, kompaktowy maping struktury do wzbogacania sekcji
            'structure_map': {
                'h2_to_h3': (base.get('comprehensive_structure', {}) or {}).get('h3_structure') or {},
                'h2_list': (base.get('comprehensive_structure', {}) or {}).get('h2_structure') or []
            },
            'navigation': {
                'main': navigation.get('main'),
                'sidebar': navigation.get('sidebar'),
                'mobile': navigation.get('mobile'),
                'max_depth': navigation.get('max_depth')
            },
            'keywords': keywords,
            'serp': serp,
            'opportunities': cut(base.get('content_opportunities_enhanced') or [], 12),
            'implementation_tips': cut(base.get('implementation_tips') or [], 8)
        }
        # Usuń None
        def prune(obj):
            if isinstance(obj, dict):
                return {k: prune(v) for k, v in obj.items() if v is not None}
            if isinstance(obj, list):
                return [prune(v) for v in obj if v is not None]
            return obj
        ctx = prune(ctx)
        # Limit rozmiaru: jeśli > 32KB, usuń najmniej krytyczne bloki
        payload = json.dumps(ctx, ensure_ascii=False)
        if len(payload) > 32000:
            ctx.pop('implementation_tips', None)
            ctx['opportunities'] = cut(ctx.get('opportunities') or [], 6)
        # Zawsze zapewnij obecność pustych list dla linków
        ctx.setdefault('links', {})
        for k in ['hierarchy','bridges','funnel','instructions']:
            ctx['links'].setdefault(k, [])
        return ctx

    def _log_ai_interaction(self, context_pack: Dict, system_prompt: str, user_prompt: str, ai_response: str, parsed_result: Dict):
        """Zapisuje szczegółowy log interakcji z AI do pliku na dysku"""
        try:
            import os
            from datetime import datetime
            
            # Dla Railway użyj /tmp, lokalnie użyj bieżącego katalogu
            log_dir = "/tmp" if os.getenv("RAILWAY_ENVIRONMENT") else "."
            if not os.path.exists(log_dir):
                os.makedirs(log_dir)
            
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            log_file = os.path.join(log_dir, f"scaffold_generation_{timestamp}.txt")
            
            with open(log_file, 'w', encoding='utf-8') as f:
                f.write("=" * 80 + "\n")
                f.write("SCAFFOLD GENERATION LOG\n")
                f.write(f"Timestamp: {datetime.now().isoformat()}\n")
                f.write("=" * 80 + "\n\n")
                
                f.write("1. CONTEXT PACK SENT TO AI:\n")
                f.write("-" * 40 + "\n")
                f.write(json.dumps(context_pack, ensure_ascii=False, indent=2))
                f.write("\n\n")
                
                f.write("2. SYSTEM PROMPT SENT TO AI:\n")
                f.write("-" * 40 + "\n")
                f.write(system_prompt)
                f.write("\n\n")
                
                f.write("3. USER PROMPT SENT TO AI:\n")
                f.write("-" * 40 + "\n")
                f.write(user_prompt)
                f.write("\n\n")
                
                f.write("4. RAW AI RESPONSE:\n")
                f.write("-" * 40 + "\n")
                f.write(str(ai_response))
                f.write("\n\n")
                
                f.write("5. PARSED RESULT:\n")
                f.write("-" * 40 + "\n")
                f.write(json.dumps(parsed_result, ensure_ascii=False, indent=2))
                f.write("\n\n")
                
                f.write("6. CONTEXT PACK ANALYSIS:\n")
                f.write("-" * 40 + "\n")
                f.write(f"Brief data keys: {list(context_pack.get('brief', {}).keys())}\n")
                f.write(f"Keywords primary: {len(context_pack.get('keywords', {}).get('primary', []))}\n")
                f.write(f"Keywords semantic: {len(context_pack.get('keywords', {}).get('semantic', []))}\n")
                f.write(f"Opportunities count: {len(context_pack.get('opportunities', []))}\n")
                f.write(f"Links bridges: {len(context_pack.get('links', {}).get('bridges', []))}\n")
                f.write(f"Links funnel: {len(context_pack.get('links', {}).get('funnel_links', []))}\n")
                f.write(f"Strategic linking intelligence keys: {list(context_pack.get('strategic_linking_intelligence', {}).keys())}\n")
                
                # Detailed content opportunities analysis
                if context_pack.get('opportunities'):
                    f.write("\nCONTENT OPPORTUNITIES DETAILS:\n")
                    for i, opp in enumerate(context_pack.get('opportunities', [])[:5]):
                        f.write(f"  {i+1}. {opp.get('question_or_topic', 'N/A')}\n")
                
                # Detailed keywords analysis
                if context_pack.get('keywords', {}).get('primary'):
                    f.write(f"\nPRIMARY KEYWORDS: {context_pack.get('keywords', {}).get('primary', [])}\n")
                if context_pack.get('keywords', {}).get('semantic'):
                    f.write(f"SEMANTIC KEYWORDS (first 10): {context_pack.get('keywords', {}).get('semantic', [])[:10]}\n")
                
                f.write("\n" + "=" * 80 + "\n")
            
            logger.info(f"📝 [LOG] AI interaction logged to: {log_file}")
            
        except Exception as e:
            logger.error(f"❌ [LOG] Failed to write AI interaction log: {str(e)}")

    async def _call_ai_with_provider_fallback(self, system_prompt: str, user_prompt: str) -> str:
        """Wywołuje AI z fallbackiem providerów - jak w innych modułach"""
        
        # Mapa max_tokens dla różnych modeli
        max_tokens_map = {
            # OpenAI
            "gpt-5": 128000,
            "gpt-5-mini": 128000,
            "gpt-5-nano": 128000,
            "gpt-5-chat-latest": 128000,
            "gpt-4o-mini": 16384,
            "gpt-4o": 16384,
            "gpt-3.5-turbo": 4096,
            "gpt-4-turbo": 4096,
            "gpt-4": 32768,
            # Claude (orientacyjne)
            "claude-sonnet-4-20250514": 64000,
        }
        
        async def call_gpt5():
            if not self.openai_client:
                raise RuntimeError("OpenAI client (for GPT-5) unavailable")
            logger.info(f"🤖 [AI] GPT-5 call (model={self.gpt5_model})")
            request_data = {
                "model": self.gpt5_model,
                "input": [{
                    "role": "user",
                    "content": [
                        {"type": "input_text", "text": f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}"}
                    ]
                }],
                "max_output_tokens": max_tokens_map.get(self.gpt5_model, 64000),
                "reasoning": {"effort": self.gpt5_reasoning_effort},
                "text": {"verbosity": self.gpt5_verbosity}
            }
            
            resp = await self.openai_client.responses.create(**request_data)
            
            # DEBUG RESPONSE - jak w content_brief_generator.py
            try:
                logger.info(f"🔍 [GPT5_RESPONSE] Response type: {type(resp)}")
                logger.info(f"🔍 [GPT5_RESPONSE] Response ID: {getattr(resp, 'id', 'No ID')}")
                logger.info(f"🔍 [GPT5_RESPONSE] Model used: {getattr(resp, 'model', 'No model')}")
                logger.info(f"🔍 [GPT5_RESPONSE] Status: {getattr(resp, 'status', 'No status')}")
                logger.info(f"🔍 [GPT5_RESPONSE] Has output_text: {hasattr(resp, 'output_text')}")
                if hasattr(resp, 'output_text'):
                    logger.info(f"🔍 [GPT5_RESPONSE] output_text type: {type(resp.output_text)}")
                    logger.info(f"🔍 [GPT5_RESPONSE] output_text is None: {resp.output_text is None}")
                    if resp.output_text:
                        ot = str(resp.output_text)
                        logger.info(f"🔍 [GPT5_RESPONSE] output_text length: {len(ot)}")
                        logger.info(f"🔍 [GPT5_RESPONSE] output_text first 500 chars: {ot[:500]}")
                logger.info(f"🔍 [GPT5_RESPONSE] Has output: {hasattr(resp, 'output')}")
                if hasattr(resp, 'output'):
                    out = getattr(resp, 'output', None)
                    logger.info(f"🔍 [GPT5_RESPONSE] output type: {type(out)}")
                    if out and len(out) > 0:
                        logger.info(f"🔍 [GPT5_RESPONSE] output[0] type: {type(out[0])}")
                        if hasattr(out[0], 'content'):
                            logger.info(f"🔍 [GPT5_RESPONSE] output[0].content: {out[0].content}")
            except Exception as debug_e:
                logger.error(f"🔍 [GPT5_RESPONSE] Debug error: {debug_e}")
            
            # Ekstrakcja tekstu - jak w content_brief_generator.py
            ai_text = None
            if hasattr(resp, 'output_text') and resp.output_text and str(resp.output_text).strip():
                ai_text = str(resp.output_text)
                logger.info(f"✅ [GPT5_RESPONSE] SUCCESS: Używam output_text, length: {len(ai_text)}")
                logger.info(f"🎉 [GPT5_RESPONSE] First 300 chars: {ai_text[:300]}")
            elif hasattr(resp, 'output') and resp.output and len(resp.output) > 0:
                if hasattr(resp.output[0], 'content') and resp.output[0].content:
                    if len(resp.output[0].content) > 0 and hasattr(resp.output[0].content[0], 'text'):
                        ai_text = resp.output[0].content[0].text
                        logger.info(f"✅ [GPT5_RESPONSE] SUCCESS: Używam output[0].content[0].text, length: {len(ai_text)}")
            
            if not ai_text:
                logger.error(f"❌ [GPT5_RESPONSE] ALL EXTRACTION METHODS FAILED")
                # Fallback jak w content_brief_generator.py
                try:
                    ai_text = str(resp)
                    logger.warning(f"⚠️ [GPT5_RESPONSE] FALLBACK: Używam str(resp), length: {len(ai_text)}")
                except Exception:
                    raise Exception("Cannot extract text from GPT-5 response after all attempts")
            
            return ai_text

        async def call_openai():
            if not self.openai_client:
                raise RuntimeError("OpenAI client unavailable")
            
            # Determine if JSON format is supported
            api_params = {
                "model": self.openai_model,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                "temperature": 0.2,
                "max_tokens": max_tokens_map.get(self.openai_model, 8000)
            }
            
            # Add JSON format for supported models
            if self.openai_model in ["gpt-4o", "gpt-4o-mini", "gpt-3.5-turbo-1106", "gpt-4-1106-preview"]:
                api_params["response_format"] = {"type": "json_object"}
            
            resp = await self.openai_client.chat.completions.create(**api_params)
            return resp.choices[0].message.content

        async def call_claude():
            if not self.claude_client:
                raise RuntimeError("Claude client unavailable")
            
            logger.info(f"🤖 [AI] CLAUDE call (model={self.claude_model})")
            
            # Użyj streaming dla dużych max_tokens (>8000)
            max_tokens = max_tokens_map.get(self.claude_model, 8000)
            use_streaming = max_tokens > 8000
            
            if use_streaming:
                logger.info(f"🔍 [CLAUDE] Using streaming for max_tokens={max_tokens}")
                # Streaming response
                stream = await self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=max_tokens,
                    temperature=0.2,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}],
                    stream=True
                )
                
                # Zbierz całą odpowiedź ze streamu
                response_text = ""
                async for chunk in stream:
                    if chunk.type == "content_block_delta" and hasattr(chunk.delta, 'text'):
                        response_text += chunk.delta.text
                        
            else:
                # Non-streaming response dla mniejszych requestów
                resp = await self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=max_tokens,
                    temperature=0.2,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                response_text = resp.content[0].text
            
            logger.info(f"🔍 [CLAUDE] Raw response length: {len(response_text)}")
            logger.info(f"🔍 [CLAUDE] Raw response preview (first 200 chars): {response_text[:200]}")
            logger.info(f"🔍 [CLAUDE] Raw response ending (last 200 chars): {response_text[-200:]}")
            
            # Wyciągnij JSON z markdown bloku jeśli istnieje
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                if end != -1:
                    response_text = response_text[start:end].strip()
                    logger.info(f"🔍 [CLAUDE] Extracted JSON from markdown block, length: {len(response_text)}")
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                if end != -1:
                    response_text = response_text[start:end].strip()
                    logger.info(f"🔍 [CLAUDE] Extracted content from generic markdown block, length: {len(response_text)}")
            
            logger.info("✅ [AI] CLAUDE odpowiedział")
            return response_text

        # Provider fallback order
        primary = self.ai_provider or 'openai'
        all_providers = ['gpt5', 'openai', 'claude']
        providers_order = [primary] + [p for p in all_providers if p != primary]
        
        for provider in providers_order:
            try:
                if provider == 'gpt5':
                    ai_response = await call_gpt5()
                elif provider == 'openai':
                    ai_response = await call_openai()
                else:
                    ai_response = await call_claude()
                logger.info(f"✅ [AI] {provider.upper()} odpowiedział")
                return ai_response
            except Exception as e:
                logger.warning(f"⚠️ [AI] {provider.upper()} nieudane: {e}")
                continue
        
        raise Exception("Brak odpowiedzi AI po wszystkich fallbackach")

    async def generate_scaffold_v2(self, context_pack_v2: Dict) -> Dict:
        """Wywołuje LLM z PROMPT_SCAFFOLD_V2 i waliduje JSON zgodnie ze schemą."""
        OUTPUT_SCHEMA_V2 = {
            "type": "object",
            "required": [
                "scaffold_meta","content_sections","faq_integration_strategy","cta_placement_strategy",
                "media_plan","todo_gaps","ux","placement_guidance","writer_guidance"
            ],
            "properties": {
                "scaffold_meta": {"type":"object"},
                "content_sections": {
                  "type": "array",
                  "items": {
                    "type": "object",
                    "required": [
                      "h2","target_word_count","intro_snippet","why_it_matters","next_step",
                      "section_objectives","key_ideas","subsections","questions_to_answer",
                      "data_points","suggested_sources","keywords_focus","media_plan",
                      "psychology_integration","strategic_linking","todo_gaps",
                      "ai_answer_target","structural_format","information_gain","trust_signals",
                      "entity_connections","semantic_citation"
                    ],
                    "properties": {
                      "h2": {"type":"string"},
                      "ai_answer_target": {
                        "type": "object",
                        "properties": {
                          "snippet_text": {"type": "string"},
                          "type": {"type": "string", "enum": ["direct_answer", "definition", "step_by_step", "list"]}
                        },
                        "required": ["snippet_text", "type"]
                      },
                      "structural_format": {
                        "type": "object",
                        "properties": {
                          "recommended": {"type": "string"},
                          "columns": {"type": "array", "items": {"type": "string"}}
                        }
                      },
                      "authority_injection": {
                        "type": "object",
                        "properties": {
                          "type": {"type": "string"},
                          "instruction": {"type": "string"},
                          "required_citation": {"type": "string"}
                        }
                      },
                      "information_gain": {
                        "type": "object",
                        "description": "Unique insight not found in SERP competitor analysis",
                        "properties": {
                          "type": {"type": "string", "enum": ["new_data", "contrarian_view", "expert_quote", "case_study"]},
                          "insight": {"type": "string"},
                          "evidence_needed": {"type": "string"}
                        }
                      },
                      "trust_signals": {
                        "type": "array",
                        "items": {"type": "object", "properties": {"source": {"type": "string"}, "reason": {"type": "string"}}},
                        "description": "External credible sources to link to for Trust by Association"
                      },
                      "entity_connections": {
                        "type": "array",
                        "items": {"type": "string"},
                        "description": "List of 3-5 named entities that MUST appear in this section to build semantic density"
                      },
                      "semantic_citation": {
                        "type": "object",
                        "properties": {
                          "source": {"type": "string"},
                          "context_hook": {"type": "string", "description": "How to naturally weave this citation into the narrative"}
                        }
                      },
                      "target_word_count": {"type":"number"},
                      "intro_snippet": {"type":"string"},
                      "why_it_matters": {"type":"string"},
                      "next_step": {"type":"string"},
                      "section_kpis": {"type":"array","items":{"type":"string"}},
                      "expected_user_action": {"type":"string"},
                      "section_objectives": {"type":"array","items":{"type":"string"}},
                      "key_ideas": {
                        "type":"array",
                        "items":{
                          "type":"object",
                          "properties":{
                            "idea":{"type":"string"},
                            "proof_required":{"type":"string"}
                          }
                        }
                      },
                      "subsections": {
                        "type":"array",
                        "items":{
                          "type":"object",
                          "required":["h3","target_word_count","builder_instructions","exact_placement"],
                          "properties":{
                            "h3":{"type":"string"},
                            "target_word_count":{"type":"number"},
                            "builder_instructions":{"type":"string"},
                            "bullets":{"type":"array","items":{"type":"string"}},
                            "bullet_points":{"type":"array","items":{"type":"string"}},
                            "examples":{"type":"array","items":{"type":"string"}},
                            "examples_to_include":{"type":"array","items":{"type":"string"}},
                            "data_points":{"type":"array","items":{"type":"string"}},
                            "data_citations_required":{"type":"array","items":{"type":"string"}},
                            "keywords":{"type":"array","items":{"type":"string"}},
                            "entities_checklist":{"type":"array","items":{"type":"string"}},
                            "exact_placement":{"type":"string"},
                            "link_hooks":{"type":"array","items":{"type":"string"}},
                            "psychology":{"type":"object","properties":{
                              "trigger":{"type":"string"},
                              "reasoning":{"type":"string"}
                            }}
                          }
                        }
                      },
                      "questions_to_answer": {"type":"array","items":{"type":"string"}},
                      "data_points": {"type":"array","items":{"type":"string"}},
                      "suggested_sources": {"type":"array","items":{"type":"string"}},
                      "keywords_focus": {"type":"object"},
                      "media_plan": {"type":"array","items":{"type":"object"}},
                      "psychology_integration": {"type":"object"},
                      "strategic_linking": {
                        "type":"array",
                        "items":{
                          "type":"object",
                          "properties":{
                            "type":{"type":"string"},
                            "anchor":{"type":"string"},
                            "url":{"type":"string"},
                            "placement_section":{"type":"string"},
                            "exact_placement":{"type":"string"},
                            "funnel_stage":{"type":"string"},
                            "priority":{"type":"number"},
                            "confidence":{"type":"number"},
                            "from_h2":{"type":"string"},
                            "from_h3":{"type":"string"},
                            "psychology_reasoning":{"type":"string"}
                          }
                        }
                      },
                      "todo_gaps": {"type":"array","items":{"type":"object"}}
                    }
                  }
                },
                "faq_integration_strategy": {"type":"array","items":{"type":"object","required":["question","target_section","integration_method","exact_placement","psychology_approach"]}},
                "cta_placement_strategy": {"type":"array","items":{"type":"object","required":["cta_text","target_section","exact_placement","psychology_optimization"]}},
                "media_plan": {"type":"array"},
                "todo_gaps": {"type":"array"},
                "ux": {"type":"object"},
                "placement_guidance": {"type":"array"},
                "writer_guidance": {"type":"object"}
            }
        }
        SCAFFOLD_SYSTEM_PROMPT = """Jesteś senior SEO content strategist tworzący wyczerpujące scaffoldy treści adaptowane do specyfiki każdego słowa kluczowego. Użytkownik/writer czytający taki scaffold musi mieć doskonałą orientacje w jaki sposób napisać treść dla tej podstrony. WYkorzsytaj więc najlepiej jak potrafisz dane które ci przekazuje z mojego systemu do stworzenia najlepszego i najbardziej precyzyjnego scaffold na świecie. 

PODSTAWOWA FILOZOFIA:
Każda sekcja MUSI być merytorycznie wyczerpana dla danego tematu. Nie twórz ogólnych instrukcji - analizuj context_pack i dedukuj co konkretnie powinno się znaleźć w treści dla tego specyficznego słowa kluczowego i intencji użytkownika.

ANALIZA I ADAPTACJA DO TEMATU:
- Przeanalizuj cluster_phrases: jakie aspekty tematu są najważniejsze dla tej tematyki
- Oceń psychology_intelligence: na jakim etapie journey jest użytkownik i co go niepokoi
- Wykorzystaj content_opportunities_enhanced: na jakie pytania treść MUSI odpowiedzieć
- Dopasuj word count do głębokości potrzebnej dla danej tematyki (nie mechanicznie)

WYMAGANIA MERYTORYCZNE DLA KAŻDEJ SEKCJI:
Każdy H2 i H3 subsection MUSI zawierać:
- UZASADNIENIE: dlaczego ten aspekt jest kluczowy dla zrozumienia tematu
- KONKRETYZACJĘ: jakie specyficzne elementy z cluster_phrases należy omówić
- ROZWIĄZANIE PROBLEMU: jak ta sekcja adresuje pain_points z psychology_intelligence
- ACTIONABLE VALUE: co czytelnik konkretnie zyska/zrozumie po przeczytaniu
- Wyczerp merytorycznie wszsytko co należy w tej sekcji poruszyc piszać treść. Nei możemy czegoś pominąć. Writer musi wiedzieć, że dajemy mu całkowite wyczerpanei tematu, co pomoże mu napisać potem daną treść na bazie tych wskazówek.

STRATEGICZNE LINKOWANIE - WYKORZYSTANIE WSZYSTKICH ZASOBÓW:
- Każdy link z strategic_linking_intelligence (bridges, funnel_links, hierarchy) ma swój cel
- Anchor teksty MUSZĄ być naturalne, ludzkie dla tematu i uzasadnione rationale
- Psychology reasoning bazuje na customer_mindset - nie wymyślaj powodów

WYCZERPANIE MERYTORYCZNE:
- Evidence points: co konkretnie trzeba sprawdzić żeby sekcja była kompletna
- Research tasks: jakie luki w wiedzy trzeba uzupełnić dla tej specyficznej tematyki
- Questions to answer: wykorzystaj faq_intelligence do określenia czego oczekuje użytkownik

ADAPTACJA WORD COUNT:
Dostosuj proporcje do naturalnych potrzeb tematu z comprehensive_structure:
- Sekcje wprowadzające: tyle ile potrzeba dla zrozumienia podstaw
- Sekcje główne: proporcjonalnie do złożoności aspektów z cluster_phrases
- Sekcje praktyczne: odpowiednio do liczby actionable insights

GEO (GENERATIVE ENGINE OPTIMIZATION) - RANKOWANIE W MODELACH AI:
Twórz treści tak, aby były łatwo cytowane przez ChatGPT, Perplexity i Google SGE. Stosuj rygorystyczne "GEO Protocols":

1. INFORMATION GAIN (Klucz do Perplexity):
   - W polu 'information_gain' MUSISZ zaproponować coś unikalnego, czego nie ma w top 10 SERP (np. nowa statystyka, kontrariańska opinia, rzadki use-case).
   - Nie kopiuj ogólników. Wymuś na writerze dodanie "wartości dodanej".

2. CITATION-READY FORMATS (LLM Candy):
   - W 'ai_answer_target' stwórz definicję idealną dla SGE: "[Pojęcie] to [Kategoria], która [Cechy]."
   - W 'structural_format' wymuś formaty tabelaryczne ("Stat-Block") dla danych technicznych. Modele kochają tabele Markdown.

3. TRUST BY ASSOCIATION (Wiarygodność):
   - W 'trust_signals' wskaż konkretne, zewnętrzne źródła autorytatywne (Raporty Gov, Wikipedia, Nature, Statista), które należy zacytować, aby "pożyczyć" wiarygodność.

4. ENTITY DENSITY:
   - W 'entity_connections' buduj łańcuchy encji (Podmiot -> Relacja -> Obiekt).

POZOSTAŁE POLA:
- AI ANSWER TARGET: Definicja/Snippet "na tacy".
- AUTHORITY INJECTION: Instrukcja użycia autorytetu.
- SEMANTIC CITATION: Jak wpleść cytat w narrację.

PSYCHOLOGY-DRIVEN APPROACH:
- Tone sekcji wynika z funnel_stage: świadomość potrzeb vs gotowość decyzyjna
- Każda sekcja rozwiązuje konkretny pain_point lub rozwija zrozumienie
- Strategic linking prowadzi użytkownika przez logiczny journey

ZAKAZ SZABLONOWOŚCI:
Nie używaj generycznych określeń. Każda instrukcja musi wynikać z analizy danych dla tego konkretnego słowa kluczowego. Jeśli nie ma wystarczających danych w context_pack - dodaj do todo_gaps.

JSON SCHEMA REQUIREMENTS bez zmian, ale treść całkowicie dostosowana do specyfiki tematu z context_pack. Zwracaj wyłącznie poprawny JSON zgodny ze schematem. Return, for each H2, a non-empty 'subsections' array with 3–7 items. Never invent data beyond context_pack; add missing items to 'todo_gaps'."""
        USER_PROMPT_TEMPLATE = """ULTRA-COMPREHENSIVE CONTEXTPACK (JSON poniżej). Zwróć tylko JSON zgodny z podanym SCHEMA.

KONKRETNE WYMAGANIA WYKORZYSTANIA DANYCH:
- Z cluster_phrases wyciągnij 3-5 najważniejszych aspektów tematu dla każdej sekcji
- Z content_opportunities_enhanced użyj konkretnych pytań jako "questions_to_answer"
- Z faq_intelligence zintegruj pytania inline w odpowiednich sekcjach
- Research tasks muszą być specyficzne dla tematu (nie generyczne)
- Evidence points mają zawierać konkretne nazwy, liczby, źródła

PRZYKŁAD DOBREGO RESEARCH TASK:
❌ ZŁE: "Sprawdź dane techniczne"
✅ DOBRE: "Sprawdź DPI sensora HERO 25K w modelu G PRO X SUPERLIGHT (logitech.com/g-pro-x-superlight/specs)"

PRZYKŁAD DOBREGO EVIDENCE POINT:
❌ ZŁE: {{"label": "Specyfikacje produktu"}}
✅ DOBRE: {{"label": "G PRO X SUPERLIGHT: 25,600 DPI, 1ms Lightspeed", "source_hint": "logitech.com/specs"}}

PRZYKŁAD WYKORZYSTANIA CLUSTER_PHRASES:
Jeśli w cluster_phrases jest "myszka logitech g pro wireless", to w sekcji o modelach gamingowych napisz konkretnie o G PRO Wireless, nie ogólnie o "myszkach gamingowych".

PRZYKŁAD WYKORZYSTANIA CONTENT_OPPORTUNITIES:
Jeśli w content_opportunities_enhanced jest pytanie "Jaka jest różnica między G PRO a G PRO X?", to dodaj to jako question_to_answer w odpowiedniej sekcji.

ContextPack:
{context}

SCHEMA ODPOWIEDZI:
{schema}
"""
        # Ustal język: z brief.tone_guidelines lub domyślnie pl-PL
        lang = (
            (context_pack_v2.get('brief', {}).get('tone_guidelines') or {}).get('language')
            or 'pl-PL'
        )
        user_prompt = USER_PROMPT_TEMPLATE.format(
            context=json.dumps(context_pack_v2, ensure_ascii=False),
            schema=json.dumps(OUTPUT_SCHEMA_V2, ensure_ascii=False)
        )
        # Wywołaj AI z fallbackiem providerów - jak w innych modułach
        try:
            ai_response = await self._call_ai_with_provider_fallback(SCAFFOLD_SYSTEM_PROMPT, user_prompt)
            logger.info(f"🔍 [SCAFFOLD] AI response length: {len(ai_response)} chars")
            logger.info(f"🔍 [SCAFFOLD] AI response preview (first 200 chars): {ai_response[:200]}")
            logger.info(f"🔍 [SCAFFOLD] AI response ending (last 200 chars): {ai_response[-200:]}")
            
            # Parsuj odpowiedź - zawsze używaj _best_effort_parse_json dla niezawodności
            data = self._best_effort_parse_json(ai_response)
            logger.info(f"🔍 [SCAFFOLD] Parsed data keys: {list(data.keys()) if isinstance(data, dict) else 'NOT_DICT'}")
            total_tokens = 0  # Będzie ustawione przez _call_ai_with_provider_fallback
            # Twarda normalizacja niezależnie od kształtu
            data = self._normalize_scaffold_shape(data)
            # Wymuś poprawne typy kluczowych pól top-level
            def ensure_list(val):
                return val if isinstance(val, list) else []
            def ensure_dict(val):
                return val if isinstance(val, dict) else {}
            for key in [
                'content_sections','faq_integration_strategy','cta_placement_strategy',
                'media_plan','todo_gaps','placement_guidance'
            ]:
                data[key] = ensure_list(data.get(key))
            for key in ['scaffold_meta','ux','ux_elements','writer_guidance','tone_restrictions']:
                data[key] = ensure_dict(data.get(key))
            
            # Log AI interaction to file
            logger.info(f"🔍 [SCAFFOLD] Logging AI interaction - response length: {len(ai_response) if ai_response else 'None'}")
            self._log_ai_interaction(context_pack_v2, SCAFFOLD_SYSTEM_PROMPT, user_prompt, ai_response, data)
        except Exception as e:
            # Retry with REPAIR_JSON
            logger.warning(f"⚠️ [SCAFFOLD] First attempt failed: {str(e)}, trying repair...")
            bad_response = locals().get('ai_response', '')
            repair = {
                "tool": "REPAIR_JSON",
                "instruction": "Napraw JSON tak, aby był 100% zgodny ze SCHEMA. Zwróć wyłącznie poprawny JSON.",
                "schema": OUTPUT_SCHEMA_V2,
                "bad_json_snippet": bad_response[:8000]
            }
            
            repair_system_prompt = SCAFFOLD_SYSTEM_PROMPT + "\n\nSECOND ATTEMPT - STRICT JSON REPAIR"
            repair_user_prompt = user_prompt + "\n\n" + json.dumps(repair, ensure_ascii=False)
            
            try:
                ai_response = await self._call_ai_with_provider_fallback(repair_system_prompt, repair_user_prompt)
                if isinstance(ai_response, str) and ai_response.strip().startswith('{'):
                    try:
                        data = json.loads(ai_response)
                    except Exception:
                        data = self._best_effort_parse_json(ai_response)
                else:
                    data = self._best_effort_parse_json(ai_response)
                
                total_tokens = 0  # Retry attempt
                data = self._normalize_scaffold_shape(data)
                def ensure_list(val):
                    return val if isinstance(val, list) else []
                def ensure_dict(val):
                    return val if isinstance(val, dict) else {}
                for key in [
                    'content_sections','faq_integration_strategy','cta_placement_strategy',
                    'media_plan','todo_gaps','placement_guidance'
                ]:
                    data[key] = ensure_list(data.get(key))
                for key in ['scaffold_meta','ux','ux_elements','writer_guidance','tone_restrictions']:
                    data[key] = ensure_dict(data.get(key))
                
                # Log AI interaction to file (retry attempt)
                retry_info = f"RETRY ATTEMPT - Original error: {str(e)}\nRepair request: {json.dumps(repair, ensure_ascii=False)}\n\n"
                self._log_ai_interaction(context_pack_v2, repair_system_prompt, repair_user_prompt, ai_response, data)
            except Exception as retry_error:
                logger.error(f"❌ [SCAFFOLD] Retry also failed: {str(retry_error)}")
                raise
        # Prosta walidacja minimalna (pełną jsonschema można dodać później)
        for key in ["summary","sections","links","faq","cta","media_plan","todo_gaps","ux","placement_guidance","metrics","risks"]:
            if key not in data:
                data[key] = [] if key not in ["summary","ux","metrics"] else {}
        # Dołącz meta dla dalszego zapisu
        data.setdefault('_meta', {})
        data['_meta'].update({
            'model_used': f"{self.ai_provider}:{getattr(self, f'{self.ai_provider}_model', 'unknown')}",
            'total_tokens': total_tokens or 0,
            'generation_timestamp': datetime.now().isoformat()
        })
        # Rozszerzenie scaffold_meta o audience_profile z danych demograficznych (fallback)
        sm = data.setdefault('scaffold_meta', {})
        ap = sm.get('audience_profile')
        if not isinstance(ap, dict):
            # wyciągnij z context_pack_v2
            kw = context_pack_v2.get('keywords') or {}
            demo_source = 'keywords.demographics'
            audience_profile = {
                'persona_label': 'general',
                'dominant_gender': 'mixed',
                'top_age_brackets': [],
                'top_regions': [],
                'voice_tips': []
            }
            sm['audience_profile'] = audience_profile
            sm['demographic_basis'] = demo_source
        return data

    # ========================================
    # PERSISTENCE AND DATABASE METHODS
    # ========================================
    
    async def _update_scaffold_status(self, brief_id: str, status: str, completeness_score: float, error_message: str = None):
        """Update scaffold generation status"""
        try:
            update_data = {
                'generation_status': status,
                'updated_at': datetime.now().isoformat()
            }
            
            # Don't include completeness_score as it's a generated column
            if error_message:
                update_data['error_message'] = error_message
            
            # Try to update existing record, or create new one
            existing = self.supabase.table('content_scaffolds').select('id').eq('brief_id', brief_id).execute()
            
            if existing.data:
                # Update existing
                self.supabase.table('content_scaffolds').update(update_data).eq('brief_id', brief_id).execute()
            else:
                # Skip insert for non-completed statuses to avoid constraint violations
                logger.info(f"[SCAFFOLD] No existing row for brief {brief_id}; skip insert on status='{status}'. Will insert on final save.")
                
            logger.info(f"✅ [SCAFFOLD] Status updated: {status}")
            
        except Exception as e:
            logger.warning(f"⚠️ [SCAFFOLD] Could not update status: {e}")

    def _validate_and_enrich_scaffold(self, scaffold_result: Dict, context_pack: Dict) -> Dict:
        """Validate and enrich scaffold with additional data"""
        logger.info("🔍 [SCAFFOLD] Validating and enriching scaffold...")
        
        # Ensure required fields exist + compat normalization
        if not isinstance(scaffold_result, dict):
            scaffold_result = {"content_sections": []}
        if isinstance(scaffold_result.get('summary'), str) or (scaffold_result.get('sections') and not scaffold_result.get('content_sections')):
            scaffold_result = self._normalize_scaffold_shape(scaffold_result)
        if not isinstance(context_pack, dict):
            context_pack = {}
        if 'scaffold_meta' not in scaffold_result:
            scaffold_result['scaffold_meta'] = {}
        # Coerce scaffold_meta to dict if model returned wrong type
        if not isinstance(scaffold_result['scaffold_meta'], dict):
            scaffold_result['scaffold_meta'] = {}
        
        if 'content_sections' not in scaffold_result:
            scaffold_result['content_sections'] = []
        # Coerce every section to a dict with safe defaults
        coerced_sections = []
        for i, sec in enumerate(scaffold_result['content_sections']):
            if isinstance(sec, dict):
                coerced_sections.append(sec)
            elif isinstance(sec, str):
                coerced_sections.append({
                    "h2": sec,
                    "target_word_count": 0,
                    "intro_snippet": "",
                    "why_it_matters": "",
                    "next_step": "",
                    "section_objectives": [],
                    "key_ideas": [],
                    "subsections": [],
                    "questions_to_answer": [],
                    "data_points": [],
                    "suggested_sources": [],
                    "keywords_focus": {},
                    "media_plan": [],
                    "psychology_integration": {},
                    "strategic_linking": [],
                    "todo_gaps": [],
                    "ai_answer_target": {},
                    "structural_format": {},
                    "authority_injection": {},
                    "information_gain": {},
                    "trust_signals": [],
                    "entity_connections": [],
                    "semantic_citation": {}
                })
            else:
                coerced_sections.append({
                    "h2": f"Sekcja {i+1}",
                    "target_word_count": 0,
                    "intro_snippet": "",
                    "why_it_matters": "",
                    "next_step": "",
                    "section_objectives": [],
                    "key_ideas": [],
                    "subsections": [],
                    "questions_to_answer": [],
                    "data_points": [],
                    "suggested_sources": [],
                    "keywords_focus": {},
                    "media_plan": [],
                    "psychology_integration": {},
                    "strategic_linking": [],
                    "todo_gaps": [],
                    "ai_answer_target": {},
                    "structural_format": {},
                    "authority_injection": {},
                    "information_gain": {},
                    "trust_signals": [],
                    "entity_connections": [],
                    "semantic_citation": {}
                })
        scaffold_result['content_sections'] = coerced_sections
        
        # Enrich with context data (defensive logs)
        meta = scaffold_result['scaffold_meta']
        try:
            logger.info(f"[SCAFFOLD] Debug meta before context summary: keys={list(meta.keys())}")
        except Exception:
            pass
        # If meta came as list from model, reset to {}
        if not isinstance(meta, dict):
            meta = {}
            scaffold_result['scaffold_meta'] = meta

        # Per-section hard type coercion to expected shapes
        for sec in scaffold_result['content_sections']:
            if not isinstance(sec.get('section_objectives'), list):
                sec['section_objectives'] = []
            if not isinstance(sec.get('key_ideas'), list):
                sec['key_ideas'] = []
            if not isinstance(sec.get('subsections'), list):
                sec['subsections'] = []
            if not isinstance(sec.get('questions_to_answer'), list):
                sec['questions_to_answer'] = []
            if not isinstance(sec.get('data_points'), list):
                sec['data_points'] = []
            if not isinstance(sec.get('suggested_sources'), list):
                sec['suggested_sources'] = []
            if not isinstance(sec.get('media_plan'), list):
                sec['media_plan'] = []
            if not isinstance(sec.get('strategic_linking'), list):
                sec['strategic_linking'] = []
            if not isinstance(sec.get('todo_gaps'), list):
                sec['todo_gaps'] = []
            if not isinstance(sec.get('keywords_focus'), dict):
                sec['keywords_focus'] = {}
            if not isinstance(sec.get('psychology_integration'), dict):
                sec['psychology_integration'] = {}
            # Scalars
            if not isinstance(sec.get('h2'), str):
                sec['h2'] = str(sec.get('h2') or '')
            try:
                twc = sec.get('target_word_count', 0)
                sec['target_word_count'] = int(twc) if isinstance(twc, (int, float, str)) and str(twc).isdigit() else 0
            except Exception:
                sec['target_word_count'] = 0

            # Normalize keywords_focus structure
            kf = sec.get('keywords_focus') or {}
            if not isinstance(kf, dict):
                kf = {}
            if not isinstance(kf.get('primary'), list):
                kf['primary'] = []
            if not isinstance(kf.get('semantic'), list):
                kf['semantic'] = []
            sec['keywords_focus'] = kf

            # Normalize psychology_integration keys to avoid 'undefined'
            psy = sec.get('psychology_integration') or {}
            if not isinstance(psy, dict):
                psy = {}
            psy.setdefault('primary_trigger', '')
            psy.setdefault('emotional_angle', '')
            psy.setdefault('implementation', '')
            sec['psychology_integration'] = psy

            # Coerce key_ideas entries to dict shape
            normalized_key_ideas = []
            for item in sec.get('key_ideas', []):
                if isinstance(item, dict):
                    idea_text = item.get('idea') or item.get('point') or item.get('text') or item.get('title') or ''
                    if idea_text:
                        normalized_key_ideas.append({
                            'idea': str(idea_text),
                            'placement': item.get('placement') or '',
                            'proof_required': item.get('proof_required') or ''
                        })
                elif isinstance(item, str):
                    text = item.strip()
                    if text:
                        normalized_key_ideas.append({'idea': text, 'placement': '', 'proof_required': ''})
            sec['key_ideas'] = normalized_key_ideas

            # Coerce data_points to dicts with label
            normalized_data_points = []
            for dp in sec.get('data_points', []):
                if isinstance(dp, dict):
                    label = dp.get('label') or dp.get('text') or dp.get('title') or ''
                    if label:
                        normalized_data_points.append({'label': str(label), 'source_hint': dp.get('source_hint') or ''})
                elif isinstance(dp, str):
                    txt = dp.strip()
                    if txt:
                        normalized_data_points.append({'label': txt})
            sec['data_points'] = normalized_data_points

            # Coerce suggested_sources to list of strings
            normalized_sources = []
            for src in sec.get('suggested_sources', []):
                if isinstance(src, str):
                    if src.strip():
                        normalized_sources.append(src.strip())
                elif isinstance(src, dict):
                    # pick any url/name-like field
                    cand = src.get('url') or src.get('domain') or src.get('name')
                    if cand:
                        normalized_sources.append(str(cand))
            sec['suggested_sources'] = normalized_sources

            # Coerce questions_to_answer to list of strings
            normalized_questions = []
            for q in sec.get('questions_to_answer', []):
                if isinstance(q, str):
                    if q.strip():
                        normalized_questions.append(q.strip())
                elif isinstance(q, dict):
                    qt = q.get('question') or q.get('text') or ''
                    if qt:
                        normalized_questions.append(str(qt))
            sec['questions_to_answer'] = normalized_questions
        # Aliasy meta: total_word_count -> target_word_count
        if 'target_word_count' not in meta and 'total_word_count' in meta:
            meta['target_word_count'] = meta.pop('total_word_count')
        brief_obj = context_pack.get('brief')
        if not isinstance(brief_obj, dict):
            brief_obj = {}
        tone = (brief_obj.get('tone_guidelines') or {})
        psy_from_ultra = (context_pack.get('psychology_intelligence') or {})
        if not isinstance(psy_from_ultra, dict):
            psy_from_ultra = {}
        links_ultra = (context_pack.get('strategic_linking_intelligence') or {})
        links_v2 = (context_pack.get('links') or {})
        if not isinstance(links_ultra, dict):
            links_ultra = {}
        if not isinstance(links_v2, dict):
            links_v2 = {}

        psychology_triggers_count = len(psy_from_ultra.get('psychology_triggers_used', [])) or len(tone.get('psychology_triggers_used', []))
        strategic_links_count = (
            len(links_ultra.get('bridges', [])) + len(links_ultra.get('funnel_links', [])) + len(links_ultra.get('hierarchy_links', []))
        ) or (
            len(links_v2.get('bridges', [])) + len(links_v2.get('funnel_links', [])) + len(links_v2.get('hierarchy_links', []))
        )
        content_opps = context_pack.get('content_opportunities_enhanced')
        if not isinstance(content_opps, list):
            content_opps = []
        content_opps_count = len(content_opps) or len(context_pack.get('opportunities', []))
        faq_intel = context_pack.get('faq_intelligence')
        if not isinstance(faq_intel, list):
            faq_intel = []
        faq_count = len(faq_intel) or len((context_pack.get('brief') or {}).get('faq_questions', []))

        meta['context_pack_summary'] = {
            'psychology_triggers': psychology_triggers_count,
            'strategic_links': strategic_links_count,
            'content_opportunities': content_opps_count,
            'faq_questions': faq_count
        }
        
        # Validate word count distribution (używaj target_word_count)
        try:
            tw = meta.get('target_word_count') if isinstance(meta, dict) else None
        except Exception:
            tw = None
        total_words = tw if isinstance(tw, (int, float)) else meta.get('total_word_count', 2000) if isinstance(meta, dict) else 2000
        safe_sections = scaffold_result.get('content_sections', []) if isinstance(scaffold_result.get('content_sections'), list) else []
        section_words = 0
        for sec in safe_sections:
            if isinstance(sec, dict):
                try:
                    section_words += int(sec.get('target_word_count', 0) or 0)
                except Exception:
                    pass
        
        if abs(total_words - section_words) > total_words * 0.2:  # Allow 20% variance
            logger.warning(f"⚠️ [SCAFFOLD] Word count mismatch: total={total_words}, sections={section_words}")
        
        # Enrich sections z danych briefu/klastrów, aby nie były puste
        # 1) Keywords focus uzupełnij semantyką z context_pack
        kw = context_pack.get('keywords') or {}
        kw_primary = kw.get('primary') or []
        kw_semantic = kw.get('semantic') or kw.get('related') or []
        for section in scaffold_result['content_sections']:
            kf = section.get('keywords_focus') or {}
            if not isinstance(kf.get('primary'), list) or len(kf.get('primary', [])) == 0:
                # dobierz 1-2 primary dla sekcji po heurystyce tytułu
                title = (section.get('h2') or '').lower()
                picked = [k for k in kw_primary if isinstance(k, str) and k.lower() in title]
                if not picked:
                    picked = kw_primary[:2]
                kf['primary'] = picked
            if not isinstance(kf.get('semantic'), list) or len(kf.get('semantic', [])) == 0:
                kf['semantic'] = kw_semantic[:5]
            section['keywords_focus'] = kf

        # 2) Key ideas/data points/sources – zasiej minimalny zestaw z bazy, gdy puste
        brief_obj = context_pack.get('brief') or {}
        tg = brief_obj.get('tone_guidelines') or {}
        default_sources = ['stat.gov.pl','gov.pl','wikipedia.org']
        for section in scaffold_result['content_sections']:
            if not section.get('key_ideas'):
                section['key_ideas'] = [{
                    'idea': f"Co czytelnik ma wynieść z sekcji: {section.get('h2','')}?",
                    'placement': 'paragraph 1',
                    'proof_required': '1 wiarygodne źródło'
                }]
            if not section.get('data_points'):
                section['data_points'] = [{'label': 'Statystyka/parametr do weryfikacji', 'source_hint': 'zob. źródła poniżej'}]
            if not section.get('suggested_sources'):
                section['suggested_sources'] = default_sources
            # psychology baseline, gdy puste
            psy = section.get('psychology_integration') or {}
            if not psy.get('primary_trigger'):
                psy['primary_trigger'] = (tg.get('psychology_triggers_used') or ['education'])[0]
            if not psy.get('emotional_angle'):
                psy['emotional_angle'] = tg.get('customer_mindset') or 'curiosity'
            if not psy.get('implementation'):
                psy['implementation'] = 'Wpleć język korzyści i krótkie wskazówki decyzyjne.'
            section['psychology_integration'] = psy
            # Ensure subsections bullet points style
            subs = section.get('subsections') or []
            if isinstance(subs, list):
                for ss in subs:
                    if not isinstance(ss, dict):
                        continue
                    # bullet_points min 3
                    b = ss.get('bullet_points') or ss.get('bullets') or []
                    if not isinstance(b, list):
                        b = []
                    if len(b) < 3:
                        # generuj z builder_instructions lub intro_snippet
                        src = (ss.get('builder_instructions') or section.get('intro_snippet') or '').strip()
                        seeds = [s.strip() for s in src.split('.') if s.strip()][:3]
                        while len(b) < 3 and seeds:
                            b.append(seeds.pop(0))
                        while len(b) < 3:
                            b.append("Dodaj konkret: co, dlaczego, przykład.")
                    ss['bullet_points'] = b[:7]
                    # entities_checklist default
                    ents = ss.get('entities_checklist')
                    if not isinstance(ents, list) or len(ents) == 0:
                        ss['entities_checklist'] = (kw_semantic[:8] or kw_primary[:8])
                    # data_citations_required default
                    dcr = ss.get('data_citations_required')
                    if not isinstance(dcr, list) or len(dcr) == 0:
                        ss['data_citations_required'] = ["Dodaj 1–2 źródła danych", "Zweryfikuj parametry/liczby"]

        # Compute section_readiness_score per section (uwzględnia why_it_matters/next_step)
        for section in scaffold_result['content_sections']:
            # Fallback: section KPIs / expected action
            if not isinstance(section.get('section_kpis'), list) or len(section.get('section_kpis') or []) == 0:
                section['section_kpis'] = ["scroll_depth > 60%", "klik w link wewnętrzny"]
            if not isinstance(section.get('expected_user_action'), str) or not section.get('expected_user_action'):
                section['expected_user_action'] = "przejście do kategorii powiązanej"
            section.setdefault('why_it_matters', '')
            section.setdefault('next_step', '')
            factors = [
                bool(section.get('intro_snippet')),
                bool(section.get('key_ideas')),
                bool(section.get('questions_to_answer')),
                bool(section.get('data_points')),
                bool(section.get('media_plan')),
                bool(section.get('strategic_linking')),
                bool(section.get('keywords_focus')),
                bool(section.get('subsections')),
                bool(section.get('why_it_matters')),
                bool(section.get('next_step')),
            ]
            score = sum(1 for f in factors if f) / len(factors)
            section['section_readiness_score'] = round(score, 2)

        return scaffold_result

    def _calculate_scaffold_metadata(self, scaffold: Dict, context_pack: Dict, context_size: int) -> Dict:
        """Calculate comprehensive metadata for scaffold"""
        
        content_sections = scaffold.get('content_sections', [])
        media_plan = scaffold.get('media_plan', [])
        todo_gaps = scaffold.get('todo_gaps', [])
        
        # Calculate completeness score
        completeness_factors = {
            'has_sections': len(content_sections) > 0,
            'has_word_counts': all(s.get('target_word_count', 0) > 0 for s in content_sections),
            'has_psychology': any(s.get('psychology_integration') for s in content_sections),
            'has_strategic_links': any(s.get('strategic_linking') for s in content_sections),
            'has_media_plan': len(media_plan) > 0,
            'has_todo_gaps': len(todo_gaps) > 0,
            'has_ux_elements': 'ux_elements' in scaffold,
            'has_tone_restrictions': 'tone_restrictions' in scaffold
        }
        
        completeness_score = sum(completeness_factors.values()) / len(completeness_factors)
        
        # Psychology triggers list (unique)
        psychology_triggers = []
        for section in content_sections:
            psy = section.get('psychology_integration') or {}
            trigger = psy.get('primary_trigger')
            if trigger and trigger not in psychology_triggers:
                psychology_triggers.append(trigger)
        
        # Strategic links count
        strategic_links_count = 0
        for section in content_sections:
            links = section.get('strategic_linking') or []
            if isinstance(links, list):
                strategic_links_count += len(links)
        
        return {
            'completeness_score': completeness_score,
            'total_sections': len(content_sections),
            'total_words_planned': sum(s.get('target_word_count', 0) for s in content_sections),
            'media_elements': len(media_plan),
            'todo_items': len(todo_gaps),
            'context_pack_size': context_size,
            'generation_timestamp': datetime.now().isoformat(),
            'psychology_integration': completeness_factors['has_psychology'],
            'strategic_linking': completeness_factors['has_strategic_links'],
            'psychology_applied': psychology_triggers,
            'strategic_links_count': strategic_links_count
        }

    async def _save_scaffold_to_database(self, brief_id: str, scaffold_data: Dict, metadata: Dict) -> Dict:
        """Save complete scaffold to Supabase with proper structure"""
        logger.info(f"💾 [SCAFFOLD] Saving scaffold to database...")
        
        try:
            # Extract specific components for separate JSONB columns
            # Obsługa word_distribution: preferuj v2 'sections' → derive przybliżone długości
            if scaffold_data.get('sections'):
                sections_v2 = scaffold_data['sections']
                per_section = {}
                total_words = scaffold_data.get('summary', {}).get('word_count', 0) or metadata.get('total_words_planned', 0)
                if total_words and len(sections_v2) > 0:
                    even = max(1, int(total_words / len(sections_v2)))
                else:
                    even = 0
                for i, s in enumerate(sections_v2):
                    title = s.get('title') or f'section_{i+1}'
                    per_section[title] = even
                word_distribution = per_section
            else:
                word_distribution = {
                    section.get('h2', f'section_{i}'): section.get('target_word_count', 0) 
                    for i, section in enumerate(scaffold_data.get('content_sections', []))
                }
            
            media_plan = scaffold_data.get('media_plan', [])
            ux_elements = scaffold_data.get('ux', scaffold_data.get('ux_elements', {}))
            tone_restrictions = scaffold_data.get('tone_restrictions', {})
            todo_gaps = scaffold_data.get('todo_gaps', [])
            placement_guidance = scaffold_data.get('placement_guidance', [])
            
            # Prepare generation metadata
            scaffold_meta = scaffold_data.get('_meta', {})
            generation_metadata = {
                'model_used': scaffold_meta.get('model_used', f"{self.ai_provider}:{getattr(self, f'{self.ai_provider}_model', 'unknown')}"),
                'total_tokens': scaffold_meta.get('total_tokens', 0),
                'generation_timestamp': scaffold_meta.get('generation_timestamp', datetime.now().isoformat()),
                'completeness_score': metadata.get('completeness_score', 0.0),
                'context_pack_size': metadata.get('context_pack_size', 0),
                'processing_time': metadata.get('processing_time'),
                'total_sections': metadata.get('total_sections', 0),
                'total_words_planned': metadata.get('total_words_planned', 0),
                'media_elements': metadata.get('media_elements', 0),
                'todo_items': metadata.get('todo_items', 0),
                'psychology_integration': metadata.get('psychology_integration', False),
                'strategic_linking': metadata.get('strategic_linking', False)
            }
            
            # Prepare database record
            db_record = {
                'brief_id': brief_id,
                'scaffold_data': scaffold_data,  # Complete scaffold in main JSONB
                'ai_model_used': scaffold_meta.get('model_used', f"{self.ai_provider}:{getattr(self, f'{self.ai_provider}_model', 'unknown')}"),  # Required NOT NULL field
                'word_distribution': word_distribution,
                'media_plan': media_plan,
                'ux_elements': ux_elements,
                'tone_restrictions': tone_restrictions,
                'todo_gaps': todo_gaps,
                'placement_guidance': placement_guidance,
                'context_pack_data': metadata.get('context_pack_data'),
                'generation_metadata': generation_metadata,  # Required NOT NULL field
                'total_tokens': scaffold_data.get('_meta', {}).get('total_tokens', 0),
                'generation_status': 'completed',
                # completeness_score is a generated column, don't include it
                'created_at': datetime.now().isoformat(),
                'updated_at': datetime.now().isoformat()
            }
            
            # Insert into database
            result = self.supabase.table('content_scaffolds').insert(db_record).execute()
            
            if result.data:
                scaffold_id = result.data[0]['id']
                logger.info(f"✅ [SCAFFOLD] Saved to database: {scaffold_id}")
                return {'scaffold_id': scaffold_id, 'success': True}
            else:
                raise Exception("No data returned from insert")
                
        except Exception as e:
            logger.error(f"❌ [SCAFFOLD] Database save failed: {str(e)}")
            raise

    async def get_scaffold_by_brief_id(self, brief_id: str) -> Optional[Dict]:
        """Get latest scaffold for brief ID"""
        try:
            result = self.supabase.table('content_scaffolds').select('*').eq('brief_id', brief_id).order('created_at', desc=True).limit(1).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ [SCAFFOLD] Error fetching scaffold: {str(e)}")
            return None

    async def get_scaffold_by_id(self, scaffold_id: str) -> Optional[Dict]:
        """Get scaffold by ID"""
        try:
            result = self.supabase.table('content_scaffolds').select('*').eq('id', scaffold_id).execute()
            
            if result.data:
                return result.data[0]
            return None
            
        except Exception as e:
            logger.error(f"❌ [SCAFFOLD] Error fetching scaffold by ID: {str(e)}")
            return None

    # ========================================
    # HELPER METHODS
    # ========================================
    
    def _safe_json_parse(self, data: Any, default: Any) -> Any:
        """Safely parse JSON data"""
        if data is None:
            return default
        if isinstance(data, str):
            try:
                return json.loads(data)
            except json.JSONDecodeError:
                return default
        return data

    def _best_effort_parse_json(self, txt: Any) -> Dict:
        """Wyciąga pierwszy kompletny obiekt JSON z tekstu, uwzględniając cudzysłowy/escape."""
        if not isinstance(txt, str):
            return {}
        
        # Usuń markdown bloki jeśli istnieją
        clean_txt = txt
        if "```json" in clean_txt:
            start = clean_txt.find("```json") + 7
            end = clean_txt.find("```", start)
            if end != -1:
                clean_txt = clean_txt[start:end].strip()
        elif "```" in clean_txt:
            start = clean_txt.find("```") + 3
            end = clean_txt.find("```", start)
            if end != -1:
                clean_txt = clean_txt[start:end].strip()
        
        # Znajdź pierwszy i ostatni nawias klamrowy
        start = clean_txt.find('{')
        if start == -1:
            return {}
            
        # Spróbuj różnych końcówek JSON
        attempts = []
        
        # 1. Znajdź ostatni kompletny nawias
        depth = 0
        in_str = False
        escape = False
        end = -1
        for i in range(start, len(clean_txt)):
            ch = clean_txt[i]
            if in_str:
                if escape:
                    escape = False
                elif ch == '\\':
                    escape = True
                elif ch == '"':
                    in_str = False
                continue
            else:
                if ch == '"':
                    in_str = True
                    continue
                if ch == '{':
                    depth += 1
                elif ch == '}':
                    depth -= 1
                    if depth == 0:
                        end = i
                        break
        
        if end != -1:
            attempts.append(clean_txt[start:end+1])
        
        # 2. Znajdź ostatni nawias w ogóle
        last_brace = clean_txt.rfind('}')
        if last_brace != -1:
            attempts.append(clean_txt[start:last_brace+1])
        
        # 3. Próba naprawy niekompletnego JSON-a
        if not attempts:
            # Jeśli nie ma zamykającego nawiasu, spróbuj dodać
            attempts.append(clean_txt[start:] + '}')
        
        # Spróbuj każdą wersję
        for attempt in attempts:
            try:
                parsed = json.loads(attempt)
                logger.info(f"✅ [SCAFFOLD] Successfully parsed JSON with {len(str(parsed))} chars")
                return parsed
            except json.JSONDecodeError as e:
                logger.warning(f"⚠️ [SCAFFOLD] JSON parse attempt failed: {str(e)[:100]}")
                continue
        
        logger.error(f"❌ [SCAFFOLD] All JSON parse attempts failed for text: {clean_txt[:200]}...")
        return {}

    def _analyze_content_flow(self, h2_structure: List[str]) -> Dict:
        """Analyze logical flow of content sections"""
        return {
            "sections_count": len(h2_structure),
            "flow_type": "educational" if len(h2_structure) > 5 else "concise",
            "logical_progression": "problem->solution->implementation" if len(h2_structure) >= 3 else "simple"
        }

    def _calculate_section_lengths(self, h2_structure: List[str], total_words: int) -> Dict:
        """Calculate word distribution across sections"""
        if not h2_structure:
            return {}
        
        section_count = len(h2_structure)
        base_words = total_words // section_count
        
        return {section: base_words for section in h2_structure}

    def generate_writer_friendly_scaffold(self, scaffold_data: Dict, context_pack: Dict) -> str:
        """
        Generuje writer-friendly markdown template z JSON scaffold data
        """
        try:
            # Extract basic info
            scaffold_meta = scaffold_data.get('scaffold_meta', {})
            content_sections = scaffold_data.get('content_sections', [])
            faq_strategy = scaffold_data.get('faq_integration_strategy', [])
            cta_strategy = scaffold_data.get('cta_placement_strategy', [])
            media_plan = scaffold_data.get('media_plan', [])
            todo_gaps = scaffold_data.get('todo_gaps', [])
            
            # Template variables
            article_title = scaffold_meta.get('h1_title', 'Artykuł')
            total_words = scaffold_meta.get('target_word_count', 2000)
            reading_time = max(1, total_words // 250)
            funnel_stage = scaffold_meta.get('funnel_stage', 'awareness').title()
            
            # Build template
            template = f"""📝 CONTENT SCAFFOLD - WRITER VIEW
Artykuł: {article_title}
Cel: {scaffold_meta.get('main_goal', 'Dostarczenie wartościowej treści dla czytelnika')}
Długość: {total_words} słów | Czas czytania: ~{reading_time} minut
Stage: {funnel_stage}

🎯 CO OSIĄGNĄĆ W TYM ARTYKULE
Czytelnik po przeczytaniu:

{self._generate_user_outcomes(scaffold_meta, content_sections)}

📖 STRUKTURA ARTYKUŁU
{self._generate_sections_structure(content_sections, total_words)}

❓ FAQ INTEGRATION STRATEGY
{self._generate_faq_strategy(faq_strategy, content_sections)}

⚡ QUICK ACTIONS - CO ZROBIĆ NAJPIERW
🔍 RESEARCH NEEDED (zrób przed pisaniem):

HIGH PRIORITY:
{self._generate_research_tasks(todo_gaps, 'high')}

MEDIUM PRIORITY:
{self._generate_research_tasks(todo_gaps, 'medium')}

📝 WRITING TIPS:
{self._generate_writing_tips(scaffold_meta)}

🔗 CTA PLACEMENT:
{self._generate_cta_placement(cta_strategy)}

📊 SUCCESS METRICS
{self._generate_success_metrics(scaffold_meta)}

🎨 MULTIMEDIA PLAN
{self._generate_media_plan(media_plan)}

✅ CHECKLIST PRZED PUBLIKACJĄ
{self._generate_checklist(scaffold_meta)}

🛡️ LIVE VALIDATION & QUALITY CONTROL
📏 WORD COUNT TRACKER: 0/{total_words} słów ({0:.1f}%)
🎯 KEYWORD DENSITY MONITOR: Sprawdź gęstość głównych słów kluczowych
🔗 LINK PLACEMENT VALIDATOR: {self._count_strategic_links(content_sections)} linków strategicznych zaplanowanych
❓ FAQ PLACEMENT CHECK: {len(faq_strategy)} FAQ do umieszczenia inline
"""
            
            return template
            
        except Exception as e:
            logger.error(f"❌ [SCAFFOLD] Error generating writer template: {str(e)}")
            return f"❌ Błąd generowania writer template: {str(e)}"
    
    def _generate_user_outcomes(self, scaffold_meta: Dict, sections: List[Dict]) -> str:
        """Generate user outcomes list"""
        outcomes = []
        
        # Extract from scaffold_meta or generate based on sections
        if scaffold_meta.get('user_outcomes'):
            for outcome in scaffold_meta['user_outcomes'][:4]:
                outcomes.append(f"✅ {outcome}")
        else:
            # Generate based on sections
            for i, section in enumerate(sections[:4]):
                h2 = section.get('h2', f'Sekcja {i+1}')
                outcome = f"Zrozumie {h2.lower()}"
                outcomes.append(f"✅ {outcome}")
        
        return '\n'.join(outcomes) if outcomes else "✅ Zdobędzie praktyczną wiedzę z tematu"
    
    def _generate_sections_structure(self, sections: List[Dict], total_words: int) -> str:
        """Generate sections structure with 7-point system"""
        if not sections:
            return "Brak sekcji do wygenerowania"
        
        section_word_count = total_words // len(sections)
        structure = []
        
        for i, section in enumerate(sections, 1):
            h2 = section.get('h2', f'Sekcja {i}')
            subsections = section.get('subsections', [])
            strategic_links = section.get('strategic_linking', [])
            
            section_template = f"""🔹 SEKCJA {i}: {h2}
📏 Target: {section_word_count} słów | ✅ Status: 0/{section_word_count} | 🎯 Keyword density: 0%

1. CEL SEKCJI
{section.get('why_it_matters', 'Przekazanie kluczowych informacji czytelnikowi')}

2. EFEKT U CZYTELNIKA
{section.get('next_step', 'Czytelnik będzie wiedział więcej o temacie')}

3. OUTLINE SEKCJI
{self._generate_subsection_outline(subsections, section_word_count)}

4. EVIDENCE DO ZDOBYCIA
{self._generate_evidence_points(section)}

5. LINKI STRATEGICZNE
{self._generate_strategic_links_format(strategic_links)}

6. DO SPRAWDZENIA (przed pisaniem)
{self._generate_section_research_tasks(section)}

7. KPI SEKCJI
Scroll rate: >60% czytelników przechodzi do następnej sekcji
Time on section: >{max(30, section_word_count//10)} sekund średnio
Link clicks: >15% kliknie w linki strategiczne

"""
            structure.append(section_template)
        
        return '\n'.join(structure)
    
    def _generate_subsection_outline(self, subsections: List[Dict], total_words: int) -> str:
        """Generate subsection outline"""
        if not subsections:
            return "Paragraph 1: Wprowadzenie do tematu (100 słów)\nParagraph 2: Główne punkty (150 słów)\nParagraph 3: Podsumowanie i wnioski (100 słów)"
        
        outline = []
        words_per_subsection = total_words // max(1, len(subsections))
        
        for i, sub in enumerate(subsections, 1):
            h3 = sub.get('h3', f'Podsekcja {i}')
            bullets = sub.get('bullet_points', [])
            bullet_preview = f" - {bullets[0]}" if bullets else ""
            outline.append(f"Paragraph {i}: {h3} ({words_per_subsection} słów){bullet_preview}")
        
        return '\n'.join(outline)
    
    def _generate_evidence_points(self, section: Dict) -> str:
        """Generate evidence points to gather"""
        evidence = []
        
        # From data_points if available
        data_points = section.get('data_points', [])
        for point in data_points[:3]:
            evidence.append(f"✅ {point} (sprawdź oficjalne źródła)")
        
        # From entities_checklist in subsections
        subsections = section.get('subsections', [])
        for sub in subsections[:2]:
            entities = sub.get('entities_checklist', [])
            if entities:
                evidence.append(f"⚠️ Zweryfikuj dane o: {', '.join(entities[:2])}")
        
        if not evidence:
            evidence = [
                "✅ Aktualne dane statystyczne",
                "✅ Przykłady z praktyki", 
                "⚠️ Opinie ekspertów"
            ]
        
        return '\n'.join(evidence)
    
    def _generate_strategic_links_format(self, links: List[Dict]) -> str:
        """Generate strategic links in writer-friendly format"""
        if not links:
            return "Brak linków strategicznych zaplanowanych"
        
        formatted_links = []
        for i, link in enumerate(links[:3], 1):  # Limit to 3 most important
            anchor = link.get('anchor', 'link text')
            url = link.get('url', '/path/')
            placement = link.get('exact_placement', 'content_mid')
            reasoning = link.get('psychology_reasoning', 'Wspiera user journey')
            
            link_template = f"""**Link {i}:**
- **Anchor:** "{anchor}"
- **URL:** `{url}`
- **Placement:** {placement}
- **Uzasadnienie:** {reasoning}"""
            
            formatted_links.append(link_template)
        
        return '\n\n'.join(formatted_links)
    
    def _generate_section_research_tasks(self, section: Dict) -> str:
        """Generate research tasks for section"""
        tasks = []
        
        # From subsections data_citations_required
        subsections = section.get('subsections', [])
        for sub in subsections:
            citations = sub.get('data_citations_required', [])
            for citation in citations[:2]:
                tasks.append(f"- [ ] **HIGH:** {citation}")
        
        # From suggested_sources
        sources = section.get('suggested_sources', [])
        for source in sources[:2]:
            tasks.append(f"- [ ] **MEDIUM:** Sprawdź {source}")
        
        if not tasks:
            tasks = [
                "- [ ] **HIGH:** Zweryfikuj kluczowe dane",
                "- [ ] **MEDIUM:** Znajdź aktualne przykłady"
            ]
        
        return '\n'.join(tasks)
    
    def _generate_faq_strategy(self, faq_strategy: List[Dict], sections: List[Dict]) -> str:
        """Generate FAQ integration strategy"""
        if not faq_strategy:
            return "Brak FAQ zaplanowanych"
        
        faq_formatted = []
        for i, faq in enumerate(faq_strategy[:3], 1):
            question = faq.get('question', f'Pytanie {i}')
            answer = faq.get('answer_framework', 'Odpowiedź do opracowania')
            target_section = faq.get('target_section', 'Sekcja 1')
            placement = faq.get('exact_placement', 'Po pierwszym paragrafie')
            
            faq_template = f"""FAQ {i}: "{question}"

Target Section: {target_section}
Integration: Inline
Exact Placement: {placement}
Answer Framework: "{answer[:100]}..."
Psychology: Odpowiada na główne obawy czytelnika"""
            
            faq_formatted.append(faq_template)
        
        return '\n\n'.join(faq_formatted)
    
    def _generate_research_tasks(self, todo_gaps: List[Dict], priority: str) -> str:
        """Generate research tasks by priority"""
        tasks = []
        
        for todo in todo_gaps:
            if isinstance(todo, dict) and todo.get('priority', '').lower() == priority:
                task = todo.get('task', todo.get('description', 'Zadanie do wykonania'))
                tasks.append(f"- {task}")
        
        if not tasks:
            if priority == 'high':
                tasks = ["- Sprawdź aktualne dane i statystyki", "- Zweryfikuj kluczowe informacje"]
            else:
                tasks = ["- Znajdź dodatkowe przykłady", "- Sprawdź konkurencję"]
        
        return '\n'.join(tasks)
    
    def _generate_writing_tips(self, scaffold_meta: Dict) -> str:
        """Generate writing tips"""
        tone = scaffold_meta.get('tone', 'profesjonalny, pomocny')
        return f"""Ton: {tone}
Unikaj: "Najlepszy", "Gwarantujemy", "Musisz"
Używaj: "Warto rozważyć", "Eksperci zalecają", "Według badań" """
    
    def _generate_cta_placement(self, cta_strategy: List[Dict]) -> str:
        """Generate CTA placement guide"""
        if not cta_strategy:
            return "Po ostatniej sekcji: \"Dowiedz się więcej\""
        
        placements = []
        for cta in cta_strategy[:3]:
            section = cta.get('target_section', 'Koniec artykułu')
            text = cta.get('cta_text', 'Dowiedz się więcej')
            placements.append(f"Po {section}: \"{text}\"")
        
        return '\n'.join(placements)
    
    def _generate_success_metrics(self, scaffold_meta: Dict) -> str:
        """Generate success metrics"""
        return """Cel minimum:
- Czas na stronie: >4 minuty
- Scroll depth: >70%
- Kliknięcia w linki wewnętrzne: >15%

Cel idealny:
- Zapytania o usługi: >5 tygodniowo
- Udostępnienia: >10 miesięcznie"""
    
    def _generate_media_plan(self, media_plan: List[Dict]) -> str:
        """Generate multimedia plan"""
        if not media_plan:
            return "Zdjęcie główne: Ilustracja tematu (za H1)"
        
        media_items = []
        for media in media_plan[:5]:
            media_type = media.get('type', 'IMAGE').title()
            placement = media.get('placement', 'content_mid')
            caption = media.get('caption', 'Opis do dodania')
            media_items.append(f"{media_type}: {caption} ({placement})")
        
        return '\n'.join(media_items)
    
    def _generate_checklist(self, scaffold_meta: Dict) -> str:
        """Generate pre-publication checklist"""
        primary_keyword = scaffold_meta.get('primary_keyword', 'główne słowo kluczowe')
        
        return f"""SEO:
- [ ] H1 zawiera "{primary_keyword}"
- [ ] H2/H3 używają słów kluczowych naturalnie
- [ ] Meta description max 155 znaków
- [ ] Alt text dla wszystkich zdjęć

UX:
- [ ] Akapity max 4 zdania
- [ ] Listy punktowane gdzie to możliwe
- [ ] Jasne przejścia między sekcjami
- [ ] TOC na początku artykułu

LEGAL:
- [ ] Disclaimer o cenach (mogą się zmieniać)
- [ ] Link do polityki prywatności
- [ ] Brak gwarancji medycznych"""
    
    def _count_strategic_links(self, sections: List[Dict]) -> int:
        """Count total strategic links"""
        total = 0
        for section in sections:
            links = section.get('strategic_linking', [])
            total += len(links) if isinstance(links, list) else 0
        return total

    def _get_cluster_phrases_with_scores(self, semantic_cluster: Optional[Dict]) -> List[Dict]:
        """Extract cluster phrases with similarity scores"""
        if not semantic_cluster:
            return []
        
        # Mock implementation - would need to fetch from semantic_groups table
        return [
            {"phrase": "example phrase", "similarity": 0.85, "search_volume": 1000}
        ]

    def _map_keywords_to_intent(self, keywords: List[str], content_intent: str) -> Dict:
        """Map keywords to search intent"""
        intent_mapping = {}
        for keyword in keywords:
            if content_intent in ['commercial', 'transactional']:
                intent_mapping[keyword] = "commercial"
            elif content_intent == 'informational':
                intent_mapping[keyword] = "informational"
            else:
                intent_mapping[keyword] = "mixed"
        return intent_mapping

    def _identify_keyword_gaps(self, semantic_cluster: Optional[Dict]) -> List[str]:
        """Identify keyword gaps in cluster"""
        if not semantic_cluster:
            return []
        return ["gap keyword 1", "gap keyword 2"]  # Mock implementation

    def _build_semantic_graph(self, semantic_cluster: Optional[Dict]) -> Dict:
        """Build semantic relationship graph"""
        return {
            "core_topics": ["topic 1", "topic 2"],
            "related_concepts": ["concept 1", "concept 2"],
            "semantic_distance": 0.7
        }

    def _map_triggers_to_biases(self, triggers: List[str]) -> List[str]:
        """Map psychology triggers to cognitive biases"""
        bias_mapping = {
            "scarcity": "loss_aversion",
            "social_proof": "conformity_bias",
            "authority": "authority_bias",
            "reciprocity": "reciprocity_principle"
        }
        return [bias_mapping.get(trigger, "confirmation_bias") for trigger in triggers]

    def _distribute_emotional_hooks(self, h2_structure: List[str], tone_guidelines: Dict) -> Dict:
        """Distribute emotional hooks across sections"""
        hooks = {}
        emotions = ["curiosity", "urgency", "trust", "satisfaction"]
        
        for i, section in enumerate(h2_structure):
            hooks[section] = emotions[i % len(emotions)]
        
        return hooks

    def _select_persuasion_techniques(self, content_intent: str, funnel_stage: str) -> List[str]:
        """Select appropriate persuasion techniques"""
        techniques = []
        
        if funnel_stage == "awareness":
            techniques.extend(["curiosity", "social_proof"])
        elif funnel_stage == "consideration":
            techniques.extend(["comparison", "authority"])
        elif funnel_stage == "decision":
            techniques.extend(["scarcity", "urgency"])
        
        return techniques

    def _extract_link_url(self, link: Dict) -> str:
        """Extract URL from link object (bezpiecznie dla różnych kształtów)."""
        try:
            if not isinstance(link, dict):
                return link if isinstance(link, str) else '#'
            to_page = link.get('to_page')
            if isinstance(to_page, dict):
                url = to_page.get('url_pattern') or to_page.get('url') or to_page.get('url_path')
                if url:
                    return url
            # Fallbacki na pola linku
            url = link.get('url') or link.get('target_url') or link.get('to_url')
            if not url and isinstance(to_page, str):
                url = to_page
            return url or '#'
        except Exception:
            return '#'

    def _calculate_semantic_relevance(self, link: Dict, h2_structure: List[str]) -> float:
        """Calculate semantic relevance of link to content"""
        return 0.8  # Mock implementation

    def _suggest_link_context(self, link: Dict, content_intent: str) -> str:
        """Suggest optimal context for link placement"""
        return f"Introduce link naturally when discussing {link.get('rationale', 'related topic')}"

    def _estimate_conversion_value(self, link: Dict) -> str:
        """Estimate conversion value of link"""
        priority = link.get('priority', 'medium')
        if priority == 'high':
            return "high"
        elif priority == 'medium':
            return "medium"
        else:
            return "low"

    def _suggest_psychology_angle_for_link(self, link: Dict, tone_guidelines: Dict) -> str:
        """Suggest psychology angle for link"""
        funnel_stage = link.get('funnel_stage', 'awareness')
        if funnel_stage == "decision":
            return "urgency and scarcity"
        elif funnel_stage == "consideration":
            return "authority and social proof"
        else:
            return "curiosity and value"

    def _calculate_seo_link_value(self, link: Dict) -> str:
        """Calculate SEO value of link"""
        return "high" if link.get('priority') == 'high' else "medium"

    def _map_opportunity_to_section_advanced(self, opportunity: Dict, h2_structure: List[str]) -> str:
        """Map content opportunity to specific H2 section"""
        if not h2_structure:
            return "introduction"
        
        # Simple mapping based on opportunity type
        opp_text = opportunity.get('question_or_topic', '').lower()
        
        for section in h2_structure:
            if any(keyword in section.lower() for keyword in opp_text.split()[:3]):
                return section
        
        return h2_structure[0]  # Default to first section

    def _suggest_content_angle(self, opportunity: Dict, content_intent: str) -> str:
        """Suggest content angle for opportunity"""
        if opportunity.get('source') == 'PAA':
            return "direct answer with supporting context"
        elif opportunity.get('source') == 'AI_OVERVIEW':
            return "comprehensive explanation with examples"
        else:
            return "educational approach with practical application"

    def _map_opportunity_to_psychology(self, opportunity: Dict, tone_guidelines: Dict) -> str:
        """Map opportunity to psychology approach"""
        if opportunity.get('priority') == 'high':
            return "authority and expertise demonstration"
        else:
            return "helpful and educational tone"

    def _estimate_opportunity_value(self, opportunity: Dict) -> str:
        """Estimate search volume potential of opportunity"""
        priority = opportunity.get('priority', 'medium')
        return f"{priority} potential"

    def _provide_implementation_guidance(self, opportunity: Dict, content_intent: str) -> str:
        """Provide implementation guidance for opportunity"""
        if opportunity.get('decision') == 'FAQ':
            return "Add as FAQ item with detailed answer"
        elif opportunity.get('decision') == 'NEW_PAGE':
            return "Consider creating dedicated content piece"
        else:
            return "Integrate naturally into existing content"

    def _map_faq_to_section_advanced(self, faq: Dict, h2_structure: List[str]) -> str:
        """Map FAQ to specific section"""
        question = faq.get('question', '').lower()
        
        for section in h2_structure:
            if any(keyword in section.lower() for keyword in question.split()[:3]):
                return section
        
        return "FAQ section"

    def _develop_answer_strategy(self, faq: Dict, content_intent: str) -> str:
        """Develop answer strategy for FAQ"""
        if faq.get('priority') == 'high':
            return "comprehensive answer with examples and supporting evidence"
        else:
            return "concise answer with relevant details"

    def _suggest_faq_keyword_usage(self, faq: Dict, primary_keywords: List[str]) -> List[str]:
        """Suggest keyword usage in FAQ"""
        suggestions = []
        for keyword in primary_keywords[:2]:  # Use top 2 keywords
            suggestions.append(f"Naturally incorporate '{keyword}' in answer")
        return suggestions

    def _identify_faq_linking_opportunities(self, faq: Dict, strategic_bridges: List[Dict]) -> List[str]:
        """Identify linking opportunities in FAQ"""
        opportunities = []
        for bridge in strategic_bridges[:2]:  # Top 2 bridges
            opportunities.append(f"Link to {bridge.get('url', '#')} when relevant")
        return opportunities

    def _generate_faq_schema_hint(self, faq: Dict) -> str:
        """Generate FAQ schema markup hint"""
        return "Add FAQPage schema with question and acceptedAnswer properties"

    def _normalize_scaffold_shape(self, s: Dict) -> Dict:
        """
        Twarda normalizacja wyniku LLM:
        - zawsze zwraca dict z 'content_sections' jako listą DICTrów,
        - stringi/listy w 'sections'/'content_sections' zamienia na pełne obiekty,
        - ustawia aliasy faq/cta, defaulty guidance/ux/media/placement.
        """
        if not isinstance(s, dict):
            return {"summary": {}, "sections": [], "content_sections": []}

        out = dict(s)

        # helper normalizacji H3
        def _norm_h3_list(v):
            out_list = []
            if isinstance(v, list):
                for it in v:
                    if isinstance(it, str):
                        out_list.append({
                            "h3": it,
                            "target_word_count": 0,
                            "builder_instructions": "",
                            "bullets": [],
                            "examples": [],
                            "data_points": [],
                            "keywords": [],
                            "exact_placement": "",
                            "link_hooks": [],
                            "psychology": {"trigger":"", "reasoning":""}
                        })
                    elif isinstance(it, dict):
                        out_list.append({
                            "h3": it.get("h3") or it.get("title") or "",
                            "target_word_count": it.get("target_word_count", 0),
                            "builder_instructions": it.get("builder_instructions",""),
                            "bullets": it.get("bullets",[]) if isinstance(it.get("bullets"), list) else [],
                            "examples": it.get("examples",[]) if isinstance(it.get("examples"), list) else [],
                            "data_points": it.get("data_points",[]) if isinstance(it.get("data_points"), list) else [],
                            "keywords": it.get("keywords",[]) if isinstance(it.get("keywords"), list) else [],
                            "exact_placement": it.get("exact_placement",""),
                            "link_hooks": it.get("link_hooks",[]) if isinstance(it.get("link_hooks"), list) else [],
                            "psychology": it.get("psychology") if isinstance(it.get("psychology"), dict) else {"trigger":"", "reasoning":""}
                        })
            return out_list

        # --- summary ---
        summary = out.get("summary")
        if isinstance(summary, str):
            out["summary"] = {"text": summary}
        elif summary is None:
            out["summary"] = {}

        # --- sections (legacy) -> lista dictów ---
        sections = out.get("sections")
        norm_sections = []
        if isinstance(sections, list):
            for i, sec in enumerate(sections):
                if isinstance(sec, str):
                    norm_sections.append({
                        "title": sec,
                        "target_word_count": 0,
                        "key_ideas": [],
                        "subsections": [],
                        "intro_snippet": "",
                        "why_it_matters": "",
                        "next_step": "",
                        "questions_to_answer": [],
                        "data_points": [],
                        "suggested_sources": [],
                        "keywords_focus": {},
                        "media_plan": [],
                        "psychology_integration": {},
                        "strategic_links": [],
                        "todo_gaps": []
                    })
                elif isinstance(sec, dict):
                    norm_sections.append(sec)
        out["sections"] = norm_sections

        # --- content_sections -> lista dictów (ZAWSZE) ---
        def _sec_defaults(idx: int, title: str = "") -> Dict:
            return {
                "h2": title or f"Sekcja {idx+1}",
                "target_word_count": 0,
                "intro_snippet": "",
                "why_it_matters": "",
                "next_step": "",
                "section_objectives": [],
                "key_ideas": [],
                "subsections": [],
                "questions_to_answer": [],
                "data_points": [],
                "suggested_sources": [],
                "keywords_focus": {},
                "media_plan": [],
                "psychology_integration": {},
                "strategic_linking": [],
                "todo_gaps": []
            }

        cs = out.get("content_sections")
        norm_cs = []

        if isinstance(cs, list) and cs:
            # Mamy content_sections – normalizujemy każdy element
            for i, sec in enumerate(cs):
                if isinstance(sec, dict):
                    kf = sec.get("keywords_focus")
                    if not isinstance(kf, dict):
                        kf = {}
                    norm_cs.append({
                        "h2": sec.get("h2") or sec.get("title") or f"Sekcja {i+1}",
                        "target_word_count": sec.get("target_word_count") or sec.get("words") or 0,
                        "intro_snippet": sec.get("intro_snippet") or sec.get("intro") or "",
                        "why_it_matters": sec.get("why_it_matters") or sec.get("benefit") or "",
                        "next_step": sec.get("next_step") or sec.get("what_next") or "",
                        "section_objectives": sec.get("section_objectives") or sec.get("objectives") or [],
                        "key_ideas": sec.get("key_ideas") or sec.get("key_points") or [],
                        "subsections": _norm_h3_list(sec.get("subsections") or sec.get("h3") or []),
                        "questions_to_answer": sec.get("questions_to_answer") or sec.get("questions") or [],
                        "data_points": sec.get("data_points") or [],
                        "suggested_sources": sec.get("suggested_sources") or sec.get("sources") or [],
                        "keywords_focus": kf,
                        "media_plan": sec.get("media_plan") or [],
                        "psychology_integration": sec.get("psychology_integration") or {},
                        "strategic_linking": sec.get("strategic_linking") or sec.get("strategic_links") or [],
                        "todo_gaps": sec.get("todo_gaps") or []
                    })
                elif isinstance(sec, str):
                    norm_cs.append(_sec_defaults(i, sec))
                else:
                    norm_cs.append(_sec_defaults(i))
            out["content_sections"] = norm_cs
        else:
            # Brak/nieprawidłowe content_sections -> odbuduj z legacy sections
            out["content_sections"] = []
            for i, sec in enumerate(out.get("sections", [])):
                title = (sec.get("title") if isinstance(sec, dict) else None) or f"Sekcja {i+1}"
                base = _sec_defaults(i, title)
                if isinstance(sec, dict):
                    base.update({
                        "target_word_count": sec.get("target_word_count", sec.get("words", 0)) or 0,
                        "section_objectives": sec.get("objectives", sec.get("section_objectives", [])) or [],
                        "key_ideas": sec.get("key_ideas", sec.get("key_points", [])) or [],
                        "subsections": sec.get("subsections", []),
                        "intro_snippet": sec.get("intro_snippet", sec.get("intro", "")) or "",
                        "why_it_matters": sec.get("why_it_matters", sec.get("benefit", "")) or "",
                        "next_step": sec.get("next_step", sec.get("what_next", "")) or "",
                        "questions_to_answer": sec.get("questions_to_answer", sec.get("questions", [])) or [],
                        "data_points": sec.get("data_points", []),
                        "suggested_sources": sec.get("suggested_sources", sec.get("sources", [])) or [],
                        "keywords_focus": sec.get("keywords_focus") if isinstance(sec.get("keywords_focus"), dict) else {},
                        "media_plan": sec.get("media_plan", []),
                        "psychology_integration": sec.get("psychology_integration", {}),
                        "strategic_linking": sec.get("strategic_links", sec.get("strategic_linking", [])) or [],
                        "todo_gaps": sec.get("todo_gaps", [])
                    })
                out["content_sections"].append(base)

        # --- aliasy faq/cta ---
        if out.get("faq") and not out.get("faq_integration_strategy"):
            out["faq_integration_strategy"] = out["faq"]
        if out.get("cta") and not out.get("cta_placement_strategy"):
            out["cta_placement_strategy"] = out["cta"]

        # --- defaulty guidance/media/ux/placement ---
        wg = out.get("writer_guidance") or out.get("guidance") or {}
        if not isinstance(wg, dict):
            wg = {}
        wg.setdefault("checklists", {"seo": [], "ux": []})
        out["writer_guidance"] = wg
        out.setdefault("media_plan", out.get("media_plan", []))
        out.setdefault("ux_elements", out.get("ux", {}))
        out.setdefault("tone_restrictions", out.get("tone_restrictions", {}))
        out.setdefault("placement_guidance", out.get("placement_guidance", []))
        out.setdefault("_meta", out.get("_meta", {}))

        return out

    def _hydrate_links_into_sections(self, scaffold: Dict, ctx: Dict, per_section_min: int = 2) -> Dict:
        # Twarde zabezpieczenia typów kontekstu i sekcji
        sections = scaffold.get("content_sections", [])
        if not isinstance(sections, list):
            sections = []
            scaffold["content_sections"] = sections
        if not isinstance(ctx, dict):
            ctx = {}
        sli = (ctx.get("strategic_linking_intelligence") or {})
        if not isinstance(sli, dict):
            sli = {}
        links_fallback = (ctx.get("links") or {})
        if not isinstance(links_fallback, dict):
            links_fallback = {}
        candidates_raw = (
            (sli.get("funnel_links") or links_fallback.get("funnel_links") or []) +
            (sli.get("bridges") or links_fallback.get("bridges") or []) +
            (sli.get("hierarchy_links") or links_fallback.get("hierarchy_links") or [])
        )
        # Odfiltruj elementy nie-będące dict (np. stringi), które mogłyby wywołać 'str'.get
        candidates = [l for l in candidates_raw if isinstance(l, dict)]
        def score(sec, link):
            try:
                h2 = (sec.get("h2") or "").lower()
                kw = (sec.get("keywords_focus", {}).get("primary") or []) + (sec.get("keywords_focus", {}).get("semantic") or [])
                s = 0
                if any((k or '').lower() in ((link.get("anchor") or '')).lower() for k in kw): s += 2
                if link.get("funnel_stage") and link.get("funnel_stage") == scaffold.get("scaffold_meta", {}).get("funnel_stage"): s += 1
                if h2 and (h2.split(" ")[0] in ((link.get("anchor") or '').lower())): s += 1
                return s + (link.get("priority") or 0)/100.0
            except Exception:
                return 0
        for sec in sections:
            # Guard: skip non-dict sections to avoid 'list/str has no attribute get'
            if not isinstance(sec, dict):
                continue
            existing = sec.get("strategic_linking")
            if not isinstance(existing, list):
                existing = []
            # Odfiltruj elementy nie-dict, aby uniknąć 'str'.get podczas deduplikacji
            existing = [e for e in existing if isinstance(e, dict)]
            need = max(0, per_section_min - len(existing))
            if need <= 0: continue
            ranked = sorted(candidates, key=lambda l: score(sec, l), reverse=True)
            picked = []
            seen = set(((l.get("anchor"), l.get("url")) for l in existing))
            for l in ranked:
                key = (l.get("anchor"), l.get("url"))
                if key in seen: continue
                picked.append({
                    "type": l.get("type") or ("hierarchy" if (l.get("link_type") == 'hierarchy') else ("funnel" if l.get("link_type") == 'funnel' else "bridge")),
                    "anchor": l.get("anchor"),
                    "url": self._extract_link_url(l) if hasattr(self, '_extract_link_url') else (l.get("url") or l.get("target_url")),
                    "placement": (l.get("placement") or ["content_mid"])[0] if isinstance(l.get("placement"), list) else (l.get("placement") or "content_mid"),
                    "placement_section": (lambda p: "intro" if "intro" in p else ("conclusion" if "conclusion" in p else "content_mid"))((l.get("placement") or "content_mid") if isinstance(l.get("placement"), str) else str(l.get("placement") or "content_mid")),
                    "exact_placement": "after paragraph 2",
                    "psychology_reasoning": l.get("rationale") or l.get("psychology_angle") or "",
                    "funnel_stage": l.get("funnel_stage"),
                    "priority": l.get("priority") if isinstance(l.get("priority"), int) else 70,
                    "confidence": l.get("confidence_score") if isinstance(l.get("confidence_score"), (int,float)) else 0.7,
                    "from_h2": sec.get("h2"),
                    "from_h3": None
                })
                seen.add(key)
                if len(picked) >= need: break
            if picked:
                sec["strategic_linking"] = existing + picked
        return scaffold
