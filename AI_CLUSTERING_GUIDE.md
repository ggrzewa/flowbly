# 🤖 AI Clustering z pamięcią kontekstu - Przewodnik

## 📋 Przegląd

Nowy system semantycznego klastrowania wykorzystuje AI z pamięcią kontekstu zamiast starycznego 5-etapowego pipeline. Wykorzystuje naturalne mocne strony AI w rozumieniu semantyki języka, zachowując pamięć między decyzjami klastrowania.

## 🔄 Migracja z starého systemu

### Stary system (5-etapowy pipeline):
```
TAG → HEU → ASSIGN → QA → NAME
```
**Problemy:**
- 5 miejsc na błędy kumulacyjne 
- HDBSCAN to tylko matematyka na wektorach
- Fragmentaryczne instrukcje dla AI
- Zbyt skomplikowane reguły heurystyczne
- Brak pamięci kontekstu między etapami

### Nowy system (AI z pamięcią):
```
STRATEGIA → BATCH PROCESSING → FINALIZACJA → KONWERSJA
```
**Zalety:**
- AI rozumie semantykę naturalnie
- Pamięć poprzednich decyzji 
- Batch processing z kontekstem
- Inteligentna redistribution
- Cel biznesowy wbudowany w prompty

## ⚙️ Konfiguracja

### Zmienne środowiskowe

```bash
# Włącz nowy AI clustering (domyślnie: true)
USE_AI_CLUSTERING=true

# AI Provider (domyślnie: openai)
AI_PROVIDER=openai
AI_MODEL_OPENAI=gpt-4o

# Alternatywnie Claude
AI_PROVIDER=claude  
AI_MODEL_CLAUDE=claude-3-5-sonnet-20241022

# Klucze API (zawsze wymagany OpenAI dla embeddingów)
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
```

### Przełączanie metod

```bash
# Nowy AI clustering z pamięcią (zalecane)
USE_AI_CLUSTERING=true

# Stary 5-etapowy pipeline (do porównań)
USE_AI_CLUSTERING=false
```

## 🏗️ Architektura AI Clustering

### ETAP 1: Ustalenie strategii semantycznej
- AI analizuje próbkę 30 fraz 
- Ustala strategię klastrowania
- Definiuje osie podziału
- Planuje docelową liczbę grup (8-12)

### ETAP 2: Batch processing z pamięcią
- Podział na batche po 25 fraz
- Każdy batch ma dostęp do pamięci poprzednich decyzji
- AI "pamięta" utworzone grupy przez kontekst konwersacji
- Spójna metodologia przez całą sesję

### ETAP 3: Finalna optymalizacja
- Redistribution niesklasyfikowanych fraz
- Konsolidacja małych grup (<3 frazy) 
- Sprawdzenie celu jakościowego (≤35% outliers)

### ETAP 4: Konwersja do formatu legacy
- Mapowanie grup AI na cluster_labels
- Kalkulacja metryk jakości 
- Kompatybilność z resztą systemu

## 📊 Oczekiwane rezultaty

### Dla "soczewki kontaktowe" (~100 fraz):

**Stary system:** 36 grup po 1-3 frazy

**Nowy system:** ~8 grup:
1. "Soczewki kontaktowe - podstawy" (8-12 fraz)
2. "Acuvue - produkty marki" (6-10 fraz)  
3. "Soczewki miesięczne" (8-15 fraz)
4. "Soczewki jednodniowe" (8-15 fraz)
5. "Soczewki specjalne (astygmatyzm)" (6-10 fraz)
6. "Sklepy i sprzedaż" (8-12 fraz)
7. "Ceny i koszty" (5-8 fraz)
8. "Pozostałe" (outliers <10%)

## 🎯 Zasady semantyczne wbudowane w AI

### Test kompatybilności treści:
> "Czy user szukający pierwszej frazy będzie zadowolony znajdując treść o drugiej frazie na tej samej stronie?"
> - ✅ TAK = ta sama grupa
> - ❌ NIE = różne grupy

### Kryteria podziału:
- **MARKI/PRODUCENCI:** różne marki = różne grupy jeśli są alternatywami  
- **TYPY/KATEGORIE:** różne typy produktu = różne grupy
- **INTENCJE:** można łączyć jeśli dotyczą tego samego obiektu
- **POZIOM SZCZEGÓŁOWOŚCI:** ogólne z konkretnymi jeśli ten sam temat

### Hierarchia abstrakcji:
```
ogólne → szczegółowe → warianty
"soczewki" ⊃ "soczewki kontaktowe" ⊃ "soczewki miesięczne" ⊃ "Acuvue Oasys miesięczne"
```

## 🛡️ Obsługa błędów i fallback

### Fallback do HDBSCAN:
- Timeout AI API (>300s)
- Błędy sieciowe po retry
- Nieprawidłowy JSON od AI
- Brak dostępu do AI clientów

### Retry logic:
- 3 próby dla każdego zapytania AI
- Exponential backoff (2^attempt sekund)
- Szczegółowe logowanie błędów z kontekstem

### Validation:
- Weryfikacja formatów JSON
- Sprawdzenie spójności fraz
- Walidacja metryk jakości

## 📈 Monitoring i metryki

### Metryki jakości:
```python
{
    "num_clusters": 8,                    # Liczba utworzonych grup
    "noise_points": 12,                   # Liczba outliers
    "noise_ratio": 0.12,                  # Procent outliers (cel: ≤35%)
    "clustering_method": "ai_with_memory", # Użyta metoda
    "ai_provider": "openai",              # AI provider
    "target_groups_achieved": true,       # Czy cel grup osiągnięty
    "quality_goal_achieved": true         # Czy cel jakości osiągnięty
}
```

### Logi do monitorowania:
```
🤖 [AI-CLUSTERING] ===== AI-DRIVEN CLUSTERING Z PAMIĘCIĄ =====
🎯 [STRATEGY] Docelowa liczba grup: 8
🔄 [BATCH-1] Przetwarzam 25 fraz
✅ [FINALIZE] Finalne grupy: 8
🎯 [AI-CLUSTERING] SUKCES! Osiągnięto cel ≤35% outliers!
```

## 🔧 Rozwój i testowanie

### Porównywanie metod:
1. Uruchom z `USE_AI_CLUSTERING=true` 
2. Zapisz wyniki
3. Uruchom z `USE_AI_CLUSTERING=false`
4. Porównaj metryki jakości

### Kluczowe metryki do porównania:
- Liczba klastrów vs cel (8-12)
- Procent outliers (cel: ≤35%)
- Średni rozmiar grupy (cel: 5-15 fraz)
- Czas wykonania
- Semantyczna spójność grup

## 💡 Best practices

### Dla developera:
- Zawsze testuj z prawdziwymi danymi SEO
- Monitoruj koszty AI API
- Sprawdzaj logi dla debugowania
- Używaj AI clustering dla nowych projektów

### Dla biznesu:
- Każda grupa = jeden typ treści/strony
- Każda grupa = jedna sekcja URL
- Każda grupa = jeden projekt content marketing
- Weryfikuj grup przed utworzeniem briefów

## 🚀 Wdrożenie

### Krok 1: Włącz w .env
```bash
USE_AI_CLUSTERING=true
```

### Krok 2: Przetestuj z małym zbiorem
```bash
# Uruchom klastrowanie dla testowego słowa kluczowego
curl -X POST http://localhost:8000/api/v6/clustering/start \
  -H "Content-Type: application/json" \
  -d '{"keyword_id": "test-keyword-uuid"}'
```

### Krok 3: Porównaj wyniki
```bash
# Sprawdź rezultaty
curl http://localhost:8000/api/v6/clustering/results/test-keyword-uuid
```

### Krok 4: Wdrożenie produkcyjne
- Monitoruj metryki przez tydzień
- Porównaj jakość z starym systemem  
- W razie problemów: `USE_AI_CLUSTERING=false`

## 📞 Wsparcie

W przypadku problemów:
1. Sprawdź logi aplikacji
2. Sprawdź zmienne środowiskowe
3. Sprawdź limity API
4. Użyj fallback: `USE_AI_CLUSTERING=false`

Nowy system jest w pełni kompatybilny wstecznie - można bezpiecznie przełączać między metodami. 