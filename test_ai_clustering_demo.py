#!/usr/bin/env python3
"""
🧪 Demo skript dla testowania nowego AI Clustering z pamięcią kontekstu

Uruchom: python test_ai_clustering_demo.py
"""

import asyncio
import json
import logging
from datetime import datetime

# Symulacja testowych danych
test_phrases = [
    # Grupa 1: Soczewki podstawowe
    "soczewki kontaktowe",
    "soczewki do oczu", 
    "miękkie soczewki",
    "jak nosić soczewki",
    "pierwsze soczewki",
    
    # Grupa 2: Acuvue (marka)
    "acuvue oasys",
    "soczewki acuvue",
    "acuvue trueye",
    "acuvue advance",
    "johnson and johnson soczewki",
    
    # Grupa 3: Soczewki miesięczne
    "soczewki miesięczne",
    "soczewki 30 dni",
    "air optix aqua",
    "biofinity miesięczne",
    
    # Grupa 4: Soczewki jednodniowe
    "soczewki jednodniowe",
    "soczewki jednorazowe",
    "daily soczewki",
    "1 day acuvue",
    
    # Grupa 5: Sklepy
    "gdzie kupić soczewki",
    "soczewki allegro",
    "optyk soczewki",
    "soczewki online",
    "najtańsze soczewki",
    
    # Grupa 6: Ceny
    "cena soczewek",
    "ile kosztują soczewki",
    "tanie soczewki",
    "promocja soczewki",
    
    # Outliers
    "okulary przeciwsłoneczne",
    "badanie wzroku",
    "zaćma operacja"
]

async def demo_ai_clustering():
    """Demonstracja AI clustering z pamięcią kontekstu"""
    
    print("🤖 DEMO: AI Clustering z pamięcią kontekstu")
    print("=" * 50)
    print(f"📝 Frazy testowe: {len(test_phrases)}")
    print(f"🎯 Cel: 6-8 grup + outliers")
    print()
    
    # Symuluj embeddingów (w rzeczywistości byłyby to wektory OpenAI)
    import numpy as np
    embeddings = np.random.rand(len(test_phrases), 512)
    
    # Import i uruchomienie nowego systemu
    try:
        from app.services.semantic_clustering import AIClusteringSession
        from openai import AsyncOpenAI
        from anthropic import AsyncAnthropic
        import os
        
        # Sprawdź konfigurację
        openai_key = os.getenv("OPENAI_API_KEY")
        claude_key = os.getenv("ANTHROPIC_API_KEY") 
        ai_provider = os.getenv("AI_PROVIDER", "openai").lower()
        
        if not openai_key and not claude_key:
            print("⚠️ UWAGA: Brak API keys - używam symulacji")
            await demo_simulation()
            return
        
        # Inicjalizuj AI clients
        openai_client = AsyncOpenAI(api_key=openai_key) if openai_key else None
        claude_client = AsyncAnthropic(api_key=claude_key) if claude_key else None
        
        # Uruchom AI clustering session
        ai_session = AIClusteringSession(
            openai_client=openai_client,
            claude_client=claude_client,
            ai_provider=ai_provider,
            seed_keyword="soczewki kontaktowe"
        )
        
        print(f"🤖 Używam {ai_provider.upper()} dla klastrowania...")
        print("⚡ Rozpoczynam AI clustering...")
        
        start_time = datetime.now()
        cluster_labels, quality_metrics = await ai_session.process_complete_clustering(
            test_phrases, embeddings
        )
        end_time = datetime.now()
        
        # Wyświetl wyniki
        duration = (end_time - start_time).total_seconds()
        
        print("\n🎉 WYNIKI AI CLUSTERING:")
        print(f"⏱️ Czas wykonania: {duration:.2f}s")
        print(f"📊 Klastrów: {quality_metrics['num_clusters']}")
        print(f"🎯 Outliers: {quality_metrics['noise_points']}/{len(test_phrases)} ({quality_metrics['noise_ratio']:.1%})")
        print(f"✅ Cel osiągnięty: {quality_metrics['quality_goal_achieved']}")
        
        # Pokaż grupy
        print("\n📋 UTWORZONE GRUPY:")
        cluster_map = {}
        for i, (phrase, label) in enumerate(zip(test_phrases, cluster_labels)):
            if label not in cluster_map:
                cluster_map[label] = []
            cluster_map[label].append(phrase)
        
        for label, phrases in cluster_map.items():
            if label == -1:
                print(f"🔴 OUTLIERS ({len(phrases)}):")
            else:
                cluster_name = quality_metrics.get('cluster_names', {}).get(label, f"Klaster {label}")
                print(f"🔵 {cluster_name} ({len(phrases)}):")
            
            for phrase in phrases:
                print(f"   - {phrase}")
            print()
        
        print("✅ Demo zakończone pomyślnie!")
        
    except ImportError as e:
        print(f"❌ Błąd importu: {e}")
        print("Upewnij się, że jesteś w głównym katalogu projektu")
        
    except Exception as e:
        print(f"❌ Błąd demo: {e}")
        await demo_simulation()

async def demo_simulation():
    """Symulacja wyników gdy brak API keys"""
    
    print("🎭 SYMULACJA AI CLUSTERING (brak API keys)")
    print()
    
    # Symulowane grupy
    simulated_groups = {
        0: ["soczewki kontaktowe", "soczewki do oczu", "miękkie soczewki", "jak nosić soczewki", "pierwsze soczewki"],
        1: ["acuvue oasys", "soczewki acuvue", "acuvue trueye", "acuvue advance", "johnson and johnson soczewki"],
        2: ["soczewki miesięczne", "soczewki 30 dni", "air optix aqua", "biofinity miesięczne"],
        3: ["soczewki jednodniowe", "soczewki jednorazowe", "daily soczewki", "1 day acuvue"],
        4: ["gdzie kupić soczewki", "soczewki allegro", "optyk soczewki", "soczewki online", "najtańsze soczewki"],
        5: ["cena soczewek", "ile kosztują soczewki", "tanie soczewki", "promocja soczewki"],
        -1: ["okulary przeciwsłoneczne", "badanie wzroku", "zaćma operacja"]  # outliers
    }
    
    group_names = {
        0: "Soczewki kontaktowe - podstawy",
        1: "Acuvue - produkty marki", 
        2: "Soczewki miesięczne",
        3: "Soczewki jednodniowe",
        4: "Sklepy i sprzedaż",
        5: "Ceny i koszty"
    }
    
    total_phrases = sum(len(phrases) for phrases in simulated_groups.values())
    outliers = len(simulated_groups[-1])
    noise_ratio = outliers / total_phrases
    
    print("🎉 SYMULOWANE WYNIKI:")
    print(f"📊 Klastrów: {len(simulated_groups) - 1}")
    print(f"🎯 Outliers: {outliers}/{total_phrases} ({noise_ratio:.1%})")
    print(f"✅ Cel osiągnięty: {noise_ratio <= 0.35}")
    
    print("\n📋 SYMULOWANE GRUPY:")
    for label, phrases in simulated_groups.items():
        if label == -1:
            print(f"🔴 OUTLIERS ({len(phrases)}):")
        else:
            cluster_name = group_names.get(label, f"Klaster {label}")
            print(f"🔵 {cluster_name} ({len(phrases)}):")
        
        for phrase in phrases:
            print(f"   - {phrase}")
        print()
    
    print("✅ Symulacja zakończona!")
    print("\n💡 Aby uruchomić prawdziwy test:")
    print("1. Ustaw OPENAI_API_KEY w .env")
    print("2. Ustaw USE_AI_CLUSTERING=true")
    print("3. Uruchom ponownie demo")

async def main():
    """Główna funkcja demo"""
    
    print("🚀 DEMO AI CLUSTERING")
    print(f"📅 {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()
    
    try:
        await demo_ai_clustering()
        
    except KeyboardInterrupt:
        print("\n🛑 Demo przerwane przez użytkownika")
        
    except Exception as e:
        print(f"\n❌ Nieoczekiwany błąd: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    # Ustaw logi
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s | %(levelname)s | %(message)s'
    )
    
    # Uruchom demo
    asyncio.run(main()) 