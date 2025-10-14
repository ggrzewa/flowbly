import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from dataforseo_client import configuration as dfs_config, api_client as dfs_api_provider
from dataforseo_client.api.serp_api import SerpApi
from dataforseo_client.models.serp_google_autocomplete_live_advanced_request_info import (
    SerpGoogleAutocompleteLiveAdvancedRequestInfo,
)
from supabase import create_client, Client
import json
import re
from collections import Counter

# ========================================
# ENVIRONMENT SETUP
# ========================================
load_dotenv()
router = APIRouter()

# Logger setup
logger = logging.getLogger("autocomplete_parser_complete")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Configuration
DFS_LOGIN = os.getenv("DATAFORSEO_LOGIN")
DFS_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================================
# INPUT MODELS
# ========================================
class AutocompleteInput(BaseModel):
    keyword: str
    location_code: Optional[int] = 2616  # Poland
    language_code: Optional[str] = "pl"
    cursor_pointer: Optional[int] = None
    client: Optional[str] = "gws-wiz-serp"
    include_analysis: Optional[bool] = True

# ========================================
# PARSING FUNCTIONS
# ========================================
class AutocompleteDataParser:
    
    @staticmethod
    def validate_integer_field(value, field_name, default=None):
        """Validate and convert integer fields, handle None/string 'None' cases"""
        if value is None:
            return default
        if isinstance(value, str):
            if value.lower() in ['none', 'null', '']:
                return default
            try:
                return int(value)
            except ValueError:
                logger.warning(f"Cannot convert {field_name} '{value}' to integer, using default: {default}")
                return default
        if isinstance(value, (int, float)):
            return int(value)
        return default
    
    @staticmethod
    def parse_execution_time(time_string: str) -> float:
        """Parse execution time like '3.7924 sec.' -> 3.7924"""
        if not time_string:
            return 0.0
        try:
            return float(time_string.replace(' sec.', '').replace(',', '.'))
        except:
            return 0.0

    @staticmethod
    def calculate_freshness_hours(datetime_str: str) -> int:
        """Calculate hours since autocomplete data was retrieved"""
        try:
            autocomplete_date = datetime.fromisoformat(datetime_str.replace(' +00:00', ''))
            now = datetime.utcnow()
            return int((now - autocomplete_date).total_seconds() / 3600)
        except:
            return 0

    @staticmethod
    async def lookup_keyword_id(keyword: str, location_code: int, language_code: str) -> str:
        """Find or create keyword ID in keywords table"""
        try:
            # Validate input parameters
            location_code = AutocompleteDataParser.validate_integer_field(location_code, "location_code", 2616)
            
            # Try to find existing keyword
            existing = supabase.table("keywords").select("id").eq("keyword", keyword).eq("location_code", location_code).eq("language_code", language_code).execute()
            
            if existing.data:
                return existing.data[0]["id"]
            
            # Create new keyword record
            keyword_record = {
                "keyword": keyword,
                "location_code": location_code,
                "language_code": language_code,
                "seed_keyword": keyword,
                "is_suggestion": False,
                "data_sources": ["autocomplete"],
                "last_updated": datetime.utcnow().isoformat()
            }
            
            result = supabase.table("keywords").insert(keyword_record).execute()
            logger.info(f"✅ Created new keyword: {keyword}")
            return result.data[0]["id"]
            
        except Exception as e:
            logger.error(f"❌ Error looking up keyword: {str(e)}")
            raise

    @staticmethod
    def analyze_keyword_intent(suggestions: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Analyze search intent based on autocomplete suggestions"""
        # Polish intent patterns
        INTENT_PATTERNS = {
            "informational": [
                r"\b(jak|co|dlaczego|kiedy|gdzie|czy|jakie|jakich|czym|kim)\b",
                r"\b(znaczenie|definicja|wyjaśnienie|opis|instrukcja)\b",
                r"\b(zasady|reguły|poradnik|tutorial|nauka)\b",
                r"\b(historia|pochodzenie|przyczyny)\b"
            ],
            "transactional": [
                r"\b(kup|kupić|sklep|cena|koszt|tanio|promocja|rabat)\b",
                r"\b(książka|podręcznik|zestaw|materiały|produkt)\b",
                r"\b(zamów|zamówienie|dostawa|sprzedaż|online)\b",
                r"\b(allegro|empik|ceneo|sklep)\b"
            ],
            "navigational": [
                r"\b(strona|portal|serwis|oficjalna|www)\b",
                r"\.(pl|com|org|net|edu)\b",
                r"\b(logowanie|login|konto|rejestracja)\b",
                r"\b(facebook|youtube|instagram|twitter)\b"
            ],
            "local": [
                r"\b(w|warszawa|kraków|gdańsk|poznań|wrocław|łódź)\b",
                r"\b(blisko|obok|okolica|region|miasto)\b",
                r"\b(adres|telefon|godziny|otwarcie)\b"
            ],
            "educational": [
                r"\b(klasa|szkoła|uczniów|nauczyciel|edukacja)\b",
                r"\b(ćwiczenia|zadania|test|sprawdzian|egzamin)\b",
                r"\b(nauka|learning|kurs|lekcja)\b"
            ]
        }
        
        intent_counts = {intent: 0 for intent in INTENT_PATTERNS.keys()}
        categorized_suggestions = {intent: [] for intent in INTENT_PATTERNS.keys()}
        
        for suggestion in suggestions:
            text = suggestion.get("suggestion", "").lower()
            
            for intent, patterns in INTENT_PATTERNS.items():
                for pattern in patterns:
                    if re.search(pattern, text, re.IGNORECASE):
                        intent_counts[intent] += 1
                        categorized_suggestions[intent].append(suggestion.get("suggestion"))
                        break
        
        total = sum(intent_counts.values())
        intent_distribution = {}
        
        if total > 0:
            intent_distribution = {
                intent: round((count / total) * 100, 1) 
                for intent, count in intent_counts.items()
                if count > 0
            }
        
        return {
            "intent_distribution": intent_distribution,
            "categorized_suggestions": categorized_suggestions,
            "total_analyzed": len(suggestions),
            "primary_intent": max(intent_distribution.items(), key=lambda x: x[1])[0] if intent_distribution else "unknown"
        }

    @staticmethod
    def extract_trending_modifiers(suggestions: List[Dict[str, Any]], base_keyword: str) -> Dict[str, Any]:
        """Extract trending modifiers and patterns from suggestions"""
        all_suggestions = [s.get("suggestion", "") for s in suggestions]
        all_text = " ".join(all_suggestions).lower()
        
        # Extract words, remove base keyword
        words = re.findall(r'\b\w+\b', all_text)
        base_words = set(base_keyword.lower().split())
        filtered_words = [w for w in words if w not in base_words and len(w) > 2]
        
        # Count frequency
        word_freq = Counter(filtered_words)
        
        # Modifier categories
        MODIFIER_CATEGORIES = {
            "format": ["online", "pdf", "interaktywne", "audio", "wideo", "app", "aplikacja"],
            "target": ["dzieci", "dorosłych", "klasa", "szkoła", "uczniów", "nauczyciel"],
            "difficulty": ["łatwe", "trudne", "krótkie", "długie", "podstawowe", "zaawansowane"],
            "topic": ["ortografia", "gramatyka", "interpunkcja", "pisownia", "język"],
            "commercial": ["cena", "sklep", "książka", "materiały", "zestaw", "tanio"],
            "time": ["nowe", "2024", "2025", "aktualne", "najnowsze"]
        }
        
        detected_modifiers = {}
        for category, keywords in MODIFIER_CATEGORIES.items():
            detected = [(word, word_freq[word]) for word in word_freq.keys() if word in keywords]
            if detected:
                detected_modifiers[category] = sorted(detected, key=lambda x: x[1], reverse=True)
        
        return {
            "top_modifiers": dict(word_freq.most_common(15)),
            "categorized_modifiers": detected_modifiers,
            "long_tail_opportunities": [s for s in all_suggestions if len(s.split()) >= 4],
            "question_patterns": [s for s in all_suggestions if any(q in s.lower() for q in ["jak", "co", "dlaczego", "kiedy", "gdzie", "czy"])]
        }

    @staticmethod
    def identify_content_opportunities(suggestions: List[Dict[str, Any]], base_keyword: str) -> List[Dict[str, Any]]:
        """Identify content marketing opportunities based on suggestions"""
        opportunities = []
        
        # Analyze long phrases (long-tail keywords)
        for suggestion in suggestions:
            text = suggestion.get("suggestion", "")
            rank = suggestion.get("rank_absolute", 999)
            
            if len(text.split()) >= 3:
                difficulty = "Easy" if rank > 7 else "Medium" if rank > 4 else "Hard"
                
                opportunity = {
                    "keyword": text,
                    "rank": rank,
                    "opportunity_type": "long_tail",
                    "difficulty": difficulty,
                    "reason": f"Długa fraza ({len(text.split())} słów) - potencjalnie mniejsza konkurencja",
                    "word_count": len(text.split())
                }
                opportunities.append(opportunity)
        
        # Search for unique angles/modifiers
        all_suggestions = [s.get("suggestion", "") for s in suggestions]
        for suggestion_data in suggestions:
            text = suggestion_data.get("suggestion", "")
            words = text.lower().split()
            
            # Find unique modifiers
            unique_words = []
            for word in words:
                if len(word) > 3 and sum(1 for s in all_suggestions if word in s.lower()) == 1:
                    unique_words.append(word)
            
            if unique_words:
                opportunity = {
                    "keyword": text,
                    "rank": suggestion_data.get("rank_absolute", 999),
                    "opportunity_type": "unique_angle", 
                    "unique_modifiers": unique_words,
                    "reason": f"Zawiera unikalne modyfikatory: {', '.join(unique_words)}"
                }
                opportunities.append(opportunity)
        
        return sorted(opportunities, key=lambda x: x.get("rank", 999))[:10]

# ========================================
# MAIN AUTOCOMPLETE PROCESSOR
# ========================================
class AutocompleteProcessor:
    
    def __init__(self):
        self.parser = AutocompleteDataParser()
    
    async def process_autocomplete_response(self, autocomplete_response: Dict, input_data: AutocompleteInput) -> Dict:
        """Process complete autocomplete response and save to database"""
        try:
            result = autocomplete_response["result"]
            task_info = autocomplete_response["task_info"]
            
            logger.info(f"🔄 Processing autocomplete for keyword: {result['keyword']}")
            logger.info(f"📊 Autocomplete zawiera typy: {result.get('item_types', [])}")
            logger.info(f"📊 Sugestie do przetworzenia: {len(result.get('items', []))}")
            
            # 1. LOOKUP/CREATE keyword_id
            keyword_id = await self.parser.lookup_keyword_id(
                result["keyword"], 
                result["location_code"], 
                result["language_code"]
            )
            
            # 2. INSERT/UPDATE autocomplete_results
            autocomplete_result_id = await self.insert_autocomplete_result(result, task_info, keyword_id, input_data, autocomplete_response.get("business_intelligence"))
            
            # 3. PROCESS all suggestions
            suggestions_processed = 0
            for item in result.get("items", []):
                try:
                    await self.process_suggestion(item, autocomplete_result_id, autocomplete_response.get("business_intelligence"))
                    suggestions_processed += 1
                except Exception as e:
                    logger.warning(f"⚠️ Error processing suggestion: {str(e)}")
                    continue
            
            logger.info(f"✅ Processed {suggestions_processed}/{len(result.get('items', []))} autocomplete suggestions")
            
            return {
                "success": True,
                "autocomplete_result_id": autocomplete_result_id,
                "keyword": result["keyword"],
                "suggestions_processed": suggestions_processed,
                "total_suggestions": len(result.get("items", [])),
                "cost_usd": task_info.get("cost", 0)
            }
            
        except Exception as e:
            logger.exception(f"❌ Error processing autocomplete response: {str(e)}")
            raise

    async def insert_autocomplete_result(self, result: Dict, task_info: Dict, keyword_id: str, input_data: AutocompleteInput, business_intelligence: Dict = None) -> str:
        """Insert main autocomplete result record"""
        try:
            # Validate integer fields before database insertion
            validated_location_code = self.parser.validate_integer_field(result.get("location_code"), "location_code", 2616)
            validated_cursor_pointer = self.parser.validate_integer_field(input_data.cursor_pointer, "cursor_pointer", None)
            validated_se_results_count = self.parser.validate_integer_field(result.get("se_results_count"), "se_results_count", 0)
            validated_items_count = self.parser.validate_integer_field(result.get("items_count"), "items_count", 0)
            
            logger.debug(f"🔄 Inserting autocomplete with validated fields: keyword_id={keyword_id}, location_code={validated_location_code}, cursor_pointer={validated_cursor_pointer}")
            
            autocomplete_record = {
                "keyword_id": keyword_id,
                "keyword": result["keyword"],
                "location_code": validated_location_code,
                "language_code": result["language_code"],
                "se_domain": result["se_domain"],
                "cursor_pointer": validated_cursor_pointer,
                "client": input_data.client,
                "check_url": result["check_url"],
                "datetime": result["datetime"],
                "se_results_count": validated_se_results_count,
                "items_count": validated_items_count,
                "item_types": result.get("item_types", []),
                "spell_correction": json.dumps(result.get("spell")) if result.get("spell") else None,
                "refinement_chips": json.dumps(result.get("refinement_chips")) if result.get("refinement_chips") else None,
                "api_cost": task_info.get("cost", 0),
                "execution_time": self.parser.parse_execution_time(task_info.get("execution_time", "")),
                "data_freshness_hours": self.parser.calculate_freshness_hours(result["datetime"])
            }
            
            # Add business intelligence data if available
            if business_intelligence:
                autocomplete_record.update({
                    "intent_analysis": json.dumps(business_intelligence.get("intent_analysis")),
                    "trending_modifiers": json.dumps(business_intelligence.get("trending_modifiers")),
                    "content_opportunities": json.dumps(business_intelligence.get("content_opportunities")),
                    "analysis_metrics": json.dumps(business_intelligence.get("metrics")),
                    "analysis_summary": json.dumps(business_intelligence.get("summary"))
                })
            
            # Check for existing autocomplete result (unique constraint) - with proper None handling
            existing_query = supabase.table("autocomplete_results").select("id").eq("keyword_id", keyword_id).eq("location_code", validated_location_code).eq("language_code", result["language_code"]).eq("client", input_data.client)
            
            # Add cursor_pointer condition only if it's not None
            if validated_cursor_pointer is not None:
                existing_query = existing_query.eq("cursor_pointer", validated_cursor_pointer)
            else:
                existing_query = existing_query.is_("cursor_pointer", None)
            
            existing = existing_query.execute()
            
            if existing.data:
                # Update existing
                autocomplete_result_id = existing.data[0]["id"]
                autocomplete_record["updated_at"] = datetime.utcnow().isoformat()
                supabase.table("autocomplete_results").update(autocomplete_record).eq("id", autocomplete_result_id).execute()
                logger.info(f"🔄 Updated existing autocomplete result: {autocomplete_result_id}")
            else:
                # Insert new
                autocomplete_record["created_at"] = datetime.utcnow().isoformat()
                result_insert = supabase.table("autocomplete_results").insert(autocomplete_record).execute()
                autocomplete_result_id = result_insert.data[0]["id"]
                logger.info(f"✅ Created new autocomplete result: {autocomplete_result_id}")
            
            return autocomplete_result_id
            
        except Exception as e:
            logger.error(f"❌ Error inserting autocomplete result: {str(e)}")
            logger.error(f"🔍 Debug info - keyword_id: {keyword_id}, input_data.cursor_pointer: {input_data.cursor_pointer} (type: {type(input_data.cursor_pointer)})")
            raise

    async def process_suggestion(self, item: Dict, autocomplete_result_id: str, business_intelligence: Dict = None) -> str:
        """Process individual autocomplete suggestion"""
        try:
            logger.debug(f"🔄 Processing suggestion: {item.get('suggestion', 'No text')[:50]} (rank {item.get('rank_absolute', 'N/A')})")
            
            # Insert basic autocomplete_suggestion
            suggestion_id = await self.insert_autocomplete_suggestion(item, autocomplete_result_id, business_intelligence)
            
            return suggestion_id
            
        except Exception as e:
            logger.error(f"❌ Error processing suggestion: {str(e)}")
            raise

    async def insert_autocomplete_suggestion(self, item: Dict, autocomplete_result_id: str, business_intelligence: Dict = None) -> str:
        """Insert autocomplete suggestion"""
        try:
            # Validate integer fields
            validated_rank_group = self.parser.validate_integer_field(item.get("rank_group"), "rank_group", None)
            validated_rank_absolute = self.parser.validate_integer_field(item.get("rank_absolute"), "rank_absolute", None)
            validated_relevance = self.parser.validate_integer_field(item.get("relevance"), "relevance", None)
            validated_word_count = len(item.get("suggestion", "").split()) if item.get("suggestion") else 0
            
            suggestion_record = {
                "autocomplete_result_id": autocomplete_result_id,
                "type": item.get("type", "autocomplete"),
                "rank_group": validated_rank_group,
                "rank_absolute": validated_rank_absolute,
                "suggestion": item.get("suggestion"),
                "suggestion_type": item.get("suggestion_type"),
                "relevance": validated_relevance,
                "search_query_url": item.get("search_query_url"),
                "thumbnail_url": item.get("thumbnail_url"),
                "highlighted": json.dumps(item.get("highlighted"), ensure_ascii=False) if item.get("highlighted") else None,
                "word_count": validated_word_count
            }
            
            # Match with business intelligence data
            intent_category = None
            opportunity_data = None
            if business_intelligence:
                suggestion_text = item.get("suggestion", "")
                
                # Match intent category
                intent_category = self.match_intent_category(suggestion_text, business_intelligence.get("intent_analysis", {}))
                if intent_category:
                    suggestion_record["intent_category"] = intent_category
                
                # Match content opportunity
                opportunity_data = self.match_content_opportunity(suggestion_text, business_intelligence.get("content_opportunities", []))
                if opportunity_data:
                    suggestion_record.update({
                        "opportunity_type": opportunity_data.get("opportunity_type"),
                        "difficulty_level": opportunity_data.get("difficulty"),
                        "analysis_reason": opportunity_data.get("reason"),
                        "unique_modifiers": json.dumps(opportunity_data.get("unique_modifiers", []))
                    })
            
            # Debug logging
            logger.debug(f"🔄 Processing suggestion: '{item.get('suggestion')}' - intent: {intent_category}, opportunity: {opportunity_data}, rank: {validated_rank_absolute}")
            
            # Insert to database
            result = supabase.table("autocomplete_suggestions").insert(suggestion_record).execute()
            suggestion_id = result.data[0]["id"]
            
            logger.debug(f"✅ Created autocomplete suggestion: {item.get('suggestion', 'No text')[:50]}")
            return suggestion_id
            
        except Exception as e:
            logger.error(f"❌ Error inserting autocomplete suggestion: {str(e)}")
            logger.error(f"🔍 Debug info - item keys: {list(item.keys()) if item else 'None'}")
            raise

    def match_intent_category(self, suggestion: str, intent_analysis: Dict) -> Optional[str]:
        """Match suggestion with intent category from business intelligence"""
        categorized_suggestions = intent_analysis.get("categorized_suggestions", {})
        
        for category, suggestions in categorized_suggestions.items():
            if suggestion in suggestions:
                logger.debug(f"✅ Matched '{suggestion}' → {category}")
                return category
        
        logger.debug(f"❌ No intent match for: '{suggestion}'")
        return None

    def match_content_opportunity(self, suggestion: str, content_opportunities: List[Dict]) -> Optional[Dict]:
        """Match suggestion with content opportunity from business intelligence"""
        for opportunity in content_opportunities:
            if opportunity.get("keyword") == suggestion:
                logger.debug(f"✅ Matched opportunity '{suggestion}' → {opportunity.get('opportunity_type')}")
                return opportunity
        
        logger.debug(f"❌ No opportunity match for: '{suggestion}'")
        return None

# ========================================
# API ENDPOINTS
# ========================================
@router.post("/autocomplete/google/live/advanced/with-database")
async def get_autocomplete_and_save_to_database(data: AutocompleteInput):
    """
    Pobiera dane Autocomplete i zapisuje je do bazy danych zgodnie z mapowaniem.
    """
    if not all([DFS_LOGIN, DFS_PASSWORD, SUPABASE_URL, SUPABASE_KEY]):
        raise HTTPException(status_code=500, detail="Missing API credentials")
    
    # Debug logging dla input data
    logger.info(f"🔄 Processing autocomplete with database save for: {data.keyword}")
    logger.debug(f"🔍 Input data: keyword={data.keyword}, location_code={data.location_code}, language_code={data.language_code}, cursor_pointer={data.cursor_pointer} (type: {type(data.cursor_pointer)}), client={data.client}")
    
    config = dfs_config.Configuration(username=DFS_LOGIN, password=DFS_PASSWORD)
    
    # Prepare request - with validation
    validated_cursor_pointer = AutocompleteDataParser.validate_integer_field(data.cursor_pointer, "cursor_pointer", None)
    logger.debug(f"🔍 Validated cursor_pointer: {validated_cursor_pointer} (type: {type(validated_cursor_pointer)})")
    
    request_params = {
        "keyword": data.keyword,
        "location_code": data.location_code,
        "language_code": data.language_code,
        "client": data.client
    }
    
    if validated_cursor_pointer is not None:
        request_params["cursor_pointer"] = validated_cursor_pointer
        logger.debug(f"🔍 Added cursor_pointer to request: {validated_cursor_pointer}")
    
    request_data = [SerpGoogleAutocompleteLiveAdvancedRequestInfo(**request_params)]
    
    try:
        # 1. Call DataForSEO API  
        with dfs_api_provider.ApiClient(config) as api_client:
            api_instance = SerpApi(api_client)
            api_response = api_instance.google_autocomplete_live_advanced(request_data)
            
            if not api_response.tasks or api_response.tasks[0].status_code != 20000:
                raise HTTPException(status_code=400, detail="DataForSEO API error")
            
            task = api_response.tasks[0]
            if not task.result:
                raise HTTPException(status_code=404, detail="No autocomplete data found")
        
        # 2. Process and add business intelligence if requested
        autocomplete_response = {
            "task_info": {
                "id": task.id,
                "status_code": task.status_code,
                "status_message": task.status_message,
                "cost": task.cost,
                "execution_time": task.time
            },
            "result": task.result[0].to_dict()
        }
        
        # Add business intelligence analysis if requested
        if data.include_analysis and task.result[0].items:
            logger.info("🧠 Generating business intelligence analysis...")
            
            # Convert items to list of dicts for analysis
            suggestions = []
            for item in task.result[0].items:
                suggestions.append(item.to_dict())
            
            # Generate analysis
            parser = AutocompleteDataParser()
            intent_analysis = parser.analyze_keyword_intent(suggestions)
            trending_modifiers = parser.extract_trending_modifiers(suggestions, data.keyword)
            content_opportunities = parser.identify_content_opportunities(suggestions, data.keyword)
            
            autocomplete_response["business_intelligence"] = {
                "intent_analysis": intent_analysis,
                "trending_modifiers": trending_modifiers,
                "content_opportunities": content_opportunities,
                "metrics": {
                    "total_suggestions": len(suggestions),
                    "average_suggestion_length": sum(len(s.get("suggestion", "").split()) for s in suggestions) / len(suggestions) if suggestions else 0,
                    "primary_intent": intent_analysis.get("primary_intent", "unknown"),
                    "top_modifier": list(trending_modifiers["top_modifiers"].keys())[0] if trending_modifiers["top_modifiers"] else None,
                    "opportunity_count": len(content_opportunities)
                },
                "summary": {
                    "recommendation": f"Focus on {intent_analysis.get('primary_intent', 'mixed')} intent content",
                    "key_insights": [f"Primary intent: {intent_analysis.get('primary_intent', 'unknown')}"]
                }
            }
        
        # 3. Process and save to database
        processor = AutocompleteProcessor()
        result = await processor.process_autocomplete_response(autocomplete_response, data)
        
        # 4. Return success response
        return {
            "success": True,
            "message": "Autocomplete data successfully saved to database",
            "api_response": {
                "keyword": data.keyword,
                "autocomplete_result_id": result["autocomplete_result_id"],
                "suggestions_processed": result["suggestions_processed"],
                "total_suggestions": result["total_suggestions"],
                "cost_usd": result["cost_usd"]
            },
            "raw_api_response": autocomplete_response  # For debugging
        }
        
    except Exception as e:
        logger.exception(f"❌ Error processing autocomplete: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Processing failed: {str(e)}")

@router.get("/autocomplete/database-stats")
async def get_autocomplete_database_stats():
    """
    Pokaż statystyki danych autocomplete w bazie danych
    """
    try:
        # Count records in each table
        autocomplete_results = supabase.table("autocomplete_results").select("id", count="exact").execute()
        autocomplete_suggestions = supabase.table("autocomplete_suggestions").select("id", count="exact").execute()
        
        # Get recent autocomplete results
        recent_results = supabase.table("autocomplete_results").select("keyword, datetime, items_count, api_cost").order("created_at", desc=True).limit(10).execute()
        
        # Calculate total API costs
        total_costs = supabase.table("autocomplete_results").select("api_cost").execute()
        total_cost = sum(float(record.get("api_cost", 0) or 0) for record in total_costs.data)
        
        # Get client distribution
        client_stats = supabase.table("autocomplete_results").select("client", count="exact").execute()
        
        return {
            "database_stats": {
                "autocomplete_results": autocomplete_results.count,
                "autocomplete_suggestions": autocomplete_suggestions.count
            },
            "recent_results": recent_results.data,
            "total_api_cost_usd": round(total_cost, 4),
            "clients_used": {}  # Would need GROUP BY query for this
        }
        
    except Exception as e:
        logger.exception(f"❌ Error getting database stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@router.get("/autocomplete/keyword/{keyword}/complete")
async def get_complete_autocomplete_data(keyword: str, location_code: int = 2616, language_code: str = "pl"):
    """
    Pobierz kompletne dane autocomplete dla słowa kluczowego ze wszystkich tabel
    """
    try:
        # Find autocomplete result
        autocomplete_result = supabase.table("autocomplete_results").select("*").eq("keyword", keyword).eq("location_code", location_code).eq("language_code", language_code).execute()
        
        if not autocomplete_result.data:
            raise HTTPException(status_code=404, detail=f"No autocomplete data found for keyword: {keyword}")
        
        autocomplete_data = autocomplete_result.data[0]
        autocomplete_result_id = autocomplete_data["id"]
        
        # Get all suggestions
        suggestions = supabase.table("autocomplete_suggestions").select("*").eq("autocomplete_result_id", autocomplete_result_id).order("rank_absolute").execute()
        
        # Organize suggestions by intent
        suggestions_by_intent = {}
        for suggestion in suggestions.data:
            intent = suggestion.get("intent_category", "unknown")
            if intent not in suggestions_by_intent:
                suggestions_by_intent[intent] = []
            suggestions_by_intent[intent].append(suggestion)
        
        # Organize suggestions by opportunity type
        suggestions_by_opportunity = {}
        for suggestion in suggestions.data:
            opp_type = suggestion.get("opportunity_type", "none")
            if opp_type not in suggestions_by_opportunity:
                suggestions_by_opportunity[opp_type] = []
            suggestions_by_opportunity[opp_type].append(suggestion)
        
        return {
            "success": True,
            "keyword": keyword,
            "autocomplete_metadata": {
                "autocomplete_result_id": autocomplete_result_id,
                "datetime": autocomplete_data["datetime"],
                "se_domain": autocomplete_data["se_domain"],
                "client": autocomplete_data["client"],
                "cursor_pointer": autocomplete_data["cursor_pointer"],
                "items_count": autocomplete_data["items_count"],
                "api_cost": autocomplete_data["api_cost"],
                "check_url": autocomplete_data["check_url"]
            },
            "suggestions": {
                "by_intent": suggestions_by_intent,
                "by_opportunity": suggestions_by_opportunity,
                "all_suggestions": suggestions.data,
                "total_count": len(suggestions.data)
            },
            "business_intelligence": {
                "intent_analysis": json.loads(autocomplete_data["intent_analysis"]) if autocomplete_data.get("intent_analysis") else None,
                "trending_modifiers": json.loads(autocomplete_data["trending_modifiers"]) if autocomplete_data.get("trending_modifiers") else None,
                "content_opportunities": json.loads(autocomplete_data["content_opportunities"]) if autocomplete_data.get("content_opportunities") else None,
                "analysis_metrics": json.loads(autocomplete_data["analysis_metrics"]) if autocomplete_data.get("analysis_metrics") else None,
                "analysis_summary": json.loads(autocomplete_data["analysis_summary"]) if autocomplete_data.get("analysis_summary") else None
            },
            "statistics": {
                "total_suggestions": len(suggestions.data),
                "intents_found": len(suggestions_by_intent),
                "opportunities_found": len([s for s in suggestions.data if s.get("opportunity_type")]),
                "avg_word_count": sum(s.get("word_count", 0) for s in suggestions.data) / len(suggestions.data) if suggestions.data else 0,
                "long_tail_count": len([s for s in suggestions.data if s.get("word_count", 0) >= 4])
            }
        }
        
    except Exception as e:
        logger.exception(f"❌ Error getting complete autocomplete data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching autocomplete data: {str(e)}")

@router.get("/autocomplete/analyze/{keyword}")
async def analyze_autocomplete_performance(keyword: str, location_code: int = 2616, language_code: str = "pl"):
    """
    Analiza wydajności autocomplete - intencje, modyfikatory, okazje content'owe
    """
    try:
        # Get autocomplete data
        autocomplete_result = supabase.table("autocomplete_results").select("*").eq("keyword", keyword).eq("location_code", location_code).eq("language_code", language_code).execute()
        
        if not autocomplete_result.data:
            raise HTTPException(status_code=404, detail=f"No autocomplete data found for keyword: {keyword}")
        
        autocomplete_result_id = autocomplete_result.data[0]["id"]
        
        # Get all suggestions
        suggestions = supabase.table("autocomplete_suggestions").select("*").eq("autocomplete_result_id", autocomplete_result_id).order("rank_absolute").execute()
        
        # Analyze suggestions
        intent_distribution = {}
        opportunity_distribution = {}
        difficulty_distribution = {}
        
        for suggestion in suggestions.data:
            # Intent analysis
            intent = suggestion.get("intent_category", "unknown")
            intent_distribution[intent] = intent_distribution.get(intent, 0) + 1
            
            # Opportunity analysis
            opp_type = suggestion.get("opportunity_type", "none")
            opportunity_distribution[opp_type] = opportunity_distribution.get(opp_type, 0) + 1
            
            # Difficulty analysis
            difficulty = suggestion.get("difficulty_level", "unknown")
            difficulty_distribution[difficulty] = difficulty_distribution.get(difficulty, 0) + 1
        
        # Top suggestions by relevance (if available)
        top_suggestions = [
            {
                "rank": s["rank_absolute"],
                "suggestion": s["suggestion"],
                "relevance": s.get("relevance"),
                "intent": s.get("intent_category"),
                "opportunity": s.get("opportunity_type"),
                "difficulty": s.get("difficulty_level"),
                "word_count": s.get("word_count", 0)
            }
            for s in sorted(suggestions.data, key=lambda x: x.get("relevance", 0), reverse=True)[:10]
        ]
        
        # Long-tail opportunities
        long_tail_opportunities = [
            s for s in suggestions.data 
            if s.get("word_count", 0) >= 4 and s.get("opportunity_type") == "long_tail"
        ]
        
        return {
            "success": True,
            "keyword": keyword,
            "autocomplete_overview": {
                "total_suggestions": len(suggestions.data),
                "autocomplete_date": autocomplete_result.data[0]["datetime"],
                "client_used": autocomplete_result.data[0]["client"],
                "primary_intent": max(intent_distribution.items(), key=lambda x: x[1])[0] if intent_distribution else "unknown"
            },
            "intent_analysis": {
                "distribution": intent_distribution,
                "primary_intent": max(intent_distribution.items(), key=lambda x: x[1])[0] if intent_distribution else "unknown"
            },
            "opportunity_analysis": {
                "distribution": opportunity_distribution,
                "long_tail_count": len(long_tail_opportunities),
                "easy_opportunities": len([s for s in suggestions.data if s.get("difficulty_level") == "Easy"])
            },
            "difficulty_analysis": difficulty_distribution,
            "top_suggestions": top_suggestions,
            "content_opportunities": [
                {
                    "suggestion": opp["suggestion"],
                    "rank": opp["rank_absolute"],
                    "word_count": opp["word_count"],
                    "opportunity_type": opp["opportunity_type"],
                    "difficulty": opp["difficulty_level"],
                    "reason": opp["analysis_reason"]
                }
                for opp in long_tail_opportunities[:5]
            ]
        }
        
    except Exception as e:
        logger.exception(f"❌ Error analyzing autocomplete performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

# ========================================
# BULK PROCESSING ENDPOINTS
# ========================================
@router.post("/autocomplete/bulk-process")
async def bulk_process_autocomplete_keywords(keywords: List[str], location_code: int = 2616, language_code: str = "pl", client: str = "gws-wiz-serp"):
    """
    Masowe przetwarzanie słów kluczowych autocomplete (z limitem 10 na raz)
    """
    if len(keywords) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 keywords per bulk request")
    
    results = []
    total_cost = 0
    
    for keyword in keywords:
        try:
            input_data = AutocompleteInput(
                keyword=keyword,
                location_code=location_code,
                language_code=language_code,
                client=client,
                include_analysis=True
            )
            
            # Process each keyword
            result = await get_autocomplete_and_save_to_database(input_data)
            results.append({
                "keyword": keyword,
                "success": True,
                "autocomplete_result_id": result["api_response"]["autocomplete_result_id"],
                "suggestions_processed": result["api_response"]["suggestions_processed"],
                "cost": result["api_response"]["cost_usd"]
            })
            total_cost += result["api_response"]["cost_usd"]
            
            logger.info(f"✅ Bulk processed autocomplete: {keyword}")
            
        except Exception as e:
            logger.error(f"❌ Bulk autocomplete processing failed for {keyword}: {str(e)}")
            results.append({
                "keyword": keyword,
                "success": False,
                "error": str(e),
                "cost": 0
            })
    
    return {
        "success": True,
        "total_keywords": len(keywords),
        "successful": len([r for r in results if r["success"]]),
        "failed": len([r for r in results if not r["success"]]),
        "total_cost_usd": round(total_cost, 4),
        "results": results
    }

# ========================================
# TESTING AND DEBUG ENDPOINTS
# ========================================
@router.post("/autocomplete/test-parser")
async def test_autocomplete_parser(raw_autocomplete_data: Dict):
    """
    Test parser z surowym JSON autocomplete (do debugowania)
    """
    try:
        input_data = AutocompleteInput(
            keyword=raw_autocomplete_data["result"]["keyword"],
            location_code=raw_autocomplete_data["result"]["location_code"],
            language_code=raw_autocomplete_data["result"]["language_code"],
            client=raw_autocomplete_data["result"].get("client", "gws-wiz-serp")
        )
        
        processor = AutocompleteProcessor()
        result = await processor.process_autocomplete_response(raw_autocomplete_data, input_data)
        
        return {
            "success": True,
            "message": "Test autocomplete parsing completed",
            "result": result
        }
        
    except Exception as e:
        logger.exception(f"❌ Test autocomplete parsing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test parsing failed: {str(e)}")

@router.get("/autocomplete/test-functions")
async def test_autocomplete_parsing_functions():
    """
    Test funkcji parsujących autocomplete
    """
    parser = AutocompleteDataParser()
    
    # Test suggestions data
    test_suggestions = [
        {"suggestion": "jak napisać dyktando", "rank_absolute": 1},
        {"suggestion": "dyktanda dla dzieci", "rank_absolute": 2},
        {"suggestion": "dyktanda klasa 3 pdf", "rank_absolute": 3},
        {"suggestion": "dyktanda online interaktywne", "rank_absolute": 4},
        {"suggestion": "dyktanda cena książka", "rank_absolute": 5}
    ]
    
    test_cases = {
        "execution_time": {
            "3.7924 sec.": parser.parse_execution_time("3.7924 sec."),
            "1.234 sec.": parser.parse_execution_time("1.234 sec."),
            "invalid": parser.parse_execution_time("invalid")
        },
        "freshness_hours": {
            "2025-06-03 07:47:32 +00:00": parser.calculate_freshness_hours("2025-06-03 07:47:32 +00:00"),
            "invalid": parser.calculate_freshness_hours("invalid")
        },
        "intent_analysis": parser.analyze_keyword_intent(test_suggestions),
        "trending_modifiers": parser.extract_trending_modifiers(test_suggestions, "dyktanda"),
        "content_opportunities": parser.identify_content_opportunities(test_suggestions, "dyktanda")
    }
    
    return {
        "success": True,
        "test_results": test_cases
    }

@router.post("/autocomplete/reprocess-existing")
async def reprocess_existing_autocomplete(autocomplete_result_id: str):
    """
    Przetwórz ponownie istniejący wynik autocomplete (użyteczne gdy dodano nowe pola do mapowania)
    """
    try:
        # Get existing autocomplete result
        existing = supabase.table("autocomplete_results").select("*").eq("id", autocomplete_result_id).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Autocomplete result not found")
        
        result_data = existing.data[0]
        
        # Create input data from existing record
        input_data = AutocompleteInput(
            keyword=result_data["keyword"],
            location_code=result_data["location_code"],
            language_code=result_data["language_code"],
            client=result_data.get("client", "gws-wiz-serp"),
            cursor_pointer=result_data.get("cursor_pointer"),
            include_analysis=True
        )
        
        # Delete existing suggestions to reprocess
        supabase.table("autocomplete_suggestions").delete().eq("autocomplete_result_id", autocomplete_result_id).execute()
        
        # Note: Would need raw API response stored to fully reprocess
        # For now, just return success message
        
        return {
            "success": True,
            "message": "Autocomplete data marked for reprocessing",
            "autocomplete_result_id": autocomplete_result_id,
            "note": "Full reprocessing requires raw API response to be stored"
        }
        
    except Exception as e:
        logger.exception(f"❌ Error in autocomplete reprocessing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Autocomplete reprocessing failed: {str(e)}")
