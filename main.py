import os
import logging
import numpy as np
import requests
import os
import asyncio
from fastapi import FastAPI, HTTPException, Request
from fastapi.responses import HTMLResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from fastapi.templating import Jinja2Templates
from pydantic import BaseModel
from dotenv import load_dotenv
import json
from datetime import datetime
from typing import Any, List

# Function to convert numpy types to Python native types for JSON serialization
def convert_numpy_types(obj: Any) -> Any:
    """Convert numpy types to Python native types for JSON serialization"""
    if isinstance(obj, np.floating):
        return float(obj)
    elif isinstance(obj, np.integer):
        return int(obj)
    elif isinstance(obj, np.ndarray):
        return obj.tolist()
    elif isinstance(obj, dict):
        return {key: convert_numpy_types(value) for key, value in obj.items()}
    elif isinstance(obj, list):
        return [convert_numpy_types(item) for item in obj]
    return obj

# Import orchestratora
from app.api.full_analysis import orchestrator

# Import modułu klastrowania semantycznego
from app.services.semantic_clustering import SemanticClusteringService

# Import modułu architektury (Moduł 3)
from app.services.architecture_generator import ArchitectureGenerator

# Import modułu Content Brief Generator (Moduł 4)
from app.services.content_brief_generator import ContentBriefGeneratorService
from app.services.dataforseo_scraper import DataForSEOScraper

# ========================================
# ENVIRONMENT SETUP
# ========================================
load_dotenv()

# DataForSEO credentials
DFS_LOGIN = os.getenv("DATAFORSEO_LOGIN")
DFS_PASSWORD = os.getenv("DATAFORSEO_PASSWORD")

# Logger setup - identyczny z orchestratorem
logger = logging.getLogger("main")
# Poziom logowania jest już ustawiony globalnie w app/__init__.py

# Konfiguracja uvicorn logging - wyłącz kolorowe logi
logging.getLogger("uvicorn").setLevel(logging.INFO)
logging.getLogger("uvicorn.access").setLevel(logging.WARNING)  # Wycisz access logi
logging.getLogger("uvicorn.error").setLevel(logging.INFO)

# FastAPI app
app = FastAPI(title="SEO Analysis Tool", version="1.0.0")

# Static files
app.mount("/static", StaticFiles(directory="static"), name="static")

# Templates
templates = Jinja2Templates(directory="templates")

class AnalysisRequest(BaseModel):
    keyword: str
    country: str  # Format: "2616|pl"
    use_cache: bool = True  # Nowy parametr do kontroli cache

class DataForSEOScraperRequest(BaseModel):
    keywords: List[str]
    max_expand_depth: int = 1
    location_code: int = 2616
    language_code: str = "pl"
    device: str = "desktop"
    os: str = "windows"
    serp_depth: int = 100

# ========================================
# ROUTES
# ========================================

@app.get("/")
async def root():
    """Root endpoint - przekierowanie do analizy SEO"""
    return {"message": "SEO Analysis Tool", "version": "1.0.0", "endpoints": ["/seo-analysis"]}

@app.get("/seo-analysis", response_class=HTMLResponse)
async def seo_analysis_page(request: Request):
    """Główna strona z formularzem analizy SEO"""
    return templates.TemplateResponse("seo_analysis.html", {"request": request})

@app.get("/seo-analysis-modular", response_class=HTMLResponse)
async def seo_analysis_modular_page(request: Request):
    """Modularna wersja strony z formularzem analizy SEO"""
    return templates.TemplateResponse("seo_analysis_modular.html", {"request": request})

@app.get("/dataforseo-scraper", response_class=HTMLResponse)
async def dataforseo_scraper_page(request: Request):
    """Strona narzędzia DataForSEO Scraper"""
    return templates.TemplateResponse("dataforseo_scraper.html", {"request": request})

@app.post("/api/v6/analyze-complete")
async def run_complete_analysis(data: AnalysisRequest):
    """Uruchamia kompletną analizę SEO - TYLKO ZAPIS DO BAZY"""
    try:
        # Parsuj country (format: "location_code|language_code")
        location_code, language_code = data.country.split("|")
        location_code = int(location_code)
        
        logger.info(f"🚀 Rozpoczynam analizę: {data.keyword} ({location_code}|{language_code})")
        
        # Uruchom kompletną analizę (zapis do bazy)
        result = await orchestrator.run_complete_analysis(
            keyword=data.keyword,
            location_code=location_code,
            language_code=language_code,
            use_cache=data.use_cache
        )
        
        return result
        
    except ValueError:
        raise HTTPException(status_code=400, detail="Nieprawidłowy format kraju")
    except Exception as e:
        logger.exception(f"❌ Błąd analizy: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Błąd analizy: {str(e)}")

@app.get("/api/v6/keyword-data/{keyword}")
async def get_keyword_data(keyword: str, location_code: int, language_code: str):
    """Pobiera dane słowa kluczowego z bazy - SEKCJA 1: EXTENDED HEADER"""
    try:
        logger.info(f"📊 Pobieranie danych dla: {keyword} ({location_code}|{language_code})")
        
        # Pobierz dane z bazy przez orchestrator
        keyword_data = await orchestrator.get_keyword_header_data(
            keyword=keyword,
            location_code=location_code,
            language_code=language_code
        )
        
        if not keyword_data:
            raise HTTPException(status_code=404, detail=f"Brak danych dla słowa: {keyword}")
        
        return {"success": True, "data": keyword_data}
        
    except Exception as e:
        logger.exception(f"❌ Błąd pobierania danych: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Błąd pobierania danych: {str(e)}")

@app.get("/api/v6/countries")
async def get_countries():
    """Pobiera listę krajów do wyboru"""
    try:
        countries = await orchestrator.get_available_countries()
        return {"success": True, "countries": countries}
    except Exception as e:
        logger.exception(f"❌ Błąd pobierania krajów: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Błąd pobierania krajów: {str(e)}")

@app.get("/api/v6/status")
async def get_orchestrator_status():
    """Status orchestratora"""
    try:
        cache_size = len(orchestrator.cache)
        return {
            "status": "active",
            "cache_size": cache_size,
            "cache_duration_hours": orchestrator.cache_duration.total_seconds() / 3600
        }
    except Exception as e:
        logger.exception(f"❌ Błąd statusu: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Błąd statusu: {str(e)}")

@app.get("/api/v6/ip")
async def get_public_ip():
    """Zwraca publiczny IP widziany przez usługę (diagnostyka)"""
    try:
        response = requests.get("https://ipinfo.io/json", timeout=5)
        if response.status_code != 200:
            raise HTTPException(
                status_code=502,
                detail=f"Błąd pobierania IP: HTTP {response.status_code}"
            )
        return {"success": True, "data": response.json()}
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ Błąd pobierania IP: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Błąd pobierania IP: {str(e)}")

@app.post("/api/v6/dataforseo-scraper/run")
async def run_dataforseo_scraper(data: DataForSEOScraperRequest):
    """Uruchamia niezależny DataForSEO Scraper i zapisuje output do plików"""
    if not DFS_LOGIN or not DFS_PASSWORD:
        raise HTTPException(status_code=500, detail="Missing DataForSEO credentials")

    try:
        scraper = DataForSEOScraper(DFS_LOGIN, DFS_PASSWORD)
        result = await asyncio.to_thread(
            scraper.run,
            keywords=data.keywords,
            max_expand_depth=data.max_expand_depth,
            location_code=data.location_code,
            language_code=data.language_code,
            device=data.device,
            os_name=data.os,
            serp_depth=data.serp_depth
        )

        run_id = result.get("run_id")
        return {
            "success": True,
            "run_id": run_id,
            "stats": result.get("stats"),
            "download": {
                "json": f"/api/v6/dataforseo-scraper/download/{run_id}.json",
                "txt": f"/api/v6/dataforseo-scraper/download/{run_id}.txt"
            }
        }
    except Exception as e:
        logger.exception(f"❌ DataForSEO Scraper error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"DataForSEO Scraper error: {str(e)}")

@app.get("/api/v6/dataforseo-scraper/download/{run_id}.{ext}")
async def download_dataforseo_output(run_id: str, ext: str):
    """Pobiera output JSON lub TXT dla danego run_id"""
    if ext not in ("json", "txt"):
        raise HTTPException(status_code=400, detail="Invalid file extension")

    try:
        scraper = DataForSEOScraper(DFS_LOGIN, DFS_PASSWORD)
        file_path = os.path.join(scraper.output_dir, f"{run_id}.{ext}")
        if not os.path.exists(file_path):
            raise HTTPException(status_code=404, detail="File not found")
        media_type = "application/json" if ext == "json" else "text/plain"
        return FileResponse(path=file_path, media_type=media_type, filename=f"{run_id}.{ext}")
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ DataForSEO download error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Download error: {str(e)}")

@app.post("/api/v6/clear-cache")
async def clear_cache():
    """Czyści cache orchestratora"""
    try:
        cache_size_before = len(orchestrator.cache)
        orchestrator.cache.clear()
        logger.info(f"🗑️ Wyczyszczono cache: {cache_size_before} elementów")
        return {
            "success": True,
            "message": f"Cache wyczyszczony: {cache_size_before} elementów",
            "cache_size_before": cache_size_before,
            "cache_size_after": 0
        }
    except Exception as e:
        logger.exception(f"❌ Błąd czyszczenia cache: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Błąd czyszczenia cache: {str(e)}")

@app.get("/api/v6/export-data/{keyword}")
async def export_keyword_data(keyword: str, location_code: int, language_code: str, format: str = "json"):
    """
    Eksportuje kompletne dane słowa kluczowego ze wszystkich sekcji
    
    Args:
        keyword: Słowo kluczowe
        location_code: Kod lokalizacji 
        language_code: Kod języka
        format: Format eksportu ('json' lub 'html')
    
    Returns:
        Kompletne dane w wybranym formacie
    """
    try:
        logger.info(f"📦 Eksportowanie danych dla: {keyword} ({location_code}|{language_code}) - format: {format}")
        
        # Pobierz wszystkie dane z bazy przez orchestrator
        complete_data = await orchestrator.get_keyword_header_data(
            keyword=keyword,
            location_code=location_code,
            language_code=language_code
        )
        
        if not complete_data:
            raise HTTPException(status_code=404, detail=f"Brak danych dla słowa: {keyword}")
        
        # Dodaj metadane eksportu
        export_metadata = {
            "export_timestamp": datetime.now().isoformat(),
            "export_format": format,
            "keyword": keyword,
            "location_code": location_code,
            "language_code": language_code,
            "data_completeness": {
                "sections_included": [
                    "SEKCJA 1: EXTENDED HEADER",
                    "SEKCJA 2: EXTENDED CORE SEO METRICS", 
                    "SEKCJA 3: COMPLETE INTENT ANALYSIS",
                    "SEKCJA 4: COMPLETE DEMOGRAPHICS",
                    "SEKCJA 5: EXTENDED TRENDS & SEASONALITY",
                    "SEKCJA 6: COMPLETE GEOGRAPHIC DATA",
                    "SEKCJA 7: ENHANCED COMPETITION ANALYSIS",
                    "SEKCJA 8: ENHANCED RELATED KEYWORDS",
                    "SEKCJA 9: ENHANCED SERP ANALYSIS",
                    "SEKCJA 10: ENHANCED AUTOCOMPLETE ANALYSIS"
                ],
                "total_related_keywords": len(complete_data.get("related_keywords", [])),
                "total_serp_items": len(complete_data.get("serp_items", [])),
                "total_autocomplete_suggestions": len(complete_data.get("autocomplete_suggestions", [])),
                "total_historical_records": len(complete_data.get("historical_data", []))
            }
        }
        
        # Przygotuj finalne dane eksportu
        export_data = {
            "metadata": export_metadata,
            "keyword_data": complete_data
        }
        
        if format.lower() == "json":
            return export_data
        elif format.lower() == "html":
            # Generuj HTML z danymi
            html_content = generate_html_export(export_data)
            return HTMLResponse(content=html_content, media_type="text/html")
        else:
            raise HTTPException(status_code=400, detail="Nieobsługiwany format. Dostępne: 'json', 'html'")
        
    except Exception as e:
        logger.exception(f"❌ Błąd eksportowania danych: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Błąd eksportowania danych: {str(e)}")

def generate_html_export(export_data: dict) -> str:
    """Generuje HTML z eksportowanymi danymi"""
    metadata = export_data["metadata"]
    data = export_data["keyword_data"]
    
    # Podstawowy HTML bez zagnieżdżonych f-stringów
    html_template = """
    <!DOCTYPE html>
    <html lang="pl">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Eksport danych SEO - {keyword}</title>
        <style>
            body {{ font-family: Arial, sans-serif; margin: 20px; background: #f5f5f5; }}
            .container {{ max-width: 1200px; margin: 0 auto; background: white; padding: 30px; border-radius: 8px; }}
            .header {{ background: #007bff; color: white; padding: 20px; text-align: center; margin: -30px -30px 30px -30px; }}
            .section {{ margin: 30px 0; padding: 20px; border: 1px solid #ddd; border-radius: 5px; }}
            .metric {{ display: inline-block; margin: 10px; padding: 15px; background: #f8f9fa; border-left: 4px solid #007bff; }}
            .metric-label {{ font-size: 0.9em; color: #666; }}
            .metric-value {{ font-size: 1.2em; font-weight: bold; }}
            .json-display {{ background: #f8f9fa; padding: 15px; border-radius: 4px; overflow: auto; max-height: 300px; font-family: monospace; font-size: 12px; }}
        </style>
    </head>
    <body>
        <div class="container">
            <div class="header">
                <h1>🔍 Eksport danych SEO</h1>
                <p>Słowo: {keyword} | Lokalizacja: {location_code} | Język: {language_code}</p>
                <p>Wygenerowano: {timestamp}</p>
            </div>
            
            <div class="section">
                <h2>📊 Podstawowe metryki</h2>
                <div class="metric">
                    <div class="metric-label">Słowo kluczowe</div>
                    <div class="metric-value">{keyword_name}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Volume wyszukiwań</div>
                    <div class="metric-value">{search_volume}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">CPC</div>
                    <div class="metric-value">{cpc}</div>
                </div>
                <div class="metric">
                    <div class="metric-label">Trudność</div>
                    <div class="metric-value">{difficulty}</div>
                </div>
            </div>

            <div class="section">
                <h2>📋 KOMPLETNE DANE JSON</h2>
                <div class="json-display">
{json_data}
                </div>
            </div>
        </div>
    </body>
    </html>
    """
    
    # Przygotuj dane
    def safe_display(value, fallback="Brak danych"):
        if value is None:
            return fallback
        if isinstance(value, (list, dict)) and len(value) == 0:
            return fallback
        if isinstance(value, str) and value.strip() == "":
            return fallback
        return str(value)
    
    def format_number(value, is_currency=False):
        if value is None:
            return "Brak danych"
        try:
            num = float(value)
            if is_currency:
                return f"${num:,.2f}"
            else:
                return f"{num:,.0f}" if num >= 1000 else f"{num}"
        except:
            return str(value)
    
    # Wygeneruj HTML
    formatted_html = html_template.format(
        keyword=metadata['keyword'],
        location_code=metadata['location_code'],
        language_code=metadata['language_code'],
        timestamp=metadata['export_timestamp'][:19].replace('T', ' '),
        keyword_name=safe_display(data.get('keyword_name')),
        search_volume=format_number(data.get('search_volume')),
        cpc=format_number(data.get('cpc'), is_currency=True),
        difficulty=format_number(data.get('keyword_difficulty')),
        json_data=json.dumps(export_data, indent=2, ensure_ascii=False, default=str)
    )
    
    return formatted_html

# ========================================
# MODUŁ KLASTROWANIA SEMANTYCZNEGO (MODUŁ 1)
# ========================================

# Inicjalizacja serwisu klastrowania (wykorzystuje to samo połączenie Supabase co orchestrator)
from app.api.full_analysis import supabase
clustering_service = SemanticClusteringService(supabase)

class ClusteringRequest(BaseModel):
    keyword_id: str  # UUID słowa kluczowego

class ArchitectureGenerationRequest(BaseModel):
    semantic_cluster_id: str  # UUID klastra semantycznego z Modułu 1
    architecture_type: str = 'silo'  # 'silo' lub 'clusters'
    domain: str = 'example.com'  # Domena docelowa
    save: bool = True  # Czy zapisać do bazy danych
    user_preferences: dict = {}  # Preferencje użytkownika

@app.post("/api/v6/clustering/start")
async def start_semantic_clustering(data: ClusteringRequest):
    """🚀 Uruchamia proces klastrowania semantycznego dla danego słowa kluczowego"""
    try:
        logger.info(f"🔬 [ENDPOINT] Otrzymano żądanie klastrowania dla keyword_id: {data.keyword_id}")
        logger.info(f"📨 [ENDPOINT] Dane wejściowe: {data.dict()}")
        
        # Uruchom proces klastrowania
        logger.info(f"⚡ [ENDPOINT] Rozpoczynam klastrowanie...")
        result = await clustering_service.process_semantic_clustering(data.keyword_id)
        
        logger.info(f"✅ [ENDPOINT] Klastrowanie zakończone: {result['groups_found']} grup z {result['total_phrases']} fraz")
        logger.info(f"📈 [ENDPOINT] Jakość: {result['quality_score']:.3f}, Koszt: ${result.get('cost_usd', 0.0):.6f}")
        
        response = {
            "success": True,
            "message": f"Klastrowanie zakończone pomyślnie",
            "data": result
        }
        
        logger.info(f"📤 [ENDPOINT] Zwracam odpowiedź: {response}")
        return response
        
    except Exception as e:
        logger.exception(f"❌ [ENDPOINT] Błąd klastrowania: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Błąd klastrowania: {str(e)}")

@app.get("/api/v6/clustering/results/{keyword_id}")
async def get_clustering_results(keyword_id: str):
    """📊 Pobiera wyniki klastrowania dla danego słowa kluczowego"""
    try:
        logger.info(f"📊 [ENDPOINT] Otrzymano żądanie wyników dla keyword_id: {keyword_id}")
        
        results = await clustering_service.get_clustering_results(keyword_id)
        
        if not results:
            logger.warning(f"⚠️ [ENDPOINT] Brak wyników klastrowania dla keyword_id: {keyword_id}")
            raise HTTPException(status_code=404, detail="Brak wyników klastrowania dla tego słowa")
        
        logger.info(f"✅ [ENDPOINT] Znaleziono wyniki: {len(results['groups'])} grup, {results['total_phrases']} fraz")
        # Bezpieczne logowanie grup
        groups_count = len(results['groups'])
        logger.info(f"📊 [ENDPOINT] Liczba grup: {groups_count}")
        
        response = {
            "success": True,
            "data": results
        }
        
        logger.info(f"📤 [ENDPOINT] Zwracam wyniki: {len(results['groups'])} grup")
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ [ENDPOINT] Błąd pobierania wyników: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Błąd pobierania wyników: {str(e)}")

@app.get("/api/v6/clustering/test-ai")
async def test_ai_connection():
    """🧪 Testuje połączenie z aktywnym AI provider"""
    try:
        result = await clustering_service.test_ai_connection()
        
        if result["success"]:
            logger.info(f"✅ Test {result.get('provider', 'AI').upper()} pomyślny: {result['message']}")
        else:
            logger.warning(f"⚠️ Test {result.get('provider', 'AI').upper()} nieudany: {result['error']}")
        
        return result
        
    except Exception as e:
        logger.exception(f"❌ Błąd testu AI: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Nieoczekiwany błąd podczas testu AI"
        }

@app.get("/api/v6/clustering/test-openai")
async def test_openai_connection():
    """🧪 Testuje połączenie z OpenAI API (dla kompatybilności)"""
    try:
        result = await clustering_service.test_openai_connection()
        
        if result["success"]:
            logger.info(f"✅ Test OpenAI pomyślny: {result['message']}")
        else:
            logger.warning(f"⚠️ Test OpenAI nieudany: {result['error']}")
        
        return result
        
    except Exception as e:
        logger.exception(f"❌ Błąd testu OpenAI: {str(e)}")
        return {
            "success": False,
            "error": str(e),
            "message": "Nieoczekiwany błąd podczas testu OpenAI"
        }

@app.get("/api/v6/clustering/debug/tables")
async def debug_clustering_tables():
    """🔍 Debug: Sprawdza czy tabele klastrowania istnieją w bazie"""
    try:
        logger.info(f"🔍 [DEBUG] Sprawdzanie tabel klastrowania...")
        
        tables_status = {}
        
        # Sprawdź semantic_clusters
        try:
            response = await clustering_service._execute_supabase_query_with_retry(
                lambda: clustering_service.supabase.table('semantic_clusters').select('id').limit(1).execute(),
                "check_semantic_clusters"
            )
            tables_status['semantic_clusters'] = {
                'exists': True,
                'sample_count': len(response.data) if response.data else 0
            }
        except Exception as e:
            tables_status['semantic_clusters'] = {
                'exists': False,
                'error': str(e)
            }
        
        # Sprawdź semantic_groups
        try:
            response = await clustering_service._execute_supabase_query_with_retry(
                lambda: clustering_service.supabase.table('semantic_groups').select('id').limit(1).execute(),
                "check_semantic_groups"
            )
            tables_status['semantic_groups'] = {
                'exists': True,
                'sample_count': len(response.data) if response.data else 0
            }
        except Exception as e:
            tables_status['semantic_groups'] = {
                'exists': False,
                'error': str(e)
            }
        
        # Sprawdź semantic_group_members (problematyczna tabela)
        try:
            response = await clustering_service._execute_supabase_query_with_retry(
                lambda: clustering_service.supabase.table('semantic_group_members').select('id').limit(1).execute(),
                "check_semantic_group_members"
            )
            tables_status['semantic_group_members'] = {
                'exists': True,
                'sample_count': len(response.data) if response.data else 0
            }
        except Exception as e:
            tables_status['semantic_group_members'] = {
                'exists': False,
                'error': str(e)
            }
        
        logger.info(f"🔍 [DEBUG] Status tabel: {tables_status}")
        
        return {
            "success": True,
            "tables": tables_status,
            "recommendation": "Jeśli semantic_group_members nie istnieje, uruchom create_semantic_tables.sql w Supabase SQL Editor"
        }
        
    except Exception as e:
        logger.exception(f"❌ [DEBUG] Błąd sprawdzania tabel: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Błąd sprawdzania tabel: {str(e)}")

@app.post("/api/v6/clustering/test-methods")
async def test_clustering_methods(data: ClusteringRequest):
    """🧪 Testuje i porównuje obie metody klastrowania (AI vs Legacy)"""
    try:
        logger.info(f"🧪 [ENDPOINT] Rozpoczynam test porównawczy metod klastrowania dla keyword_id: {data.keyword_id}")
        
        # Uruchom test porównawczy
        comparison_result = await clustering_service.test_clustering_methods(data.keyword_id)
        
        if "error" in comparison_result:
            logger.error(f"❌ [ENDPOINT] Błąd testu porównawczego: {comparison_result['error']}")
            raise HTTPException(status_code=500, detail=comparison_result['error'])
        
        # Loguj wyniki porównania
        ai_data = comparison_result.get("ai_clustering", {})
        legacy_data = comparison_result.get("legacy_pipeline", {})
        analysis = comparison_result.get("analysis", {})
        
        logger.info(f"🤖 [ENDPOINT] AI Clustering: {ai_data.get('num_clusters', 0)} grup, {ai_data.get('noise_ratio', 0):.1%} outliers")
        logger.info(f"🔧 [ENDPOINT] Legacy Pipeline: {legacy_data.get('num_clusters', 0)} grup, {legacy_data.get('noise_ratio', 0):.1%} outliers")
        logger.info(f"🏆 [ENDPOINT] Zwycięzca: {analysis.get('winner', 'unknown')}")
        
        response = {
            "success": True,
            "message": "Test porównawczy zakończony pomyślnie",
            "data": comparison_result
        }
        
        return response
        
    except HTTPException:
        raise
    except Exception as e:
        logger.exception(f"❌ [ENDPOINT] Błąd testu porównawczego: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Błąd testu porównawczego: {str(e)}")

@app.get("/api/v6/clustering/config")
async def get_clustering_config():
    """⚙️ Pobiera aktualną konfigurację systemu klastrowania"""
    try:
        config = {
            "use_ai_clustering": clustering_service.use_ai_clustering,
            "ai_provider": clustering_service.ai_provider,
            "openai_model": clustering_service.openai_model,
            "claude_model": clustering_service.claude_model,
            "openai_client_available": clustering_service.openai_client is not None,
            "claude_client_available": clustering_service.claude_client is not None,
            "embedding_model": clustering_service.embedding_model,
            "embedding_dimensions": clustering_service.embedding_dimensions,
            "recommended_settings": {
                "USE_AI_CLUSTERING": "true",
                "AI_PROVIDER": "openai",
                "note": "OpenAI zawsze wymagany dla embeddingów, nawet gdy używasz Claude do klastrowania"
            }
        }
        
        logger.info(f"⚙️ [ENDPOINT] Zwracam konfigurację: AI={config['use_ai_clustering']}, Provider={config['ai_provider']}")
        
        return {
            "success": True,
            "config": config
        }
        
    except Exception as e:
        logger.exception(f"❌ [ENDPOINT] Błąd pobierania konfiguracji: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Błąd pobierania konfiguracji: {str(e)}")

# ========================================
# MODUŁ 3: ARCHITECTURE GENERATOR ENDPOINTS
# ========================================

@app.post("/api/v6/architecture/generate")
async def generate_architecture(data: ArchitectureGenerationRequest):
    """🏗️ GŁÓWNY ENDPOINT - Generuje architekturę strony na podstawie klastra semantycznego"""
    try:
        logger.info(f"🏗️ [ARCHITECTURE] Otrzymano żądanie generowania dla cluster: {data.semantic_cluster_id}")
        logger.info(f"🏗️ [ARCHITECTURE] Parametry: type={data.architecture_type}, domain={data.domain}")
        
        # Pobierz dane klastra semantycznego z bazy danych (używając funkcji z klastrowania)
        cluster_data = await get_semantic_cluster_data_for_architecture(data.semantic_cluster_id)
        
        if not cluster_data['success']:
            logger.error(f"❌ [ARCHITECTURE] Nie znaleziono klastra: {data.semantic_cluster_id}")
            raise HTTPException(status_code=404, detail=f"Semantic cluster not found: {data.semantic_cluster_id}")
        
        # Sprawdź czy klaster ma wystarczająco danych
        if cluster_data['data']['groups_found'] < 2:
            logger.warning(f"⚠️ [ARCHITECTURE] Za mało grup w klastrze: {cluster_data['data']['groups_found']}")
            raise HTTPException(status_code=400, detail="Klaster musi mieć co najmniej 2 grupy semantyczne")
        
        # Inicjalizuj generator architektury
        try:
            architecture_generator = ArchitectureGenerator(
                cluster_data=cluster_data['data'],
                arch_type=data.architecture_type,
                domain=data.domain,
                supabase_client=supabase if data.save else None,
                user_preferences=data.user_preferences
            )
        except ValueError as ve:
            logger.error(f"❌ [ARCHITECTURE] Błąd inicjalizacji generatora: {str(ve)}")
            raise HTTPException(status_code=400, detail=f"Generator initialization error: {str(ve)}")
        
        # Generuj architekturę
        if data.save:
            logger.info("💾 [ARCHITECTURE] Generuję i zapisuję architekturę...")
            result = await architecture_generator.generate_and_save(user_id=None)  # TODO: prawdziwy user_id z auth
        else:
            logger.info("🔄 [ARCHITECTURE] Generuję architekturę (bez zapisu)...")
            result = await architecture_generator.generate()
        
        # Przygotuj odpowiedź
        response = {
            "success": True,
            "message": "Architektura wygenerowana pomyślnie",
            "data": result,
            "saved_to_database": data.save and result.get('database_result', {}).get('success', False),
            "meta": {
                "processing_time": result.get('processing_time', 0),
                "total_pages": result.get('stats', {}).get('total_pages', 0),
                "cross_links_found": result.get('stats', {}).get('cross_links_found', 0),
                "seo_score": result.get('seo_score', 0)
            }
        }
        
        logger.info(f"✅ [ARCHITECTURE] Architektura wygenerowana: {result.get('stats', {}).get('total_pages', 0)} stron, SEO: {result.get('seo_score', 0)}/100")
        
        # Convert numpy types to Python native types for JSON serialization
        response = convert_numpy_types(response)
        return response
        
    except HTTPException:
        raise  # Re-raise HTTP exceptions
    except Exception as e:
        logger.exception(f"❌ [ARCHITECTURE] Błąd generowania architektury: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Architecture generation failed: {str(e)}")

@app.get("/api/v6/architecture/list")
async def list_architectures(semantic_cluster_id: str = None, limit: int = 10, offset: int = 0):
    """📋 Lista wygenerowanych architektur"""
    try:
        logger.info(f"📋 [ARCHITECTURE] Lista architektur: cluster={semantic_cluster_id}, limit={limit}")
        
        # Bezpośrednie zapytanie do Supabase
        query = supabase.table('architectures').select('*')
        
        if semantic_cluster_id:
            query = query.eq('semantic_cluster_id', semantic_cluster_id)
        
        query = query.order('created_at', desc=True).limit(limit).offset(offset)
        
        response = query.execute()
        result = {
            'success': True,
            'data': response.data,
            'count': len(response.data) if response.data else 0
        }
        
        if result['success']:
            logger.info(f"✅ [ARCHITECTURE] Zwrócono {result['count']} architektur")
            return {"success": True, "architectures": result['data'], "total": result['count']}
        else:
            logger.error(f"❌ [ARCHITECTURE] Błąd: {result.get('error', 'Unknown error')}")
            raise HTTPException(status_code=500, detail=result.get('error', 'Database error'))
            
    except Exception as e:
        logger.error(f"❌ [ARCHITECTURE] list_architectures error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to list architectures: {str(e)}")

@app.get("/api/v6/architecture/test-connection")
async def test_architecture_module():
    """🧪 Test połączenia modułu architektury"""
    try:
        logger.info("🧪 [ARCHITECTURE] Test połączenia modułu...")
        
        # Test database connection
        test_query = supabase.table('architectures').select('id').limit(1).execute()
        db_status = "connected" if test_query else "error"
        
        # Test LLM availability
        llm_status = []
        if os.getenv("OPENAI_API_KEY"):
            llm_status.append("OpenAI")
        if os.getenv("ANTHROPIC_API_KEY"):
            llm_status.append("Claude")
        
        # Test architecture generator initialization
        try:
            test_cluster_data = {
                'seed_keyword': 'test',
                'groups': [{'name': 'test_group', 'phrases': ['test'], 'embeddings_available': False}]
            }
            test_generator = ArchitectureGenerator(test_cluster_data)
            generator_status = "working"
        except Exception as gen_error:
            generator_status = f"error: {str(gen_error)}"
        
        result = {
            "success": True,
            "module": "architecture_generator",
            "version": "1.0.0",
            "status": {
                "database": db_status,
                "llm_clients": llm_status,
                "generator": generator_status
            },
            "endpoints": [
                "POST /api/v6/architecture/generate",
                "GET /api/v6/architecture/list", 
                "GET /api/v6/architecture/{id}",
                "DELETE /api/v6/architecture/{id}",
                "GET /api/v6/architecture/test-connection"
            ]
        }
        
        logger.info(f"✅ [ARCHITECTURE] Test modułu: database={db_status}, LLM={len(llm_status)}, generator={generator_status}")
        return result
        
    except Exception as e:
        logger.exception(f"❌ [ARCHITECTURE] Błąd testu modułu: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Module test failed: {str(e)}")

@app.get("/api/v6/architecture/{architecture_id}")
async def get_architecture_details(architecture_id: str):
    """🔍 Pobiera szczegóły konkretnej architektury"""
    try:
        logger.info(f"🔍 [ARCHITECTURE] Pobieranie szczegółów: {architecture_id}")
        
        # Bezpośrednie zapytanie do Supabase
        response = supabase.table('architectures').select('*').eq('id', architecture_id).execute()
        
        if not response.data:
            raise HTTPException(status_code=404, detail="Architecture not found")
        
        architecture = response.data[0]
        
        # Pobierz powiązane strony
        pages_response = supabase.table('architecture_pages').select('*').eq('architecture_id', architecture_id).execute()
        
        result = {
            'success': True,
            'data': {
                'architecture': architecture,
                'pages': pages_response.data or []
            }
        }
        
        logger.info(f"✅ [ARCHITECTURE] Szczegóły pobrane: {len(result['data']['pages'])} stron")
        return result
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [ARCHITECTURE] get_architecture_details error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to get architecture: {str(e)}")

@app.delete("/api/v6/architecture/{architecture_id}")
async def delete_architecture(architecture_id: str):
    """🗑️ Usuwa architekturę"""
    try:
        logger.info(f"🗑️ [ARCHITECTURE] Usuwanie architektury: {architecture_id}")
        
        # Sprawdź czy architektura istnieje
        check_response = supabase.table('architectures').select('id').eq('id', architecture_id).execute()
        
        if not check_response.data:
            raise HTTPException(status_code=404, detail="Architecture not found")
        
        # Usuń powiązane strony
        supabase.table('architecture_pages').delete().eq('architecture_id', architecture_id).execute()
        
        # Usuń architekturę
        delete_response = supabase.table('architectures').delete().eq('id', architecture_id).execute()
        
        logger.info(f"✅ [ARCHITECTURE] Architektura usunięta: {architecture_id}")
        return {"success": True, "message": "Architecture deleted successfully"}
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"❌ [ARCHITECTURE] delete_architecture error: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to delete architecture: {str(e)}")

# Helper function do pobierania danych klastra
async def get_semantic_cluster_data_for_architecture(semantic_cluster_id: str):
    """
    Pobiera dane klastra semantycznego z embeddingami dla generatora architektury
    Wykorzystuje ten sam mechanizm co Moduł 1
    """
    try:
        logger.info(f"📊 [ARCHITECTURE] Pobieranie danych klastra: {semantic_cluster_id}")
        
        # 1. Pobierz główny klaster
        cluster_query = supabase.table('semantic_clusters').select(
            'id, cluster_name, total_phrases, quality_score, created_at'
        ).eq('id', semantic_cluster_id).execute()
        
        if not cluster_query.data:
            return {"success": False, "error": "Semantic cluster not found"}
        
        cluster = cluster_query.data[0]
        
        # 2. Pobierz wszystkie grupy w klastrze
        groups_query = supabase.table('semantic_groups').select(
            'id, group_label, group_number, phrases_count, avg_similarity_score'
        ).eq('semantic_cluster_id', semantic_cluster_id).order('group_number').execute()
        
        if not groups_query.data:
            return {"success": False, "error": "No groups found in cluster"}
        
        # 3. Dla każdej grupy pobierz członków Z EMBEDDINGAMI I VOLUME
        enriched_groups = []
        for group in groups_query.data:
            # Pobierz członków grupy z embeddingami
            members_query = supabase.table('semantic_group_members').select(
                'phrase, embedding_vector, similarity_to_centroid, source_table, source_id'
            ).eq('group_id', group['id']).execute()
            if not members_query.data:
                continue
            # Wyciągnij frazy i embeddingi
            phrases = []
            phrases_with_details = []
            embeddings = []
            for member in members_query.data:
                phrase = member['phrase']
                # Pobierz search_volume i cpc z tabeli keywords
                kw_query = supabase.table('keywords').select('search_volume, cpc').eq('keyword', phrase).limit(1).execute()
                if kw_query.data:
                    search_volume = kw_query.data[0].get('search_volume', 0)
                    cpc = kw_query.data[0].get('cpc', 0.0)
                else:
                    search_volume = 0
                    cpc = 0.0
                phrases.append(phrase)
                phrases_with_details.append({
                    'phrase': phrase,
                    'search_volume': search_volume,
                    'cpc': cpc
                })
                if member.get('embedding_vector'):
                    embeddings.append(member['embedding_vector'])
            # Oblicz centroid grupy (średnia embeddingów)
            group_centroid = None
            if embeddings:
                try:
                    embeddings_array = np.array(embeddings)
                    group_centroid = np.mean(embeddings_array, axis=0).tolist()
                except Exception as e:
                    logger.warning(f"⚠️ [ARCHITECTURE] Centroid calculation failed for group {group['group_label']}: {e}")
            enriched_groups.append({
                "group_id": group['id'],
                "name": group['group_label'],
                "phrases": phrases,
                "phrases_with_details": phrases_with_details,
                "phrase_count": len(phrases),
                "similarity_score": group.get('avg_similarity_score', 0.85),
                "group_number": group.get('group_number', 0),
                "embeddings_available": len(embeddings) > 0,
                "group_centroid": group_centroid,  # Dla strategic cross-linking
                "individual_embeddings": embeddings  # Dla advanced analysis
            })
        
        # 4. Extract seed keyword from cluster name
        seed_keyword = cluster.get('cluster_name', '').replace('AI Clustering: ', '').strip()
        if not seed_keyword:
            seed_keyword = "unknown"
        
        result_data = {
            "id": cluster['id'],
            "semantic_cluster_id": cluster['id'],
            "seed_keyword": seed_keyword,
            "cluster_name": cluster.get('cluster_name', ''),
            "total_phrases": cluster.get('total_phrases', 0),
            "quality_score": cluster.get('quality_score', 0.0),
            "groups_found": len(enriched_groups),
            "clusters": enriched_groups,  # For compatibility
            "groups": enriched_groups,    # Preferred naming
            "created_at": cluster.get('created_at'),
            "embeddings_ready": any(g.get('embeddings_available', False) for g in enriched_groups),
            "original_cluster_data": {
                "cluster": cluster,
                "groups_raw": groups_query.data,
                "enriched_groups": enriched_groups
            }
        }
        
        logger.info(f"✅ [ARCHITECTURE] Dane klastra pobrane: {len(enriched_groups)} grup, embeddings={result_data['embeddings_ready']}")
        return {
            "success": True,
            "data": result_data
        }
        
    except Exception as e:
        logger.error(f"❌ [ARCHITECTURE] Error fetching semantic cluster data: {str(e)}")
        return {"success": False, "error": f"Data fetch error: {str(e)}"}

# Inicjalizacja serwisu content briefów
content_brief_service = ContentBriefGeneratorService(supabase)

# Inicjalizacja serwisu content scaffold generator (Moduł 5)
from app.services.content_scaffold_generator import ContentScaffoldGenerator
content_scaffold_service = ContentScaffoldGenerator(supabase)

import logging
content_brief_api_logger = logging.getLogger("content_brief_api")
content_scaffold_api_logger = logging.getLogger("content_scaffold_api")

@app.post("/api/content-briefs/generate/{page_id}")
async def generate_content_brief(page_id: str):
    content_brief_api_logger.info(f"[API] Start generate_content_brief page_id={page_id}")
    try:
        result = await content_brief_service.generate_content_brief(page_id)
        content_brief_api_logger.info(f"[API] End generate_content_brief page_id={page_id} result={result}")
        return result
    except Exception as e:
        content_brief_api_logger.error(f"[API] Error generate_content_brief page_id={page_id} error={e}")
        return {"success": False, "error": str(e)}

@app.post("/api/content-briefs/batch/{architecture_id}")
async def generate_all_content_briefs(architecture_id: str):
    content_brief_api_logger.info(f"[API] Start generate_all_content_briefs architecture_id={architecture_id}")
    try:
        result = await content_brief_service.generate_all_briefs_for_architecture(architecture_id)
        content_brief_api_logger.info(f"[API] End generate_all_content_briefs architecture_id={architecture_id} result={result}")
        return result
    except Exception as e:
        content_brief_api_logger.error(f"[API] Error generate_all_content_briefs architecture_id={architecture_id} error={e}")
        return {"success": False, "error": str(e)}

@app.get("/api/content-briefs/{brief_id}")
async def get_content_brief(brief_id: str):
    content_brief_api_logger.info(f"[API] Start get_content_brief brief_id={brief_id}")
    try:
        result = await content_brief_service.get_content_brief(brief_id)
        content_brief_api_logger.info(f"[API] End get_content_brief brief_id={brief_id} result={result}")
        if result:
            return {"success": True, "data": result}
        else:
            return {"success": False, "error": "Nie znaleziono brief"}
    except Exception as e:
        content_brief_api_logger.error(f"[API] Error get_content_brief brief_id={brief_id} error={e}")
        return {"success": False, "error": str(e)}

@app.get("/api/content-briefs/architecture/{architecture_id}/summary")
async def get_architecture_briefs_summary(architecture_id: str):
    content_brief_api_logger.info(f"[API] Start get_architecture_briefs_summary architecture_id={architecture_id}")
    try:
        result = await content_brief_service.get_architecture_briefs_summary(architecture_id)
        content_brief_api_logger.info(f"[API] End get_architecture_briefs_summary architecture_id={architecture_id} result={result}")
        return {"success": True, "data": result}
    except Exception as e:
        content_brief_api_logger.error(f"[API] Error get_architecture_briefs_summary architecture_id={architecture_id} error={e}")
        return {"success": False, "error": str(e)}

# ========================================
# MODUŁ 5: CONTENT SCAFFOLD GENERATOR ENDPOINTS
# ========================================

@app.post("/api/content-briefs/{brief_id}/generate-comprehensive-scaffold")
async def generate_comprehensive_scaffold(brief_id: str):
    """🧠 MODUŁ 5: Generuje ultra-szczegółowy content scaffold"""
    content_scaffold_api_logger.info(f"[API] Start generate_comprehensive_scaffold brief_id={brief_id}")
    
    try:
        # Użyj nowej głównej metody, która obsługuje cały flow + persistence
        content_scaffold_api_logger.info(f"[API] Generating complete scaffold with persistence...")
        result = await content_scaffold_service.generate_and_save_scaffold(brief_id)
        
        scaffold_result = result['scaffold_data']
        context_size = result['context_pack_size']
        
        # Przygotuj meta-informacje z result
        meta_info = result.get('metadata', {})
        meta_info.update({
            "context_pack_size": context_size,
            "sections_count": len(scaffold_result.get("content_sections", [])),
            "opportunities_integrated": len(scaffold_result.get("faq_integration_strategy", [])),
            "strategic_links": sum(len(section.get("strategic_linking", [])) for section in scaffold_result.get("content_sections", [])),
            "scaffold_id": result.get('scaffold_id'),
            "database_saved": result.get('database_saved', False),
            "generated_at": datetime.now().isoformat()
        })
        
        content_scaffold_api_logger.info(f"[API] Scaffold generated and saved: {meta_info['sections_count']} sections, {meta_info['strategic_links']} strategic links, ID: {meta_info['scaffold_id']}")
        
        response = {
            "success": True,
            "data": scaffold_result,
            "meta": meta_info
        }
        
        content_scaffold_api_logger.info(f"[API] End generate_comprehensive_scaffold brief_id={brief_id} success=True")
        return response
        
    except Exception as e:
        content_scaffold_api_logger.error(f"[API] Error generate_comprehensive_scaffold brief_id={brief_id} error={e}")
        return {
            "success": False, 
            "error": str(e),
            "meta": {
                "brief_id": brief_id,
                "error_at": datetime.now().isoformat()
            }
        }

@app.get("/api/content-briefs/{brief_id}/scaffold")
async def get_content_scaffold(brief_id: str):
    """📋 Pobiera zapisany content scaffold dla briefu"""
    content_scaffold_api_logger.info(f"[API] Start get_content_scaffold brief_id={brief_id}")
    
    try:
        # Pobierz najnowszy scaffold dla tego briefu
        response = supabase.table('content_scaffolds').select('*').eq('brief_id', brief_id).order('created_at', desc=True).limit(1).execute()
        
        if not response.data:
            content_scaffold_api_logger.warning(f"[API] No scaffold found for brief_id={brief_id}")
            return {
                "success": False,
                "error": "No scaffold found for this brief",
                "meta": {"brief_id": brief_id}
            }
        
        scaffold_data = response.data[0]
        
        content_scaffold_api_logger.info(f"[API] End get_content_scaffold brief_id={brief_id} success=True")
        return {
            "success": True,
            "data": {
                "scaffold_id": scaffold_data.get('id'),
                "scaffold_data": scaffold_data.get('scaffold_data'),
                "meta_info": scaffold_data.get('meta_info'),
                "created_at": scaffold_data.get('created_at')
            }
        }
        
    except Exception as e:
        content_scaffold_api_logger.error(f"[API] Error get_content_scaffold brief_id={brief_id} error={e}")
        return {
            "success": False,
            "error": str(e),
            "meta": {"brief_id": brief_id}
        }

@app.get("/api/content-scaffolds/{scaffold_id}")
async def get_scaffold_by_id(scaffold_id: str):
    """📋 Pobiera content scaffold po ID"""
    content_scaffold_api_logger.info(f"[API] Start get_scaffold_by_id scaffold_id={scaffold_id}")
    
    try:
        scaffold = await content_scaffold_service.get_scaffold_by_id(scaffold_id)
        
        if not scaffold:
            content_scaffold_api_logger.warning(f"[API] No scaffold found for scaffold_id={scaffold_id}")
            return {
                "success": False,
                "error": "Scaffold not found",
                "meta": {"scaffold_id": scaffold_id}
            }
        
        # 🔍 DEBUG: Check if GEO fields are in scaffold_data from DB
        scaffold_data = scaffold.get('scaffold_data', {})
        if isinstance(scaffold_data, dict) and scaffold_data.get('content_sections'):
            if len(scaffold_data['content_sections']) > 0:
                first_section = scaffold_data['content_sections'][0]
                geo_fields_present = {
                    'ai_answer_target': 'ai_answer_target' in first_section,
                    'structural_format': 'structural_format' in first_section,
                    'information_gain': 'information_gain' in first_section,
                    'trust_signals': 'trust_signals' in first_section,
                    'entity_connections': 'entity_connections' in first_section,
                    'semantic_citation': 'semantic_citation' in first_section
                }
                content_scaffold_api_logger.info(f"🔍 [API DEBUG] GEO fields in scaffold from DB: {geo_fields_present}")
        
        content_scaffold_api_logger.info(f"[API] End get_scaffold_by_id scaffold_id={scaffold_id} success=True")
        return {
            "success": True,
            "data": scaffold
        }
        
    except Exception as e:
        content_scaffold_api_logger.error(f"[API] Error get_scaffold_by_id scaffold_id={scaffold_id} error={e}")
        return {
            "success": False,
            "error": str(e),
            "meta": {"scaffold_id": scaffold_id}
        }

@app.get("/api/content-scaffolds/test-connection")
async def test_content_scaffold_connection():
    """🧪 Test połączenia Modułu 5 - Content Scaffold Generator"""
    content_scaffold_api_logger.info("[API] Testing content scaffold generator connection...")
    
    try:
        # Test AI providers connection
        ai_status = {
            "provider": content_scaffold_service.ai_provider,
            "openai": "unknown",
            "claude": "unknown"
        }
        
        try:
            if content_scaffold_service.openai_client:
                test_response = content_scaffold_service.openai_client.chat.completions.create(
                    model="gpt-3.5-turbo",
                    messages=[{"role": "user", "content": "Test"}],
                    max_tokens=5
                )
                ai_status["openai"] = "connected"
            else:
                ai_status["openai"] = "not_configured"
        except Exception as openai_error:
            ai_status["openai"] = f"error: {str(openai_error)}"
        
        try:
            if content_scaffold_service.claude_client:
                ai_status["claude"] = "configured"
            else:
                ai_status["claude"] = "not_configured"
        except Exception as claude_error:
            ai_status["claude"] = f"error: {str(claude_error)}"
        
        # Test database connection
        db_status = "unknown"
        try:
            test_query = supabase.table('content_briefs').select('id').limit(1).execute()
            db_status = "connected"
        except Exception as db_error:
            db_status = f"error: {str(db_error)}"
        
        # Test log directory
        # Dla Railway użyj /tmp, lokalnie użyj bieżącego katalogu
        log_dir = "/tmp" if os.getenv("RAILWAY_ENVIRONMENT") else "."
        log_dir_status = "writable" if os.path.exists(log_dir) or os.access(os.path.dirname(log_dir), os.W_OK) else "not_accessible"
        
        result = {
            "success": True,
            "module": "content_scaffold_generator",
            "version": "2.0.0",
            "status": {
                "ai_providers": ai_status,
                "database": db_status,
                "models": {
                    "openai": content_scaffold_service.openai_model,
                    "claude": content_scaffold_service.claude_model,
                    "gpt5": content_scaffold_service.gpt5_model
                },
                "log_directory": log_dir_status,
                "log_path": log_dir
            },
            "endpoints": [
                "POST /api/content-briefs/{brief_id}/generate-comprehensive-scaffold",
                "GET /api/content-briefs/{brief_id}/scaffold",
                "GET /api/content-scaffolds/test-connection"
            ],
            "capabilities": [
                "Enhanced context pack utilization with concrete examples",
                "Psychology-driven scaffold creation",
                "Strategic linking integration",
                "Content opportunities analysis",
                "FAQ psychology integration", 
                "CTA optimization guidance",
                "Schema markup suggestions",
                "AI interaction logging to disk",
                "Improved prompt engineering with specific instructions",
                "Anti-template approach for personalized scaffolds"
            ]
        }
        
        content_scaffold_api_logger.info(f"[API] Content scaffold test completed: AI={ai_status['provider']}, DB={db_status}")
        return result
        
    except Exception as e:
        content_scaffold_api_logger.error(f"[API] Error testing content scaffold connection: {e}")
        return {
            "success": False,
            "error": str(e),
            "module": "content_scaffold_generator"
        }

@app.get("/api/v6/architecture/{architecture_id}/links")
async def get_architecture_links(architecture_id: str):
    """
    🔗 Endpoint testowy do weryfikacji zapisanych linków w architecture_links
    """
    try:
        logger.info(f"🔗 [API] Pobieranie linków dla architecture: {architecture_id}")
        
        response = supabase.table('architecture_links').select(
            'id, from_page_id, to_page_id, link_type, anchor_text, priority, source, enabled, '
            'similarity_score, funnel_stage, placement, link_context, '
            'from_page:architecture_pages!architecture_links_from_page_id_fkey(name, url_path), '
            'to_page:architecture_pages!architecture_links_to_page_id_fkey(name, url_path)'
        ).eq('architecture_id', architecture_id).order('priority', desc=True).execute()
        
        if not response.data:
            return {
                "success": True,
                "architecture_id": architecture_id,
                "total_links": 0,
                "links": [],
                "summary": {
                    "hierarchy_links": 0,
                    "bridge_links": 0,
                    "funnel_links": 0
                }
            }
        
        # Grupuj linki według typu
        hierarchy_links = [l for l in response.data if l['link_type'] == 'hierarchy']
        bridge_links = [l for l in response.data if l['link_type'] == 'bridge']
        funnel_links = [l for l in response.data if l['link_type'] == 'funnel']
        
        # Formatuj dane dla odpowiedzi
        formatted_links = []
        for link in response.data:
            from_page = link.get('from_page', {})
            to_page = link.get('to_page', {})
            
            formatted_link = {
                "id": link['id'],
                "link_type": link['link_type'],
                "source": link['source'],
                "priority": link['priority'],
                "enabled": link['enabled'],
                "from_page": {
                    "id": link['from_page_id'],
                    "name": from_page.get('name', ''),
                    "url": from_page.get('url_path', '')
                },
                "to_page": {
                    "id": link['to_page_id'],
                    "name": to_page.get('name', ''),
                    "url": to_page.get('url_path', '')
                },
                "anchor_text": link.get('anchor_text', ''),
                "placement": link.get('placement', ''),
                "context": link.get('link_context', ''),
                "similarity_score": link.get('similarity_score'),
                "funnel_stage": link.get('funnel_stage', '')
            }
            formatted_links.append(formatted_link)
        
        logger.info(f"✅ [API] Znaleziono {len(response.data)} linków")
        
        return {
            "success": True,
            "architecture_id": architecture_id,
            "total_links": len(response.data),
            "links": formatted_links,
            "summary": {
                "hierarchy_links": len(hierarchy_links),
                "bridge_links": len(bridge_links),
                "funnel_links": len(funnel_links)
            }
        }
        
    except Exception as e:
        logger.error(f"❌ [API] Błąd pobierania architecture links: {e}")
        raise HTTPException(status_code=500, detail=str(e))

@app.get("/api/debug/scaffold-logs")
async def get_scaffold_logs(limit: int = 5):
    """🔍 DEBUG: Pobiera ostatnie logi generowania scaffoldów z /tmp"""
    try:
        import glob
        log_dir = "/tmp" if os.getenv("RAILWAY_ENVIRONMENT") else "."
        log_pattern = os.path.join(log_dir, "scaffold_generation_*.txt")
        log_files = sorted(glob.glob(log_pattern), key=os.path.getmtime, reverse=True)[:limit]
        
        logs_data = []
        for log_file in log_files:
            try:
                with open(log_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                    logs_data.append({
                        "filename": os.path.basename(log_file),
                        "size": len(content),
                        "preview": content[:2000] + "..." if len(content) > 2000 else content,
                        "full_content": content
                    })
            except Exception as e:
                logs_data.append({
                    "filename": os.path.basename(log_file),
                    "error": str(e)
                })
        
        return {
            "success": True,
            "log_dir": log_dir,
            "total_logs": len(log_files),
            "logs": logs_data
        }
    except Exception as e:
        logger.error(f"❌ [DEBUG] Error reading logs: {e}")
        return {"success": False, "error": str(e)}

if __name__ == "__main__":
    import uvicorn
    port = int(os.getenv("PORT", 8000))  # Railway przekaże PORT
    uvicorn.run(app, host="0.0.0.0", port=port)
