import requests
import json

def test_ai_references():
    """Test czy AI references są zapisywane do bazy"""
    
    # 1. Uruchom analizę przez modular endpoint
    print("🔄 Uruchamiam analizę przez modular endpoint...")
    
    analysis_data = {
        "keyword": "python programming",
        "country": "2840|en",  # USA English
        "use_cache": False
    }
    
    response = requests.post(
        "http://localhost:8000/api/v6/analyze-complete",
        json=analysis_data,
        timeout=300
    )
    
    if response.status_code == 200:
        result = response.json()
        print(f"✅ Analiza zakończona: {result.get('success')}")
        print(f"📊 Completed steps: {result.get('completed_steps')}/{result.get('total_steps')}")
        
        # 2. Sprawdź czy są AI references w bazie
        print("\n🔍 Sprawdzam AI references w bazie...")
        
        data_response = requests.get(
            f"http://localhost:8000/api/v6/keyword-data/{analysis_data['keyword']}?location_code=2840&language_code=en"
        )
        
        if data_response.status_code == 200:
            data_result = data_response.json()
            ai_refs = data_result.get('data', {}).get('serp_ai_references', [])
            print(f"📊 Znaleziono {len(ai_refs)} AI references w bazie")
            
            if ai_refs:
                print("✅ AI references są zapisywane!")
                for i, ref in enumerate(ai_refs[:3]):  # Pokaż pierwsze 3
                    print(f"  {i+1}. {ref.get('title', 'No title')[:50]}...")
            else:
                print("❌ Brak AI references w bazie")
        else:
            print(f"❌ Błąd pobierania danych: {data_response.status_code}")
    else:
        print(f"❌ Błąd analizy: {response.status_code}")
        print(response.text)

if __name__ == "__main__":
    test_ai_references() 