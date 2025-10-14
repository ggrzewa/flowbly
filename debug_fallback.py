#!/usr/bin/env python3
"""
Debug script for Universal Fallback - sprawdza dlaczego frazy cenowe trafiają do outliers
"""

# Symulacja problemu
ai_groups = {
    "Marka - Acuvue": ["soczewki acuvue", "acuvue oasys"],
    "Sklepy": ["vision express", "alensa.pl"],
    "outliers": [
        "ile kosztują soczewki jednodniowe",
        "ile kosztują soczewki kontaktowe", 
        "ile kosztują soczewki miesięczne",
        "soczewki miesięczne cena",
        "tanie soczewki"
    ]
}

def debug_price_detection():
    """Debuguje wykrywanie wzorców cenowych"""
    
    print("🔍 DEBUG: Sprawdzanie wykrywania wzorców cenowych")
    print("=" * 60)
    
    # Obecne wzorce w systemie
    price_patterns = ["cena", "koszt", "ile kosztuje", "tani", "drogi", "promocja", "rabat"]
    
    # Frazy cenowe z outliers
    price_phrases = [
        "ile kosztują soczewki jednodniowe",
        "ile kosztują soczewki kontaktowe", 
        "ile kosztują soczewki miesięczne",
        "soczewki miesięczne cena",
        "tanie soczewki"
    ]
    
    print("📋 Frazy cenowe do sprawdzenia:")
    for phrase in price_phrases:
        print(f"  - {phrase}")
    
    print("\n🎯 Obecne wzorce cenowe:")
    for pattern in price_patterns:
        print(f"  - '{pattern}'")
    
    print("\n🔍 Analiza dopasowań:")
    
    for phrase in price_phrases:
        phrase_lower = phrase.lower()
        matched = False
        
        for pattern in price_patterns:
            if pattern in phrase_lower:
                print(f"  ✅ '{phrase}' → dopasowano wzorzec '{pattern}'")
                matched = True
                break
        
        if not matched:
            print(f"  ❌ '{phrase}' → NIE dopasowano żadnego wzorca")
            
            # Sprawdź dlaczego
            print(f"      Fraza: '{phrase_lower}'")
            print(f"      Zawiera 'ile': {'ile' in phrase_lower}")
            print(f"      Zawiera 'cena': {'cena' in phrase_lower}")
            print(f"      Zawiera 'tani': {'tani' in phrase_lower}")
    
    print("\n🚨 PROBLEM ZDIAGNOZOWANY!")
    print("Wzorzec 'ile kosztuje' nie pasuje do 'ile kosztują'")
    print("Wzorzec 'tani' nie pasuje do 'tanie'")
    
    print("\n✅ ROZWIĄZANIE:")
    better_patterns = ["ile", "cena", "koszt", "tani", "drogi", "promocja", "rabat"]
    
    print("Lepsze wzorce:")
    for pattern in better_patterns:
        print(f"  - '{pattern}'")
    
    print("\n🔍 Test z lepszymi wzorcami:")
    for phrase in price_phrases:
        phrase_lower = phrase.lower()
        matched = False
        
        for pattern in better_patterns:
            if pattern in phrase_lower:
                print(f"  ✅ '{phrase}' → dopasowano wzorzec '{pattern}'")
                matched = True
                break
        
        if not matched:
            print(f"  ❌ '{phrase}' → NIE dopasowano")

if __name__ == "__main__":
    debug_price_detection() 