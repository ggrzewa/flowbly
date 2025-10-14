# 🚀 Railway Deployment Guide

## ✅ WYKONANE ZMIANY

### 1. Naprawione ścieżki logów
- ✅ `app/main.py` - linia 1153-1154
- ✅ `app/services/content_scaffold_generator.py` - linia 523-524
- **Zmiana:** Lokalne ścieżki Windows zastąpione dynamicznym wyborem:
  ```python
  log_dir = "/tmp" if os.getenv("RAILWAY_ENVIRONMENT") else "."
  ```

### 2. Dynamiczny port
- ✅ `app/main.py` - linia 1285
- **Zmiana:** Port odczytywany z zmiennej środowiskowej Railway:
  ```python
  port = int(os.getenv("PORT", 8000))
  ```

### 3. Nowe pliki konfiguracyjne
- ✅ `.gitignore` - zabezpiecza przed wyciekiem sekretów
- ✅ `railway.json` - konfiguracja Railway
- ✅ `Procfile` - alternatywny sposób uruchomienia
- ✅ `RAILWAY_DEPLOYMENT_GUIDE.md` - ten plik

---

## 📋 KROKI DEPLOYMENTU NA RAILWAY

### Krok 1: Przygotuj repozytorium Git
```bash
git init
git add .
git commit -m "Initial commit - Railway ready"
```

### Krok 2: Utwórz projekt na Railway
1. Wejdź na https://railway.app/
2. Kliknij "New Project"
3. Wybierz "Deploy from GitHub repo"
4. Podłącz swoje repozytorium
5. Railway automatycznie wykryje Python i zainstaluje zależności

### Krok 3: Ustaw zmienne środowiskowe
W Railway Dashboard → Variables, dodaj:

**Obowiązkowe:**
```
SUPABASE_URL=https://twoj-projekt.supabase.co
SUPABASE_KEY=twoj_klucz_anon
OPENAI_API_KEY=sk-...
ANTHROPIC_API_KEY=sk-ant-...
RAILWAY_ENVIRONMENT=production
```

**Konfiguracja AI:**
```
AI_PROVIDER=gpt-5
AI_MODEL_OPENAI=gpt-4o-mini
AI_MODEL_CLAUDE=claude-sonnet-4-20250514
AI_MODEL_GPT5=gpt-5
GPT5_REASONING_EFFORT=medium
GPT5_VERBOSITY=medium
```

**DataForSEO (opcjonalne, jeśli używasz):**
```
DATAFORSEO_LOGIN=twoj_login
DATAFORSEO_PASSWORD=twoj_password
```

### Krok 4: Deploy
Railway automatycznie:
1. Zainstaluje zależności z `requirements.txt`
2. Uruchomi aplikację używając `railway.json` lub `Procfile`
3. Przydzieli publiczny URL (np. `https://twoja-app.up.railway.app`)

---

## 🔍 WERYFIKACJA PO DEPLOYMENCIE

### Test 1: Sprawdź czy aplikacja działa
```bash
curl https://twoja-app.up.railway.app/
```
Powinieneś zobaczyć:
```json
{
  "message": "SEO Analysis Tool",
  "version": "1.0.0",
  "endpoints": ["/seo-analysis"]
}
```

### Test 2: Sprawdź endpoint analizy
```bash
curl https://twoja-app.up.railway.app/seo-analysis
```
Powinien zwrócić HTML z formularzem.

### Test 3: Sprawdź logi
W Railway Dashboard → Deployments → Logs, sprawdź czy:
- ✅ Aplikacja startuje bez błędów
- ✅ Połączenie z Supabase działa
- ✅ Klucze API są załadowane
- ✅ Port jest ustawiony poprawnie

---

## 🐛 TROUBLESHOOTING

### Problem: "Application failed to respond"
**Rozwiązanie:**
- Sprawdź logi Railway
- Upewnij się, że `PORT` nie jest hardcoded
- Zweryfikuj czy `host="0.0.0.0"` (nie `127.0.0.1`)

### Problem: "Missing environment variables"
**Rozwiązanie:**
- Sprawdź Variables w Railway Dashboard
- Upewnij się że wszystkie klucze są ustawione
- Zrestartuj deployment

### Problem: "Database connection failed"
**Rozwiązanie:**
- Sprawdź `SUPABASE_URL` i `SUPABASE_KEY`
- Upewnij się że Supabase project jest aktywny
- Sprawdź czy tabele istnieją (uruchom SQL z `create_semantic_tables.sql`)

### Problem: "AI provider errors"
**Rozwiązanie:**
- Sprawdź klucze API (OpenAI, Anthropic)
- Upewnij się że `AI_PROVIDER` jest ustawiony
- Sprawdź limity API (quota, rate limits)

### Problem: "Logs not saving"
**Rozwiązanie:**
- Sprawdź czy `/tmp` jest dostępny
- Logi na Railway są tymczasowe (używaj Railway Logs zamiast plików)
- Rozważ integrację z zewnętrznym systemem logowania

---

## 📊 MONITORING

### Logi Railway
```bash
# W Railway CLI
railway logs
```

### Metryki
Railway Dashboard pokazuje:
- CPU usage
- Memory usage
- Network traffic
- Response times

---

## 🔐 BEZPIECZEŃSTWO

### ✅ Zrobione:
- `.gitignore` blokuje `.env` i sekrety
- Zmienne środowiskowe w Railway (nie w kodzie)
- Brak hardcoded ścieżek

### ⚠️ Do zrobienia:
- [ ] Dodaj rate limiting (np. SlowAPI)
- [ ] Ustaw CORS jeśli frontend jest na innej domenie
- [ ] Rozważ dodanie autentykacji dla wrażliwych endpointów
- [ ] Monitoruj koszty API (OpenAI, Claude, DataForSEO)

---

## 💰 KOSZTY

### Railway:
- Starter Plan: $5/miesiąc (500h compute)
- Developer Plan: $20/miesiąc (unlimited)

### Supabase:
- Free Tier: 500 MB database
- Pro: $25/miesiąc

### AI APIs:
- OpenAI: pay-as-you-go
- Claude: pay-as-you-go
- DataForSEO: według użycia

---

## 🎯 NEXT STEPS

1. **Własna domena:**
   - Railway Dashboard → Settings → Domains
   - Dodaj CNAME: `twoja-domena.pl` → `twoja-app.up.railway.app`

2. **CI/CD:**
   - Każdy push do `main` automatycznie deployuje
   - Możesz ustawić branch preview dla testów

3. **Scaling:**
   - Railway automatycznie skaluje (w ramach planu)
   - Rozważ Redis dla cache jeśli będzie duży ruch

4. **Backup:**
   - Eksportuj dane z Supabase regularnie
   - Railway robi snapshoty projektu

---

## 📞 SUPPORT

- Railway Docs: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway
- Supabase Docs: https://supabase.com/docs

---

**Ostatnia aktualizacja:** 2025-01-14
**Status:** ✅ Ready for deployment

