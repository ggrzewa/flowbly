import os
import logging
from datetime import datetime
from typing import Dict, List
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
# ENVIRONMENT SETUP
# ========================================
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.join(current_dir, "..", "..")
env_path = os.path.join(project_root, ".env")
load_dotenv(dotenv_path=env_path)

print(f"🔍 Loading .env from: {env_path}")
print(f"🔍 .env exists: {os.path.exists(env_path)}")

router = APIRouter()

# ========================================
# CONFIGURATION
# ========================================
DFS_LOGIN = os.getenv("DATAFORSEO_LOGIN")
DFS_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Logger setup
logger = logging.getLogger("flowbly_parser_v2")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter('%(asctime)s | %(levelname)s | %(message)s')
handler.setFormatter(formatter)
logger.addHandler(handler)

# Initialize Supabase client
supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

# ========================================
# INPUT MODEL
# ========================================
class KeywordAnalysisInput(BaseModel):
    keyword: str
    location_code: int = 2616  # Poland
    language_code: str = "pl"

# ========================================
# DATAFORSEO CLIENT
# ========================================
class DataForSEOClient:
    def __init__(self):
        self.config = dfs_config.Configuration(username=DFS_LOGIN, password=DFS_PASSWORD)
        
    async def get_intent_data(self, keywords: List[str], location_code: int, language_code: str) -> Dict:
        logger.info(f"🧠 Getting Intent data for: {keywords}")
        
        request_data = [DataforseoLabsGoogleSearchIntentLiveRequestInfo(
            keywords=keywords, location_code=location_code, language_code=language_code
        )]
        
        try:
            with dfs_api_provider.ApiClient(self.config) as api_client:
                api_instance = DataforseoLabsApi(api_client)
                api_response = api_instance.google_search_intent_live(request_data)
                task = api_response.tasks[0]
                
                if not task.result:
                    return {"cost": task.cost if hasattr(task, 'cost') else 0, "data": None}
                
                return {"cost": task.cost if hasattr(task, 'cost') else 0, "data": task.result[0].to_dict()}
                
        except Exception as e:
            logger.exception("❌ Intent API error")
            return {"cost": 0, "data": None, "error": str(e)}
    
    async def get_related_keywords(self, keyword: str, location_code: int, language_code: str) -> Dict:
        logger.info(f"🔗 Getting Related Keywords for: {keyword}")
        
        request_data = [DataforseoLabsGoogleRelatedKeywordsLiveRequestInfo(
            keyword=keyword, location_code=location_code, language_code=language_code
        )]
        
        try:
            with dfs_api_provider.ApiClient(self.config) as api_client:
                api_instance = DataforseoLabsApi(api_client)
                api_response = api_instance.google_related_keywords_live(request_data)
                task = api_response.tasks[0]
                
                if not task.result:
                    return {"cost": task.cost if hasattr(task, 'cost') else 0, "data": None}
                
                return {"cost": task.cost if hasattr(task, 'cost') else 0, "data": task.result[0].to_dict()}
                
        except Exception as e:
            logger.exception("❌ Related Keywords API error")
            return {"cost": 0, "data": None, "error": str(e)}
    
    async def get_keyword_suggestions(self, keyword: str, location_code: int, language_code: str) -> Dict:
        logger.info(f"💡 Getting Keyword Suggestions for: {keyword}")
        
        request_data = [DataforseoLabsGoogleKeywordSuggestionsLiveRequestInfo(
            keyword=keyword, location_code=location_code, language_code=language_code,
            include_seed_keyword=True, include_serp_info=False, limit=20
        )]
        
        try:
            with dfs_api_provider.ApiClient(self.config) as api_client:
                api_instance = DataforseoLabsApi(api_client)
                api_response = api_instance.google_keyword_suggestions_live(request_data)
                task = api_response.tasks[0]
                
                if not task.result or not task.result[0].items:
                    return {"cost": task.cost if hasattr(task, 'cost') else 0, "data": None}
                
                return {
                    "cost": task.cost if hasattr(task, 'cost') else 0,
                    "data": {"seed_keyword": task.result[0].seed_keyword, "items": [item.to_dict() for item in task.result[0].items]}
                }
                
        except Exception as e:
            logger.exception("❌ Suggestions API error")
            return {"cost": 0, "data": None, "error": str(e)}
    
    async def get_historical_data(self, keywords: List[str], location_code: int, language_code: str) -> Dict:
        logger.info(f"📅 Getting Historical data for: {keywords}")
        
        request_data = [DataforseoLabsGoogleHistoricalKeywordDataLiveRequestInfo(
            keywords=keywords, location_code=location_code, language_code=language_code
        )]
        
        try:
            with dfs_api_provider.ApiClient(self.config) as api_client:
                api_instance = DataforseoLabsApi(api_client)
                api_response = api_instance.google_historical_keyword_data_live(request_data)
                task = api_response.tasks[0]
                
                if not task.result:
                    return {"cost": task.cost if hasattr(task, 'cost') else 0, "data": None}
                
                return {"cost": task.cost if hasattr(task, 'cost') else 0, "data": task.result[0].to_dict()}
                
        except Exception as e:
            logger.exception("❌ Historical API error")
            return {"cost": 0, "data": None, "error": str(e)}
    
    async def get_dataforseo_trends(self, keywords: List[str], location_code: int, language_code: str) -> Dict:
        logger.info(f"📈 Getting DataForSEO Trends for: {keywords}")
        
        request_data = [KeywordsDataDataforseoTrendsMergedDataLiveRequestInfo(
            keywords=keywords, location_code=location_code, language_code=language_code, type="web"
        )]
        
        try:
            with dfs_api_provider.ApiClient(self.config) as api_client:
                api_instance = KeywordsDataApi(api_client)
                api_response = api_instance.dataforseo_trends_merged_data_live(request_data)
                task = api_response.tasks[0]
                
                if not task.result:
                    return {"cost": task.cost if hasattr(task, 'cost') else 0, "data": None}
                
                return {"cost": task.cost if hasattr(task, 'cost') else 0, "data": task.result[0].to_dict()}
                
        except Exception as e:
            logger.exception("❌ Trends API error")
            return {"cost": 0, "data": None, "error": str(e)}

    async def get_google_trends_explore(self, keywords: List[str], location_code: int, language_code: str) -> Dict:
        logger.info(f"🌍 Getting Google Trends Explore for: {keywords}")
        
        url = "https://api.dataforseo.com/v3/keywords_data/google_trends/explore/live"
        payload = [
            {
                "keywords": keywords,
                "location_code": location_code,
                "language_code": language_code,
                "type": "web",
                "item_types": [
                    "google_trends_graph",
                    "google_trends_map", 
                    "google_trends_topics_list",
                    "google_trends_queries_list"
                ]
            }
        ]
        
        try:
            auth = HTTPBasicAuth(DFS_LOGIN, DFS_PASSWORD)
            response = requests.post(url, auth=auth, json=payload)
            
            if response.status_code != 200:
                logger.error(f"GT Explore API error: {response.status_code} - {response.text}")
                return {"cost": 0, "data": None, "error": f"API error: {response.status_code}"}
            
            json_data = response.json()
            tasks = json_data.get("tasks", [])
            
            if not tasks or not tasks[0].get("result"):
                return {"cost": tasks[0].get("cost", 0) if tasks else 0, "data": None}
            
            return {"cost": tasks[0].get("cost", 0), "data": tasks[0]["result"][0]}
            
        except Exception as e:
            logger.exception("❌ GT Explore API error")
            return {"cost": 0, "data": None, "error": str(e)}

# ========================================
# SEPARATE ENDPOINTS - NO LIMITS
# ========================================

@router.post("/analyze-intent-only")
async def analyze_intent_only(data: KeywordAnalysisInput):
    """🧠 Intent API only - compact response"""
    
    if not all([DFS_LOGIN, DFS_PASSWORD, SUPABASE_URL, SUPABASE_KEY]):
        raise HTTPException(status_code=500, detail="Missing API credentials")
    
    dfs_client = DataForSEOClient()
    
    try:
        intent_response = await dfs_client.get_intent_data([data.keyword], data.location_code, data.language_code)
        
        keyword_record = {
            "keyword": data.keyword, "location_code": data.location_code, "language_code": data.language_code,
            "seed_keyword": data.keyword, "is_suggestion": False, "data_sources": ["intent"],
            "api_costs_total": intent_response.get("cost", 0), "last_updated": datetime.utcnow().isoformat()
        }
        
        # Parse intent data
        if intent_response.get("data"):
            items = intent_response["data"].get("items", [])
            for item in items:
                if item.get("keyword") == data.keyword:
                    keyword_intent = item.get("keyword_intent", {})
                    keyword_record["main_intent"] = keyword_intent.get("label")
                    keyword_record["intent_probability"] = keyword_intent.get("probability")
                    
                    secondary_intents = item.get("secondary_keyword_intents", [])
                    if secondary_intents:
                        keyword_record["secondary_intents"] = secondary_intents
                    break
        
        # Upsert to database
        existing = supabase.table("keywords").select("id").eq("keyword", data.keyword).eq("location_code", data.location_code).eq("language_code", data.language_code).execute()
        
        if existing.data:
            keyword_id = existing.data[0]["id"]
            supabase.table("keywords").update(keyword_record).eq("id", keyword_id).execute()
            logger.info(f"🔄 Updated keyword: {data.keyword}")
        else:
            result = supabase.table("keywords").insert(keyword_record).execute()
            keyword_id = result.data[0]["id"]
            logger.info(f"✅ Created keyword: {data.keyword}")
        
        return {
            "success": True, "keyword_id": keyword_id, "keyword": data.keyword,
            "cost_usd": intent_response.get("cost", 0),
            "main_intent": keyword_record.get("main_intent"),
            "intent_probability": keyword_record.get("intent_probability"),
            "secondary_intents": keyword_record.get("secondary_intents", []),
            "raw_response": intent_response
        }
        
    except Exception as e:
        logger.exception(f"❌ Intent analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Intent analysis failed: {str(e)}")

@router.post("/analyze-related-only")
async def analyze_related_only(data: KeywordAnalysisInput):
    """🔗 Related Keywords API only - saves ALL related keywords"""
    
    if not all([DFS_LOGIN, DFS_PASSWORD, SUPABASE_URL, SUPABASE_KEY]):
        raise HTTPException(status_code=500, detail="Missing API credentials")
    
    dfs_client = DataForSEOClient()
    
    try:
        related_response = await dfs_client.get_related_keywords(data.keyword, data.location_code, data.language_code)
        
        if not related_response.get("data"):
            raise HTTPException(status_code=404, detail="No related keywords found")
        
        related_data = related_response["data"]
        
        logger.info(f"🔍 === RAW RESPONSE STRUCTURE ===")
        logger.info(f"🔍 related_response keys: {list(related_response.keys())}")
        logger.info(f"🔍 related_data keys: {list(related_data.keys())}")
        logger.info(f"🔍 related_data type: {type(related_data)}")
        
        # Parse seed keyword data first
        seed_keyword_record = {
            "keyword": data.keyword, "location_code": data.location_code, "language_code": data.language_code,
            "seed_keyword": data.keyword, "is_suggestion": False, "data_sources": ["related_kw"],
            "api_costs_total": related_response.get("cost", 0), "last_updated": datetime.utcnow().isoformat()
        }
        
        # Extract seed keyword info - search in items where depth == 0
        items = related_data.get("items", [])
        seed_data = None
        
        logger.info(f"🔍 DEBUGGING SEED KEYWORD SEARCH")
        logger.info(f"🔍 Total items in response: {len(items)}")
        logger.info(f"🔍 Items type: {type(items)}")
        
        # Detailed logging for each item
        for i, item in enumerate(items):
            logger.info(f"🔍 === ITEM {i} ANALYSIS ===")
            logger.info(f"🔍 Item type: {type(item)}")
            logger.info(f"🔍 Item keys: {list(item.keys()) if isinstance(item, dict) else 'NOT A DICT'}")
            
            # Check depth
            depth_value = item.get("depth")
            logger.info(f"🔍 Raw depth value: {repr(depth_value)} (type: {type(depth_value)})")
            
            # Check keyword
            keyword_data = item.get("keyword_data", {})
            keyword_name = keyword_data.get("keyword", "UNKNOWN") if isinstance(keyword_data, dict) else "NO KEYWORD_DATA"
            logger.info(f"🔍 Keyword name: '{keyword_name}'")
            
            # Depth comparison tests
            logger.info(f"🔍 depth == 0: {depth_value == 0}")
            logger.info(f"🔍 depth == '0': {depth_value == '0'}")
            logger.info(f"🔍 str(depth) == '0': {str(depth_value) == '0'}")
            logger.info(f"🔍 int(depth) == 0: {int(depth_value) == 0 if depth_value is not None else 'DEPTH IS NONE'}")
            
            # Check if this is seed keyword
            if depth_value == 0:
                logger.info(f"✅ FOUND SEED KEYWORD (depth == 0) at index {i}: '{keyword_name}'")
                seed_data = keyword_data
                break
            elif str(depth_value) == "0":
                logger.info(f"✅ FOUND SEED KEYWORD (str(depth) == '0') at index {i}: '{keyword_name}'")
                seed_data = keyword_data
                break
            else:
                logger.info(f"❌ NOT seed keyword - depth: {repr(depth_value)}")
        
        logger.info(f"🔍 === SEED KEYWORD SEARCH RESULT ===")
        if seed_data:
            logger.info(f"✅ Seed keyword found! Keyword: '{seed_data.get('keyword', 'UNKNOWN')}'")
            logger.info(f"✅ Seed data keys: {list(seed_data.keys())}")
        else:
            logger.warning(f"❌ SEED KEYWORD NOT FOUND!")
            logger.warning(f"❌ Falling back to first item as seed")
            if items and len(items) > 0:
                seed_data = items[0].get("keyword_data", {})
                fallback_keyword = seed_data.get("keyword", "UNKNOWN") if isinstance(seed_data, dict) else "NO DATA"
                logger.warning(f"🔄 Using fallback seed: '{fallback_keyword}'")
            else:
                logger.error(f"💥 NO ITEMS AVAILABLE - CANNOT PROCEED")
        
        if seed_data:
            keyword_info = seed_data.get("keyword_info", {})
            seed_keyword_record.update({
                "search_volume": keyword_info.get("search_volume"),
                "competition": keyword_info.get("competition"),
                "competition_level": keyword_info.get("competition_level"),
                "cpc": keyword_info.get("cpc"),
                "categories": keyword_info.get("categories", []),
                "monthly_searches": keyword_info.get("monthly_searches", []),
                "search_volume_trend": keyword_info.get("search_volume_trend", {}),
                "low_top_of_page_bid": keyword_info.get("low_top_of_page_bid"),
                "high_top_of_page_bid": keyword_info.get("high_top_of_page_bid")
            })
            
            if "keyword_properties" in seed_data:
                props = seed_data["keyword_properties"]
                seed_keyword_record.update({
                    "keyword_difficulty": props.get("keyword_difficulty"),
                    "detected_language": props.get("detected_language"),
                    "is_another_language": props.get("is_another_language"),
                    "core_keyword": props.get("core_keyword"),
                    "synonym_clustering_algorithm": props.get("synonym_clustering_algorithm")
                })
            
            if "avg_backlinks_info" in seed_data:
                seed_keyword_record["backlinks_info"] = seed_data["avg_backlinks_info"]
            if "serp_info" in seed_data:
                seed_keyword_record["serp_info"] = seed_data["serp_info"]
            if "search_intent_info" in seed_data:
                search_intent = seed_data["search_intent_info"]
                seed_keyword_record["main_intent"] = search_intent.get("main_intent")
        
        # Upsert seed keyword
        existing = supabase.table("keywords").select("id").eq("keyword", data.keyword).eq("location_code", data.location_code).eq("language_code", data.language_code).execute()
        
        if existing.data:
            seed_keyword_id = existing.data[0]["id"]
            supabase.table("keywords").update(seed_keyword_record).eq("id", seed_keyword_id).execute()
            logger.info(f"🔄 Updated seed keyword: {data.keyword}")
        else:
            result = supabase.table("keywords").insert(seed_keyword_record).execute()
            seed_keyword_id = result.data[0]["id"]
            logger.info(f"✅ Created seed keyword: {data.keyword}")
        
        # Parse ALL related keywords (NO LIMIT!)
        related_keywords = []
        relations_created = 0
        
        for item in items:
            # Skip seed keyword (depth == 0) as it's already processed
            if item.get("depth") == 0:
                continue
            
            # Get real keyword from keyword_data.keyword or item.keyword
            keyword_text = None
            keyword_data = item.get("keyword_data", {})
            
            if keyword_data.get("keyword"):
                keyword_text = keyword_data["keyword"]
            elif item.get("keyword"):
                keyword_text = item["keyword"]
            
            if not keyword_text or keyword_text.lower() == data.keyword.lower():
                continue
            
            related_record = {
                "keyword": keyword_text, "location_code": data.location_code, "language_code": data.language_code,
                "depth": item.get("depth", 0), "is_suggestion": False, "seed_keyword": data.keyword
            }
            
            # Extract keyword info - WSZYSTKIE POLA
            if "keyword_info" in keyword_data:
                kw_info = keyword_data["keyword_info"]
                related_record.update({
                    "search_volume": kw_info.get("search_volume"),
                    "competition": kw_info.get("competition"),
                    "competition_level": kw_info.get("competition_level"),
                    "cpc": kw_info.get("cpc"),
                    "categories": kw_info.get("categories", []),
                    "monthly_searches": kw_info.get("monthly_searches", []),
                    "search_volume_trend": kw_info.get("search_volume_trend", {}),
                    "low_top_of_page_bid": kw_info.get("low_top_of_page_bid"),
                    "high_top_of_page_bid": kw_info.get("high_top_of_page_bid")
                })
            
            # Extract keyword_properties - WSZYSTKIE POLA
            if "keyword_properties" in keyword_data:
                props = keyword_data["keyword_properties"]
                related_record.update({
                    "keyword_difficulty": props.get("keyword_difficulty"),
                    "detected_language": props.get("detected_language"),
                    "is_another_language": props.get("is_another_language"),
                    "core_keyword": props.get("core_keyword"),
                    "synonym_clustering_algorithm": props.get("synonym_clustering_algorithm")
                })
            
            # Extract dodatkowo serp_info, avg_backlinks_info, search_intent_info
            if "serp_info" in keyword_data:
                related_record["serp_info"] = keyword_data["serp_info"]
            if "avg_backlinks_info" in keyword_data:
                related_record["backlinks_info"] = keyword_data["avg_backlinks_info"]
            if "search_intent_info" in keyword_data:
                search_intent = keyword_data["search_intent_info"]
                related_record["main_intent"] = search_intent.get("main_intent")
            
            # Check if related keyword exists
            existing_related = supabase.table("keywords").select("id").eq("keyword", keyword_text).eq("location_code", data.location_code).execute()
            
            if existing_related.data:
                related_id = existing_related.data[0]["id"]
                logger.info(f"🔄 Related keyword exists: {keyword_text}")
            else:
                try:
                    result = supabase.table("keywords").insert(related_record).execute()
                    related_id = result.data[0]["id"]
                    logger.info(f"✅ Created related keyword: {keyword_text}")
                except Exception as e:
                    logger.warning(f"⚠️ Error creating related keyword {keyword_text}: {str(e)}")
                    continue
            
            # Create relation
            try:
                relation = {
                    "parent_keyword_id": seed_keyword_id, "related_keyword_id": related_id,
                    "depth": item.get("depth", 0), "relationship_type": "related",
                    "search_volume": related_record.get("search_volume")
                }
                supabase.table("keyword_relations").insert(relation).execute()
                relations_created += 1
            except Exception as e:
                logger.warning(f"⚠️ Error creating relation for {keyword_text}: {str(e)}")
            
            related_keywords.append({
                "keyword": keyword_text,
                "search_volume": related_record.get("search_volume"),
                "depth": item.get("depth", 0)
            })
        
        # Process deeper levels (depth 2+) from related_keywords arrays
        logger.info("🔗 Processing deeper levels (depth 2+)")
        deeper_relations_created = 0
        
        for item in items:
            current_depth = item.get("depth", 0)
            if current_depth == 0:  # Skip seed keyword
                continue
            
            # Znajdź ID tego keyword w bazie
            current_keyword = item.get("keyword_data", {}).get("keyword")
            if not current_keyword:
                continue
                
            current_keyword_record = supabase.table("keywords").select("id").eq("keyword", current_keyword).eq("location_code", data.location_code).execute()
            if not current_keyword_record.data:
                continue
                
            current_keyword_id = current_keyword_record.data[0]["id"]
            
            # Przetwórz jego related_keywords jako kolejny poziom
            deeper_keywords = item.get("related_keywords") or []
            logger.info(f"🔍 Processing {len(deeper_keywords)} deeper keywords for '{current_keyword}' (depth {current_depth})")
            
            for deeper_keyword_text in deeper_keywords:
                if not deeper_keyword_text or deeper_keyword_text.lower() == data.keyword.lower():
                    continue
                    
                # Sprawdź czy już istnieje
                existing_deeper = supabase.table("keywords").select("id").eq("keyword", deeper_keyword_text).eq("location_code", data.location_code).execute()
                
                if existing_deeper.data:
                    deeper_keyword_id = existing_deeper.data[0]["id"]
                    logger.info(f"🔄 Deeper keyword exists: {deeper_keyword_text}")
                else:
                    # Utwórz nowy rekord (minimal data, bo nie mamy pełnych info z API)
                    deeper_record = {
                        "keyword": deeper_keyword_text,
                        "location_code": data.location_code,
                        "language_code": data.language_code,
                        "depth": current_depth + 1,
                        "is_suggestion": False,
                        "seed_keyword": data.keyword
                    }
                    
                    try:
                        result = supabase.table("keywords").insert(deeper_record).execute()
                        deeper_keyword_id = result.data[0]["id"]
                        logger.info(f"✅ Created deeper keyword (depth {current_depth + 1}): {deeper_keyword_text}")
                    except Exception as e:
                        logger.warning(f"⚠️ Error creating deeper keyword {deeper_keyword_text}: {str(e)}")
                        continue
                
                # Utwórz relację
                try:
                    relation = {
                        "parent_keyword_id": current_keyword_id,
                        "related_keyword_id": deeper_keyword_id,
                        "depth": current_depth + 1,
                        "relationship_type": "related"
                    }
                    supabase.table("keyword_relations").insert(relation).execute()
                    deeper_relations_created += 1
                    logger.info(f"✅ Created deeper relation: {current_keyword} -> {deeper_keyword_text}")
                except Exception as e:
                    logger.warning(f"⚠️ Error creating deeper relation for {deeper_keyword_text}: {str(e)}")
        
        logger.info(f"🎯 Total deeper relations created: {deeper_relations_created}")
        
        return {
            "success": True, "seed_keyword_id": seed_keyword_id, "keyword": data.keyword,
            "cost_usd": related_response.get("cost", 0),
            "seed_data": {
                "search_volume": seed_keyword_record.get("search_volume"),
                "competition": seed_keyword_record.get("competition"),
                "keyword_difficulty": seed_keyword_record.get("keyword_difficulty")
            },
            "related_keywords": related_keywords, "relations_created": relations_created,
            "deeper_relations_created": deeper_relations_created,
            "total_related_found": len(items), "raw_response": related_response
        }
        
    except Exception as e:
        logger.exception(f"❌ Related keywords analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Related keywords analysis failed: {str(e)}")

@router.post("/analyze-historical-only")
async def analyze_historical_only(data: KeywordAnalysisInput):
    """📅 Historical API only - saves ALL months"""
    
    if not all([DFS_LOGIN, DFS_PASSWORD, SUPABASE_URL, SUPABASE_KEY]):
        raise HTTPException(status_code=500, detail="Missing API credentials")
    
    dfs_client = DataForSEOClient()
    
    try:
        historical_response = await dfs_client.get_historical_data([data.keyword], data.location_code, data.language_code)
        
        if not historical_response.get("data"):
            raise HTTPException(status_code=404, detail="No historical data found")
        
        # Find keyword in database
        existing = supabase.table("keywords").select("id").eq("keyword", data.keyword).eq("location_code", data.location_code).eq("language_code", data.language_code).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Keyword not found in database. Run related-keywords analysis first.")
        
        keyword_id = existing.data[0]["id"]
        
        # Parse historical data - ALL MONTHS
        historical_data = historical_response["data"]
        items = historical_data.get("items", [])
        historical_records = []
        
        for item in items:
            if item.get("keyword") != data.keyword:
                continue
                
            history = item.get("history", [])
            
            for hist_item in history:
                keyword_info = hist_item.get("keyword_info", {})
                
                hist_record = {
                    "keyword_id": keyword_id,
                    "year": hist_item.get("year"),
                    "month": hist_item.get("month"),
                    "search_volume": keyword_info.get("search_volume"),
                    "competition": keyword_info.get("competition"),
                    "competition_level": keyword_info.get("competition_level"),
                    "cpc": keyword_info.get("cpc"),
                    "low_top_of_page_bid": keyword_info.get("low_top_of_page_bid"),
                    "high_top_of_page_bid": keyword_info.get("high_top_of_page_bid"),
                    "categories": keyword_info.get("categories", []),
                    "monthly_searches": keyword_info.get("monthly_searches", []),
                    "search_volume_trend": keyword_info.get("search_volume_trend", {})
                }
                
                # Upsert historical record
                existing_hist = supabase.table("keyword_historical_data").select("id").eq("keyword_id", keyword_id).eq("year", hist_item.get("year")).eq("month", hist_item.get("month")).execute()
                
                if existing_hist.data:
                    supabase.table("keyword_historical_data").update(hist_record).eq("id", existing_hist.data[0]["id"]).execute()
                    logger.info(f"🔄 Updated historical: {hist_item.get('year')}-{hist_item.get('month')}")
                else:
                    supabase.table("keyword_historical_data").insert(hist_record).execute()
                    logger.info(f"✅ Created historical: {hist_item.get('year')}-{hist_item.get('month')}")
                
                historical_records.append({
                    "year": hist_item.get("year"),
                    "month": hist_item.get("month"),
                    "search_volume": keyword_info.get("search_volume")
                })
        
        return {
            "success": True, "keyword_id": keyword_id, "keyword": data.keyword,
            "cost_usd": historical_response.get("cost", 0),
            "historical_records": len(historical_records),
            "data": historical_records, "raw_response": historical_response
        }
        
    except Exception as e:
        logger.exception(f"❌ Historical analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Historical analysis failed: {str(e)}")

@router.post("/analyze-suggestions-only")
async def analyze_suggestions_only(data: KeywordAnalysisInput):
    """💡 Keyword Suggestions API only - saves ALL suggestions"""
    
    if not all([DFS_LOGIN, DFS_PASSWORD, SUPABASE_URL, SUPABASE_KEY]):
        raise HTTPException(status_code=500, detail="Missing API credentials")
    
    dfs_client = DataForSEOClient()
    
    try:
        suggestions_response = await dfs_client.get_keyword_suggestions(data.keyword, data.location_code, data.language_code)
        
        if not suggestions_response.get("data"):
            raise HTTPException(status_code=404, detail="No suggestions found")
        
        # Find parent keyword
        existing = supabase.table("keywords").select("id").eq("keyword", data.keyword).eq("location_code", data.location_code).eq("language_code", data.language_code).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Parent keyword not found. Run related-keywords analysis first.")
        
        parent_keyword_id = existing.data[0]["id"]
        
        # Parse ALL suggestions (NO LIMIT!)
        suggestions_data = suggestions_response["data"]
        items = suggestions_data.get("items", [])
        suggestions_created = []
        relations_created = 0
        
        for item in items:
            suggestion_keyword = item.get("keyword")
            
            if not suggestion_keyword or suggestion_keyword.lower() == data.keyword.lower():
                continue
            
            suggestion_record = {
                "keyword": suggestion_keyword, "location_code": data.location_code, "language_code": data.language_code,
                "is_suggestion": True, "parent_keyword_id": parent_keyword_id, "seed_keyword": data.keyword
            }
            
            # Extract keyword info - WSZYSTKIE POLA
            keyword_info = item.get("keyword_info", {})
            suggestion_record.update({
                "search_volume": keyword_info.get("search_volume"),
                "competition": keyword_info.get("competition"),
                "competition_level": keyword_info.get("competition_level"),
                "cpc": keyword_info.get("cpc"),
                "categories": keyword_info.get("categories", []),
                "monthly_searches": keyword_info.get("monthly_searches", []),
                "search_volume_trend": keyword_info.get("search_volume_trend", {}),
                "low_top_of_page_bid": keyword_info.get("low_top_of_page_bid"),
                "high_top_of_page_bid": keyword_info.get("high_top_of_page_bid")
            })
            
            # Extract keyword_properties - WSZYSTKIE POLA
            if "keyword_properties" in item:
                props = item["keyword_properties"]
                suggestion_record.update({
                    "keyword_difficulty": props.get("keyword_difficulty"),
                    "detected_language": props.get("detected_language"),
                    "is_another_language": props.get("is_another_language"),
                    "core_keyword": props.get("core_keyword"),
                    "synonym_clustering_algorithm": props.get("synonym_clustering_algorithm")
                })
            
            # Extract backlinks_info
            if "avg_backlinks_info" in item:
                suggestion_record["backlinks_info"] = item["avg_backlinks_info"]
            
            # Extract search_intent_info
            if "search_intent_info" in item:
                search_intent = item["search_intent_info"]
                suggestion_record["main_intent"] = search_intent.get("main_intent")
            
            # Check if keyword exists as suggestion
            existing_suggestion = supabase.table("keywords").select("id").eq("keyword", suggestion_keyword).eq("location_code", data.location_code).eq("is_suggestion", True).execute()
            
            # Check if keyword exists at all (regardless of is_suggestion)
            existing_keyword = supabase.table("keywords").select("id").eq("keyword", suggestion_keyword).eq("location_code", data.location_code).execute()
            
            # Decision logic for keyword ID
            if existing_suggestion.data:
                # Keyword exists as suggestion → use existing ID and update with full data
                suggestion_id = existing_suggestion.data[0]["id"]
                try:
                    supabase.table("keywords").update(suggestion_record).eq("id", suggestion_id).execute()
                    logger.info(f"🔄 Updated existing suggestion with full data: {suggestion_keyword}")
                except Exception as e:
                    logger.warning(f"⚠️ Error updating existing suggestion {suggestion_keyword}: {str(e)}")
            elif existing_keyword.data:
                # Keyword exists as related → use existing ID and update with full data
                suggestion_id = existing_keyword.data[0]["id"]
                try:
                    supabase.table("keywords").update(suggestion_record).eq("id", suggestion_id).execute()
                    logger.info(f"🔄 Updated existing keyword with suggestion data: {suggestion_keyword}")
                except Exception as e:
                    logger.warning(f"⚠️ Error updating existing keyword {suggestion_keyword}: {str(e)}")
            else:
                # Keyword doesn't exist → create new
                try:
                    result = supabase.table("keywords").insert(suggestion_record).execute()
                    suggestion_id = result.data[0]["id"]
                    logger.info(f"✅ Created suggestion: {suggestion_keyword}")
                except Exception as e:
                    logger.warning(f"⚠️ Error creating suggestion {suggestion_keyword}: {str(e)}")
                    continue
            
            # Check if relation already exists
            existing_relation = supabase.table("keyword_relations").select("id").eq("parent_keyword_id", parent_keyword_id).eq("related_keyword_id", suggestion_id).eq("relationship_type", "suggestion").execute()
            
            if existing_relation.data:
                logger.info(f"🔄 Suggestion relation already exists: {suggestion_keyword}")
            else:
                # Create suggestion relation
                try:
                    relation = {
                        "parent_keyword_id": parent_keyword_id, "related_keyword_id": suggestion_id,
                        "depth": 0, "relationship_type": "suggestion", "relevance_score": 1.0,
                        "search_volume": suggestion_record.get("search_volume")
                    }
                    supabase.table("keyword_relations").insert(relation).execute()
                    relations_created += 1
                    logger.info(f"✅ Created suggestion relation: {suggestion_keyword}")
                except Exception as e:
                    logger.warning(f"⚠️ Error creating relation for suggestion {suggestion_keyword}: {str(e)}")
            
            suggestions_created.append({
                "keyword": suggestion_keyword,
                "search_volume": suggestion_record.get("search_volume")
            })
        
        return {
            "success": True, "parent_keyword_id": parent_keyword_id, "keyword": data.keyword,
            "cost_usd": suggestions_response.get("cost", 0),
            "suggestions": suggestions_created, "relations_created": relations_created,
            "total_suggestions_found": len(items), "raw_response": suggestions_response
        }
        
    except Exception as e:
        logger.exception(f"❌ Suggestions analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Suggestions analysis failed: {str(e)}")

@router.post("/analyze-trends-only")
async def analyze_trends_only(data: KeywordAnalysisInput):
    """📈 DataForSEO Trends API only - trends_graph, subregion_interests, demography"""
    
    if not all([DFS_LOGIN, DFS_PASSWORD, SUPABASE_URL, SUPABASE_KEY]):
        raise HTTPException(status_code=500, detail="Missing API credentials")
    
    dfs_client = DataForSEOClient()
    
    try:
        trends_response = await dfs_client.get_dataforseo_trends([data.keyword], data.location_code, data.language_code)
        
        if not trends_response.get("data"):
            raise HTTPException(status_code=404, detail="No trends data found")
        
        logger.info(f"🔍 Trends response structure: {list(trends_response.keys())}")
        logger.info(f"🔍 Trends data items count: {len(trends_response.get('data', {}).get('items', []))}")
        
        # Find keyword in database
        existing = supabase.table("keywords").select("id").eq("keyword", data.keyword).eq("location_code", data.location_code).eq("language_code", data.language_code).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Keyword not found. Run related-keywords analysis first.")
        
        keyword_id = existing.data[0]["id"]
        
        # Parse trends data
        trends_data = trends_response["data"]
        items = trends_data.get("items", [])
        
        trends_record = {
            "data_sources": ["df_trends"],
            "api_costs_total": trends_response.get("cost", 0),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        for item in items:
            item_type = item.get("type")
            
            if item_type == "dataforseo_trends_graph":
                trends_record["trends_graph"] = item.get("data", [])
            
            elif item_type == "subregion_interests":
                interests = item.get("interests", [])
                if interests:
                    geo_data = []
                    for interest in interests:
                        values = interest.get("values") or []
                        if values:  # Sprawdź czy values nie jest None
                            for value in values:
                                geo_data.append({
                                    "geo_id": value.get("geo_id"),
                                    "geo_name": value.get("geo_name"),
                                    "value": value.get("value")
                                })
                    trends_record["subregion_interests"] = geo_data
            
            elif item_type == "demography":
                demo = item.get("demography", {})
                
                # Age distribution
                age_data = demo.get("age", [])
                for age_item in age_data:
                    if age_item.get("keyword") == data.keyword:
                        values = age_item.get("values", [])
                        if values:  # Sprawdź czy values nie jest None lub puste
                            for val in values:
                                age_type = val.get("type")
                                age_value = val.get("value")
                                if age_type == "18-24":
                                    trends_record["age_18_24"] = age_value
                                elif age_type == "25-34":
                                    trends_record["age_25_34"] = age_value
                                elif age_type == "35-44":
                                    trends_record["age_35_44"] = age_value
                                elif age_type == "45-54":
                                    trends_record["age_45_54"] = age_value
                                elif age_type == "55-64":
                                    trends_record["age_55_64"] = age_value
                
                # Gender distribution
                gender_data = demo.get("gender", [])
                for gender_item in gender_data:
                    if gender_item.get("keyword") == data.keyword:
                        values = gender_item.get("values", [])
                        if values:  # Sprawdź czy values nie jest None
                            for val in values:
                                gender_type = val.get("type")
                                gender_value = val.get("value")
                                if gender_type == "female":
                                    trends_record["gender_female"] = gender_value
                                elif gender_type == "male":
                                    trends_record["gender_male"] = gender_value
        
        # Update keyword with trends data
        supabase.table("keywords").update(trends_record).eq("id", keyword_id).execute()
        logger.info(f"✅ Updated keyword with trends data: {data.keyword}")
        
        return {
            "success": True, "keyword_id": keyword_id, "keyword": data.keyword,
            "cost_usd": trends_response.get("cost", 0),
            "trends_data": {
                "has_graph": "trends_graph" in trends_record,
                "has_geo": "subregion_interests" in trends_record,
                "has_demographics": any(k.startswith(("age_", "gender_")) for k in trends_record.keys())
            },
            "raw_response": trends_response
        }
        
    except Exception as e:
        logger.exception(f"❌ Trends analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Trends analysis failed: {str(e)}")

@router.post("/analyze-gt-explore-only")
async def analyze_gt_explore_only(data: KeywordAnalysisInput):
    """🌍 Google Trends Explore API only - topics, queries, trends_map, trends_graph"""
    
    if not all([DFS_LOGIN, DFS_PASSWORD, SUPABASE_URL, SUPABASE_KEY]):
        raise HTTPException(status_code=500, detail="Missing API credentials")
    
    dfs_client = DataForSEOClient()
    
    try:
        gt_response = await dfs_client.get_google_trends_explore([data.keyword], data.location_code, data.language_code)
        
        if not gt_response.get("data"):
            raise HTTPException(status_code=404, detail="No Google Trends data found")
        
        # Find keyword in database
        existing = supabase.table("keywords").select("id, data_sources").eq("keyword", data.keyword).eq("location_code", data.location_code).eq("language_code", data.language_code).execute()
        
        if not existing.data:
            raise HTTPException(status_code=404, detail="Keyword not found. Run related-keywords analysis first.")
        
        keyword_id = existing.data[0]["id"]
        existing_sources = existing.data[0].get("data_sources", [])
        
        # Parse GT Explore data
        gt_data = gt_response["data"]
        items = gt_data.get("items", [])
        
        update_record = {
            "data_sources": list(set(existing_sources + ["gt_explore"])),
            "api_costs_total": gt_response.get("cost", 0),
            "last_updated": datetime.utcnow().isoformat()
        }
        
        # Parse different item types
        for item in items:
            item_type = item.get("type")
            
            if item_type == "google_trends_graph":
                # Save trends_graph (czasowy wykres trendów)
                update_record["trends_graph"] = item.get("data", [])
                logger.info(f"📈 Saved trends_graph with {len(item.get('data', []))} data points")
            
            elif item_type == "google_trends_map":
                # Save trends_map (dane geograficzne)
                map_data = item.get("data", [])
                if map_data:
                    geo_data = []
                    for location in map_data:
                        geo_data.append({
                            "geo_id": location.get("geo_id"),
                            "geo_name": location.get("geo_name"),
                            "values": location.get("values", [])
                        })
                    update_record["trends_map"] = geo_data
                    logger.info(f"🗺️ Saved trends_map with {len(geo_data)} locations")
            
            elif item_type == "google_trends_topics_list":
                # Save topics_list (powiązane tematy)
                topics_data = {
                    "top": item.get("data", {}).get("top", []),
                    "rising": item.get("data", {}).get("rising", [])
                }
                update_record["topics_list"] = topics_data
                logger.info(f"🏷️ Saved topics_list: {len(topics_data['top'])} top, {len(topics_data['rising'])} rising")
            
            elif item_type == "google_trends_queries_list":
                # Save queries_list (powiązane zapytania)
                queries_data = {
                    "top": item.get("data", {}).get("top", []),
                    "rising": item.get("data", {}).get("rising", [])
                }
                update_record["queries_list"] = queries_data
                logger.info(f"🔍 Saved queries_list: {len(queries_data['top'])} top, {len(queries_data['rising'])} rising")
        
        # Update keyword with GT Explore data
        supabase.table("keywords").update(update_record).eq("id", keyword_id).execute()
        logger.info(f"✅ Updated keyword with GT Explore data: {data.keyword}")
        
        return {
            "success": True, "keyword_id": keyword_id, "keyword": data.keyword,
            "cost_usd": gt_response.get("cost", 0),
            "gt_data": {
                "has_trends_graph": "trends_graph" in update_record,
                "has_trends_map": "trends_map" in update_record,
                "has_topics": "topics_list" in update_record,
                "has_queries": "queries_list" in update_record,
                "total_items": len(items)
            },
            "raw_response": gt_response
        }
        
    except Exception as e:
        logger.exception(f"❌ GT Explore analysis failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"GT Explore analysis failed: {str(e)}")

# ========================================
# READING ENDPOINTS
# ========================================

@router.get("/keyword-complete/{keyword}")
async def get_keyword_complete(keyword: str, location_code: int = 2616, language_code: str = "pl"):
    """Get COMPLETE keyword data - everything in one response"""
    
    try:
        # 1. Find main keyword
        main_keyword = supabase.table("keywords").select("*").eq("keyword", keyword).eq("location_code", location_code).eq("language_code", language_code).execute()
        
        if not main_keyword.data:
            raise HTTPException(status_code=404, detail=f"Keyword '{keyword}' not found in database")
        
        keyword_data = main_keyword.data[0]
        keyword_id = keyword_data["id"]
        
        # 2. Get all related keywords and suggestions
        related_keywords_query = supabase.table("keyword_relations").select("""
            *,
            related_keyword:related_keyword_id(
                id, keyword, search_volume, competition, cpc, keyword_difficulty, main_intent
            )
        """).eq("parent_keyword_id", keyword_id).execute()
        
        # Split into related and suggestions
        related_keywords = []
        suggestions = []
        
        for relation in related_keywords_query.data:
            rel_data = {
                "keyword": relation["related_keyword"]["keyword"],
                "search_volume": relation["related_keyword"]["search_volume"],
                "competition": relation["related_keyword"]["competition"],
                "depth": relation["depth"],
                "relationship_type": relation["relationship_type"]
            }
            
            if relation["relationship_type"] == "suggestion":
                suggestions.append(rel_data)
            else:
                related_keywords.append(rel_data)
        
        # 3. Get historical data
        historical_data = supabase.table("keyword_historical_data").select("*").eq("keyword_id", keyword_id).order("year.desc,month.desc").execute()
        
        # 4. Calculate statistics
        stats = {
            "total_related_keywords": len(related_keywords),
            "total_suggestions": len(suggestions),
            "total_historical_months": len(historical_data.data),
            "data_sources": keyword_data.get("data_sources", []),
            "api_costs_total": keyword_data.get("api_costs_total", 0),
            "last_updated": keyword_data.get("last_updated")
        }
        
        # 5. Trends availability
        trends_data = {
            "has_trends_graph": bool(keyword_data.get("trends_graph")),
            "has_demographics": any(keyword_data.get(f"age_{age}") for age in ["18_24", "25_34", "35_44", "45_54", "55_64"]),
            "has_gender_data": bool(keyword_data.get("gender_female") or keyword_data.get("gender_male")),
            "has_geo_data": bool(keyword_data.get("subregion_interests"))
        }
        
        # 6. Recent 12 months search volume
        recent_months = []
        if historical_data.data:
            for month_data in historical_data.data[:12]:
                recent_months.append({
                    "year": month_data["year"],
                    "month": month_data["month"],
                    "search_volume": month_data["search_volume"]
                })
        
        return {
            "success": True,
            "keyword": keyword,
            "main_data": {
                "id": keyword_id,
                "keyword": keyword_data["keyword"],
                "search_volume": keyword_data["search_volume"],
                "competition": keyword_data["competition"],
                "competition_level": keyword_data["competition_level"],
                "cpc": keyword_data["cpc"],
                "keyword_difficulty": keyword_data["keyword_difficulty"],
                "main_intent": keyword_data["main_intent"],
                "intent_probability": keyword_data["intent_probability"],
                "categories": keyword_data["categories"]
            },
            "demographics": {
                "gender_female": keyword_data.get("gender_female"),
                "gender_male": keyword_data.get("gender_male"),
                "age_18_24": keyword_data.get("age_18_24"),
                "age_25_34": keyword_data.get("age_25_34"),
                "age_35_44": keyword_data.get("age_35_44"),
                "age_45_54": keyword_data.get("age_45_54"),
                "age_55_64": keyword_data.get("age_55_64")
            },
            "related_keywords": related_keywords,
            "suggestions": suggestions,
            "recent_historical": recent_months,
            "trends_data": trends_data,
            "stats": stats
        }
        
    except Exception as e:
        logger.exception(f"❌ Error fetching complete keyword data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching keyword data: {str(e)}")

@router.get("/keyword-tree/{keyword}")
async def get_keyword_tree(keyword: str, location_code: int = 2616, language_code: str = "pl"):
    """Show keyword relationship tree - visualization of connections"""
    
    try:
        # Find main keyword
        main_keyword = supabase.table("keywords").select("id, keyword, search_volume").eq("keyword", keyword).eq("location_code", location_code).eq("language_code", language_code).execute()
        
        if not main_keyword.data:
            raise HTTPException(status_code=404, detail=f"Keyword '{keyword}' not found")
        
        keyword_id = main_keyword.data[0]["id"]
        
        # Get all relations with depth
        relations = supabase.table("keyword_relations").select("""
            depth, relationship_type,
            related_keyword:related_keyword_id(keyword, search_volume)
        """).eq("parent_keyword_id", keyword_id).order("depth.asc,related_keyword(search_volume).desc").execute()
        
        # Organize by depth
        tree = {
            "root": {
                "keyword": keyword,
                "search_volume": main_keyword.data[0]["search_volume"],
                "depth": 0
            },
            "suggestions": [],  # depth = 0
            "related_depth_1": [],
            "related_depth_2": [],
            "related_depth_3": [],
            "related_depth_4": []
        }
        
        for relation in relations.data:
            item = {
                "keyword": relation["related_keyword"]["keyword"],
                "search_volume": relation["related_keyword"]["search_volume"],
                "type": relation["relationship_type"]
            }
            
            if relation["relationship_type"] == "suggestion":
                tree["suggestions"].append(item)
            else:
                depth = relation["depth"]
                if depth == 1:
                    tree["related_depth_1"].append(item)
                elif depth == 2:
                    tree["related_depth_2"].append(item)
                elif depth == 3:
                    tree["related_depth_3"].append(item)
                elif depth == 4:
                    tree["related_depth_4"].append(item)
        
        return {
            "success": True,
            "keyword": keyword,
            "tree": tree,
            "summary": {
                "total_suggestions": len(tree["suggestions"]),
                "total_related_depth_1": len(tree["related_depth_1"]),
                "total_related_depth_2": len(tree["related_depth_2"]),
                "total_related_depth_3": len(tree["related_depth_3"]),
                "total_related_depth_4": len(tree["related_depth_4"])
            }
        }
        
    except Exception as e:
        logger.exception(f"❌ Error fetching keyword tree: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching keyword tree: {str(e)}")

# ========================================
# TEST ENDPOINTS
# ========================================

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
        historical_count = supabase.table("keyword_historical_data").select("id", count="exact").execute()
        
        return {
            "total_keywords": keywords_count.count,
            "total_relations": relations_count.count,
            "total_historical_records": historical_count.count
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@router.post("/test-single-endpoint")
async def test_single_endpoint(endpoint: str, keyword: str):
    """Test individual endpoint - for debugging"""
    dfs_client = DataForSEOClient()
    
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
        elif endpoint == "gt_explore":
            result = await dfs_client.get_google_trends_explore([keyword], 2616, "pl")
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