import asyncio
import os
import time
from typing import List, Dict, Tuple, Optional

# Dodaj katalog główny do path
import sys
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app.services.semantic_clustering import SemanticClusteringService
from supabase import create_client, Client as SupabaseClient

# Wczytaj zmienne środowiskowe
from dotenv import load_dotenv
load_dotenv()

# Ustawienia
SUPABASE_URL = os.getenv("SUPABASE_URL")
SUPABASE_KEY = os.getenv("SUPABASE_KEY")

# Włącz Super Simple Clustering
os.environ["USE_SUPER_SIMPLE_CLUSTERING"] = "true"
os.environ["USE_UNIVERSAL_CLUSTERING"] = "false"

# Dane testowe - soczewki kontaktowe
TEST_PHRASES = [
    "soczewki kontaktowe",
    "soczewki jednodniowe",
    "soczewki miesięczne",
    "soczewki roczne",
    "soczewki toryczne",
    "soczewki progresywne",
    "soczewki kolorowe",
    "soczewki na astygmatyzm",
    "acuvue soczewki",
    "biofinity soczewki",
    "dailies soczewki",
    "vision express soczewki",
    "kodano soczewki",
    "family optic soczewki",
    "jak założyć soczewki",
    "jak wyjąć soczewki",
    "co to są soczewki",
    "soczewki do oczu",
    "ile kosztują soczewki",
    "tanie soczewki",
    "soczewki cena",
    "najlepsze soczewki",
    "gdzie kupić soczewki",
    "soczewki w aptece",
    "soczewki online",
    "soczewki z filtrem uv",
    "soczewki dla dzieci",
    "soczewki po czterdziestce",
    "soczewki silikon hydrogel",
    "soczewki multifokalne",
    "soczewki jednorazowe",
    "soczewki miękkie",
    "soczewki twarde",
    "soczewki kontaktowe opinie",
    "soczewki na receptę",
    "soczewki bez recepty",
    "soczewki do komputera",
    "soczewki na noc",
    "soczewki ortho-k",
    "soczewki na dobre widzenie",
    "soczewki na krótkowzroczność",
    "soczewki na dalekowzroczność",
    "soczewki na zaćmę",
    "soczewki po operacji",
    "soczewki johnson & johnson",
    "soczewki cooper vision",
    "soczewki alcon",
    "soczewki bausch & lomb",
    "soczewki menicon",
    "soczewki air optix",
    "soczewki proclear",
    "soczewki moist",
    "soczewki ultra",
    "soczewki plus",
    "soczewki oasys",
    "soczewki trueye",
    "soczewki define",
    "soczewki natural",
    "soczewki comfort",
    "soczewki focus",
    "soczewki soflens",
    "soczewki purevision",
    "soczewki clear",
    "soczewki total",
    "soczewki 1 day",
    "soczewki 2 week",
    "soczewki 30 dni",
    "soczewki 90 dni",
    "soczewki 365 dni",
    "soczewki do pływania",
    "soczewki do sportu",
    "soczewki do makijażu",
    "soczewki do pracy",
    "soczewki do czytania",
    "soczewki do jazdy",
    "soczewki do teatru",
    "soczewki do kina",
    "soczewki do tańca",
    "soczewki do biegania",
    "soczewki do fitnessu",
    "soczewki do tenisa",
    "soczewki do golfa",
    "soczewki do żeglarstwa",
    "soczewki do narciarstwa",
    "soczewki do paintball",
    "soczewki do airsoft",
    "soczewki do fotografii",
    "soczewki do modelingu",
    "soczewki do cosplay",
    "soczewki do halloweenu",
    "soczewki do karnawału",
    "soczewki do imprez",
    "soczewki do sesji",
    "soczewki do ślubu",
    "soczewki do studniówki",
    "soczewki do walentynek",
    "soczewki do randki",
    "soczewki do pracy biurowej",
    "soczewki do komputera niebieskie",
    "soczewki anti blue light",
    "soczewki z filtrem światła",
    "soczewki hybrydowe",
    "soczewki skleralne",
    "soczewki orthokeratologiczne",
    "soczewki na noc ortho k",
    "soczewki dream lite",
    "soczewki kontaktowe warszawa",
    "soczewki kontaktowe kraków",
    "soczewki kontaktowe gdańsk",
    "soczewki kontaktowe poznań",
    "soczewki kontaktowe wrocław",
    "soczewki kontaktowe łódź",
    "soczewki kontaktowe szczecin",
    "soczewki kontaktowe lublin",
    "soczewki kontaktowe katowice",
    "soczewki kontaktowe bydgoszcz",
    "soczewki kontaktowe toruń",
    "soczewki kontaktowe rzeszów",
    "soczewki kontaktowe opole",
    "soczewki kontaktowe kielce",
    "soczewki kontaktowe olsztyn",
    "soczewki kontaktowe białystok",
    "soczewki kontaktowe gorzów",
    "soczewki kontaktowe zielona góra",
    "soczewki kontaktowe płock",
    "soczewki kontaktowe radom",
    "soczewki kontaktowe tarnów",
    "soczewki kontaktowe rybnik",
    "soczewki kontaktowe sosnowiec",
    "soczewki kontaktowe gliwice",
    "soczewki kontaktowe zabrze",
    "soczewki kontaktowe tychy",
    "soczewki kontaktowe dąbrowa górnicza",
    "soczewki kontaktowe częstochowa",
    "soczewki kontaktowe jaworzno",
    "soczewki kontaktowe mysłowice",
    "soczewki kontaktowe siemianowice śląskie",
    "soczewki kontaktowe piekary śląskie",
    "soczewki kontaktowe świętochłowice",
    "soczewki kontaktowe chorzów",
    "soczewki kontaktowe będzin",
    "soczewki kontaktowe czeladź",
    "soczewki kontaktowe sławków"
]

async def test_super_simple_clustering():
    print("=" * 70)
    print("🚀 **TEST SUPER SIMPLE CLUSTERING**")
    print("=" * 70)
    
    # Utwórz klienta Supabase
    supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)
    
    # Utwórz serwis
    service = SemanticClusteringService(supabase)
    
    # Testuj flagi
    use_super_simple = os.getenv("USE_SUPER_SIMPLE_CLUSTERING", "false").lower() == "true"
    use_universal = os.getenv("USE_UNIVERSAL_CLUSTERING", "false").lower() == "true"
    
    print(f"🔧 **KONFIGURACJA:**")
    print(f"   - USE_SUPER_SIMPLE_CLUSTERING: {use_super_simple}")
    print(f"   - USE_UNIVERSAL_CLUSTERING: {use_universal}")
    print(f"   - Liczba testowych fraz: {len(TEST_PHRASES)}")
    
    # Symuluj dane
    service.all_phrases = [{"text": phrase} for phrase in TEST_PHRASES]
    service._current_seed_keyword = "soczewki kontaktowe"
    
    # Stwórz fake embeddings
    import numpy as np
    embeddings = np.random.random((len(TEST_PHRASES), 1536))
    
    print("\n🧪 **URUCHAMIANIE TESTU...**")
    
    start_time = time.time()
    
    try:
        # Wywołaj clustering
        cluster_labels, quality_metrics = await service._perform_clustering(embeddings)
        
        duration = time.time() - start_time
        
        print(f"\n✅ **WYNIKI:**")
        print(f"   - Czas przetwarzania: {duration:.2f}s")
        print(f"   - Metoda: {quality_metrics.get('method', 'unknown')}")
        print(f"   - Liczba grup: {quality_metrics.get('num_clusters', 0)}")
        print(f"   - Outliers: {quality_metrics.get('noise_ratio', 0):.1%}")
        print(f"   - Seed keyword: {quality_metrics.get('seed_keyword', 'unknown')}")
        
        # Sprawdź czy to naprawdę Super Simple
        expected_method = "super_simple_clustering"
        actual_method = quality_metrics.get('method', 'unknown')
        
        if actual_method == expected_method:
            print(f"🎯 **SUKCES!** Używa Super Simple Clustering")
        else:
            print(f"⚠️  **UWAGA!** Oczekiwano {expected_method}, otrzymano {actual_method}")
        
        # Sprawdź jakość
        num_groups = quality_metrics.get('num_clusters', 0)
        outlier_ratio = quality_metrics.get('noise_ratio', 0)
        
        if 6 <= num_groups <= 12:
            print(f"✅ Liczba grup OK: {num_groups} (cel: 6-12)")
        else:
            print(f"❌ Liczba grup NOK: {num_groups} (cel: 6-12)")
        
        if outlier_ratio <= 0.15:
            print(f"✅ Outliers OK: {outlier_ratio:.1%} (cel: ≤15%)")
        else:
            print(f"❌ Outliers NOK: {outlier_ratio:.1%} (cel: ≤15%)")
            
    except Exception as e:
        print(f"❌ **BŁĄD:** {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    asyncio.run(test_super_simple_clustering()) 