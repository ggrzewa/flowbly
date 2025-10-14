#!/usr/bin/env python3
"""
SUPER PROSTY SYSTEM KLASTROWANIA

Filozofia: "Zrób semantyzację tych fraz" i tyle!
Tak jak człowiek by pogrupował gdyby tworzył strony internetowe.
"""

import asyncio
import json
import numpy as np
import time
import os
from typing import List, Dict, Tuple
from openai import AsyncOpenAI
from anthropic import AsyncAnthropic

class SuperSimpleClusteringService:
    """
    SUPER PROSTY clustering - bez komplikacji!
    """
    
    def __init__(self):
        # AI clients
        openai_api_key = os.getenv("OPENAI_API_KEY")
        claude_api_key = os.getenv("ANTHROPIC_API_KEY")
        self.ai_provider = os.getenv("AI_PROVIDER", "openai").lower()
        
        if openai_api_key:
            self.openai_client = AsyncOpenAI(api_key=openai_api_key)
        else:
            self.openai_client = None
            
        if claude_api_key:
            self.claude_client = AsyncAnthropic(api_key=claude_api_key)
        else:
            self.claude_client = None
    
    def create_super_simple_prompt(self, phrases: List[str], seed_keyword: str) -> Tuple[str, str]:
        """
        SUPER PROSTY PROMPT - bez komplikacji!
        """
        
        system_prompt = "Jesteś ekspertem grupowania fraz. Grupujesz frazy tak, jak zrobiłby to człowiek myślący o stronach internetowych."
        
        formatted_phrases = "\n".join(f"- {phrase}" for phrase in phrases)
        
        user_prompt = f"""Pogrupuj te frazy na temat "{seed_keyword}" w sensowne grupy semantyczne.

ZASADA: Każda grupa = jedna strona internetowa. Frazy w grupie muszą pasować do tej samej treści.

FRAZY:
{formatted_phrases}

Zrób to tak, jak sam byś pogrupował gdybyś tworzył strony internetowe.

Cel: 6-10 grup, minimalne outliers.

JSON:
{{
  "groups": [
    {{
      "name": "Nazwa grupy",
      "phrases": ["fraza1", "fraza2", "fraza3"]
    }}
  ],
  "outliers": ["fraza_niepasująca"]
}}"""

        return system_prompt, user_prompt
    
    async def call_ai(self, system_prompt: str, user_prompt: str) -> str:
        """Proste wywołanie AI"""
        
        try:
            if self.ai_provider == "openai" and self.openai_client:
                response = await self.openai_client.chat.completions.create(
                    model="gpt-4o",
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": user_prompt}
                    ],
                    temperature=0.1,
                    max_tokens=4096
                )
                return response.choices[0].message.content
                
            elif self.ai_provider == "claude" and self.claude_client:
                response = await self.claude_client.messages.create(
                    model="claude-3-5-sonnet-20241022",
                    max_tokens=4096,
                    temperature=0.1,
                    system=system_prompt,
                    messages=[{"role": "user", "content": user_prompt}]
                )
                return response.content[0].text
            else:
                raise ValueError(f"AI provider {self.ai_provider} niedostępny")
                
        except Exception as e:
            print(f"❌ AI Error: {e}")
            raise e
    
    def parse_response(self, ai_response: str) -> Dict[str, List[str]]:
        """Proste parsowanie JSON"""
        
        try:
            # Oczyszczenie
            cleaned = ai_response.strip()
            if cleaned.startswith('```json'):
                cleaned = cleaned[7:]
            if cleaned.startswith('```'):
                cleaned = cleaned[3:]
            if cleaned.endswith('```'):
                cleaned = cleaned[:-3]
            cleaned = cleaned.strip()
            
            # Znajdź JSON
            start = cleaned.find('{')
            end = cleaned.rfind('}')
            if start != -1 and end != -1:
                json_part = cleaned[start:end+1]
                result = json.loads(json_part)
                
                # Konwertuj do prostego formatu
                groups = {}
                for group in result.get("groups", []):
                    group_name = group.get("name", "Grupa")
                    group_phrases = group.get("phrases", [])
                    if group_phrases:
                        groups[group_name] = group_phrases
                
                # Dodaj outliers
                if result.get("outliers"):
                    groups["outliers"] = result["outliers"]
                
                return groups
            else:
                raise ValueError("Nie znaleziono JSON")
                
        except Exception as e:
            print(f"❌ Parse Error: {e}")
            return {}
    
    async def cluster_phrases(self, phrases: List[str], seed_keyword: str) -> Dict[str, List[str]]:
        """
        GŁÓWNA METODA - super prosty clustering
        """
        
        print(f"🚀 SUPER SIMPLE CLUSTERING")
        print(f"📋 Frazy: {len(phrases)}")
        print(f"🎯 Temat: {seed_keyword}")
        
        start_time = time.time()
        
        try:
            # Stwórz prosty prompt
            system_prompt, user_prompt = self.create_super_simple_prompt(phrases, seed_keyword)
            
            # Wywołaj AI
            ai_response = await self.call_ai(system_prompt, user_prompt)
            
            # Parsuj wyniki
            groups = self.parse_response(ai_response)
            
            # Podsumowanie
            processing_time = time.time() - start_time
            num_groups = len([name for name in groups.keys() if name != "outliers"])
            outliers_count = len(groups.get("outliers", []))
            outlier_ratio = outliers_count / len(phrases) if len(phrases) > 0 else 0
            
            print(f"✅ WYNIKI:")
            print(f"  📊 Grup: {num_groups}")
            print(f"  📊 Outliers: {outliers_count} ({outlier_ratio:.1%})")
            print(f"  ⏱️ Czas: {processing_time:.1f}s")
            
            return groups
            
        except Exception as e:
            print(f"❌ Błąd: {e}")
            return {}

async def test_super_simple():
    """Test z frazami użytkownika"""
    
    phrases = [
        "soczewki",
        "soczewki acuvue oasys",
        "soczewki astygmatyzm",
        "soczewki jednodniowe",
        "soczewki kolorowe",
        "soczewki kontaktowe",
        "soczewki kontaktowe astygmatyzm",
        "soczewki miesięczne",
        "soczewki progresywne",
        "soczewki toryczne",
        "acuvue oasys soczewki",
        "acuvue soczewki",
        "biofinity soczewki",
        "family optic twoje soczewki",
        "ile kosztują soczewki kontaktowe roczne",
        "ile kosztują soczewki na stałe",
        "jak założyć soczewki",
        "kodano soczewki",
        "kolorowe soczewki",
        "soczewki acuvue",
        "soczewki biofinity",
        "soczewki kontaktowe 1-dniowe",
        "soczewki kontaktowe 30-dniowe",
        "soczewki kontaktowe miesięczne",
        "tanie soczewki",
        "twoje soczewki",
        "vision express soczewki",
        "Czym są soczewki?",
        "Ile godzin maksymalnie można nosić soczewki?",
        "Ile kosztuje 1 soczewka?",
        "Jakie są minusy noszenia soczewek?",
        "Soczewki Biofinity",
        "Soczewki Cena",
        "Soczewki Fizyka",
        "Soczewki kolorowe",
        "Soczewki kontaktowe 30 dniowe",
        "Soczewki kontaktowe miesięczne"
    ]
    
    # Usuń duplikaty
    unique_phrases = list(dict.fromkeys(phrases))
    
    service = SuperSimpleClusteringService()
    groups = await service.cluster_phrases(unique_phrases, "soczewki")
    
    print(f"\n📋 SZCZEGÓŁOWE WYNIKI:")
    for group_name, group_phrases in groups.items():
        print(f"\n🏷️ {group_name} ({len(group_phrases)} fraz):")
        for phrase in group_phrases:
            print(f"  - {phrase}")

if __name__ == "__main__":
    # Ustaw zmienne środowiskowe dla testów
    os.environ['OPENAI_API_KEY'] = os.environ.get('OPENAI_API_KEY', 'sk-test-key')
    os.environ['AI_PROVIDER'] = 'openai'
    
    asyncio.run(test_super_simple()) 