# 🚂 Railway Deployment - Quick Start

## 🎯 Ten projekt jest gotowy do wdrożenia na Railway.app

### ✅ Co zostało zrobione:
- ✅ Wszystkie lokalne ścieżki Windows naprawione
- ✅ Port dynamiczny ($PORT)
- ✅ Logi zapisywane do /tmp na Railway
- ✅ .gitignore chroni sekrety
- ✅ railway.json + Procfile skonfigurowane
- ✅ requirements.txt zawiera wszystkie zależności

---

## 🚀 Deploy w 5 krokach:

### 1. Stwórz repozytorium Git (jeśli jeszcze nie masz)
```bash
git init
git add .
git commit -m "Ready for Railway deployment"
git branch -M main
git remote add origin https://github.com/twoj-user/twoje-repo.git
git push -u origin main
```

### 2. Utwórz projekt na Railway
1. Wejdź na https://railway.app/
2. Zaloguj się przez GitHub
3. Kliknij **"New Project"**
4. Wybierz **"Deploy from GitHub repo"**
5. Wybierz swoje repozytorium

### 3. Ustaw zmienne środowiskowe
W Railway Dashboard → **Variables**, dodaj:

**Kliknij "Raw Editor" i wklej:**
```
SUPABASE_URL=https://twoj-projekt.supabase.co
SUPABASE_KEY=twoj_klucz_anon
OPENAI_API_KEY=sk-proj-...
ANTHROPIC_API_KEY=sk-ant-...
AI_PROVIDER=gpt-5
AI_MODEL_OPENAI=gpt-4o-mini
AI_MODEL_CLAUDE=claude-sonnet-4-20250514
AI_MODEL_GPT5=gpt-5
GPT5_REASONING_EFFORT=medium
GPT5_VERBOSITY=medium
RAILWAY_ENVIRONMENT=production
```

### 4. Deploy
Railway automatycznie:
- Wykryje Python
- Zainstaluje zależności z `requirements.txt`
- Uruchomi aplikację z `railway.json`
- Przezieli publiczny URL

### 5. Testuj
```bash
# Zamień na swój URL z Railway
curl https://twoja-app.up.railway.app/

# Powinno zwrócić:
# {"message":"SEO Analysis Tool","version":"1.0.0","endpoints":["/seo-analysis"]}
```

---

## 📋 Dodatkowe pliki pomocnicze:

- **RAILWAY_DEPLOYMENT_GUIDE.md** - pełna dokumentacja
- **DEPLOYMENT_CHECKLIST.md** - checklist krok po kroku
- **ENV_TEMPLATE.txt** - szablon zmiennych środowiskowych
- **struktura_folderow.txt** - struktura projektu

---

## 🐛 Szybka pomoc:

### Problem: Aplikacja nie startuje
```bash
# Sprawdź logi w Railway Dashboard
railway logs
```

### Problem: Brak połączenia z bazą
- Sprawdź `SUPABASE_URL` i `SUPABASE_KEY`
- Uruchom SQL z `create_semantic_tables.sql` w Supabase

### Problem: AI nie działa
- Sprawdź klucze: `OPENAI_API_KEY`, `ANTHROPIC_API_KEY`
- Sprawdź limity API w dashboard OpenAI/Anthropic

---

## 💡 Pro tipy:

1. **Własna domena:**
   Railway → Settings → Domains → Add Custom Domain

2. **Automatyczne deploye:**
   Każdy push do `main` = automatyczny deploy

3. **Preview branches:**
   Railway może stworzyć osobne środowisko dla każdego PR

4. **Monitoring:**
   Railway pokazuje CPU, RAM, Network w czasie rzeczywistym

5. **Koszty:**
   - Starter: $5/mies (500h)
   - Developer: $20/mies (unlimited)

---

## 📞 Pomoc:

- Railway Docs: https://docs.railway.app/
- Railway Discord: https://discord.gg/railway
- Status Railway: https://status.railway.app/

---

**Status:** 🟢 GOTOWE DO DEPLOYMENTU

**Następny krok:** Wejdź na Railway.app i kliknij "New Project"

