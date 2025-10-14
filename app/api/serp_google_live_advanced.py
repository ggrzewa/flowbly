import os
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from dataforseo_client import configuration as dfs_config, api_client as dfs_api_provider
from dataforseo_client.api.serp_api import SerpApi
from dataforseo_client.models.serp_google_organic_live_advanced_request_info import (
    SerpGoogleOrganicLiveAdvancedRequestInfo,
)
from supabase import create_client, Client
import json
import re

# ========================================
# ENVIRONMENT SETUP
# ========================================
load_dotenv()
router = APIRouter()

# Logger setup
logger = logging.getLogger("serp_parser_complete")
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
class SerpOrganicInput(BaseModel):
    keyword: str
    location_code: Optional[int] = 2616  # Poland
    language_code: Optional[str] = "pl"
    device: Optional[str] = "desktop"
    os: Optional[str] = "windows"
    depth: Optional[int] = 100
    calculate_rectangles: Optional[bool] = False
    group_organic_results: Optional[bool] = True

# ========================================
# PARSING FUNCTIONS
# ========================================
class SerpDataParser:
    
    @staticmethod
    def parse_relative_time(date_string: str) -> Optional[int]:
        """Parse relative time like '20 godzin temu' -> 20"""
        if not date_string:
            return None
            
        patterns = [
            (r'(\d+)\s*godzin', 1),      # "20 godzin temu" -> 20
            (r'(\d+)\s*godziny', 1),     # "2 godziny temu" -> 2  
            (r'(\d+)\s*godz', 1),        # "3 godz temu" -> 3
            (r'dzień\s*temu', 24),       # "dzień temu" -> 24
            (r'(\d+)\s*dni', 24),        # "3 dni temu" -> 72
            (r'(\d+)\s*dzień', 24),      # "1 dzień temu" -> 24
            (r'wczoraj', 24),            # "wczoraj" -> 24
            (r'(\d+)\s*hour', 1),        # English: "20 hours ago"
            (r'(\d+)\s*day', 24),        # English: "3 days ago"
        ]
        
        for pattern, multiplier in patterns:
            match = re.search(pattern, date_string.lower())
            if match:
                if match.groups():
                    return int(match.group(1)) * multiplier
                else:
                    return multiplier
        return None

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
        """Calculate hours since SERP was retrieved"""
        try:
            serp_date = datetime.fromisoformat(datetime_str.replace(' +00:00', ''))
            now = datetime.utcnow()
            return int((now - serp_date).total_seconds() / 3600)
        except:
            return 0

    @staticmethod
    async def lookup_keyword_id(keyword: str, location_code: int, language_code: str) -> str:
        """Find or create keyword ID in keywords table"""
        try:
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
                "data_sources": ["serp"],
                "last_updated": datetime.utcnow().isoformat()
            }
            
            result = supabase.table("keywords").insert(keyword_record).execute()
            logger.info(f"✅ Created new keyword: {keyword}")
            return result.data[0]["id"]
            
        except Exception as e:
            logger.error(f"❌ Error looking up keyword: {str(e)}")
            raise

# ========================================
# MAIN SERP PROCESSOR
# ========================================
class SerpProcessor:
    
    def __init__(self):
        self.parser = SerpDataParser()
    
    async def process_serp_response(self, serp_response: Dict, input_data: SerpOrganicInput) -> Dict:
        """Process complete SERP response and save to database"""
        try:
            result = serp_response["result"]
            task_info = serp_response["task_info"]
            
            logger.info(f"🔄 Processing SERP for keyword: {result['keyword']}")
            logger.info(f"📊 SERP zawiera typy: {result.get('item_types', [])}")
            logger.info(f"📊 Elementy do przetworzenia: {len(result.get('items', []))}")
            
            # 1. LOOKUP/CREATE keyword_id
            keyword_id = await self.parser.lookup_keyword_id(
                result["keyword"], 
                result["location_code"], 
                result["language_code"]
            )
            
            # 2. INSERT/UPDATE serp_results
            serp_result_id = await self.insert_serp_result(result, task_info, keyword_id, input_data)
            
            # 3. PROCESS all items
            items_processed = 0
            for item in result.get("items", []):
                try:
                    await self.process_item(item, serp_result_id, result)
                    items_processed += 1
                except Exception as e:
                    logger.warning(f"⚠️ Error processing item: {str(e)}")
                    continue
            
            logger.info(f"✅ Processed {items_processed}/{len(result.get('items', []))} SERP items")
            
            return {
                "success": True,
                "serp_result_id": serp_result_id,
                "keyword": result["keyword"],
                "items_processed": items_processed,
                "total_items": len(result.get("items", [])),
                "cost_usd": task_info.get("cost", 0)
            }
            
        except Exception as e:
            logger.exception(f"❌ Error processing SERP response: {str(e)}")
            raise

    async def insert_serp_result(self, result: Dict, task_info: Dict, keyword_id: str, input_data: SerpOrganicInput) -> str:
        """Insert main SERP result record"""
        try:
            serp_record = {
                "keyword_id": keyword_id,
                "keyword": result["keyword"],
                "location_code": result["location_code"],
                "language_code": result["language_code"],
                "se_domain": result["se_domain"],
                "device": input_data.device,
                "os": input_data.os,
                "check_url": result["check_url"],
                "datetime": result["datetime"],
                "se_results_count": result["se_results_count"],
                "items_count": result["items_count"],
                "item_types": result.get("item_types", []),
                "spell_correction": json.dumps(result.get("spell")) if result.get("spell") else None,
                "refinement_chips": json.dumps(result.get("refinement_chips")) if result.get("refinement_chips") else None,
                "api_cost": task_info.get("cost", 0),
                "execution_time": self.parser.parse_execution_time(task_info.get("execution_time", "")),
                "data_freshness_hours": self.parser.calculate_freshness_hours(result["datetime"])
            }
            
            # Check for existing SERP result (unique constraint)
            existing = supabase.table("serp_results").select("id").eq("keyword_id", keyword_id).eq("location_code", result["location_code"]).eq("language_code", result["language_code"]).eq("device", input_data.device).eq("se_domain", result["se_domain"]).execute()
            
            if existing.data:
                # Update existing
                serp_result_id = existing.data[0]["id"]
                serp_record["updated_at"] = datetime.utcnow().isoformat()
                supabase.table("serp_results").update(serp_record).eq("id", serp_result_id).execute()
                logger.info(f"🔄 Updated existing SERP result: {serp_result_id}")
            else:
                # Insert new
                serp_record["created_at"] = datetime.utcnow().isoformat()
                result_insert = supabase.table("serp_results").insert(serp_record).execute()
                serp_result_id = result_insert.data[0]["id"]
                logger.info(f"✅ Created new SERP result: {serp_result_id}")
            
            return serp_result_id
            
        except Exception as e:
            logger.error(f"❌ Error inserting SERP result: {str(e)}")
            raise

    async def process_item(self, item: Dict, serp_result_id: str, result: Dict) -> str:
        """Process individual SERP item"""
        try:
            # Dodaj logowanie na początku
            item_type = item.get("type")
            logger.debug(f"🔄 Przetwarzam element: {item_type} (pozycja {item.get('rank_absolute', 'N/A')})")
            
            # Specjalne logowanie dla AI overview
            if item_type == "ai_overview":
                logger.info(f"🤖 ZNALEZIONO AI OVERVIEW! Pozycja: {item.get('rank_absolute', 'N/A')}")
                if item.get("references"):
                    logger.info(f"🤖 AI Overview ma {len(item['references'])} references")
                else:
                    logger.info(f"🤖 AI Overview BEZ references - ale zapisuję treść!")
                
                # Ekstraktuj treść z items
                ai_text = ""
                if 'items' in item and item['items']:
                    for ai_item in item['items']:
                        if ai_item.get('type') == 'ai_overview_element' and 'text' in ai_item:
                            ai_text = ai_item['text']
                            break
                
                logger.info(f"🤖 Ekstraktowana treść AI Overview ({len(ai_text)} znaków): {ai_text[:100]}...")
                
                # Modyfikuj item dla AI Overview
                item['title'] = '🤖 AI Overview'
                item['description'] = ai_text  # Zapisz treść AI Overview w description
            
            # Insert basic serp_item
            serp_item_id = await self.insert_serp_item(item, serp_result_id)
            
            # Process special types
            if item_type == "people_also_ask":
                await self.process_people_also_ask(item, serp_result_id)
            elif item_type == "organic" and item.get("related_result"):
                await self.process_related_results(item["related_result"], serp_item_id)
            elif item_type == "ai_overview":
                # ZAWSZE przetwarzaj AI Overview, niezależnie od references
                if item.get("references"):
                    logger.info(f"🤖 Wywołuję process_ai_references dla {len(item['references'])} references")
                    await self.process_ai_references(item["references"], serp_item_id)
                else:
                    logger.info(f"🤖 AI Overview bez references - ale treść została zapisana w serp_items")
            elif item_type == "shopping" and item.get("items"):
                await self.process_shopping_results(item["items"], serp_result_id)
            elif item_type == "local_pack":
                # local_pack może być pojedynczym obiektem lub zawierać items
                if item.get("items"):
                    await self.process_local_results(item["items"], serp_result_id)
                else:
                    # Pojedynczy local_pack element
                    await self.process_single_local_result(item, serp_result_id)
            elif item_type == "top_stories":
                await self.process_top_stories(item, serp_result_id)
            elif item_type == "related_searches":
                await self.process_related_searches(item, serp_result_id)
            
            return serp_item_id
            
        except Exception as e:
            logger.error(f"❌ Error processing item: {str(e)}")
            raise

    async def insert_serp_item(self, item: Dict, serp_result_id: str) -> str:
        """Insert basic SERP item"""
        try:
            serp_item = {
                "serp_result_id": serp_result_id,
                "type": item.get("type"),
                "rank_group": item.get("rank_group"),
                "rank_absolute": item.get("rank_absolute"),
                "position": item.get("position"),
                "xpath": item.get("xpath"),
                "domain": item.get("domain"),
                "title": item.get("title"),
                "url": item.get("url"),
                "breadcrumb": item.get("breadcrumb"),
                "website_name": item.get("website_name"),
                "description": item.get("description"),
                "pre_snippet": item.get("pre_snippet"),
                "extended_snippet": item.get("extended_snippet"),
                "is_image": item.get("is_image", False),
                "is_video": item.get("is_video", False),
                "is_featured_snippet": item.get("is_featured_snippet", False),
                "is_malicious": item.get("is_malicious", False),
                "is_web_story": item.get("is_web_story", False),
                "is_amp": item.get("amp_version", False),
                "timestamp": item.get("timestamp"),
                "featured_title": item.get("featured_title"),
                "cache_url": item.get("cache_url"),
                "related_search_url": item.get("related_search_url"),
                "raw_data": json.dumps(item)
            }
            
            # Rating data
            if item.get("rating"):
                rating = item["rating"]
                serp_item.update({
                    "rating_value": rating.get("value"),
                    "rating_type": rating.get("rating_type"),
                    "rating_votes_count": rating.get("votes_count"),
                    "rating_max": rating.get("rating_max")
                })
            
            # Price data
            if item.get("price"):
                price = item["price"]
                serp_item.update({
                    "price_current": price.get("current"),
                    "price_regular": price.get("regular"),
                    "price_max": price.get("max_value"),
                    "price_currency": price.get("currency"),
                    "price_is_range": price.get("is_price_range", False),
                    "price_displayed": price.get("displayed_price")
                })
            
            # AI Overview - treść zapisywana w description, nie ma kolumny ai_overview_text
            
            # Complex structures as JSONB
            if item.get("images"):
                serp_item["images"] = json.dumps(item["images"])
            if item.get("links"):
                serp_item["links"] = json.dumps(item["links"])
            if item.get("highlighted"):
                serp_item["highlighted"] = json.dumps(item["highlighted"])
            if item.get("faq"):
                serp_item["faq"] = json.dumps(item["faq"])
            if item.get("table"):
                serp_item["table_data"] = json.dumps(item["table"])
            if item.get("graph"):
                serp_item["graph_data"] = json.dumps(item["graph"])
            
            # Rectangle positioning
            if item.get("rectangle"):
                rect = item["rectangle"]
                serp_item.update({
                    "rectangle_x": rect.get("x"),
                    "rectangle_y": rect.get("y"),
                    "rectangle_width": rect.get("width"),
                    "rectangle_height": rect.get("height")
                })
            
            # Parse time-related fields
            if item.get("pre_snippet"):
                hours_ago = self.parser.parse_relative_time(item["pre_snippet"])
                if hours_ago:
                    serp_item["hours_ago"] = hours_ago
            
            # Insert to database
            result = supabase.table("serp_items").insert(serp_item).execute()
            serp_item_id = result.data[0]["id"]
            
            logger.debug(f"✅ Created SERP item: {item.get('type')} - {item.get('title', 'No title')[:50]}")
            return serp_item_id
            
        except Exception as e:
            logger.error(f"❌ Error inserting SERP item: {str(e)}")
            raise

    async def process_people_also_ask(self, item: Dict, serp_result_id: str):
        """Process People Also Ask items"""
        try:
            paa_items = item.get("items", [])
            
            for paa_item in paa_items:
                paa_record = {
                    "serp_result_id": serp_result_id,
                    "question": paa_item.get("title"),
                    "seed_question": paa_item.get("seed_question"),
                    "xpath": paa_item.get("xpath")
                }
                
                # Get expanded element data
                expanded = paa_item.get("expanded_element", [])
                if expanded and len(expanded) > 0:
                    exp = expanded[0]
                    paa_record.update({
                        "expanded_title": exp.get("title"),
                        "expanded_url": exp.get("url"),
                        "expanded_domain": exp.get("domain"),
                        "expanded_description": exp.get("description"),
                        "expanded_timestamp": exp.get("timestamp"),
                        "is_ai_overview": exp.get("type") == "people_also_ask_ai_overview_expanded_element"
                    })
                    
                    if exp.get("images"):
                        paa_record["images"] = json.dumps(exp["images"])
                    if exp.get("table"):
                        paa_record["table_data"] = json.dumps(exp["table"])
                    if exp.get("references"):
                        paa_record["ai_references"] = json.dumps(exp["references"])
                
                supabase.table("serp_people_also_ask").insert(paa_record).execute()
                logger.debug(f"✅ Created PAA: {paa_item.get('title', 'No title')[:50]}")
                
        except Exception as e:
            logger.error(f"❌ Error processing People Also Ask: {str(e)}")

    async def process_related_results(self, related_results: List[Dict], parent_serp_item_id: str):
        """Process related/grouped organic results"""
        try:
            for related_item in related_results:
                related_record = {
                    "parent_serp_item_id": parent_serp_item_id,
                    "type": related_item.get("type", "related_result"),
                    "xpath": related_item.get("xpath"),
                    "domain": related_item.get("domain"),
                    "title": related_item.get("title"),
                    "url": related_item.get("url"),
                    "breadcrumb": related_item.get("breadcrumb"),
                    "description": related_item.get("description"),
                    "is_image": related_item.get("is_image", False),
                    "is_video": related_item.get("is_video", False),
                    "is_amp": related_item.get("amp_version", False),
                    "timestamp": related_item.get("timestamp")
                }
                
                # JSONB fields
                if related_item.get("highlighted"):
                    related_record["highlighted"] = json.dumps(related_item["highlighted"])
                if related_item.get("images"):
                    related_record["images"] = json.dumps(related_item["images"])
                if related_item.get("rating"):
                    related_record["rating_data"] = json.dumps(related_item["rating"])
                if related_item.get("price"):
                    related_record["price_data"] = json.dumps(related_item["price"])
                
                supabase.table("serp_related_results").insert(related_record).execute()
                logger.debug(f"✅ Created related result: {related_item.get('title', 'No title')[:50]}")
                
        except Exception as e:
            logger.error(f"❌ Error processing related results: {str(e)}")

    async def process_ai_references(self, references: List[Dict], serp_item_id: str):
        """Process AI Overview references"""
        try:
            logger.info(f"🔄 Processing {len(references)} AI references for serp_item_id: {serp_item_id}")
            
            for i, ref in enumerate(references):
                logger.info(f"🔄 Processing AI reference {i+1}/{len(references)}: {ref.get('title', 'No title')[:50]}")
                
                ref_record = {
                    "serp_item_id": serp_item_id,
                    "type": ref.get("type", "ai_overview_reference"),
                    "source": ref.get("source"),
                    "domain": ref.get("domain"),
                    "title": ref.get("title"),
                    "url": ref.get("url"),
                    "date": ref.get("date"),
                    "timestamp": ref.get("timestamp"),
                    "text_fragment": ref.get("text"),
                    "image_url": ref.get("image_url"),
                    "is_amp": ref.get("amp_version", False)
                }
                
                if ref.get("badges"):
                    ref_record["badges"] = json.dumps(ref["badges"])
                
                result = supabase.table("serp_ai_references").insert(ref_record).execute()
                logger.info(f"✅ Successfully created AI reference in database: {ref.get('title', 'No title')[:50]}")
                logger.debug(f"   Database record ID: {result.data[0]['id'] if result.data else 'Unknown'}")
                
            logger.info(f"✅ Completed processing {len(references)} AI references")
                
        except Exception as e:
            logger.error(f"❌ Error processing AI references: {str(e)}")
            logger.exception("Full traceback:")

    async def process_shopping_results(self, shopping_items: List[Dict], serp_result_id: str):
        """Process Google Shopping results"""
        try:
            for shop_item in shopping_items:
                shop_record = {
                    "serp_result_id": serp_result_id,
                    "title": shop_item.get("title"),
                    "description": shop_item.get("description"),
                    "source": shop_item.get("source"),
                    "marketplace": shop_item.get("marketplace"),
                    "marketplace_url": shop_item.get("marketplace_url"),
                    "url": shop_item.get("url"),
                    "xpath": shop_item.get("xpath")
                }
                
                # Price data
                if shop_item.get("price"):
                    price = shop_item["price"]
                    shop_record.update({
                        "price_current": price.get("current"),
                        "price_regular": price.get("regular"),
                        "price_currency": price.get("currency"),
                        "price_displayed": price.get("displayed_price")
                    })
                
                # Rating data
                if shop_item.get("rating"):
                    rating = shop_item["rating"]
                    shop_record.update({
                        "rating_value": rating.get("value"),
                        "rating_votes_count": rating.get("votes_count"),
                        "rating_max": rating.get("rating_max")
                    })
                
                if shop_item.get("images"):
                    shop_record["images"] = json.dumps(shop_item["images"])
                
                supabase.table("serp_shopping_results").insert(shop_record).execute()
                logger.debug(f"✅ Created shopping result: {shop_item.get('title', 'No title')[:50]}")
                
        except Exception as e:
            logger.error(f"❌ Error processing shopping results: {str(e)}")

    async def process_local_results(self, local_items: List[Dict], serp_result_id: str):
        """Process Local Pack results"""
        try:
            for local_item in local_items:
                local_record = {
                    "serp_result_id": serp_result_id,
                    "title": local_item.get("title"),
                    "description": local_item.get("description"),
                    "domain": local_item.get("domain"),
                    "url": local_item.get("url"),
                    "phone": local_item.get("phone"),
                    "cid": local_item.get("cid"),
                    "place_id": local_item.get("place_id"),
                    "is_paid": local_item.get("is_paid", False),
                    "xpath": local_item.get("xpath")
                }
                
                # Rating data
                if local_item.get("rating"):
                    rating = local_item["rating"]
                    local_record.update({
                        "rating_value": rating.get("value"),
                        "rating_votes_count": rating.get("votes_count")
                    })
                
                supabase.table("serp_local_results").insert(local_record).execute()
                logger.debug(f"✅ Created local result: {local_item.get('title', 'No title')[:50]}")
                
        except Exception as e:
            logger.error(f"❌ Error processing local results: {str(e)}")

    async def process_top_stories(self, item: Dict, serp_result_id: str):
        """Process Top Stories as individual SERP items"""
        try:
            stories = item.get("items", [])
            
            for i, story in enumerate(stories):
                # Create individual SERP item for each story
                story_item = {
                    "serp_result_id": serp_result_id,
                    "type": "top_stories",
                    "rank_group": i + 1,
                    "rank_absolute": item.get("rank_absolute"),
                    "title": story.get("title"),
                    "url": story.get("url"),
                    "domain": story.get("domain"),
                    "timestamp": story.get("timestamp"),
                    "website_name": story.get("source"),
                    "pre_snippet": story.get("date"),
                    "raw_data": json.dumps(story)
                }
                
                # Parse hours ago from date
                if story.get("date"):
                    hours_ago = self.parser.parse_relative_time(story["date"])
                    if hours_ago:
                        story_item["hours_ago"] = hours_ago
                
                # Images
                if story.get("image_url"):
                    story_item["images"] = json.dumps([{"image_url": story["image_url"]}])
                
                supabase.table("serp_items").insert(story_item).execute()
                logger.debug(f"✅ Created top story: {story.get('title', 'No title')[:50]}")
                
        except Exception as e:
            logger.error(f"❌ Error processing top stories: {str(e)}")

    async def process_related_searches(self, item: Dict, serp_result_id: str):
        """Process Related Searches items"""
        try:
            related_items = item.get("items", [])
            
            for index, related_item in enumerate(related_items):
                # related_item może być stringiem lub obiektem
                if isinstance(related_item, str):
                    keyword = related_item
                else:
                    keyword = related_item.get("keyword") or related_item.get("title") or str(related_item)
                    
                related_record = {
                    "serp_result_id": serp_result_id,
                    "keyword": keyword,
                    "position": index + 1
                }
                
                supabase.table("serp_related_searches").insert(related_record).execute()
                logger.debug(f"✅ Created related search: {keyword[:50]}")
                
        except Exception as e:
            logger.error(f"❌ Error processing related searches: {str(e)}")

    async def process_single_local_result(self, item: Dict, serp_result_id: str):
        """Process single Local Pack result"""
        try:
            local_record = {
                "serp_result_id": serp_result_id,
                "title": item.get("title"),
                "description": item.get("description"),
                "domain": item.get("domain"),
                "url": item.get("url"),
                "phone": item.get("phone"),
                "cid": item.get("cid"),
                "place_id": item.get("place_id"),
                "is_paid": item.get("is_paid", False),
                "xpath": item.get("xpath")
            }
            
            # Rating data
            if item.get("rating"):
                rating = item["rating"]
                local_record.update({
                    "rating_value": rating.get("value"),
                    "rating_votes_count": rating.get("votes_count")
                })
            
            supabase.table("serp_local_results").insert(local_record).execute()
            logger.debug(f"✅ Created local result: {item.get('title', 'No title')[:50]}")
            
        except Exception as e:
            logger.error(f"❌ Error processing single local result: {str(e)}")

# ========================================
# API ENDPOINTS
# ========================================
@router.post("/serp/google/organic/live/advanced/with-database")
async def get_serp_and_save_to_database(data: SerpOrganicInput):
    """
    Pobiera dane SERP i zapisuje je do bazy danych zgodnie z mapowaniem.
    """
    if not all([DFS_LOGIN, DFS_PASSWORD, SUPABASE_URL, SUPABASE_KEY]):
        raise HTTPException(status_code=500, detail="Missing API credentials")
    
    logger.info(f"🔄 Processing SERP with database save for: {data.keyword}")
    
    config = dfs_config.Configuration(username=DFS_LOGIN, password=DFS_PASSWORD)
    
    # Prepare request
    request_data = [
        SerpGoogleOrganicLiveAdvancedRequestInfo(
            keyword=data.keyword,
            location_code=data.location_code,
            language_code=data.language_code,
            device=data.device,
            os=data.os,
            depth=data.depth,
            calculate_rectangles=data.calculate_rectangles,
            group_organic_results=data.group_organic_results
        )
    ]
    
    try:
        # 1. Call DataForSEO API
        with dfs_api_provider.ApiClient(config) as api_client:
            api_instance = SerpApi(api_client)
            api_response = api_instance.google_organic_live_advanced(request_data)
            
            if not api_response.tasks or api_response.tasks[0].status_code != 20000:
                raise HTTPException(status_code=400, detail="DataForSEO API error")
            
            task = api_response.tasks[0]
            if not task.result:
                raise HTTPException(status_code=404, detail="No SERP data found")
        
        # 2. Process and save to database
        serp_response = {
            "task_info": {
                "id": task.id,
                "status_code": task.status_code,
                "status_message": task.status_message,
                "cost": task.cost,
                "execution_time": task.time
            },
            "result": task.result[0].to_dict()
        }
        
        processor = SerpProcessor()
        result = await processor.process_serp_response(serp_response, data)
        
        # 3. Return success response
        return {
            "success": True,
            "message": "SERP data successfully saved to database",
            "api_response": {
                "keyword": data.keyword,
                "serp_result_id": result["serp_result_id"],
                "items_processed": result["items_processed"],
                "total_items": result["total_items"],
                "cost_usd": result["cost_usd"]
            },
            "raw_api_response": serp_response  # For debugging
        }
        
    except Exception as e:
        logger.exception(f"❌ Error reprocessing SERP: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Reprocessing failed: {str(e)}")

@router.get("/serp/database-stats")
async def get_serp_database_stats():
    """
    Pokaż statystyki danych SERP w bazie danych
    """
    try:
        # Count records in each table
        serp_results = supabase.table("serp_results").select("id", count="exact").execute()
        serp_items = supabase.table("serp_items").select("id", count="exact").execute()
        paa_items = supabase.table("serp_people_also_ask").select("id", count="exact").execute()
        related_results = supabase.table("serp_related_results").select("id", count="exact").execute()
        ai_references = supabase.table("serp_ai_references").select("id", count="exact").execute()
        shopping_results = supabase.table("serp_shopping_results").select("id", count="exact").execute()
        local_results = supabase.table("serp_local_results").select("id", count="exact").execute()
        
        # Get recent SERP results
        recent_serps = supabase.table("serp_results").select("keyword, datetime, items_count, api_cost").order("created_at", desc=True).limit(10).execute()
        
        # Get item types distribution
        item_types = supabase.table("serp_items").select("type", count="exact").execute()
        
        # Calculate total API costs
        total_costs = supabase.table("serp_results").select("api_cost").execute()
        total_cost = sum(float(record.get("api_cost", 0) or 0) for record in total_costs.data)
        
        return {
            "database_stats": {
                "serp_results": serp_results.count,
                "serp_items": serp_items.count,
                "people_also_ask": paa_items.count,
                "related_results": related_results.count,
                "ai_references": ai_references.count,
                "shopping_results": shopping_results.count,
                "local_results": local_results.count
            },
            "recent_serps": recent_serps.data,
            "total_api_cost_usd": round(total_cost, 4),
            "item_types_distribution": {}  # Would need GROUP BY query for this
        }
        
    except Exception as e:
        logger.exception(f"❌ Error getting database stats: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Stats error: {str(e)}")

@router.get("/serp/keyword/{keyword}/complete")
async def get_complete_serp_data(keyword: str, location_code: int = 2616, language_code: str = "pl"):
    """
    Pobierz kompletne dane SERP dla słowa kluczowego ze wszystkich tabel
    """
    try:
        # Find SERP result
        serp_result = supabase.table("serp_results").select("*").eq("keyword", keyword).eq("location_code", location_code).eq("language_code", language_code).execute()
        
        if not serp_result.data:
            raise HTTPException(status_code=404, detail=f"No SERP data found for keyword: {keyword}")
        
        serp_data = serp_result.data[0]
        serp_result_id = serp_data["id"]
        
        # Get all SERP items
        serp_items = supabase.table("serp_items").select("*").eq("serp_result_id", serp_result_id).order("rank_absolute").execute()
        
        # Get People Also Ask
        paa_items = supabase.table("serp_people_also_ask").select("*").eq("serp_result_id", serp_result_id).execute()
        
        # Get Shopping results
        shopping_items = supabase.table("serp_shopping_results").select("*").eq("serp_result_id", serp_result_id).execute()
        
        # Get Local results
        local_items = supabase.table("serp_local_results").select("*").eq("serp_result_id", serp_result_id).execute()
        
        # Get related results for each SERP item
        related_results = {}
        ai_references = {}
        
        for item in serp_items.data:
            item_id = item["id"]
            
            # Get related results
            related = supabase.table("serp_related_results").select("*").eq("parent_serp_item_id", item_id).execute()
            if related.data:
                related_results[item_id] = related.data
            
            # Get AI references
            ai_refs = supabase.table("serp_ai_references").select("*").eq("serp_item_id", item_id).execute()
            if ai_refs.data:
                ai_references[item_id] = ai_refs.data
        
        # Organize items by type
        items_by_type = {}
        for item in serp_items.data:
            item_type = item["type"]
            if item_type not in items_by_type:
                items_by_type[item_type] = []
            items_by_type[item_type].append(item)
        
        return {
            "success": True,
            "keyword": keyword,
            "serp_metadata": {
                "serp_result_id": serp_result_id,
                "datetime": serp_data["datetime"],
                "se_results_count": serp_data["se_results_count"],
                "items_count": serp_data["items_count"],
                "item_types": serp_data["item_types"],
                "api_cost": serp_data["api_cost"],
                "check_url": serp_data["check_url"]
            },
            "serp_items": {
                "by_type": items_by_type,
                "total_count": len(serp_items.data)
            },
            "people_also_ask": paa_items.data,
            "shopping_results": shopping_items.data,
            "local_results": local_items.data,
            "related_results": related_results,
            "ai_references": ai_references,
            "statistics": {
                "organic_results": len(items_by_type.get("organic", [])),
                "paid_results": len(items_by_type.get("paid", [])),
                "featured_snippets": len(items_by_type.get("featured_snippet", [])),
                "people_also_ask_count": len(paa_items.data),
                "shopping_count": len(shopping_items.data),
                "local_count": len(local_items.data),
                "total_related_results": sum(len(rels) for rels in related_results.values()),
                "total_ai_references": sum(len(refs) for refs in ai_references.values())
            }
        }
        
    except Exception as e:
        logger.exception(f"❌ Error getting complete SERP data: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Error fetching SERP data: {str(e)}")

@router.get("/serp/analyze/{keyword}")
async def analyze_serp_performance(keyword: str, location_code: int = 2616, language_code: str = "pl"):
    """
    Analiza wydajności SERP - pozycje organiczne, konkurencja, featured snippets
    """
    try:
        # Get SERP data
        serp_result = supabase.table("serp_results").select("*").eq("keyword", keyword).eq("location_code", location_code).eq("language_code", language_code).execute()
        
        if not serp_result.data:
            raise HTTPException(status_code=404, detail=f"No SERP data found for keyword: {keyword}")
        
        serp_result_id = serp_result.data[0]["id"]
        
        # Get organic results
        organic_items = supabase.table("serp_items").select("*").eq("serp_result_id", serp_result_id).eq("type", "organic").order("rank_absolute").execute()
        
        # Get paid results
        paid_items = supabase.table("serp_items").select("*").eq("serp_result_id", serp_result_id).eq("type", "paid").order("rank_absolute").execute()
        
        # Get featured snippets
        featured_items = supabase.table("serp_items").select("*").eq("serp_result_id", serp_result_id).eq("is_featured_snippet", True).execute()
        
        # Analyze domains
        domain_analysis = {}
        for item in organic_items.data:
            domain = item.get("domain", "unknown")
            if domain not in domain_analysis:
                domain_analysis[domain] = {
                    "positions": [],
                    "titles": [],
                    "has_rating": False,
                    "avg_rating": None,
                    "has_rich_snippets": False
                }
            
            domain_analysis[domain]["positions"].append(item["rank_absolute"])
            domain_analysis[domain]["titles"].append(item["title"])
            
            if item.get("rating_value"):
                domain_analysis[domain]["has_rating"] = True
                if not domain_analysis[domain]["avg_rating"]:
                    domain_analysis[domain]["avg_rating"] = []
                domain_analysis[domain]["avg_rating"].append(item["rating_value"])
            
            if item.get("images") or item.get("links"):
                domain_analysis[domain]["has_rich_snippets"] = True
        
        # Calculate average ratings
        for domain in domain_analysis:
            if domain_analysis[domain]["avg_rating"]:
                domain_analysis[domain]["avg_rating"] = round(
                    sum(domain_analysis[domain]["avg_rating"]) / len(domain_analysis[domain]["avg_rating"]), 2
                )
        
        # Top performing domains
        top_domains = sorted(
            domain_analysis.items(),
            key=lambda x: (len(x[1]["positions"]), -min(x[1]["positions"])),
            reverse=True
        )[:10]
        
        return {
            "success": True,
            "keyword": keyword,
            "serp_overview": {
                "total_organic": len(organic_items.data),
                "total_paid": len(paid_items.data),
                "has_featured_snippet": len(featured_items.data) > 0,
                "featured_snippet_domain": featured_items.data[0].get("domain") if featured_items.data else None,
                "total_domains": len(domain_analysis),
                "serp_date": serp_result.data[0]["datetime"]
            },
            "top_organic_results": [
                {
                    "position": item["rank_absolute"],
                    "domain": item["domain"],
                    "title": item["title"],
                    "url": item["url"],
                    "has_rating": bool(item.get("rating_value")),
                    "rating": item.get("rating_value"),
                    "has_images": bool(item.get("images")),
                    "has_sitelinks": bool(item.get("links"))
                }
                for item in organic_items.data[:10]
            ],
            "domain_analysis": {
                "top_domains": [
                    {
                        "domain": domain,
                        "total_results": len(data["positions"]),
                        "best_position": min(data["positions"]),
                        "all_positions": data["positions"],
                        "has_rating": data["has_rating"],
                        "avg_rating": data["avg_rating"],
                        "has_rich_snippets": data["has_rich_snippets"]
                    }
                    for domain, data in top_domains
                ]
            },
            "competition_analysis": {
                "domains_with_multiple_results": len([d for d in domain_analysis if len(domain_analysis[d]["positions"]) > 1]),
                "domains_with_ratings": len([d for d in domain_analysis if domain_analysis[d]["has_rating"]]),
                "domains_with_rich_snippets": len([d for d in domain_analysis if domain_analysis[d]["has_rich_snippets"]]),
                "top_3_dominated_by": list(set([organic_items.data[i]["domain"] for i in range(min(3, len(organic_items.data)))])),
            }
        }
        
    except Exception as e:
        logger.exception(f"❌ Error analyzing SERP performance: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Analysis error: {str(e)}")

# ========================================
# BULK PROCESSING ENDPOINTS
# ========================================
@router.post("/serp/bulk-process")
async def bulk_process_keywords(keywords: List[str], location_code: int = 2616, language_code: str = "pl"):
    """
    Masowe przetwarzanie słów kluczowych SERP (z limitem 10 na raz)
    """
    if len(keywords) > 10:
        raise HTTPException(status_code=400, detail="Maximum 10 keywords per bulk request")
    
    results = []
    total_cost = 0
    
    for keyword in keywords:
        try:
            input_data = SerpOrganicInput(
                keyword=keyword,
                location_code=location_code,
                language_code=language_code
            )
            
            # Process each keyword
            result = await get_serp_and_save_to_database(input_data)
            results.append({
                "keyword": keyword,
                "success": True,
                "serp_result_id": result["api_response"]["serp_result_id"],
                "items_processed": result["api_response"]["items_processed"],
                "cost": result["api_response"]["cost_usd"]
            })
            total_cost += result["api_response"]["cost_usd"]
            
            logger.info(f"✅ Bulk processed: {keyword}")
            
        except Exception as e:
            logger.error(f"❌ Bulk processing failed for {keyword}: {str(e)}")
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
@router.post("/serp/test-parser")
async def test_serp_parser(raw_serp_data: Dict):
    """
    Test parser z surowym JSON SERP (do debugowania)
    """
    try:
        input_data = SerpOrganicInput(
            keyword=raw_serp_data["result"]["keyword"],
            location_code=raw_serp_data["result"]["location_code"],
            language_code=raw_serp_data["result"]["language_code"]
        )
        
        processor = SerpProcessor()
        result = await processor.process_serp_response(raw_serp_data, input_data)
        
        return {
            "success": True,
            "message": "Test parsing completed",
            "result": result
        }
        
    except Exception as e:
        logger.exception(f"❌ Test parsing failed: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Test parsing failed: {str(e)}")

@router.get("/serp/test-functions")
async def test_parsing_functions():
    """
    Test funkcji parsujących
    """
    parser = SerpDataParser()
    
    test_cases = {
        "relative_time": {
            "20 godzin temu": parser.parse_relative_time("20 godzin temu"),
            "dzień temu": parser.parse_relative_time("dzień temu"),
            "3 dni temu": parser.parse_relative_time("3 dni temu"),
            "5 godzin temu": parser.parse_relative_time("5 godzin temu"),
            "invalid": parser.parse_relative_time("invalid string")
        },
        "execution_time": {
            "3.7924 sec.": parser.parse_execution_time("3.7924 sec."),
            "1.234 sec.": parser.parse_execution_time("1.234 sec."),
            "invalid": parser.parse_execution_time("invalid")
        },
        "freshness_hours": {
            "2025-06-03 07:47:32 +00:00": parser.calculate_freshness_hours("2025-06-03 07:47:32 +00:00"),
            "invalid": parser.calculate_freshness_hours("invalid")
        }
    }
    
    return {
        "success": True,
        "test_results": test_cases
    }

@router.post("/serp/reprocess-existing")
async def reprocess_existing_serp(serp_result_id: str):
    """
    Przetwórz ponownie istniejący wynik SERP (użyteczne gdy dodano nowe pola do mapowania)
    """
    try:
        # Get existing SERP result
        existing = supabase.table("serp_results").select("raw_api_response").eq("id", serp_result_id).execute()
        
        if not existing.data or not existing.data[0].get("raw_api_response"):
            raise HTTPException(status_code=404, detail="SERP result not found or missing raw data")
        
        raw_response = existing.data[0]["raw_api_response"]
        
        # Create input data from existing record
        input_data = SerpOrganicInput(
            keyword=raw_response["result"]["keyword"],
            location_code=raw_response["result"]["location_code"],
            language_code=raw_response["result"]["language_code"]
        )
        
        # Reprocess
        processor = SerpProcessor()
        result = await processor.process_serp_response(raw_response, input_data)
        
        return {
            "success": True,
            "message": "SERP data reprocessed successfully",
            "serp_result_id": result["serp_result_id"],
            "items_processed": result["items_processed"]
        }
        
    except Exception as e:
        logger.exception(f"❌ Error in SERP reprocessing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"SERP reprocessing failed: {str(e)}")