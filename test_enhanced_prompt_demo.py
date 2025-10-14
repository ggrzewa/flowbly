#!/usr/bin/env python3
"""
🎯 Demo Enhanced AI Prompt System - Test porównawczy starych vs nowych promptów

Ten skrypt demonstruje różnice między legacy prompt a enhanced prompt
na przykładowych danych podobnych do rzeczywistych.

Uruchom: python test_enhanced_prompt_demo.py
"""

import asyncio
import json
import os
import sys
from typing import List, Dict

# Dodaj ścieżkę do modułu app
sys.path.append(os.path.join(os.path.dirname(__file__), 'app'))

from services.semantic_clustering import SemanticClusteringService

class MockSupabaseClient:
    """Mock client dla demonstracji"""
    def table(self, table_name):
        return self
    
    def select(self, *args):
        return self
    
    def eq(self, *args):
        return self
    
    def execute(self):
        class MockResponse:
            data = []
        return MockResponse()

# Przykładowe dane podobne do rzeczywistych problemów
EXAMPLE_PHRASES_LAPTOPS = [
    "laptop do gier", "gaming laptop", "laptop gamingowy", "laptopy do gier",
    "MacBook Pro", "MacBook Air", "Apple MacBook", "MacBook 2024",
    "laptop Dell", "Dell XPS", "Dell Inspiron", "Dell Latitude",
    "laptop Lenovo", "Lenovo ThinkPad", "Lenovo IdeaPad", "Lenovo Legion",
    "laptop HP", "HP EliteBook", "HP Pavilion", "HP Envy",
    "laptop Asus", "Asus VivoBook", "Asus ZenBook", "Asus ROG",
    "tani laptop", "najtańsze laptopy", "laptop do 2000 zł", "budżetowy laptop",
    "laptop do pracy", "laptop biurowy", "laptop studencki", "laptop do domu",
    "laptop 15 cali", "laptop 14 cali", "laptop 13 cali", "laptop 17 cali",
    "laptop SSD", "laptop z dyskiem SSD", "laptop 512GB", "laptop 1TB",
    "laptop 8GB RAM", "laptop 16GB RAM", "laptop 32GB RAM", "laptop pamięć",
    "laptop Intel", "laptop AMD", "laptop Ryzen", "laptop Core i5",
    "laptop Windows", "laptop Linux", "laptop bez systemu", "laptop Ubuntu"
]

EXAMPLE_PHRASES_CONTACT_LENSES = [
    "soczewki kontaktowe", "soczewki", "kontaktowe", "szkła kontaktowe",
    "soczewki jednodniowe", "soczewki daily", "soczewki dzienne", "jednorazowe soczewki",
    "soczewki miesięczne", "soczewki monthly", "soczewki 30 dni", "miesięczne kontaktowe",
    "Acuvue", "soczewki Acuvue", "Johnson Acuvue", "Acuvue Oasys",
    "Biofinity", "soczewki Biofinity", "Cooper Vision Biofinity", "Biofinity monthly",
    "Dailies", "soczewki Dailies", "Alcon Dailies", "Dailies Total",
    "cena soczewek", "ile kosztują soczewki", "tanie soczewki", "najtańsze soczewki",
    "gdzie kupić soczewki", "sklep soczewki", "optyk", "apteka soczewki",
    "soczewki astygmatyzm", "soczewki toryczne", "soczewki dla astygmatyków",
    "soczewki multifocal", "soczewki progresywne", "soczewki presbyopia",
    "soczewki kolorowe", "soczewki colored", "kolorowe kontaktowe", "color lenses",
    "jak zakładać soczewki", "jak nosić soczewki", "pielęgnacja soczewek", "płyn do soczewek"
]

async def test_enhanced_vs_legacy_prompt():
    """Porównuje wyniki legacy vs enhanced prompt"""
    
    print("🎯 DEMO: Enhanced AI Prompt System")
    print("=" * 60)
    
    # Inicializuj mock service
    mock_supabase = MockSupabaseClient()
    service = SemanticClusteringService(mock_supabase)
    
    # Test dla różnych tematów
    test_cases = [
        ("laptopy", EXAMPLE_PHRASES_LAPTOPS[:20]),  # Ograniczamy do 20 fraz dla demo
        ("soczewki kontaktowe", EXAMPLE_PHRASES_CONTACT_LENSES[:20])
    ]
    
    for seed_keyword, phrases in test_cases:
        print(f"\n📝 Test dla tematu: '{seed_keyword}'")
        print(f"📊 Liczba fraz do klastrowania: {len(phrases)}")
        print("-" * 40)
        
        # Test 1: Legacy Prompt
        print("\n🔄 LEGACY PROMPT:")
        try:
            # Tymczasowo wymuś legacy prompt
            original_env = os.environ.get("USE_ENHANCED_PROMPT")
            os.environ["USE_ENHANCED_PROMPT"] = "false"
            
            legacy_prompt = service._create_ai_clustering_prompt(phrases, seed_keyword)
            legacy_length = len(legacy_prompt)
            
            print(f"📏 Długość promptu: {legacy_length} znaków")
            print(f"🔍 Pierwsze 200 znaków: {legacy_prompt[:200]}...")
            print(f"📋 Typ: Hardkodowane instrukcje z DataForSEO intents")
            
        except Exception as e:
            print(f"❌ Błąd legacy prompt: {e}")
        
        # Test 2: Enhanced Prompt  
        print("\n🎯 ENHANCED PROMPT:")
        try:
            # Wymuś enhanced prompt
            os.environ["USE_ENHANCED_PROMPT"] = "true"
            
            enhanced_prompt = service._create_enhanced_ai_prompt(phrases, seed_keyword)
            enhanced_length = len(enhanced_prompt)
            
            print(f"📏 Długość promptu: {enhanced_length} znaków")
            print(f"🔍 Pierwsze 200 znaków: {enhanced_prompt[:200]}...")
            print(f"📋 Typ: Uniwersalny framework z kontekstem biznesowym")
            
            # Przywróć oryginalne ustawienia
            if original_env:
                os.environ["USE_ENHANCED_PROMPT"] = original_env
            else:
                os.environ.pop("USE_ENHANCED_PROMPT", None)
                
        except Exception as e:
            print(f"❌ Błąd enhanced prompt: {e}")
        
        # Analiza różnic
        print(f"\n📈 PORÓWNANIE:")
        if 'legacy_length' in locals() and 'enhanced_length' in locals():
            ratio = enhanced_length / legacy_length
            print(f"📏 Enhanced prompt jest {ratio:.1f}x {'dłuższy' if ratio > 1 else 'krótszy'}")
            print(f"🎯 Enhanced zawiera kontekst biznesowy i uniwersalny framework")
            print(f"🔄 Legacy zawiera hardkodowane instrukcje specyficzne dla tematu")

def analyze_prompt_components():
    """Analizuje komponenty enhanced prompt"""
    
    print("\n\n🔬 ANALIZA KOMPONENTÓW ENHANCED PROMPT")
    print("=" * 60)
    
    mock_supabase = MockSupabaseClient()
    service = SemanticClusteringService(mock_supabase)
    
    seed_keyword = "przykładowy temat"
    
    components = {
        "Kontekst biznesowy": service._build_business_context(seed_keyword),
        "Framework uniwersalny": service._build_universal_framework(),
        "Przykłady myślenia": service._build_thinking_examples(),
        "Instrukcje JSON": service._build_json_instructions()
    }
    
    total_length = 0
    for name, content in components.items():
        length = len(content)
        total_length += length
        print(f"\n📋 {name}:")
        print(f"📏 Długość: {length} znaków")
        print(f"🔍 Początek: {content[:100]}...")
    
    print(f"\n📊 PODSUMOWANIE:")
    print(f"📏 Łączna długość komponentów: {total_length} znaków")
    print(f"🎯 Największy komponent: {max(components.items(), key=lambda x: len(x[1]))[0]}")

def demonstrate_quality_logging():
    """Demonstruje nowe logowanie jakości"""
    
    print("\n\n📊 DEMO: Nowe logowanie jakości")
    print("=" * 60)
    
    mock_supabase = MockSupabaseClient()
    service = SemanticClusteringService(mock_supabase)
    
    # Przykładowe wyniki klastrowania (symulacja)
    mock_legacy_result = {
        "szczegolowe_klastrowanie": [
            {"frazy": [{"tekst": f"fraza{i}"} for i in range(2)]},  # 37 małych grup
            {"frazy": [{"tekst": f"fraza{i}"} for i in range(3)]},
            {"frazy": [{"tekst": f"fraza{i}"} for i in range(1)]},
        ] * 12,  # Symulacja 36 grup
        "frazy_niesklasyfikowane": [{"tekst": f"outlier{i}"} for i in range(15)]
    }
    
    mock_enhanced_result = {
        "grupy": [
            {"frazy": [{"tekst": f"fraza{i}"} for i in range(12)]},  # 8 dużych grup
            {"frazy": [{"tekst": f"fraza{i}"} for i in range(10)]},
            {"frazy": [{"tekst": f"fraza{i}"} for i in range(15)]},
            {"frazy": [{"tekst": f"fraza{i}"} for i in range(8)]},
            {"frazy": [{"tekst": f"fraza{i}"} for i in range(14)]},
            {"frazy": [{"tekst": f"fraza{i}"} for i in range(11)]},
            {"frazy": [{"tekst": f"fraza{i}"} for i in range(9)]},
            {"frazy": [{"tekst": f"fraza{i}"} for i in range(6)]},
        ],
        "niesklasyfikowane": [{"tekst": f"outlier{i}"} for i in range(3)]
    }
    
    test_phrases = [f"fraza{i}" for i in range(100)]
    
    print("\n🔄 LEGACY PROMPT - symulowane wyniki:")
    service._log_clustering_quality(mock_legacy_result, test_phrases)
    
    print("\n🎯 ENHANCED PROMPT - symulowane wyniki:")
    service._log_clustering_quality(mock_enhanced_result, test_phrases)

def show_configuration_examples():
    """Pokazuje przykłady konfiguracji"""
    
    print("\n\n⚙️ PRZYKŁADY KONFIGURACJI")
    print("=" * 60)
    
    configs = {
        "Testowanie (bezpieczne)": {
            "USE_ENHANCED_PROMPT": "false",
            "opis": "Używa stary prompt, wszystko działa jak wcześniej"
        },
        "Pierwszy test": {
            "USE_ENHANCED_PROMPT": "true", 
            "opis": "Włącza nowy prompt, test na małej próbie"
        },
        "Produkcja (po testach)": {
            "USE_ENHANCED_PROMPT": "true",
            "USE_AI_CLUSTERING": "true",
            "ENABLE_CLUSTERING_CONSOLIDATION": "true",
            "opis": "Pełna konfiguracja z wszystkimi ulepszeniami"
        }
    }
    
    for scenario, config in configs.items():
        print(f"\n📋 Scenariusz: {scenario}")
        opis = config.pop("opis", "")
        print(f"💡 {opis}")
        print("⚙️ Ustawienia .env:")
        for key, value in config.items():
            print(f"   {key}={value}")

if __name__ == "__main__":
    print("🚀 Uruchamiam demo Enhanced AI Prompt System...")
    
    try:
        # Główne demo
        asyncio.run(test_enhanced_vs_legacy_prompt())
        
        # Dodatkowe analizy
        analyze_prompt_components()
        demonstrate_quality_logging()
        show_configuration_examples()
        
        print("\n\n✅ DEMO ZAKOŃCZONE POMYŚLNIE!")
        print("\n📖 Następne kroki:")
        print("1. Dodaj USE_ENHANCED_PROMPT=false do pliku .env")
        print("2. Przetestuj system na swoich danych")  
        print("3. Zmień na USE_ENHANCED_PROMPT=true i porównaj wyniki")
        print("4. Sprawdź logi jakości klastrowania")
        print("5. Zobacz ENHANCED_PROMPT_CONFIG.md dla szczegółów")
        
    except Exception as e:
        print(f"❌ Błąd w demo: {e}")
        import traceback
        traceback.print_exc() 