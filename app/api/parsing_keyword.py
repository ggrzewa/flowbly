import os
import json
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
import requests
from requests.auth import HTTPBasicAuth
from supabase import create_client, Client
from dataforseo_client import configuration as dfs_config, api_client as dfs_api_provider
from dataforseo_client.api.keywords_data_api import KeywordsDataApi
from dataforseo_client.api.dataforseo_labs_api import DataforseoLabsApi
from dataforseo_client.models.dataforseo_labs_google_search_intent_live_request_info import DataforseoLabsGoogleSearchIntentLiveRequestInfo
from dataforseo_client.models.dataforseo_labs_google_related_keywords_live_request_info import DataforseoLabsGoogleRelatedKeywordsLiveRequestInfo  
from dataforseo_client.models.dataforseo_labs_google_keyword_suggestions_live_request_info import DataforseoLabsGoogleKeywordSuggestionsLiveRequestInfo
from dataforseo_client.models.dataforseo_labs_google_historical_keyword_data_live_request_info import DataforseoLabsGoogleHistoricalKeywordDataLiveRequestInfo
from dataforseo_client.models.keywords_data_dataforseo_trends_merged_data_live_request_info import KeywordsDataDataforseoTrendsMergedDataLiveRequestInfo

# ========================================
# POPRAWIONE ŁADOWANIE .env - dla struktury app/api/
# ========================================

# Znajdź katalog główny projektu (2 poziomy wyżej od parsing_keyword.py)
current_dir = os.path.dirname(os.path.abspath(__file__))  # app/api/
project_root = os.path.join(current_dir, "..", "..")      # flowbly_python/
env_path = os.path.join(project_root, ".env")             # flowbly_python/.env

# Załaduj .env z właściwej lokalizacji
load_dotenv(dotenv_path=env_path)

print(f"🔍 Loading .env from: {env_path}")
print(f"🔍 .env exists: {os.path.exists(env_path)}")

router = APIRouter()

# ============================================================================
# CONFIGURATION
# ============================================================================

# DataForSEO
DFS_LOGIN = os.getenv("DATAFORSEO_LOGIN")
DFS_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

# Supabase
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Logger setup
logger = logging.getLogger("flowbly_parser")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ============================================================================
# SIMPLIFIED INPUT MODEL - bez zbędnych parametrów
# ============================================================================

class KeywordAnalysisInput(BaseModel):
    keyword: str
    location_code: int = 2616  # Poland
    language_code: str = "pl"

# ============================================================================
# WORKING API CLIENTS - 1:1 z działających pojedynczych
# ============================================================================

class WorkingDataForSEOClient:
    def __init__(self):
        self.config = dfs_config.Configuration(username=DFS_LOGIN, password=DFS_PASSWORD)
        
    async def get_intent_data(self, keywords: List[str], location_code: int, language_code: str) -> Dict:
        """Intent API - 1:1 z działającego skryptu"""
        logger.info(f"🧠 Getting Intent data for: {keywords}")
        
        request_data = [
            DataforseoLabsGoogleSearchIntentLiveRequestInfo(
                keywords=keywords,
                location_code=location_code,
                language_code=language_code
            )
        ]
        
        try:
            with dfs_api_provider.ApiClient(self.config) as api_client:
                api_instance = DataforseoLabsApi(api_client)
                logger.debug("➡️ Wysyłanie żądania do DataForSEO Labs API (Search Intent)...")
                api_response = api_instance.google_search_intent_live(request_data)
                task = api_response.tasks[0]
                
                if not task.result:
                    logger.warning("⚠️ Brak wyników dla tych słów kluczowych.")
                    return {"cost": task.cost if hasattr(task, 'cost') else 0, "data": None}
                
                logger.info("✅ Pobrano dane z DFS Labs API (Search Intent).")
                return {
                    "cost": task.cost if hasattr(task, 'cost') else 0,
                    "data": task.result[0].to_dict()
                }
                
        except Exception as e:
            logger.exception("❌ Błąd podczas pobierania danych z DataForSEO Labs API (Search Intent)")
            return {"cost": 0, "data": None, "error": str(e)}
    
    async def get_related_keywords(self, keyword: str, location_code: int, language_code: str) -> Dict:
        """Related Keywords API - 1:1 z działającego skryptu"""
        logger.info(f"🔗 Getting Related Keywords for: {keyword}")
        
        request_data = [
            DataforseoLabsGoogleRelatedKeywordsLiveRequestInfo(
                keyword=keyword,
                location_code=location_code,
                language_code=language_code
            )
        ]
        
        try:
            with dfs_api_provider.ApiClient(self.config) as api_client:
                api_instance = DataforseoLabsApi(api_client)
                logger.debug("➡️ Wysyłanie żądania do DataForSEO Labs API (Related Keywords)...")
                api_response = api_instance.google_related_keywords_live(request_data)
                task = api_response.tasks[0]
                
                if not task.result:
                    logger.warning("⚠️ Brak wyników dla tego słowa kluczowego.")
                    return {"cost": task.cost if hasattr(task, 'cost') else 0, "data": None}
                
                logger.info("✅ Pobrano dane z DFS Labs API (Related Keywords).")
                return {
                    "cost": task.cost if hasattr(task, 'cost') else 0,
                    "data": task.result[0].to_dict()
                }
                
        except Exception as e:
            logger.exception("❌ Błąd podczas pobierania danych z DataForSEO Labs API (Related Keywords)")
            return {"cost": 0, "data": None, "error": str(e)}
    
    async def get_keyword_suggestions(self, keyword: str, location_code: int, language_code: str) -> Dict:
        """Keyword Suggestions API - 1:1 z działającego skryptu"""
        logger.info(f"💡 Getting Keyword Suggestions for: {keyword}")
        
        request_data = [
            DataforseoLabsGoogleKeywordSuggestionsLiveRequestInfo(
                keyword=keyword,
                location_code=location_code,
                language_code=language_code,
                include_seed_keyword=True,
                include_serp_info=False,
                limit=20
            )
        ]
        
        try:
            with dfs_api_provider.ApiClient(self.config) as api_client:
                api_instance = DataforseoLabsApi(api_client)
                logger.debug("➡️ Wysyłanie żądania do DFS Labs API (Keyword Suggestions)...")
                api_response = api_instance.google_keyword_suggestions_live(request_data)
                task = api_response.tasks[0]
                
                if not task.result or not task.result[0].items:
                    logger.warning("⚠️ Brak wyników dla podanego słowa.")
                    return {"cost": task.cost if hasattr(task, 'cost') else 0, "data": None}
                
                logger.info("✅ Pobrano dane z DFS Labs API (Keyword Suggestions).")
                return {
                    "cost": task.cost if hasattr(task, 'cost') else 0,
                    "data": {
                        "seed_keyword": task.result[0].seed_keyword,
                        "items": [item.to_dict() for item in task.result[0].items]
                    }
                }
                
        except Exception as e:
            logger.exception("❌ Błąd podczas pobierania sugestii z DFS Labs API")
            return {"cost": 0, "data": None, "error": str(e)}
    
    async def get_historical_data(self, keywords: List[str], location_code: int, language_code: str) -> Dict:
        """Historical Data API - 1:1 z działającego skryptu"""
        logger.info(f"📅 Getting Historical data for: {keywords}")
        
        request_data = [
            DataforseoLabsGoogleHistoricalKeywordDataLiveRequestInfo(
                keywords=keywords,
                location_code=location_code,
                language_code=language_code
            )
        ]
        
        try:
            with dfs_api_provider.ApiClient(self.config) as api_client:
                api_instance = DataforseoLabsApi(api_client)
                logger.debug("➡️ Wysyłanie żądania do DataForSEO Labs API (Historical Keyword Data)...")
                api_response = api_instance.google_historical_keyword_data_live(request_data)
                task = api_response.tasks[0]
                
                if not task.result:
                    logger.warning("⚠️ Brak wyników dla podanych słów kluczowych.")
                    return {"cost": task.cost if hasattr(task, 'cost') else 0, "data": None}
                
                logger.info("✅ Pobrano dane z DFS Labs API (Historical Keyword Data).")
                return {
                    "cost": task.cost if hasattr(task, 'cost') else 0,
                    "data": task.result[0].to_dict()
                }
                
        except Exception as e:
            logger.exception("❌ Błąd podczas pobierania danych z DFS Labs API (Historical)")
            return {"cost": 0, "data": None, "error": str(e)}
    
    async def get_dataforseo_trends(self, keywords: List[str], location_code: int, language_code: str) -> Dict:
        """DataForSEO Trends API - 1:1 z działającego skryptu"""
        logger.info(f"📈 Getting DataForSEO Trends for: {keywords}")
        
        request_data = [
            KeywordsDataDataforseoTrendsMergedDataLiveRequestInfo(
                keywords=keywords,
                location_code=location_code,
                language_code=language_code,
                type="web"
            )
        ]
        
        try:
            with dfs_api_provider.ApiClient(self.config) as api_client:
                api_instance = KeywordsDataApi(api_client)
                logger.debug("➡️ Wysyłanie żądania do DataForSEO Trends API...")
                api_response = api_instance.dataforseo_trends_merged_data_live(request_data)
                task = api_response.tasks[0]
                
                if not task.result:
                    logger.warning("⚠️ Brak wyników dla podanych słów kluczowych.")
                    return {"cost": task.cost if hasattr(task, 'cost') else 0, "data": None}
                
                logger.info("✅ Pobrano dane z DataForSEO Trends API.")
                return {
                    "cost": task.cost if hasattr(task, 'cost') else 0,
                    "data": task.result[0].to_dict()
                }
                
        except Exception as e:
            logger.exception("❌ Błąd podczas pobierania danych z DataForSEO Trends API")
            return {"cost": 0, "data": None, "error": str(e)}

# ============================================================================
# SIMPLIFIED PARSER
# ============================================================================

class SimpleFlowblyParser:
    def __init__(self):
        self.total_cost = 0.0
        self.parsed_data = {}
    
    def parse_all_endpoints(self, keyword: str, all_responses: Dict) -> Dict:
        """Parse data from all endpoints"""
        logger.info(f"🔄 Parsing data for keyword: {keyword}")
        
        # Initialize base keyword record
        keyword_record = {
            "keyword": keyword,
            "location_code": 2616,
            "language_code": "pl",
            "seed_keyword": keyword,
            "is_suggestion": False,
            "parent_keyword_id": None,
            "data_sources": [],
            "api_costs_total": 0.0,
            "raw_responses": all_responses,
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Count total cost
        for endpoint, response in all_responses.items():
            if response and "cost" in response:
                keyword_record["api_costs_total"] += response["cost"]
        
        # Parse each endpoint if data exists
        if all_responses.get("intent", {}).get("data"):
            self._parse_intent_data(keyword_record, all_responses["intent"]["data"])
            keyword_record["data_sources"].append("intent")
        
        if all_responses.get("related_kw", {}).get("data"):
            self._parse_related_keywords(keyword_record, all_responses["related_kw"]["data"])
            keyword_record["data_sources"].append("related_kw")
        
        if all_responses.get("suggestions", {}).get("data"):
            self._parse_keyword_suggestions(keyword_record, all_responses["suggestions"]["data"])
            keyword_record["data_sources"].append("keyword_suggestions")
        
        if all_responses.get("historical", {}).get("data"):
            self._parse_historical_data(keyword_record, all_responses["historical"]["data"])
            keyword_record["data_sources"].append("historical")
        
        if all_responses.get("df_trends", {}).get("data"):
            self._parse_dataforseo_trends(keyword_record, all_responses["df_trends"]["data"])
            keyword_record["data_sources"].append("df_trends")
        
        return keyword_record
    
    def _parse_intent_data(self, keyword_record: Dict, intent_data: Dict):
        """Parse Intent API data"""
        items = intent_data.get("items", [])
        if not items:
            return
            
        for item in items:
            if item.get("keyword") == keyword_record["keyword"]:
                keyword_intent = item.get("keyword_intent", {})
                keyword_record["main_intent"] = keyword_intent.get("label")
                keyword_record["intent_probability"] = keyword_intent.get("probability")
                
                secondary_intents = item.get("secondary_keyword_intents", [])
                if secondary_intents:
                    keyword_record["secondary_intents"] = secondary_intents
                break
    
    def _parse_related_keywords(self, keyword_record: Dict, related_data: Dict):
        """Parse Related Keywords data"""
        items = related_data.get("items", [])
        seed_data = related_data.get("seed_keyword_data", {})
        
        # Extract seed keyword info
        if seed_data:
            keyword_info = seed_data.get("keyword_info", {})
            self._extract_keyword_info(keyword_record, keyword_info)
        
        # Store related keywords
        self.parsed_data["related_keywords"] = []
        for item in items:
            related_kw = {
                "keyword": item.get("keyword"),
                "depth": item.get("depth", 0),
                "keyword_data": item.get("keyword_data", {})
            }
            self.parsed_data["related_keywords"].append(related_kw)
    
    def _parse_keyword_suggestions(self, keyword_record: Dict, suggestions_data: Dict):
        """Parse Keyword Suggestions data"""
        items = suggestions_data.get("items", [])
        if not items:
            return
        
        self.parsed_data["suggestions"] = []
        for item in items:
            suggestion = {
                "keyword": item.get("keyword"),
                "keyword_info": item.get("keyword_info", {}),
                "is_suggestion": True,
                "parent_keyword": keyword_record["keyword"]
            }
            self.parsed_data["suggestions"].append(suggestion)
    
    def _parse_historical_data(self, keyword_record: Dict, historical_data: Dict):
        """Parse Historical data"""
        items = historical_data.get("items", [])
        if not items:
            return
        
        self.parsed_data["historical_data"] = []
        for item in items:
            if item.get("keyword") == keyword_record["keyword"]:
                history = item.get("history", [])
                for hist_item in history:
                    hist_record = {
                        "year": hist_item.get("year"),
                        "month": hist_item.get("month"),
                        "keyword_info": hist_item.get("keyword_info", {})
                    }
                    self.parsed_data["historical_data"].append(hist_record)
    
    def _parse_dataforseo_trends(self, keyword_record: Dict, df_trends_data: Dict):
        """Parse DataForSEO Trends data"""
        items = df_trends_data.get("items", [])
        if not items:
            return
        
        for item in items:
            item_type = item.get("type")
            
            if item_type == "dataforseo_trends_graph":
                keyword_record["trends_graph"] = item.get("data", [])
            
            elif item_type == "subregion_interests":
                interests = item.get("interests", [])
                if interests:
                    geo_data = []
                    for interest in interests:
                        values = interest.get("values", [])
                        for value in values:
                            geo_data.append({
                                "geo_id": value.get("geo_id"),
                                "geo_name": value.get("geo_name"),
                                "value": value.get("value")
                            })
                    keyword_record["subregion_interests"] = geo_data
    
    def _extract_keyword_info(self, keyword_record: Dict, keyword_info: Dict):
        """Extract standard keyword_info fields"""
        keyword_record["search_volume"] = keyword_info.get("search_volume")
        keyword_record["competition"] = keyword_info.get("competition")
        keyword_record["competition_level"] = keyword_info.get("competition_level")
        keyword_record["cpc"] = keyword_info.get("cpc")
        keyword_record["categories"] = keyword_info.get("categories", [])
        
        monthly_searches = keyword_info.get("monthly_searches", [])
        if monthly_searches:
            keyword_record["monthly_searches"] = monthly_searches
        
        search_volume_trend = keyword_info.get("search_volume_trend", {})
        if search_volume_trend:
            keyword_record["search_volume_trend"] = search_volume_trend
            keyword_record["monthly_trend_pct"] = search_volume_trend.get("monthly")
            keyword_record["quarterly_trend_pct"] = search_volume_trend.get("quarterly")
            keyword_record["yearly_trend_pct"] = search_volume_trend.get("yearly")

# ============================================================================
# SIMPLIFIED DATABASE OPERATIONS
# ============================================================================

class SimpleSupabaseOperations:
    def __init__(self):
        self.client = supabase
    
    async def save_keyword_data(self, keyword_record: Dict, related_data: Dict) -> str:
        """Save keyword data to Supabase with UPSERT"""
        logger.info(f"💾 Saving keyword data: {keyword_record['keyword']}")
        
        try:
            # Check if keyword already exists
            existing = self.client.table("keywords").select("id").eq("keyword", keyword_record["keyword"]).eq("location_code", keyword_record["location_code"]).eq("language_code", keyword_record["language_code"]).execute()
            
            if existing.data:
                # UPDATE existing keyword
                keyword_id = existing.data[0]["id"]
                result = self.client.table("keywords").update(keyword_record).eq("id", keyword_id).execute()
                logger.info(f"🔄 Updated existing keyword with ID: {keyword_id}")
            else:
                # INSERT new keyword
                result = self.client.table("keywords").insert(keyword_record).execute()
                keyword_id = result.data[0]["id"]
                logger.info(f"✅ Created new keyword with ID: {keyword_id}")
            
            # Save related data if exists
            if "suggestions" in related_data and related_data["suggestions"]:
                await self._save_suggestions(keyword_id, related_data["suggestions"])
            
            if "related_keywords" in related_data and related_data["related_keywords"]:
                await self._save_related_keywords(keyword_id, related_data["related_keywords"])
            
            return keyword_id
            
        except Exception as e:
            logger.error(f"❌ Error saving to Supabase: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")
    
    async def _save_suggestions(self, parent_id: str, suggestions: List[Dict]):
        """Save suggestions"""
        for suggestion in suggestions[:5]:  # Limit to first 5 for now
            try:
                suggestion_record = {
                    "keyword": suggestion["keyword"],
                    "location_code": 2616,
                    "language_code": "pl",
                    "is_suggestion": True,
                    "parent_keyword_id": parent_id,
                    "seed_keyword": suggestion["parent_keyword"]
                }
                
                keyword_info = suggestion.get("keyword_info", {})
                suggestion_record.update({
                    "search_volume": keyword_info.get("search_volume"),
                    "competition": keyword_info.get("competition"),
                    "cpc": keyword_info.get("cpc")
                })
                
                result = self.client.table("keywords").insert(suggestion_record).execute()
                suggestion_id = result.data[0]["id"]
                
                relation = {
                    "parent_keyword_id": parent_id,
                    "related_keyword_id": suggestion_id,
                    "depth": 0,
                    "relationship_type": "suggestion",
                    "search_volume": suggestion_record.get("search_volume")
                }
                
                self.client.table("keyword_relations").insert(relation).execute()
                
            except Exception as e:
                logger.warning(f"⚠️ Error saving suggestion {suggestion['keyword']}: {str(e)}")
    
    async def _save_related_keywords(self, parent_id: str, related_keywords: List[Dict]):
        """Save related keywords"""
        for related in related_keywords[:10]:  # Limit to first 10 for now
            try:
                # Skip if keyword is None or empty
                if not related.get("keyword"):
                    logger.warning(f"⚠️ Skipping related keyword with null/empty keyword: {related}")
                    continue
                
                related_record = {
                    "keyword": related["keyword"],
                    "location_code": 2616,
                    "language_code": "pl",
                    "depth": related.get("depth", 0),
                    "is_suggestion": False
                }
                
                keyword_data = related.get("keyword_data", {})
                if "keyword_info" in keyword_data:
                    keyword_info = keyword_data["keyword_info"]
                    related_record.update({
                        "search_volume": keyword_info.get("search_volume"),
                        "competition": keyword_info.get("competition"),
                        "cpc": keyword_info.get("cpc")
                    })
                
                # Check if keyword already exists
                existing = self.client.table("keywords").select("id").eq("keyword", related["keyword"]).eq("location_code", 2616).execute()
                
                if existing.data:
                    related_id = existing.data[0]["id"]
                    logger.info(f"🔄 Related keyword already exists: {related['keyword']}")
                else:
                    result = self.client.table("keywords").insert(related_record).execute()
                    related_id = result.data[0]["id"]
                    logger.info(f"✅ Created related keyword: {related['keyword']}")
                
                relation = {
                    "parent_keyword_id": parent_id,
                    "related_keyword_id": related_id,
                    "depth": related.get("depth", 0),
                    "relationship_type": "related",
                    "search_volume": related_record.get("search_volume")
                }
                
                self.client.table("keyword_relations").insert(relation).execute()
                
            except Exception as e:
                logger.warning(f"⚠️ Error saving related keyword {related.get('keyword', 'UNKNOWN')}: {str(e)}")

# ============================================================================
# MAIN ENDPOINT - SIMPLIFIED
# ============================================================================

@router.post("/analyze-keyword")
async def analyze_keyword(data: KeywordAnalysisInput):
    """Complete keyword analysis - ALL endpoints automatically"""
    
    if not all([DFS_LOGIN, DFS_PASSWORD, SUPABASE_URL, SUPABASE_KEY]):
        raise HTTPException(status_code=500, detail="Missing API credentials")
    
    logger.info(f"🚀 Starting analysis for: {data.keyword}")
    
    # Initialize clients
    dfs_client = WorkingDataForSEOClient()
    parser = SimpleFlowblyParser()
    db_ops = SimpleSupabaseOperations()
    
    # Collect ALL API responses
    all_responses = {}
    total_cost = 0.0
    
    try:
        # Call ALL endpoints automatically
        logger.info("📞 Calling ALL DataForSEO endpoints...")
        
        # 1. Intent API
        all_responses["intent"] = await dfs_client.get_intent_data([data.keyword], data.location_code, data.language_code)
        
        # 2. Related Keywords  
        all_responses["related_kw"] = await dfs_client.get_related_keywords(data.keyword, data.location_code, data.language_code)
        
        # 3. Keyword Suggestions
        all_responses["suggestions"] = await dfs_client.get_keyword_suggestions(data.keyword, data.location_code, data.language_code)
        
        # 4. Historical Data
        all_responses["historical"] = await dfs_client.get_historical_data([data.keyword], data.location_code, data.language_code)
        
        # 5. DataForSEO Trends
        all_responses["df_trends"] = await dfs_client.get_dataforseo_trends([data.keyword], data.location_code, data.language_code)
        
        # Calculate total cost
        for endpoint, response in all_responses.items():
            if response and "cost" in response:
                total_cost += response["cost"]
        
        logger.info(f"💰 Total API cost: ${total_cost:.4f}")
        
        # Parse all data
        keyword_record = parser.parse_all_endpoints(data.keyword, all_responses)
        
        # Save to Supabase
        keyword_id = await db_ops.save_keyword_data(keyword_record, parser.parsed_data)
        
        # Response
        response = {
            "success": True,
            "keyword_id": keyword_id,
            "keyword": data.keyword,
            "total_cost_usd": total_cost,
            "data_sources": keyword_record["data_sources"],
            "summary": {
                "search_volume": keyword_record.get("search_volume"),
                "main_intent": keyword_record.get("main_intent"),
                "keyword_difficulty": keyword_record.get("keyword_difficulty"),
                "related_keywords_count": len(parser.parsed_data.get("related_keywords", [])),
                "suggestions_count": len(parser.parsed_data.get("suggestions", [])),
                "historical_months": len(parser.parsed_data.get("historical_data", []))
            },
            "api_responses": all_responses,
            "parsed_data": {
                "main_keyword": keyword_record,
                "related_keywords": parser.parsed_data.get("related_keywords", []),
                "suggestions": parser.parsed_data.get("suggestions", []),
                "historical_data": parser.parsed_data.get("historical_data", [])
            }
        }
        
        logger.info(f"✅ Analysis completed for: {data.keyword}")
        return response
        
    except Exception as e:
        logger.exception(f"❌ Error during analysis: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis failed: {str(e)}")

# ============================================================================
# TEST ENDPOINTS
# ============================================================================

@router.get("/test-dataforseo")
async def test_dataforseo():
    """Test DataForSEO API connection"""
    
    if not DFS_LOGIN or not DFS_PASSWORD:
        return {
            "status": "❌ MISSING CREDENTIALS",
            "login": "✅ SET" if DFS_LOGIN else "❌ MISSING",
            "password": "✅ SET" if DFS_PASSWORD else "❌ MISSING"
        }
    
    try:
        # Simple test call
        auth = HTTPBasicAuth(DFS_LOGIN, DFS_PASSWORD)
        response = requests.get("https://api.dataforseo.com/v3/user", auth=auth)
        
        if response.status_code == 200:
            data = response.json()
            return {
                "status": "✅ CONNECTED",
                "login": DFS_LOGIN,
                "remaining_money": data.get("tasks", [{}])[0].get("data", {}).get("money", {}).get("remaining", "Unknown")
            }
        else:
            return {
                "status": "❌ AUTH FAILED", 
                "error": response.text,
                "status_code": response.status_code
            }
            
    except Exception as e:
        return {"status": "❌ CONNECTION ERROR", "error": str(e)}

@router.get("/stats")
async def get_stats():
    """Get database statistics"""
    try:
        keywords_count = supabase.table("keywords").select("id", count="exact").execute()
        relations_count = supabase.table("keyword_relations").select("id", count="exact").execute()
        return {
            "total_keywords": keywords_count.count,
            "total_relations": relations_count.count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@router.post("/test-single-endpoint")
async def test_single_endpoint(endpoint: str, keyword: str):
    """Test individual endpoint - for debugging"""
    dfs_client = WorkingDataForSEOClient()
    
    try:
        if endpoint == "intent":
            result = await dfs_client.get_intent_data([keyword], 2616, "pl")
        elif endpoint == "related":
            result = await dfs_client.get_related_keywords(keyword, 2616, "pl")
        elif endpoint == "suggestions":
            result = await dfs_client.get_keyword_suggestions(keyword, 2616, "pl")
        elif endpoint == "historical":
            result = await dfs_client.get_historical_data([keyword], 2616, "pl")
        elif endpoint == "df_trends":
            result = await dfs_client.get_dataforseo_trends([keyword], 2616, "pl")
        else:
            raise HTTPException(status_code=400, detail="Invalid endpoint")
        
        return {
            "endpoint": endpoint,
            "keyword": keyword,
            "cost": result["cost"],
            "data": result["data"],
            "has_data": result["data"] is not None,
            "error": result.get("error")
        }
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Test failed: {str(e)}")

@router.get("/keyword/{keyword_id}")
async def get_keyword_data(keyword_id: str):
    """Get complete keyword data from database"""
    try:
        # Get main keyword
        keyword_result = supabase.table("keywords").select("*").eq("id", keyword_id).execute()
        if not keyword_result.data:
            raise HTTPException(status_code=404, detail="Keyword not found")
        
        keyword = keyword_result.data[0]
        
        # Get related keywords
        relations_result = supabase.table("keyword_relations").select("""
            *,
            related_keyword:related_keyword_id(*)
        """).eq("parent_keyword_id", keyword_id).execute()
        
        # Get historical data
        historical_result = supabase.table("keyword_historical_data").select("*").eq("keyword_id", keyword_id).execute()
        
        return {
            "keyword": keyword,
            "relations": relations_result.data,
            "historical_data": historical_result.data
        }
        
    except Exception as e:
        logger.error(f"❌ Error fetching keyword data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Database error: {str(e)}")

@router.get("/keywords/search")
async def search_keywords(q: str, limit: int = 10):
    """Search keywords in database"""
    try:
        result = supabase.table("keywords").select("id, keyword, search_volume, main_intent, last_updated").ilike("keyword", f"%{q}%").limit(limit).execute()
        return {"keywords": result.data}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search error: {str(e)}")