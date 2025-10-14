import os
import logging
from fastapi import APIRouter, HTTPException
from pydantic import BaseModel
from dotenv import load_dotenv
from dataforseo_client import configuration as dfs_config, api_client as dfs_api_provider
from dataforseo_client.api.dataforseo_labs_api import DataforseoLabsApi
from dataforseo_client.models.dataforseo_labs_google_keyword_ideas_live_request_info import (
    DataforseoLabsGoogleKeywordIdeasLiveRequestInfo,
)

load_dotenv()

router = APIRouter()

# Konfiguracja logowania
logger = logging.getLogger("dfs_labs")
logger.setLevel(logging.DEBUG)
handler = logging.StreamHandler()
formatter = logging.Formatter("%(asctime)s | %(levelname)s | %(message)s")
handler.setFormatter(formatter)
logger.addHandler(handler)

# Dane logowania
DFS_LOGIN = os.getenv("DATAFORSEO_LOGIN")
DFS_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

# Model danych wejściowych
class KeywordIdeasInput(BaseModel):
    keywords: list[str]
    location_code: int = 2840  # Polska
    language_code: str = "en"

@router.post("/labs/keyword-ideas")
async def get_keyword_ideas(data: KeywordIdeasInput):
    if not DFS_LOGIN or not DFS_PASSWORD:
        logger.error("❌ Brak danych logowania do API")
        raise HTTPException(status_code=500, detail="Brak danych logowania do API DataForSEO.")

    if not data.keywords:
        logger.error("❌ Brak słów kluczowych w zapytaniu.")
        raise HTTPException(status_code=422, detail="Podaj przynajmniej jedno słowo kluczowe.")

    logger.info(f"➡️ Otrzymano zapytanie dla słów kluczowych: {data.keywords}")

    config = dfs_config.Configuration(username=DFS_LOGIN, password=DFS_PASSWORD)

    request_data = [
        DataforseoLabsGoogleKeywordIdeasLiveRequestInfo(
            keywords=data.keywords,
            location_code=data.location_code,
            language_code=data.language_code
        )
    ]

    try:
        with dfs_api_provider.ApiClient(config) as api_client:
            api_instance = DataforseoLabsApi(api_client)

            logger.debug("➡️ Wysyłanie żądania do DataForSEO Labs API (Keyword Ideas)...")
            api_response = api_instance.google_keyword_ideas_live(request_data)

            task = api_response.tasks[0]
            if not task.result:
                logger.warning("⚠️ Brak wyników dla podanych słów kluczowych.")
                raise HTTPException(status_code=404, detail="Brak danych dla podanych słów kluczowych.")

            logger.info("✅ Pobrano dane z DFS Labs API (Keyword Ideas).")
            return task.result[0].to_dict()

    except Exception as e:
        logger.exception("❌ Błąd podczas pobierania danych z DataForSEO Labs API")
        raise HTTPException(status_code=500, detail=f"Błąd serwera:\n{str(e)}")