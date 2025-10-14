# 🎯 Konfiguracja Enhanced AI Prompt System

## Nowa Zmienna Środowiskowa

Dodaj następującą zmienną do swojego pliku `.env`:

```bash
# Kontrola rodzaju promptu AI (true = nowy enhanced prompt, false = stary legacy prompt)
USE_ENHANCED_PROMPT=false
```

## Strategia Wdrażania

### Etap 1: Testowanie (USE_ENHANCED_PROMPT=false)
- Rozpocznij z wartością `false` (używaj stary prompt)
- System działa jak wcześniej
- Wszystkie nowe metody są dostępne ale nieaktywne

### Etap 2: Pierwsze testy (USE_ENHANCED_PROMPT=true)
```bash
USE_ENHANCED_PROMPT=true
```
- Uruchom klastrowanie na małej próbce danych
- Sprawdź logi - powinieneś zobaczyć:
  ```
  🎯 [AI-API] Używam enhanced prompt
  📊 [QUALITY] Liczba grup: X
  📊 [QUALITY] Optymalna liczba grup: true/false
  ```

### Etap 3: Porównanie wyników
Sprawdź czy nowy prompt daje lepsze rezultaty:
- **Liczba grup**: Czy masz 6-12 grup zamiast 37?
- **Rozmiary grup**: Czy grupy mają 4-15 fraz każda?
- **Outliers**: Czy masz mniej niż 15% outliers?

### Etap 4: Wdrożenie produkcyjne
Jeśli wyniki są lepsze:
```bash
USE_ENHANCED_PROMPT=true
```

## Monitorowanie Jakości

Nowy system automatycznie loguje metryki jakości:

```
📊 [QUALITY] Liczba grup: 8
📊 [QUALITY] Średni rozmiar grupy: 12.5
📊 [QUALITY] Rozmiary grup: [15, 12, 10, 8, 14, 11, 9, 16]
📊 [QUALITY] Optymalna liczba grup: true
📊 [QUALITY] Outliers: 2/98 (2.0%)
📊 [QUALITY] Małe grupy (<4): 0, Duże grupy (>15): 1
```

## Różnice między promptami

### Legacy Prompt (stary)
- Szczegółowe instrukcje hardkodowane dla konkretnych tematów
- Format JSON dla specyficznej struktury
- Używa danych DataForSEO intents
- Może tworzyć zbyt dużo małych grup

### Enhanced Prompt (nowy)
- Uniwersalny framework działający dla każdego tematu
- Kontekst biznesowy i edukacyjny
- Przykłady procesu myślenia
- Skupia się na intencjach użytkowników
- Cel: 6-12 grup po 4-15 fraz

## Rozwiązywanie problemów

### Problem: "USE_ENHANCED_PROMPT not found"
**Rozwiązanie**: Dodaj zmienną do pliku `.env` w katalogu głównym projektu

### Problem: Nadal widzę 37 małych grup
**Rozwiązanie**: 
1. Sprawdź czy zmienna została ustawiona na `true`
2. Restart serwera FastAPI
3. Sprawdź logi czy widzisz "🎯 [AI-API] Używam enhanced prompt"

### Problem: AI zwraca błędny JSON  
**Rozwiązanie**: Nowy prompt ma lepsze instrukcje JSON, ale jeśli problem się powtarza, włącz szczegółowe logi

## Przykład kompletnej konfiguracji .env

```bash
# AI Provider Configuration
AI_PROVIDER=claude
AI_MODEL_OPENAI=gpt-4o
AI_MODEL_CLAUDE=claude-3-5-sonnet-20241022

# Enhanced Prompt System
USE_ENHANCED_PROMPT=true

# Clustering Configuration  
USE_AI_CLUSTERING=true
ENABLE_CLUSTERING_CONSOLIDATION=true

# API Keys
OPENAI_API_KEY=your_openai_key_here
ANTHROPIC_API_KEY=your_claude_key_here

# Database
SUPABASE_URL=your_supabase_url
SUPABASE_KEY=your_supabase_key
```

## Oczekiwane rezultaty

Po włączeniu enhanced prompt powinieneś zobaczyć:
- ✅ 6-12 grup zamiast 37
- ✅ Grupy o rozmiarach 4-15 fraz 
- ✅ Nazwy grup odzwierciedlające intencje użytkowników
- ✅ Mniej niż 15% outliers
- ✅ Lepsze wykorzystanie biznesowe wyników 