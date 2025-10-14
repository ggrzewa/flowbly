import os
import logging
import json
import asyncio
import difflib
from typing import Dict, List, Optional, Any, Tuple
from datetime import datetime
import uuid

from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from supabase import Client as SupabaseClient

logger = logging.getLogger("content_brief_generator")

class ContentBriefGeneratorService:
    """
    🎯 MODUŁ 4: Generator szczegółowych planów treści
    
    GŁÓWNE ZADANIA:
    1. Pobiera dane z Modułów 1-3 (semantic groups, architecture, PAA)
    2. Generuje strukturę H1/H2/H3 przez AI
    3. Tworzy listy słów kluczowych dla writera
    4. Generuje instrukcje linkowania wewnętrznego
    5. Automatyzuje Schema.org JSON-LD
    6. Zapisuje gotowe briefs do bazy
    """
    
    def __init__(self, supabase_client: SupabaseClient):
        self.supabase = supabase_client
        self.logger = logger
        
        # AI Clients setup - zgodnie z .env jak inne moduły
        self.ai_provider = os.getenv("AI_PROVIDER", "openai").lower()  # Zmieniony default na openai
        
        # Modele z .env
        self.openai_model = os.getenv("AI_MODEL_OPENAI", "gpt-4o")
        self.claude_model = os.getenv("AI_MODEL_CLAUDE", "claude-sonnet-4-20250514")
        self.gpt5_model = os.getenv("AI_MODEL_GPT5", "gpt-5")
        self.gpt5_reasoning_effort = os.getenv("GPT5_REASONING_EFFORT", "medium")
        self.gpt5_verbosity = os.getenv("GPT5_VERBOSITY", "medium")
        
        # OpenAI client
        openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = AsyncOpenAI(api_key=openai_key) if openai_key else None
        
        # Claude client  
        claude_key = os.getenv("ANTHROPIC_API_KEY")
        self.claude_client = AsyncAnthropic(api_key=claude_key) if claude_key else None
        
        self.logger.info(f"🚀 ContentBriefGenerator initialized")
        self.logger.info(f"🔧 [CONFIG] AI_PROVIDER={self.ai_provider}")
        self.logger.info(f"🔧 [CONFIG] AI_MODEL_OPENAI={self.openai_model}")
        self.logger.info(f"🔧 [CONFIG] AI_MODEL_CLAUDE={self.claude_model}")
        self.logger.info(f"🔧 [CONFIG] AI_MODEL_GPT5={self.gpt5_model}")
        self.logger.info(f"🔧 [CONFIG] GPT5_REASONING_EFFORT={self.gpt5_reasoning_effort}")

    async def generate_content_brief(self, page_id: str) -> Dict:
        """
        🎯 GŁÓWNA FUNKCJA - generuje kompletny content brief dla strony
        """
        try:
            start_time = datetime.now().timestamp()
            self.logger.info(f"🚀 [BRIEF] Rozpoczynam generowanie dla page_id: {page_id}")
            # KROK 1: Pobierz dane strony
            page_data = await self._get_page_data(page_id)
            if not page_data:
                return {"success": False, "error": "Nie znaleziono strony"}
            
            # KROK 2: 🧠 NOWE: Pobierz dane psychologii customer journey z Modułu 3
            psychology_data = await self._get_funnel_psychology_data(page_data['architecture_id'])
            
            # KROK 3: 🎯 NOWE: Określ etap customer journey dla tej strony
            funnel_stage = await self._get_page_funnel_stage(page_data, psychology_data)
            
            # KROK 4: Pobierz semantic keywords SPECIFICZNE dla tej strony
            semantic_data = await self._get_semantic_keywords(page_data['architecture_id'], page_data)
            # KROK 5: Pobierz PAA questions  
            faq_data = await self._get_faq_questions(page_data['architecture_id'], page_id)
            # KROK 6: Pobierz linking instructions
            linking_data = await self._get_linking_instructions(page_id)
            # KROK 7: 🧠 ENHANCED: Generuj psychology-aware content structure przez AI
            content_structure = await self._generate_psychology_aware_structure(
                page_data, semantic_data, faq_data, psychology_data, funnel_stage
            )
            # KROK 8: 🧠 ENHANCED: Analizuj intent i generuj psychology-aware tone guidelines
            intent_analysis = await self._get_real_intent_data_for_page(page_data)
            psychology_tone = await self._generate_psychology_tone_guidelines(
                intent_analysis, psychology_data, funnel_stage
            )
            
            # KROK 9: Generuj Schema.org templates
            schema_templates = await self._generate_schema_templates(
                page_data, content_structure, faq_data
            )
            
            # KROK 10: 🧠 ENHANCED: Zapisz psychology-enhanced content brief do bazy
            brief_id = await self._save_psychology_enhanced_brief(
                page_data, semantic_data, content_structure, 
                intent_analysis, psychology_tone, faq_data, linking_data, 
                schema_templates, psychology_data, funnel_stage
            )
            total_time = datetime.now().timestamp() - start_time
            self.logger.info(f"✅ [BRIEF] Wygenerowano psychology-enhanced brief: {brief_id} w {total_time:.1f}s")
            return {
                "success": True,
                "brief_id": brief_id,
                "page_title": page_data['title'],
                "h1_title": content_structure.get('h1_title', ''),
                "sections_count": len(content_structure.get('h2_structure', [])),
                "keywords_count": len(semantic_data.get('primary_keywords', [])),
                "faq_count": len(faq_data.get('questions', [])),
                "funnel_stage": funnel_stage,  # 🧠 NOWE: Psychology context
                "psychology_anchors_count": len(psychology_data.get('psychology_anchors', [])),
                "strategic_bridges_count": len(psychology_data.get('strategic_bridges', [])),
                "psychology_enhanced_count": len([l for l in linking_data.get('internal_links', []) if l.get('rationale')]),
                "confidence_links": len([l for l in linking_data.get('internal_links', []) if (l.get('confidence_score') or 0) > 0.7]),
                "principles_count": len(psychology_data.get('psychology_principles', [])),
                "processing_time": total_time
            }
        except Exception as e:
            self.logger.error(f"❌ [BRIEF] Błąd generowania: {str(e)}")
            return {"success": False, "error": str(e)}

    async def _get_funnel_psychology_data(self, architecture_id: str) -> Dict:
        """
        🧠 NOWE: Pobiera dane audytu lejka i psychologii z Modułu 3
        
        Returns:
        - psychology_anchors: Lista psychology triggers z instrukcjami umiejscowienia
        - strategic_bridges: Cross-linking opportunities z psychology context
        - funnel_assessment: Ogólna ocena customer journey
        - funnel_stages_detected: Wykryte etapy lejka w architekturze
        """
        try:
            self.logger.info(f"🧠 [PSYCHOLOGY] Pobieranie danych psychologii dla architecture: {architecture_id}")
            
            # POPRAWKA: Czytaj z tabeli funnel_audits zamiast architectures.funnel_audit
            funnel_response = self.supabase.table('funnel_audits').select(
                'should_optimize_for_funnel, reasoning, commercial_potential, user_journey_exists, '
                'funnel_stages_identified, confidence_score, funnel_suggestions'
            ).eq('architecture_id', architecture_id).order('created_at', desc=True).limit(1).execute()
            
            if not funnel_response.data:
                self.logger.warning(f"⚠️ [PSYCHOLOGY] Brak funnel_audits dla architecture: {architecture_id}")
                return self._get_default_psychology_data()
            
            funnel_data = funnel_response.data[0]
            
            # NAPRAWKA: Handle funnel_suggestions as string or dict
            funnel_suggestions = funnel_data.get('funnel_suggestions') or {}
            if isinstance(funnel_suggestions, str):
                try:
                    import json
                    funnel_suggestions = json.loads(funnel_suggestions)
                except json.JSONDecodeError:
                    funnel_suggestions = {}
            
            psychology_data = {
                'psychology_anchors': self._safe_get_list(funnel_suggestions, 'psychology_anchors'),
                'strategic_bridges': self._safe_get_list(funnel_suggestions, 'strategic_bridges'),
                'psychology_principles': self._safe_get_list(funnel_suggestions, 'psychology_principles'),
                'modifications_applied': self._safe_get_list(funnel_suggestions, 'modifications_applied'),
                'ai_confidence': self._safe_get_float(funnel_suggestions, 'ai_confidence'),
                'internal_linking_modifications': self._safe_get_list(funnel_suggestions, 'internal_linking_modifications'),
                'funnel_assessment': {
                    'should_optimize_for_funnel': funnel_data.get('should_optimize_for_funnel', False),
                    'reasoning': funnel_data.get('reasoning', ''),
                    'commercial_potential': funnel_data.get('commercial_potential', 'none'),
                    'user_journey_exists': funnel_data.get('user_journey_exists', False),
                    'confidence_score': funnel_data.get('confidence_score', 0.0)
                },
                'funnel_stages_detected': funnel_data.get('funnel_stages_identified', ['AWARENESS']),
                'has_psychology_data': True,
                'should_optimize_for_funnel': funnel_data.get('should_optimize_for_funnel', False),
                'psychology_applied': funnel_data.get('should_optimize_for_funnel', False),
                'funnel_confidence': funnel_data.get('confidence_score', 0.0)
            }
            
            self.logger.info(f"✅ [PSYCHOLOGY] Pobrano psychology data z funnel_audits: "
                           f"optimize={psychology_data['should_optimize_for_funnel']}, "
                           f"anchors={len(psychology_data['psychology_anchors'])}, "
                           f"bridges={len(psychology_data['strategic_bridges'])}")
            
            return psychology_data
            
        except Exception as e:
            self.logger.error(f"❌ [PSYCHOLOGY] Błąd pobierania danych psychologii: {str(e)}")
            return self._get_default_psychology_data()
    
    def _get_default_psychology_data(self) -> Dict:
        """Zwraca domyślne dane psychologii gdy brak danych z Modułu 3"""
        return {
            'psychology_anchors': [],
            'strategic_bridges': [],
            'psychology_principles': [],
            'modifications_applied': [],
            'ai_confidence': 0.0,
            'internal_linking_modifications': {},
            'funnel_assessment': {},
            'funnel_stages_detected': ['AWARENESS'],  # Default do basic stage
            'has_psychology_data': False,
            'should_optimize_for_funnel': False,
            'psychology_applied': False
        }
    
    async def _get_page_funnel_stage(self, page_data: Dict, psychology_data: Dict) -> str:
        """
        🎯 Określa etap customer journey dla konkretnej strony
        
        Returns: 'AWARENESS' | 'CONSIDERATION' | 'DECISION'
        """
        try:
            # KROK 1: Sprawdź explicit stage detection z psychology data
            if psychology_data.get('has_psychology_data'):
                stages_detected = psychology_data.get('funnel_stages_detected', [])
                if stages_detected:
                    # Jeśli mamy multi-stage architecture, analizuj page_type
                    page_type = page_data.get('page_type', '').lower()
                    
                    # Decision stage keywords
                    if any(keyword in page_type for keyword in ['pricing', 'offer', 'buy', 'purchase', 'contact', 'quote']):
                        return 'DECISION'
                    
                    # Consideration stage keywords
                    if any(keyword in page_type for keyword in ['comparison', 'vs', 'review', 'guide', 'how-to']):
                        return 'CONSIDERATION'
                    
                    # Default to first detected stage
                    return stages_detected[0] if stages_detected else 'AWARENESS'
            
            # KROK 2: Fallback analysis based on page characteristics
            page_type = page_data.get('page_type', '').lower()
            url_slug = page_data.get('url_slug', '').lower()
            business_intent = page_data.get('business_intent', '').lower()
            
            # Decision indicators
            decision_signals = [
                'pricing', 'price', 'cost', 'offer', 'buy', 'purchase', 
                'contact', 'quote', 'booking', 'order', 'payment'
            ]
            if any(signal in page_type or signal in url_slug or signal in business_intent 
                   for signal in decision_signals):
                return 'DECISION'
            
            # Consideration indicators
            consideration_signals = [
                'comparison', 'compare', 'vs', 'versus', 'review', 'guide', 
                'how-to', 'tutorial', 'best', 'top', 'choose'
            ]
            if any(signal in page_type or signal in url_slug or signal in business_intent 
                   for signal in consideration_signals):
                return 'CONSIDERATION'
            
            # Default to awareness for educational/informational content
            return 'AWARENESS'
            
        except Exception as e:
            self.logger.error(f"❌ [FUNNEL_STAGE] Błąd wykrywania etapu: {str(e)}")
            return 'AWARENESS'

    async def _get_page_data(self, page_id: str) -> Optional[Dict]:
        """Pobiera dane strony z architecture_pages"""
        try:
            response = self.supabase.table('architecture_pages').select(
                'id, architecture_id, name, url_path, page_type, target_keywords, cluster_name, content_suggestions, depth_level'
            ).eq('id', page_id).execute()
            if response.data:
                data = response.data[0]
                # Mapuj kolumny na oczekiwane nazwy
                return {
                    'id': data['id'],
                    'architecture_id': data['architecture_id'],
                    'title': data['name'],  # name → title
                    'url_path': data['url_path'],
                    'page_type': data['page_type'],
                    'target_keywords': data.get('target_keywords', []),
                    'cluster_name': data.get('cluster_name', ''),  # DODANE: nazwa grupy semantycznej
                    'meta_title': data.get('cluster_name', ''),  # cluster_name → meta_title
                    'meta_description': '',  # brak w bazie
                    'content_type': 'page',  # default
                    'priority_level': data.get('depth_level', 5)  # depth_level → priority_level
                }
            return None
        except Exception as e:
            self.logger.error(f"❌ [DATA] Błąd pobierania page_data: {e}")
            return None

    async def _get_semantic_keywords(self, architecture_id: str, page_data: Dict) -> Dict:
        """
        Pobiera semantic keywords dla strony na podstawie cluster_name
        PROSTA IMPLEMENTACJA zgodna ze strukturą bazy danych
        """
        try:
            page_title = page_data.get('title', '')
            cluster_name = page_data.get('cluster_name', '')  # Nazwa grupy semantycznej
            page_target_keywords = page_data.get('target_keywords', [])
            page_type = (page_data.get('page_type') or '').lower()
            
            self.logger.info(f"🎯 [KEYWORDS] Strona '{page_title}', page_type: '{page_type}', cluster_name: '{cluster_name}'")
            
            # Routing wg typu strony
            if page_type in ['subcategory', 'cluster_page']:
                # Dotychczasowa logika (realny cluster_name)
                pass
            else:
                # category/pillar i inne → enhanced fallback
                if not page_title and not page_target_keywords:
                    return {"primary_keywords": [], "semantic_keywords": [], "related_keywords": []}
                fallback_keywords = page_target_keywords or ([page_title.lower()] if page_title else [])
                return {
                    "primary_keywords": fallback_keywords[:5],
                    "semantic_keywords": [],
                    "related_keywords": []
                }
            
            # FALLBACK: Jeśli brak cluster_name, użyj tylko target_keywords + tytuł
            if not cluster_name:
                self.logger.warning(f"⚠️ [KEYWORDS] Brak cluster_name dla strony '{page_title}' - używam fallback")
                fallback_keywords = page_target_keywords or [page_title.lower()] if page_title else []
                return {
                    "primary_keywords": fallback_keywords[:5],
                    "semantic_keywords": [],
                    "related_keywords": []
                }
            
            # KROK 1: Pobierz semantic_cluster_id z architectures
            arch_response = self.supabase.table('architectures').select(
                'semantic_cluster_id'
            ).eq('id', architecture_id).execute()
            
            if not arch_response.data:
                self.logger.error(f"❌ [KEYWORDS] Nie znaleziono architektury {architecture_id}")
                return {
                    "primary_keywords": page_target_keywords[:5],
                    "semantic_keywords": [],
                    "related_keywords": []
                }
            
            semantic_cluster_id = arch_response.data[0]['semantic_cluster_id']
            self.logger.info(f"🔍 [KEYWORDS] semantic_cluster_id: {semantic_cluster_id}")
            
            # KROK 2: Znajdź grupę w semantic_groups WHERE semantic_cluster_id = X AND group_label = cluster_name
            group_response = self.supabase.table('semantic_groups').select(
                'id, phrases_count'
            ).eq('semantic_cluster_id', semantic_cluster_id).eq('group_label', cluster_name).execute()
            
            if not group_response.data:
                self.logger.warning(f"⚠️ [KEYWORDS] Nie znaleziono grupy '{cluster_name}' w klastrze {semantic_cluster_id}")
                return {
                    "primary_keywords": page_target_keywords[:5],
                    "semantic_keywords": [],
                    "related_keywords": []
                }
            
            group_id = group_response.data[0]['id']
            phrases_count = group_response.data[0]['phrases_count']
            self.logger.info(f"🔍 [KEYWORDS] Grupa '{cluster_name}' (ID: {group_id}) ma {phrases_count} fraz")
            
            # KROK 3: Pobierz wszystkie frazy z semantic_group_members dla tej grupy
            members_response = self.supabase.table('semantic_group_members').select(
                'phrase, similarity_to_centroid'
            ).eq('group_id', group_id).order('similarity_to_centroid', desc=True).execute()
            
            if not members_response.data:
                self.logger.warning(f"⚠️ [KEYWORDS] Brak fraz w grupie '{cluster_name}'")
                return {
                    "primary_keywords": page_target_keywords[:5],
                    "semantic_keywords": [],
                    "related_keywords": []
                }
            
            all_phrases_from_group = [
                {"phrase": member['phrase'], "similarity": member.get('similarity_to_centroid', 0.0)}
                for member in members_response.data
            ]
            
            self.logger.info(f"📊 [KEYWORDS] Pobrano {len(all_phrases_from_group)} fraz z grupy '{cluster_name}'")
            
            # KROK 4: Sortuj wszystkie frazy po similarity (BEZ FILTRACJI!)
            # Content writer POTRZEBUJE wariantów keywords - filtracja jest szkodliwa
            all_phrases_from_group.sort(key=lambda x: x['similarity'], reverse=True)
            
            self.logger.info(f"📊 [KEYWORDS] Posortowano {len(all_phrases_from_group)} fraz po similarity")
            
            # KROK 5: Podziel na primary_keywords (target_keywords), semantic_keywords (top similarity), related_keywords
            primary_keywords = page_target_keywords[:5]  # Zawsze używaj target_keywords jako primary
            
            # Semantic keywords: frazy z wysokim similarity (>= 0.7)
            semantic_keywords = []
            for item in all_phrases_from_group:
                if item['similarity'] >= 0.7 and len(semantic_keywords) < 15:
                    semantic_keywords.append(item['phrase'])
            
            # Related keywords: frazy z umiarkowanym similarity (>= 0.4 i < 0.7)
            related_keywords = []
            for item in all_phrases_from_group:
                if 0.4 <= item['similarity'] < 0.7 and len(related_keywords) < 25:
                    related_keywords.append(item['phrase'])
            
            # Jeśli za mało semantic keywords, dodaj najlepsze z remaining (>= 0.3)
            if len(semantic_keywords) < 10:
                for item in all_phrases_from_group:
                    if item['similarity'] >= 0.3 and item['phrase'] not in semantic_keywords and len(semantic_keywords) < 15:
                        semantic_keywords.append(item['phrase'])
            
            # Jeśli za mało related keywords, dodaj remaining (>= 0.2)
            if len(related_keywords) < 15:
                for item in all_phrases_from_group:
                    if item['similarity'] >= 0.2 and item['phrase'] not in semantic_keywords + related_keywords and len(related_keywords) < 25:
                        related_keywords.append(item['phrase'])
            
            self.logger.info(f"✅ [KEYWORDS] FINAL: Primary={len(primary_keywords)}, Semantic={len(semantic_keywords)}, Related={len(related_keywords)}")
            
            # Debug: Loguj przykładowe keywords
            if semantic_keywords:
                self.logger.info(f"🎯 [KEYWORDS] Przykładowe semantic: {semantic_keywords[:3]}")
            if related_keywords:
                self.logger.info(f"🔗 [KEYWORDS] Przykładowe related: {related_keywords[:3]}")
            
            return {
                "primary_keywords": primary_keywords,
                "semantic_keywords": semantic_keywords,
                "related_keywords": related_keywords
            }
            
        except Exception as e:
            self.logger.error(f"❌ [KEYWORDS] Błąd pobierania semantic keywords: {e}")
            # Fallback w przypadku błędu
            fallback_keywords = page_data.get('target_keywords', [])
            if not fallback_keywords and page_data.get('title'):
                fallback_keywords = [page_data['title'].lower()]
            
            return {
                "primary_keywords": fallback_keywords[:5],
                "semantic_keywords": [],
                "related_keywords": []
            }

    async def _get_faq_questions(self, architecture_id: str, page_id: str) -> Dict:
        """Pobiera PAA questions - najpierw z Modułu 3 routing, potem fallback"""
        try:
            # NOWE: Próba pobrania PAA z Modułu 3 routing
            self.logger.info(f"🎯 [FAQ] Próbuję pobrać PAA z Modułu 3 routing dla page_id: {page_id}")
            
            module3_response = self.supabase.table('content_opportunities').select(
                'question_or_topic, priority, rationale, source'
            ).eq('architecture_id', architecture_id).eq('target_page_id', page_id).eq('decision', 'FAQ').execute()
            
            if module3_response.data and len(module3_response.data) > 0:
                # SUCCESS: Mamy PAA routing z Modułu 3!
                self.logger.info(f"✅ [FAQ] INHERITANCE: Znaleziono {len(module3_response.data)} PAA z Modułu 3")
                
                questions = []
                for item in module3_response.data:
                    questions.append({
                        "question": item['question_or_topic'],
                        "priority": item['priority'],
                        "source": f"module3_routing_{item['source']}", # Oznacz źródło
                        "rationale": item['rationale']
                    })
                
                return {
                    "questions": questions,
                    "high_priority": [q for q in questions if q['priority'] == 'high'],
                    "total_count": len(questions),
                    "source_method": "module3_inheritance" # NOWE POLE
                }
                
            else:
                # FALLBACK: Brak routing z Modułu 3
                self.logger.info(f"⚠️ [FAQ] FALLBACK: Brak PAA routing z Modułu 3, używam obecnej logiki")
        
        except Exception as e:
            self.logger.warning(f"⚠️ [FAQ] Błąd pobierania z Modułu 3: {e}, używam fallback")
        
        # OBECNA LOGIKA (bez zmian!) - FALLBACK
        try:
            response = self.supabase.table('content_opportunities').select(
                'question_or_topic, priority, rationale, source'
            ).eq('architecture_id', architecture_id).eq('target_page_id', page_id).eq('decision', 'FAQ').execute()
            
            questions = []
            for item in response.data:
                questions.append({
                    "question": item['question_or_topic'],
                    "priority": item['priority'],
                    "source": item['source'],
                    "rationale": item['rationale']
                })
            
            return {
                "questions": questions,
                "high_priority": [q for q in questions if q['priority'] == 'high'],
                "total_count": len(questions),
                "source_method": "direct_db_query" # NOWE POLE
            }
        except Exception as e:
            self.logger.error(f"❌ [FAQ] Błąd pobierania FAQ (fallback): {e}")
            return {
                "questions": [], 
                "high_priority": [], 
                "total_count": 0,
                "source_method": "error_fallback" # NOWE POLE
            }

    async def _get_linking_instructions(self, page_id: str) -> Dict:
        """
        🔗 ENHANCED: Pobiera internal linking instructions z architecture_links po page IDs
        
        Obsługuje nowe typy linków:
        - hierarchy: linki hierarchiczne (vertical_linking)
        - bridge: strategic bridges (cross-cluster)  
        - funnel: funnel-optimized links
        """
        try:
            response = self.supabase.table('architecture_links').select(
                'to_page_id, anchor_text, link_context, link_type, priority, source, enabled, '
                'similarity_score, funnel_stage, placement, rationale, from_title, to_title, from_url, to_url, confidence_score, '
                'architecture_pages!architecture_links_to_page_id_fkey(name, url_path)'
            ).eq('from_page_id', page_id).eq('enabled', True).execute()
            
            instructions = []
            for link in response.data:
                target_page = link.get('architecture_pages', {})
                
                # Mapuj priority na czytelny poziom
                priority_num = self._safe_get_int(link, 'priority', 50)
                if priority_num >= 90:
                    priority_level = "highest"
                elif priority_num >= 75:
                    priority_level = "high" 
                elif priority_num >= 50:
                    priority_level = "medium"
                else:
                    priority_level = "low"
                
                target_url = (
                    self._safe_get_str(link, 'to_url') or
                    self._safe_get_str(target_page, 'url_path', '')
                )
                target_title = (
                    self._safe_get_str(link, 'to_title') or
                    self._safe_get_str(target_page, 'name', 'Unknown Page')
                )
                
                instruction = {
                    "target_url": target_url,
                    "target_title": target_title,
                    "anchor_text": link.get('anchor_text', ''),
                    "context": link.get('link_context', ''),
                    "link_type": link.get('link_type', ''),
                    "priority": priority_level,
                    "priority_score": priority_num,
                    "source": link.get('source', ''),
                    "placement": link.get('placement', ''),
                    # Dodatkowe metadane
                    "similarity_score": link.get('similarity_score'),
                    "funnel_stage": link.get('funnel_stage', ''),
                    "rationale": self._safe_get_str(link, 'rationale'),
                    "confidence_score": self._safe_get_float(link, 'confidence_score'),
                    "from_title": self._safe_get_str(link, 'from_title'),
                    "from_url": self._safe_get_str(link, 'from_url'),
                }
                instructions.append(instruction)
            
            # Sortuj według priority (najwyższe pierwszeliśmy)
            instructions.sort(key=lambda x: x['priority_score'], reverse=True)
            
            return {
                "internal_links": instructions,
                "hierarchy_links": [l for l in instructions if l['link_type'] == 'hierarchy'],
                "bridge_links": [l for l in instructions if l['link_type'] == 'bridge'],
                "funnel_links": [l for l in instructions if l['link_type'] == 'funnel'],
                "high_priority_links": [l for l in instructions if l['priority_score'] >= 75],
                "total_count": len(instructions),
                # Legacy compatibility (dla istniejących callów)
                "pillar_links": [l for l in instructions if l['link_type'] == 'hierarchy'],
                "cluster_links": [l for l in instructions if l['link_type'] in ['bridge', 'funnel']]
            }
            
        except Exception as e:
            self.logger.error(f"❌ [DATA] Błąd pobierania linking instructions: {e}")
            return {
                "internal_links": [], 
                "hierarchy_links": [],
                "bridge_links": [],
                "funnel_links": [],
                "high_priority_links": [],
                "pillar_links": [], 
                "cluster_links": [], 
                "total_count": 0
            }

    async def _generate_psychology_aware_structure(self, page_data: Dict, semantic_data: Dict, 
                                                 faq_data: Dict, psychology_data: Dict, 
                                                 funnel_stage: str) -> Dict:
        """
        🧠 ENHANCED: Generuje strukturę H1/H2/H3 świadomą psychologii customer journey
        
        Uwzględnia:
        - Etap lejka (AWARENESS/CONSIDERATION/DECISION)
        - Psychology anchors z Modułu 3
        - Strategic bridges z psychology triggers
        - Customer journey context
        """
        try:
            self.logger.info(f"🧠 [PSYCHOLOGY_STRUCTURE] Generowanie dla stage: {funnel_stage}")
            
            # KROK 1: Przygotuj psychology context
            psychology_anchors = psychology_data.get('psychology_anchors', [])
            strategic_bridges = psychology_data.get('strategic_bridges', [])
            
            self.logger.info(f"🎯 [PSYCHOLOGY] Psychology anchors: {len(psychology_anchors)}, "
                           f"Strategic bridges: {len(strategic_bridges)}")
            
            # KROK 2: Zdefiniuj psychology-aware prompts dla każdego etapu
            stage_prompts = {
                'AWARENESS': {
                    'tone': 'Edukacyjny, budujący zaufanie, bez presji sprzedażowej',
                    'structure_focus': 'Podstawy, definicje, zrozumienie problemu',
                    'cta_style': 'Soft, prowadzący do dalszej edukacji'
                },
                'CONSIDERATION': {
                    'tone': 'Porównawczy, wspierający decyzję, autorytatywny',
                    'structure_focus': 'Porównania, kryteria wyboru, opcje rozwiązań',
                    'cta_style': 'Zachęcający do głębszej analizy i porównań'
                },
                'DECISION': {
                    'tone': 'Akcyjny, budujący pilność, sygnały zaufania',
                    'structure_focus': 'Konkretne korzyści, gwarancje, call-to-action',
                    'cta_style': 'Jasny, bezpośredni, nakłaniający do działania'
                }
            }
            
            stage_config = stage_prompts.get(funnel_stage, stage_prompts['AWARENESS'])
            
            # KROK 3: Przygotuj psychology anchors context
            psychology_context = ""
            if psychology_anchors:
                anchor_descriptions = []
                for anchor in psychology_anchors[:3]:  # Top 3 najważniejsze
                    anchor_descriptions.append(
                        f"- '{anchor.get('text', '')}' → {anchor.get('target_url', '')} "
                        f"(psychology trigger: {anchor.get('psychology_trigger', 'N/A')})"
                    )
                psychology_context = f"\n\nPSYCHOLOGY ANCHORS do umieszczenia:\n" + "\n".join(anchor_descriptions)
            
            # KROK 4: Przygotuj strategic bridges context
            bridges_context = ""
            if strategic_bridges:
                bridge_descriptions = []
                for bridge in strategic_bridges[:3]:  # Top 3 z najwyższą similarity
                    bridge_descriptions.append(
                        f"- Naturalnie wspomnij '{bridge.get('target_keyword', '')}' "
                        f"(similarity: {bridge.get('similarity_score', 0):.1f}%) "
                        f"→ {bridge.get('target_url', '')}"
                    )
                bridges_context = f"\n\nSTRATEGIC BRIDGES do integracji:\n" + "\n".join(bridge_descriptions)
            
            # KROK 5: Enhanced system prompt z psychology awareness
            system_prompt = f"""Jesteś ekspertem psychologii customer journey i content marketingu. 
Twoje zadanie to utworzenie struktury treści (H1, H2, H3) zoptymalizowanej pod etap lejka sprzedażowego.

ETAP CUSTOMER JOURNEY: {funnel_stage}
TON I PODEJŚCIE: {stage_config['tone']}
FOCUS STRUKTURY: {stage_config['structure_focus']}
STYLE CTA: {stage_config['cta_style']}

ZASADY PSYCHOLOGY-AWARE CONTENT:
1. H1 musi być dostrojony do etapu {funnel_stage} i psychologii użytkownika
2. H2 to główne sekcje które prowadzą użytkownika przez customer journey  
3. H3 to podsekcje odpowiadające na konkretne obawy/potrzeby tego etapu
4. Struktura musi naturalnie prowadzić do psychology anchors
5. Uwzględnij miejsca na strategic bridges
6. Zoptymalizuj pod {funnel_stage} mindset

ZWRÓĆ JSON w formacie:
{{
  "h1_title": "string - zoptymalizowany pod {funnel_stage}",
  "h2_structure": ["sekcja1", "sekcja2", "sekcja3"],
  "h3_structure": {{
    "sekcja1": ["podsekcja1", "podsekcja2"],
    "sekcja2": ["podsekcja1", "podsekcja2"]
  }},
  "content_flow": "string - opis psychology-aware flow",
  "psychology_placement_suggestions": ["gdzie umieścić psychology anchors"],
  "customer_journey_progression": "string - jak treść prowadzi przez etap"
}}"""
            
            # KROK 6: Enhanced user prompt z psychology data
            title = page_data.get('title', '')
            target_keywords = page_data.get('target_keywords', [])
            primary_keywords = semantic_data.get('primary_keywords', [])
            semantic_keywords = semantic_data.get('semantic_keywords', [])[:10]
            faq_questions = [q['question'] for q in faq_data.get('high_priority', [])][:5]
            
            user_prompt = f"""Utwórz psychology-aware strukturę treści dla strony:

TYTUŁ STRONY: {title}
URL: {page_data.get('url_path', '')}
ETAP LEJKA: {funnel_stage}

TARGET KEYWORDS: {', '.join(target_keywords)}
CONTEXT KEYWORDS: 
- Primary: {', '.join(primary_keywords)}
- Semantic: {', '.join(semantic_keywords)}

FAQ QUESTIONS: {', '.join(faq_questions) if faq_questions else 'Brak'}

{psychology_context}
{bridges_context}

PSYCHOLOGY REQUIREMENTS:
- Struktura musi być dostrojona do mindset użytkownika na etapie {funnel_stage}
- H1 musi adresować główne potrzeby/obawy tego etapu
- Sekcje H2 mają prowadzić przez customer journey
- Uwzględnij miejsca na umieszczenie psychology anchors
- Zintegruj strategic bridges w naturalny sposób

Zwróć TYLKO JSON."""
            
            # KROK 7: Generuj przez AI (provider-first z fallback)
            # Provider-first z pełnym fallbackiem: gpt5 → openai → claude (zależnie od AI_PROVIDER)
            ai_response = None
            providers_order = []
            primary = (self.ai_provider or 'openai')
            all_providers = ['gpt5', 'openai', 'claude']
            providers_order = [primary] + [p for p in all_providers if p != primary]

            async def call_gpt5():
                if not self.openai_client:
                    raise RuntimeError("OpenAI client (for GPT-5) unavailable")
                self.logger.info(f"🤖 [AI] GPT-5 call (model={self.gpt5_model})")
                request_data = {
                    "model": self.gpt5_model,
                    "input": [{
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}"}
                        ]
                    }],
                    "max_output_tokens": 32768,
                    "reasoning": {"effort": "medium"},
                    "text": {"verbosity": self.gpt5_verbosity}
                }
                # DEBUG REQUEST
                try:
                    self.logger.info(f"🚀 [GPT5_REQUEST] Model: {self.gpt5_model}")
                    self.logger.info(f"🚀 [GPT5_REQUEST] Reasoning effort: {self.gpt5_reasoning_effort}")
                    self.logger.info(f"🚀 [GPT5_REQUEST] Verbosity: {self.gpt5_verbosity}")
                    self.logger.info(f"🚀 [GPT5_REQUEST] Max tokens: 64000")
                    merged_prompt = f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}"
                    self.logger.info(f"🚀 [GPT5_REQUEST] Prompt length: {len(merged_prompt)} chars")
                    self.logger.info(f"🚀 [GPT5_REQUEST] Prompt first 500 chars: {merged_prompt[:500]}")
                    self.logger.info(f"🚀 [GPT5_REQUEST] Prompt last 200 chars: {merged_prompt[-200:]}")
                    self.logger.info(f"🚀 [GPT5_REQUEST] Complete request structure: {request_data}")
                except Exception:
                    pass

                resp = await self.openai_client.responses.create(**request_data)

                # DEBUG RESPONSE
                try:
                    self.logger.info(f"🔍 [GPT5_RESPONSE] Response type: {type(resp)}")
                    self.logger.info(f"🔍 [GPT5_RESPONSE] Response ID: {getattr(resp, 'id', 'No ID')}")
                    self.logger.info(f"🔍 [GPT5_RESPONSE] Model used: {getattr(resp, 'model', 'No model')}")
                    self.logger.info(f"🔍 [GPT5_RESPONSE] Status: {getattr(resp, 'status', 'No status')}")
                    self.logger.info(f"🔍 [GPT5_RESPONSE] Has output_text: {hasattr(resp, 'output_text')}")
                    if hasattr(resp, 'output_text'):
                        self.logger.info(f"🔍 [GPT5_RESPONSE] output_text type: {type(resp.output_text)}")
                        self.logger.info(f"🔍 [GPT5_RESPONSE] output_text is None: {resp.output_text is None}")
                        self.logger.info(f"🔍 [GPT5_RESPONSE] output_text repr: {repr(resp.output_text)}")
                        if resp.output_text:
                            ot = str(resp.output_text)
                            self.logger.info(f"🔍 [GPT5_RESPONSE] output_text length: {len(ot)}")
                            self.logger.info(f"🔍 [GPT5_RESPONSE] output_text first 500 chars: {ot[:500]}")
                    self.logger.info(f"🔍 [GPT5_RESPONSE] Has output: {hasattr(resp, 'output')}")
                    if hasattr(resp, 'output'):
                        out = getattr(resp, 'output', None)
                        self.logger.info(f"🔍 [GPT5_RESPONSE] output type: {type(out)}")
                        self.logger.info(f"🔍 [GPT5_RESPONSE] output is None: {out is None}")
                        if out:
                            self.logger.info(f"🔍 [GPT5_RESPONSE] output length: {len(out)}")
                            if len(out) > 0:
                                self.logger.info(f"🔍 [GPT5_RESPONSE] output[0] type: {type(out[0])}")
                                self.logger.info(f"🔍 [GPT5_RESPONSE] output[0] dir: {dir(out[0])}")
                                if hasattr(out[0], 'content'):
                                    self.logger.info(f"🔍 [GPT5_RESPONSE] output[0].content: {out[0].content}")
                    if hasattr(resp, 'usage'):
                        self.logger.info(f"🔍 [GPT5_RESPONSE] Usage: {resp.usage}")
                    if hasattr(resp, 'error'):
                        self.logger.info(f"🔍 [GPT5_RESPONSE] Error: {resp.error}")
                    self.logger.info(f"🔍 [GPT5_RESPONSE] COMPLETE RESPONSE DUMP:")
                    self.logger.info(f"🔍 [GPT5_RESPONSE] {resp}")
                except Exception:
                    pass

                # 🔢 Token usage diagnostics
                try:
                    usage = getattr(resp, 'usage', None)
                    if usage is not None:
                        details = getattr(usage, 'output_tokens_details', None)
                        reasoning_tokens = getattr(details, 'reasoning_tokens', 0) if details is not None else 0
                        total_output = getattr(usage, 'output_tokens', None)
                        self.logger.info(f"🔢 [GPT5] Tokens used: reasoning={reasoning_tokens}, total_output={total_output}")
                        try:
                            if total_output and reasoning_tokens >= float(total_output) * 0.95:
                                self.logger.warning(f"⚠️ [GPT5] Reasoning consumed {reasoning_tokens}/{total_output} tokens - consider increasing max_output_tokens or reducing reasoning effort")
                        except Exception:
                            pass
                except Exception:
                    pass

                # Ekstrakcja tekstu
                ai_text = None
                if hasattr(resp, 'output_text') and resp.output_text and str(resp.output_text).strip():
                    ai_text = str(resp.output_text)
                    try:
                        self.logger.info(f"✅ [GPT5_RESPONSE] SUCCESS: Używam output_text, length: {len(ai_text)}")
                        self.logger.info(f"🎉 [GPT5_RESPONSE] First 300 chars: {ai_text[:300]}")
                    except Exception:
                        pass
                elif hasattr(resp, 'output') and resp.output and len(resp.output) > 0:
                    if hasattr(resp.output[0], 'content') and resp.output[0].content:
                        if len(resp.output[0].content) > 0 and hasattr(resp.output[0].content[0], 'text'):
                            ai_text = resp.output[0].content[0].text
                            try:
                                self.logger.info(f"✅ [GPT5_RESPONSE] SUCCESS: Używam output[0].content[0].text, length: {len(ai_text)}")
                            except Exception:
                                pass
                if not ai_text:
                    self.logger.error(f"❌ [GPT5_RESPONSE] ALL EXTRACTION METHODS FAILED")
                    raise Exception("Cannot extract text from GPT-5 response after all attempts")
                return ai_text

            async def call_openai():
                if not self.openai_client:
                    raise RuntimeError("OpenAI client unavailable")
                resp = await self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=4096
                )
                return resp.choices[0].message.content

            async def call_claude():
                if not self.claude_client:
                    raise RuntimeError("Claude client unavailable")
                resp = await self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=4096,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return resp.content[0].text

            for provider in providers_order:
                try:
                    if provider == 'gpt5':
                        ai_response = await call_gpt5()
                    elif provider == 'openai':
                        ai_response = await call_openai()
                    else:
                        ai_response = await call_claude()
                    self.logger.info(f"✅ [AI] {provider.upper()} odpowiedział")
                    break
                except Exception as e:
                    self.logger.warning(f"⚠️ [AI] {provider.upper()} nieudane: {e}")
                    continue
            if not ai_response:
                raise Exception("Brak odpowiedzi AI po wszystkich fallbackach")
            
            # KROK 8: Parse i dodaj psychology metadata
            structure = self._parse_json_response(ai_response)
            if structure and "h1_title" in structure:
                # Dodaj psychology metadata do struktury
                structure['funnel_stage'] = funnel_stage
                structure['psychology_applied'] = True
                structure['psychology_anchors_count'] = len(psychology_anchors)
                structure['strategic_bridges_count'] = len(strategic_bridges)
                
                self.logger.info(f"✅ [PSYCHOLOGY_AI] Wygenerowano psychology-aware strukturę: "
                               f"{len(structure.get('h2_structure', []))} sekcji H2 dla {funnel_stage}")
                return structure
            else:
                self.logger.warning(f"⚠️ [PSYCHOLOGY_AI] Niepoprawna struktura - fallback do basic")
                return await self._generate_content_structure(page_data, semantic_data, faq_data)
                
        except Exception as e:
            self.logger.error(f"❌ [PSYCHOLOGY_AI] Błąd generowania psychology-aware struktury: {e}")
            # Fallback do oryginalnej metody
            return await self._generate_content_structure(page_data, semantic_data, faq_data)

    async def _generate_content_structure(self, page_data: Dict, semantic_data: Dict, faq_data: Dict) -> Dict:
        """
        �� Generuje strukturę H1/H2/H3 przez AI na podstawie zebranych danych
        """
        try:
            # Logging FAQ inheritance status
            self.logger.info(f"📊 [STRUCTURE] FAQ source method: {faq_data.get('source_method', 'unknown')}")
            self.logger.info(f"📊 [STRUCTURE] FAQ questions count: {faq_data.get('total_count', 0)}")
            if faq_data.get('source_method') == 'module3_inheritance':
                self.logger.info(f"🎯 [STRUCTURE] INHERITANCE ACTIVE - używam PAA z Modułu 3!")
            
            title = page_data.get('title', '')
            target_keywords = page_data.get('target_keywords', [])
            primary_keywords = semantic_data.get('primary_keywords', [])
            semantic_keywords = semantic_data.get('semantic_keywords', [])[:10]
            faq_questions = [q['question'] for q in faq_data.get('high_priority', [])][:5]
            system_prompt = """Jesteś ekspertem SEO i content marketingu. Twoje zadanie to utworzenie struktury treści (H1, H2, H3) dla artykułu edukacyjnego.

ZASADY:
1. H1 musi być jasny, zawierać główne słowo kluczowe i obiecywać konkretną wartość
2. H2 to główne sekcje artykułu (4-7 sekcji)  
3. H3 to podsekcje w ramach H2 (2-4 podsekcje na H2)
4. Struktura musi być logiczna i edukacyjna
5. Uwzględnij FAQ questions jako potencjalne sekcje
6. Optymalizuj pod intent informacyjny

ZWRÓĆ JSON w formacie:
{
  "h1_title": "string",
  "h2_structure": ["sekcja1", "sekcja2", "sekcja3"],
  "h3_structure": {
    "sekcja1": ["podsekcja1", "podsekcja2"],
    "sekcja2": ["podsekcja1", "podsekcja2"]
  },
  "content_flow": "string - opis logicznego flow artykułu"
}"""
            user_prompt = f"""Utwórz strukturę treści dla strony edukacyjnej:

TYTUŁ STRONY: {title}
URL: {page_data.get('url_path', '')}

TARGET KEYWORDS (dla tej konkretnej strony): {', '.join(target_keywords)}

CONTEXT KEYWORDS: 
- Primary: {', '.join(primary_keywords)}
- Semantic: {', '.join(semantic_keywords)}

FAQ QUESTIONS: {', '.join(faq_questions) if faq_questions else 'Brak'}

UWAGI:
- H1 musi zawierać przynajmniej jedno target keyword dla tej strony
- Strukturuj treść wokół target_keywords tej strony
- Użyj context keywords jako wsparcie tematyczne
- Stwórz unikalną strukturę dla tej konkretnej strony

Zwróć TYLKO JSON."""
            # Fallback chain dla basic struktury: gpt5 → openai → claude
            async def call_gpt5():
                if not self.openai_client:
                    raise RuntimeError("OpenAI client (for GPT-5) unavailable")
                resp = await self.openai_client.responses.create(
                    model=self.gpt5_model,
                    input=[{
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}"}
                        ]
                    }],
                    max_output_tokens=64000,
                    reasoning={"effort": "medium"},
                    text={"verbosity": self.gpt5_verbosity}
                )
                try:
                    self.logger.info(f"GPT-5 response type: {type(resp)}")
                    self.logger.info(f"GPT-5 response attributes: {dir(resp)}")
                except Exception:
                    pass
                try:
                    return resp.output_text
                except Exception:
                    self.logger.warning("GPT-5: response.output_text not found; using str(resp)")
                    return str(resp)

            async def call_openai():
                if not self.openai_client:
                    raise RuntimeError("OpenAI client unavailable")
                resp = await self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=4096
                )
                return resp.choices[0].message.content

            async def call_claude():
                if not self.claude_client:
                    raise RuntimeError("Claude client unavailable")
                resp = await self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=4096,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return resp.content[0].text

            ai_response = None
            providers_order = [ (self.ai_provider or 'openai') ] + [p for p in ['gpt5','openai','claude'] if p != (self.ai_provider or 'openai')]
            for provider in providers_order:
                try:
                    if provider == 'gpt5':
                        ai_response = await call_gpt5()
                    elif provider == 'openai':
                        ai_response = await call_openai()
                    else:
                        ai_response = await call_claude()
                    self.logger.info(f"✅ [AI] {provider.upper()} odpowiedział")
                    break
                except Exception as e:
                    self.logger.warning(f"⚠️ [AI] {provider.upper()} nieudane: {e}")
                    continue
            if not ai_response:
                raise Exception("Brak odpowiedzi AI po wszystkich fallbackach")
            structure = self._parse_json_response(ai_response)
            if structure and "h1_title" in structure:
                self.logger.info(f"✅ [AI] Wygenerowano strukturę: {len(structure.get('h2_structure', []))} sekcji H2")
                return structure
            else:
                raise Exception("AI nie zwróciło poprawnej struktury")
        except Exception as e:
            self.logger.error(f"❌ [AI] Błąd generowania struktury: {e}")
            return {
                "h1_title": page_data.get('title', 'Bez tytułu'),
                "h2_structure": ["Wprowadzenie", "Główne zagadnienia", "Praktyczne wskazówki", "Podsumowanie"],
                "h3_structure": {
                    "Wprowadzenie": ["Definicja", "Znaczenie tematu"],
                    "Główne zagadnienia": ["Kluczowe aspekty", "Najczęstsze błędy"],
                    "Praktyczne wskazówki": ["Krok po kroku", "Przykłady"],
                    "Podsumowanie": ["Kluczowe punkty", "Następne kroki"]
                },
                "content_flow": "Logiczna progresja od podstaw do praktyki"
            }

    async def _analyze_content_intent(self, page_data: Dict, semantic_data: Dict, content_structure: Dict) -> Dict:
        """
        🤖 Analizuje intent treści i generuje tone guidelines przez AI
        """
        try:
            title = page_data.get('title', '')
            primary_keywords = semantic_data.get('primary_keywords', [])
            h2_structure = content_structure.get('h2_structure', [])
            system_prompt = """Jesteś ekspertem content marketingu. Analizujesz intent treści i definiujesz tone guidelines dla content writera.

ZADANIA:
1. Określ główny intent: informational/educational/commercial/transactional
2. Zdefiniuj target audience (wiek, poziom wiedzy, potrzeby)
3. Ustaw tone guidelines (formalny/casual, techniczny/prosty, etc.)
4. Zaproponuj typ CTA (call-to-action)
5. Określ target word count
6. Podaj keyword density targets

ZWRÓĆ JSON:
{
  "content_intent": "informational|educational|commercial|transactional",
  "target_audience": "string",
  "tone_guidelines": "string",
  "cta_recommendations": [{"type": "string", "text": "string", "placement": "string"}],
  "word_count_target": number,
  "keyword_density_targets": {"keyword": "percentage"},
  "content_difficulty": "beginner|intermediate|advanced"
}"""
            user_prompt = f"""Przeanalizuj intent i ton dla artykułu:

TYTUŁ: {title}
URL: {page_data.get('url_path', '')}

TARGET KEYWORDS (główne dla tej strony): {', '.join(page_data.get('target_keywords', []))}

CONTEXT KEYWORDS: {', '.join(primary_keywords)}

STRUKTURA H2: {', '.join(h2_structure)}

UWAGI:
- Optymalizuj keyword density dla target_keywords tej strony
- Uwzględnij unikalny charakter tej konkretnej strony

Określ optymalny approach dla content writera."""
            async def call_gpt5():
                if not self.openai_client:
                    raise RuntimeError("OpenAI client (for GPT-5) unavailable")
                resp = await self.openai_client.responses.create(
                    model=self.gpt5_model,
                    input=[{
                        "role": "user",
                        "content": [
                            {"type": "input_text", "text": f"SYSTEM:\n{system_prompt}\n\nUSER:\n{user_prompt}"}
                        ]
                    }],
                    max_output_tokens=64000,
                    reasoning={"effort": "medium"},
                    text={"verbosity": self.gpt5_verbosity}
                )
                try:
                    self.logger.info(f"GPT-5 response type: {type(resp)}")
                    self.logger.info(f"GPT-5 response attributes: {dir(resp)}")
                except Exception:
                    pass
                try:
                    return resp.output_text
                except Exception:
                    self.logger.warning("GPT-5: response.output_text not found; using str(resp)")
                    return str(resp)

            async def call_openai():
                if not self.openai_client:
                    raise RuntimeError("OpenAI client unavailable")
                resp = await self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.3,
                    max_tokens=2048
                )
                return resp.choices[0].message.content

            async def call_claude():
                if not self.claude_client:
                    raise RuntimeError("Claude client unavailable")
                resp = await self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=2048,
                    temperature=0.3,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return resp.content[0].text

            ai_response = None
            providers_order = [ (self.ai_provider or 'openai') ] + [p for p in ['gpt5','openai','claude'] if p != (self.ai_provider or 'openai')]
            for provider in providers_order:
                try:
                    if provider == 'gpt5':
                        ai_response = await call_gpt5()
                    elif provider == 'openai':
                        ai_response = await call_openai()
                    else:
                        ai_response = await call_claude()
                    self.logger.info(f"✅ [AI] {provider.upper()} odpowiedział")
                    break
                except Exception as e:
                    self.logger.warning(f"⚠️ [AI] {provider.upper()} nieudane: {e}")
                    continue
            if not ai_response:
                raise Exception("Brak odpowiedzi AI po wszystkich fallbackach")
            intent_data = self._parse_json_response(ai_response)
            if intent_data:
                self.logger.info(f"✅ [AI] Przeanalizowano intent: {intent_data.get('content_intent', 'unknown')}")
                return intent_data
            else:
                raise Exception("Błąd parsowania intent analysis")
        except Exception as e:
            self.logger.error(f"❌ [AI] Błąd analizy intent: {e}")
            return {
                "content_intent": "informational",
                "target_audience": "Użytkownicy szukający informacji na temat",
                "tone_guidelines": "Edukacyjny, przystępny, szczegółowy. Używaj przykładów i wyjaśnień.",
                "cta_recommendations": [{"type": "internal_link", "text": "Zobacz powiązane artykuły", "placement": "conclusion"}],
                "word_count_target": 2000,
                "keyword_density_targets": {},
                "content_difficulty": "intermediate"
            }

    async def _get_real_intent_data_for_page(self, page_data: Dict) -> Dict:
        """Get REAL intent data instead of AI guessing"""
        try:
            cluster_name = page_data.get('cluster_name')
            architecture_id = page_data.get('architecture_id')
            page_title = page_data.get('title', '')
            
            self.logger.info(f"🎯 [INTENT] Pobieranie real intent dla '{page_title}', cluster: '{cluster_name}'")
            
            if not cluster_name or not architecture_id:
                self.logger.warning(f"⚠️ [INTENT] Brak cluster_name lub architecture_id - używam fallback")
                return self._get_default_content_intent()
            
            # 1. Get semantic_cluster_id from architecture
            arch_query = self.supabase.table('architectures').select(
                'semantic_cluster_id'
            ).eq('id', architecture_id).execute()
            
            if not arch_query.data:
                self.logger.error(f"❌ [INTENT] Nie znaleziono architektury {architecture_id}")
                return self._get_default_content_intent()
            
            semantic_cluster_id = arch_query.data[0]['semantic_cluster_id']
            
            # 2. Get real intent data from semantic_groups
            intent_query = self.supabase.table('semantic_groups').select(
                'intent_data'
            ).eq('semantic_cluster_id', semantic_cluster_id).eq('group_label', cluster_name).execute()
            
            if intent_query.data and intent_query.data[0].get('intent_data'):
                intent_data = intent_query.data[0]['intent_data']
                
                self.logger.info(f"✅ [INTENT] Real intent: {intent_data.get('main_intent')}, priority: {intent_data.get('business_priority')}, value: ${intent_data.get('commercial_value', 0):.0f}")
                
                # 3. Generate content strategy based on REAL intent
                return self._generate_content_strategy_from_real_intent(intent_data)
            
            # Fallback to keywords table
            self.logger.info(f"🔄 [INTENT] Brak intent_data w semantic_groups - fallback do keywords")
            return await self._get_intent_from_keywords_fallback(cluster_name)
            
        except Exception as e:
            self.logger.error(f"❌ [INTENT] Real intent data fetch failed: {e}")
            return self._get_default_content_intent()

    def _generate_content_strategy_from_real_intent(self, intent_data: Dict) -> Dict:
        """Generate content strategy based on REAL intent data"""
        
        main_intent = intent_data.get('main_intent', 'informational')
        commercial_value = intent_data.get('commercial_value', 0)
        business_priority = intent_data.get('business_priority', 'content')
        data_source = intent_data.get('data_source', 'unknown')
        
        self.logger.info(f"📊 [INTENT] Generowanie strategii dla: {main_intent} intent, ${commercial_value:.0f} value, {business_priority} priority")
        
        # Intent-specific content strategies
        if main_intent == 'commercial':
            return {
                'content_intent': 'commercial',
                'target_audience': 'Użytkownicy porównujący opcje zakupu, researching przed decyzją',
                'tone_guidelines': f'Komercyjny, przekonujący, szczegółowy. Fokus na korzyściach i porównaniach. Commercial value: ${commercial_value:.0f}',
                'cta_recommendations': [
                    {'type': 'comparison_cta', 'text': 'Porównaj opcje i ceny', 'placement': 'mid_content'},
                    {'type': 'purchase_cta', 'text': 'Zobacz najlepsze oferty', 'placement': 'conclusion'},
                    {'type': 'affiliate_cta', 'text': 'Kup teraz z rabatem', 'placement': 'sidebar'}
                ],
                'word_count_target': 2500,
                'content_difficulty': 'intermediate',
                'monetization_potential': 'high' if commercial_value > 5000 else 'medium',
                'keyword_density_targets': {
                    'primary_focus': '2.5-3%',
                    'commercial_terms': '1.5-2%'
                },
                'data_source': data_source
            }
        
        elif main_intent == 'transactional':
            return {
                'content_intent': 'transactional',
                'target_audience': 'Użytkownicy gotowi do zakupu, bottom-funnel traffic',
                'tone_guidelines': f'Bezpośredni, akcyjny, budujący zaufanie. Fokus na szybkich decyzjach. Commercial value: ${commercial_value:.0f}',
                'cta_recommendations': [
                    {'type': 'direct_purchase', 'text': 'Kup teraz', 'placement': 'header'},
                    {'type': 'urgency_cta', 'text': 'Oferta ograniczona czasowo', 'placement': 'mid_content'},
                    {'type': 'trust_cta', 'text': 'Sprawdź opinie klientów', 'placement': 'conclusion'}
                ],
                'word_count_target': 2000,
                'content_difficulty': 'beginner',
                'monetization_potential': 'high',
                'keyword_density_targets': {
                    'transactional_terms': '3-4%',
                    'brand_terms': '2-3%'
                },
                'data_source': data_source
            }
        
        elif main_intent == 'navigational':
            return {
                'content_intent': 'navigational',
                'target_audience': 'Użytkownicy szukający konkretnej marki/strony',
                'tone_guidelines': 'Informacyjny, autorytarywny, brandowy. Fokus na unique value proposition.',
                'cta_recommendations': [
                    {'type': 'brand_cta', 'text': 'Odwiedź oficjalną stronę', 'placement': 'header'},
                    {'type': 'contact_cta', 'text': 'Skontaktuj się z nami', 'placement': 'conclusion'}
                ],
                'word_count_target': 1500,
                'content_difficulty': 'beginner',
                'monetization_potential': 'low',
                'keyword_density_targets': {
                    'brand_terms': '4-5%',
                    'navigational_terms': '2-3%'
                },
                'data_source': data_source
            }
        
        else:  # informational
            return {
                'content_intent': 'informational',
                'target_audience': 'Użytkownicy szukający wiedzy i informacji, top-funnel traffic',
                'tone_guidelines': 'Edukacyjny, szczegółowy, ekspercki. Fokus na wartości merytorycznej.',
                'cta_recommendations': [
                    {'type': 'educational_cta', 'text': 'Dowiedz się więcej', 'placement': 'mid_content'},
                    {'type': 'newsletter_cta', 'text': 'Zapisz się na newsletter', 'placement': 'conclusion'},
                    {'type': 'related_content', 'text': 'Zobacz powiązane artykuły', 'placement': 'sidebar'}
                ],
                'word_count_target': 3000,
                'content_difficulty': 'intermediate',
                'monetization_potential': 'low',
                'keyword_density_targets': {
                    'informational_terms': '2-3%',
                    'topic_terms': '1.5-2%'
                },
                'data_source': data_source
            }

    async def _get_intent_from_keywords_fallback(self, cluster_name: str) -> Dict:
        """Fallback intent lookup from keywords table"""
        try:
            keyword_query = self.supabase.table('keywords').select(
                'main_intent, intent_probability, search_volume, cpc'
            ).ilike('keyword', f'%{cluster_name.lower()}%').limit(5).execute()
            
            if keyword_query.data:
                # Use most common intent from matching keywords
                intents = [k.get('main_intent') for k in keyword_query.data if k.get('main_intent')]
                main_intent = max(set(intents), key=intents.count) if intents else 'informational'
                
                total_volume = sum(self._safe_get_int(k, 'search_volume', 0) for k in keyword_query.data)
                valid_cpcs = [self._safe_get_float(k, 'cpc', 0.0) for k in keyword_query.data if k.get('cpc') is not None]
                avg_cpc = (sum(valid_cpcs) / len(valid_cpcs)) if valid_cpcs else 0.0
                commercial_value = total_volume * avg_cpc
                
                self.logger.info(f"🔄 [INTENT] Keywords fallback: {main_intent}, ${commercial_value:.0f} value")
                
                fallback_intent = {
                    'main_intent': main_intent,
                    'intent_probability': 0.5,
                    'commercial_value': commercial_value,
                    'business_priority': 'medium',
                    'data_source': 'keywords_fallback'
                }
                
                return self._generate_content_strategy_from_real_intent(fallback_intent)
            
            return self._get_default_content_intent()
            
        except Exception as e:
            self.logger.error(f"❌ [INTENT] Fallback intent lookup failed: {e}")
            return self._get_default_content_intent()

    def _get_default_content_intent(self) -> Dict:
        """Default content intent when no real data available"""
        return {
            'content_intent': 'informational',
            'target_audience': 'Użytkownicy szukający informacji',
            'tone_guidelines': 'Edukacyjny, przystępny, szczegółowy',
            'cta_recommendations': [
                {'type': 'internal_link', 'text': 'Zobacz powiązane artykuły', 'placement': 'conclusion'}
            ],
            'word_count_target': 2000,
            'content_difficulty': 'intermediate',
            'monetization_potential': 'unknown',
            'keyword_density_targets': {},
            'data_source': 'default'
        }

    async def _generate_schema_templates(self, page_data: Dict, content_structure: Dict, faq_data: Dict) -> List[Dict]:
        """
        🤖 Generuje Schema.org JSON-LD templates dla różnych typów treści
        """
        templates = []
        try:
            title = page_data.get('title', '')
            url_path = page_data.get('url_path', '')
            h1_title = content_structure.get('h1_title', title)
            faq_questions = faq_data.get('questions', [])
            article_schema = {
                "@context": "https://schema.org",
                "@type": "Article",
                "headline": h1_title,
                "url": f"https://example.com{url_path}",
                "author": {
                    "@type": "Organization", 
                    "name": "SEO Expert Team"
                },
                "publisher": {
                    "@type": "Organization",
                    "name": "SEO Architecture Generator"
                },
                "datePublished": datetime.now().isoformat(),
                "dateModified": datetime.now().isoformat(),
                "description": page_data.get('meta_description', ''),
                "mainEntityOfPage": {
                    "@type": "WebPage",
                    "@id": f"https://example.com{url_path}"
                }
            }
            templates.append({
                "schema_type": "Article",
                "json_ld": article_schema,
                "priority": "high",
                "ai_citation_potential": 0.7
            })
            if faq_questions:
                faq_schema = {
                    "@context": "https://schema.org",
                    "@type": "FAQPage",
                    "mainEntity": []
                }
                for faq in faq_questions[:10]:
                    faq_schema["mainEntity"].append({
                        "@type": "Question",
                        "name": faq['question'],
                        "acceptedAnswer": {
                            "@type": "Answer",
                            "text": f"Odpowiedź na pytanie: {faq['question']} zostanie szczegółowo omówiona w artykule."
                        }
                    })
                templates.append({
                    "schema_type": "FAQPage", 
                    "json_ld": faq_schema,
                    "priority": "high",
                    "ai_citation_potential": 0.9
                })
            if "jak" in title.lower() or "how" in title.lower():
                howto_schema = {
                    "@context": "https://schema.org",
                    "@type": "HowTo",
                    "name": h1_title,
                    "description": page_data.get('meta_description', ''),
                    "step": []
                }
                h2_sections = content_structure.get('h2_structure', [])
                for i, section in enumerate(h2_sections[:8]):
                    howto_schema["step"].append({
                        "@type": "HowToStep",
                        "position": i + 1,
                        "name": section,
                        "text": f"Szczegółowe omówienie: {section}"
                    })
                templates.append({
                    "schema_type": "HowTo",
                    "json_ld": howto_schema, 
                    "priority": "medium",
                    "ai_citation_potential": 0.8
                })
            speakable_sections = []
            if content_structure.get('h2_structure'):
                for section in content_structure['h2_structure'][:3]:
                    speakable_sections.append({
                        "cssSelector": f".section-{section.lower().replace(' ', '-')}",
                        "xpath": f"//section[contains(@class, '{section.lower().replace(' ', '-')}')]"
                    })
            if speakable_sections:
                article_schema["speakable"] = {
                    "@type": "SpeakableSpecification",
                    "cssSelector": [section["cssSelector"] for section in speakable_sections]
                }
                templates[0]["speakable_sections"] = speakable_sections
            if page_data.get('content_type') == 'educational' or 'nauka' in title.lower():
                educational_schema = {
                    "@context": "https://schema.org",
                    "@type": "EducationalResource",
                    "name": h1_title,
                    "description": page_data.get('meta_description', ''),
                    "url": f"https://example.com{url_path}",
                    "educationalAlignment": {
                        "@type": "AlignmentObject",
                        "alignmentType": "teaches",
                        "educationalFramework": "Custom Learning Framework",
                        "targetName": "Content Writing Skills"
                    },
                    "learningResourceType": "Article",
                    "educationalUse": "instruction"
                }
                templates.append({
                    "schema_type": "EducationalResource",
                    "json_ld": educational_schema,
                    "priority": "medium", 
                    "ai_citation_potential": 0.6
                })
            self.logger.info(f"✅ [SCHEMA] Wygenerowano {len(templates)} schema templates")
            return templates
        except Exception as e:
            self.logger.error(f"❌ [SCHEMA] Błąd generowania schema: {e}")
            return []

    async def _save_psychology_enhanced_brief(self, page_data: Dict, semantic_data: Dict, 
                                            content_structure: Dict, intent_analysis: Dict,
                                            psychology_tone: Dict, faq_data: Dict, linking_data: Dict, 
                                            schema_templates: List[Dict], psychology_data: Dict, 
                                            funnel_stage: str) -> str:
        """
        🧠 ENHANCED: Zapisuje psychology-enhanced content brief z danymi customer journey
        
        Rozszerza JSONB pola o psychology data bez dodawania nowych kolumn
        """
        try:
            self.logger.info(f"💾 [PSYCHOLOGY_BRIEF] Zapisywanie brief z psychology enhancement")
            
            # KROK 1: Base brief data (jak oryginalnie)
            brief_data = {
                "architecture_id": page_data['architecture_id'],
                "page_id": page_data['id'],
                "h1_title": content_structure.get('h1_title', page_data['title']),
                "h2_structure": content_structure.get('h2_structure', []),
                "h3_structure": content_structure.get('h3_structure', {}),
                "primary_keywords": semantic_data.get('primary_keywords', []),
                "semantic_keywords": semantic_data.get('semantic_keywords', []),
                "related_keywords": semantic_data.get('related_keywords', []),
                "keyword_density_targets": intent_analysis.get('keyword_density_targets', {}),
                "content_intent": intent_analysis.get('content_intent', 'informational'),
                "brief_status": "ready",
                "generation_method": "ai_psychology_enhanced",
                "quality_score": 0.85
            }
            
            # KROK 2: 🧠 ROZSZERZ tone_guidelines JSONB o psychology context
            psychology_enhanced_tone = {
                # Original tone data
                **intent_analysis,
                
                # 🧠 Psychology enhancements
                'funnel_stage': funnel_stage,
                'customer_mindset': psychology_tone.get('customer_mindset', ''),
                'pain_points_addressed': psychology_tone.get('pain_points_addressed', []),
                'psychology_triggers_used': psychology_tone.get('psychology_triggers_used', []),
                'psychology_enhanced_tone': psychology_tone.get('psychology_enhanced_tone', ''),
                'emotional_journey': psychology_tone.get('emotional_journey', ''),
                'psychology_applied': psychology_data.get('psychology_applied', False),
                'psychology_confidence': psychology_data.get('funnel_confidence', 0),
                
                # Writer instructions
                'writer_instructions': psychology_tone.get('writer_instructions', {}),
                'content_focus_areas': psychology_tone.get('content_focus_areas', ''),
                
                # Source metadata
                'psychology_data_source': 'module_3_funnel_audit',
                'enhancement_timestamp': datetime.now().isoformat()
            }
            
            brief_data['tone_guidelines'] = psychology_enhanced_tone
            brief_data['target_audience'] = psychology_tone.get('target_audience', intent_analysis.get('target_audience', ''))
            brief_data['word_count_target'] = psychology_tone.get('word_count_target', intent_analysis.get('word_count_target', 2000))
            brief_data['content_difficulty'] = psychology_tone.get('content_difficulty', intent_analysis.get('content_difficulty', 'intermediate'))
            
            # KROK 3: 🧠 ROZSZERZ cta_recommendations JSONB o psychology anchors
            enhanced_ctas = []
            
            # Add original CTAs
            original_ctas = intent_analysis.get('cta_recommendations', [])
            for cta in original_ctas:
                enhanced_cta = {
                    **cta,
                    'psychology_enhancement': psychology_tone.get('cta_psychology_context', ''),
                    'emotional_trigger': psychology_tone.get('customer_mindset', ''),
                    'funnel_stage': funnel_stage
                }
                enhanced_ctas.append(enhanced_cta)
            
            # Add psychology anchors as special CTAs
            psychology_anchors = psychology_tone.get('psychology_anchors_instructions', [])
            for anchor in psychology_anchors:
                psychology_cta = {
                    'type': 'psychology_anchor',
                    'text': anchor.get('anchor_text', ''),
                    'placement': anchor.get('placement_suggestion', 'conclusion'),
                    'target_url': anchor.get('target_url', ''),
                    'psychology_trigger': anchor.get('psychology_trigger', ''),
                    'emotional_context': anchor.get('emotional_context', ''),
                    'funnel_stage': funnel_stage,
                    'priority': 'high'  # Psychology anchors are high priority
                }
                enhanced_ctas.append(psychology_cta)
            
            brief_data['cta_recommendations'] = enhanced_ctas
            
            # KROK 4: 🧠 FAQ questions z psychology context
            psychology_enhanced_faq = []
            for q in faq_data.get('questions', []):
                enhanced_faq = {
                    "question": q['question'],
                    "priority": q['priority'],
                    "source": q['source'],
                    "funnel_stage_relevance": funnel_stage,
                    "psychology_context": f"Addresses {funnel_stage} stage concerns"
                }
                psychology_enhanced_faq.append(enhanced_faq)
            
            brief_data['faq_questions'] = psychology_enhanced_faq
            
            # KROK 5: Zapisz enhanced brief
            brief_response = self.supabase.table('content_briefs').insert(brief_data).execute()
            brief_id = brief_response.data[0]['id']
            
            self.logger.info(f"💾 [PSYCHOLOGY_BRIEF] Zapisano psychology-enhanced brief: {brief_id}")
            
            # KROK 6: 🧠 ENHANCED linking instructions z strategic bridges
            enhanced_linking_instructions = []
            
            # Original linking instructions
            for link in linking_data.get('internal_links', []):
                enhanced_linking_instructions.append({
                    "content_brief_id": brief_id,
                    "link_type": "pillar_link" if link.get('link_type') == 'pillar' else "cluster_link",
                    "target_url": link['target_url'],
                    "anchor_text": link['anchor_text'],
                    "context_suggestion": link.get('context', ''),
                    "placement_section": "content_body",
                    "link_priority": link.get('priority', 'medium'),
                    "link_purpose": f"Link to {link.get('target_title', 'related content')}",
                    "follow_nofollow": "follow",
                    "funnel_stage": funnel_stage
                })
            
            # 🧠 Strategic bridges jako special linking instructions z URL MAPPING
            strategic_bridges = psychology_data.get('strategic_bridges', [])

            for bridge in strategic_bridges:
                from_url = bridge.get('from_url', '')
                to_url = bridge.get('to_url', '')
                suggested_anchor = bridge.get('suggested_anchor', '')
                rationale = bridge.get('rationale', '')
                if not from_url or not to_url:
                    continue

                # Ustal anchor
                final_anchor = suggested_anchor or f"Przejdź: {to_url.split('/')[-1]}"

                # Kontekst psychologiczny dla zapisu
                psychology_context = {
                    "bridge_rationale": rationale,
                    "psychology_trigger": bridge.get('psychology_trigger', 'relevance'),
                    "ai_confidence": bridge.get('confidence_score', 0.0),
                    "placement_suggestions": bridge.get('implementation', {}).get('placement', ['natural_flow']),
                    "priority": bridge.get('implementation', {}).get('priority', 75),
                    "customer_journey_phase": funnel_stage,
                    "module_3_source": True
                }

                bridge_instruction = {
                    "content_brief_id": brief_id,
                    "link_type": "strategic_bridge",
                    "target_url": to_url,
                    "anchor_text": final_anchor,
                    "context_suggestion": rationale or bridge.get('bridge_rationale', ''),
                    "placement_section": ', '.join(bridge.get('implementation', {}).get('placement', ['natural_flow'])),
                    "link_priority": "high",
                    "link_purpose": f"Psychology bridge - {funnel_stage} stage optimization",
                    "follow_nofollow": "follow",
                    "funnel_stage": funnel_stage,
                    "psychology_context": json.dumps(psychology_context)
                }
                enhanced_linking_instructions.append(bridge_instruction)

            # Enhanced success logging
            bridge_count = len([i for i in enhanced_linking_instructions if i['link_type'] == 'strategic_bridge'])
            self.logger.info(f"🔗 [LINKING] Enhanced matching result: {bridge_count} strategic bridges with URLs and anchors")
            
            # KROK 6.5: 🚫 DISABLED - Module 4 nie zapisuje linków, tylko czyta z architecture_links
            # UNIFIED FLOW: Module 3 zapisuje → Module 4 czyta z architecture_links
            self.logger.info(f"🚫 [LINKING] DISABLED: Module 4 nie zapisuje {len(enhanced_linking_instructions)} linking instructions")
            self.logger.info(f"🔄 [LINKING] Unified flow: Module 4 czyta linki wyłącznie z architecture_links (zapisane przez Module 3)")
            
            # LEGACY CODE - DISABLED:
            # linking_response = self.supabase.table('content_linking_instructions').insert(
            #     enhanced_linking_instructions
            # ).execute()
            
            # KROK 7: Schema templates (unchanged)
            for template in schema_templates:
                schema_data = {
                    "content_brief_id": brief_id,
                    "schema_type": template['schema_type'],
                    "json_ld": template['json_ld'],
                    "schema_priority": template.get('priority', 'medium'),
                    "ai_citation_potential": template.get('ai_citation_potential', 0.5),
                    "speakable_sections": template.get('speakable_sections', [])
                }
                if template['schema_type'] == 'Article':
                    schema_data["has_part_relations"] = await self._generate_has_part_relations(page_data)
                    schema_data["is_part_of_relations"] = await self._generate_is_part_of_relations(page_data)
                self.supabase.table('schema_templates').insert(schema_data).execute()
            
            self.logger.info(f"💾 [PSYCHOLOGY_BRIEF] Zapisano {len(schema_templates)} schema templates")
            
            self.logger.info(f"✅ [PSYCHOLOGY_BRIEF] Psychology-enhanced brief complete: "
                           f"stage={funnel_stage}, psychology_anchors={len(psychology_anchors)}, "
                           f"strategic_bridges={len(strategic_bridges)}")
            
            return brief_id
            
        except Exception as e:
            self.logger.error(f"❌ [PSYCHOLOGY_BRIEF] Błąd zapisu psychology-enhanced brief: {e}")
            # Fallback to original save method
            self.logger.info(f"🔄 [PSYCHOLOGY_BRIEF] Fallback to standard brief save")
            return await self._save_content_brief(
                page_data, semantic_data, content_structure, intent_analysis, 
                faq_data, linking_data, schema_templates
            )

    async def _generate_has_part_relations(self, page_data: Dict) -> List[Dict]:
        """Generuje relacje hasPart dla Schema.org (strona → podstrony)"""
        try:
            # Znajdź podstrony tej strony w architekturze
            child_pages = self.supabase.table('architecture_pages').select(
                'name, url_path'
            ).eq('architecture_id', page_data['architecture_id']).neq('id', page_data['id']).execute()
            has_part_relations = []
            for child in child_pages.data[:5]:  # Max 5 relacji
                has_part_relations.append({
                    "@type": "Article",
                    "url": f"https://example.com{child['url_path']}",
                    "name": child['name'],
                    "description": ""
                })
            return has_part_relations
        except Exception as e:
            self.logger.error(f"❌ [SCHEMA] Błąd generowania hasPart: {e}")
            return []

    async def _generate_is_part_of_relations(self, page_data: Dict) -> List[Dict]:
        """Generuje relacje isPartOf dla Schema.org (strona → nadrzędna struktura)"""
        try:
            main_page = self.supabase.table('architecture_pages').select(
                'name, url_path'
            ).eq('architecture_id', page_data['architecture_id']).eq('page_type', 'pillar').execute()
            if main_page.data:
                return [{
                    "@type": "WebSite",
                    "url": f"https://example.com{main_page.data[0]['url_path']}",
                    "name": main_page.data[0]['name']
                }]
            return []
        except Exception as e:
            self.logger.error(f"❌ [SCHEMA] Błąd generowania isPartOf: {e}")
            return []

    def _parse_json_response(self, ai_response: str) -> Optional[Dict]:
        """Parsuje JSON response od AI"""
        try:
            cleaned = ai_response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            elif cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1:
                json_part = cleaned[start:end+1]
                return json.loads(json_part)
            return None
        except Exception as e:
            self.logger.error(f"❌ [JSON] Błąd parsowania: {e}")
            return None

    async def _get_autocomplete_keywords(self, architecture_id: str) -> List[str]:
        # Tymczasowo zwróć pustą listę - brak seed_keyword_id w architectures
        return []

    async def _get_related_search_keywords(self, architecture_id: str) -> List[str]:
        # Tymczasowo zwróć pustą listę - brak seed_keyword_id w architectures
        return []

    async def generate_all_briefs_for_architecture(self, architecture_id: str) -> Dict:
        """
        🚀 Generuje content briefs dla wszystkich stron w architekturze
        """
        try:
            start_time = datetime.now().timestamp()
            self.logger.info(f"🚀 [BATCH] Rozpoczynam batch generation dla architecture: {architecture_id}")
            pages_response = self.supabase.table('architecture_pages').select(
                'id, name, page_type, depth_level'
            ).eq('architecture_id', architecture_id).execute()
            if not pages_response.data:
                return {"success": False, "error": "Brak stron w architekturze"}
            pages = pages_response.data
            results = []
            success_count = 0
            pages.sort(key=lambda x: (
                0 if x.get('page_type') == 'pillar' else 1,
                -(x.get('depth_level', 0))
            ))
            for i, page in enumerate(pages):
                self.logger.info(f"🔄 [BATCH] Przetwarzam stronę {i+1}/{len(pages)}: {page['name']}")
                try:
                    result = await self.generate_content_brief(page['id'])
                    if result.get('success'):
                        success_count += 1
                        results.append({
                            "page_id": page['id'],
                            "page_title": page['name'],
                            "brief_id": result['brief_id'],
                            "status": "success"
                        })
                    else:
                        results.append({
                            "page_id": page['id'],
                            "page_title": page['name'],
                            "error": result.get('error'),
                            "status": "failed"
                        })
                except Exception as e:
                    self.logger.error(f"❌ [BATCH] Błąd dla strony {page['name']}: {e}")
                    results.append({
                        "page_id": page['id'],
                        "page_title": page['name'],
                        "error": str(e),
                        "status": "failed"
                    })
                if i < len(pages) - 1:
                    await asyncio.sleep(2)
            total_time = datetime.now().timestamp() - start_time
            self.logger.info(f"✅ [BATCH] Zakończono: {success_count}/{len(pages)} success w {total_time:.1f}s")
            return {
                "success": True,
                "architecture_id": architecture_id,
                "total_pages": len(pages),
                "successful_briefs": success_count,
                "failed_briefs": len(pages) - success_count,
                "processing_time": total_time,
                "results": results
            }
        except Exception as e:
            self.logger.error(f"❌ [BATCH] Błąd batch processing: {e}")
            return {"success": False, "error": str(e)}

    async def get_content_brief(self, brief_id: str) -> Optional[Dict]:
        """Pobiera kompletny content brief z bazy"""
        try:
            brief_response = self.supabase.table('content_briefs').select('*').eq('id', brief_id).execute()
            if not brief_response.data:
                return None
            brief = brief_response.data[0]
            
            # 🔗 FIXED: Pobierz linking instructions z architecture_links (unified flow)
            page_id = brief.get('page_id')
            if page_id:
                linking_data = await self._get_linking_instructions(page_id)
                linking_instructions = linking_data.get('internal_links', [])
            else:
                self.logger.warning(f"⚠️ [BRIEF] Brak page_id w brief {brief_id} - nie można pobrać linking instructions")
                linking_instructions = []
            
            schema_response = self.supabase.table('schema_templates').select('*').eq('content_brief_id', brief_id).execute()
            return {
                "brief": brief,
                "linking_instructions": linking_instructions,
                "schema_templates": schema_response.data,
                "total_linking_instructions": len(linking_instructions),
                "total_schema_templates": len(schema_response.data)
            }
        except Exception as e:
            self.logger.error(f"❌ [DB] Błąd pobierania brief: {e}")
            return None

    async def get_architecture_briefs_summary(self, architecture_id: str) -> Dict:
        """Pobiera podsumowanie wszystkich briefów w architekturze"""
        try:
            briefs_response = self.supabase.table('content_briefs').select(
                'id, page_id, h1_title, brief_status, word_count_target, '
                'primary_keywords, content_intent, quality_score, created_at, '
                'architecture_pages!inner(name, url_path, page_type)'
            ).eq('architecture_id', architecture_id).execute()
            summary = {
                "architecture_id": architecture_id,
                "total_briefs": len(briefs_response.data),
                "ready_briefs": len([b for b in briefs_response.data if b['brief_status'] == 'ready']),
                "draft_briefs": len([b for b in briefs_response.data if b['brief_status'] == 'draft']),
                "total_word_count": sum(b.get('word_count_target', 0) for b in briefs_response.data),
                "avg_quality_score": sum(b.get('quality_score', 0) for b in briefs_response.data) / len(briefs_response.data) if briefs_response.data else 0,
                "briefs": []
            }
            for brief in briefs_response.data:
                page_data = brief.get('architecture_pages', {})
                summary["briefs"].append({
                    "brief_id": brief['id'],
                    "page_title": page_data.get('name', ''),
                    "url_path": page_data.get('url_path', ''),
                    "page_type": page_data.get('page_type', ''),
                    "h1_title": brief['h1_title'],
                    "status": brief['brief_status'],
                    "word_count": brief['word_count_target'],
                    "content_intent": brief['content_intent'],
                    "primary_keywords": brief.get('primary_keywords', []),
                    "quality_score": brief.get('quality_score', 0),
                    "created_at": brief['created_at']
                })
            return summary
        except Exception as e:
            self.logger.error(f"❌ [DB] Błąd pobierania summary: {e}")
            return {"architecture_id": architecture_id, "total_briefs": 0, "briefs": []} 

    async def _generate_psychology_tone_guidelines(self, intent_data: Dict, psychology_data: Dict, 
                                                  funnel_stage: str) -> Dict:
        """
        🧠 ENHANCED: Generuje wytyczne tonu zoptymalizowane pod customer journey i psychologię
        
        Integruje:
        - Real intent data z Modułu 1
        - Psychology triggers z Modułu 3  
        - Customer journey stage awareness
        - Strategic bridges context
        """
        try:
            self.logger.info(f"🧠 [PSYCHOLOGY_TONE] Generowanie dla stage: {funnel_stage}")
            
            # KROK 1: Base tone z intent data
            base_tone = intent_data.get('tone_guidelines', 'Edukacyjny, przystępny')
            commercial_value = intent_data.get('commercial_value', 0)
            business_priority = intent_data.get('business_priority', 'medium')
            
            # KROK 2: Psychology context z Modułu 3
            psychology_anchors = psychology_data.get('psychology_anchors', [])
            strategic_bridges = psychology_data.get('strategic_bridges', [])
            psychology_applied = psychology_data.get('psychology_applied', False)
            
            # KROK 3: Stage-specific psychology guidelines
            stage_psychology = {
                'AWARENESS': {
                    'primary_emotion': 'curiosity',
                    'pain_points': ['confusion', 'overwhelm', 'lack of knowledge'],
                    'psychology_triggers': ['education', 'trust building', 'authority'],
                    'tone_adjustments': 'Cierpliwy, edukacyjny, budujący zaufanie. Bez presji sprzedażowej.',
                    'cta_psychology': 'Soft invitation - "Dowiedz się więcej", "Eksploruj temat"',
                    'content_focus': 'Problem awareness, podstawowe zrozumienie, budowanie kredybilit'
                },
                'CONSIDERATION': {
                    'primary_emotion': 'analytical comparison',
                    'pain_points': ['decision paralysis', 'too many options', 'fear of wrong choice'],
                    'psychology_triggers': ['social proof', 'comparison frameworks', 'risk reduction'],
                    'tone_adjustments': 'Analityczny, wspierający decyzję, obiektywny ale pomocny.',
                    'cta_psychology': 'Decision support - "Porównaj opcje", "Zobacz co najlepsze"',
                    'content_focus': 'Criteria evaluation, comparisons, pros/cons, expert recommendations'
                },
                'DECISION': {
                    'primary_emotion': 'urgency with confidence',
                    'pain_points': ['final hesitation', 'trust concerns', 'timing uncertainty'],
                    'psychology_triggers': ['urgency', 'social proof', 'guarantee/risk reversal'],
                    'tone_adjustments': 'Pewny siebie, nakłaniający do działania, budujący pilność.',
                    'cta_psychology': 'Action oriented - "Rozpocznij teraz", "Skorzystaj z oferty"',
                    'content_focus': 'Final benefits, guarantees, immediate next steps, objection handling'
                }
            }
            
            stage_config = stage_psychology.get(funnel_stage, stage_psychology['AWARENESS'])
            
            # KROK 4: Integrate psychology anchors instructions
            psychology_instructions = []
            if psychology_anchors:
                for anchor in psychology_anchors[:3]:  # Top 3
                    psychology_instructions.append({
                        'anchor_text': anchor.get('text', ''),
                        'psychology_trigger': anchor.get('psychology_trigger', ''),
                        'placement_suggestion': anchor.get('placement', 'natural flow'),
                        'target_url': anchor.get('target_url', ''),
                        'emotional_context': anchor.get('emotional_context', '')
                    })
            
            # KROK 5: Strategic bridges integration guidelines
            bridge_guidelines = []
            if strategic_bridges:
                for bridge in strategic_bridges[:3]:  # Top 3 highest similarity
                    bridge_guidelines.append({
                        'target_keyword': bridge.get('target_keyword', ''),
                        'similarity_score': bridge.get('similarity_score', 0),
                        'integration_suggestion': f"Naturalnie wspomnij '{bridge.get('target_keyword', '')}' "
                                                f"w kontekście {bridge.get('context', 'general')}",
                        'target_url': bridge.get('target_url', ''),
                        'psychology_trigger': bridge.get('psychology_trigger', 'relevance')
                    })
            
            # KROK 6: Enhanced CTA recommendations z psychology
            psychology_ctas = []
            for anchor in psychology_anchors:
                psychology_ctas.append({
                    'type': 'psychology_anchor',
                    'text': anchor.get('text', ''),
                    'placement': anchor.get('placement', 'conclusion'),
                    'target_url': anchor.get('target_url', ''),
                    'psychology_trigger': anchor.get('psychology_trigger', ''),
                    'emotional_goal': anchor.get('emotional_context', '')
                })
            
            # Add traditional CTAs enhanced with stage psychology
            traditional_ctas = intent_data.get('cta_recommendations', [])
            for cta in traditional_ctas:
                cta['psychology_enhancement'] = stage_config['cta_psychology']
                cta['emotional_trigger'] = stage_config['primary_emotion']
            
            # KROK 7: Comprehensive psychology tone guidelines
            psychology_tone_guidelines = {
                # Core psychology data
                'funnel_stage': funnel_stage,
                'customer_mindset': stage_config['primary_emotion'],
                'pain_points_addressed': stage_config['pain_points'],
                'psychology_triggers_used': stage_config['psychology_triggers'],
                
                # Enhanced tone guidelines
                'base_tone': base_tone,
                'psychology_enhanced_tone': f"{base_tone} + {stage_config['tone_adjustments']}",
                'content_focus_areas': stage_config['content_focus'],
                'emotional_journey': f"Start: {stage_config['pain_points'][0]} → End: {stage_config['primary_emotion']}",
                
                # Psychology implementations
                'psychology_anchors_instructions': psychology_instructions,
                'strategic_bridges_guidelines': bridge_guidelines,
                'psychology_applied': psychology_applied,
                
                # Enhanced CTAs
                'cta_recommendations': traditional_ctas + psychology_ctas,
                'cta_psychology_context': stage_config['cta_psychology'],
                
                # Metrics context
                'commercial_value': commercial_value,
                'business_priority': business_priority,
                'psychology_confidence': psychology_data.get('funnel_confidence', 0),
                
                # Implementation guidelines
                'writer_instructions': {
                    'psychology_integration': f"Treść musi prowadzić czytelnika przez etap {funnel_stage}",
                    'anchor_placement': "Umieść psychology anchors naturalnie w flow treści",
                    'bridge_integration': "Wspominaj strategic bridges w kontekście głównego tematu",
                    'emotional_progression': f"Adresuj {stage_config['pain_points'][0]} → buduj {stage_config['primary_emotion']}"
                }
            }
            
            self.logger.info(f"✅ [PSYCHOLOGY_TONE] Wygenerowano guidelines dla {funnel_stage}: "
                           f"{len(psychology_instructions)} psychology anchors, "
                           f"{len(bridge_guidelines)} strategic bridges")
            
            return psychology_tone_guidelines
            
        except Exception as e:
            self.logger.error(f"❌ [PSYCHOLOGY_TONE] Błąd generowania psychology tone guidelines: {e}")
            # Fallback to basic tone with minimal psychology context
            return {
                'funnel_stage': funnel_stage,
                'base_tone': intent_data.get('tone_guidelines', 'Edukacyjny'),
                'psychology_enhanced_tone': f"{intent_data.get('tone_guidelines', 'Edukacyjny')} (psychology data unavailable)",
                'cta_recommendations': intent_data.get('cta_recommendations', []),
                'psychology_applied': False,
                'psychology_anchors_instructions': [],
                'strategic_bridges_guidelines': [],
                'writer_instructions': {
                    'psychology_integration': 'Standard content approach - psychology data missing'
                }
            }

    def _safe_get_int(self, data: dict, key: str, default: int = 0) -> int:
        try:
            value = data.get(key, default)
            return int(value) if value is not None else default
        except (TypeError, ValueError):
            return default

    def _safe_get_float(self, data: dict, key: str, default: float = 0.0) -> float:
        try:
            value = data.get(key, default)
            return float(value) if value is not None else default
        except (TypeError, ValueError):
            return default

    def _safe_get_str(self, data: dict, key: str, default: str = '') -> str:
        try:
            value = data.get(key, default)
            return str(value) if value is not None else default
        except (TypeError, ValueError):
            return default

    def _safe_get_list(self, data: dict, key: str, default: list = None) -> list:
        if default is None:
            default = []
        try:
            value = data.get(key, default)
            return list(value) if value is not None else default
        except (TypeError, ValueError):
            return default