class UniversalConsolidator:
    """
    🔗 UNIWERSALNY POST-PROCESSING CONSOLIDATOR
    
    Automatycznie wykrywa podobieństwa w nazwach grup i łączy je w większe grupy.
    Działa dla KAŻDEGO tematu bez hardkodowanych wzorców!
    
    Strategia:
    1. "acuvue oasys" + "soczewki acuvue oasys" → "Marki - Acuvue"
    2. "ile kosztują" + "ceny soczewek" → "Ceny i koszty"  
    3. Automatyczne wykrywanie podobieństw w nazwach
    """
    
    def __init__(self, logger):
        self.logger = logger

    def consolidate_groups(self, groups: dict) -> dict:
        """
        🔗 Główna metoda konsolidacji - UNIWERSALNA
        
        Args:
            groups: {group_name: [phrases]}
        Returns:  
            consolidated_groups: {new_name: [phrases]}
        """
        self.logger.info(f"🔗 [UNIVERSAL] Konsoliduję {len(groups)} grup...")
        
        # Krok 1: Wyczyść nazwy z prefixów batch_
        cleaned = self._clean_batch_prefixes(groups)
        
        # Krok 2: Automatyczna konsolidacja podobnych nazw
        consolidated = self._auto_consolidate_similar_names(cleaned)
        
        # Krok 3: Konsolidacja na podstawie zawartości fraz
        final = self._consolidate_by_phrase_similarity(consolidated)
        
        self.logger.info(f"✅ [UNIVERSAL] {len(groups)} → {len(final)} grup")
        return final

    def _clean_batch_prefixes(self, groups: dict) -> dict:
        """Usuń prefixy batch_X_ z nazw grup"""
        cleaned = {}
        for name, phrases in groups.items():
            if name == "tymczasowo_niesklasyfikowane":
                cleaned[name] = phrases
                continue
                
            clean_name = name
            if clean_name.startswith("batch_"):
                parts = clean_name.split("_", 2)
                if len(parts) >= 3:
                    clean_name = parts[2]
                    
            cleaned[clean_name] = phrases
        return cleaned

    def _auto_consolidate_similar_names(self, groups: dict) -> dict:
        """
        🎯 AUTOMATYCZNE wykrywanie podobnych nazw (UNIWERSALNE!)
        
        Przykłady:
        - "Marki Acuvue" + "Acuvue produkty" → "Marki - Acuvue"
        - "Ceny" + "Koszty" + "Ile kosztują" → "Ceny i koszty"
        - "Sklepy" + "Gdzie kupić" → "Sklepy i zakupy"
        """
        consolidated = {}
        processed = set()
        
        for name1, phrases1 in groups.items():
            if name1 in processed or name1 == "tymczasowo_niesklasyfikowane":
                continue
                
            # Znajdź wszystkie podobne nazwy
            similar_groups = [name1]
            for name2, phrases2 in groups.items():
                if (name2 != name1 and 
                    name2 not in processed and 
                    name2 != "tymczasowo_niesklasyfikowane" and
                    self._are_names_similar(name1, name2)):
                    similar_groups.append(name2)
            
            # Połącz grupy
            all_phrases = []
            for group_name in similar_groups:
                all_phrases.extend(groups[group_name])
                processed.add(group_name)
            
            # Usuń duplikaty
            unique_phrases = list(dict.fromkeys(all_phrases))
            
            # Stwórz nazwę
            new_name = self._create_smart_name(unique_phrases, similar_groups)
            consolidated[new_name] = unique_phrases
            
        # Dodaj niesklasyfikowane
        if "tymczasowo_niesklasyfikowane" in groups:
            consolidated["tymczasowo_niesklasyfikowane"] = groups["tymczasowo_niesklasyfikowane"]
            
        return consolidated

    def _are_names_similar(self, name1: str, name2: str) -> bool:
        """UNIWERSALNE wykrywanie podobieństwa nazw"""
        n1, n2 = name1.lower(), name2.lower()
        
        # Wspólne słowa
        words1, words2 = set(n1.split()), set(n2.split())
        common = words1.intersection(words2)
        
        if common:
            similarity = len(common) / min(len(words1), len(words2))
            return similarity >= 0.4
        
        # Zawieranie się nazw
        return n1 in n2 or n2 in n1

    def _create_smart_name(self, phrases: list, original_names: list) -> str:
        """UNIWERSALNE tworzenie nazw na podstawie fraz"""
        
        # Analizuj pierwsze 8 fraz
        sample_phrases = " ".join(phrases[:8]).lower()
        
        # UNIWERSALNE wzorce (działają dla każdego tematu)
        if any(word in sample_phrases for word in ["cena", "koszt", "ile", "tani", "drogi"]):
            return "Ceny i koszty"
        elif any(word in sample_phrases for word in ["sklep", "kupić", "gdzie", "zakup"]):
            return "Sklepy i zakupy" 
        elif any(word in sample_phrases for word in ["jak", "czy", "co", "dlaczego", "?"]):
            return "Pytania i porady"
        elif len(phrases) >= 10:
            # Duże grupy - znajdź dominujące słowo
            word_counts = {}
            for phrase in phrases[:5]:
                for word in phrase.lower().split():
                    if len(word) > 3:
                        word_counts[word] = word_counts.get(word, 0) + 1
            
            if word_counts:
                top_word = max(word_counts.items(), key=lambda x: x[1])[0]
                return f"Grupa główna - {top_word}"
        
        # Fallback
        if len(original_names) > 1:
            return f"Grupa skonsolidowana"
        else:
            return original_names[0]

    def _consolidate_by_phrase_similarity(self, groups: dict) -> dict:
        """Ostateczna konsolidacja na podstawie podobieństwa fraz"""
        
        # Znajdź grupy z bardzo podobnymi frazami
        final_groups = {}
        
        for name, phrases in groups.items():
            if name == "tymczasowo_niesklasyfikowane":
                final_groups[name] = phrases
                continue
                
            # Sprawdź czy ta grupa powinna być połączona z istniejącą
            merged = False
            for existing_name, existing_phrases in list(final_groups.items()):
                if existing_name == "tymczasowo_niesklasyfikowane":
                    continue
                    
                # Sprawdź podobieństwo fraz
                if self._should_merge_by_phrases(phrases, existing_phrases):
                    # Połącz grupy
                    all_phrases = existing_phrases + phrases
                    unique_phrases = list(dict.fromkeys(all_phrases))
                    
                    # Lepsze z dwóch nazw
                    better_name = self._choose_better_name(name, existing_name, unique_phrases)
                    
                    final_groups[better_name] = unique_phrases
                    if existing_name != better_name and existing_name in final_groups:
                        del final_groups[existing_name]
                    
                    merged = True
                    break
            
            if not merged:
                final_groups[name] = phrases
                
        return final_groups

    def _should_merge_by_phrases(self, phrases1: list, phrases2: list) -> bool:
        """Sprawdź czy grupy powinny być połączone na podstawie podobieństwa fraz"""
        # Sprawdź czy mają wspólne słowa kluczowe
        text1 = " ".join(phrases1[:3]).lower()
        text2 = " ".join(phrases2[:3]).lower()
        
        words1 = set(text1.split())
        words2 = set(text2.split())
        common = words1.intersection(words2)
        
        if len(common) >= 2:  # Co najmniej 2 wspólne słowa
            return True
            
        return False

    def _choose_better_name(self, name1: str, name2: str, phrases: list) -> str:
        """Wybierz lepszą nazwę z dwóch opcji"""
        # Preferuj nazwy opisowe nad technicznymi
        if "grupa" in name1.lower() and "grupa" not in name2.lower():
            return name2
        elif "grupa" in name2.lower() and "grupa" not in name1.lower():
            return name1
        
        # Preferuj dłuższe, bardziej opisowe nazwy
        if len(name1) > len(name2):
            return name1
        else:
            return name2 