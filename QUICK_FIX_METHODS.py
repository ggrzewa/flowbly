# SZYBKA POPRAWKA - SKOPIUJ TE METODY DO semantic_clustering.py PRZED LINIĄ 3106 (class AIClusteringSession:)

    def _apply_universal_fallback(self, ai_groups: Dict[str, List[str]], phrases: List[str], seed_keyword: str) -> Dict[str, List[str]]:
        """Deterministyczny fallback używający uniwersalnych wzorców semantycznych"""
        improved_groups = {}
        used_phrases = set()
        
        # Zachowaj dobre grupy AI (większe niż 3 frazy)
        for group_name, group_phrases in ai_groups.items():
            if group_name != "outliers" and len(group_phrases) >= 3:
                improved_groups[group_name] = group_phrases
                used_phrases.update(group_phrases)
        
        remaining_phrases = [p for p in phrases if p not in used_phrases]
        if not remaining_phrases:
            return improved_groups
        
        self.logger.info(f"🔧 [FALLBACK] Przetwarzam {len(remaining_phrases)} fraz deterministycznie")
        
        # Uniwersalne wzorce
        price_patterns = ["cena", "koszt", "ile kosztuje", "tani", "drogi", "promocja", "rabat"]
        question_patterns = ["jak", "czy", "co", "gdzie", "kiedy", "dlaczego", "?"]
        shop_patterns = ["allegro", "amazon", "sklep", "shop", "store", "zakup"]
        
        price_group = []
        questions_group = []
        shops_group = []
        unassigned_phrases = []
        
        for phrase in remaining_phrases:
            phrase_lower = phrase.lower()
            assigned = False
            
            if any(pattern in phrase_lower for pattern in price_patterns):
                price_group.append(phrase)
                assigned = True
            elif any(pattern in phrase_lower for pattern in question_patterns):
                questions_group.append(phrase)
                assigned = True
            elif any(pattern in phrase_lower for pattern in shop_patterns):
                shops_group.append(phrase)
                assigned = True
            
            if not assigned:
                unassigned_phrases.append(phrase)
        
        # Dodaj grupy (tylko niepuste)
        if price_group:
            improved_groups["Ceny i koszty"] = price_group
        if questions_group:
            improved_groups["Pytania i porady"] = questions_group
        if shops_group:
            improved_groups["Sklepy i zakupy"] = shops_group
        
        # Ostateczne przypisanie
        if unassigned_phrases:
            if len(unassigned_phrases) <= 3 and improved_groups:
                largest_group = max(improved_groups.items(), key=lambda x: len(x[1]))
                improved_groups[largest_group[0]].extend(unassigned_phrases)
            else:
                improved_groups[f"Grupa główna - {seed_keyword}"] = unassigned_phrases
        
        return improved_groups

    def _detect_brands_in_phrases(self, phrases: List[str], seed_keyword: str) -> List[str]:
        """Uniwersalne wykrywanie marek w frazach"""
        word_counts = {}
        for phrase in phrases:
            words = phrase.split()
            for word in words:
                word_clean = word.strip('.,!?()[]{}').lower()
                if (len(word_clean) > 2 and 
                    word_clean not in seed_keyword.lower().split() and
                    word_clean not in ['jak', 'czy', 'ile', 'co', 'gdzie', 'do', 'na', 'w', 'z', 'i', 'a']):
                    word_counts[word_clean] = word_counts.get(word_clean, 0) + 1
        
        potential_brands = []
        for word, count in word_counts.items():
            if 2 <= count <= len(phrases) // 3:
                potential_brands.append(word.title())
        
        return potential_brands[:5]

    def _detect_types_in_phrases(self, phrases: List[str], seed_keyword: str) -> List[str]:
        """Uniwersalne wykrywanie typów/kategorii"""
        return []  # Uproszczona wersja na szybko

    def _convert_groups_to_legacy_format(self, phrases: List[str], groups: Dict[str, List[str]], embeddings: np.ndarray) -> Tuple[np.ndarray, Dict]:
        """Konwertuje wyniki do formatu legacy"""
        phrase_to_cluster = {}
        cluster_id = 0
        
        for group_name, group_phrases in groups.items():
            if group_name == "outliers":
                for phrase in group_phrases:
                    phrase_to_cluster[phrase] = -1
            else:
                for phrase in group_phrases:
                    phrase_to_cluster[phrase] = cluster_id
                cluster_id += 1
        
        cluster_labels = np.array([phrase_to_cluster.get(phrase, -1) for phrase in phrases])
        
        num_clusters = cluster_id
        noise_points = np.sum(cluster_labels == -1)
        noise_ratio = noise_points / len(phrases) if len(phrases) > 0 else 0
        
        # Nazwy klastrów
        cluster_names = {}
        cluster_id = 0
        for group_name, group_phrases in groups.items():
            if group_name != "outliers":
                cluster_names[cluster_id] = group_name
                cluster_id += 1
        
        quality_metrics = {
            "num_clusters": num_clusters,
            "noise_points": int(noise_points),
            "noise_ratio": float(noise_ratio),
            "silhouette_score": 0.0,
            "clustering_method": "universal_ai_clustering",
            "quality_goal_achieved": noise_ratio <= 0.25,
            "target_groups_achieved": 6 <= num_clusters <= 12,
            "cluster_names": cluster_names
        }
        
        return cluster_labels, quality_metrics

    async def _emergency_deterministic_clustering(self, phrases: List[str], embeddings: np.ndarray, seed_keyword: str) -> Tuple[np.ndarray, Dict]:
        """Awaryjne deterministyczne klastrowanie"""
        self.logger.warning(f"🆘 [EMERGENCY] Awaryjne klastrowanie dla {len(phrases)} fraz")
        
        emergency_groups = {
            f"Grupa główna - {seed_keyword}": [],
            "Ceny i koszty": [],
            "Pytania i informacje": [],
            "Pozostałe": []
        }
        
        for phrase in phrases:
            phrase_lower = phrase.lower()
            
            if any(word in phrase_lower for word in ["cena", "koszt", "ile", "tani", "drogi"]):
                emergency_groups["Ceny i koszty"].append(phrase)
            elif any(word in phrase_lower for word in ["jak", "czy", "co", "gdzie", "?"]):
                emergency_groups["Pytania i informacje"].append(phrase)
            elif any(word in seed_keyword.lower().split() for word in phrase_lower.split()):
                emergency_groups[f"Grupa główna - {seed_keyword}"].append(phrase)
            else:
                emergency_groups["Pozostałe"].append(phrase)
        
        # Usuń puste grupy
        emergency_groups = {name: phrases for name, phrases in emergency_groups.items() if phrases}
        
        return self._convert_groups_to_legacy_format(phrases, emergency_groups, embeddings) 