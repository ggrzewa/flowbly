#!/usr/bin/env python3

import requests
import json
import time

def test_clustering():
    """Test klastrowania z poprawnym keyword ID"""
    
    # Użyj poprawnego keyword ID z bazy
    keyword_id = '4d54376d-293e-4f17-ac6a-784fd23b525e'  # vision express soczewki
    
    print(f"🚀 Testowanie klastrowania dla keyword_id: {keyword_id}")
    print(f"Keyword: vision express soczewki")
    print()
    
    try:
        # Test połączenia
        print("1. Test połączenia z OpenAI...")
        response = requests.get("http://localhost:8000/api/v6/clustering/test-openai")
        print(f"   Status: {response.status_code}")
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ {result.get('message', 'OK')}")
        else:
            print(f"   ❌ {response.text}")
            return
            
        print()
        
        # Test klastrowania
        print("2. Uruchamianie klastrowania...")
        start_time = time.time()
        
        body = {'keyword_id': keyword_id}
        response = requests.post(
            'http://localhost:8000/api/v6/clustering/start', 
            headers={'Content-Type': 'application/json'}, 
            json=body
        )
        
        elapsed_time = time.time() - start_time
        print(f"   Czas wykonania: {elapsed_time:.2f}s")
        print(f"   Status HTTP: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Sukces!")
            print(f"   Data: {json.dumps(result, indent=2, ensure_ascii=False)}")
        else:
            print(f"   ❌ Błąd:")
            print(f"   Response: {response.text}")
            
        print()
        
        # Test pobierania wyników
        print("3. Pobieranie wyników...")
        response = requests.get(f"http://localhost:8000/api/v6/clustering/results/{keyword_id}")
        print(f"   Status: {response.status_code}")
        
        if response.status_code == 200:
            result = response.json()
            print(f"   ✅ Wyniki pobrane:")
            if result.get('success'):
                data = result.get('data', {})
                groups = data.get('groups', [])
                total_phrases = data.get('total_phrases', 0)
                print(f"      - Łączna liczba fraz: {total_phrases}")
                print(f"      - Liczba grup: {len(groups)}")
                
                for group in groups[:3]:  # Pokaż pierwsze 3 grupy
                    print(f"      - Grupa {group.get('group_number', 'N/A')}: {group.get('phrases_count', 0)} fraz")
            else:
                print(f"   ❌ {result.get('error', 'Nieznany błąd')}")
        else:
            print(f"   ❌ {response.text}")
            
    except Exception as e:
        print(f"❌ Błąd: {e}")

if __name__ == "__main__":
    test_clustering() 