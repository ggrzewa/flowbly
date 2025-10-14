# SEO Analysis Tool - Wersja Deweloperska

## Opis

Uproszczona wersja narzędzia do analizy SEO. **Tylko analiza i zapis do bazy danych** - bez skomplikowanego wyświetlania wyników.

## Funkcjonalność

1. **Formularz analizy** - słowo kluczowe + wybór kraju
2. **Progress bar** - postęp analizy w czasie rzeczywistym 
3. **Zapis do bazy** - wszystkie dane trafiają do Supabase
4. **Brak wyświetlania** - nie ma funkcji pobierania i wyświetlania wyników

## Endpointy analizy

System uruchamia po kolei 8 kroków analizy:

1. ✅ **Related Keywords** - powiązane słowa kluczowe (wymagany)
2. 🔍 **Suggestions** - sugestie słów kluczowych  
3. 🧠 **Intent Analysis** - analiza intencji wyszukiwania
4. ✅ **SERP Analysis** - wyniki wyszukiwania (wymagany)
5. 💡 **Autocomplete** - podpowiedzi Google
6. 📊 **Historical Data** - dane historyczne
7. 📈 **DataForSEO Trends** - trendy z DataForSEO
8. 🌍 **Google Trends** - analiza Google Trends

## Uruchomienie

```bash
# Zainstaluj zależności
pip install -r requirements.txt

# Ustaw zmienne środowiskowe w .env
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key

# Uruchom serwer
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

## Dostępne endpointy

- `GET /seo-analysis` - strona z formularzem
- `POST /api/v6/analyze-complete` - uruchomienie analizy
- `GET /api/v6/countries` - lista krajów
- `GET /api/v6/status` - status aplikacji

## Uwagi deweloperskie

- Usunięto ciężki JavaScript (2800+ linii)
- Usunięto skomplikowany CSS (2500+ linii) 
- Usunięto funkcjonalność wyświetlania wyników z bazy
- Wszystkie style są teraz inline w HTML
- JavaScript ograniczony do minimum (obsługa formularza + progress)

## Wersja produkcyjna

Funkcjonalność wyświetlania wyników zostanie dodana w przyszłości jako osobny moduł. 