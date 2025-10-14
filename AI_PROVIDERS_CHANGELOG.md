# 🤖 AI PROVIDERS UPDATE - Claude Sonnet 4 Support

## Przegląd zmian

Dodano obsługę **Claude Sonnet 4** jako alternatywę do OpenAI GPT-4o w systemie klastrowania semantycznego. System teraz obsługuje wybór między różnymi AI providerami z konfiguracją przez zmienne środowiskowe.

## ✨ Nowe funkcje

### 1. 🔧 Konfigurowalny AI Provider
- **AI_PROVIDER** - wybór między `openai` lub `claude`
- **AI_MODEL_OPENAI** - model OpenAI (domyślnie `gpt-4o`)
- **AI_MODEL_CLAUDE** - model Claude (domyślnie `claude-3-5-sonnet-20241022`)

### 2. 🧪 Nowe endpointy testowe
- **GET /api/v6/clustering/test-ai** - testuje aktywny AI provider
- **GET /api/v6/clustering/test-openai** - testuje OpenAI (kompatybilność)

### 3. 🤖 Obsługa wielu modeli
**OpenAI:**
- `gpt-4o` (najlepszy)
- `gpt-4o-mini` (tańszy)
- `gpt-4-turbo`

**Claude:**
- `claude-3-5-sonnet-20241022` (najlepszy)
- `claude-3-5-haiku-20241022` (tańszy)
- `claude-3-opus-20240229`

## 📁 Zmodyfikowane pliki

### `app/services/semantic_clustering.py`
- ✅ Dodano konfigurację AI providera w `__init__`
- ✅ Rozszerzono `_ai_clustering_with_intents()` o obsługę Claude
- ✅ Dodano `test_ai_connection()` z obsługą obu providerów
- ✅ Zaimplementowano obsługę API Claude z prawidłowymi kosztami

### `app/main.py`
- ✅ Dodano endpoint `/api/v6/clustering/test-ai`
- ✅ Zachowano kompatybilność z `/api/v6/clustering/test-openai`

### `requirements.txt`
- ✅ Dodano `anthropic>=0.40.0` dla Claude API
- ✅ Uzupełniono wszystkie zależności AI/ML

## 🛠️ Konfiguracja

### Opcja 1: OpenAI (domyślnie)
```env
AI_PROVIDER=openai
AI_MODEL_OPENAI=gpt-4o
OPENAI_API_KEY=sk-...
```

### Opcja 2: Claude Sonnet 4
```env
AI_PROVIDER=claude
AI_MODEL_CLAUDE=claude-3-5-sonnet-20241022
OPENAI_API_KEY=sk-...  # nadal potrzebny dla embeddingów
ANTHROPIC_API_KEY=sk-ant-...
```

## 💰 Porównanie kosztów

| Provider | Model | Input ($/1K tokens) | Output ($/1K tokens) |
|----------|-------|-------------------|---------------------|
| OpenAI | gpt-4o | $0.0025 | $0.010 |
| OpenAI | gpt-4o-mini | $0.00015 | $0.0006 |
| Claude | sonnet-3.5 | $0.003 | $0.015 |
| Claude | haiku-3.5 | $0.00025 | $0.00125 |

## 🔍 Testowanie

Po konfiguracji przetestuj połączenia:

```bash
# Test aktywnego providera
curl http://localhost:8000/api/v6/clustering/test-ai

# Test OpenAI (niezależnie od AI_PROVIDER)
curl http://localhost:8000/api/v6/clustering/test-openai
```

## ⚡ Wydajność

### Czas odpowiedzi (szacunkowy):
- **OpenAI GPT-4o**: ~15-30s dla 100 fraz
- **Claude Sonnet**: ~20-40s dla 100 fraz  
- **Claude Haiku**: ~10-20s dla 100 fraz

### Jakość klastrowania:
- **GPT-4o**: Najlepsza jakość, stabilne wyniki
- **Claude Sonnet**: Podobna jakość, czasem lepsze nazwy klastrów
- **Claude Haiku**: Tańszy, nieco gorsza jakość

## 🚨 Ważne uwagi

1. **OpenAI zawsze wymagany**: Embeddingi nadal przez OpenAI (brak alternatywy)
2. **Kompatybilność**: Stary kod nadal działa bez zmian
3. **Przełączanie**: Można zmieniać provider bez restartowania serwera
4. **Fallback**: System automatycznie spada na HDBSCAN w razie błędu AI

## 🧪 Rekomendacje testowe

### Do przetestowania Claude:
1. Dodaj `ANTHROPIC_API_KEY` do `.env`
2. Ustaw `AI_PROVIDER=claude`
3. Wybierz model `claude-3-5-sonnet-20241022`
4. Przetestuj na słowie "soczewki" (31% outliers z OpenAI)
5. Porównaj wyniki z OpenAI

### Metryki do porównania:
- **% outliers** (cel: <10%)
- **Jakość nazw klastrów**
- **Czas przetwarzania**
- **Koszt na frazy**
- **Stabilność wyników**

## 🎯 Następne kroki

Po przetestowaniu Claude możesz:
1. Wybrać najlepszy provider dla Twojego use case
2. Dostroić modele (np. Claude Haiku dla kosztów)
3. Porównać wyniki na różnych słowach kluczowych
4. Ustawić provider jako domyślny w systemie 