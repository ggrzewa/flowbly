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

# Włącz AI-First Clustering (NOWE PODEJŚCIE)
os.environ["USE_AI_FIRST_CLUSTERING"] = "true"
os.environ["USE_SUPER_SIMPLE_CLUSTERING"] = "false" 
os.environ["USE_UNIVERSAL_CLUSTERING"] = "false"

# Dane testowe - soczewki kontaktowe (te same co poprzednio)
TEST_PHRASES = [
    "soczewki kontaktowe",
    "soczewki jednodniowe", 
    "soczewki miesięczne",
    "soczewki astygmatyzm",
    "acuvue soczewki",
    "biofinity soczewki", 
    "vision express",
    "alensa soczewki",
    "ile kosztują soczewki jednodniowe",
    "ile kosztują soczewki miesięczne",
    "soczewki kolorowe",
    "jak założyć soczewki",
    "czym są soczewki",
    "soczewki progresywne",
    "tanie soczewki",
    "kodano soczewki",
    "family optic",
    "rossmann soczewki miesięczne",
    "najlepsze soczewki jednodniowe",
    "soczewki toryczne"
]

async def test_ai_first_clustering():
    """
    Test nowego podejścia AI-First Clustering:
    1. AI grupuje frazy NAJPIERW
    2. Embeddingi dla gotowych grup POTEM  
    3. Brak konfliktu AI vs matematyka
    """
    
    print("=" * 80)
    print("🚀 TEST AI-FIRST CLUSTERING - NOWE PODEJŚCIE")
    print("=" * 80)
    print(f"📊 Testowanie {len(TEST_PHRASES)} fraz")
    print(f"🔧 Podejście: AI grupuje → potem embeddingi")
    print(f"🎯 Cel: <15% outliers, sensowne grupy semantyczne")
    print("=" * 80)
    
    try:
        # Inicjalizuj Supabase i serwis
        supabase: SupabaseClient = create_client(SUPABASE_URL, SUPABASE_KEY)
        service = SemanticClusteringService(supabase)
        
        # Przygotuj frazy w formacie oczekiwanym przez serwis
        service.all_phrases = [{"text": phrase} for phrase in TEST_PHRASES]
        service._current_seed_keyword = "soczewki"
        
        start_time = time.time()
        
        # Wywołaj nową metodę AI-First
        print("🔄 Uruchamiam AI-First Clustering...")
        cluster_labels, quality_metrics = await service._perform_ai_first_clustering()
        
        processing_time = time.time() - start_time
        
        # Wyświetl wyniki
        print(f"✅ ZAKOŃCZONO w {processing_time:.1f}s")
        print()
        print("📊 WYNIKI:")
        print(f"   Liczba grup: {quality_metrics['num_clusters']}")
        print(f"   Outliers: {quality_metrics['outliers_count']}/{quality_metrics['total_phrases']} ({quality_metrics['noise_ratio']:.1%})")
        print(f"   Metoda: {quality_metrics['method']}")
        print(f"   Podejście: {quality_metrics.get('approach', 'unknown')}")
        
        # Ocena jakości
        print()
        print("🎯 OCENA JAKOŚCI:")
        outlier_ratio = quality_metrics['noise_ratio']
        num_groups = quality_metrics['num_clusters']
        
        if outlier_ratio <= 0.15:
            print(f"   ✅ Outliers: {outlier_ratio:.1%} (cel: ≤15%)")
        else:
            print(f"   ❌ Outliers: {outlier_ratio:.1%} (za dużo, cel: ≤15%)")
            
        if 6 <= num_groups <= 10:
            print(f"   ✅ Liczba grup: {num_groups} (cel: 6-10)")
        else:
            print(f"   ⚠️ Liczba grup: {num_groups} (cel: 6-10)")
        
        # Porównanie z poprzednimi wynikami
        print()
        print("📈 PORÓWNANIE Z POPRZEDNIMI WYNIKAMI:")
        print(f"   Super Simple (stare): 8 grup, 20.6% outliers, mega-grupa 38 fraz")
        print(f"   AI-First (nowe):     {num_groups} grup, {outlier_ratio:.1%} outliers")
        
        if outlier_ratio < 0.206:
            print(f"   🎉 POPRAWA outliers: {0.206 - outlier_ratio:.1%} mniej!")
        else:
            print(f"   📉 Pogorszenie outliers: {outlier_ratio - 0.206:.1%} więcej")
            
        return quality_metrics
        
    except Exception as e:
        print(f"❌ BŁĄD: {e}")
        import traceback
        traceback.print_exc()
        return None

async def main():
    """Główna funkcja testowa"""
    
    print("🧪 EKSPERYMENT: AI-FIRST CLUSTERING")
    print("Hipoteza: AI grupuje lepiej gdy nie ma konfliktu z embeddingami")
    print()
    
    result = await test_ai_first_clustering()
    
    if result:
        print()
        print("=" * 80)
        print("🎯 WNIOSKI:")
        if result['noise_ratio'] <= 0.15:
            print("✅ AI-First clustering osiągnął cel: ≤15% outliers")
            print("🚀 Nowe podejście DZIAŁA - można wdrażać!")
        else:
            print("❌ AI-First clustering nie osiągnął celu outliers")
            print("🔧 Potrzebne dalsze ulepszenia prompta")
        print("=" * 80)

if __name__ == "__main__":
    asyncio.run(main()) 