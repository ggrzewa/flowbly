import os
import logging
import asyncio
import json
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Any
from fastapi import HTTPException
from supabase import create_client, Client
from dotenv import load_dotenv

# Import funkcji z istniejących plików
from app.api.parsing_keyword_v3 import (
    analyze_related_only, 
    analyze_suggestions_only, 
    analyze_trends_only,
    analyze_gt_explore_only, 
    analyze_historical_only,
    analyze_intent_only,
    KeywordAnalysisInput
)
from app.api.serp_google_live_advanced import (
    get_serp_and_save_to_database,
    SerpOrganicInput
)
from app.api.autocomplete_google_live_advanced import (
    get_autocomplete_and_save_to_database,
    AutocompleteInput
)

# ========================================
# ENVIRONMENT SETUP
# ========================================
load_dotenv()

# Logger setup
logger = logging.getLogger("seo_orchestrator")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Configuration
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================================
# SEO ANALYSIS ORCHESTRATOR
# ========================================
class SEOAnalysisOrchestrator:
    def __init__(self):
        # Add supabase client as instance attribute for Moduł 3 compatibility
        self.supabase = supabase
        
        self.steps = [
            {
                "name": "Analizuję powiązane słowa kluczowe...",
                "function": self._run_related_analysis,
                "timeout": 120,
                "required": True
            },
            {
                "name": "Pobieram sugestie słów kluczowych...",
                "function": self._run_suggestions_analysis,
                "timeout": 120,
                "required": False
            },
            {
                "name": "Analizuję intencje wyszukiwania...",
                "function": self._run_intent_analysis,
                "timeout": 90,
                "required": False
            },
            {
                "name": "Sprawdzam wyniki SERP...",
                "function": self._run_serp_analysis,
                "timeout": 150,
                "required": True
            },
            {
                "name": "Analizuję autocomplete...",
                "function": self._run_autocomplete_analysis,
                "timeout": 120,
                "required": False
            },
            {
                "name": "Pobieram dane historyczne...",
                "function": self._run_historical_analysis,
                "timeout": 120,
                "required": False
            },
            {
                "name": "Analizuję trendy DataForSEO...",
                "function": self._run_trends_analysis,
                "timeout": 120,
                "required": False
            },
            {
                "name": "Sprawdzam Google Trends...",
                "function": self._run_gt_explore_analysis,
                "timeout": 120,
                "required": False
            }
        ]
        
        # Cache dla wyników (1 godzina)
        self.cache = {}
        self.cache_duration = timedelta(hours=1)
    
    async def run_complete_analysis(self, keyword: str, location_code: int, language_code: str, use_cache: bool = True) -> Dict:
        """
        Uruchamia kompletną analizę słowa kluczowego przez wszystkie dostępne źródła.
        Zwraca postęp i status każdego kroku.
        """
        cache_key = f"{keyword}_{location_code}_{language_code}"
        
        # Sprawdź cache
        if use_cache and cache_key in self.cache:
            cached_result = self.cache[cache_key]
            if datetime.now() - cached_result["timestamp"] < self.cache_duration:
                logger.info(f"🔄 Zwracam wyniki z cache dla: {keyword}")
                cached_result["from_cache"] = True
                return cached_result["data"]
        
        logger.info(f"🚀 Rozpoczynam kompletną analizę SEO dla: {keyword}")
        
        results = []
        total_cost = 0.0
        start_time = datetime.now()
        
        # Przygotuj input objects
        keyword_input = KeywordAnalysisInput(
            keyword=keyword,
            location_code=location_code,
            language_code=language_code
        )
        
        serp_input = SerpOrganicInput(
            keyword=keyword,
            location_code=location_code,
            language_code=language_code,
            device="desktop",
            os="windows",
            depth=100,
            calculate_rectangles=False,
            group_organic_results=True
        )
        
        autocomplete_input = AutocompleteInput(
            keyword=keyword,
            location_code=location_code,
            language_code=language_code,
            include_analysis=True
        )
        
        for i, step in enumerate(self.steps):
            step_start = datetime.now()
            logger.info(f"🔄 Krok {i+1}/{len(self.steps)}: {step['name']}")
            
            try:
                # Wykonaj krok z timeout
                result = await asyncio.wait_for(
                    step["function"](keyword_input, serp_input, autocomplete_input),
                    timeout=step["timeout"]
                )
                
                step_duration = (datetime.now() - step_start).total_seconds()
                step_cost = result.get("cost_usd", 0) if result else 0
                
                results.append({
                    "step": i + 1,
                    "name": step["name"],
                    "status": "success",
                    "cost": step_cost,
                    "duration_seconds": step_duration,
                    "details": result,
                    "timestamp": datetime.now().isoformat()
                })
                
                total_cost += step_cost
                logger.info(f"✅ Krok {i+1} zakończony pomyślnie - koszt: ${step_cost:.4f}, czas: {step_duration:.1f}s")
                
            except asyncio.TimeoutError:
                logger.warning(f"⏰ Timeout kroku {i+1}: {step['name']}")
                results.append({
                    "step": i + 1,
                    "name": step["name"],
                    "status": "timeout",
                    "error": f"Przekroczono limit czasu {step['timeout']}s",
                    "cost": 0,
                    "duration_seconds": step["timeout"],
                    "timestamp": datetime.now().isoformat()
                })
                
                # Jeśli to wymagany krok, przerwij analizę
                if step["required"]:
                    logger.error(f"❌ Wymagany krok {i+1} nie powiódł się - przerywam analizę")
                    break
                    
            except Exception as e:
                step_duration = (datetime.now() - step_start).total_seconds()
                logger.exception(f"❌ Błąd w kroku {i+1}: {str(e)}")
                
                results.append({
                    "step": i + 1,
                    "name": step["name"],
                    "status": "error",
                    "error": str(e),
                    "cost": 0,
                    "duration_seconds": step_duration,
                    "timestamp": datetime.now().isoformat()
                })
                
                # Jeśli to wymagany krok, przerwij analizę
                if step["required"]:
                    logger.error(f"❌ Wymagany krok {i+1} nie powiódł się - przerywam analizę")
                    break
        
        total_duration = (datetime.now() - start_time).total_seconds()
        successful_steps = len([r for r in results if r["status"] == "success"])
        
        # Pobierz keyword_id z bazy po zakończeniu analizy
        keyword_id = None
        if successful_steps > 0:
            try:
                keyword_query = supabase.table("keywords").select("id").eq(
                    "keyword", keyword
                ).eq(
                    "location_code", location_code
                ).eq(
                    "language_code", language_code
                ).execute()
                
                if keyword_query.data:
                    keyword_id = keyword_query.data[0]["id"]
                    logger.info(f"🔗 Pobrano keyword_id dla klastrowania: {keyword_id}")
                else:
                    logger.warning(f"⚠️ Nie znaleziono keyword_id w bazie dla: {keyword}")
            except Exception as e:
                logger.warning(f"⚠️ Błąd pobierania keyword_id: {str(e)}")
        
        final_result = {
            "success": successful_steps > 0,
            "keyword": keyword,
            "keyword_id": keyword_id,  # DODANO dla klastrowania semantycznego
            "location_code": location_code,
            "language_code": language_code,
            "total_steps": len(self.steps),
            "completed_steps": successful_steps,
            "failed_steps": len([r for r in results if r["status"] == "error"]),
            "timeout_steps": len([r for r in results if r["status"] == "timeout"]),
            "total_cost": round(total_cost, 6),
            "total_duration_seconds": round(total_duration, 1),
            "results": results,
            "timestamp": datetime.now().isoformat(),
            "from_cache": False
        }
        
        # Cache wyników jeśli analiza się powiodła
        if final_result["success"]:
            self.cache[cache_key] = {
                "data": final_result,
                "timestamp": datetime.now()
            }
        
        logger.info(f"🎯 Analiza zakończona: {successful_steps}/{len(self.steps)} kroków pomyślnych, koszt: ${total_cost:.4f}, czas: {total_duration:.1f}s")
        
        return final_result
    
    # ========================================
    # INDIVIDUAL ANALYSIS FUNCTIONS
    # ========================================
    
    async def _run_related_analysis(self, keyword_input, serp_input, autocomplete_input):
        """Uruchamia analizę powiązanych słów kluczowych"""
        return await analyze_related_only(keyword_input)
    
    async def _run_suggestions_analysis(self, keyword_input, serp_input, autocomplete_input):
        """Uruchamia analizę sugestii słów kluczowych"""
        return await analyze_suggestions_only(keyword_input)
    
    async def _run_intent_analysis(self, keyword_input, serp_input, autocomplete_input):
        """Uruchamia analizę intencji wyszukiwania"""
        return await analyze_intent_only(keyword_input)
    
    async def _run_serp_analysis(self, keyword_input, serp_input, autocomplete_input):
        """Uruchamia analizę wyników SERP"""
        return await get_serp_and_save_to_database(serp_input)
    
    async def _run_autocomplete_analysis(self, keyword_input, serp_input, autocomplete_input):
        """Uruchamia analizę autocomplete"""
        return await get_autocomplete_and_save_to_database(autocomplete_input)
    
    async def _run_historical_analysis(self, keyword_input, serp_input, autocomplete_input):
        """Uruchamia analizę danych historycznych"""
        return await analyze_historical_only(keyword_input)
    
    async def _run_trends_analysis(self, keyword_input, serp_input, autocomplete_input):
        """Uruchamia analizę trendów DataForSEO"""
        return await analyze_trends_only(keyword_input)
    
    async def _run_gt_explore_analysis(self, keyword_input, serp_input, autocomplete_input):
        """Uruchamia analizę Google Trends Explore"""
        return await analyze_gt_explore_only(keyword_input)
    
    # ========================================
    # COUNTRIES FUNCTION
    # ========================================
    
    async def get_available_countries(self) -> List[Dict]:
        """
        Pobiera listę aktywnych krajów z bazy do wyświetlenia w formularzu.
        Zwraca dane w formacie gotowym dla HTML select dropdown.
        """
        try:
            logger.info("🌍 Pobieranie listy krajów z bazy danych...")
            countries = supabase.table("countries").select(
                "location_code, location_name, language_code, country_iso_code"
            ).eq("is_active", True).order("location_name").execute()
            
            if countries.data:
                result = [
                    {
                        "value": f"{country['location_code']}|{country['language_code']}", 
                        "text": country["location_name"],
                        "location_code": country["location_code"],
                        "language_code": country["language_code"],
                        "iso_code": country["country_iso_code"]
                    }
                    for country in countries.data
                ]
                logger.info(f"✅ Załadowano {len(result)} krajów z bazy danych")
                return result
            else:
                raise Exception("Brak danych w tabeli countries")
                
        except Exception as e:
            logger.warning(f"⚠️ Błąd pobierania krajów z bazy: {str(e)} - używam fallback")
            # Fallback do podstawowych krajów jeśli baza nie odpowiada
            return [
                {"value": "2616|pl", "text": "Poland", "location_code": 2616, "language_code": "pl", "iso_code": "PL"},
                {"value": "2840|en", "text": "United States", "location_code": 2840, "language_code": "en", "iso_code": "US"},
                {"value": "2276|de", "text": "Germany", "location_code": 2276, "language_code": "de", "iso_code": "DE"},
                {"value": "2826|en", "text": "United Kingdom", "location_code": 2826, "language_code": "en", "iso_code": "GB"},
                {"value": "2250|fr", "text": "France", "location_code": 2250, "language_code": "fr", "iso_code": "FR"}
            ]
    
    async def get_keyword_header_data(self, keyword: str, location_code: int, language_code: str) -> Dict:
        """
        Pobiera dane z tabeli keywords dla SEKCJI 1: EXTENDED HEADER
        + SEKCJI 2: EXTENDED CORE SEO METRICS  
        + SEKCJI 3: COMPLETE INTENT ANALYSIS
        + SEKCJA 4: COMPLETE DEMOGRAPHICS
        + SEKCJA 5: EXTENDED TRENDS & SEASONALITY
        + SEKCJA 6: COMPLETE GEOGRAPHIC DATA
        + SEKCJA 7: ENHANCED COMPETITION ANALYSIS
        + SEKCJA 8: ENHANCED RELATED KEYWORDS WITH HIERARCHY
        + SEKCJA 9: ENHANCED SERP ANALYSIS
        + SEKCJA 10: ENHANCED AUTOCOMPLETE ANALYSIS
        Zwraca wszystkie potrzebne pola do wyświetlenia nagłówka słowa kluczowego
        """
        try:
            logger.info(f"📊 Pobieranie header data dla: {keyword}")
            
            # Pobierz dane z tabeli keywords
            query = supabase.table("keywords").select("*").eq(
                "keyword", keyword
            ).eq(
                "location_code", location_code  
            ).eq(
                "language_code", language_code
            ).execute()
            
            if not query.data:
                return None
                
            keyword_data = query.data[0]
            keyword_id = keyword_data.get("id")
            
            # DEBUGGING: Loguj dane intent z tabeli keywords
            logger.info(f"🔍 SEKCJA 3 DEBUG - keywords intent data:")
            logger.info(f"  main_intent: {keyword_data.get('main_intent')}")
            logger.info(f"  intent_probability: {keyword_data.get('intent_probability')}")
            logger.info(f"  secondary_intents: {keyword_data.get('secondary_intents')}")
            
            # Pobierz dane z autocomplete_results dla SEKCJI 3
            autocomplete_data = None
            try:
                autocomplete_query = supabase.table("autocomplete_results").select(
                    "intent_analysis, trending_modifiers, content_opportunities"
                ).eq("keyword_id", keyword_id).execute()
                
                if autocomplete_query.data:
                    autocomplete_data = autocomplete_query.data[0]
                    logger.info(f"✅ Pobrano dane autocomplete dla: {keyword}")
                    
                    # DEBUGGING: Loguj surowe dane autocomplete
                    logger.info(f"🔍 SEKCJA 3 DEBUG - autocomplete raw data:")
                    logger.info(f"  intent_analysis type: {type(autocomplete_data.get('intent_analysis'))}")
                    logger.info(f"  intent_analysis (first 200 chars): {str(autocomplete_data.get('intent_analysis'))[:200]}...")
                else:
                    logger.info(f"ℹ️ Brak danych autocomplete dla: {keyword}")
            except Exception as e:
                logger.warning(f"⚠️ Błąd pobierania autocomplete: {str(e)}")
            
            # Pobierz dane historyczne z keyword_historical_data dla SEKCJI 5
            historical_data = []
            try:
                historical_query = supabase.table("keyword_historical_data").select(
                    "year, month, search_volume, cpc, competition, competition_level, "
                    "low_top_of_page_bid, high_top_of_page_bid, categories, created_at"
                ).eq("keyword_id", keyword_id).order("year", desc=True).order("month", desc=True).execute()
                
                if historical_query.data:
                    historical_data = historical_query.data
                    logger.info(f"✅ Pobrano {len(historical_data)} rekordów historycznych dla: {keyword}")
                else:
                    logger.info(f"ℹ️ Brak danych historycznych dla: {keyword}")
            except Exception as e:
                logger.warning(f"⚠️ Błąd pobierania danych historycznych: {str(e)}")
            
            # Pobierz powiązane słowa kluczowe dla SEKCJI 8
            related_keywords_data = []
            try:
                # DIAGNOSTIC: Sprawdź ile relacji mamy w bazie
                count_query = supabase.table("keyword_relations").select("id", count="exact").eq("parent_keyword_id", keyword_id).execute()
                total_relations_count = count_query.count if hasattr(count_query, 'count') else len(count_query.data) if count_query.data else 0
                logger.info(f"🔍 DIAGNOSTIC: Total relations in DB for keyword_id {keyword_id}: {total_relations_count}")
                
                # Query z JOIN do pobrania WSZYSTKICH słów kluczowych z tej samej hierarchii (seed_keyword)
                # Najpierw znajdź wszystkie słowa kluczowe z tym samym seed_keyword
                all_keywords_query = supabase.table("keywords").select("id").eq("seed_keyword", keyword).eq("location_code", location_code).eq("language_code", language_code).execute()
                
                if all_keywords_query.data:
                    all_keyword_ids = [kw["id"] for kw in all_keywords_query.data]
                    logger.info(f"🔍 DIAGNOSTIC: Found {len(all_keyword_ids)} keywords with seed_keyword '{keyword}'")
                    
                    # Pobierz wszystkie relacje dla wszystkich słów z tej hierarchii
                    relations_query = supabase.table("keyword_relations").select(
                        "depth, relationship_type, relevance_score, search_volume, "
                        "keyword_difficulty, related_keyword_id, parent_keyword_id, "
                        "keywords!keyword_relations_related_keyword_id_fkey("
                        "keyword, is_suggestion, cpc, competition, competition_level, "
                        "low_top_of_page_bid, high_top_of_page_bid, main_intent, "
                        "monthly_trend_pct, core_keyword, keyword_difficulty"
                        ")"
                    ).in_("parent_keyword_id", all_keyword_ids).order("depth").order("relevance_score", desc=True).limit(1000).execute()
                else:
                    # Fallback - pobierz tylko bezpośrednie relacje
                    relations_query = supabase.table("keyword_relations").select(
                        "depth, relationship_type, relevance_score, search_volume, "
                        "keyword_difficulty, related_keyword_id, parent_keyword_id, "
                        "keywords!keyword_relations_related_keyword_id_fkey("
                        "keyword, is_suggestion, cpc, competition, competition_level, "
                        "low_top_of_page_bid, high_top_of_page_bid, main_intent, "
                        "monthly_trend_pct, core_keyword, keyword_difficulty"
                        ")"
                    ).eq("parent_keyword_id", keyword_id).order("depth").order("relevance_score", desc=True).limit(1000).execute()
                
                if relations_query.data:
                    related_keywords_data = relations_query.data
                    logger.info(f"✅ Pobrano {len(related_keywords_data)} powiązanych słów kluczowych dla: {keyword}")
                    logger.info(f"🔍 DIAGNOSTIC: Fetched {len(related_keywords_data)} out of {total_relations_count} total relations")
                    
                    # Debug struktury danych
                    for i, relation in enumerate(related_keywords_data[:3]):
                        logger.info(f"🔍 DEBUG relation {i+1}: keys={list(relation.keys())}")
                        if 'keywords' in relation:
                            logger.info(f"🔍 DEBUG relation {i+1} keywords: {list(relation['keywords'].keys()) if relation['keywords'] else 'NULL'}")
                        else:
                            logger.info(f"🔍 DEBUG relation {i+1}: BRAK keywords w relation!")
                else:
                    logger.info(f"ℹ️ Brak powiązanych słów kluczowych dla: {keyword}")
            except Exception as e:
                logger.warning(f"⚠️ Błąd pobierania related keywords: {str(e)}")
                # Fallback - pobierz bez JOIN
                try:
                    simple_relations = supabase.table("keyword_relations").select(
                        "depth, relationship_type, relevance_score, search_volume, keyword_difficulty, related_keyword_id"
                    ).eq("parent_keyword_id", keyword_id).order("depth").order("relevance_score", desc=True).limit(1000).execute()
                    
                    if simple_relations.data:
                        related_keywords_data = simple_relations.data
                        logger.info(f"🔄 Pobrano {len(related_keywords_data)} relacji (bez JOIN) dla: {keyword}")
                except Exception as e2:
                    logger.warning(f"⚠️ Błąd fallback related keywords: {str(e2)}")
            
            # Pobierz dane SERP dla SEKCJI 9
            serp_results_data = None
            serp_items_data = []
            serp_ai_references_data = []
            serp_people_also_ask_data = []
            serp_local_results_data = []
            serp_related_searches_data = []
            
            try:
                # Pobierz główne dane SERP results
                serp_results_query = supabase.table("serp_results").select("*").eq("keyword_id", keyword_id).execute()
                
                if serp_results_query.data:
                    serp_results_data = serp_results_query.data[0]  # Najnowszy wynik
                    serp_result_id = serp_results_data.get("id")
                    logger.info(f"✅ Pobrano dane SERP results dla: {keyword}")
                    
                    # Pobierz SERP items
                    serp_items_query = supabase.table("serp_items").select("*").eq(
                        "serp_result_id", serp_result_id
                    ).order("rank_absolute").execute()
                    
                    if serp_items_query.data:
                        serp_items_data = serp_items_query.data
                        logger.info(f"✅ Pobrano {len(serp_items_data)} SERP items dla: {keyword}")
                        
                        # Pobierz AI references dla każdego AI overview item
                        ai_items = [item for item in serp_items_data if item.get("type") == "ai_overview"]
                        if ai_items:
                            ai_item_ids = [item["id"] for item in ai_items]
                            try:
                                ai_refs_query = supabase.table("serp_ai_references").select("*").in_(
                                    "serp_item_id", ai_item_ids
                                ).execute()
                                if ai_refs_query.data:
                                    serp_ai_references_data = ai_refs_query.data
                                    logger.info(f"✅ Pobrano {len(serp_ai_references_data)} AI references dla: {keyword}")
                            except Exception as e:
                                logger.warning(f"⚠️ Błąd pobierania AI references: {str(e)}")
                    
                    # Pobierz People Also Ask
                    try:
                        paa_query = supabase.table("serp_people_also_ask").select("*").eq(
                            "serp_result_id", serp_result_id
                        ).order("created_at").execute()
                        if paa_query.data:
                            serp_people_also_ask_data = paa_query.data
                            logger.info(f"✅ Pobrano {len(serp_people_also_ask_data)} People Also Ask dla: {keyword}")
                    except Exception as e:
                        logger.warning(f"⚠️ Błąd pobierania People Also Ask: {str(e)}")
                    
                    # Pobierz Local Results
                    try:
                        local_query = supabase.table("serp_local_results").select("*").eq(
                            "serp_result_id", serp_result_id
                        ).order("created_at").execute()
                        if local_query.data:
                            serp_local_results_data = local_query.data
                            logger.info(f"✅ Pobrano {len(serp_local_results_data)} Local Results dla: {keyword}")
                    except Exception as e:
                        logger.warning(f"⚠️ Błąd pobierania Local Results: {str(e)}")
                    
                    # Pobierz Related Searches
                    try:
                        related_searches_query = supabase.table("serp_related_searches").select("*").eq(
                            "serp_result_id", serp_result_id
                        ).order("position").execute()
                        if related_searches_query.data:
                            serp_related_searches_data = related_searches_query.data
                            logger.info(f"✅ Pobrano {len(serp_related_searches_data)} Related Searches dla: {keyword}")
                    except Exception as e:
                        logger.warning(f"⚠️ Błąd pobierania Related Searches: {str(e)}")
                        
                else:
                    logger.info(f"ℹ️ Brak danych SERP results dla: {keyword}")
            except Exception as e:
                logger.warning(f"⚠️ Błąd pobierania danych SERP: {str(e)}")
            
            # Pobierz dane AUTOCOMPLETE dla SEKCJI 10
            complete_autocomplete_results_data = None
            autocomplete_suggestions_data = []
            
            try:
                # Pobierz główne dane autocomplete results
                autocomplete_results_query = supabase.table("autocomplete_results").select("*").eq("keyword_id", keyword_id).execute()
                
                if autocomplete_results_query.data:
                    complete_autocomplete_results_data = autocomplete_results_query.data[0]  # Najnowszy wynik
                    autocomplete_result_id = complete_autocomplete_results_data.get("id")
                    logger.info(f"✅ Pobrano dane autocomplete results dla: {keyword}")
                    
                    # Pobierz autocomplete suggestions
                    autocomplete_suggestions_query = supabase.table("autocomplete_suggestions").select("*").eq(
                        "autocomplete_result_id", autocomplete_result_id
                    ).order("rank_absolute").execute()
                    
                    if autocomplete_suggestions_query.data:
                        autocomplete_suggestions_data = autocomplete_suggestions_query.data
                        logger.info(f"✅ Pobrano {len(autocomplete_suggestions_data)} autocomplete suggestions dla: {keyword}")
                        
                else:
                    logger.info(f"ℹ️ Brak danych autocomplete results dla: {keyword}")
            except Exception as e:
                logger.warning(f"⚠️ Błąd pobierania danych autocomplete: {str(e)}")
            
            # Formatuj dane zgodnie ze schematem SEKCJI 1 + SEKCJI 2 + SEKCJI 3 + SEKCJI 4 + SEKCJI 5 + SEKCJI 6 + SEKCJI 7 + SEKCJI 8 + SEKCJI 9 + SEKCJI 10
            result = {
                # SEKCJA 1: EXTENDED HEADER
                "keyword_name": keyword_data.get("keyword"),
                "location_code": keyword_data.get("location_code"),
                "language_code": keyword_data.get("language_code"),
                "seed_keyword": keyword_data.get("seed_keyword"),
                "depth": keyword_data.get("depth"),
                "is_suggestion": keyword_data.get("is_suggestion", False),
                "detected_language": keyword_data.get("detected_language"),
                "is_another_language": keyword_data.get("is_another_language", False),
                "core_keyword": keyword_data.get("core_keyword"),
                "synonym_clustering_algorithm": keyword_data.get("synonym_clustering_algorithm"),
                "categories": keyword_data.get("categories", []),
                "last_updated": keyword_data.get("last_updated"),
                "api_costs_total": keyword_data.get("api_costs_total", 0.0),
                "data_sources": keyword_data.get("data_sources", []),
                
                # SEKCJA 2: EXTENDED CORE SEO METRICS
                "search_volume": keyword_data.get("search_volume"),
                "traffic_potential": keyword_data.get("traffic_potential"),
                "keyword_difficulty": keyword_data.get("keyword_difficulty"),
                "cpc": keyword_data.get("cpc"),
                "competition": keyword_data.get("competition"),
                "competition_level": keyword_data.get("competition_level"),
                "low_top_of_page_bid": keyword_data.get("low_top_of_page_bid"),
                "high_top_of_page_bid": keyword_data.get("high_top_of_page_bid"),
                "monthly_trend_pct": keyword_data.get("monthly_trend_pct"),
                "quarterly_trend_pct": keyword_data.get("quarterly_trend_pct"),
                "yearly_trend_pct": keyword_data.get("yearly_trend_pct"),
                
                # SEKCJA 3: COMPLETE INTENT ANALYSIS - Keywords table
                "main_intent": keyword_data.get("main_intent"),
                "intent_probability": keyword_data.get("intent_probability"),
                "secondary_intents": keyword_data.get("secondary_intents"),
                
                # SEKCJA 3: COMPLETE INTENT ANALYSIS - Autocomplete table
                "autocomplete_intent_analysis": None,
                "autocomplete_trending_modifiers": None,
                "autocomplete_content_opportunities": None,
                
                # SEKCJA 4: COMPLETE DEMOGRAPHICS
                "gender_female": keyword_data.get("gender_female"),
                "gender_male": keyword_data.get("gender_male"),
                "age_18_24": keyword_data.get("age_18_24"),
                "age_25_34": keyword_data.get("age_25_34"),
                "age_35_44": keyword_data.get("age_35_44"),
                "age_45_54": keyword_data.get("age_45_54"),
                "age_55_64": keyword_data.get("age_55_64"),
                
                # SEKCJA 5: EXTENDED TRENDS & SEASONALITY
                "monthly_searches": keyword_data.get("monthly_searches"),
                "search_volume_trend": keyword_data.get("search_volume_trend"),
                "trends_graph": keyword_data.get("trends_graph"),
                "historical_data": historical_data,
                
                # SEKCJA 6: COMPLETE GEOGRAPHIC DATA
                "subregion_interests": keyword_data.get("subregion_interests"),
                "trends_map": keyword_data.get("trends_map"),
                
                # SEKCJA 7: ENHANCED COMPETITION ANALYSIS
                "serp_info": keyword_data.get("serp_info"),
                "backlinks_info": keyword_data.get("backlinks_info"),
                
                # SEKCJA 8: ENHANCED RELATED KEYWORDS WITH HIERARCHY
                "related_keywords": related_keywords_data,
                "hierarchy": keyword_data.get("hierarchy"),
                "topics_list": keyword_data.get("topics_list"),
                "queries_list": keyword_data.get("queries_list"),
                
                # SEKCJA 9: ENHANCED SERP ANALYSIS
                "serp_results": serp_results_data,
                "serp_items": serp_items_data,
                "serp_ai_references": serp_ai_references_data,
                "serp_people_also_ask": serp_people_also_ask_data,
                "serp_local_results": serp_local_results_data,
                "serp_related_searches": serp_related_searches_data,
                
                # SEKCJA 10: ENHANCED AUTOCOMPLETE ANALYSIS
                "autocomplete_results": complete_autocomplete_results_data,
                "autocomplete_suggestions": autocomplete_suggestions_data
            }
            
            # Dodaj dane autocomplete jeśli dostępne
            if autocomplete_data:
                # Bezpieczne parsowanie JSONB z podwójnym escapowaniem
                intent_analysis_raw = autocomplete_data.get("intent_analysis")
                if intent_analysis_raw:
                    try:
                        # Jeśli to string z podwójnymi cudzysłowami, najpierw go parsuj
                        if isinstance(intent_analysis_raw, str):
                            # Usuń zewnętrzne potrójne cudzysłowy jeśli są
                            cleaned = intent_analysis_raw.strip('"""')
                            result["autocomplete_intent_analysis"] = json.loads(cleaned)
                        else:
                            result["autocomplete_intent_analysis"] = intent_analysis_raw
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ Błąd parsowania intent_analysis: {str(e)}")
                        result["autocomplete_intent_analysis"] = intent_analysis_raw
                else:
                    result["autocomplete_intent_analysis"] = None
                    
                # Podobnie dla innych pól JSONB
                trending_modifiers_raw = autocomplete_data.get("trending_modifiers")
                if trending_modifiers_raw:
                    try:
                        if isinstance(trending_modifiers_raw, str):
                            cleaned = trending_modifiers_raw.strip('"""')
                            result["autocomplete_trending_modifiers"] = json.loads(cleaned)
                        else:
                            result["autocomplete_trending_modifiers"] = trending_modifiers_raw
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ Błąd parsowania trending_modifiers: {str(e)}")
                        result["autocomplete_trending_modifiers"] = trending_modifiers_raw
                else:
                    result["autocomplete_trending_modifiers"] = None
                    
                content_opportunities_raw = autocomplete_data.get("content_opportunities")
                if content_opportunities_raw:
                    try:
                        if isinstance(content_opportunities_raw, str):
                            cleaned = content_opportunities_raw.strip('"""')
                            result["autocomplete_content_opportunities"] = json.loads(cleaned)
                        else:
                            result["autocomplete_content_opportunities"] = content_opportunities_raw
                    except json.JSONDecodeError as e:
                        logger.warning(f"⚠️ Błąd parsowania content_opportunities: {str(e)}")
                        result["autocomplete_content_opportunities"] = content_opportunities_raw
                else:
                    result["autocomplete_content_opportunities"] = None
            
            logger.info(f"✅ Pobrano complete data dla: {keyword}")
            return result
            
        except Exception as e:
            logger.exception(f"❌ Błąd pobierania header data: {str(e)}")
            raise

# ========================================
# SINGLETON INSTANCE
# ========================================
orchestrator = SEOAnalysisOrchestrator()