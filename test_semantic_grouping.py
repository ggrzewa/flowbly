import streamlit as st
import json
import os
from typing import List, Dict, Tuple
import asyncio
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

# ============================ KONFIGURACJA ============================

st.set_page_config(
    page_title="🧠 Semantic Grouping Tester",
    page_icon="🧠",
    layout="wide"
)

# ============================ AI CLIENTS ============================

@st.cache_resource
def get_openai_client():
    api_key = os.getenv("OPENAI_API_KEY")
    if not api_key:
        st.error("❌ OPENAI_API_KEY nie jest ustawiony!")
        return None
    return AsyncOpenAI(api_key=api_key)

@st.cache_resource  
def get_claude_client():
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        st.error("❌ ANTHROPIC_API_KEY nie jest ustawiony!")
        return None
    return AsyncAnthropic(api_key=api_key)

# ============================ AI FUNCTIONS ============================

async def call_openai_grouping(client, system_prompt: str, user_prompt: str, model: str = "gpt-4o") -> Dict:
    """Wywołaj OpenAI API do grupowania"""
    try:
        response = await client.chat.completions.create(
            model=model,
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=0.0,
            response_format={"type": "json_object"}
        )
        
        result = json.loads(response.choices[0].message.content)
        return {
            "success": True,
            "result": result,
            "tokens": response.usage.total_tokens,
            "cost": response.usage.total_tokens * 0.000015  # Przybliżony koszt
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

async def call_claude_grouping(client, system_prompt: str, user_prompt: str, model: str = "claude-3-5-sonnet-20241022") -> Dict:
    """Wywołaj Claude API do grupowania"""
    try:
        response = await client.messages.create(
            model=model,
            max_tokens=4000,
            temperature=0.0,
            system=system_prompt,
            messages=[{"role": "user", "content": user_prompt}]
        )
        
        # Claude może zwrócić JSON w tekście
        content = response.content[0].text
        if "```json" in content:
            json_start = content.find("```json") + 7
            json_end = content.find("```", json_start)
            content = content[json_start:json_end].strip()
        
        result = json.loads(content)
        return {
            "success": True,
            "result": result,
            "tokens": response.usage.input_tokens + response.usage.output_tokens,
            "cost": (response.usage.input_tokens * 0.000003) + (response.usage.output_tokens * 0.000015)
        }
    except Exception as e:
        return {"success": False, "error": str(e)}

# ============================ PROMPTY DOMYŚLNE ============================

DEFAULT_SYSTEM_PROMPT = """Jesteś ekspertem grupowania fraz semantycznie. Grupujesz frazy tak, jak zrobiłby to człowiek myślący o stronach internetowych."""

DEFAULT_USER_PROMPT_TEMPLATE = """Pogrupuj te frazy na temat "{seed_keyword}" w sensowne grupy semantyczne.

ZASADY UNIWERSALNE:
1. Każda grupa = jedna strona internetowa  
2. PREFERUJ WIĘKSZE GRUPY - łącz co się da semantycznie
3. Outliers = TYLKO frazy kompletnie spoza tematu (maksymalnie 10%)
4. Docelowo 4-8 dużych grup po 10-25 fraz każda
5. Lepiej jedna duża grupa niż 3 małe mikrogrupy

FRAZY:
{formatted_phrases}

WAŻNE: Łącz frazy o podobnej intencji w duże, użyteczne grupy!

JSON:
{{
  "groups": [
    {{
      "name": "Nazwa grupy",
      "phrases": ["fraza1", "fraza2", "fraza3"]
    }}
  ],
  "outliers": ["tylko_jeśli_kompletnie_spoza_tematu"]
}}"""

# ============================ STREAMLIT UI ============================

st.title("🧠 Semantic Grouping Tester")
st.markdown("**Testuj różne prompty dla grupowania semantycznego fraz**")

# ============================ SIDEBAR - KONFIGURACJA ============================

st.sidebar.header("⚙️ Konfiguracja")

# Wybór AI Provider
ai_provider = st.sidebar.selectbox(
    "🤖 AI Provider",
    ["OpenAI", "Claude"],
    index=0
)

# Model selection
if ai_provider == "OpenAI":
    model = st.sidebar.selectbox(
        "📱 Model OpenAI", 
        ["gpt-4o", "gpt-4", "gpt-3.5-turbo"],
        index=0
    )
else:
    model = st.sidebar.selectbox(
        "📱 Model Claude",
        ["claude-3-5-sonnet-20241022", "claude-3-sonnet-20240229"],
        index=0
    )

# ============================ MAIN INTERFACE ============================

# Kolumny
col1, col2 = st.columns([1, 1])

with col1:
    st.header("📝 Input")
    
    # Seed keyword
    seed_keyword = st.text_input(
        "🎯 Główne słowo kluczowe (temat)",
        value="soczewki kontaktowe",
        help="Główny temat wokół którego będą grupowane frazy"
    )
    
    # Lista fraz
    st.subheader("📋 Lista fraz (jedna na linię)")
    phrases_text = st.text_area(
        "Frazy do pogrupowania:",
        value="""biofinity soczewki
soczewki progresywne
soczewki astygmatyzm
soczewki toryczne
soczewki kontaktowe miesięczne
family optic twoje soczewki
soczewki biofinity
kolorowe soczewki kontaktowe
soczewki kontaktowe cena
acuvue oasys soczewki
soczewki acuvue oasys
soczewki acuvue
acuvue soczewki
acuvue oasys
ACUVUE OASYS 1-Day
Acuvue Oasys for ASTIGMATISM""",
        height=200
    )
    
    # Konwersja na listę
    phrases_list = [line.strip() for line in phrases_text.split('\n') if line.strip()]
    st.info(f"📊 Znaleziono **{len(phrases_list)}** fraz do grupowania")

with col2:
    st.header("🎛️ Prompty")
    
    # System prompt
    st.subheader("🤖 System Prompt")
    system_prompt = st.text_area(
        "System prompt:",
        value=DEFAULT_SYSTEM_PROMPT,
        height=100,
        help="Instrukcje dla AI o roli i kontekście"
    )
    
    # User prompt template
    st.subheader("👤 User Prompt Template")
    user_prompt_template = st.text_area(
        "User prompt (użyj {seed_keyword} i {formatted_phrases}):",
        value=DEFAULT_USER_PROMPT_TEMPLATE,
        height=300,
        help="Główne instrukcje dla AI. Użyj {seed_keyword} i {formatted_phrases} jako placeholdery"
    )

# ============================ BUTTON & EXECUTION ============================

st.markdown("---")

if st.button("🚀 **GRUPUJ FRAZY**", type="primary", use_container_width=True):
    if not phrases_list:
        st.error("❌ Podaj przynajmniej jedną frazę!")
    elif not seed_keyword:
        st.error("❌ Podaj główne słowo kluczowe!")
    else:
        # Przygotuj prompt
        formatted_phrases = "\n".join(f"- {phrase}" for phrase in phrases_list)
        user_prompt = user_prompt_template.format(
            seed_keyword=seed_keyword,
            formatted_phrases=formatted_phrases
        )
        
        # Progress bar
        progress_bar = st.progress(0)
        status_text = st.empty()
        
        # Call AI
        async def run_grouping():
            status_text.text("🤖 Łączenie z AI...")
            progress_bar.progress(25)
            
            if ai_provider == "OpenAI":
                client = get_openai_client()
                if not client:
                    return None
                status_text.text("🤖 Wywoływanie OpenAI...")
                progress_bar.progress(50)
                result = await call_openai_grouping(client, system_prompt, user_prompt, model)
            else:
                client = get_claude_client()
                if not client:
                    return None
                status_text.text("🤖 Wywoływanie Claude...")
                progress_bar.progress(50)
                result = await call_claude_grouping(client, system_prompt, user_prompt, model)
                
            progress_bar.progress(100)
            status_text.text("✅ Gotowe!")
            return result
        
        # Execute
        try:
            result = asyncio.run(run_grouping())
            
            # Clear progress
            progress_bar.empty()
            status_text.empty()
            
            if result and result.get("success"):
                st.success("✅ **Grupowanie zakończone sukcesem!**")
                
                # Wyniki w kolumnach
                res_col1, res_col2 = st.columns([2, 1])
                
                with res_col1:
                    st.header("📊 Wyniki grupowania")
                    
                    groups = result["result"].get("groups", [])
                    outliers = result["result"].get("outliers", [])
                    
                    # Statystyki
                    total_phrases_in_groups = sum(len(group["phrases"]) for group in groups)
                    outlier_percentage = (len(outliers) / len(phrases_list)) * 100 if phrases_list else 0
                    
                    st.metric("🎯 Liczba grup", len(groups))
                    st.metric("📈 Frazy w grupach", f"{total_phrases_in_groups}/{len(phrases_list)}")
                    st.metric("⚠️ Outliers", f"{len(outliers)} ({outlier_percentage:.1f}%)")
                    
                    # Pokaż grupy
                    for i, group in enumerate(groups, 1):
                        with st.expander(f"**Grupa {i}: {group['name']}** ({len(group['phrases'])} fraz)", expanded=True):
                            for phrase in group['phrases']:
                                st.write(f"• {phrase}")
                    
                    # Outliers
                    if outliers:
                        with st.expander(f"⚠️ **Outliers** ({len(outliers)} fraz)", expanded=True):
                            for phrase in outliers:
                                st.write(f"• {phrase}")
                
                with res_col2:
                    st.header("📈 Statystyki")
                    st.metric("🎯 Tokeny", result.get("tokens", 0))
                    st.metric("💰 Koszt", f"${result.get('cost', 0):.6f}")
                    st.metric("🤖 Provider", ai_provider)
                    st.metric("📱 Model", model)
                    
                    # Raw JSON
                    st.subheader("🔧 Raw JSON Response")
                    st.json(result["result"])
                    
            else:
                st.error(f"❌ **Błąd podczas grupowania:**\n{result.get('error', 'Nieznany błąd')}")
                
        except Exception as e:
            progress_bar.empty()
            status_text.empty()
            st.error(f"❌ **Błąd wykonania:** {str(e)}")

# ============================ FOOTER ============================

st.markdown("---")
st.markdown("**💡 Tip:** Eksperymentuj z różnymi promptami żeby znaleźć optymalne grupowanie!") 