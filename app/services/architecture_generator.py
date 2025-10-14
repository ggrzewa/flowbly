"""
MODUŁ 3: ARCHITECTURE GENERATOR
Przekształca klastry semantyczne w konkretną architekturę strony
"""

import os
import asyncio
import json
import time
import logging
import re
import uuid
from typing import Dict, List, Tuple, Optional, Any
from datetime import datetime
import numpy as np
from difflib import SequenceMatcher

# Imports do AI/LLM
from openai import OpenAI
import anthropic

# Imports dla bazy danych
from supabase import Client as SupabaseClient

# --- M3 Bridge Selection Config ---
BRIDGES_TOP_K = int(os.getenv("BRIDGES_TOP_K", "5"))

SEM_MIN = float(os.getenv("BRIDGE_SEM_MIN", "0.85"))
SERP_MIN = float(os.getenv("BRIDGE_SERP_MIN", "0.65"))
INTENT_REQUIRED = True
CONF_MIN = float(os.getenv("BRIDGE_CONF_MIN", "0.80"))

# kara/bonus
PEN_OUTLIER = float(os.getenv("BRIDGE_PEN_OUTLIER", "-0.20"))
BONUS_JOURNEY = float(os.getenv("BRIDGE_BONUS_JOURNEY", "0.05"))

# Logger setup
logger = logging.getLogger("architecture_generator")

# --- Bridge Quality Helpers ---
STOP_WORDS = {"kontaktowych", "kontaktowe", "przewodnik", "inne"}

def _norm_name(name: str) -> str:
    """Normalizuje nazwę klastra/strony dla porównań"""
    n = (name or "").lower().strip()
    n = re.sub(r"\s+", " ", n)
    parts = [p for p in re.split(r"[\s\-_/]+", n) if p and p not in STOP_WORDS]
    return " ".join(parts)

def _fuzzy_sim(a: str, b: str) -> float:
    """Oblicza similarity między dwoma nazwami po normalizacji"""
    return SequenceMatcher(None, _norm_name(a), _norm_name(b)).ratio()

def _strict_fuzzy_match(a: str, b: str, threshold: float = 0.90) -> bool:
    """Sprawdza czy nazwy są podobne powyżej progu"""
    return _fuzzy_sim(a, b) >= threshold

class ArchitectureGenerator:
    """
    🏗️ PRODUCTION-GRADE Architecture Generator
    Przekształca klastry semantyczne w konkretną architekturę strony z strategic cross-linking
    """
    
    def __init__(self, cluster_data: Dict, arch_type: str = 'silo', domain: str = 'example.com', 
                 supabase_client: SupabaseClient = None, user_preferences: Dict = None):
        """
        Inicjalizacja generatora architektury
        
        Args:
            cluster_data: Dane z semantic_clusters + groups + members
            arch_type: 'silo' (rygorystyczne) lub 'clusters' (z cross-linking)
            domain: Domena docelowa
            supabase_client: Klient bazy danych
            user_preferences: Preferencje użytkownika
        """
        self.cluster_data = cluster_data
        self.arch_type = arch_type
        self.domain = domain
        self.seed_keyword = cluster_data.get('seed_keyword', 'unknown')
        self.groups = cluster_data.get('groups', cluster_data.get('clusters', []))
        self.supabase = supabase_client
        self.preferences = user_preferences or {}
        
        # --- AI Provider & Models (env-driven) ---
        self.ai_provider = os.getenv("AI_PROVIDER", "openai").lower()
        self.openai_model = os.getenv("AI_MODEL_OPENAI", "gpt-4o")
        self.claude_model = os.getenv("AI_MODEL_CLAUDE", "claude-sonnet-4-20250514")
        self.gpt5_model = os.getenv("AI_MODEL_GPT5", "gpt-5")
        self.gpt5_reasoning_effort = os.getenv("GPT5_REASONING_EFFORT", "medium")
        self.gpt5_verbosity = os.getenv("GPT5_VERBOSITY", "medium")
        
        # Configuration
        self.max_depth = self.preferences.get('max_depth', 3)
        self.include_local_seo = self.preferences.get('include_local_seo', True)
        self.cross_link_threshold = self.preferences.get('cross_link_threshold', 0.7)
        self.enable_funnel_audit = self.preferences.get('enable_funnel_audit', True)  # AI-powered customer journey audit
        
        # --- ARCH POLICY (SILO vs CLUSTERS) ---
        self.arch_policy = {
            "silo": {
                "enable_bridges": False,               # SILO = brak mostów
                "enable_funnel": True,
                "allow_ai_override_bridges": False,    # AI nie może „dorzucić" bridges
                "topk": 6,                             # konserwatywnie, możesz podnieść
                "min_per_type": {"bridge": 0, "funnel": 2}
            },
            "clusters": {
                "enable_bridges": True,                # CLUSTERS = mosty włączone
                "enable_funnel": True,
                "allow_ai_override_bridges": True,     # AI może wzmocnić istniejące mosty
                "topk": 6,                             # K=6 – jeśli masz 5 dobrych, to 5 przejdzie
                "min_per_type": {"bridge": 2, "funnel": 2}
            }
        }.get(self.arch_type, {
            # fallback (zachowuj się jak clusters)
            "enable_bridges": True,
            "enable_funnel": True,
            "allow_ai_override_bridges": True,
            "topk": 6,
            "min_per_type": {"bridge": 2, "funnel": 2}
        })
        
        # Initialize AI clients
        self._init_ai_clients()
        
        # Database helper
        if self.supabase:
            self.db = ArchitectureDatabase(self.supabase)
        else:
            self.db = None
        
        # Validation
        if not self.groups:
            raise ValueError("No groups found in cluster data")
            
        logger.info(f"🏗️ ArchitectureGenerator initialized: {len(self.groups)} groups, type={arch_type}")
        logger.info(f"🔧 [CONFIG] AI_PROVIDER={self.ai_provider}")
        logger.info(f"🔧 [CONFIG] AI_MODEL_OPENAI={self.openai_model}")
        logger.info(f"🔧 [CONFIG] AI_MODEL_CLAUDE={self.claude_model}")
        logger.info(f"🔧 [CONFIG] AI_MODEL_GPT5={self.gpt5_model}")
        logger.info(f"🔧 [CONFIG] GPT5_REASONING_EFFORT={self.gpt5_reasoning_effort}")
    
    def _init_ai_clients(self):
        """Inicjalizuje klientów AI (OpenAI + Claude)"""
        try:
            # OpenAI client
            openai_key = os.getenv("OPENAI_API_KEY")
            if openai_key:
                self.openai_client = OpenAI(api_key=openai_key)
                logger.info(f"✅ OpenAI client initialized (model={self.openai_model})")
            else:
                self.openai_client = None
                logger.warning("⚠️ OpenAI API key not found")
            
            # Claude client
            claude_key = os.getenv("ANTHROPIC_API_KEY")
            if claude_key:
                self.claude_client = anthropic.Anthropic(api_key=claude_key)
                logger.info(f"✅ Claude client initialized (model={self.claude_model})")
            else:
                self.claude_client = None
                logger.warning("⚠️ Claude API key not found")
                
        except Exception as e:
            logger.error(f"❌ AI client initialization failed: {str(e)}")
            self.openai_client = None
            self.claude_client = None

    def _reset_ai_session(self) -> None:
        """Hard reset of AI clients to ensure session isolation between phases."""
        try:
            self.openai_client = None
            self.claude_client = None
            logger.info("🧹 [SESSION] Cleared AI clients")
            self._init_ai_clients()
            logger.info("🔄 [SESSION] Reinitialized AI clients for isolated phase")
        except Exception as e:
            logger.warning(f"⚠️ [SESSION] AI session reset failed: {e}")

    def _score_bridge(self, s_sem: float, s_serp: float, intent_match: bool, *, 
                     journey_ok: bool = False, has_outlier: bool = False) -> float:
        """
        🎯 Oblicza confidence_score dla bridge na podstawie multiple signals
        """
        base = 0.6 * float(s_sem) + 0.35 * float(s_serp) + 0.05 * (1.0 if intent_match else 0.0)
        if journey_ok: 
            base += BONUS_JOURNEY
        if has_outlier: 
            base += PEN_OUTLIER
        return max(0.0, min(1.0, base))

    def _passes_hard_thresholds(self, s_sem: float, s_serp: float, intent_match: bool) -> bool:
        """
        🚪 Hard quality gates - musi przejść wszystkie aby bridge był rozważany
        """
        if s_sem < SEM_MIN: 
            return False
        if s_serp < SERP_MIN: 
            return False
        if INTENT_REQUIRED and not intent_match: 
            return False
        return True

    # ===== Helpery separacji funnel vs bridges =====
    def _pair_key(self, link: Dict) -> tuple:
        return (
            link.get('from_page_id') or link.get('from_url') or link.get('from'),
            link.get('to_page_id') or link.get('to_url') or link.get('to'),
        )

    def _same_parent_bucket(self, from_page_id: Optional[str], to_page_id: Optional[str]) -> bool:
        """Porównuje 'bucket' pierwszego segmentu ścieżki URL obu stron.
        Jeśli brak metadanych – wraca False (bezpieczniej dla recall bridges),
        ale spróbuje fallback na URL z linku gdy dostępny w obiekcie linku (obsłużone niżej).
        """
        def _meta_by_id(pid: Optional[str]) -> Optional[Dict]:
            if not pid:
                return None
            return (getattr(self, "_pages_meta", {}) or {}).get(pid)

        def _bucket_from_path(path: str) -> str:
            parts = (path or '').strip('/').split('/')
            return parts[1] if len(parts) > 1 else (parts[0] if parts else '')

        fp = _meta_by_id(from_page_id)
        tp = _meta_by_id(to_page_id)
        if not fp or not tp:
            return False
        return _bucket_from_path(fp.get('url_path') or '') == _bucket_from_path(tp.get('url_path') or '')

    def _infer_funnel_stage(self, from_intent: str, to_intent: str) -> str:
        intent_rank = {'informational': 0, 'commercial': 1, 'transactional': 2}
        f = intent_rank.get((from_intent or '').lower(), 0)
        t = intent_rank.get((to_intent or '').lower(), 0)
        if t <= f:
            return "awareness"
        if t == 1:
            return "consideration"
        return "decision"

    def _separate_and_dedupe_funnel_vs_bridges(self, internal_linking, strategic_bridges):
        """Rozdziela i odduplikuje funnel vs bridges po audycie AI.
        - internal_linking: może być listą linków 'funnel' lub dict-em dla vertical_linking – jeśli dict, zwracamy bez zmian.
        - strategic_bridges: lista linków bridge
        """
        # jeśli internal_linking to dict (vertical), zostaw jak jest
        if isinstance(internal_linking, dict):
            return internal_linking, strategic_bridges or []

        internal_linking = internal_linking or []
        strategic_bridges = strategic_bridges or []

        # Zasil meta stron jeśli brak (użyj arch_pages jeżeli dostępne)
        if not hasattr(self, "_pages_meta") or not self._pages_meta:
            self._pages_meta = {}
            try:
                # Jeśli mamy zapisane strony w pamięci
                arch_pages = getattr(self, 'arch_pages', None) or []
                for p in arch_pages:
                    if isinstance(p, dict) and p.get('id'):
                        self._pages_meta[p['id']] = {
                            'url_path': p.get('url_path') or '',
                            'intent': (p.get('intent') or '').lower() or 'informational'
                        }
            except Exception:
                pass

        def uniq_by_pair(links: List[Dict]) -> List[Dict]:
            seen = set()
            out = []
            for l in links:
                k = self._pair_key(l)
                if k in seen:
                    continue
                seen.add(k)
                out.append(l)
            return out

        # 1) dedup w obrębie list
        internal_linking = uniq_by_pair(internal_linking)
        strategic_bridges = uniq_by_pair(strategic_bridges)

        # 2) usuń z bridges pary, które są w funnel (oznaczone typem 'funnel' lub mają funnel_stage)
        funnel_pairs = set()
        for l in internal_linking:
            if (l.get('type') == 'funnel') or l.get('funnel_stage'):
                funnel_pairs.add(self._pair_key(l))
        strategic_bridges = [b for b in strategic_bridges if self._pair_key(b) not in funnel_pairs]

        # 3) wymuś cross-bucket dla bridges – te z tego samego bucketu przenieś do funnel
        brid_out = []
        for b in strategic_bridges:
            from_id = b.get('from_page_id')
            to_id = b.get('to_page_id')
            same_bucket = False
            if from_id and to_id:
                same_bucket = self._same_parent_bucket(from_id, to_id)
            else:
                # Fallback: spróbuj z URL jeśli brak ID
                def _bucket_from_url(u: str) -> str:
                    parts = (u or '').replace('https://', '').replace('http://', '').split('/')
                    # znajdź część ścieżki po domenie
                    path_parts = []
                    if len(parts) > 1:
                        path_parts = parts[1:]
                    segs = '/'.join(path_parts).strip('/').split('/')
                    return segs[1] if len(segs) > 1 else (segs[0] if segs else '')
                fb = _bucket_from_url(b.get('from_url') or '')
                tb = _bucket_from_url(b.get('to_url') or '')
                same_bucket = (fb and tb and fb == tb)

            if same_bucket:
                # to raczej krok lejka – przenieś do funnel
                b['type'] = 'funnel'
                if not b.get('funnel_stage'):
                    fi = (self._pages_meta.get(from_id) or {}).get('intent', 'informational')
                    ti = (self._pages_meta.get(to_id) or {}).get('intent', 'informational')
                    b['funnel_stage'] = self._infer_funnel_stage(fi, ti)
                internal_linking.append(b)
            else:
                brid_out.append(b)
        strategic_bridges = brid_out

        # 4) uzupełnij funnel_stage tam, gdzie puste
        for l in internal_linking:
            if (l.get('type') == 'funnel' or l.get('funnel_stage')) and not l.get('funnel_stage'):
                fp = self._pages_meta.get(l.get('from_page_id'), {})
                tp = self._pages_meta.get(l.get('to_page_id'), {})
                fi = (fp or {}).get('intent', 'informational')
                ti = (tp or {}).get('intent', 'informational')
                l['funnel_stage'] = self._infer_funnel_stage(fi, ti)

        # 5) końcowa deduplikacja
        internal_linking = uniq_by_pair(internal_linking)
        strategic_bridges = uniq_by_pair(strategic_bridges)

        return internal_linking, strategic_bridges
    
    async def generate(self) -> Dict:
        """🔥 Główna funkcja generująca kompletną architekturę - PRODUCTION VERSION"""
        try:
            start_time = time.time()
            logger.info(f"🚀 [ARCHITECTURE] Rozpoczynam generowanie dla '{self.seed_keyword}' ({self.arch_type})")
            
            # 1. Identyfikuj hierarchię (LLM-powered with retry logic)
            logger.info("📊 [ARCHITECTURE] Krok 1/7: Identyfikacja hierarchii...")
            hierarchy = await self.identify_hierarchy_with_retry()
            
            # 2. Generuj strukturę URL
            logger.info("🔗 [ARCHITECTURE] Krok 2/7: Generowanie struktury URL...")
            url_structure = self.generate_url_structure(hierarchy)
            
            # 3. Stwórz schemat nawigacji
            logger.info("🧭 [ARCHITECTURE] Krok 3/7: Tworzenie nawigacji...")
            navigation = self.generate_navigation(url_structure)
            
            # 4. Zaplanuj internal linking (vertical)
            logger.info("🔗 [ARCHITECTURE] Krok 4/7: Planowanie internal linking...")
            internal_linking = self.generate_internal_linking(hierarchy)
            
            # 5. Znajdź strategic cross-links (AI-based, URL mapping) - zgodnie z polityką
            strategic_bridges = []
            if self.arch_policy["enable_bridges"]:
                logger.info("🌉 [ARCHITECTURE] Krok 5/7: Strategic cross-linking (AI-based)...")
                pages_data = self._extract_pages_from_structure(url_structure)
                strategic_bridges = await self._ai_generate_strategic_bridges(pages_data)
            else:
                logger.info("🛡️ [POLICY] Krok 5/7: SILO policy - skipping strategic cross-linking")
            
            # Hard-isolate AI session before funnel phase
            self._reset_ai_session()
            await asyncio.sleep(0)  # yield to ensure fresh context
            
            # 5.5. OPTIONAL: AI-driven Funnel audit (if enabled)
            funnel_audit = {}
            funnel_links: List[Dict] = []
            if self.enable_funnel_audit:
                logger.info("🎯 [ARCHITECTURE] Krok 5.5/7: AI-driven Funnel audit...")
                pages_data = self._extract_pages_from_structure(url_structure)
                funnel_audit = await self._audit_existing_linking_for_funnel(
                    {
                        'internal_linking': internal_linking, 
                        'strategic_bridges': [],  # hard isolation: do not pass bridges into funnel audit
                        'architecture_type': self.arch_type
                    }, 
                    pages_data
                )
                
                # 5.6. Apply AI-generated funnel structure if recommended - zgodnie z polityką
                if funnel_audit.get('should_modify_structure', False):
                    logger.info("🎯 [ARCHITECTURE] Krok 5.6/7: Applying AI-modified funnel structure...")
                    logger.info(f"🔍 [PIPELINE_DEBUG] Strategic bridges BEFORE funnel modify: {len(strategic_bridges)}")
                    
                    if funnel_audit.get('modified_internal_linking'):
                        internal_linking = funnel_audit['modified_internal_linking']
                        logger.info("✅ [ARCHITECTURE] AI modified internal linking structure")
                        
                    # ROZDZIEL: Funnel links osobno, strategic_bridges pozostają nietknięte
                    if funnel_audit.get('modified_strategic_bridges'):
                        funnel_links = funnel_audit['modified_strategic_bridges']
                        logger.info("✅ [ARCHITECTURE] AI generated funnel links")
                        logger.info(f"🔍 [PIPELINE_DEBUG] Funnel links created: {len(funnel_links)}")
                    logger.info(f"🔍 [PIPELINE_DEBUG] Strategic bridges AFTER funnel modify: {len(strategic_bridges)}")
                    logger.info(f"🔍 [PIPELINE_DEBUG] Final strategic_bridges preview:")
                    try:
                        for i, bridge in enumerate((strategic_bridges or [])[:5]):
                            logger.info(f"🔍 [PIPELINE_DEBUG] Strategic {i+1}: {bridge.get('from_cluster','')} → {bridge.get('to_cluster','')}")
                    except Exception:
                        pass
                    logger.info(f"🔍 [PIPELINE_DEBUG] Strategic bridges preserved: {len(strategic_bridges)}")
                    logger.info(f"🔍 [PIPELINE_DEBUG] Final counts: strategic={len(strategic_bridges)}, funnel={len(funnel_links)}")

                    # UWAGA: Nie mieszamy już strategic_bridges do payloadu funnel
                    # funnel_audit['modified_strategic_bridges'] pozostaje tym, co zwróciło AI dla customer journey
                        
                    modifications = funnel_audit.get('modifications_summary', [])
                    logger.info(f"🎯 [ARCHITECTURE] AI modifications applied: {', '.join(modifications)}")
                else:
                    logger.info("⏭️ [ARCHITECTURE] Krok 5.6/7: AI nie rekomenduje modyfikacji struktury")
            else:
                logger.info("⏭️ [ARCHITECTURE] Krok 5.5/7: Funnel audit disabled - pomijam")
            
            # 6. Generuj implementation notes
            logger.info("📝 [ARCHITECTURE] Krok 6/7: Implementation notes...")
            implementation_notes = self.generate_implementation_notes()
            
            # 7. Generate SEO recommendations
            logger.info("📈 [ARCHITECTURE] Krok 7/7: SEO recommendations...")
            seo_recommendations = self.generate_seo_recommendations(url_structure)
            
            processing_time = time.time() - start_time
            
            # Calculate SEO score
            seo_score = self.calculate_seo_score(url_structure, internal_linking, strategic_bridges)
            
            result = {
                "architecture_type": self.arch_type,
                "seed_keyword": self.seed_keyword,
                "semantic_cluster_id": self.cluster_data.get('id', self.cluster_data.get('semantic_cluster_id')),
                "domain": self.domain,
                "hierarchy": hierarchy,
                "url_structure": url_structure,
                "navigation": navigation,
                "internal_linking": internal_linking,
                "strategic_bridges": strategic_bridges,
                "implementation_notes": implementation_notes,
                "seo_recommendations": seo_recommendations,
                "processing_time": processing_time,
                "seo_score": seo_score,
                "funnel_audit": funnel_audit,  # AI-powered customer journey audit
                "stats": {
                    "total_pages": self.count_total_pages(url_structure) or 0,  # Safe fallback
                    "max_depth": self.calculate_max_depth(url_structure) or 1,  # Safe fallback
                    "cross_links_found": len(strategic_bridges),
                    "embeddings_used": any(g.get('embeddings_available', False) for g in self.groups),
                    "funnel_optimized": funnel_audit.get('should_optimize_for_funnel', False),
                    "funnel_structure_modified": funnel_audit.get('should_modify_structure', False),
                    "funnel_confidence": float(funnel_audit.get('confidence_score', 0.0)),
                    "ai_modifications": funnel_audit.get('modifications_summary', []),
                    "psychology_applied": funnel_audit.get('should_modify_structure', False),
                    "quality_indicators": {
                        "hierarchy_complexity": len(hierarchy.get('main_categories', [])),
                        "strategic_bridges": len(strategic_bridges),
                        "avg_similarity": float(np.mean([b.get('similarity_score', 0) for b in strategic_bridges])) if strategic_bridges else 0.0,
                        "funnel_stages_detected": funnel_audit.get('funnel_stages_detected', [])
                    }
                }
            }

            # --- NOWOŚĆ: PAA + AI Overview Analysis ---
            if self.preferences.get('include_content_analysis', True):
                self.analyze_paa_and_ai_overview(result)
            # ZAWSZE dodaj content_opportunities do result
            result["content_opportunities"] = getattr(self, '_content_opportunities_decisions', [])

            logger.info(f"✅ [ARCHITECTURE] Architektura wygenerowana w {processing_time:.2f}s - SEO Score: {seo_score}/100")
            return result
        except Exception as e:
            logger.error(f"❌ [ARCHITECTURE] Generowanie nie powiodło się: {str(e)}")
            raise

    def analyze_paa_and_ai_overview(self, architecture_result: Dict):
        """Po podstawowej architekturze, analizuje PAA i AI Overview"""
        logger.info("🔎 [ARCHITECTURE] Analiza PAA + AI Overview (content opportunities)...")
        try:
            paa_data = self.get_paa_data()
            ai_overview_data = self.get_ai_overview_data()
            if not paa_data and not ai_overview_data:
                logger.info("ℹ️ Brak PAA i AI Overview - pomijam content opportunities")
                self._content_opportunities_decisions = []
                return
            existing_pages = self._extract_existing_pages(architecture_result['url_structure'])
            decisions = self._ai_decide_paa_ai_overview(existing_pages, paa_data, ai_overview_data)
            self._content_opportunities_decisions = decisions
            self._apply_content_opportunities(architecture_result, decisions)
            # NIE zapisuj do bazy tutaj!
            logger.info(f"✅ [PAA] Content opportunities processed: {len(decisions)} decisions")
        except Exception as e:
            logger.error(f"❌ [ARCHITECTURE] analyze_paa_and_ai_overview failed: {str(e)}")
            self._content_opportunities_decisions = []

    def _ai_decide_paa_ai_overview(self, existing_pages, paa_data, ai_overview_data):
        """Ultra-lekka analiza PAA/AI Overview - tylko struktura URL + pytania"""
        # 1. TYLKO STRUKTURA URL - bez słów kluczowych!
        structure_summary = []
        for page in existing_pages:  # Bez limitu
            structure_summary.append(f"📄 {page['name']} → {page['url']}")
        # 2. TYLKO PYTANIA PAA - bez snippetów!
        paa_questions = []
        for paa in (paa_data or []):  # Bez limitu
            question = paa.get("question", "")  # Bez skracania
            if question:
                paa_questions.append(question)
        # 3. TYLKO TYTUŁY AI OVERVIEW - bez contentu!
        ai_topics = []
        for ai in (ai_overview_data or []):  # Bez limitu
            title = ai.get("title", "") or ai.get("snippet", "")  # Bez skracania
            if title:
                ai_topics.append(title)
        # 4. SPRAWDŹ CZY MAMY DANE
        if not paa_questions and not ai_topics:
            logger.info("ℹ️ [PAA] Brak pytań PAA i AI Overview - pomijam analizę")
            return []
        logger.info(f"🔍 [PAA] Analizuję: {len(paa_questions)} PAA + {len(ai_topics)} AI Overview")
        # 5. ULTRA-KRÓTKI PROMPT - tylko struktura + pytania
        prompt = f"""
STRUKTURA STRONY dla: '{self.seed_keyword}'
{chr(10).join(structure_summary)}

PYTANIA PAA ({len(paa_questions)}):
{chr(10).join([f"• {q}" for q in paa_questions])}

AI OVERVIEW TEMATY ({len(ai_topics)}):
{chr(10).join([f"• {t}" for t in ai_topics])}

ZADANIE: Dla każdego pytania/tematu wybierz:
- FAQ: dodaj jako FAQ do istniejącej strony
- NEW_PAGE: stwórz nową stronę (jeśli nie pasuje nigdzie)
- SKIP: pomiń jeśli nieistotne

ZWRÓĆ TYLKO JSON:
{{
 "decisions": [
   {{
     "source": "PAA",
     "question": "pytanie...",
     "decision": "FAQ",
     "target_page": "/laptopy/poradnik-zakupowy/faq/",
     "priority": "high",
     "rationale": "Pytanie FAQ pasuje do istniejącej sekcji FAQ"
   }},
   {{
     "source": "AI_OVERVIEW", 
     "topic": "temat...",
     "decision": "NEW_PAGE",
     "suggested_url": "/laptopy/nowy-temat/",
     "parent_category": "/laptopy/poradnik-zakupowy/",
     "priority": "medium",
     "rationale": "Temat wymaga dedykowanej strony"
   }}
 ]
}}
"""
        try:
            # 6. KRÓTSZY TIMEOUT bo prompt jest mały
            response = self.call_llm_with_timeout(prompt, timeout=60)
            logger.info(f"🔍 [PAA] Claude response length: {len(response)} chars")
            # Czyść markdown
            if response.startswith("```json"):
                response = response.replace("```json", "").replace("```", "").strip()
            elif response.startswith("```"):
                response = response.replace("```", "").strip()
            response = response.strip()
            if not response or not (response.startswith('{') or response.startswith('[')):
                logger.warning(f"⚠️ [PAA] Claude nie zwrócił JSON. Response preview: {response[:200]}...")
                return []
            data = json.loads(response)
            decisions = data.get("decisions", [])
            logger.info(f"✅ [PAA] Otrzymano {len(decisions)} decyzji od Claude")
            return decisions
        except json.JSONDecodeError as e:
            logger.error(f"❌ [PAA] JSON parse error: {e}")
            logger.error(f"❌ [PAA] Raw response: {response[:500]}...")
            return []
        except Exception as e:
            logger.error(f"❌ [PAA] LLM PAA/AI Overview analysis failed: {e}")
            return []

    def get_paa_data(self):
        """Pobiera TYLKO pytania PAA - bez zbędnych metadanych"""
        try:
            serp_result = self.supabase.table("serp_results").select("id").eq("keyword", self.seed_keyword).execute()
            if not serp_result.data:
                logger.info(f"ℹ️ [PAA] Brak serp_results dla: '{self.seed_keyword}'")
                return []
            serp_result_id = serp_result.data[0]["id"]
            # TYLKO question - nie pobieraj snippet!
            paa_query = self.supabase.table("serp_people_also_ask").select("question").eq("serp_result_id", serp_result_id).execute()
            paa_count = len(paa_query.data) if paa_query.data else 0
            logger.info(f"🔍 [PAA] Znaleziono {paa_count} pytań PAA dla: '{self.seed_keyword}'")
            return paa_query.data if paa_query.data else []
        except Exception as e:
            logger.warning(f"⚠️ [PAA] get_paa_data error: {e}")
            return []

    def get_ai_overview_data(self):
        """Pobiera AI Overview z serp_items + references przez serp_item_id"""
        try:
            serp_result = self.supabase.table("serp_results").select("id").eq("keyword", self.seed_keyword).execute()
            if not serp_result.data:
                logger.info(f"ℹ️ [AI_OVERVIEW] Brak serp_results dla: '{self.seed_keyword}'")
                return []
            serp_result_id = serp_result.data[0]["id"]
            all_ai_data = []
            # 1. AI Overview z serp_items (główny content)
            serp_items = self.supabase.table("serp_items").select("id, title").eq("serp_result_id", serp_result_id).eq("type", "ai_overview").execute()
            for item in (serp_items.data or []):
                if item.get("title"):
                    all_ai_data.append({
                        "title": item.get("title"),
                        "source": "serp_items"
                    })
                    # 2. Pobierz references dla tego AI Overview
                    serp_item_id = item.get("id")
                    if serp_item_id:
                        ai_references = self.supabase.table("serp_ai_references").select("title").eq("serp_item_id", serp_item_id).execute()
                        for ref in (ai_references.data or []):
                            if ref.get("title"):
                                all_ai_data.append({
                                    "title": ref.get("title"),
                                    "source": "serp_ai_references"
                                })
            ai_count = len(all_ai_data)
            logger.info(f"🔍 [AI_OVERVIEW] Znaleziono {ai_count} AI Overview items dla: '{self.seed_keyword}'")
            return all_ai_data
        except Exception as e:
            logger.warning(f"⚠️ [AI_OVERVIEW] get_ai_overview_data error: {e}")
            return []

    def _extract_existing_pages(self, url_structure: Dict) -> list:
        pages = []
        if url_structure.get('pillar_page'):
            pages.append({
                "name": url_structure['pillar_page']['name'],
                "url": url_structure['pillar_page']['url_pattern']
            })
        for cat in url_structure.get('categories', []):
            pages.append({"name": cat['name'], "url": cat['url_pattern']})
            for sub in cat.get('subcategories', []):
                pages.append({"name": sub['name'], "url": sub['url_pattern']})
            for page in cat.get('standalone_pages', []):
                pages.append({"name": page['name'], "url": page['url_pattern']})
        return pages

    def _apply_content_opportunities(self, architecture_result: Dict, decisions: list):
        """Aktualizuje architekturę na podstawie decyzji AI (FAQ, nowe strony, linki)"""
        url_structure = architecture_result['url_structure']
        pages_by_url = {}
        if url_structure.get('pillar_page'):
            pages_by_url[url_structure['pillar_page']['url_pattern']] = url_structure['pillar_page']
        for cat in url_structure.get('categories', []):
            pages_by_url[cat['url_pattern']] = cat
            for sub in cat.get('subcategories', []):
                pages_by_url[sub['url_pattern']] = sub
            for page in cat.get('standalone_pages', []):
                pages_by_url[page['url_pattern']] = page
        new_pages = []
        for dec in decisions:
            if dec.get('decision') == 'FAQ' and dec.get('target_page') in pages_by_url:
                page = pages_by_url[dec['target_page']]
                if 'paa_questions' not in page:
                    page['paa_questions'] = []
                page['paa_questions'].append({
                    'question': dec.get('question'),
                    'source': dec.get('source'),
                    'priority': dec.get('priority', 'medium')
                })
                page['has_faq_section'] = True
                page['content_opportunities_count'] = page.get('content_opportunities_count', 0) + 1
            elif dec.get('decision') == 'NEW_PAGE' and dec.get('suggested_url'):
                # Dodaj nową stronę do architektury
                new_page = {
                    'name': dec.get('topic') or dec.get('question') or 'Nowa strona',
                    'url': dec['suggested_url'],
                    'url_pattern': dec['suggested_url'],
                    'page_type': 'cluster_page',
                    'ai_overview_topics': [{
                        'topic': dec.get('topic') or dec.get('question'),
                        'source': dec.get('source'),
                        'priority': dec.get('priority', 'medium')
                    }] if dec.get('source') == 'AI_OVERVIEW' else [],
                    'paa_questions': [{
                        'question': dec.get('question'),
                        'source': dec.get('source'),
                        'priority': dec.get('priority', 'medium')
                    }] if dec.get('source') == 'PAA' else [],
                    'content_opportunities_count': 1,
                    'has_faq_section': dec.get('source') == 'PAA',
                    'depth_level': 2  # Dodaj depth_level do nowej strony
                }
                parent_url = dec.get('parent_category')
                added = False
                if parent_url and parent_url in pages_by_url:
                    parent = pages_by_url[parent_url]
                    # Dodaj jako standalone_page jeśli to kategoria, lub subcategory jeśli to podkategoria
                    if 'standalone_pages' in parent:
                        parent['standalone_pages'].append(new_page)
                        added = True
                    elif 'subcategories' in parent:
                        parent['subcategories'].append(new_page)
                        added = True
                    else:
                        if 'standalone_pages' not in parent:
                            parent['standalone_pages'] = []
                        parent['standalone_pages'].append(new_page)
                        added = True
                if not added:
                    # Jeśli nie znaleziono parenta, dodaj do głównej listy kategorii jako standalone_page do pierwszej kategorii
                    if url_structure.get('categories'):
                        url_structure['categories'][0].setdefault('standalone_pages', []).append(new_page)
                    else:
                        url_structure.setdefault('categories', []).append(new_page)
                pages_by_url[dec['suggested_url']] = new_page
                new_pages.append(new_page)
        # Przelicz linki (hierarchiczne + strategic bridges jeśli clusters)
        # (Można rozbudować o automatyczne linkowanie do nowych stron)
        # Zaktualizuj stats
        architecture_result['stats']['content_opportunities_found'] = len(decisions)
        architecture_result['stats']['new_pages_from_paa'] = len(new_pages)
    
    async def generate_and_save(self, user_id: str = None) -> Dict:
        """Generuje architekturę i zapisuje do bazy danych"""
        try:
            architecture_result = await self.generate()
            if self.db:
                logger.info("💾 [ARCHITECTURE] Zapisuję do bazy danych...")
                save_result = self.db.save_architecture(architecture_result, user_id)
                architecture_result['database_result'] = save_result
                if save_result['success']:
                    logger.info(f"✅ [ARCHITECTURE] Zapisano architekturę: {save_result['architecture_id']}")
                    saved_architecture_id = save_result['architecture_id']
                    
                    # 🆕 NOWE: Tworzenie architecture_pages
                    try:
                        await self._create_architecture_pages(saved_architecture_id, architecture_result['url_structure'])
                    except Exception as pages_error:
                        logger.error(f"❌ [PAGES] Architecture_pages creation failed: {pages_error}")
                        # NIE przerywaj - architektura już zapisana
                    
                    # 🆕 NOWE: Top-K Links Selection i zapis do architecture_links
                    try:
                        saved_links_data = await self._save_architecture_links_simple(
                            saved_architecture_id, 
                            architecture_result['internal_linking'],
                            architecture_result['strategic_bridges'],
                            architecture_result.get('funnel_audit', {})
                        )
                        
                        # 🎯 UNIFIED FLOW: Zastąp dane w architekturze tymi z DB
                        architecture_result['strategic_bridges'] = saved_links_data.get('strategic_bridges', [])
                        architecture_result['funnel_links'] = saved_links_data.get('funnel_links', [])
                        architecture_result['hierarchy_links'] = saved_links_data.get('hierarchy_links', [])
                        architecture_result['total_links'] = saved_links_data.get('total_links', 0)
                        
                        logger.info(f"🎯 [UNIFIED] Architecture result updated with {saved_links_data.get('total_links', 0)} links from DB")
                        
                    except Exception as links_error:
                        logger.error(f"❌ [LINKS] Architecture_links creation failed: {links_error}")
                        # NIE przerywaj - architektura już zapisana
                    
                    # ISTNIEJĄCY KOD (bez zmian):
                    if hasattr(self, '_content_opportunities_decisions') and self._content_opportunities_decisions:
                        self.db.save_content_opportunities_fixed(saved_architecture_id, self._content_opportunities_decisions)
                else:
                    logger.error(f"❌ [ARCHITECTURE] Błąd zapisu: {save_result['error']}")
            else:
                logger.warning("⚠️ [ARCHITECTURE] Brak połączenia z bazą - pomijam zapis")
            return architecture_result
        except Exception as e:
            logger.error(f"❌ [ARCHITECTURE] Generate and save failed: {str(e)}")
            raise

    def generate_slug(self, text: str) -> str:
        """Generuje SEO-friendly URL slug (bez polskich znaków)"""
        # Polskie znaki → ASCII
        polish_chars = {
            'ą': 'a', 'ć': 'c', 'ę': 'e', 'ł': 'l', 'ń': 'n',
            'ó': 'o', 'ś': 's', 'ź': 'z', 'ż': 'z',
            'Ą': 'A', 'Ć': 'C', 'Ę': 'E', 'Ł': 'L', 'Ń': 'N',
            'Ó': 'O', 'Ś': 'S', 'Ź': 'Z', 'Ż': 'Z'
        }
        
        text = text.lower()
        for pl, en in polish_chars.items():
            text = text.replace(pl.lower(), en)
        
        # Tylko litery, cyfry i myślniki
        text = re.sub(r'[^a-z0-9\s-]', '', text)
        text = re.sub(r'\s+', '-', text)
        text = re.sub(r'-+', '-', text)
        text = text.strip('-')
        
        # Limit length
        if len(text) > 50:
            text = text[:50].rstrip('-')
        
        return text or "unknown"
    
    def generate_url_structure(self, hierarchy: Dict) -> Dict:
        """🔗 Generuje pełną strukturę URL na podstawie hierarchii"""
        logger.info(f"🔗 [URL] Generuję strukturę URL dla domeny: {self.domain}")
        
        base_url = f"https://{self.domain}"
        pillar_slug = hierarchy['pillar']['url_slug']
        
        structure = {
            "pillar_page": {
                "name": hierarchy['pillar']['name'],
                "url": f"{base_url}/{pillar_slug}/",
                "url_pattern": f"/{pillar_slug}/",
                "page_type": "pillar",
                "target_keywords": [self.seed_keyword],
                "business_intent": hierarchy['pillar'].get('target_intent', 'informational'),
                "estimated_word_count": hierarchy['pillar'].get('estimated_word_count', 3000)
            },
            "categories": []
        }
        
        for main_cat in hierarchy['main_categories']:
            category = {
                "name": main_cat['name'],
                "url": f"{base_url}/{pillar_slug}/{main_cat['url_slug']}/",
                "url_pattern": f"/{pillar_slug}/{main_cat['url_slug']}/",
                "page_type": "category",
                "business_intent": main_cat.get('intent', 'informational'),
                "priority": main_cat.get('priority', 1),
                "subcategories": [],
                "standalone_pages": []
            }
            
            # Sub-categories (jeśli są)
            for sub_cat in main_cat.get('sub_categories', []):
                cluster = self.get_cluster_by_name(sub_cat['cluster_name'])
                subcategory = {
                    "name": sub_cat['name'],
                    "url": f"{base_url}/{pillar_slug}/{main_cat['url_slug']}/{sub_cat['url_slug']}/",
                    "url_pattern": f"/{pillar_slug}/{main_cat['url_slug']}/{sub_cat['url_slug']}/",
                    "page_type": "subcategory",
                    "cluster_data": cluster,
                    "phrases_with_details": cluster.get('phrases_with_details', []) if cluster else [],
                    "estimated_word_count": sub_cat.get('estimated_word_count', 1500)
                }
                category['subcategories'].append(subcategory)
            
            # Standalone clusters w ramach kategorii
            for standalone in main_cat.get('standalone_clusters', []):
                cluster = self.get_cluster_by_name(standalone['cluster_name'])
                page = {
                    "name": standalone['name'],
                    "url": f"{base_url}/{pillar_slug}/{main_cat['url_slug']}/{standalone['url_slug']}/",
                    "url_pattern": f"/{pillar_slug}/{main_cat['url_slug']}/{standalone['url_slug']}/",
                    "page_type": "cluster_page",
                    "cluster_data": cluster,
                    "phrases_with_details": cluster.get('phrases_with_details', []) if cluster else [],
                    "estimated_word_count": standalone.get('estimated_word_count', 1200)
                }
                category['standalone_pages'].append(page)
            
            structure['categories'].append(category)
        
        logger.info(f"✅ [URL] Struktura URL: {self.count_total_pages(structure)} stron, głębokość: {self.calculate_max_depth(structure)}")
        return structure
    
    def get_cluster_by_name(self, cluster_name: str) -> Optional[Dict]:
        """Znajduje klaster po nazwie"""
        for cluster in self.groups:
            if cluster['name'] == cluster_name:
                return cluster
        
        logger.warning(f"⚠️ [URL] Nie znaleziono klastra: {cluster_name}")
        return None
    
    def generate_navigation(self, url_structure: Dict) -> Dict:
        """🧭 Generuje schematy nawigacji"""
        logger.info("🧭 [NAVIGATION] Generuję struktury nawigacji...")
        
        # Main Menu
        main_menu = {
            "pillar": {
                "label": url_structure['pillar_page']['name'],
                "url": url_structure['pillar_page']['url_pattern'],
                "children": []
            }
        }
        
        for category in url_structure['categories']:
            menu_item = {
                "label": category['name'],
                "url": category['url_pattern'],
                "children": []
            }
            
            # Dodaj subcategorie do menu
            for sub in category['subcategories']:
                menu_item['children'].append({
                    "label": sub['name'],
                    "url": sub['url_pattern']
                })
            
            # Dodaj standalone pages
            for page in category['standalone_pages']:
                menu_item['children'].append({
                    "label": page['name'], 
                    "url": page['url_pattern']
                })
            
            main_menu['pillar']['children'].append(menu_item)
        
        # Breadcrumb Templates
        breadcrumb_templates = {
            "pillar": "Strona główna > {pillar_name}",
            "category": "Strona główna > {pillar_name} > {category_name}",
            "subcategory": "Strona główna > {pillar_name} > {category_name} > {subcategory_name}",
            "cluster_page": "Strona główna > {pillar_name} > {category_name} > {page_name}"
        }
        
        # Mobile menu (simplified)
        mobile_menu = self.generate_mobile_nav(main_menu)
        
        # Sidebar navigation
        sidebar_nav = self.generate_sidebar_nav(url_structure)
        
        navigation = {
            "main_menu": main_menu,
            "breadcrumb_templates": breadcrumb_templates,
            "sidebar_nav": sidebar_nav,
            "mobile_menu": mobile_menu
        }
        
        logger.info("✅ [NAVIGATION] Struktury nawigacji wygenerowane")
        return navigation
    
    def generate_mobile_nav(self, main_menu: Dict) -> Dict:
        """Generuje uproszczoną nawigację mobilną"""
        # Simplified version for mobile - max 2 levels
        mobile = {
            "pillar": main_menu['pillar'].copy()
        }
        
        # Limit children for mobile
        if 'children' in mobile['pillar']:
            mobile['pillar']['children'] = main_menu['pillar']['children'][:5]  # Max 5 items
            
            # Remove sub-children for mobile simplicity
            for child in mobile['pillar']['children']:
                if 'children' in child and len(child['children']) > 3:
                    child['children'] = child['children'][:3]  # Max 3 sub-items
        
        return mobile
    
    def generate_sidebar_nav(self, url_structure: Dict) -> Dict:
        """Generuje nawigację boczną dla deep hierarchii"""
        sidebar = {
            "section_based": True,
            "sections": []
        }
        
        for category in url_structure['categories']:
            section = {
                "title": category['name'],
                "pages": []
            }
            
            # Add category itself
            section['pages'].append({
                "title": category['name'],
                "url": category['url_pattern'],
                "type": "category"
            })
            
            # Add subcategories and standalone pages
            for sub in category['subcategories']:
                section['pages'].append({
                    "title": sub['name'],
                    "url": sub['url_pattern'],
                    "type": "subcategory"
                })
            
            for page in category['standalone_pages']:
                section['pages'].append({
                    "title": page['name'],
                    "url": page['url_pattern'],
                    "type": "cluster_page"
                })
            
            sidebar['sections'].append(section)
        
        return sidebar
    
    def generate_internal_linking(self, hierarchy: Dict) -> Dict:
        """🔗 Generuje strategię linkowania wewnętrznego (vertical)"""
        logger.info("🔗 [LINKING] Generuję plan internal linking...")
        
        vertical_links = []
        
        # SUB → CATEGORY → PILLAR linking
        for main_cat in hierarchy['main_categories']:
            
            # Sub-category → Category links
            for sub_cat in main_cat.get('sub_categories', []):
                vertical_links.append({
                    "from_page": f"/{hierarchy['pillar']['url_slug']}/{main_cat['url_slug']}/{sub_cat['url_slug']}/",
                    "to_page": f"/{hierarchy['pillar']['url_slug']}/{main_cat['url_slug']}/",
                    "link_type": "upward_category",
                    "anchor_text": f"Wszystko o {main_cat['name'].lower()}",
                    "placement": ["breadcrumb", "content_end", "sidebar"],
                    "context": f"Link z podstrony do kategorii nadrzędnej"
                })
            
            # Standalone pages → Category links
            for standalone in main_cat.get('standalone_clusters', []):
                vertical_links.append({
                    "from_page": f"/{hierarchy['pillar']['url_slug']}/{main_cat['url_slug']}/{standalone['url_slug']}/",
                    "to_page": f"/{hierarchy['pillar']['url_slug']}/{main_cat['url_slug']}/",
                    "link_type": "upward_category",
                    "anchor_text": f"Zobacz więcej: {main_cat['name'].lower()}",
                    "placement": ["content_intro", "conclusion"],
                    "context": f"Link ze strony klastra do kategorii nadrzędnej"
                })
            
            # Category → Pillar links  
            vertical_links.append({
                "from_page": f"/{hierarchy['pillar']['url_slug']}/{main_cat['url_slug']}/",
                "to_page": f"/{hierarchy['pillar']['url_slug']}/",
                "link_type": "upward_pillar",
                "anchor_text": f"Kompletny przewodnik: {hierarchy['pillar']['name']}",
                "placement": ["header", "content_intro", "footer"],
                "context": "Link z kategorii do strony filarowej"
            })
        
        internal_linking = {
            "vertical_linking": vertical_links,
            "linking_principles": [
                "Każda podstrona linkuje do kategorii nadrzędnej",
                "Każda kategoria linkuje do strony filarowej", 
                "Anchor text zawiera target keyword kategorii",
                "Linki umieszczone w breadcrumbs + content + sidebar"
            ]
        }
        
        logger.info(f"✅ [LINKING] Plan internal linking: {len(vertical_links)} linków vertical")
        return internal_linking
    
    async def _ai_generate_strategic_bridges(self, pages_data: List[Dict]) -> List[Dict]:
        """🤖 AI-based Strategic Bridges z business logic zamiast embedding similarity"""
        try:
            if not self.arch_policy.get("enable_bridges", False):
                logger.info("🛡️ [AI_BRIDGES] SILO policy - strategic bridges disabled")
                return []

            logger.info("🤖 [AI_BRIDGES] Generuję strategic bridges przez AI...")

            # Przygotuj strukturę stron
            pages_summary = []
            for page in pages_data:
                pages_summary.append({
                    'name': page.get('name', ''),
                    'url_path': page.get('url_pattern', ''),
                    'page_type': page.get('page_type', ''),
                    'category': self._extract_category_from_url(page.get('url_pattern', ''))
                })

            # DEBUG: Co AI dostaje jako input
            logger.info(f"🔍 [AI_DEBUG] Wysyłam do AI {len(pages_summary)} stron:")
            for i, p in enumerate(pages_summary):
                logger.info(f"🔍 [AI_DEBUG] Page {i+1}: {p.get('name')} → {p.get('url_path')}")

            logger.info(f"🔍 [AI_DEBUG] Sample pages_data z url_structure:")
            for i, p in enumerate((pages_data or [])[:5]):
                logger.info(f"🔍 [AI_DEBUG] Input {i+1}: {p.get('name')} → {p.get('url_pattern', p.get('url_path', 'NO_URL'))}")

            prompt = f"""
ZADANIE: Stwórz strategic cross-links między RÓŻNYMI kategoriami dla "{self.seed_keyword}"

STRUKTURA STRON ({len(pages_summary)}):
{json.dumps(pages_summary, indent=2, ensure_ascii=False)}

ZASADY STRATEGIC BRIDGES:
1. CROSS-CATEGORICAL ONLY - łącz strony z różnych głównych kategorii
2. LATERAL CONNECTIONS - alternatives, comparisons, related options (NIE sequential flow)
3. BUSINESS LOGIC - użytkownik porównuje opcje, szuka alternatyw
4. USER VALUE - pomaga w research i decision making

PRZYKŁADY DOBRYCH STRATEGIC BRIDGES:
- Gaming ↔ Business (use case comparison)
- New ↔ Used (purchase alternatives)  
- Budget ↔ Premium (price comparison)
- Brands ↔ Specs (research approaches)
- Student ↔ Professional (target audience)

ZWRÓĆ 3-5 strategic bridges w JSON:
{{
  "strategic_bridges": [
    {{
      "from_url": "/laptopy/gaming/",
      "to_url": "/laptopy/business/", 
      "suggested_anchor": "Porównaj z laptopami biznesowymi",
      "bridge_type": "use_case_comparison",
      "rationale": "Użytkownicy rozważający gaming często potrzebują też funkcji biznesowych"
    }}
  ]
}}

KRYTYCZNE: Używaj DOKŁADNYCH url_path z listy wyżej!
"""

            # DEBUG: Strategic AI prompt + inputs
            logger.info(f"🤖 [STRATEGIC_AI] Prompt preview: {prompt[:200]}...")
            logger.info(f"🤖 [STRATEGIC_AI] Input pages count: {len(pages_summary)}")
            logger.info(f"🤖 [STRATEGIC_AI] First 3 pages: {[p.get('name') for p in pages_summary[:3]]}")

            try:
                response = self.call_llm_with_timeout(prompt, timeout=90)
                if response.startswith("```json"):
                    response = response.replace("```json", "").replace("```", "").strip()
                response = response.strip()
                ai_result = json.loads(response)
                bridges = ai_result.get('strategic_bridges', [])
                logger.info(f"🤖 [AI_BRIDGES] AI wygenerował {len(bridges)} strategic bridges")
                for i, bridge in enumerate(bridges):
                    logger.info(f"🤖 [AI_BRIDGES] Bridge {i+1}: {bridge.get('from_url', '')} → {bridge.get('to_url', '')} | anchor: {bridge.get('suggested_anchor', '')[:50]}...")
                # DEBUG: Strategic AI response summary
                logger.info(f"🤖 [STRATEGIC_RESPONSE] Bridges count: {len(bridges)}")
                for i, bridge in enumerate(bridges[:3]):
                    logger.info(f"🤖 [STRATEGIC_RESPONSE] Bridge {i+1}: {bridge.get('from_url', '')} → {bridge.get('to_url', '')} | anchor: {bridge.get('suggested_anchor', '')[:50]}...")
                return bridges
            except json.JSONDecodeError as e:
                logger.error(f"❌ [AI_BRIDGES] JSON parse error: {e}")
                return []
        except Exception as e:
            logger.error(f"❌ [AI_BRIDGES] Strategic bridges generation failed: {e}")
            return []

    def _extract_category_from_url(self, url_path: str) -> str:
        """Helper: wyciągnij główną kategorię z URL"""
        parts = (url_path or '').strip('/').split('/')
        return parts[1] if len(parts) > 1 else (parts[0] if parts else '')
    
    def calculate_cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """PRAWDZIWA implementacja cosine similarity"""
        try:
            # Convert to numpy arrays
            a = np.array(vec1, dtype=np.float32)
            b = np.array(vec2, dtype=np.float32)
            
            # Handle edge cases
            if len(a) == 0 or len(b) == 0:
                return 0.0
            
            if len(a) != len(b):
                logger.warning(f"⚠️ [SIMILARITY] Vector dimension mismatch: {len(a)} vs {len(b)}")
                return 0.0
            
            # Calculate cosine similarity
            dot_product = np.dot(a, b)
            norm_a = np.linalg.norm(a)
            norm_b = np.linalg.norm(b)
            
            if norm_a == 0 or norm_b == 0:
                return 0.0
            
            similarity = dot_product / (norm_a * norm_b)
            
            # Normalize to [0, 1] range (cosine similarity is [-1, 1])
            normalized = (similarity + 1.0) / 2.0
            
            # Clamp to valid range
            return float(max(0.0, min(1.0, normalized)))
            
        except Exception as e:
            logger.error(f"❌ [SIMILARITY] Calculation failed: {str(e)}")
            return 0.0
    
    def analyze_semantic_relationship(self, group_a: Dict, group_b: Dict, similarity: float) -> Dict:
        """Analizuje semantyczny związek między grupami dla lepszego bridge reasoning"""
        
        name_a = group_a['name'].lower()
        name_b = group_b['name'].lower()
        
        phrases_a = [p.lower() for p in group_a.get('phrases', [])]
        phrases_b = [p.lower() for p in group_b.get('phrases', [])]
        
        analysis = {
            "bridge_worthy": True,
            "relationship_type": "semantic",
            "rationale": "",
            "strength": "medium"
        }
        
        # Detect relationship patterns
        
        # 1. Cost-Quality relationship
        if (any(word in name_a for word in ['koszt', 'cena', 'tani']) and 
            any(word in name_b for word in ['jakość', 'najlepsze', 'dobór', 'porównanie'])):
            analysis.update({
                "relationship_type": "cost_quality",
                "rationale": f"Użytkownicy porównujący {name_a} potrzebują informacji o {name_b}",
                "strength": "strong"
            })
        
        # 2. Location-Service relationship  
        elif (any(phrase for phrase in phrases_a if any(city in phrase for city in ['warszawa', 'kraków', 'gdańsk', 'poznań'])) and
              any(word in name_b for word in ['instalacja', 'serwis', 'montaż', 'usługa'])):
            analysis.update({
                "relationship_type": "location_service",
                "rationale": f"Lokalni klienci z {name_a} szukają {name_b} w swojej okolicy",
                "strength": "strong"
            })
        
        # 3. Product-Brand relationship
        elif (any(word in name_a for word in ['marka', 'producent', 'firma']) and
              any(word in name_b for word in ['model', 'typ', 'rodzaj', 'specyfikacja'])):
            analysis.update({
                "relationship_type": "brand_product",
                "rationale": f"Użytkownicy wybierający {name_a} potrzebują szczegółów o {name_b}",
                "strength": "strong"
            })
        
        # 4. Problem-Solution relationship
        elif (any(word in name_a for word in ['problem', 'błąd', 'awaria', 'wada']) and
              any(word in name_b for word in ['rozwiązanie', 'naprawa', 'serwis', 'pomoc'])):
            analysis.update({
                "relationship_type": "problem_solution",
                "rationale": f"Użytkownicy z {name_a} szukają {name_b}",
                "strength": "very_strong"
            })
        
        # 5. Feature-Benefit relationship
        elif similarity > 0.8:
            analysis.update({
                "relationship_type": "high_similarity",
                "rationale": f"Wysokie podobieństwo semantyczne ({similarity:.3f}) wskazuje na powiązane potrzeby użytkowników",
                "strength": "strong"
            })
        
        # 6. Weak relationship - might not be worth bridging
        elif similarity < 0.72:
            analysis.update({
                "bridge_worthy": False,
                "relationship_type": "weak_semantic",
                "rationale": f"Zbyt niskie podobieństwo semantyczne ({similarity:.3f}) dla bridge",
                "strength": "weak"
            })
        
        return analysis
    
    def generate_smart_anchor_text(self, from_group: Dict, to_group: Dict, relationship: Dict) -> str:
        """Generuje inteligentny anchor text na podstawie semantic relationship"""
        
        to_name = to_group['name'].lower()
        relationship_type = relationship.get('relationship_type', 'semantic')
        
        # Template based on relationship type
        templates = {
            "cost_quality": [
                f"jak wybrać {to_name}",
                f"najlepsze {to_name}",
                f"porównanie {to_name}"
            ],
            "location_service": [
                f"{to_name} w twojej okolicy", 
                f"gdzie znaleźć {to_name}",
                f"lokalny {to_name}"
            ],
            "brand_product": [
                f"modele {to_name}",
                f"typy {to_name}",
                f"wybór {to_name}"
            ],
            "problem_solution": [
                f"jak rozwiązać problem z {to_name}",
                f"pomoc przy {to_name}",
                f"rozwiązanie problemów {to_name}"
            ],
            "high_similarity": [
                f"więcej o {to_name}",
                f"szczegóły {to_name}",
                f"wszystko o {to_name}"
            ]
        }
        
        # Get appropriate templates
        anchor_options = templates.get(relationship_type, templates["high_similarity"])
        
        # Return first template (can be randomized in future)
        return anchor_options[0]
    
    def determine_link_placement(self, relationship: Dict) -> List[str]:
        """Określa optymalne miejsca dla linków na podstawie relationship strength"""
        
        strength = relationship.get('strength', 'medium')
        
        if strength == "very_strong":
            return ["content_intro", "mid_content", "conclusion"]
        elif strength == "strong":
            return ["mid_content", "conclusion"]  
        else:
            return ["mid_content"]
    
    def calculate_bridge_priority(self, similarity: float, relationship: Dict) -> int:
        """Oblicza priorytet bridge na podstawie similarity i business logic"""
        
        base_priority = int(similarity * 100)
        
        # Boost for strong business relationships
        strength_boost = {
            "very_strong": 20,
            "strong": 15,
            "medium": 10,
            "weak": 0
        }
        
        strength = relationship.get('strength', 'medium')
        final_priority = base_priority + strength_boost.get(strength, 10)
        
        return min(final_priority, 100)  # Cap at 100
    
    def generate_implementation_notes(self) -> Dict:
        """📝 Generuje praktyczne notatki implementacyjne"""
        logger.info("📝 [IMPLEMENTATION] Generuję notatki implementacyjne...")
        
        return {
            "wordpress_tips": [
                "Użyj Custom Post Types dla różnych typów stron (pillar, category, cluster)",
                "Zainstaluj Yoast SEO lub RankMath dla breadcrumbs i structured data",
                "Stwórz custom menu structure odpowiadający hierarchii",
                "Użyj kategorii WordPress do grupowania treści zgodnie z architekturą",
                "Skonfiguruj permalinki jako /%category%/%postname%/ dla SEO"
            ],
            "technical_seo": [
                "Dodaj structured data (BreadcrumbList, Organization, WebSite)",
                "Optymalizuj internal link equity flow - więcej linków do ważniejszych stron",
                "Monitor crawl depth - maksymalnie 3 kliki od strony głównej",
                "Stwórz XML sitemap zgodny z hierarchią architektury",
                "Zaimplementuj canonical URLs dla każdej strony",
                "Dodaj Open Graph i Twitter Card meta tags"
            ],
            "content_strategy": [
                "Pillar page = comprehensive, 3000+ słów, hub dla całej tematyki",
                "Category pages = hub pages, 1500-2000 słów, linkują do subpages", 
                "Cluster pages = specific, long-tail optimized, 1200+ słów",
                "Użyj target keywords w title, H1, meta description każdej strony",
                "Stwórz content calendar oparty na hierarchii architektury",
                "Regularnie aktualizuj pillar page nowymi linkami do subpages"
            ]
        }
    
    def generate_seo_recommendations(self, url_structure: Dict) -> Dict:
        """📈 Generuje rekomendacje SEO"""
        logger.info("📈 [SEO] Generuję rekomendacje SEO...")
        
        total_pages = self.count_total_pages(url_structure)
        max_depth = self.calculate_max_depth(url_structure)
        
        recommendations = {
            "on_page_seo": [
                f"Optymalizuj {total_pages} stron pod kątem target keywords",
                "Każda strona powinna mieć unikalny title tag (50-60 znaków)",
                "Meta descriptions 150-160 znaków z call-to-action",
                "Użyj H1-H6 headers zgodnie z hierarchią treści",
                "Alt text dla wszystkich obrazów z target keywords"
            ],
            "internal_linking": [
                "Implementuj breadcrumbs na wszystkich stronach",
                "Strategic cross-linking między powiązanymi klastrami",
                "Anchor text powinien zawierać target keywords",
                "Linkuj z pillar page do wszystkich category pages",
                "Każda subpage powinna linkować 'w górę' hierarchii"
            ],
            "technical_optimization": [
                f"Maksymalna głębokość {max_depth} poziomów - optymalna dla crawlingu",
                "URLs przyjazne SEO bez polskich znaków",
                "Responsive design dla wszystkich urządzeń",
                "Page speed optimization - cel < 3 sekundy",
                "SSL certificate i HTTPS dla całej witryny"
            ],
            "content_guidelines": [
                "Pillar page jako comprehensive resource (3000+ słów)",
                "Category pages jako topic clusters (1500+ słów)",
                "Cluster pages zoptymalizowane pod long-tail keywords",
                "Regularne aktualizacje treści (monthly/quarterly)",
                "User-generated content w komentarzach i reviews"
            ]
        }
        
        return recommendations
    
    def calculate_seo_score(self, url_structure: Dict, internal_linking: Dict, strategic_bridges: List[Dict]) -> int:
        """📊 Oblicza SEO score na podstawie best practices"""
        
        score = 0
        max_score = 100
        
        # URL Structure (25 points)
        if url_structure.get('pillar_page'):
            score += 10  # Has pillar page
        
        total_pages = self.count_total_pages(url_structure)
        if 5 <= total_pages <= 50:
            score += 10  # Reasonable number of pages
        elif total_pages > 50:
            score += 5   # Too many pages penalty
        
        max_depth = self.calculate_max_depth(url_structure)
        if max_depth <= 3:
            score += 5   # Good depth
        
        # Internal Linking (25 points)
        vertical_links = len(internal_linking.get('vertical_linking', []))
        if vertical_links > 0:
            score += 15  # Has vertical linking
        
        if vertical_links >= total_pages:
            score += 10  # Comprehensive linking
        
        # Strategic Bridges (25 points)
        if strategic_bridges:
            score += 15  # Has strategic bridges
            
            avg_similarity = float(np.mean([b.get('similarity_score', 0) for b in strategic_bridges]))
            if avg_similarity > 0.75:
                score += 10  # High quality bridges
        
        # Architecture Quality (25 points)
        if len(self.groups) >= 5:
            score += 10  # Good number of clusters
        
        if any(g.get('embeddings_available', False) for g in self.groups):
            score += 10  # Uses embeddings
        
        if self.arch_type == 'clusters' and strategic_bridges:
            score += 5   # Implements advanced features
        
        return min(score, max_score)
    
    # Utility methods
    def count_total_pages(self, url_structure: Dict) -> int:
        """Liczy całkowitą liczbę stron w architekturze"""
        count = 1  # Pillar page
        for category in url_structure.get('categories', []):
            count += 1  # Category page
            count += len(category.get('subcategories', []))
            count += len(category.get('standalone_pages', []))
        return count
    
    def calculate_max_depth(self, url_structure: Dict) -> int:
        """Oblicza maksymalną głębokość architektury"""
        max_depth = 1  # Pillar = depth 0, categories = depth 1
        for category in url_structure.get('categories', []):
            if category.get('subcategories') or category.get('standalone_pages'):
                max_depth = 2
                break
        return max_depth

    async def identify_hierarchy_with_retry(self) -> Dict:
        """LLM hierarchy identification with fallback logic"""
        max_retries = 2
        for attempt in range(max_retries + 1):
            try:
                logger.info(f"🤖 [HIERARCHY] Próba {attempt + 1}/{max_retries + 1}")
                if attempt == 0:
                    # Primary attempt with Claude (if available)
                    return await self.identify_hierarchy()
                elif attempt == 1:
                    # Retry with simplified prompt or OpenAI
                    return await self.identify_hierarchy_simplified()
                else:
                    # Final fallback: deterministic hierarchy
                    logger.warning("⚠️ [HIERARCHY] LLM zawodne, używam deterministycznej hierarchii")
                    return self.create_fallback_hierarchy()
            except Exception as e:
                logger.warning(f"⚠️ [HIERARCHY] Próba {attempt + 1} nieudana: {str(e)}")
                if attempt == max_retries:
                    raise

    async def identify_hierarchy(self) -> Dict:
        """🔥 Używa LLM do identyfikacji hierarchii w klastrach - ENHANCED VERSION"""
        # Przygotuj dane dla LLM z dodatkowymi informacjami
        groups_summary = []
        for group in self.groups:
            groups_summary.append({
                "name": group['name'],
                "phrase_count": group.get('phrase_count', len(group.get('phrases', []))),
                "example_phrases": group.get('phrases', [])[:3],  # Top 3 phrases
                "similarity_score": group.get('similarity_score', 0.85),
                "has_embeddings": group.get('embeddings_available', False),
                "group_context": self.analyze_group_context(group)  # Business context
            })
        prompt = f"""
Jesteś ekspertem SEO i architektury informacji. Zbuduj ARCHITEKTURĘ URL maksymalizującą: (1) odkrywalność SEO, (2) ekstrahowalność przez AI Overviews (jednowątkowe tematy), (3) nawigację użytkownika. Pracuj WYŁĄCZNIE na podanych klastrach – nie wymyślaj nowych stron.

SEED: "{self.seed_keyword}"
KLASTRY ({len(groups_summary)} grup, {sum(g['phrase_count'] for g in groups_summary)} fraz):
{json.dumps(groups_summary, indent=2, ensure_ascii=False)}

UNIWERSALNE ZASADY KLASTROWANIA (deterministyczne):
1) Pokrycie: każdy klaster musi być przypisany DOKŁADNIE raz – jako sub_category albo jako standalone_cluster w jednej z main_categories.
2) Liczba kategorii: 2–5 main_categories. Kandydaci = duże klastry (>=10 fraz) + grupy o wysokiej wartości biznesowej.
3) Mapowanie oparte na intencji i lejku:
   - Awareness/educational → „podstawy/poradniki"
   - Consideration/comparison_focused → „porównania, rankingi, recenzje"
   - Decision/pricing_focused, commercial/transactional → „zakup/oferta"
   - Local_seo → „landing pages" w decyzji lokalnej
   Jeśli klaster pasuje do kilku miejsc, zastosuj tie-breakers: (a) większy phrase_count, (b) większa przybliżona wartość komercyjna wywnioskowana z group_context, (c) większa jednowątkowość (lepsza dla AIO).
4) AIO/Ai Overviews: strony mają być jednowątkowe – nie łącz niespokrewnionych tematów w jedną podstronę.
5) Intent i priorytet:
   - Każda main_category musi mieć "intent": informational/commercial/local/transactional.
   - "priority": 1 = najwyższy. Sortuj kategorie wg wartości biznesowej: transactional > commercial > local > informational. Przy remisie sortuj malejąco po łącznym phrase_count (sub_categories + standalone).
6) Reguły URL (2024/2025) - ANTY-KEYWORD STUFFING:
   - Slugi ASCII (bez polskich znaków), małe litery, myślniki.
   - Unikalne slugi w całej hierarchii.
ANTY-STUFFING RULES (KRYTYCZNE):
   - SEED KEYWORD pojawia się TYLKO w pillar URL, NIE w podstronach
   - Każdy segment URL może zawierać MAX 1 główny keyword z klastra
   - Zakazane powtarzanie słów między segmentami tej samej ścieżki
   - Priorytet dla brandów, typów, kategorii zamiast keyword repetition
   - url nie mogą być keywords STUFFING - url muszą być zupełnie natuarlne dla człowieka ale i robota google. Badź naturalny.
DŁUGOŚĆ LIMITS:
   - PILLAR: 15-25 znaków (np. /kredyt-hipoteczny/)
   - CATEGORY: 15-30 znaków (np. /banki/, /porownania/, /kalkulator/)
   - SUBCATEGORY: 20-40 znaków (np. /pko-bp/, /zdolnosc-kredytowa/)
   - MAX TOTAL PATH: 80 znaków
DOBRE PRZYKŁADY:
   - /kredyt-hipoteczny/banki/pko-bp/
   - /kredyt-hipoteczny/porownania/ranking-2025/
   - /kredyt-hipoteczny/kalkulator/rata-miesięczna/
   ZŁE PRZYKŁADY (keyword stuffing):
   - /kredyt-hipoteczny/kredyt-bankowy/kredyt-pko-hipoteczny/
   - /kredyt/kredyt-hipoteczny-oferty/kredyt-hipoteczny-pko-kalkulator/
   - Jakiekolwiek powtarzanie root keyword w podścieżkach
   OPTYMALIZACJA dla AIO:
   - Używaj semantic variations zamiast exact match repetition
   - Kategorie = nouns (banki, kalkulator, ranking)
   - Subcategories = specific entities (pko-bp, santander, ing)
   - Unikaj compound keywords w URL jeśli nie są naturalne
7) Zakazy:
   - Nie twórz nowych klastrów/stron.
   - Nie zmieniaj nazw w "cluster_name" – muszą idealnie odpowiadać wejściowym nazwom grup.
   - Nie używaj markdownu ani komentarzy. Zwróć wyłącznie CZYSTY JSON.
8) Kontrola jakości PRZED zwrotem:
   - Suma unikalnych "cluster_name" w sub_categories + standalone_clusters == {len(groups_summary)}.
   - 0 duplikatów "cluster_name".
   - 2–5 main_categories.
   - Wszystkie slugi unikalne i zgodne z zasadami.
      - ZERO powtórzeń seed keyword poza pillar URL
   - Każdy segment URL semantycznie unikalny w swojej ścieżce
   - Całkowita długość ścieżki URL < 80 znaków
   - Brak compound keywords stuffing (max 1 keyword per segment)
   9) URL SEMANTIC DIVERSITY (anty-stuffing enforcement):
   - Każdy poziom hierarchii używa RÓŻNYCH słów z pola semantycznego
   - Level 1 (pillar): seed keyword
   - Level 2 (category): semantic category 
   - Level 3 (subcategory): specific entity/aspect 
   - ZERO tolerance dla keyword echo w tej samej ścieżce URL

ODPOWIEDŹ – DOKŁADNIE TEN JSON (bez zbędnych pól na górze, bez markdownu):
{{
  "pillar": {{
    "name": "Nazwa głównego tematu",
    "url_slug": "krotki-pillar-slug",
    "description": "Dlaczego to pillar",
    "target_intent": "informational",
    "estimated_word_count": 3000
  }},
  "main_categories": [
    {{
      "name": "Nazwa kategorii",
      "url_slug": "kategoria-slug",
      "description": "Logika biznesowa tej kategorii",
      "intent": "informational/commercial/local/transactional",
      "priority": 1,
      "sub_categories": [
        {{
          "name": "Nazwa subkategorii",
          "url_slug": "sub-slug",
          "cluster_name": "Dokładna nazwa z listy klastrów",
          "estimated_word_count": 1500
        }}
      ],
      "standalone_clusters": [
        {{
          "name": "Klaster bez subkategorii",
          "url_slug": "klaster-slug",
          "cluster_name": "Dokładna nazwa z listy klastrów",
          "estimated_word_count": 1200
        }}
      ]
    }}
  ]
}}
"""
        try:
            response = self.call_llm_with_timeout(prompt, timeout=120)
            if response.startswith("```json"):
                response = response.replace("```json", "").replace("```", "").strip()
            hierarchy = json.loads(response)
            self.validate_hierarchy(hierarchy)
            logger.info(f"✅ [HIERARCHY] LLM hierarchy: {len(hierarchy.get('main_categories', []))} głównych kategorii")
            
            # NEW: Enhance hierarchy with real intent data
            enhanced_hierarchy = await self._enhance_hierarchy_with_intent(hierarchy)
            return enhanced_hierarchy
        except json.JSONDecodeError as e:
            logger.error(f"❌ [HIERARCHY] LLM zwróciło nieprawidłowy JSON: {str(e)}")
            logger.debug(f"LLM Response: {response[:500]}...")
            raise
        except Exception as e:
            logger.error(f"❌ [HIERARCHY] Generowanie hierarchii nie powiodło się: {str(e)}")
            raise

    def identify_hierarchy_simplified(self) -> Dict:
        """Uproszczona wersja hierarchii gdy główna zawiedzie"""
        logger.info("🔄 [HIERARCHY] Próbuję uproszczoną wersję...")
        prompt = f"""
Zbuduj uproszczoną architekturę URL dla tematu "{self.seed_keyword}". Użyj WYŁĄCZNIE poniższych klastrów i przypisz każdy DOKŁADNIE raz (do "sub_categories" lub "standalone_clusters"). Nie twórz nowych klastrów i nie zmieniaj ich nazw.

KLASTRY ({len(self.groups)}):
{json.dumps([g['name'] for g in self.groups], ensure_ascii=False, indent=2)}

Wymagania:
- 2–5 "main_categories".
- Slugi ASCII, małe litery, myślniki; unikalne w całej hierarchii.
- Zachowaj dokładne wartości w polu "cluster_name" z listy powyżej.

Zwróć wyłącznie CZYSTY JSON dokładnie w tym schemacie (te same klucze jak w modelu głównym):
{{
  "pillar": {{
    "name": "{self.seed_keyword.title()}",
    "url_slug": "{self.generate_slug(self.seed_keyword)}",
    "description": "Pillar dla całego tematu",
    "target_intent": "informational",
    "estimated_word_count": 3000
  }},
  "main_categories": [
    {{
      "name": "Nazwa kategorii",
      "url_slug": "kategoria-slug",
      "description": "Opis/logika biznesowa kategorii",
      "intent": "informational/commercial/local/transactional",
      "priority": 1,
      "sub_categories": [
        {{
          "name": "Nazwa subkategorii",
          "url_slug": "sub-slug",
          "cluster_name": "Dokładna nazwa z listy klastrów",
          "estimated_word_count": 1500
        }}
      ],
      "standalone_clusters": [
        {{
          "name": "Nazwa strony klastrowej",
          "url_slug": "klaster-slug",
          "cluster_name": "Dokładna nazwa z listy klastrów",
          "estimated_word_count": 1200
        }}
      ]
    }}
  ]
}}
"""
        try:
            response = self.call_llm_with_timeout(prompt, timeout=60, use_openai=True)
            hierarchy = json.loads(response.replace("```json", "").replace("```", "").strip())
            logger.info("✅ [HIERARCHY] Uproszczona hierarchia utworzona")
            return hierarchy
        except Exception as e:
            logger.error(f"❌ [HIERARCHY] Uproszczona wersja też nie powiodła się: {str(e)}")
            raise

    def create_fallback_hierarchy(self) -> Dict:
        """Deterministyczna hierarchia gdy LLM zawiedzie"""
        logger.info("🔄 [HIERARCHY] Tworzę deterministyczną hierarchię...")
        pillar_name = self.seed_keyword.title()
        pillar_slug = self.generate_slug(pillar_name)
        sorted_groups = sorted(self.groups, key=lambda g: g.get('phrase_count', 0), reverse=True)
        main_categories = []
        for i, group in enumerate(sorted_groups[:5]):  # Max 5 main categories
            main_categories.append({
                "name": group['name'],
                "url_slug": self.generate_slug(group['name']),
                "description": f"Auto-generated category for {group['name']}",
                "intent": self.guess_intent(group),
                "priority": i + 1,
                "standalone_clusters": [{
                    "name": group['name'],
                    "url_slug": self.generate_slug(group['name']),
                    "cluster_name": group['name'],
                    "estimated_word_count": 1200
                }],
                "sub_categories": []
            })
        fallback_hierarchy = {
            "pillar": {
                "name": pillar_name,
                "url_slug": pillar_slug,
                "description": f"Comprehensive guide about {pillar_name}",
                "target_intent": "informational",
                "estimated_word_count": 3000
            },
            "main_categories": main_categories
        }
        logger.info("✅ [HIERARCHY] Deterministyczna hierarchia utworzona")
        return fallback_hierarchy

    def analyze_group_context(self, group: Dict) -> str:
        """Analizuje kontekst biznesowy grupy dla lepszej kategoryzacji"""
        phrases = group.get('phrases', [])
        name = group.get('name', '').lower()
        contexts = []
        if any(word in name for word in ['cena', 'koszt', 'tani', 'drogi', 'ile kosztuje']):
            contexts.append("pricing_focused")
        if any(word in name for word in ['opinie', 'recenzje', 'najlepsze', 'porównanie']):
            contexts.append("comparison_focused")
        polish_cities = ['warszawa', 'kraków', 'gdańsk', 'poznań', 'wrocław', 'łódź', 'szczecin', 'bydgoszcz', 'lublin', 'katowice']
        if any(phrase for phrase in phrases if any(city in phrase.lower() for city in polish_cities)):
            contexts.append("local_seo")
        if any(word in name for word in ['jak', 'dlaczego', 'co to', 'schemat', 'działanie']):
            contexts.append("educational")
        if any(word in name for word in ['marki', 'producenci', 'firma', 'sklep']):
            contexts.append("commercial")
        return ", ".join(contexts) if contexts else "general"

    def call_llm_with_timeout(self, prompt: str, timeout: int = 60, use_openai: bool = False) -> str:
        """Wywołanie LLM z pełnym fallbackiem (gpt5/openai/claude) zgodnie z AI_PROVIDER."""
        # Ustal kolejność providerów
        if use_openai:
            providers_order = ['openai', 'gpt5', 'claude']
        else:
            primary = (self.ai_provider or 'openai')
            all_providers = ['gpt5', 'openai', 'claude']
            providers_order = [primary] + [p for p in all_providers if p != primary]

        def _call_gpt5() -> str:
            if not getattr(self, 'openai_client', None):
                raise RuntimeError("OpenAI client (for GPT-5) unavailable")
            logger.info(f"🤖 [LLM] Wywołanie GPT-5 (model={self.gpt5_model}, effort={self.gpt5_reasoning_effort}, verbosity={self.gpt5_verbosity})…")
            # 🔍 DEBUG REQUEST (GPT-5)
            request_data = {
                "model": self.gpt5_model,
                "input": [{
                    "role": "user",
                    "content": [{"type": "input_text", "text": prompt}]
                }],
                "max_output_tokens": 64000,
                "reasoning": {"effort": "low"},
                "text": {"verbosity": self.gpt5_verbosity}
            }
            try:
                logger.info(f"🚀 [GPT5_REQUEST] Model: {self.gpt5_model}")
                logger.info(f"🚀 [GPT5_REQUEST] Reasoning effort: {self.gpt5_reasoning_effort}")
                logger.info(f"🚀 [GPT5_REQUEST] Verbosity: {self.gpt5_verbosity}")
                logger.info(f"🚀 [GPT5_REQUEST] Max tokens: 64000")
                logger.info(f"🚀 [GPT5_REQUEST] Prompt length: {len(prompt)} chars")
                logger.info(f"🚀 [GPT5_REQUEST] Prompt first 500 chars: {prompt[:500]}")
                logger.info(f"🚀 [GPT5_REQUEST] Prompt last 200 chars: {prompt[-200:]}")
                logger.info(f"🚀 [GPT5_REQUEST] Complete request structure: {request_data}")
            except Exception:
                pass

            response = self.openai_client.responses.create(**request_data)

            # 🔍 DEBUG RESPONSE (GPT-5)
            try:
                logger.info(f"🔍 [GPT5_RESPONSE] Response type: {type(response)}")
                logger.info(f"🔍 [GPT5_RESPONSE] Response ID: {getattr(response, 'id', 'No ID')}")
                logger.info(f"🔍 [GPT5_RESPONSE] Model used: {getattr(response, 'model', 'No model')}")
                logger.info(f"🔍 [GPT5_RESPONSE] Status: {getattr(response, 'status', 'No status')}")
                logger.info(f"🔍 [GPT5_RESPONSE] Has output_text: {hasattr(response, 'output_text')}")
                if hasattr(response, 'output_text'):
                    logger.info(f"🔍 [GPT5_RESPONSE] output_text type: {type(response.output_text)}")
                    logger.info(f"🔍 [GPT5_RESPONSE] output_text is None: {response.output_text is None}")
                    logger.info(f"🔍 [GPT5_RESPONSE] output_text repr: {repr(response.output_text)}")
                    if response.output_text:
                        ot = str(response.output_text)
                        logger.info(f"🔍 [GPT5_RESPONSE] output_text length: {len(ot)}")
                        logger.info(f"🔍 [GPT5_RESPONSE] output_text first 500 chars: {ot[:500]}")
                logger.info(f"🔍 [GPT5_RESPONSE] Has output: {hasattr(response, 'output')}")
                if hasattr(response, 'output'):
                    logger.info(f"🔍 [GPT5_RESPONSE] output type: {type(getattr(response, 'output', None))}")
                    logger.info(f"🔍 [GPT5_RESPONSE] output is None: {getattr(response, 'output', None) is None}")
                    out = getattr(response, 'output', None)
                    if out:
                        logger.info(f"🔍 [GPT5_RESPONSE] output length: {len(out)}")
                        if len(out) > 0:
                            logger.info(f"🔍 [GPT5_RESPONSE] output[0] type: {type(out[0])}")
                            logger.info(f"🔍 [GPT5_RESPONSE] output[0] dir: {dir(out[0])}")
                            if hasattr(out[0], 'content'):
                                logger.info(f"🔍 [GPT5_RESPONSE] output[0].content: {out[0].content}")
                if hasattr(response, 'usage'):
                    logger.info(f"🔍 [GPT5_RESPONSE] Usage: {response.usage}")
                if hasattr(response, 'error'):
                    logger.info(f"🔍 [GPT5_RESPONSE] Error: {response.error}")
                logger.info(f"🔍 [GPT5_RESPONSE] COMPLETE RESPONSE DUMP:")
                logger.info(f"🔍 [GPT5_RESPONSE] {response}")
            except Exception:
                pass

            # 🔢 Token usage diagnostics
            try:
                usage = getattr(response, 'usage', None)
                if usage is not None:
                    details = getattr(usage, 'output_tokens_details', None)
                    reasoning_tokens = getattr(details, 'reasoning_tokens', 0) if details is not None else 0
                    total_output = getattr(usage, 'output_tokens', None)
                    logger.info(f"🔢 [GPT5] Tokens used: reasoning={reasoning_tokens}, total_output={total_output}")
                    try:
                        if total_output and reasoning_tokens >= float(total_output) * 0.95:
                            logger.warning(f"⚠️ [GPT5] Reasoning consumed {reasoning_tokens}/{total_output} tokens - consider increasing max_output_tokens or reducing reasoning effort")
                    except Exception:
                        pass
            except Exception:
                pass

            ai_response = None
            if hasattr(response, 'output_text') and getattr(response, 'output_text') and str(getattr(response, 'output_text')).strip():
                ai_response = str(response.output_text)
                try:
                    logger.info(f"✅ [GPT5_RESPONSE] SUCCESS: Używam output_text, length: {len(ai_response)}")
                    logger.info(f"🎉 [GPT5_RESPONSE] First 300 chars: {ai_response[:300]}")
                except Exception:
                    pass
            elif hasattr(response, 'output') and getattr(response, 'output'):
                out = getattr(response, 'output')
                if len(out) > 0 and hasattr(out[0], 'content') and out[0].content:
                    first_content = out[0].content[0] if len(out[0].content) > 0 else None
                    if first_content is not None and hasattr(first_content, 'text'):
                        ai_response = first_content.text
                        try:
                            logger.info(f"✅ [GPT5_RESPONSE] SUCCESS: Używam output[0].content[0].text, length: {len(ai_response)}")
                        except Exception:
                            pass
            if not ai_response:
                logger.error(f"❌ [GPT5_RESPONSE] ALL EXTRACTION METHODS FAILED")
                raise Exception("Cannot extract text from GPT-5 response after all attempts")
            return ai_response

        def _call_openai() -> str:
            if not getattr(self, 'openai_client', None):
                raise RuntimeError("OpenAI client unavailable")
            logger.info(f"🤖 [LLM] Wywołanie OpenAI (model={self.openai_model})…")
            response = self.openai_client.chat.completions.create(
                model=self.openai_model,
                messages=[{"role": "user", "content": prompt}],
                temperature=0.3,
                max_tokens=4096,
            )
            return response.choices[0].message.content

        def _call_claude() -> str:
            if not getattr(self, 'claude_client', None):
                raise RuntimeError("Claude client unavailable")
            logger.info(f"🤖 [LLM] Wywołanie Claude (model={self.claude_model})…")
            response = self.claude_client.messages.create(
                model=self.claude_model,
                max_tokens=4096,
                temperature=0.3,
                messages=[{"role": "user", "content": prompt}]
            )
            return response.content[0].text

        errors: list[str] = []
        for provider in providers_order:
            try:
                if provider == 'gpt5':
                    result = _call_gpt5()
                elif provider == 'openai':
                    result = _call_openai()
                else:
                    result = _call_claude()
                logger.info(f"✅ [LLM] {provider.upper()} odpowiedział")
                return result
            except Exception as e:
                errors.append(f"{provider}:{e}")
                logger.warning(f"⚠️ [LLM] {provider.upper()} nieudane: {e}")

        logger.error(f"❌ [LLM] Wszyscy providerzy zawiedli: {'; '.join(errors)}")
        raise Exception("Brak dostępnych klientów LLM")

    def guess_intent(self, group: Dict) -> str:
        """Heurystyczna identyfikacja intencji gdy LLM zawiedzie"""
        name = group.get('name', '').lower()
        phrases = [p.lower() for p in group.get('phrases', [])]
        if any(word in name for word in ['cena', 'koszt', 'tani', 'sklep', 'promocja']):
            return "commercial"
        polish_cities = ['warszawa', 'kraków', 'gdańsk', 'poznań', 'wrocław', 'łódź']
        if any(phrase for phrase in phrases if any(city in phrase for city in polish_cities)):
            return "local"
        if any(word in name for word in ['kup', 'zamów', 'oferta', 'sprzedaż']):
            return "transactional"
        return "informational"

    def validate_hierarchy(self, hierarchy: Dict):
        """Waliduje strukturę hierarchii z LLM"""
        if not hierarchy.get('pillar'):
            raise ValueError("Brak pillar w hierarchii")
        if not hierarchy.get('main_categories'):
            raise ValueError("Brak main_categories w hierarchii")
        pillar = hierarchy['pillar']
        if not pillar.get('name') or not pillar.get('url_slug'):
            raise ValueError("Niepełne dane pillar (name, url_slug)")
        for cat in hierarchy['main_categories']:
            if not cat.get('name') or not cat.get('url_slug'):
                raise ValueError(f"Niepełne dane kategorii: {cat}")
        logger.info("✅ [HIERARCHY] Walidacja hierarchii przeszła pomyślnie")

    def update_page_relationships_enhanced(self, architecture_id: str, pages_data: List[Dict]):
        """Enhanced relationship updates with better parent-child mapping"""
        try:
            # Find pillar page
            pillar_page = next((p for p in pages_data if p.get('page_type') == 'pillar'), None)
            
            if not pillar_page:
                logger.warning(f"⚠️ [DATABASE] No pillar page found for architecture {architecture_id}")
                return
            
            # Update all non-pillar pages to have pillar as parent
            updates = []
            for page in pages_data:
                if page.get('page_type') != 'pillar':
                    updates.append({
                        'id': page['id'],
                        'parent_page_id': pillar_page['id']
                    })
            
            # Batch update parent relationships
            if updates:
                for update in updates:
                    self.supabase.table('architecture_pages').update({
                        'parent_page_id': update['parent_page_id']
                    }).eq('id', update['id']).execute()
                
                logger.info(f"✅ [DATABASE] Updated {len(updates)} parent relationships")
        
        except Exception as e:
            logger.error(f"❌ [DATABASE] Failed to update page relationships: {e}")

    def find_parent_category(self, sub_page: Dict, categories: List[Dict]) -> Optional[Dict]:
        """Find best parent category for sub-page based on semantic similarity"""
        sub_url = sub_page.get('url_path', '')
        sub_name = sub_page.get('name', '').lower()
        
        best_match = None
        best_score = 0
        
        for category in categories:
            cat_url = category.get('url_path', '')
            cat_name = category.get('name', '').lower()
            
            # Simple scoring based on URL and name similarity
            score = 0
            
            # URL containment check
            if cat_url in sub_url and cat_url != sub_url:
                score += 3
            
            # Name similarity check
            cat_words = set(cat_name.split())
            sub_words = set(sub_name.split())
            common_words = cat_words.intersection(sub_words)
            if common_words:
                score += len(common_words)
            
            if score > best_score:
                best_score = score
                best_match = category
        
        return best_match

    async def _get_cluster_intent_data(self, cluster_name: str, semantic_cluster_id: str) -> Dict:
        """Get real intent data for cluster from semantic_groups"""
        try:
            intent_query = self.supabase.table('semantic_groups').select(
                'intent_data'
            ).eq('semantic_cluster_id', semantic_cluster_id).eq('group_label', cluster_name).execute()
            
            if intent_query.data and intent_query.data[0].get('intent_data'):
                intent_data = intent_query.data[0]['intent_data']
                logger.info(f"🎯 [INTENT] Znaleziono real intent dla '{cluster_name}': {intent_data.get('main_intent', 'unknown')}")
                return intent_data
            
            # Fallback to keywords table if no intent_data
            return await self._get_fallback_intent_data(cluster_name)
            
        except Exception as e:
            logger.warning(f"⚠️ [INTENT] Intent data fetch failed for {cluster_name}: {e}")
            return self._get_default_intent_data()

    async def _get_fallback_intent_data(self, cluster_name: str) -> Dict:
        """Fallback intent lookup from keywords table"""
        try:
            # Try to find keywords matching cluster name
            keyword_query = self.supabase.table('keywords').select(
                'main_intent, intent_probability, search_volume, cpc'
            ).ilike('keyword', f'%{cluster_name.lower()}%').limit(5).execute()
            
            if keyword_query.data:
                # Use most common intent from matching keywords
                intents = [k.get('main_intent') for k in keyword_query.data if k.get('main_intent')]
                main_intent = max(set(intents), key=intents.count) if intents else 'informational'
                
                total_volume = sum(k.get('search_volume', 0) for k in keyword_query.data)
                avg_cpc = sum(k.get('cpc', 0) for k in keyword_query.data) / len(keyword_query.data)
                
                logger.info(f"🔄 [INTENT] Fallback intent dla '{cluster_name}': {main_intent}")
                
                return {
                    'main_intent': main_intent,
                    'intent_probability': 0.5,  # Default
                    'commercial_value': total_volume * avg_cpc,
                    'business_priority': 'medium',
                    'total_volume': total_volume,
                    'avg_cpc': round(avg_cpc, 2),
                    'data_source': 'keywords_fallback'
                }
            
            return self._get_default_intent_data()
            
        except Exception as e:
            logger.error(f"❌ [INTENT] Fallback intent lookup failed: {e}")
            return self._get_default_intent_data()

    def _get_default_intent_data(self) -> Dict:
        """Default intent data when no real data available"""
        return {
            'main_intent': 'informational',
            'intent_probability': 0.0,
            'commercial_value': 0.0,
            'business_priority': 'content',
            'total_volume': 0,
            'avg_cpc': 0.0,
            'data_source': 'default'
        }

    async def _enhance_hierarchy_with_intent(self, hierarchy: Dict) -> Dict:
        """Enhance hierarchy with real intent data and business priorities"""
        try:
            semantic_cluster_id = self.cluster_data.get('id', self.cluster_data.get('semantic_cluster_id'))
            logger.info(f"🎯 [INTENT] Enhancing hierarchy z real intent data dla cluster: {semantic_cluster_id}")
            
            enhanced_count = 0
            total_commercial_value = 0
            
            # Enhance main categories
            for category in hierarchy.get('main_categories', []):
                
                # Enhance subcategories
                for sub_cat in category.get('sub_categories', []):
                    cluster_name = sub_cat.get('cluster_name')
                    if cluster_name:
                        intent_data = await self._get_cluster_intent_data(cluster_name, semantic_cluster_id)
                        sub_cat['intent_data'] = intent_data
                        sub_cat['business_priority'] = intent_data['business_priority']
                        sub_cat['commercial_value'] = intent_data['commercial_value']
                        total_commercial_value += intent_data['commercial_value']
                        enhanced_count += 1
                
                # Enhance standalone clusters  
                for standalone in category.get('standalone_clusters', []):
                    cluster_name = standalone.get('cluster_name')
                    if cluster_name:
                        intent_data = await self._get_cluster_intent_data(cluster_name, semantic_cluster_id)
                        standalone['intent_data'] = intent_data
                        standalone['business_priority'] = intent_data['business_priority']
                        standalone['commercial_value'] = intent_data['commercial_value']
                        total_commercial_value += intent_data['commercial_value']
                        enhanced_count += 1
            
            # Sort categories by business priority
            hierarchy['main_categories'] = self._sort_categories_by_intent_priority(hierarchy['main_categories'])
            
            # Add summary to hierarchy
            hierarchy['intent_summary'] = {
                'enhanced_pages': enhanced_count,
                'total_commercial_value': round(total_commercial_value, 2),
                'intent_sources': ['semantic_groups', 'keywords_fallback', 'default']
            }
            
            logger.info(f"✅ [INTENT] Enhanced {enhanced_count} pages, total commercial value: ${total_commercial_value:.0f}")
            return hierarchy
            
        except Exception as e:
            logger.error(f"❌ [INTENT] Intent enhancement failed: {e}")
            return hierarchy

    def _sort_categories_by_intent_priority(self, categories: List[Dict]) -> List[Dict]:
        """Sort categories by business value (commercial/transactional first)"""
        
        def get_category_priority_score(category):
            total_value = 0
            high_priority_count = 0
            commercial_count = 0
            
            # Calculate total commercial value from subcategories and standalone
            for sub_cat in category.get('sub_categories', []):
                intent_data = sub_cat.get('intent_data', {})
                total_value += intent_data.get('commercial_value', 0)
                if intent_data.get('business_priority') == 'high':
                    high_priority_count += 1
                if intent_data.get('main_intent') in ['commercial', 'transactional']:
                    commercial_count += 1
            
            for standalone in category.get('standalone_clusters', []):
                intent_data = standalone.get('intent_data', {})
                total_value += intent_data.get('commercial_value', 0)
                if intent_data.get('business_priority') == 'high':
                    high_priority_count += 1
                if intent_data.get('main_intent') in ['commercial', 'transactional']:
                    commercial_count += 1
            
            # Priority score: commercial intent + high commercial value + high priority items
            return (commercial_count * 100000) + total_value + (high_priority_count * 10000)
        
        sorted_categories = sorted(categories, key=get_category_priority_score, reverse=True)
        
        # Log sorting results
        for i, cat in enumerate(sorted_categories):
            score = get_category_priority_score(cat)
            logger.info(f"📊 [INTENT] Kategoria {i+1}: '{cat.get('name', 'Unknown')}' - score: {score:.0f}")
        
        return sorted_categories

    # === FUNNEL AUDIT SYSTEM - AI-POWERED CUSTOMER JOURNEY ANALYSIS ===
    
    def _extract_pages_from_structure(self, url_structure: Dict) -> List[Dict]:
        """Extract page data for funnel audit"""
        pages = []
        
        # Add pillar page
        if url_structure.get('pillar_page'):
            pages.append(url_structure['pillar_page'])
        
        # Add category pages
        for category in url_structure.get('categories', []):
            pages.append(category)
            
            # Add subcategories
            for sub in category.get('subcategories', []):
                pages.append(sub)
            
            # Add standalone pages  
            for page in category.get('standalone_pages', []):
                pages.append(page)
        
        return pages

    async def _audit_existing_linking_for_funnel(self, existing_structure: Dict, pages_data: List[Dict]) -> Dict:
        """
        🎯 UNIVERSAL FUNNEL AUDIT z kompletną AI-driven modyfikacją struktury
        """
        try:
            audit_start_time = time.time()
            logger.info(f"🔍 [FUNNEL_AUDIT] Rozpoczynam AI-driven audit dla '{self.seed_keyword}'")
            
            # Przygotuj kompletne dane dla AI
            audit_data = {
                'seed_keyword': self.seed_keyword,
                'architecture_type': self.arch_type,
                'current_internal_linking': existing_structure.get('internal_linking', {}),
                'current_strategic_bridges': existing_structure.get('strategic_bridges', []),
                'pages_structure': pages_data,
                'commercial_value': sum(g.get('intent_data', {}).get('commercial_value', 0) for g in self.groups),
                'total_pages': len(pages_data)
            }
            
            # Wyślij do AI z uniwersalnym promptem
            ai_assessment = await self._call_ai_complete_funnel_assessment(audit_data)
            
            audit_processing_time = time.time() - audit_start_time
            
            # Zapisz do bazy
            audit_id = self._save_funnel_audit_to_database(ai_assessment, audit_processing_time)
            if audit_id:
                ai_assessment['audit_id'] = audit_id
            
            logger.info(f"✅ [FUNNEL_AUDIT] AI-driven audit completed in {audit_processing_time:.2f}s")
            return ai_assessment
            
        except Exception as e:
            logger.error(f"❌ [FUNNEL_AUDIT] Audit failed: {e}")
            return {
                'should_optimize_for_funnel': False,
                'should_modify_structure': False,
                'reasoning': f'Audit failed: {str(e)}',
                'audit_status': 'failed'
            }

    async def _call_ai_complete_funnel_assessment(self, audit_data: Dict) -> Dict:
        """Universal AI prompt dla complete funnel assessment z modyfikacją struktury"""
        
        # Przygotuj skrócone dane dla AI (bez embeddingów!)
        pages_summary = []
        for page in audit_data.get('pages_structure', []):
            pages_summary.append({
                'name': page.get('name', ''),
                'url': page.get('url_pattern', ''),
                'page_type': page.get('page_type', ''),
                'business_intent': page.get('business_intent', 'informational'),
                'hierarchy_level': 1 if page.get('page_type') == 'pillar' else 2,
                'sample_keywords': page.get('target_keywords', [])[:3]  # Tylko 3 przykłady
            })

        # Rozdzielone sesje: funnel nie widzi strategic bridges

        # Internal links - tylko anchor texts
        internal_links_summary = []
        for link in audit_data.get('current_internal_linking', {}).get('vertical_linking', [])[:10]:
            internal_links_summary.append({
                'from_page': link.get('from_page', ''),
                'to_page': link.get('to_page', ''),
                'anchor_text': link.get('anchor_text', ''),
                'link_type': link.get('link_type', '')
            })

        session_salt = f"FUNNEL_SESSION::{int(time.time()*1000)}"
        prompt = f"""
DEFINICJA CUSTOMER FUNNEL:
Customer funnel to ścieżka użytkownika przez etapy decyzyjne:
1. AWARENESS - uczenie się podstaw, poznawanie tematu  
2. CONSIDERATION - research, porównywanie opcji, analiza wariantów
3. DECISION - wybór konkretnej opcji, podjęcie decyzji zakupowej

ZADANIE - UNIWERSALNE:
Przeanalizuj strukturę stron dla "{audit_data['seed_keyword']}" i stwórz SELEKTYWNY customer funnel.

ADAPTIVE REQUIREMENTS:
- MAKSYMALNIE 2-3 linki na kategorię główną (quality over quantity)
- TOTAL LIMIT: MIN(18, liczba_kategorii * 3) linków
- TYLKO naturalne customer progression paths z business value
- REALISTIC similarity scores 65-85% (różne dla różnych par)
- Każdy link wymaga business justification w rationale

UNIVERSAL FUNNEL LOGIC:
- AWARENESS: educational → foundational content progression
- CONSIDERATION: comparison → tools → research flow
- DECISION: research → specific vendor/product selection
- SKIP: competitive peer-to-peer bez customer value

QUALITY GATES:
- Business flow score ≥ 7/10 (czy user rzeczywiście to przejdzie?)
- No backwards funnel progression (decision → awareness forbidden)
- Maximum 2 outbound funnel links per page
- Unique anchor texts (no template repetition)
- Content progression: general → specific, simple → complex

WAŻNE: Używaj dokładnych url_path z listy (nie nazw kategorii)!

# SESSION: FUNNEL
# SESSION_SALT: {session_salt}

STRUKTURA STRON ({audit_data['total_pages']} stron):
{json.dumps(pages_summary, indent=2, ensure_ascii=False)}

 ZWRÓĆ JSON z KOMPLETNYMI połączeniami:
{{
    "should_optimize_for_funnel": true/false,
    "reasoning": "szczegółowe uzasadnienie",
    "confidence_score": 0.0-1.0,
    "should_modify_structure": true/false,
    "modified_strategic_bridges": [
        {{
            "from_url": "/dokladny/url/path/",
            "to_url": "/dokladny/url/path/",
            "suggested_anchor": "naturalny anchor text z psychology",
            "funnel_stage": "awareness/consideration/decision", 
            "rationale": "dlaczego ten link w customer journey",
            "implementation": {{
                "placement": ["mid_content"],
                "priority": 85
            }}
        }}
    ],
    "modifications_summary": ["lista wszystkich zmian"]
}}

"""

        try:
            # DEBUG: Funnel AI prompt + inputs (immediately before call)
            logger.info(f"🤖 [FUNNEL_AI] Prompt preview: {prompt[:200]}...")
            logger.info(f"🤖 [FUNNEL_AI] Input pages count: {len(pages_summary)}")
            logger.info(f"🤖 [FUNNEL_AI] First 3 pages: {[p.get('name') for p in pages_summary[:3]]}")
            logger.info(f"🤖 [FUNNEL_AI] Session: {session_salt}")

            response = self.call_llm_with_timeout(prompt, timeout=120)
            
            # Clean JSON response
            if response.startswith("```json"):
                response = response.replace("```json", "").replace("```", "").strip()
            elif response.startswith("```"):
                response = response.replace("```", "").strip()
            
            response = response.strip()
            
            try:
                assessment = json.loads(response)
                # 🔥 DEBUG: Raw Claude response
                logger.info(f"🔍 [FUNNEL_DEBUG] Claude raw response length: {len(response)} chars")
                logger.info(f"🔍 [FUNNEL_DEBUG] Claude response preview: {response[:2000]}...")

                # 🔥 DEBUG: Parsed assessment
                logger.info(f"🔍 [FUNNEL_DEBUG] Should modify: {assessment.get('should_modify_structure', False)}")
                logger.info(f"🔍 [FUNNEL_DEBUG] Modified bridges count: {len(assessment.get('modified_strategic_bridges', []))}")

                # 🔥 DEBUG: Each bridge
                try:
                    for i, bridge in enumerate(assessment.get('modified_strategic_bridges', [])[:10]):
                        logger.info(f"🔍 [FUNNEL_DEBUG] Bridge {i+1}: {bridge.get('from_cluster', '')} → {bridge.get('to_cluster', '')} | anchor: {str(bridge.get('suggested_anchor', ''))[:50]}...")
                except Exception as _:
                    pass

                # 🔥 DEBUG: Modifications summary  
                logger.info(f"🔍 [FUNNEL_DEBUG] Modifications: {assessment.get('modifications_summary', [])}")

                # DEBUG: Funnel AI response summary
                modified_bridges = assessment.get('modified_strategic_bridges', [])
                logger.info(f"🤖 [FUNNEL_RESPONSE] Modified bridges count: {len(modified_bridges)}")
                for i, bridge in enumerate(modified_bridges[:3]):
                    logger.info(f"🤖 [FUNNEL_RESPONSE] Bridge {i+1}: {bridge.get('from_url', '')} → {bridge.get('to_url', '')} | anchor: {str(bridge.get('suggested_anchor', ''))[:50]}...")
                
                # Rozdzielone sesje → brak wiedzy o strategic bridges; brak filtracji na tym etapie
                
                # NOWE: Map AI response to funnel_suggestions structure
                if assessment.get('should_modify_structure', False):
                    # Extract psychology data from AI modifications
                    strategic_bridges = assessment.get('modified_strategic_bridges', [])
                    internal_linking = assessment.get('modified_internal_linking', {})
                    
                    # Create psychology anchors from strategic bridges (top similarity ones)
                    psychology_anchors = []
                    for bridge in strategic_bridges[:5]:  # Top 5 as psychology anchors
                        psychology_anchors.append({
                            'text': bridge.get('suggested_anchor', ''),
                            'target_url': bridge.get('target_url', ''),
                            'psychology_trigger': bridge.get('psychology_trigger', 'relevance'),
                            'placement': bridge.get('implementation', {}).get('placement', ['mid_content']),
                            'emotional_context': f"Bridge from {bridge.get('from_cluster', '')} to {bridge.get('to_cluster', '')}",
                            'similarity_score': bridge.get('similarity_score', 0)
                        })
                    
                    # Map to funnel_suggestions structure that Module 4 expects
                    assessment['funnel_suggestions'] = {
                        'psychology_anchors': psychology_anchors,
                        'strategic_bridges': strategic_bridges,
                        'internal_linking_modifications': internal_linking,
                        'psychology_applied': True,
                        'funnel_optimized': True,
                        'ai_confidence': assessment.get('confidence_score', 0.0),
                        'modifications_applied': assessment.get('modifications_summary', []),
                        'psychology_principles': assessment.get('psychology_principles_applied', [])
                    }
                    
                    logger.info(f"🧠 [FUNNEL_AUDIT] Zmapowano psychology data: {len(psychology_anchors)} anchors, {len(strategic_bridges)} bridges")
                else:
                    # No psychology modifications - empty but structured
                    assessment['funnel_suggestions'] = {
                        'psychology_anchors': [],
                        'strategic_bridges': [],
                        'psychology_applied': False,
                        'funnel_optimized': False,
                        'ai_confidence': assessment.get('confidence_score', 0.0)
                    }
                    
                    logger.info(f"🧠 [FUNNEL_AUDIT] No psychology modifications - empty funnel_suggestions")
                
                logger.info(f"🤖 [FUNNEL_AUDIT] AI assessment: optimize={assessment.get('should_optimize_for_funnel', False)}, modify_structure={assessment.get('should_modify_structure', False)}")
                return assessment
                
            except json.JSONDecodeError as e:
                logger.error(f"❌ [FUNNEL_AUDIT] JSON parse error: {e}")
                logger.error(f"🔍 [FUNNEL_AUDIT] Raw response: {response[:500]}...")
                
                # INTELLIGENT PARSING - extract basic data from broken JSON
                should_optimize = False
                should_modify = False
                reasoning = f"JSON parse failed: {str(e)}"
                confidence = 0.0
                
                if '"should_optimize_for_funnel": true' in response:
                    should_optimize = True
                    confidence = 0.8
                    reasoning = "Partial response extracted - AI recommended funnel optimization despite JSON parsing error"
                    
                if '"should_modify_structure": true' in response:
                    should_modify = True
                
                return {
                    'should_optimize_for_funnel': should_optimize,
                    'should_modify_structure': should_modify,
                    'reasoning': reasoning,
                    'confidence_score': confidence,
                    'audit_status': 'partial_success' if should_optimize else 'json_parse_failed'
                }
                
        except Exception as e:
            logger.error(f"❌ [FUNNEL_AUDIT] Complete AI assessment failed: {e}")
            return {
                'should_optimize_for_funnel': False,
                'should_modify_structure': False,
                'reasoning': f'Complete AI assessment failed: {str(e)}',
                'confidence_score': 0.0,
                'audit_status': 'failed'
            }

    async def _prepare_audit_data(self, existing_structure: Dict, pages_data: List[Dict]) -> Dict:
        """Prepare audit data for funnel assessment"""
        # This method should return a dictionary containing all necessary data for funnel assessment
        # You can add any additional data you want to include in the audit
        return {
            'seed_keyword': self.seed_keyword,
            'architecture_type': self.arch_type,
            'current_internal_linking': existing_structure.get('internal_linking', {}),
            'current_strategic_bridges': existing_structure.get('strategic_bridges', []),
            'pages_structure': pages_data,
            'commercial_value': sum(g.get('intent_data', {}).get('commercial_value', 0) for g in self.groups),
            'total_pages': len(pages_data)
        }

    def _save_funnel_audit_to_database(self, funnel_audit: Dict, processing_time: float) -> Optional[str]:
        """Zapisuje wyniki funnel audit do bazy danych"""
        try:
            if not self.supabase:
                logger.warning("⚠️ [FUNNEL_AUDIT] Brak połączenia z bazą - pomijam zapis")
                return None
            
            audit_data = {
                'seed_keyword': self.seed_keyword,
                'should_optimize_for_funnel': funnel_audit.get('should_optimize_for_funnel', False),
                'reasoning': funnel_audit.get('reasoning', ''),
                'commercial_potential': funnel_audit.get('commercial_potential', 'none'),
                'user_journey_exists': funnel_audit.get('user_journey_exists', False),
                'funnel_stages_identified': funnel_audit.get('funnel_stages_identified', []),
                'suggested_approach': funnel_audit.get('suggested_approach', 'semantic_linking'),
                'confidence_score': funnel_audit.get('confidence_score', 0.0),
                'funnel_suggestions': funnel_audit.get('funnel_suggestions', {}),
                'ai_processing_time': processing_time,
                'audit_status': funnel_audit.get('audit_status', 'completed')
            }
            
            # Note: architecture_id będzie dodane w generate_and_save()
            response = self.supabase.table('funnel_audits').insert(audit_data).execute()

            if response.data:
                audit_id = response.data[0]['id']
                
                # Store audit_id to update with architecture_id later
                if self.db:
                    self.db._temp_funnel_audit_id = audit_id
                
                logger.info(f"💾 [FUNNEL_AUDIT] Zapisano audit: {audit_id}")
                return audit_id

            return None
            
        except Exception as e:
            logger.error(f"❌ [FUNNEL_AUDIT] Błąd zapisu audit: {e}")
            return None

    def get_safe_stats_value(self, architecture_data: Dict, key: str, default_value):
        """Bezpiecznie wyciąga wartość ze stats z fallback"""
        return architecture_data.get('stats', {}).get(key, default_value)
    
    def prepare_safe_architecture_record(self, architecture_data: Dict) -> Dict:
        """Przygotowuje record do zapisu z bezpiecznymi wartościami stats"""
        return {
            'total_pages': self.get_safe_stats_value(architecture_data, 'total_pages', 0),
            'max_depth': self.get_safe_stats_value(architecture_data, 'max_depth', 1),
            'cross_links_found': self.get_safe_stats_value(architecture_data, 'cross_links_found', 0),
            'embeddings_used': self.get_safe_stats_value(architecture_data, 'embeddings_used', False),
            'funnel_optimization_suggested': self.get_safe_stats_value(architecture_data, 'funnel_optimization_suggested', False),
            'funnel_confidence_score': self.get_safe_stats_value(architecture_data, 'funnel_confidence_score', 0.0)
        }

    async def _create_architecture_pages(self, architecture_id: str, url_structure: Dict) -> None:
        """
        🆕 Tworzy rekordy w tabeli architecture_pages na podstawie url_structure
        BEZPIECZNE DODANIE - nie wpływa na istniejące funkcje
        """
        try:
            logger.info(f"💾 [PAGES] Tworzę architecture_pages dla {architecture_id}")
            pages_to_create = []
            parent_pages = {}  # Mapa dla parent_page_id relationships
            
            # 1. PILLAR PAGE
            if url_structure.get('pillar_page'):
                pillar = url_structure['pillar_page']
                pillar_record = {
                    'architecture_id': architecture_id,
                    'name': pillar.get('name', ''),
                    'url_path': pillar.get('url_pattern', ''),
                    'url_slug': self._extract_slug_from_url(pillar.get('url_pattern', '')),
                    'page_type': 'pillar',
                    'parent_page_id': None,  # Pillar nie ma parenta
                    'depth_level': 0,
                    'target_keywords': pillar.get('target_keywords', []),
                    'estimated_content_length': pillar.get('estimated_word_count', 3000),
                    'cluster_name': self.seed_keyword,  # ← POPRAWKA: użyj seed_keyword zamiast None
                    'cluster_phrase_count': None,
                    'seo_recommendations': {},
                    'content_suggestions': {},
                    'paa_questions': pillar.get('paa_questions', []),
                    'ai_overview_topics': pillar.get('ai_overview_topics', []),
                    'content_opportunities_count': pillar.get('content_opportunities_count', 0),
                    'has_faq_section': pillar.get('has_faq_section', False)
                }
                pages_to_create.append(pillar_record)
                parent_pages['pillar'] = len(pages_to_create) - 1  # Index for later reference
            
            # 2. CATEGORIES
            for cat_idx, category in enumerate(url_structure.get('categories', [])):
                # Category page
                category_record = {
                    'architecture_id': architecture_id,
                    'name': category.get('name', ''),
                    'url_path': category.get('url_pattern', ''),
                    'url_slug': self._extract_slug_from_url(category.get('url_pattern', '')),
                    'page_type': 'category',
                    'parent_page_id': None,  # Będzie ustawione po insert
                    'depth_level': 1,
                    'target_keywords': category.get('target_keywords', []),
                    'estimated_content_length': category.get('estimated_word_count', 2000),
                    'cluster_name': category.get('name', ''),  # ← POPRAWKA: użyj category name zamiast None
                    'cluster_phrase_count': None,
                    'seo_recommendations': {},
                    'content_suggestions': {},
                    'paa_questions': category.get('paa_questions', []),
                    'ai_overview_topics': category.get('ai_overview_topics', []),
                    'content_opportunities_count': category.get('content_opportunities_count', 0),
                    'has_faq_section': category.get('has_faq_section', False)
                }
                pages_to_create.append(category_record)
                parent_pages[f'category_{cat_idx}'] = len(pages_to_create) - 1
                
                # 3. SUBCATEGORIES
                for sub_idx, subcategory in enumerate(category.get('subcategories', [])):
                    cluster_data = subcategory.get('cluster_data', {})
                    phrases_with_details = subcategory.get('phrases_with_details', [])
                    
                    subcategory_record = {
                        'architecture_id': architecture_id,
                        'name': subcategory.get('name', ''),
                        'url_path': subcategory.get('url_pattern', ''),
                        'url_slug': self._extract_slug_from_url(subcategory.get('url_pattern', '')),
                        'page_type': 'subcategory',
                        'parent_page_id': None,  # Będzie ustawione po insert
                        'depth_level': 2,
                        'target_keywords': self._extract_keywords_from_cluster(cluster_data, phrases_with_details),
                        'estimated_content_length': subcategory.get('estimated_word_count', 1500),
                        'cluster_name': cluster_data.get('name', ''),
                        'cluster_phrase_count': cluster_data.get('phrase_count', len(phrases_with_details)),
                        'seo_recommendations': {},
                        'content_suggestions': {},
                        'paa_questions': subcategory.get('paa_questions', []),
                        'ai_overview_topics': subcategory.get('ai_overview_topics', []),
                        'content_opportunities_count': subcategory.get('content_opportunities_count', 0),
                        'has_faq_section': subcategory.get('has_faq_section', False)
                    }
                    pages_to_create.append(subcategory_record)
                
                # 4. STANDALONE PAGES
                for standalone_idx, standalone in enumerate(category.get('standalone_pages', [])):
                    cluster_data = standalone.get('cluster_data', {})
                    phrases_with_details = standalone.get('phrases_with_details', [])
                    
                    standalone_record = {
                        'architecture_id': architecture_id,
                        'name': standalone.get('name', ''),
                        'url_path': standalone.get('url_pattern', ''),
                        'url_slug': self._extract_slug_from_url(standalone.get('url_pattern', '')),
                        'page_type': 'cluster_page',
                        'parent_page_id': None,  # Będzie ustawione po insert
                        'depth_level': 2,
                        'target_keywords': self._extract_keywords_from_cluster(cluster_data, phrases_with_details),
                        'estimated_content_length': standalone.get('estimated_word_count', 1200),
                        'cluster_name': cluster_data.get('name', ''),
                        'cluster_phrase_count': cluster_data.get('phrase_count', len(phrases_with_details)),
                        'seo_recommendations': {},
                        'content_suggestions': {},
                        'paa_questions': standalone.get('paa_questions', []),
                        'ai_overview_topics': standalone.get('ai_overview_topics', []),
                        'content_opportunities_count': standalone.get('content_opportunities_count', 0),
                        'has_faq_section': standalone.get('has_faq_section', False)
                    }
                    pages_to_create.append(standalone_record)
            
            # 5. BATCH INSERT
            if pages_to_create:
                response = self.supabase.table('architecture_pages').insert(pages_to_create).execute()
                
                if response.data:
                    logger.info(f"✅ [PAGES] Utworzono {len(response.data)} architecture_pages")
                    
                    # 6. UPDATE PARENT RELATIONSHIPS (opcjonalne - może być w przyszłości)
                    # await self._update_parent_relationships(response.data)
                    
                else:
                    logger.warning(f"⚠️ [PAGES] Insert architecture_pages zwrócił pustą odpowiedź")
            else:
                logger.warning(f"⚠️ [PAGES] Brak stron do utworzenia")
                
        except Exception as e:
            # KRYTYCZNE: NIE przerywaj procesu - architecture już zapisana
            logger.error(f"❌ [PAGES] Błąd tworzenia architecture_pages: {e}")
            logger.warning(f"⚠️ [PAGES] Architektura nadal zapisana - tylko architecture_pages failed")
            # NIE raise - pozwól procesowi kontynuować

    async def _save_architecture_links(self, architecture_id: str, internal_linking: Dict, 
                                     strategic_bridges: List[Dict], funnel_audit: Dict) -> Dict:
        """
        🔗 ENHANCED: Top-K Global Link Selection z Quality Gates
        
        Implementuje unified flow:
        1. Zbiera kandydatów z wszystkich źródeł (bridge + funnel)
        2. Ocenia jakość (embedding/serp/intent + bonus/kara)
        3. Wybiera Top-K global po confidence_score z anty-duplikacją
        4. Zapisuje do architecture_links po page_id
        5. Re-read z DB i zwraca to co zostało zapisane
        
        Returns: Dict z danymi odczytanymi z DB po zapisie
        """
        try:
            logger.info(f"🔗 [TOPK] Rozpoczynam Top-K global selection dla architecture: {architecture_id}")
            
            # KROK 1: Zbierz kandydatów bridge + funnel z quality assessment
            candidates = []
            
            # Bridge candidates z strategic_bridges
            bridge_candidates = await self._collect_bridge_candidates(
                strategic_bridges, architecture_id, source='bridge'
            )
            candidates.extend(bridge_candidates)
            
            # Funnel candidates z funnel_audit (jeśli są modifikacje)
            funnel_candidates = await self._collect_funnel_candidates(
                funnel_audit, architecture_id, source='funnel'
            )
            candidates.extend(funnel_candidates)
            
            logger.info(f"📊 [TOPK] Zebranych kandydatów: {len(candidates)} "
                       f"(bridge: {len(bridge_candidates)}, funnel: {len(funnel_candidates)})")
            
            # KROK 2: Quality gates + scoring
            qualified_candidates = []
            for candidate in candidates:
                # Hard thresholds
                if not self._passes_hard_thresholds(
                    candidate['s_sem'], candidate['s_serp'], candidate['intent_match']
                ):
                    continue
                
                # Confidence scoring
                confidence = self._score_bridge(
                    candidate['s_sem'], candidate['s_serp'], candidate['intent_match'],
                    journey_ok=candidate.get('journey_ok', False),
                    has_outlier=candidate.get('has_outlier', False)
                )
                
                if confidence < CONF_MIN:
                    continue
                
                candidate['confidence_score'] = confidence
                qualified_candidates.append(candidate)
            
            logger.info(f"🚪 [TOPK] Po quality gates: {len(qualified_candidates)}/{len(candidates)} kandydatów")
            
            # KROK 3: Anti-duplication i Top-K selection
            final_links = await self._select_topk_with_dedup(qualified_candidates, architecture_id)
            
            # KROK 4: Dodaj hierarchy links (zawsze bez quality gates)
            hierarchy_links = await self._process_hierarchy_links_simple(internal_linking, architecture_id)
            final_links.extend(hierarchy_links)
            
            # KROK 5: Batch insert do DB
            if final_links:
                await self._batch_insert_links_with_deduplication(final_links, architecture_id)
                
                # Agregaty do logów
                bridge_count = len([l for l in final_links if l['link_type'] == 'bridge'])
                funnel_count = len([l for l in final_links if l['link_type'] == 'funnel'])
                hierarchy_count = len([l for l in final_links if l['link_type'] == 'hierarchy'])
                
                # Statystyki confidence dla bridge+funnel
                scored_links = [l for l in final_links if 'confidence_score' in l and l.get('link_type') in ['bridge', 'funnel']]
                if scored_links:
                    conf_scores = [l['confidence_score'] for l in scored_links]
                    avg_conf = sum(conf_scores) / len(conf_scores)
                    min_conf = min(conf_scores)
                    max_conf = max(conf_scores)
                    
                    logger.info(f"📊 [TOPK] FINAL STATS: "
                               f"Total={len(final_links)} "
                               f"(hierarchy={hierarchy_count}, bridge={bridge_count}, funnel={funnel_count}) "
                               f"| Confidence: avg={avg_conf:.3f}, min={min_conf:.3f}, max={max_conf:.3f}")
                else:
                    logger.info(f"📊 [TOPK] FINAL STATS: "
                               f"Total={len(final_links)} "
                               f"(hierarchy={hierarchy_count}, bridge={bridge_count}, funnel={funnel_count}) | No confidence scores")
            
            # KROK 6: 🎯 RE-READ z DB i zwróć to co zostało zapisane
            saved_links_data = await self._reread_saved_links(architecture_id)
            
            logger.info(f"✅ [TOPK] Zapisano {len(final_links)} linków, re-read z DB: {len(saved_links_data['links'])} rekordów")
            return saved_links_data
            
        except Exception as e:
            logger.error(f"❌ [TOPK] Błąd Top-K link selection: {e}")
            # Fallback - zwróć pustą strukturę
            return {
                'strategic_bridges': [],
                'funnel_links': [],
                'hierarchy_links': [],
                'total_links': 0,
                'links': []
            }

    async def _collect_bridge_candidates(self, strategic_bridges: List[Dict], 
                                       architecture_id: str, source: str) -> List[Dict]:
        """
        🌉 Zbiera kandydatów bridge z oceną jakości
        """
        candidates = []
        for bridge in strategic_bridges:
            try:
                # Resolve do page_ids
                from_page = await self._resolve_to_page_id(
                    architecture_id=architecture_id,
                    cluster_name=bridge.get('from_cluster', ''),
                    url_path=bridge.get('from_url', '')
                )
                to_page = await self._resolve_to_page_id(
                    architecture_id=architecture_id,
                    cluster_name=bridge.get('to_cluster', ''),
                    url_path=bridge.get('to_url', '')
                )
                
                if not from_page or not to_page:
                    logger.warning(f"⚠️ [BRIDGE] Nie zmapowano: {bridge.get('from_cluster')} → {bridge.get('to_cluster')}")
                    continue
                
                # Extract quality metrics (z domyślnymi wartościami)
                s_sem = bridge.get('similarity_score', 0.0) / 100.0 if bridge.get('similarity_score', 0) > 1 else bridge.get('similarity_score', 0.0)
                s_serp = bridge.get('serp_similarity', 0.7)  # Default moderate
                intent_match = bridge.get('intent_match', True)  # Default optimistic
                
                candidate = {
                    'from_page_id': from_page['id'],
                    'to_page_id': to_page['id'],
                    'from_cluster': bridge.get('from_cluster', ''),
                    'to_cluster': bridge.get('to_cluster', ''),
                    'anchor_text': bridge.get('suggested_anchor', ''),
                    'link_type': source,
                    'source': 'strategic_bridges',
                    's_sem': s_sem,
                    's_serp': s_serp,
                    'intent_match': intent_match,
                    'journey_ok': bridge.get('journey_ok', False),
                    'has_outlier': bridge.get('has_outlier', False),
                    'placement': bridge.get('implementation', {}).get('placement', ['natural_flow']),
                    'funnel_stage': bridge.get('funnel_stage', ''),
                    'resolution_method': 'cluster_resolution'
                }
                candidates.append(candidate)
                
            except Exception as e:
                logger.error(f"❌ [BRIDGE] Błąd przetwarzania bridge: {e}")
                continue
        
        logger.info(f"🌉 [BRIDGE] Zebranych kandydatów bridge: {len(candidates)}")
        return candidates

    async def _collect_funnel_candidates(self, funnel_audit: Dict, 
                                       architecture_id: str, source: str) -> List[Dict]:
        """
        🎯 Zbiera kandydatów funnel z oceną jakości
        """
        candidates = []
        
        # Sprawdź warunek zapisu funnel links
        should = funnel_audit.get("should_modify_structure", False)
        mods = funnel_audit.get("modified_strategic_bridges") or []
        
        if not (should or mods):
            logger.info(f"🎯 [FUNNEL] Brak modyfikacji funnel - pomijam kandydatów")
            return candidates
        
        for bridge in mods:
            try:
                # Resolve do page_ids
                from_page = await self._resolve_to_page_id(
                    architecture_id=architecture_id,
                    cluster_name=bridge.get('from_cluster', ''),
                    url_path=bridge.get('from_url', '')
                )
                to_page = await self._resolve_to_page_id(
                    architecture_id=architecture_id,
                    cluster_name=bridge.get('to_cluster', ''),
                    url_path=bridge.get('to_url', '')
                )
                
                if not from_page or not to_page:
                    logger.warning(f"⚠️ [FUNNEL] Nie zmapowano: {bridge.get('from_cluster')} → {bridge.get('to_cluster')}")
                    continue
                
                # Extract quality metrics (funnel bridges zazwyczaj lepsze)
                s_sem = bridge.get('similarity_score', 0.0) / 100.0 if bridge.get('similarity_score', 0) > 1 else bridge.get('similarity_score', 0.0)
                s_serp = bridge.get('serp_similarity', 0.8)  # Higher default dla funnel
                intent_match = bridge.get('intent_match', True)
                
                candidate = {
                    'from_page_id': from_page['id'],
                    'to_page_id': to_page['id'],
                    'from_cluster': bridge.get('from_cluster', ''),
                    'to_cluster': bridge.get('to_cluster', ''),
                    'anchor_text': bridge.get('suggested_anchor', ''),
                    'link_type': source,
                    'source': 'funnel_audit',
                    's_sem': s_sem,
                    's_serp': s_serp,
                    'intent_match': intent_match,
                    'journey_ok': True,  # Funnel bridges mają journey bonus
                    'has_outlier': bridge.get('has_outlier', False),
                    'placement': bridge.get('implementation', {}).get('placement', ['natural_flow']),
                    'funnel_stage': bridge.get('funnel_stage', ''),
                    'resolution_method': 'cluster_resolution'
                }
                # Uzupełnij funnel_stage jeśli puste – heurystyka na bazie intencji stron
                try:
                    if not candidate.get('funnel_stage'):
                        fi = (getattr(self, '_pages_meta', {}) or {}).get(candidate['from_page_id'], {})
                        ti = (getattr(self, '_pages_meta', {}) or {}).get(candidate['to_page_id'], {})
                        candidate['funnel_stage'] = self._infer_funnel_stage(
                            (fi or {}).get('intent', 'informational'),
                            (ti or {}).get('intent', 'informational')
                        )
                except Exception:
                    pass
                candidates.append(candidate)
                
            except Exception as e:
                logger.error(f"❌ [FUNNEL] Błąd przetwarzania funnel bridge: {e}")
                continue
        
        logger.info(f"🎯 [FUNNEL] Zebranych kandydatów funnel: {len(candidates)}")
        return candidates

    def _confidence(self, link: dict) -> float:
        """Helper do obliczania confidence_score"""
        try:
            val = link.get("confidence_score")
            return float(val) if val is not None else 0.0
        except Exception:
            return 0.0

    def select_topk_links_enforced(self, candidates: List[Dict], K: int, min_per_type: Dict[str, int]) -> Tuple[List[Dict], List[Dict]]:
        """
        Deterministyczny Top-K z twardym min_per_type po deduplikacji par from→to.
        Zwraca (selected_bridges, selected_funnel).
        """
        candidates = candidates or []

        # 0) Dedup per pair with funnel preference and best-by-score within type
        def _tp(x: Dict) -> Tuple[str, str]:
            return (str(x.get('from_page_id')), str(x.get('to_page_id')))

        def _ty(x: Dict) -> str:
            return (x.get('type') or x.get('link_type') or '').lower()

        def _score_for(x: Dict) -> Tuple[float, int]:
            cs = float(x.get('confidence_score') or 0.0)
            pr = x.get('priority')
            pr = int(pr) if pr is not None else int(cs * 100)
            return (cs, pr)

        # diagnostic: count pairs existing in both types before dedup
        try:
            types_by_pair: Dict[Tuple[str, str], set] = {}
            for c in candidates:
                types_by_pair.setdefault(_tp(c), set()).add(_ty(c))
            pairs_with_both = sum(1 for v in types_by_pair.values() if {'bridge', 'funnel'}.issubset(v) or v == {'bridge', 'funnel'})
            logger.info(f"[TOPK] pairs_with_both_types(before_dedup)={pairs_with_both}")
        except Exception:
            pass

        best_by_pair: Dict[Tuple[str, str], Dict] = {}
        for c in candidates:
            pk = _tp(c)
            prev = best_by_pair.get(pk)
            if not prev:
                best_by_pair[pk] = c
                continue
            if _ty(prev) != _ty(c):
                # Prefer funnel over bridge for same pair
                if _ty(c) == 'funnel':
                    best_by_pair[pk] = c
                # else keep prev (funnel already there or both bridge)
                continue
            # Same type → keep higher scored
            if _score_for(c) > _score_for(prev):
                best_by_pair[pk] = c

        deduped: List[Dict] = list(best_by_pair.values())

        # 1) Split by type (accept both 'type' and 'link_type')
        def get_type(x: Dict) -> str:
            return (x.get('type') or x.get('link_type') or '').lower()

        bridges_pool = [x for x in deduped if get_type(x) == 'bridge']
        funnel_pool = [x for x in deduped if get_type(x) == 'funnel']

        # 2) Stable sort: priority desc → similarity/confidence desc → tie-breaker
        def eff_priority(x: Dict) -> int:
            p = x.get('priority')
            if p is None:
                p = int((x.get('confidence_score') or 0.0) * 100)
            return int(p)

        def eff_similarity(x: Dict) -> float:
            v = x.get('similarity')
            if v is None:
                v = x.get('confidence_score', 0.0)
            try:
                return float(v)
            except Exception:
                return 0.0

        def tie(x: Dict) -> Tuple[str, str]:
            return (str(x.get('from_page_id')), str(x.get('to_page_id')))

        for pool in (bridges_pool, funnel_pool):
            pool.sort(key=tie)
            pool.sort(key=eff_similarity, reverse=True)
            pool.sort(key=eff_priority, reverse=True)

        # 3) Enforce min_per_type
        min_bridge = int(min_per_type.get('bridge', 0) or 0)
        min_funnel = int(min_per_type.get('funnel', 0) or 0)
        min_sum = min_bridge + min_funnel
        if min_sum > K:
            logger.info(f"[TOPK] Raising K from {K} to {min_sum} to meet min_per_type policy")
            K = min_sum

        picked_br: List[Dict] = bridges_pool[:min_bridge]
        picked_fn: List[Dict] = funnel_pool[:min_funnel]

        picked_pair_keys = {f"{_tp(x)[0]}→{_tp(x)[1]}" for x in (picked_br + picked_fn)}

        # 4) Fill to K from unified remainder (stably sorted)
        remainder: List[Dict] = []
        for x in bridges_pool[min_bridge:]:
            if f"{_tp(x)[0]}→{_tp(x)[1]}" not in picked_pair_keys:
                remainder.append(x)
        for x in funnel_pool[min_funnel:]:
            if f"{_tp(x)[0]}→{_tp(x)[1]}" not in picked_pair_keys:
                remainder.append(x)

        remainder.sort(key=tie)
        remainder.sort(key=eff_similarity, reverse=True)
        remainder.sort(key=eff_priority, reverse=True)

        need = K - (len(picked_br) + len(picked_fn))
        for x in remainder:
            if need <= 0:
                break
            pk = f"{_tp(x)[0]}→{_tp(x)[1]}"
            if pk in picked_pair_keys:
                continue
            if get_type(x) == 'bridge':
                picked_br.append(x)
            else:
                picked_fn.append(x)
            picked_pair_keys.add(pk)
            need -= 1

        # 5) Log unmet mins and compensate by other type if needed
        if len(picked_br) < min_bridge:
            logger.warning(f"⚠️ POLICY: unmet min_per_type for 'bridge' (required={min_bridge}, got={len(picked_br)})")
        if len(picked_fn) < min_funnel:
            logger.warning(f"⚠️ POLICY: unmet min_per_type for 'funnel' (required={min_funnel}, got={len(picked_fn)})")

        logger.info(f"[TOPK] selected_by_type: bridge={len(picked_br)}, funnel={len(picked_fn)}, K={K}, dropped_due_to_dedupe={len(candidates)-len(deduped)}")
        return picked_br, picked_fn

    def select_topk_links(self, candidates: list) -> list:
        """
        🔝 Top-K selection z minimalnymi kwotami per typ + anti-duplication
        Wymogi:
        - Deduplikacja po kluczu: (from_page_id, to_page_id, link_type)
        - Sortowanie malejąco po: confidence_score (None traktuj jak 0) → priority (None jak 0)
        - Najpierw minimalne kwoty per typ: policy["min_per_type"][t]
        - Następnie dobij do policy["K"] najlepszymi pozostałymi, respektując policy["enable_*"]
        """
        if not candidates:
            return []

        def score(x):
            cs = x.get("confidence_score") or 0
            pr = x.get("priority") or 0
            return (cs, pr)

        # użyj polityki z konfiguracji architektury
        policy = self.arch_policy
        # flags
        enable_bridges = policy.get("enable_bridges", True)
        enable_funnel = policy.get("enable_funnel", True)
        
        # dedup
        seen = set()
        deduped = []
        for c in candidates:
            key = (c.get("from_page_id"), c.get("to_page_id"), c.get("link_type"))
            if key in seen:
                continue
            seen.add(key)
            deduped.append(c)

        # split by type
        bridges = [c for c in deduped if c.get("link_type") == "bridge" and enable_bridges]
        funnels = [c for c in deduped if c.get("link_type") == "funnel" and enable_funnel]

        bridges.sort(key=score, reverse=True)
        funnels.sort(key=score, reverse=True)

        selected = []

        # min per type
        min_bridge = policy.get("min_per_type", {}).get("bridge", 0)
        min_funnel = policy.get("min_per_type", {}).get("funnel", 0)
        K = policy.get("topk", len(deduped))

        selected += bridges[:min_bridge]
        selected += funnels[:min_funnel]

        selected_ids = set((c.get("from_page_id"), c.get("to_page_id"), c.get("link_type")) for c in selected)

        # pool remaining by policy
        pool = []
        if enable_bridges:
            pool += bridges[min_bridge:]
        if enable_funnel:
            pool += funnels[min_funnel:]
        pool.sort(key=score, reverse=True)

        for c in pool:
            if len(selected) >= K:
                break
            key = (c.get("from_page_id"), c.get("to_page_id"), c.get("link_type"))
            if key in selected_ids:
                continue
            selected.append(c)
            selected_ids.add(key)

        return selected

    async def _select_topk_with_dedup(self, candidates: List[Dict], architecture_id: str) -> List[Dict]:
        """
        🔝 ENHANCED: Top-K selection używający nowej polityki z kwotami per typ
        """
        if not candidates:
            return []
        
        # stats do logów
        cnt_bridge = sum(1 for c in candidates if c.get("link_type") == "bridge")
        cnt_funnel = sum(1 for c in candidates if c.get("link_type") == "funnel")
        logger.info(f"📊 [TOPK] Zebranych kandydatów: {len(candidates)} (bridge: {cnt_bridge}, funnel: {cnt_funnel})")

        # Log policy
        logger.info(f"🧮 [TOPK] policy: K={self.arch_policy.get('topk')}, enable_bridges={self.arch_policy.get('enable_bridges')}, enable_funnel={self.arch_policy.get('enable_funnel', True)}, min_per_type={self.arch_policy.get('min_per_type')}")
        
        # Filtruj tylko bridge i funnel dla quality gates check
        filtered = [c for c in candidates if c.get("link_type") in ("bridge", "funnel")]
        logger.info(f"🚪 [TOPK] Po quality gates: {len(filtered)}/{len(candidates)} kandydatów")

        # Użyj nowej funkcji select_topk_links z odpowiednią polityką
        policy = {
            "topk": self.arch_policy.get("topk", 6),
            "enable_bridges": self.arch_policy.get("enable_bridges", True),
            "enable_funnel": self.arch_policy.get("enable_funnel", True),
            "min_per_type": self.arch_policy.get("min_per_type", {"bridge": 2, "funnel": 2})
        }
        
        # Deterministyczny selektor z min_per_type enforcement
        K = self.arch_policy.get('topk', 6)
        min_per_type = self.arch_policy.get('min_per_type', {'bridge': 2, 'funnel': 2})
        selected_br, selected_fn = self.select_topk_links_enforced(filtered, K, min_per_type)
        selected = selected_br + selected_fn

        # Cross-type dedupe: jeśli jest funnel i bridge o tej samej parze, usuń bridge
        try:
            pairs_with_funnel = set(
                (c.get("from_page_id"), c.get("to_page_id"))
                for c in selected if c.get("link_type") == "funnel"
            )
            if pairs_with_funnel:
                selected = [
                    c for c in selected
                    if not (
                        c.get("link_type") == "bridge" and
                        (c.get("from_page_id"), c.get("to_page_id")) in pairs_with_funnel
                    )
                ]
        except Exception as _:
            pass

        sel_bridge = sum(1 for c in selected if c.get("link_type") == "bridge")
        sel_funnel = sum(1 for c in selected if c.get("link_type") == "funnel")
        logger.info(f"🔝 [TOPK] Selected {len(selected)}/{policy.get('topk')} | by type: bridge={sel_bridge}, funnel={sel_funnel}")
        # Policy assertions
        try:
            min_funnel_req = self.arch_policy.get('min_per_type', {}).get('funnel', 0)
            if self.arch_policy.get('enable_funnel', True) and min_funnel_req > 0 and sel_funnel < min_funnel_req:
                logger.warning(f"⚠️ POLICY: selected funnel {sel_funnel} < required {min_funnel_req}")
        except Exception:
            pass
        logger.info(f"🔝 [TOPK] Final: bridge={len(selected_br)}, funnel={len(selected_fn)} | K={K}")
        
        # Convert to link records
        link_records = []
        for candidate in selected:
            link_record = {
                'architecture_id': architecture_id,
                'from_page_id': candidate['from_page_id'],
                'to_page_id': candidate['to_page_id'],
                'link_type': candidate['link_type'],
                'anchor_text': candidate['anchor_text'],
                'placement': candidate['placement'],
                'priority': int(candidate.get('confidence_score', 0.0) * 100),  # Convert to 0-100 scale
                'source': candidate['source'],
                'enabled': True,
                'link_context': f"{candidate['link_type'].title()} link (confidence: {candidate.get('confidence_score', 0.0):.3f})",
                'confidence_score': candidate.get('confidence_score', 0.0),
                'resolution_method': candidate['resolution_method'],
                'funnel_stage': candidate['funnel_stage']
            }
            link_records.append(link_record)
        
        return link_records

    async def _process_hierarchy_links_simple(self, internal_linking: Dict, architecture_id: str) -> List[Dict]:
        """
        📋 Przetwarza hierarchy links bez quality gates (zawsze dodawane)
        """
        hierarchy_links = []
        try:
            vertical_links = internal_linking.get('vertical_linking', [])
            logger.info(f"📋 [HIERARCHY] Przetwarzanie {len(vertical_links)} linków hierarchicznych")
            
            for link in vertical_links:
                from_url = link.get('from_page', '')
                to_url = link.get('to_page', '')
                
                # Resolve URLs do page_ids
                from_page = await self._resolve_to_page_id(
                    architecture_id=architecture_id,
                    url_path=from_url
                )
                to_page = await self._resolve_to_page_id(
                    architecture_id=architecture_id,
                    url_path=to_url
                )
                
                if not from_page or not to_page:
                    logger.warning(f"⚠️ [HIERARCHY] Nie zmapowano: {from_url} → {to_url}")
                    continue
                
                hierarchy_link = {
                    'architecture_id': architecture_id,
                    'from_page_id': from_page['id'],
                    'to_page_id': to_page['id'],
                    'link_type': 'hierarchy',
                    'anchor_text': link.get('anchor_text', ''),
                    'placement': link.get('placement', ''),
                    'priority': 100,  # Highest priority for hierarchical links
                    'source': 'vertical_linking',
                    'enabled': True,
                    'link_context': 'Hierarchical navigation link',
                    'resolution_method': 'url_resolution'
                }
                hierarchy_links.append(hierarchy_link)
            
            logger.info(f"✅ [HIERARCHY] Przetworzono {len(hierarchy_links)} linków hierarchicznych")
            return hierarchy_links
            
        except Exception as e:
            logger.error(f"❌ [HIERARCHY] Błąd przetwarzania linków hierarchicznych: {e}")
            return []

    async def _reread_saved_links(self, architecture_id: str) -> Dict:
        """
        🔄 Re-read zapisanych linków z DB dla zwrócenia do UI, z JOIN do obu stron i wzbogaceniem pól
        """
        try:
            response = self.supabase.table('architecture_links').select(
                'id, from_page_id, to_page_id, link_type, anchor_text, priority, source, '
                'confidence_score, similarity_score, funnel_stage, placement, link_context, '
                'from_title, to_title, from_url, to_url, '
                'from_page:architecture_pages!architecture_links_from_page_id_fkey(name, url_path, cluster_name), '
                'to_page:architecture_pages!architecture_links_to_page_id_fkey(name, url_path, cluster_name)'
            ).eq('architecture_id', architecture_id).order('priority', desc=True).execute()
            
            data = response.data or []
            if not data:
                return {
                    'strategic_bridges': [],
                    'funnel_links': [],
                    'hierarchy_links': [],
                    'total_links': 0,
                    'links': []
                }

            # Enrich rows with from/to titles/urls + normalized similarity
            enriched: list[dict] = []
            for row in data:
                from_meta = row.get('from_page') or {}
                to_meta = row.get('to_page') or {}
                snap_from_url = row.get('from_url')
                snap_to_url = row.get('to_url')
                snap_from_title = row.get('from_title')
                snap_to_title = row.get('to_title')

                # Primary: użyj snapshotów jeśli są
                from_url = snap_from_url or (from_meta.get('url_path') or '')
                to_url = snap_to_url or (to_meta.get('url_path') or '')

                # Fallback tytułów: snapshot → name → cluster_name → segment z URL → 'Unknown'
                def pick_title(snap_title, meta, url):
                    if snap_title:
                        return snap_title
                    return (
                        meta.get('name')
                        or meta.get('cluster_name')
                        or (url or '').rstrip('/').split('/')[-1]
                        or 'Unknown'
                    )

                from_title = pick_title(snap_from_title, from_meta, from_url)
                to_title = pick_title(snap_to_title, to_meta, to_url)

                # similarity: prefer similarity_score; fallback to confidence_score; normalize to 0..1
                sim = row.get('similarity_score')
                if sim is None:
                    sim = row.get('confidence_score')
                # if similarity came in 0..100, normalize
                if isinstance(sim, (int, float)) and sim > 1:
                    sim = sim / 100.0

                enriched.append({
                    **row,
                    'from_url': from_url,
                    'to_url': to_url,
                    'from_title': from_title,
                    'to_title': to_title,
                    'similarity': float(sim) if isinstance(sim, (int, float)) else None,
                    'priority': row.get('priority') or 0,
                    'funnel_stage': row.get('funnel_stage') or ""
                })

            # Grupowanie po typie
            hierarchy_links = [l for l in enriched if l.get('link_type') == 'hierarchy']
            bridge_links = [l for l in enriched if l.get('link_type') == 'bridge']
            funnel_links = [l for l in enriched if l.get('link_type') == 'funnel']

            logger.info(
                f"🔄 [REREAD] Z DB: {len(enriched)} linków (hierarchy={len(hierarchy_links)}, bridge={len(bridge_links)}, funnel={len(funnel_links)})"
            )
            logger.info(
                f"🌉 [DISPLAY] strategic_bridges: {len(bridge_links)} | 🔗 funnel: {len(funnel_links)} | ⬆️ hierarchy: {len(hierarchy_links)}"
            )

            # Warn missing URLs
            for l in enriched:
                if not l.get('from_url') or not l.get('to_url'):
                    logger.warning(f"⚠️ [DISPLAY] Missing URL for link_id={l.get('id')}")

            return {
                'strategic_bridges': bridge_links,
                'funnel_links': funnel_links,
                'hierarchy_links': hierarchy_links,
                'total_links': len(enriched),
                'links': enriched
            }
            
        except Exception as e:
            logger.error(f"❌ [REREAD] Błąd re-read z DB: {e}")
            return {
                'strategic_bridges': [],
                'funnel_links': [],
                'hierarchy_links': [],
                'total_links': 0,
                'links': []
            }

    async def _simple_url_to_page(self, architecture_id: str, url_path: str) -> Optional[Dict]:
        """PROSTY mapping URL na stronę"""
        try:
            normalized_url = (url_path or '').strip('/')
            response = self.supabase.table('architecture_pages').select('id, name, url_path').eq(
                'architecture_id', architecture_id
            ).execute()
            for page in (response.data or []):
                page_url = (page.get('url_path') or '').strip('/')
                if page_url == normalized_url:
                    return page
            return None
        except Exception:
            return None

    async def _simple_cluster_to_page(self, architecture_id: str, cluster_name: str) -> Optional[Dict]:
        """PROSTY mapping klastra na stronę - exact/fuzzy match"""
        try:
            if not cluster_name:
                return None
            response = self.supabase.table('architecture_pages').select('id, name, cluster_name, url_path').eq(
                'architecture_id', architecture_id
            ).execute()
            # Exact cluster_name match
            for page in (response.data or []):
                if (page.get('cluster_name') or '').lower() == (cluster_name or '').lower():
                    return page
            # Fuzzy: substring in name
            cl = (cluster_name or '').lower()
            for page in (response.data or []):
                name_l = (page.get('name') or '').lower()
                if cl in name_l or name_l in cl:
                    return page
            return (response.data or [None])[0]
        except Exception:
            return None

    async def _save_architecture_links_simple(self, architecture_id: str, internal_linking: Dict, 
                                             strategic_bridges: List[Dict], funnel_audit: Dict) -> Dict:
        """🔥 PROSTY zapis linków - BEZ Top-K selection"""
        try:
            logger.info(f"🔗 [LINKS] PROSTY zapis linków dla architecture: {architecture_id}")
            # DEBUG: Co faktycznie jest w bazie danych i porównanie z AI bridges
            try:
                db_pages_response = self.supabase.table('architecture_pages').select('name, url_path, page_type').eq('architecture_id', architecture_id).execute()
                db_pages = db_pages_response.data or []
                logger.info(f"🔍 [DB_DEBUG] W bazie danych jest {len(db_pages)} stron:")
                for page in db_pages:
                    logger.info(f"🔍 [DB_DEBUG] DB Page: {page.get('name')} → {page.get('url_path')} ({page.get('page_type')})")

                logger.info(f"🔍 [COMPARE_DEBUG] Comparing AI bridges vs DB pages:")
                for bridge in (strategic_bridges or [])[:3]:
                    from_url = bridge.get('from_url', '')
                    to_url = bridge.get('to_url', '')
                    from_exists = any((p.get('url_path') or '').strip('/') == (from_url or '').strip('/') for p in db_pages)
                    to_exists = any((p.get('url_path') or '').strip('/') == (to_url or '').strip('/') for p in db_pages)
                    logger.info(f"🔍 [COMPARE_DEBUG] Bridge: {from_url} → {to_url} | from_exists: {from_exists} | to_exists: {to_exists}")
            except Exception as debug_err:
                logger.error(f"❌ [DB_DEBUG] Debug pages query failed: {debug_err}")
            links_to_save: List[Dict] = []

            # 1) Hierarchy links
            vertical_links = internal_linking.get('vertical_linking', [])
            for link in vertical_links:
                from_page = await self._simple_url_to_page(architecture_id, link.get('from_page', ''))
                to_page = await self._simple_url_to_page(architecture_id, link.get('to_page', ''))
                if from_page and to_page:
                    links_to_save.append({
                        'architecture_id': architecture_id,
                        'from_page_id': from_page['id'],
                        'to_page_id': to_page['id'],
                        'link_type': 'hierarchy',
                        'anchor_text': link.get('anchor_text', ''),
                        'placement': link.get('placement', []),
                        'priority': 100,
                        'source': 'vertical_linking',
                        'enabled': True,
                        'link_context': 'Hierarchical navigation link',
                        'from_title': from_page.get('name', ''),
                        'to_title': to_page.get('name', ''),
                        'from_url': f"https://{self.domain}{from_page.get('url_path', '')}",
                        'to_url': f"https://{self.domain}{to_page.get('url_path', '')}"
                    })

            # 2) Strategic bridges (TOP 3 ONLY) - z deduplikacją i DEBUG
            logger.info(f"🔗 [SAVE_DEBUG] Processing {len(strategic_bridges or [])} strategic bridges")
            bridge_keys_seen = set()
            successful_bridges = 0
            failed_bridges = 0
            # Zbierz klucze mostów dla późniejszej ekskluzywności (para+anchor)
            bridge_exact_keys = set()
            for bridge in (strategic_bridges or [])[:3]:
                from_page = await self._simple_url_to_page(architecture_id, bridge.get('from_url', ''))
                to_page = await self._simple_url_to_page(architecture_id, bridge.get('to_url', ''))
                if from_page and to_page:
                    successful_bridges += 1
                    logger.info(f"✅ [SAVE_DEBUG] Bridge mapped: {bridge.get('from_url','')} → {bridge.get('to_url','')} | from_id: {from_page['id']} | to_id: {to_page['id']}")
                    bridge_key = (from_page['id'], to_page['id'], 'bridge')
                    if bridge_key in bridge_keys_seen:
                        logger.warning(f"⚠️ [LINKS] Duplikat bridge pominięty: {from_page['id']}→{to_page['id']}")
                    else:
                        bridge_keys_seen.add(bridge_key)
                        placement_list = (bridge.get('implementation', {}) or {}).get('placement', ['mid_content'])
                        links_to_save.append({
                            'architecture_id': architecture_id,
                            'from_page_id': from_page['id'],
                            'to_page_id': to_page['id'],
                            'link_type': 'bridge',
                            'anchor_text': bridge.get('suggested_anchor', ''),
                            'placement': placement_list,
                            'priority': (bridge.get('implementation', {}) or {}).get('priority', 80),
                            'similarity_score': bridge.get('similarity_score', 0),
                            'source': 'strategic_bridges',
                            'enabled': True,
                            'link_context': f"Strategic bridge ({bridge.get('similarity_score', 0):.1f}% similarity)",
                            'from_title': from_page.get('name', ''),
                            'to_title': to_page.get('name', ''),
                            'from_url': f"https://{self.domain}{from_page.get('url_path', '')}",
                            'to_url': f"https://{self.domain}{to_page.get('url_path', '')}"
                        })
                        # zapamiętaj dokładny klucz dla ekskluzywności z funnelem
                        bx_anchor = (bridge.get('suggested_anchor', '') or '').strip().lower()
                        bridge_exact_keys.add((from_page['id'], to_page['id'], bx_anchor))
                else:
                    failed_bridges += 1
                    logger.info(f"❌ [SAVE_DEBUG] Bridge mapping FAILED: {bridge.get('from_url','')} → {bridge.get('to_url','')} | from_page: {from_page is not None} | to_page: {to_page is not None}")
                    if not from_page:
                        logger.error(f"❌ [MAPPING_DEBUG] FROM_PAGE missing for URL: '{bridge.get('from_url', '')}' - check if page exists in architecture_pages")
                    if not to_page:
                        logger.error(f"❌ [MAPPING_DEBUG] TO_PAGE missing for URL: '{bridge.get('to_url', '')}' - check if page exists in architecture_pages")
            logger.info(f"🔗 [SAVE_DEBUG] Strategic bridge mapping: success={successful_bridges}, failed={failed_bridges}")

            # 3) Funnel links (jeśli są)
            if funnel_audit.get('should_modify_structure', False):
                modified_bridges = funnel_audit.get('modified_strategic_bridges', [])
                funnel_keys_seen = set()
                for bridge in (modified_bridges or []):
                    from_page = await self._simple_url_to_page(architecture_id, bridge.get('from_url', ''))
                    to_page = await self._simple_url_to_page(architecture_id, bridge.get('to_url', ''))
                    if from_page and to_page:
                        funnel_key = (from_page['id'], to_page['id'], 'funnel')
                        if funnel_key in funnel_keys_seen:
                            logger.warning(f"⚠️ [LINKS] Duplikat funnel pominięty: {from_page['id']}→{to_page['id']}")
                        else:
                            # Ekskluzywność cross-type: odrzuć funnel jeżeli para+anchor identyczne do strategic
                            fx_anchor_norm = (bridge.get('suggested_anchor', '') or '').strip().lower()
                            if (from_page['id'], to_page['id'], fx_anchor_norm) in bridge_exact_keys:
                                logger.info(f"🚫 [SAVE_DEBUG] Skip funnel duplicate of bridge (exact match by pair+anchor): {from_page['id']}→{to_page['id']} | anchor='{bridge.get('suggested_anchor','')[:60]}'")
                                continue

                            funnel_keys_seen.add(funnel_key)
                            placement_list = (bridge.get('implementation', {}) or {}).get('placement', ['mid_content'])
                            links_to_save.append({
                                'architecture_id': architecture_id,
                                'from_page_id': from_page['id'],
                                'to_page_id': to_page['id'],
                                'link_type': 'funnel',
                                'anchor_text': bridge.get('suggested_anchor', ''),
                                'placement': placement_list,
                                'priority': (bridge.get('implementation', {}) or {}).get('priority', 85),
                                'funnel_stage': bridge.get('funnel_stage', ''),
                                'rationale': bridge.get('rationale', ''),
                                'source': 'funnel_audit',
                                'enabled': True,
                                'link_context': 'Funnel-optimized link',
                                'confidence_score': 0.92,
                                'from_title': from_page.get('name', ''),
                                'to_title': to_page.get('name', ''),
                                'from_url': f"https://{self.domain}{from_page.get('url_path', '')}",
                                'to_url': f"https://{self.domain}{to_page.get('url_path', '')}"
                            })

            # 3b) Cross-type dedupe removed: sesje są rozłączne; pozostawiamy pełne dane z obu mechanik

            # FINAL SUMMARY przed return (przed zapisem)
            try:
                bridge_count = len([l for l in links_to_save if l.get('link_type') == 'bridge'])
                funnel_count = len([l for l in links_to_save if l.get('link_type') == 'funnel'])
                hierarchy_count = len([l for l in links_to_save if l.get('link_type') == 'hierarchy'])
                logger.info(f"🔗 [SAVE_DEBUG] FINAL links_to_save breakdown: bridge={bridge_count}, funnel={funnel_count}, hierarchy={hierarchy_count}, total={len(links_to_save)}")
            except Exception:
                pass

            # 4) BATCH INSERT z deduplikacją i error handling
            if links_to_save:
                # DEDUPE pre-insert
                seen_keys = set()
                deduped_links = []
                for link in links_to_save:
                    key = (link['from_page_id'], link['to_page_id'], link['link_type'])
                    if key not in seen_keys:
                        deduped_links.append(link)
                        seen_keys.add(key)
                    else:
                        logger.warning(f"⚠️ [LINKS] Duplikat usunięty: {link['link_type']} {link.get('anchor_text','')[:30]}...")

                logger.info(f"🔧 [LINKS] Deduplikacja: {len(links_to_save)} → {len(deduped_links)} linków")

                # DELETE z error handling
                try:
                    delete_resp = self.supabase.table('architecture_links').delete().eq('architecture_id', architecture_id).execute()
                    deleted_count = len(delete_resp.data or [])
                    logger.info(f"🗑️ [LINKS] Usunięto {deleted_count} starych linków")
                except Exception as e:
                    logger.error(f"❌ [LINKS] Delete failed: {e}")
                    return {'strategic_bridges': [], 'funnel_links': [], 'hierarchy_links': [], 'total_links': 0}

                # INSERT z error handling
                try:
                    insert_resp = self.supabase.table('architecture_links').insert(deduped_links).execute()
                    inserted_count = len(insert_resp.data or [])
                    logger.info(f"✅ [LINKS] PROSTY zapis: {inserted_count} linków zapisanych")
                    return {
                        'strategic_bridges': [l for l in deduped_links if l['link_type'] == 'bridge'],
                        'funnel_links': [l for l in deduped_links if l['link_type'] == 'funnel'],
                        'hierarchy_links': [l for l in deduped_links if l['link_type'] == 'hierarchy'],
                        'total_links': len(deduped_links)
                    }
                except Exception as e:
                    logger.error(f"❌ [LINKS] Insert failed: {e}")
                    logger.error(f"❌ [LINKS] Error details: {str(e)}")
                    return {'strategic_bridges': [], 'funnel_links': [], 'hierarchy_links': [], 'total_links': 0}

            return {'strategic_bridges': [], 'funnel_links': [], 'hierarchy_links': [], 'total_links': 0}

        except Exception as e:
            logger.error(f"❌ [LINKS] PROSTY zapis failed: {e}")
            return {'strategic_bridges': [], 'funnel_links': [], 'hierarchy_links': [], 'total_links': 0}

    async def _create_url_to_page_mapping(self, architecture_id: str) -> Dict[str, str]:
        """
        🗺️ Tworzy mapowanie URL → page_id dla danej architektury z normalizacją ścieżek
        """
        try:
            response = self.supabase.table('architecture_pages').select(
                'id, url_path'
            ).eq('architecture_id', architecture_id).execute()
            
            if not response.data:
                logger.warning(f"⚠️ [MAPPING] Brak stron dla architecture: {architecture_id}")
                return {}
            
            url_mapping = {}
            for page in response.data:
                normalized_url = self._norm_path(page['url_path'])
                url_mapping[normalized_url] = page['id']
            
            logger.info(f"🗺️ [MAPPING] Utworzono mapowanie dla {len(url_mapping)} stron")
            return url_mapping
            
        except Exception as e:
            logger.error(f"❌ [MAPPING] Błąd tworzenia mapowania URL→page_id: {e}")
            return {}

    def _norm_path(self, url_path: str) -> str:
        """
        🔧 Normalizuje ścieżkę URL (usuwa leading/trailing slashes dla spójności)
        """
        if not url_path:
            return ""
        # Usuń leading i trailing slashes, zostaw tylko content
        return url_path.strip('/')

    async def _process_hierarchy_links(self, internal_linking: Dict, url_to_page_map: Dict, 
                                     architecture_id: str) -> List[Dict]:
        """
        📋 Przetwarza linki hierarchiczne z internal_linking.vertical_linking
        """
        hierarchy_links = []
        try:
            vertical_links = internal_linking.get('vertical_linking', [])
            logger.info(f"📋 [HIERARCHY] Przetwarzanie {len(vertical_links)} linków hierarchicznych")
            
            for link in vertical_links:
                from_url = self._norm_path(link.get('from_page', ''))
                to_url = self._norm_path(link.get('to_page', ''))
                
                from_page_id = url_to_page_map.get(from_url)
                to_page_id = url_to_page_map.get(to_url)
                
                if not from_page_id or not to_page_id:
                    logger.warning(f"⚠️ [HIERARCHY] Nie zmapowano: {from_url} → {to_url}")
                    continue
                
                hierarchy_link = {
                    'architecture_id': architecture_id,
                    'from_page_id': from_page_id,
                    'to_page_id': to_page_id,
                    'link_type': 'hierarchy',
                    'anchor_text': link.get('anchor_text', ''),
                    'placement': link.get('placement', ''),
                    'priority': 100,  # Highest priority for hierarchical links
                    'source': 'vertical_linking',
                    'enabled': True,
                    'link_context': 'Hierarchical navigation link'
                }
                hierarchy_links.append(hierarchy_link)
            
            logger.info(f"✅ [HIERARCHY] Przetworzono {len(hierarchy_links)} linków hierarchicznych")
            return hierarchy_links
            
        except Exception as e:
            logger.error(f"❌ [HIERARCHY] Błąd przetwarzania linków hierarchicznych: {e}")
            return []

    async def _process_strategic_bridge_links(self, strategic_bridges: List[Dict], 
                                            url_to_page_map: Dict, architecture_id: str) -> List[Dict]:
        """
        🌉 Przetwarza strategic bridges - mapuje klastry na strony i tworzy linki
        """
        bridge_links = []
        try:
            logger.info(f"🌉 [BRIDGES] Przetwarzanie {len(strategic_bridges)} strategic bridges")
            
            for bridge in strategic_bridges:
                from_cluster = bridge.get('from_cluster', '')
                to_cluster = bridge.get('to_cluster', '')
                
                # Znajdź strony dla klastrów
                from_pages = await self._find_pages_for_cluster(from_cluster, architecture_id)
                to_pages = await self._find_pages_for_cluster(to_cluster, architecture_id)
                
                if not from_pages or not to_pages:
                    logger.warning(f"⚠️ [BRIDGES] Nie znaleziono stron dla bridge: {from_cluster} → {to_cluster}")
                    continue
                
                # Stwórz linki między pierwszymi stronami klastrów (main pages)
                from_page_id = from_pages[0]['id']
                to_page_id = to_pages[0]['id']
                
                # Obsłuż placement jako listę → CSV string
                placement = bridge.get('implementation', {}).get('placement', ['natural_flow'])
                if isinstance(placement, list):
                    placement_str = ', '.join(placement)
                else:
                    placement_str = str(placement)
                
                bridge_link = {
                    'architecture_id': architecture_id,
                    'from_page_id': from_page_id,
                    'to_page_id': to_page_id,
                    'link_type': 'bridge',
                    'anchor_text': bridge.get('suggested_anchor', ''),
                    'placement': placement_str,
                    'priority': bridge.get('implementation', {}).get('priority', 75),
                    'similarity_score': bridge.get('similarity_score', 0.0),
                    'source': 'strategic_bridges',
                    'enabled': True,
                    'link_context': f"Strategic cross-link (similarity: {bridge.get('similarity_score', 0):.1f}%)"
                }
                bridge_links.append(bridge_link)
            
            logger.info(f"✅ [BRIDGES] Przetworzono {len(bridge_links)} strategic bridge links")
            return bridge_links
            
        except Exception as e:
            logger.error(f"❌ [BRIDGES] Błąd przetwarzania strategic bridges: {e}")
            return []

    async def _process_funnel_audit_links(self, funnel_audit: Dict, url_to_page_map: Dict, 
                                        architecture_id: str) -> List[Dict]:
        """
        🎯 Przetwarza linki z funnel audit (modified_strategic_bridges)
        """
        funnel_links = []
        try:
            if not funnel_audit.get('should_modify_structure', False):
                logger.info(f"🎯 [FUNNEL] Funnel audit nie rekomenduje modyfikacji - pomijam funnel links")
                return funnel_links
            
            modified_bridges = funnel_audit.get('modified_strategic_bridges', [])
            logger.info(f"🎯 [FUNNEL] Przetwarzanie {len(modified_bridges)} funnel-optimized bridges")
            
            for bridge in modified_bridges:
                from_cluster = bridge.get('from_cluster', '')
                to_cluster = bridge.get('to_cluster', '')
                
                # Znajdź strony dla klastrów
                from_pages = await self._find_pages_for_cluster(from_cluster, architecture_id)
                to_pages = await self._find_pages_for_cluster(to_cluster, architecture_id)
                
                if not from_pages or not to_pages:
                    logger.warning(f"⚠️ [FUNNEL] Nie znaleziono stron dla funnel bridge: {from_cluster} → {to_cluster}")
                    continue
                
                from_page_id = from_pages[0]['id']
                to_page_id = to_pages[0]['id']
                
                # Obsłuż placement jako listę → CSV string
                placement = bridge.get('implementation', {}).get('placement', ['natural_flow'])
                if isinstance(placement, list):
                    placement_str = ', '.join(placement)
                else:
                    placement_str = str(placement)
                
                funnel_link = {
                    'architecture_id': architecture_id,
                    'from_page_id': from_page_id,
                    'to_page_id': to_page_id,
                    'link_type': 'funnel',
                    'anchor_text': bridge.get('suggested_anchor', ''),
                    'placement': placement_str,
                    'priority': bridge.get('implementation', {}).get('priority', 85),
                    'funnel_stage': bridge.get('funnel_stage', ''),
                    'source': 'funnel_audit',
                    'enabled': True,
                    'link_context': f"Funnel-optimized link ({bridge.get('funnel_stage', 'unknown')} stage)"
                }
                funnel_links.append(funnel_link)
            
            logger.info(f"✅ [FUNNEL] Przetworzono {len(funnel_links)} funnel-optimized links")
            return funnel_links
            
        except Exception as e:
            logger.error(f"❌ [FUNNEL] Błąd przetwarzania funnel audit links: {e}")
            return []

    async def _resolve_to_page_id(self, *, architecture_id: str, cluster_name: str = "", 
                                 url_path: str = "") -> Optional[dict]:
        """
        🎯 ENHANCED: Resolver cluster/page → page_id z kaskadą exact/fuzzy matching
        
        Zwraca rekord strony {id, name, cluster_name, url_path} lub None.
        Kaskada: url_path → exact cluster_name → strict fuzzy ≥ 0.90.
        """
        try:
            sel = 'id, name, cluster_name, url_path'
            
            # 1) url_path exact (ze slashem i bez)
            if url_path:
                up = url_path.strip().strip('/')
                rows = self.supabase.table('architecture_pages').select(sel).eq(
                    'architecture_id', architecture_id
                ).execute().data or []
                for row in rows:
                    rp = (row.get('url_path') or '').strip().strip('/')
                    if rp == up or rp.rstrip('/') == up.rstrip('/'):
                        logger.info(f"🎯 [RESOLVE] URL path match: {url_path} → {row['id']}")
                        return row
            
            # 2) cluster_name exact
            if cluster_name:
                r = self.supabase.table('architecture_pages').select(sel).eq(
                    'architecture_id', architecture_id
                ).eq('cluster_name', cluster_name).execute().data or []
                if r: 
                    logger.info(f"🎯 [RESOLVE] Exact cluster name match: {cluster_name} → {r[0]['id']}")
                    return r[0]
            
            # 3) strict fuzzy ≥ 0.80
            if cluster_name:
                rows = self.supabase.table('architecture_pages').select(sel).eq(
                    'architecture_id', architecture_id
                ).execute().data or []
                best = None
                best_sim = 0.0
                for row in rows:
                    # Próbuj fuzzy z cluster_name i z name
                    for field in ['cluster_name', 'name']:
                        target = row.get(field) or ''
                        sim = _fuzzy_sim(cluster_name, target)
                        if sim > best_sim:
                            best = row
                            best_sim = sim
                
                if best and best_sim >= 0.80:
                    logger.info(f"🎯 [RESOLVE] Fuzzy match: {cluster_name} → {best.get('name') or best.get('cluster_name')} (sim: {best_sim:.2f})")
                    return best
                elif best_sim > 0.0:
                    logger.warning(f"⚠️ [RESOLVE] Low fuzzy sim: {cluster_name} → best {best_sim:.2f} < 0.80")

            # 4) Fallback: dopasowanie po końcówce ścieżki URL (last segment)
            def _last_segment(p: str) -> str:
                try:
                    if not p:
                        return ''
                    s = p.strip().rstrip('/')
                    return s.split('/')[-1]
                except Exception:
                    return ''

            if url_path:
                try:
                    up_last = _last_segment(url_path)
                    if up_last:
                        rows = self.supabase.table('architecture_pages').select(sel).eq(
                            'architecture_id', architecture_id
                        ).execute().data or []
                        for row in rows:
                            rp_last = _last_segment(row.get('url_path') or '')
                            if rp_last and rp_last.lower() == up_last.lower():
                                logger.info(f"🎯 [RESOLVE] URL last-segment match: {up_last} → {row.get('name') or row.get('cluster_name')} ({row.get('url_path')})")
                                return row
                except Exception as e:
                    logger.warning(f"⚠️ [RESOLVE] URL last-segment fallback failed: {e}")
            
            logger.warning(f"⚠️ [RESOLVE] No match found for: cluster_name='{cluster_name}', url_path='{url_path}'")
            return None
            
        except Exception as e:
            logger.error(f"❌ [RESOLVE] Error resolving to page_id: {e}")
            return None

    async def _find_pages_for_cluster(self, cluster_name: str, architecture_id: str) -> List[Dict]:
        """
        🔍 LEGACY WRAPPER: Kompatybilność z istniejącym kodem
        """
        try:
            result = await self._resolve_to_page_id(
                architecture_id=architecture_id, 
                cluster_name=cluster_name
            )
            return [result] if result else []
        except Exception as e:
            logger.error(f"❌ [CLUSTER_PAGES] Błąd wyszukiwania stron dla klastra '{cluster_name}': {e}")
            return []

    async def _batch_insert_links_with_deduplication(self, links_to_save: List[Dict], 
                                                   architecture_id: str) -> None:
        """
        💾 Wykonuje batch insert linków z deduplikacją (usuwa stare, wstawia nowe)
        """
        try:
            if not links_to_save:
                return
            
            logger.info(f"💾 [BATCH] Rozpoczynam batch insert {len(links_to_save)} linków")

            # SNAPSHOT: Pobierz meta stron aby zbudować from_title/to_title oraz from_url/to_url
            pages_meta: Dict[str, Dict] = {}
            try:
                pages_resp = self.supabase.table('architecture_pages').select(
                    'id, name, url_path, cluster_name'
                ).eq('architecture_id', architecture_id).execute()
                for p in (pages_resp.data or []):
                    pages_meta[p['id']] = p
                logger.info(f"💾 [BATCH] Załadowano meta {len(pages_meta)} stron do snapshotu linków")
            except Exception as meta_err:
                logger.warning(f"⚠️ [BATCH] Nie udało się pobrać meta stron do snapshotu: {meta_err}")

            def build_full_url(url_path: str) -> str:
                if not url_path:
                    return ''
                # Jeżeli mamy domenę, zbuduj pełny URL; w innym wypadku zwróć sam url_path
                try:
                    base = self.domain.strip() if getattr(self, 'domain', None) else ''
                    if base:
                        # Upewnij się, że nie powielamy ukośników
                        if not url_path.startswith('/'):
                            url_path_norm = '/' + url_path
                        else:
                            url_path_norm = url_path
                        return f"https://{base}{url_path_norm}"
                except Exception:
                    pass
                return url_path

            def fallback_title(meta: Dict, url_path: str) -> str:
                name = (meta or {}).get('name')
                cluster = (meta or {}).get('cluster_name')
                if name:
                    return name
                if cluster:
                    return cluster
                segment = (url_path or '').rstrip('/').split('/')[-1]
                return segment or 'Unknown'

            # Uzupełnij snapshoty w każdym rekordzie zanim zapiszemy do DB
            for link in links_to_save:
                # FROM
                if not link.get('from_title') or not link.get('from_url'):
                    meta_from = pages_meta.get(link.get('from_page_id'))
                    url_from_path = (meta_from or {}).get('url_path') or ''
                    url_from = link.get('from_url') or build_full_url(url_from_path)
                    title_from = link.get('from_title') or fallback_title(meta_from, url_from_path)
                    link['from_url'] = url_from
                    link['from_title'] = title_from
                # TO
                if not link.get('to_title') or not link.get('to_url'):
                    meta_to = pages_meta.get(link.get('to_page_id'))
                    url_to_path = (meta_to or {}).get('url_path') or ''
                    url_to = link.get('to_url') or build_full_url(url_to_path)
                    title_to = link.get('to_title') or fallback_title(meta_to, url_to_path)
                    link['to_url'] = url_to
                    link['to_title'] = title_to
            
            # KROK 1: Usuń istniejące linki dla tej architektury (idempotencja)
            delete_response = self.supabase.table('architecture_links').delete().eq(
                'architecture_id', architecture_id
            ).execute()
            
            deleted_count = len(delete_response.data) if delete_response.data else 0
            if deleted_count > 0:
                logger.info(f"🗑️ [BATCH] Usunięto {deleted_count} istniejących linków")
            
            # KROK 2: Batch insert nowych linków
            insert_response = self.supabase.table('architecture_links').insert(links_to_save).execute()
            
            if insert_response.data:
                inserted_count = len(insert_response.data)
                logger.info(f"✅ [BATCH] Wstawiono {inserted_count} nowych linków do architecture_links")
            else:
                logger.warning(f"⚠️ [BATCH] Insert zwrócił pustą odpowiedź")
            
        except Exception as e:
            logger.error(f"❌ [BATCH] Błąd batch insert architecture_links: {e}")
            raise  # Re-raise to allow caller to handle

    def _extract_slug_from_url(self, url_path: str) -> str:
        """Extractuje slug z url_path"""
        if not url_path:
            return ""
        # Usuń leading/trailing slashes i weź ostatni segment
        clean_path = url_path.strip('/')
        if '/' in clean_path:
            return clean_path.split('/')[-1]
        return clean_path

    def _extract_keywords_from_cluster(self, cluster_data: Dict, phrases_with_details: List) -> List[str]:
        """Extractuje keywords z cluster_data"""
        keywords = []
        
        # Z cluster_data
        if cluster_data.get('phrases'):
            keywords.extend(cluster_data['phrases'][:5])  # Top 5
        
        # Z phrases_with_details
        for phrase_detail in phrases_with_details[:3]:  # Top 3
            if isinstance(phrase_detail, dict) and phrase_detail.get('phrase'):
                keywords.append(phrase_detail['phrase'])
            elif isinstance(phrase_detail, str):
                keywords.append(phrase_detail)
        
        # Deduplikacja i limit
        unique_keywords = list(dict.fromkeys(keywords))  # Preserve order, remove duplicates
        return unique_keywords[:10]  # Max 10 keywords


class ArchitectureDatabase:
    """Klasa do zapisu architektur w Supabase - ORYGINALNA WERSJA"""
    
    def __init__(self, supabase_client):
        self.supabase = supabase_client
    
    def convert_numpy_types(self, obj):
        """Konwertuje NumPy types do JSON serializable types"""
        if isinstance(obj, np.float32) or isinstance(obj, np.float64):
            return float(obj)
        elif isinstance(obj, np.int32) or isinstance(obj, np.int64):
            return int(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif isinstance(obj, dict):
            return {key: self.convert_numpy_types(value) for key, value in obj.items()}
        elif isinstance(obj, list):
            return [self.convert_numpy_types(item) for item in obj]
        return obj
    
    def save_architecture(self, architecture_result: Dict, user_id: str = None) -> Dict:
        """Zapisuje architekturę do bazy danych - ORYGINALNE POLA"""
        try:
            import uuid
            from datetime import datetime
            
            # Konwertuj NumPy types do JSON serializable
            clean_result = self.convert_numpy_types(architecture_result)
            
            # ORYGINALNE POLA KTÓRE ISTNIEJĄ W TABELI + NOWE WYMAGANE POLA
            record = {
                'semantic_cluster_id': clean_result.get('semantic_cluster_id'),
                'name': f"{clean_result['seed_keyword']} - {clean_result['architecture_type'].upper()}",
                'architecture_type': clean_result['architecture_type'],
                'seed_keyword': clean_result['seed_keyword'],
                'domain': clean_result.get('domain', 'example.com'),
                'hierarchy': clean_result['hierarchy'],
                'seo_score': int(clean_result.get('seo_score', 0)),
                'total_pages': clean_result.get('stats', {}).get('total_pages', 0),
                'max_depth': clean_result.get('stats', {}).get('max_depth', 1),
                'cross_links_count': clean_result.get('stats', {}).get('cross_links_found', 0),
                'total_phrases': 0,  # Default value
                'groups_found': len(clean_result.get('groups', [])) if clean_result.get('groups') else 0,
                'quality_score': float(clean_result.get('stats', {}).get('avg_similarity', 0.0)),
                'content_opportunities_found': clean_result.get('stats', {}).get('content_opportunities_found', 0),
                'new_pages_from_paa': clean_result.get('stats', {}).get('new_pages_from_paa', 0),
                'paa_analyzed': True,
                'ai_overview_analyzed': True,
                'user_id': user_id,
                'created_at': datetime.utcnow().isoformat()
            }
            
            # Zapisz architekturę do tabeli z PRAWIDŁOWYM SCHEMATEM
            response = self.supabase.table('architectures').insert(record).execute()
            
            if not response.data:
                return {'success': False, 'error': 'Failed to save architecture'}
            
            architecture_id = response.data[0]['id']
            
            # Update funnel audit with architecture_id if exists
            try:
                if hasattr(self, '_temp_funnel_audit_id'):
                    self.supabase.table('funnel_audits').update({
                        'architecture_id': architecture_id
                    }).eq('id', self._temp_funnel_audit_id).execute()
                    delattr(self, '_temp_funnel_audit_id')
            except Exception as e:
                logger.warning(f"⚠️ [DB] Could not update funnel audit with architecture_id: {e}")
            
            logger.info(f"💾 [DB] Architecture saved successfully: {architecture_id}")
            
            return {
                'success': True,
                'architecture_id': architecture_id,
                'message': 'Architecture saved successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ [DB] Save architecture failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def list_architectures(self, user_id: str = None, semantic_cluster_id: str = None, limit: int = 10, offset: int = 0) -> Dict:
        """Lista architektur"""
        try:
            query = self.supabase.table('architectures').select('*')
            
            if user_id:
                query = query.eq('user_id', user_id)
            if semantic_cluster_id:
                query = query.eq('semantic_cluster_id', semantic_cluster_id)
            
            response = query.order('created_at', desc=True).range(offset, offset + limit - 1).execute()
            
            return {
                'success': True,
                'data': response.data,
                'count': len(response.data)
            }
            
        except Exception as e:
            logger.error(f"❌ [DB] List architectures failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def get_architecture(self, architecture_id: str, user_id: str = None) -> Dict:
        """Pobierz konkretną architekturę"""
        try:
            query = self.supabase.table('architectures').select('*').eq('id', architecture_id)
            
            if user_id:
                query = query.eq('user_id', user_id)
            
            response = query.execute()
            
            if not response.data:
                return {'success': False, 'error': 'Architecture not found'}
            
            return {
                'success': True,
                'data': response.data[0]
            }
            
        except Exception as e:
            logger.error(f"❌ [DB] Get architecture failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def delete_architecture(self, architecture_id: str) -> Dict:
        """Usuń architekturę"""
        try:
            response = self.supabase.table('architectures').delete().eq('id', architecture_id).execute()
            
            return {
                'success': True,
                'message': 'Architecture deleted successfully'
            }
            
        except Exception as e:
            logger.error(f"❌ [DB] Delete architecture failed: {e}")
            return {'success': False, 'error': str(e)}
    
    def save_content_opportunities_fixed(self, architecture_id: str, decisions: list):
        """Zapisuje content opportunities do bazy danych"""
        try:
            if not decisions:
                logger.info(f"📄 [DB] No content opportunities to save for architecture {architecture_id}")
                return {'success': True, 'message': 'No content opportunities to save'}
            
            # NOWE: Pobierz mapowanie URL → page_id dla tej architektury
            pages_mapping = {}
            try:
                pages_response = self.supabase.table('architecture_pages').select(
                    'id, url_path'
                ).eq('architecture_id', architecture_id).execute()
                
                for page in pages_response.data:
                    pages_mapping[page['url_path']] = page['id']
                
                logger.info(f"📄 [DB] Utworzono mapowanie dla {len(pages_mapping)} stron")
            except Exception as e:
                logger.warning(f"⚠️ [DB] Błąd tworzenia mapowania stron: {e}")
            
            # Save each decision as a content opportunity record
            opportunities = []
            for decision in decisions:
                # NOWE: Spróbuj zmapować target_page na page_id
                target_page_id = None
                target_page_url = decision.get('target_page', '')
                
                if target_page_url and target_page_url in pages_mapping:
                    target_page_id = pages_mapping[target_page_url]
                    logger.info(f"📄 [DB] Zmapowano '{target_page_url}' → {target_page_id}")
                elif target_page_url:
                    logger.warning(f"⚠️ [DB] Nie znaleziono page_id dla URL: {target_page_url}")
                
                opportunity = {
                    'architecture_id': architecture_id,
                    'question_or_topic': decision.get('question') or decision.get('topic', ''),
                    'decision': decision.get('decision', 'FAQ'),
                    'source': decision.get('source', 'PAA'),
                    'priority': decision.get('priority', 'medium'),
                    'rationale': decision.get('rationale', ''),
                    'target_page_id': target_page_id,  # ← POPRAWKA: prawdziwy page_id zamiast None
                    'suggested_url': decision.get('suggested_url', ''),
                    'parent_category': decision.get('parent_category', ''),
                    'ai_overview_mentioned': decision.get('source') == 'AI_OVERVIEW'
                    # USUŃ: 'created_at': datetime.utcnow()  - baza ustawi automatycznie
                }
                opportunities.append(opportunity)
            
            # Batch insert to content_opportunities table
            if opportunities:
                response = self.supabase.table('content_opportunities').insert(opportunities).execute()
                
                if response.data:
                    logger.info(f"💾 [DB] Saved {len(opportunities)} content opportunities for architecture {architecture_id}")
                    return {
                        'success': True, 
                        'message': f'Saved {len(opportunities)} content opportunities',
                        'count': len(opportunities)
                    }
                else:
                    logger.warning(f"⚠️ [DB] Failed to save content opportunities for architecture {architecture_id}")
                    return {'success': False, 'error': 'Failed to insert content opportunities'}
            
            return {'success': True, 'message': 'No opportunities to save'}
            
        except Exception as e:
            logger.error(f"❌ [DB] Content opportunities save failed: {e}")
            # Don't crash the whole system - just log and continue
            return {'success': False, 'error': str(e)}