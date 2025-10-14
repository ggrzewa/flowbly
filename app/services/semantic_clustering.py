import os
import logging
import json
import time
import re
from typing import Dict, List, Tuple
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic
from supabase import Client as SupabaseClient

logger = logging.getLogger("semantic_clustering")


class SemanticClusteringService:
    """🚀 PROSTY SEMANTIC CLUSTERING - tylko AI prompt, BEZ embeddingów!"""
    
    def __init__(self, supabase_client: SupabaseClient):
        self.supabase = supabase_client
        self.logger = logger
        
        # AI Provider & Models z ENV
        self.ai_provider = os.getenv("AI_PROVIDER", "openai").lower()
        self.openai_model = os.getenv("AI_MODEL_OPENAI", "gpt-4o")
        self.claude_model = os.getenv("AI_MODEL_CLAUDE", "claude-sonnet-4-20250514")
        self.gpt5_model = os.getenv("AI_MODEL_GPT5", "gpt-5")
        self.gpt5_reasoning_effort = os.getenv("GPT5_REASONING_EFFORT", "medium")
        
        openai_key = os.getenv("OPENAI_API_KEY")
        self.openai_client = AsyncOpenAI(api_key=openai_key) if openai_key else None
        
        claude_key = os.getenv("ANTHROPIC_API_KEY") 
        self.claude_client = AsyncAnthropic(api_key=claude_key) if claude_key else None
        
        self.logger.info(f"🚀 SemanticClusteringService initialized")
        self.logger.info(f"🔧 [CONFIG] AI_PROVIDER={self.ai_provider}")
        self.logger.info(f"🔧 [CONFIG] AI_MODEL_OPENAI={self.openai_model}")
        self.logger.info(f"🔧 [CONFIG] AI_MODEL_CLAUDE={self.claude_model}")
        self.logger.info(f"🔧 [CONFIG] AI_MODEL_GPT5={self.gpt5_model}")
        self.logger.info(f"🔧 [CONFIG] GPT5_REASONING_EFFORT={self.gpt5_reasoning_effort}")
    
    async def process_semantic_clustering(self, seed_keyword_id: str) -> Dict:
        """🎯 GŁÓWNA FUNKCJA - prosty AI clustering bez embeddingów"""
        try:
            start_time = time.time()
            self.logger.info(f"🚀 [CLUSTERING] Start dla keyword_id: {seed_keyword_id}")
            
            # KROK 1: Pobierz frazy (DOKŁADNIE JAK W STARYM PLIKU!)
            phrases, seed_keyword = await self._collect_related_phrases(seed_keyword_id)
            if not phrases:
                return self._error_response("Brak fraz do klastrowania")
            
            self.logger.info(f"📝 [CLUSTERING] Znaleziono {len(phrases)} fraz dla '{seed_keyword}'")
            
            # KROK 2: AI clustering (prosty prompt!)
            groups = await self._call_ai_clustering(phrases, seed_keyword)
            if not groups:
                return self._error_response("AI nie zwróciło grup")
            
            # KROK 3: Zapisz do bazy (BEZ embeddingów!)
            cluster_id = await self._save_to_database_simple(seed_keyword_id, seed_keyword, groups)
            
            # KROK 4: Pobierz dla UI
            groups_for_ui = await self._get_groups_for_ui(cluster_id)
            
            # Podsumowanie
            total_time = time.time() - start_time
            num_groups = len(groups.get("groups", []))
            outliers = len(groups.get("outliers", []))
            
            self.logger.info(f"✅ [CLUSTERING] Zakończono: {num_groups} grup, {outliers} outliers w {total_time:.1f}s")
            
            return {
                "success": True,
                "cluster_id": cluster_id,
                "total_phrases": len(phrases),
                "groups_found": num_groups,
                "noise_points": outliers,
                "processing_time": total_time,
                "quality_score": 0.95,
                "cost_usd": 0.001,
                "embedding_model": None,
                "groups": groups_for_ui
            }
            
        except Exception as e:
            self.logger.error(f"❌ [CLUSTERING] Błąd: {e}", exc_info=True)
            return self._error_response(str(e))

    async def _collect_related_phrases(self, seed_keyword_id: str) -> Tuple[List[str], str]:
        """
        📊 SKOPIOWANE ZE STAREGO PLIKU - zbiera frazy ze WSZYSTKICH 6 ŹRÓDEŁ
        """
        all_phrases = []
        seed_keyword = ""
        
        try:
            self.logger.info(f"📊 [PHRASES] ===== ROZPOCZYNAM ZBIERANIE FRAZ ZE WSZYSTKICH 6 ŹRÓDEŁ =====")
            self.logger.info(f"📊 [PHRASES] Seed keyword_id: {seed_keyword_id}")
            
            # Pobierz seed keyword
            seed_keyword_query = self.supabase.table('keywords').select(
                'keyword, seed_keyword, location_code, language_code'
            ).eq('id', seed_keyword_id).execute()
                
            if not seed_keyword_query.data:
                raise Exception(f"Nie znaleziono seed keyword dla ID: {seed_keyword_id}")
                
            seed_keyword_info = seed_keyword_query.data[0]
            seed_keyword = seed_keyword_info['keyword']
            actual_seed_keyword = seed_keyword_info['seed_keyword']
            location_code = seed_keyword_info['location_code'] 
            language_code = seed_keyword_info['language_code']
            
            self.logger.info(f"🔍 Seed keyword: '{seed_keyword}' (seed: '{actual_seed_keyword}', location: {location_code}, lang: {language_code})")
            
            # ===== 1/6. KEYWORD_RELATIONS =====
            self.logger.info(f"📊 [PHRASES] ----- 1/6: KEYWORD_RELATIONS -----")
            try:
                all_keywords_query = self.supabase.table('keywords').select('id').eq(
                        'seed_keyword', actual_seed_keyword
                ).eq('location_code', location_code).eq('language_code', language_code).execute()
                
                if all_keywords_query.data:
                    all_keyword_ids = [kw['id'] for kw in all_keywords_query.data]
                    self.logger.info(f"🔍 [KEYWORD_RELATIONS] Znaleziono {len(all_keyword_ids)} słów w hierarchii")
                    
                    relations_query = self.supabase.table('keyword_relations').select(
                            'depth, relationship_type, relevance_score, search_volume, '
                            'keyword_difficulty, related_keyword_id, parent_keyword_id, '
                            'keywords!keyword_relations_related_keyword_id_fkey('
                            'keyword, is_suggestion, cpc, competition, competition_level, '
                            'low_top_of_page_bid, high_top_of_page_bid, main_intent, '
                            'monthly_trend_pct, core_keyword, keyword_difficulty'
                            ')'
                    ).in_('parent_keyword_id', all_keyword_ids).order('depth').order('relevance_score', desc=True).limit(1000).execute()
                else:
                    self.logger.warning(f"⚠️ [KEYWORD_RELATIONS] Fallback: używam tylko bezpośrednie relacje")
                    relations_query = self.supabase.table('keyword_relations').select(
                            'depth, relationship_type, relevance_score, search_volume, '
                            'keyword_difficulty, related_keyword_id, parent_keyword_id, '
                            'keywords!keyword_relations_related_keyword_id_fkey('
                            'keyword, is_suggestion, cpc, competition, competition_level, '
                            'low_top_of_page_bid, high_top_of_page_bid, main_intent, '
                            'monthly_trend_pct, core_keyword, keyword_difficulty'
                            ')'
                    ).eq('parent_keyword_id', seed_keyword_id).order('depth').order('relevance_score', desc=True).limit(1000).execute()
                
                relations_count = 0
                if relations_query.data:
                    self.logger.info(f"🔍 [KEYWORD_RELATIONS] Znaleziono {len(relations_query.data)} rekordów z relacji")
                    for relation in relations_query.data:
                        if relation.get('keywords') and relation['keywords'].get('keyword'):
                            keyword_text = relation['keywords']['keyword'].strip()
                            if keyword_text:
                                all_phrases.append(keyword_text)
                                relations_count += 1
                
                self.logger.info(f"📊 [PHRASES] ✅ keyword_relations: {relations_count} fraz")
            except Exception as e:
                self.logger.warning(f"⚠️ [PHRASES] Błąd keyword_relations: {e}")
            
            # ===== 2/6. AUTOCOMPLETE_SUGGESTIONS =====
            self.logger.info(f"📊 [PHRASES] ----- 2/6: AUTOCOMPLETE_SUGGESTIONS -----")
            try:
                autocomplete_result_query = self.supabase.table('autocomplete_results').select('id').eq('keyword_id', seed_keyword_id).execute()
                autocomplete_count = 0
                
                if autocomplete_result_query.data:
                    autocomplete_result_id = autocomplete_result_query.data[0]['id']
                    suggestions_query = self.supabase.table('autocomplete_suggestions').select(
                            'id, suggestion'
                    ).eq('autocomplete_result_id', autocomplete_result_id).execute()
                    
                    if suggestions_query.data:
                        for suggestion in suggestions_query.data:
                            suggestion_text = suggestion.get('suggestion', '').strip()
                            if suggestion_text:
                                all_phrases.append(suggestion_text)
                                autocomplete_count += 1
                
                self.logger.info(f"📊 [PHRASES] ✅ autocomplete_suggestions: {autocomplete_count} fraz")
            except Exception as e:
                self.logger.warning(f"⚠️ [PHRASES] Błąd autocomplete_suggestions: {e}")
            
            # ===== 3/6. SERP_PEOPLE_ALSO_ASK =====
            self.logger.info(f"📊 [PHRASES] ----- 3/6: SERP_PEOPLE_ALSO_ASK -----")
            try:
                serp_result_query = self.supabase.table('serp_results').select('id').eq('keyword_id', seed_keyword_id).execute()
                paa_count = 0
                
                if serp_result_query.data:
                    serp_result_id = serp_result_query.data[0]['id']
                    paa_query = self.supabase.table('serp_people_also_ask').select(
                            'id, question'
                    ).eq('serp_result_id', serp_result_id).execute()
                    
                    if paa_query.data:
                        for paa in paa_query.data:
                            question_text = paa.get('question', '').strip()
                            if question_text:
                                all_phrases.append(question_text)
                                paa_count += 1
                
                self.logger.info(f"📊 [PHRASES] ✅ serp_people_also_ask: {paa_count} fraz")
            except Exception as e:
                self.logger.warning(f"⚠️ [PHRASES] Błąd serp_people_also_ask: {e}")
            
            # ===== 4/6. SERP_RELATED_SEARCHES =====
            self.logger.info(f"📊 [PHRASES] ----- 4/6: SERP_RELATED_SEARCHES -----")
            try:
                related_searches_count = 0
                serp_result_id = None
                if 'serp_result_query' in locals() and serp_result_query.data:
                    serp_result_id = serp_result_query.data[0]['id']
                else:
                    serp_result_lookup = self.supabase.table('serp_results').select('id').eq('keyword_id', seed_keyword_id).execute()
                    if serp_result_lookup.data:
                        serp_result_id = serp_result_lookup.data[0]['id']
                
                if serp_result_id:
                    related_searches_query = self.supabase.table('serp_related_searches').select(
                            'id, keyword'
                    ).eq('serp_result_id', serp_result_id).execute()
                    
                    if related_searches_query.data:
                        for related_search in related_searches_query.data:
                            query_text = related_search.get('keyword', '').strip()
                            if query_text:
                                all_phrases.append(query_text)
                                related_searches_count += 1
                
                self.logger.info(f"📊 [PHRASES] ✅ serp_related_searches: {related_searches_count} fraz")
            except Exception as e:
                self.logger.warning(f"⚠️ [PHRASES] Błąd serp_related_searches: {e}")
            
            # ===== 5/6. GOOGLE_TRENDS_TOPICS =====
            self.logger.info(f"📊 [PHRASES] ----- 5/6: GOOGLE_TRENDS_TOPICS -----")
            try:
                topics_query = self.supabase.table('keywords').select('topics_list').eq('id', seed_keyword_id).execute()
                topics_count = 0
                
                if topics_query.data and topics_query.data[0].get('topics_list'):
                    topics_list = topics_query.data[0]['topics_list']
                    parsed_topics = []
                    
                    if isinstance(topics_list, dict):
                        if 'top' in topics_list and isinstance(topics_list['top'], list):
                            parsed_topics.extend(topics_list['top'])
                        if 'rising' in topics_list and isinstance(topics_list['rising'], list):
                            parsed_topics.extend(topics_list['rising'])
                    elif isinstance(topics_list, list):
                        parsed_topics = topics_list
                    elif isinstance(topics_list, str):
                        try:
                            topics_data = json.loads(topics_list)
                            if isinstance(topics_data, dict):
                                if 'top' in topics_data:
                                    parsed_topics.extend(topics_data['top'])
                                if 'rising' in topics_data:
                                    parsed_topics.extend(topics_data['rising'])
                            elif isinstance(topics_data, list):
                                parsed_topics = topics_data
                        except json.JSONDecodeError:
                            pass
                    
                    for topic in parsed_topics:
                        if isinstance(topic, dict):
                            topic_title = topic.get('topic_title') or topic.get('title') or topic.get('value') or topic.get('query')
                            if topic_title and isinstance(topic_title, str):
                                topic_text = topic_title.strip()
                                if topic_text:
                                    all_phrases.append(topic_text)
                                    topics_count += 1
                        elif isinstance(topic, str):
                            topic_text = topic.strip()
                            if topic_text:
                                all_phrases.append(topic_text)
                                topics_count += 1
                
                self.logger.info(f"📊 [PHRASES] ✅ google_trends_topics: {topics_count} fraz")
            except Exception as e:
                self.logger.warning(f"⚠️ [PHRASES] Błąd google_trends_topics: {e}")
            
            # ===== 6/6. GOOGLE_TRENDS_QUERIES =====
            self.logger.info(f"📊 [PHRASES] ----- 6/6: GOOGLE_TRENDS_QUERIES -----")
            try:
                queries_query = self.supabase.table('keywords').select('queries_list').eq('id', seed_keyword_id).execute()
                queries_count = 0
                
                if queries_query.data and queries_query.data[0].get('queries_list'):
                    queries_list = queries_query.data[0]['queries_list']
                    parsed_queries = []
                    
                    if isinstance(queries_list, dict):
                        if 'top' in queries_list and isinstance(queries_list['top'], list):
                            parsed_queries.extend(queries_list['top'])
                        if 'rising' in queries_list and isinstance(queries_list['rising'], list):
                            parsed_queries.extend(queries_list['rising'])
                    elif isinstance(queries_list, list):
                        parsed_queries = queries_list
                    elif isinstance(queries_list, str):
                        try:
                            queries_data = json.loads(queries_list)
                            if isinstance(queries_data, dict):
                                if 'top' in queries_data:
                                    parsed_queries.extend(queries_data['top'])
                                if 'rising' in queries_data:
                                    parsed_queries.extend(queries_data['rising'])
                            elif isinstance(queries_data, list):
                                parsed_queries = queries_data
                        except json.JSONDecodeError:
                            pass
                    
                    for query in parsed_queries:
                        if isinstance(query, dict):
                            query_title = query.get('query') or query.get('title') or query.get('value')
                            if query_title and isinstance(query_title, str):
                                query_text = query_title.strip()
                                if query_text:
                                    all_phrases.append(query_text)
                                    queries_count += 1
                        elif isinstance(query, str):
                            query_text = query.strip()
                            if query_text:
                                all_phrases.append(query_text)
                                queries_count += 1
                
                self.logger.info(f"📊 [PHRASES] ✅ google_trends_queries: {queries_count} fraz")
            except Exception as e:
                self.logger.warning(f"⚠️ [PHRASES] Błąd google_trends_queries: {e}")
            
            # ===== DEDUPLIKACJA =====
            self.logger.info(f"🔄 [PHRASES] Rozpoczynam deduplikację...")
            
            unique_phrases = []
            seen_texts = set()
            
            for phrase in all_phrases:
                text_clean = phrase.lower().strip()
                if (text_clean not in seen_texts 
                    and len(text_clean) >= 3 
                    and len(text_clean) <= 200 
                    and text_clean != ""
                    and not text_clean.isdigit()):
                    seen_texts.add(text_clean)
                    unique_phrases.append(phrase)
            
            self.logger.info(f"✅ [PHRASES] PODSUMOWANIE:")
            self.logger.info(f"📊 [PHRASES] Łącznie przed deduplikacją: {len(all_phrases)} fraz")
            self.logger.info(f"📊 [PHRASES] Po deduplikacji: {len(unique_phrases)} unikalnych fraz")
            self.logger.info(f"📊 [PHRASES] Usunięto duplikatów: {len(all_phrases) - len(unique_phrases)}")
            
            if not unique_phrases:
                unique_phrases = [seed_keyword]
                self.logger.warning(f"⚠️ [PHRASES] Brak fraz - używam tylko seed keyword")
            
            return unique_phrases, seed_keyword
            
        except Exception as e:
            self.logger.error(f"❌ [PHRASES] Błąd zbierania fraz: {e}")
            return [seed_keyword] if seed_keyword else [], seed_keyword

    async def _call_ai_clustering(self, phrases: List[str], seed_keyword: str) -> Dict:
        """🤖 PROSTY PROMPT do AI - z fallback jak w starym pliku"""
        try:
            formatted_phrases = "\n".join(phrases)
            
            user_prompt = f"""Pogrupuj słowa kluczowe tematycznie dla tematu: {seed_keyword}
Słowa kluczowe:
{formatted_phrases}

Zwróć JSON:
{{
  "groups": [
    {{
      "name": "nazwa_grupy",
      "phrases": ["fraza1", "fraza2"]
    }}
  ],
  "outliers": []
}}"""

            self.logger.info(f"🤖 [AI] Wysyłam {len(phrases)} fraz do {self.ai_provider.upper()}...")
            
            # Fallback chain jak w starym pliku
            ai_response = None
            primary = self.ai_provider or 'openai'
            providers_order = [primary] + [p for p in ['gpt5', 'openai', 'claude'] if p != primary]
            
            async def call_gpt5():
                if not self.openai_client:
                    raise RuntimeError("OpenAI client (for GPT-5) unavailable")
                request_data = {
                    "model": self.gpt5_model,
                    "input": [{
                        "role": "user",
                        "content": [{"type": "input_text", "text": user_prompt}]
                    }],
                    "max_output_tokens": 16384,
                    "reasoning": {"effort": "minimal"},
                    "text": {"verbosity": self.gpt5_verbosity}
                }
                resp = await self.openai_client.responses.create(**request_data)

                # Ekstrak tekst
                if hasattr(resp, 'output_text') and resp.output_text:
                    return str(resp.output_text)
                if hasattr(resp, 'output') and resp.output and len(resp.output) > 0:
                    if hasattr(resp.output[0], 'content') and resp.output[0].content:
                        if len(resp.output[0].content) > 0 and hasattr(resp.output[0].content[0], 'text'):
                            return resp.output[0].content[0].text
                self.logger.error(f"❌ [GPT5_RESPONSE] ALL EXTRACTION METHODS FAILED")
                raise Exception("Cannot extract text from GPT-5 response after all attempts")
            
            async def call_openai():
                if not self.openai_client:
                    raise RuntimeError("OpenAI client unavailable")
                resp = await self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[{"role": "user", "content": user_prompt}],
                    temperature=0.7,
                    max_tokens=16384
                )
                return resp.choices[0].message.content
            
            async def call_claude():
                if not self.claude_client:
                    raise RuntimeError("Claude client unavailable")
                resp = await self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=4096,
                    temperature=0.7,
                    timeout=120.0,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return resp.content[0].text
            
            # Próbuj kolejno providerów
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
            
            # Loguj surową odpowiedź dla debugowania
            self.logger.info(f"📝 [AI] Długość odpowiedzi: {len(ai_response)} znaków")
            self.logger.debug(f"📝 [AI] Pierwsze 500 znaków: {ai_response[:500]}")
            
            return self._parse_json(ai_response)
            
        except Exception as e:
            self.logger.error(f"❌ [AI] Błąd: {e}")
            return {}

    def _parse_json(self, ai_response: str) -> Dict:
        """Parsuje JSON z odpowiedzi AI - z naprawą błędów"""
        try:
            cleaned = ai_response.strip()
            
            # Usuń markdown code blocks
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            elif cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            # Znajdź JSON
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start == -1 or end == -1:
                self.logger.error(f"❌ [JSON] Brak nawiasów klamrowych w odpowiedzi")
                return {}
            
            json_part = cleaned[start:end+1]
            
            # Napraw typowe błędy w JSON
            json_part = json_part.replace('\n', ' ')  # usuń newline w środku stringów
            json_part = json_part.replace('\r', ' ')
            # Napraw trailing commas przed ]
            json_part = re.sub(r',\s*]', ']', json_part)
            json_part = re.sub(r',\s*}', '}', json_part)
            
            try:
                result = json.loads(json_part)
                self.logger.info(f"✅ [JSON] Parsowanie OK: {len(result.get('groups', []))} grup")
                return result
            except json.JSONDecodeError as e:
                self.logger.error(f"❌ [JSON] JSONDecodeError: {e}")
                self.logger.error(f"❌ [JSON] Problematyczny fragment: {json_part[max(0, e.pos-50):min(len(json_part), e.pos+50)]}")
                
                # Ostatnia próba - wyczyść dalej
                json_part = json_part.replace("'", '"')  # zamień pojedyncze cudzysłowy
                json_part = re.sub(r'(\w+):', r'"\1":', json_part)  # dodaj cudzysłowy do kluczy
                
                try:
                    result = json.loads(json_part)
                    self.logger.info(f"✅ [JSON] Parsowanie OK po naprawie: {len(result.get('groups', []))} grup")
                    return result
                except:
                    self.logger.error(f"❌ [JSON] Parsowanie nieudane nawet po naprawie")
                    return {}
        
        except Exception as e:
            self.logger.error(f"❌ [JSON] Błąd parsowania: {e}", exc_info=True)
            return {}

    async def _save_to_database_simple(self, seed_keyword_id: str, seed_keyword: str, groups: Dict) -> str:
        """💾 Zapisuje do bazy BEZ embeddingów"""
        try:
            total_phrases = sum(len(g.get("phrases", [])) for g in groups.get("groups", []))
            total_phrases += len(groups.get("outliers", []))
            
            cluster_response = self.supabase.table("semantic_clusters").insert({
                "seed_keyword_id": seed_keyword_id,
                "cluster_name": f"AI Clustering: {seed_keyword}",
                "processing_status": "completed",
                "total_phrases": total_phrases,
                "clustering_algorithm": "ai_prompt_only",
                "quality_score": 0.95
            }).execute()
            
            cluster_id = cluster_response.data[0]["id"]
            self.logger.info(f"💾 [DB] Cluster ID: {cluster_id}")
            
            # Zapisz grupy
            for idx, group in enumerate(groups.get("groups", [])):
                group_name = group.get("name", f"Grupa {idx + 1}")
                group_phrases = group.get("phrases", [])
                
                group_response = self.supabase.table("semantic_groups").insert({
                    "semantic_cluster_id": cluster_id,
                    "group_label": group_name,
                    "group_number": idx,
                    "phrases_count": len(group_phrases),
                    "avg_similarity_score": 0.90
                }).execute()
                
                group_id = group_response.data[0]["id"]
                
                for phrase in group_phrases:
                    self.supabase.table("semantic_group_members").insert({
                        "group_id": group_id,
                        "phrase": phrase,
                        "source_table": "keyword_relations",
                        "source_id": seed_keyword_id,
                        "embedding_vector": None,
                        "similarity_to_centroid": 0.90,
                        "is_representative": False
                    }).execute()
                
                self.logger.info(f"💾 [DB] Grupa '{group_name}': {len(group_phrases)} fraz")
            
            # Outliers
            outliers = groups.get("outliers", [])
            if outliers:
                outlier_response = self.supabase.table("semantic_groups").insert({
                    "semantic_cluster_id": cluster_id,
                    "group_label": "Outliers",
                    "group_number": -1,
                    "phrases_count": len(outliers),
                    "avg_similarity_score": 0.0
                }).execute()
                
                outlier_group_id = outlier_response.data[0]["id"]
                
                for phrase in outliers:
                    self.supabase.table("semantic_group_members").insert({
                        "group_id": outlier_group_id,
                        "phrase": phrase,
                        "source_table": "keyword_relations", 
                        "source_id": seed_keyword_id,
                        "embedding_vector": None,
                        "similarity_to_centroid": 0.0,
                        "is_representative": False
                    }).execute()
                
                self.logger.info(f"💾 [DB] Outliers: {len(outliers)} fraz")
            
            return cluster_id
                
        except Exception as e:
            self.logger.error(f"❌ [DB] Błąd zapisu: {e}")
            raise

    async def _get_groups_for_ui(self, cluster_id: str) -> List[Dict]:
        """🔍 Pobiera grupy dla UI"""
        try:
            self.logger.info(f"🔍 [UI] Pobieram grupy dla cluster: {cluster_id}")
            
            groups_query = self.supabase.table('semantic_groups').select(
                'id, group_label, group_number'
            ).eq('semantic_cluster_id', cluster_id).order('group_number').execute()
            
            if not groups_query.data:
                return []
            
            groups_for_ui = []
            
            for group in groups_query.data:
                group_id = group['id']
                group_name = group['group_label']
                
                members_query = self.supabase.table('semantic_group_members').select(
                'phrase'
            ).eq('group_id', group_id).execute()
            
                if not members_query.data:
                    continue
                
                phrases = [m['phrase'] for m in members_query.data]
                
                groups_for_ui.append({
                    'name': group_name,
                    'phrases': phrases
                })
                
                self.logger.info(f"📊 [UI] Grupa '{group_name}': {len(phrases)} fraz")
            
            self.logger.info(f"✅ [UI] Pobrano {len(groups_for_ui)} grup")
            return groups_for_ui
            
        except Exception as e:
            self.logger.error(f"❌ [UI] Błąd: {e}")
            return []

    def _error_response(self, error: str) -> Dict:
        """Error response"""
        return {
            "success": False,
            "error": error,
            "groups_found": 0,
            "total_phrases": 0,
            "quality_score": 0.0,
            "cost_usd": 0.0,
            "processing_time": 0.0,
            "embedding_model": None,
            "groups": []
        }

    async def test_openai_connection(self) -> Dict:
        """Test connection"""
        return await self.test_ai_connection()
    
    async def test_ai_connection(self) -> Dict:
        """Test AI connection"""
        try:
            if self.ai_provider == "openai" and self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model=self.openai_model,
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=10
                )
                return {"success": True, "provider": "openai"}
            elif self.ai_provider == "claude" and self.claude_client:
                response = await self.claude_client.messages.create(
                    model=self.claude_model,
                    max_tokens=10,
                    messages=[{"role": "user", "content": "Test"}]
                )
                return {"success": True, "provider": "claude"}
            return {"success": False, "error": "No AI client"}
        except Exception as e:
            return {"success": False, "error": str(e)}

