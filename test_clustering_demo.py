# test_clustering_demo.py
# Demo script dla nowego biznesowego klastrowania semantycznego

import asyncio
import os
import logging
from typing import List, Dict, Any
from openai import AsyncOpenAI

# Dodaj ścieżkę do modułów
import sys
sys.path.append('.')

from app.services.semantic_assign import SemanticAssigner, _validate_brand_separation, _split_oversized_clusters

# Konfiguracja loggera
logging.basicConfig(level=logging.INFO, format='%(asctime)s | %(levelname)s | %(message)s')
logger = logging.getLogger(__name__)

class ClusteringDemo:
    """Demo nowego biznesowego klastrowania"""
    
    # Zestawy testowe z różnych branż
    TEST_SCENARIOS = {
        "laptopy_konflikt_marek": [
            {"text": "laptop Dell Inspiron", "brand": "dell", "intent": "komercyjny", "has_spec": False},
            {"text": "laptop HP Pavilion", "brand": "hp", "intent": "komercyjny", "has_spec": False},
            {"text": "MacBook Pro Apple", "brand": "apple", "intent": "komercyjny", "has_spec": False},
            {"text": "laptop do gier", "brand": None, "intent": "komercyjny", "has_spec": False},
            {"text": "najlepszy laptop 2024", "brand": None, "intent": "komercyjny", "has_spec": False},
            {"text": "laptop dla studenta", "brand": None, "intent": "komercyjny", "has_spec": False},
            {"text": "laptop Allegro", "brand": None, "intent": "transakcyjny", "has_spec": False},
            {"text": "naprawa laptopa", "brand": None, "intent": "transakcyjny", "has_spec": False},
        ],
        
        "restauracje_lokalizacje": [
            {"text": "restauracja Kraków", "brand": None, "intent": "nawigacyjny", "has_spec": False},
            {"text": "pizzeria Warszawa", "brand": None, "intent": "nawigacyjny", "has_spec": False},
            {"text": "McDonald's menu", "brand": "mcdonalds", "intent": "informacyjny", "has_spec": False},
            {"text": "KFC promocje", "brand": "kfc", "intent": "komercyjny", "has_spec": False},
            {"text": "najlepsza restauracja", "brand": None, "intent": "komercyjny", "has_spec": False},
            {"text": "rezerwacja stolika", "brand": None, "intent": "transakcyjny", "has_spec": False},
        ],
        
        "mega_klaster_test": [
            # Symulacja mega-klastra z 20 frazami
            {"text": f"laptop gaming {i}", "brand": "dell" if i < 10 else "hp", "intent": "komercyjny", "has_spec": False}
            for i in range(20)
        ]
    }
    
    def __init__(self):
        api_key = os.getenv("OPENAI_API_KEY")
        if not api_key:
            raise ValueError("OPENAI_API_KEY nie jest ustawiony w zmiennych środowiskowych")
        
        self.client = AsyncOpenAI(api_key=api_key)
        self.assigner = SemanticAssigner(self.client)
    
    async def run_demo(self):
        """Uruchom demo wszystkich scenariuszy"""
        print("🚀 DEMO: Nowe biznesowe klastrowanie semantyczne")
        print("=" * 60)
        
        for scenario_name, test_data in self.TEST_SCENARIOS.items():
            print(f"\n📋 SCENARIUSZ: {scenario_name.upper()}")
            print("-" * 40)
            
            try:
                await self.test_scenario(scenario_name, test_data)
            except Exception as e:
                print(f"❌ Błąd w scenariuszu {scenario_name}: {e}")
                continue
        
        print("\n🎉 Demo zakończone!")
    
    async def test_scenario(self, name: str, test_data: List[Dict[str, Any]]):
        """Testuj jeden scenariusz"""
        print(f"📝 Input: {len(test_data)} fraz")
        
        # Pokaż pierwsze 5 fraz
        for i, item in enumerate(test_data[:5]):
            brand_info = f" (marka: {item['brand']})" if item.get('brand') else ""
            print(f"  {i+1}. '{item['text']}'{brand_info}")
        if len(test_data) > 5:
            print(f"  ... i {len(test_data) - 5} więcej")
        
        print("\n🔄 Przetwarzanie...")
        
        # Test 1: Tylko post-processing (bez LLM dla demo)
        result = await self.simulate_clustering(test_data)
        
        # Analiza wyników
        self.analyze_results(result, name)
    
    async def simulate_clustering(self, test_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Symulacja klastrowania (bez rzeczywistego LLM dla demo)"""
        
        # Symuluj podstawowe przypisanie
        result = []
        for item in test_data:
            item_copy = item.copy()
            
            # Prosta logika biznesowa
            if item_copy.get("brand"):
                item_copy["cluster_key"] = f"brand_{item_copy['brand']}"
            elif "naprawa" in item_copy["text"]:
                item_copy["cluster_key"] = "serwis"
            elif any(word in item_copy["text"].lower() for word in ["allegro", "sklep", "rezerwacja"]):
                item_copy["cluster_key"] = "transakcje"
            elif item_copy["intent"] == "informacyjny":
                item_copy["cluster_key"] = "informacje"
            else:
                item_copy["cluster_key"] = "ogolne"
            
            result.append(item_copy)
        
        print("🔧 Zastosowanie post-processingu...")
        
        # POST-PROCESSING
        # 1. Walidacja marek
        result = _validate_brand_separation(result)
        
        # 2. Dzielenie mega-klastrów
        result = _split_oversized_clusters(result, max_size=10)  # Niższy limit dla demo
        
        return result
    
    def analyze_results(self, result: List[Dict[str, Any]], scenario_name: str):
        """Analizuj wyniki klastrowania"""
        
        # Grupuj według cluster_key
        clusters = {}
        for item in result:
            key = item["cluster_key"]
            if key not in clusters:
                clusters[key] = []
            clusters[key].append(item)
        
        print(f"\n📊 WYNIKI dla {scenario_name}:")
        print(f"  📋 Łącznie klastrów: {len(clusters)}")
        
        # Sprawdź konflikty marek
        brand_conflicts = 0
        mega_clusters = 0
        
        for cluster_key, items in clusters.items():
            brands = set(item.get("brand") for item in items if item.get("brand"))
            
            print(f"  🎯 {cluster_key}: {len(items)} fraz")
            
            # Pokaż przykładowe frazy (max 3)
            for i, item in enumerate(items[:3]):
                brand_info = f" [{item.get('brand', 'brak marki')}]" if item.get('brand') else ""
                print(f"      - {item['text']}{brand_info}")
            if len(items) > 3:
                print(f"      ... i {len(items) - 3} więcej")
            
            # Sprawdź konflikty
            if len(brands) > 1:
                brand_conflicts += 1
                print(f"      ⚠️ KONFLIKT MAREK: {brands}")
            
            if len(items) > 10:
                mega_clusters += 1
                print(f"      ⚠️ MEGA-KLASTER: {len(items)} fraz")
        
        # Oblicz noise
        noise_count = sum(len(items) for key, items in clusters.items() if key == "noise")
        noise_ratio = noise_count / len(result) if result else 0
        
        print(f"\n🎯 OCENA BIZNESOWA:")
        print(f"  ✅ Separacja marek: {'OK' if brand_conflicts == 0 else f'BŁĄD ({brand_conflicts} konfliktów)'}")
        print(f"  ✅ Rozmiar klastrów: {'OK' if mega_clusters == 0 else f'BŁĄD ({mega_clusters} mega-klastrów)'}")
        print(f"  ✅ Noise ratio: {noise_ratio:.1%} {'(OK)' if noise_ratio <= 0.20 else '(za dużo)'}")
        
        # Ocena content managera
        useful_clusters = [k for k in clusters.keys() if k not in ["noise", "ogolne"]]
        print(f"  🎨 Użytecznych klastrów: {len(useful_clusters)}")
        
        if brand_conflicts == 0 and mega_clusters == 0 and len(useful_clusters) >= 2:
            print("  🎉 SUKCES: Wyniki nadają się do strategii treści!")
        else:
            print("  ⚠️ UWAGA: Wyniki wymagają poprawek")

async def main():
    """Główna funkcja demo"""
    try:
        demo = ClusteringDemo()
        await demo.run_demo()
    except Exception as e:
        print(f"❌ Błąd uruchomienia demo: {e}")
        print("💡 Sprawdź czy OPENAI_API_KEY jest ustawiony w zmiennych środowiskowych")

if __name__ == "__main__":
    asyncio.run(main()) 