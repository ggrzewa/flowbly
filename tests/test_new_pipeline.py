# test_new_pipeline.py
# Testy podstawowe dla nowego 5-etapowego pipeline klastrowania

import asyncio
import sys
import os
import json

# Dodaj root directory do PYTHONPATH
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..'))

async def test_tag_module():
    """Test modułu TAG - tagowanie fraz"""
    print("🏷️ Testowanie modułu TAG...")
    
    try:
        from app.services.semantic_tagging import tag_phrases_llm
        
        # Test phrases
        test_phrases = [
            "iPhone 15 cena",
            "Samsung Galaxy S24 vs iPhone 15", 
            "najlepszy telefon 2024",
            "jak wybrać smartfon",
            "iPhone 15 Pro Max 256GB"
        ]
        
        print(f"📱 Testuję {len(test_phrases)} fraz...")
        
        # Call the function
        results = await tag_phrases_llm(test_phrases)
        
        print(f"✅ TAG: Przetworzono {len(results)} fraz")
        for i, result in enumerate(results[:2]):  # Pokaż pierwsze 2
            print(f"  📱 {result['text'][:30]}... → brand: {result.get('brand')}, intent: {result.get('intent')}, has_spec: {result.get('has_spec')}")
        
        return True
        
    except Exception as e:
        print(f"❌ TAG Error: {e}")
        return False

async def test_heuristics_module():
    """Test modułu heurystyk"""
    print("🧠 Testowanie modułu heurystyk...")
    
    try:
        from app.services.heuristics import apply_rules
        
        # Test tagged data
        test_tagged = [
            {"text": "iPhone 15 cena", "brand": "apple", "intent": "komercyjny", "has_spec": True},
            {"text": "Samsung Galaxy cena", "brand": "samsung", "intent": "komercyjny", "has_spec": True},
            {"text": "najlepszy telefon 2024", "brand": None, "intent": "komercyjny", "has_spec": False},
        ]
        
        results = apply_rules(test_tagged)
        
        print(f"✅ HEU: Przetworzono {len(results)} fraz")
        for result in results:
            print(f"  🧠 {result['text'][:30]}... → pre_label: {result.get('pre_label')}")
        
        return True
        
    except Exception as e:
        print(f"❌ HEU Error: {e}")
        return False

async def test_assign_module():
    """Test modułu ASSIGN"""
    print("🎯 Testowanie modułu ASSIGN...")
    
    try:
        from app.services.semantic_assign import assign_cluster_llm
        
        # Test data with pre_labels
        test_data = [
            {"text": "iPhone 15 cena", "brand": "apple", "intent": "komercyjny", "has_spec": True, "pre_label": "apple_commercial"},
            {"text": "Samsung Galaxy cena", "brand": "samsung", "intent": "komercyjny", "has_spec": True, "pre_label": "samsung_commercial"},
            {"text": "najlepszy telefon 2024", "brand": None, "intent": "komercyjny", "has_spec": False, "pre_label": None},
        ]
        
        results = await assign_cluster_llm(test_data)
        
        print(f"✅ ASSIGN: Przetworzono {len(results)} fraz")
        for result in results:
            print(f"  🎯 {result['text'][:30]}... → cluster_key: {result.get('cluster_key')}")
        
        return True
        
    except Exception as e:
        print(f"❌ ASSIGN Error: {e}")
        return False

async def test_naming_module():
    """Test modułu NAME"""
    print("🏷️ Testowanie modułu NAME...")
    
    try:
        from app.services.semantic_naming import SemanticNamer
        from openai import AsyncOpenAI
        
        # Test data with cluster_keys
        test_data = [
            {"text": "iPhone 15 cena", "cluster_key": "apple_commercial"},
            {"text": "iPhone 15 Pro cena", "cluster_key": "apple_commercial"},
            {"text": "Samsung Galaxy cena", "cluster_key": "samsung_commercial"},
        ]
        
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        namer = SemanticNamer(openai_client)
        
        brief = namer.create_clusters_brief(test_data)
        names = await namer.name_clusters_llm(brief)
        
        print(f"✅ NAME: Utworzono {len(names)} nazw klastrów")
        for cluster_key, name in names.items():
            print(f"  🏷️ {cluster_key} → '{name}'")
        
        return True
        
    except Exception as e:
        print(f"❌ NAME Error: {e}")
        return False

async def test_full_pipeline():
    """Test pełnego pipeline"""
    print("🚀 Testowanie pełnego pipeline...")
    
    try:
        # Simulacja pełnego pipeline
        from app.services.semantic_tagging import tag_phrases_llm
        from app.services.heuristics import apply_rules
        from app.services.semantic_assign import assign_cluster_llm
        from app.services.semantic_naming import SemanticNamer
        from openai import AsyncOpenAI
        
        test_phrases = [
            "iPhone 15 cena",
            "iPhone 15 Pro Max gdzie kupić",
            "Samsung Galaxy S24 cena", 
            "najlepszy telefon 2024",
            "jak wybrać smartfon dla seniora"
        ]
        
        print(f"🔄 PIPELINE: Przetwarzam {len(test_phrases)} fraz...")
        
        # ETAP 1: TAG
        tagged = await tag_phrases_llm(test_phrases)
        print(f"✅ ETAP 1 (TAG): {len(tagged)} fraz")
        
        # ETAP 2: HEU
        tagged_with_pre = apply_rules(tagged)
        print(f"✅ ETAP 2 (HEU): {len(tagged_with_pre)} fraz")
        
        # ETAP 3: ASSIGN  
        assigned = await assign_cluster_llm(tagged_with_pre)
        print(f"✅ ETAP 3 (ASSIGN): {len(assigned)} fraz")
        
        # ETAP 5: NAME
        openai_client = AsyncOpenAI(api_key=os.getenv("OPENAI_API_KEY"))
        namer = SemanticNamer(openai_client)
        brief = namer.create_clusters_brief(assigned)
        names = await namer.name_clusters_llm(brief)
        print(f"✅ ETAP 5 (NAME): {len(names)} nazw klastrów")
        
        # Podsumowanie
        cluster_keys = set(item.get("cluster_key") for item in assigned)
        noise_count = sum(1 for item in assigned if item.get("cluster_key") in ["noise", "outlier", "unclassified"])
        
        print(f"📊 WYNIKI PIPELINE:")
        print(f"  📊 Klastry: {len(cluster_keys)}")
        print(f"  📊 Outliers: {noise_count}/{len(assigned)} ({noise_count/len(assigned)*100:.1f}%)")
        print(f"  📊 Nazwy klastrów: {list(names.keys())}")
        
        return True
        
    except Exception as e:
        print(f"❌ PIPELINE Error: {e}")
        import traceback
        traceback.print_exc()
        return False

async def main():
    """Uruchom podstawowy test"""
    print("🧪 TESTOWANIE NOWEGO 5-ETAPOWEGO PIPELINE")
    print("=" * 50)
    
    result = await test_tag_module()
    
    if result:
        print("🎉 Test podstawowy przeszedł!")
    else:
        print("❌ Test podstawowy nie przeszedł!")

if __name__ == "__main__":
    asyncio.run(main()) 