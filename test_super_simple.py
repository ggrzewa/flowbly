#!/usr/bin/env python3
"""
DEMO SUPER PROSTEGO KLASTROWANIA

Symuluje odpowiedź AI żeby pokazać jak to będzie działać
"""

import json

def simulate_super_simple_clustering():
    """Symuluje super prosty clustering"""
    
    phrases = [
        "soczewki",
        "soczewki acuvue oasys",
        "soczewki astygmatyzm",
        "soczewki jednodniowe",
        "soczewki kolorowe",
        "soczewki kontaktowe",
        "soczewki kontaktowe astygmatyzm",
        "soczewki miesięczne",
        "soczewki progresywne",
        "soczewki toryczne",
        "acuvue oasys soczewki",
        "acuvue soczewki",
        "biofinity soczewki",
        "family optic twoje soczewki",
        "ile kosztują soczewki kontaktowe roczne",
        "ile kosztują soczewki na stałe",
        "jak założyć soczewki",
        "kodano soczewki",
        "kolorowe soczewki",
        "soczewki acuvue",
        "soczewki biofinity",
        "soczewki kontaktowe 1-dniowe",
        "soczewki kontaktowe 30-dniowe",
        "soczewki kontaktowe miesięczne",
        "tanie soczewki",
        "twoje soczewki",
        "vision express soczewki",
        "Czym są soczewki?",
        "Ile godzin maksymalnie można nosić soczewki?",
        "Ile kosztuje 1 soczewka?",
        "Jakie są minusy noszenia soczewek?",
        "Soczewki Biofinity",
        "Soczewki Cena",
        "Soczewki Fizyka",
        "Soczewki kolorowe",
        "Soczewki kontaktowe 30 dniowe",
        "Soczewki kontaktowe miesięczne"
    ]
    
    # Usuń duplikaty
    unique_phrases = list(dict.fromkeys(phrases))
    
    print(f"🚀 SUPER SIMPLE CLUSTERING - DEMO")
    print(f"📋 Frazy: {len(unique_phrases)}")
    print(f"🎯 Temat: soczewki")
    print()
    
    # Prompt który by został wysłany do AI
    print("📤 PROMPT DO AI:")
    print("=" * 50)
    print("Pogrupuj te frazy na temat 'soczewki' w sensowne grupy semantyczne.")
    print()
    print("ZASADA: Każda grupa = jedna strona internetowa. Frazy w grupie muszą pasować do tej samej treści.")
    print()
    print("Zrób to tak, jak sam byś pogrupował gdybyś tworzył strony internetowe.")
    print()
    print("Cel: 6-10 grup, minimalne outliers.")
    print("=" * 50)
    print()
    
    # Symulowana odpowiedź AI - tak jak człowiek by pogrupował
    simulated_response = {
        "groups": [
            {
                "name": "Typy według okresu",
                "phrases": [
                    "soczewki jednodniowe",
                    "soczewki kontaktowe 1-dniowe", 
                    "soczewki miesięczne",
                    "soczewki kontaktowe miesięczne",
                    "Soczewki kontaktowe miesięczne",
                    "soczewki kontaktowe 30-dniowe",
                    "Soczewki kontaktowe 30 dniowe",
                    "ile kosztują soczewki kontaktowe roczne",
                    "ile kosztują soczewki na stałe"
                ]
            },
            {
                "name": "Problemy medyczne",
                "phrases": [
                    "soczewki astygmatyzm",
                    "soczewki kontaktowe astygmatyzm",
                    "soczewki progresywne", 
                    "soczewki toryczne"
                ]
            },
            {
                "name": "Marki soczewek",
                "phrases": [
                    "soczewki acuvue oasys",
                    "acuvue oasys soczewki",
                    "soczewki acuvue",
                    "acuvue soczewki",
                    "soczewki biofinity",
                    "biofinity soczewki",
                    "Soczewki Biofinity"
                ]
            },
            {
                "name": "Sklepy i miejsca zakupu",
                "phrases": [
                    "family optic twoje soczewki",
                    "kodano soczewki", 
                    "twoje soczewki",
                    "vision express soczewki"
                ]
            },
            {
                "name": "Pytania i porady",
                "phrases": [
                    "Czym są soczewki?",
                    "Ile godzin maksymalnie można nosić soczewki?",
                    "Jakie są minusy noszenia soczewek?",
                    "jak założyć soczewki"
                ]
            },
            {
                "name": "Ceny i koszty",
                "phrases": [
                    "Ile kosztuje 1 soczewka?",
                    "tanie soczewki",
                    "Soczewki Cena"
                ]
            },
            {
                "name": "Soczewki kolorowe",
                "phrases": [
                    "soczewki kolorowe",
                    "kolorowe soczewki",
                    "Soczewki kolorowe"
                ]
            },
            {
                "name": "Ogólne informacje",
                "phrases": [
                    "soczewki",
                    "soczewki kontaktowe",
                    "Soczewki Fizyka"
                ]
            }
        ],
        "outliers": []
    }
    
    print("📥 ODPOWIEDŹ AI:")
    print("=" * 50)
    print(json.dumps(simulated_response, indent=2, ensure_ascii=False))
    print("=" * 50)
    print()
    
    # Analiza wyników
    total_phrases = len(unique_phrases)
    groups = simulated_response["groups"]
    outliers = simulated_response.get("outliers", [])
    
    grouped_phrases = sum(len(group["phrases"]) for group in groups)
    outliers_count = len(outliers)
    outlier_ratio = outliers_count / total_phrases
    
    print("✅ ANALIZA WYNIKÓW:")
    print(f"  📊 Liczba grup: {len(groups)}")
    print(f"  📊 Pogrupowane frazy: {grouped_phrases}/{total_phrases}")
    print(f"  📊 Outliers: {outliers_count} ({outlier_ratio:.1%})")
    print(f"  🎯 Cel osiągnięty: {'✅' if 6 <= len(groups) <= 10 and outlier_ratio <= 0.1 else '❌'}")
    print()
    
    print("📋 SZCZEGÓŁOWE GRUPY:")
    for i, group in enumerate(groups, 1):
        print(f"\n{i}. 🏷️ {group['name']} ({len(group['phrases'])} fraz):")
        for phrase in group['phrases']:
            print(f"     - {phrase}")
    
    if outliers:
        print(f"\n⚠️ OUTLIERS ({len(outliers)} fraz):")
        for phrase in outliers:
            print(f"     - {phrase}")
    
    print(f"\n🎉 SUPER PROSTY SYSTEM DZIAŁA!")
    print(f"🎯 {len(groups)} grup semantycznych - idealne dla stron internetowych!")
    print(f"🎯 {outlier_ratio:.1%} outliers - doskonały wynik!")

if __name__ == "__main__":
    simulate_super_simple_clustering() 