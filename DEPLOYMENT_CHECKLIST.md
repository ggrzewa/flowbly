# ✅ Railway Deployment Checklist

## PRE-DEPLOYMENT

- [x] Naprawione wszystkie lokalne ścieżki Windows
- [x] Port dynamiczny (odczyt z `$PORT`)
- [x] Utworzono `.gitignore`
- [x] Utworzono `railway.json`
- [x] Utworzono `Procfile`
- [x] `requirements.txt` zawiera wszystkie zależności
- [ ] Przetestowano lokalnie: `uvicorn app.main:app --host 0.0.0.0 --port 8000`
- [ ] Kod jest w repozytorium Git

---

## RAILWAY SETUP

- [ ] Utworzono projekt na Railway.app
- [ ] Podłączono repozytorium GitHub
- [ ] Ustawiono zmienne środowiskowe:
  - [ ] `SUPABASE_URL`
  - [ ] `SUPABASE_KEY`
  - [ ] `OPENAI_API_KEY`
  - [ ] `ANTHROPIC_API_KEY`
  - [ ] `AI_PROVIDER`
  - [ ] `AI_MODEL_OPENAI`
  - [ ] `AI_MODEL_CLAUDE`
  - [ ] `AI_MODEL_GPT5`
  - [ ] `GPT5_REASONING_EFFORT`
  - [ ] `GPT5_VERBOSITY`
  - [ ] `RAILWAY_ENVIRONMENT=production`
  - [ ] (Opcjonalnie) `DATAFORSEO_LOGIN`
  - [ ] (Opcjonalnie) `DATAFORSEO_PASSWORD`

---

## POST-DEPLOYMENT

- [ ] Sprawdzono logi Railway - brak błędów
- [ ] Test endpoint `/` - zwraca JSON
- [ ] Test endpoint `/seo-analysis` - zwraca HTML
- [ ] Test połączenia z Supabase
- [ ] Test AI providers (OpenAI/Claude)
- [ ] Sprawdzono metryki (CPU, Memory)
- [ ] Zapisano URL aplikacji: `https://________________.up.railway.app`

---

## SUPABASE DATABASE

- [ ] Uruchomiono `create_semantic_tables.sql` w Supabase SQL Editor
- [ ] Uruchomiono `create_architecture_tables.sql` w Supabase SQL Editor
- [ ] Zweryfikowano że tabele istnieją:
  - [ ] `keywords`
  - [ ] `keyword_relations`
  - [ ] `serp_results`
  - [ ] `autocomplete_results`
  - [ ] `semantic_clusters`
  - [ ] `semantic_groups`
  - [ ] `semantic_group_members`
  - [ ] `architectures`
  - [ ] `architecture_pages`
  - [ ] `architecture_links`
  - [ ] `content_briefs`
  - [ ] `content_scaffolds`

---

## OPTIONAL

- [ ] Dodano własną domenę w Railway
- [ ] Skonfigurowano DNS (CNAME)
- [ ] Dodano monitoring zewnętrzny
- [ ] Skonfigurowano alerty (email/Slack)
- [ ] Ustawiono backup Supabase
- [ ] Dodano rate limiting
- [ ] Skonfigurowano CORS (jeśli potrzebny)

---

## KOMENDY DO TESTOWANIA

### Test lokalny
```bash
# Aktywuj venv
.\venv\Scripts\activate

# Uruchom aplikację
uvicorn app.main:app --host 0.0.0.0 --port 8000

# W innym terminalu:
curl http://localhost:8000/
```

### Test produkcyjny
```bash
# Sprawdź status
curl https://TWOJA-APP.up.railway.app/

# Test analizy
curl https://TWOJA-APP.up.railway.app/seo-analysis
```

---

## TROUBLESHOOTING COMMANDS

### Railway CLI
```bash
# Zainstaluj Railway CLI
npm i -g @railway/cli

# Login
railway login

# Link do projektu
railway link

# Zobacz logi
railway logs

# Sprawdź zmienne
railway variables

# Otwórz dashboard
railway open
```

---

**Status projektu:** 🟢 READY TO DEPLOY

Wszystkie wymagane zmiany zostały wykonane.
Projekt jest gotowy do wdrożenia na Railway.

**Następny krok:** Stwórz projekt na Railway.app i połącz z repozytorium Git.

