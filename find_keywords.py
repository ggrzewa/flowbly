#!/usr/bin/env python3

import os
from supabase import create_client, Client
from dotenv import load_dotenv

# Załaduj zmienne środowiskowe
load_dotenv()

def find_keywords():
    """Znajdź dostępne keywords w bazie danych"""
    
    # Połączenie z Supabase
    url = os.getenv("SUPABASE_URL")
    key = os.getenv("SUPABASE_KEY")
    supabase: Client = create_client(url, key)
    
    try:
        # Znajdź keywords zawierające "makaron"
        print("🔍 Szukam keywords zawierających 'makaron'...")
        response = supabase.table('keywords').select('id, keyword, location_code, language_code').ilike('keyword', '%makaron%').execute()
        
        if response.data:
            print(f"\n✅ Znaleziono {len(response.data)} keywords:")
            for kw in response.data:
                print(f"  - ID: {kw['id']}")
                print(f"    Keyword: {kw['keyword']}")
                print(f"    Location: {kw['location_code']} | Language: {kw['language_code']}")
                print()
        else:
            print("❌ Nie znaleziono keywords z 'makaron'")
            
        # Sprawdź pierwsze keywords
        print("\n" + "="*50)
        print("📅 Pierwsze 10 keywords:")
        response = supabase.table('keywords').select('id, keyword, location_code, language_code').limit(10).execute()
        
        for kw in response.data:
            print(f"  - {kw['keyword']} (ID: {kw['id']})")
            
        # Sprawdź czy są jakiekolwiek keywords z "ugotować"
        print("\n" + "="*50)
        print("🔍 Szukam keywords zawierających 'ugotować'...")
        response = supabase.table('keywords').select('id, keyword, location_code, language_code').ilike('keyword', '%ugotować%').execute()
        
        if response.data:
            print(f"\n✅ Znaleziono {len(response.data)} keywords z 'ugotować':")
            for kw in response.data:
                print(f"  - ID: {kw['id']}")
                print(f"    Keyword: {kw['keyword']}")
                print(f"    Location: {kw['location_code']} | Language: {kw['language_code']}")
                print()
        else:
            print("❌ Nie znaleziono keywords z 'ugotować'")
            
    except Exception as e:
        print(f"❌ Błąd: {e}")

if __name__ == "__main__":
    find_keywords() 