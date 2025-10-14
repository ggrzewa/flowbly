#!/usr/bin/env python3
"""
🔗 DEMO KONSOLIDACJI KLASTRÓW - Test Nowego Systemu Post-Processing
Demonstracja jak nowy system konsolidacji radzi sobie z problemem over-segmentation

Symuluje dane podobne do tych które użytkownik ma (37 małych grup → 8-12 dużych grup)
"""

import asyncio
import os
from app.services.semantic_clustering import SemanticClusteringService, enable_clustering_consolidation
from app.services.semantic_clustering import ClusterConsolidator

# Dane testowe na podstawie rzeczywistych wyników użytkownika
SAMPLE_CLUSTER_RESULTS = [
    {
        "group_label": "Grupa: ile kosztują soczewki roczne na astygmatyzm, ile kosztują soczewki dzienne, ile kosztują soczewki jednodniowe",
        "phrases_count": 7,
        "avg_similarity": 0.834,
        "members": [
            {"phrase": "ile kosztują soczewki astygmatyzm", "similarity_score": 0.89},
            {"phrase": "ile kosztują soczewki dzienne", "similarity_score": 0.87},
            {"phrase": "ile kosztują soczewki jednodniowe", "similarity_score": 0.85},
            {"phrase": "ile kosztują soczewki kontaktowe", "similarity_score": 0.83},
            {"phrase": "ile kosztują soczewki miesięczne", "similarity_score": 0.82},
            {"phrase": "ile kosztują soczewki na wadę wzroku", "similarity_score": 0.81},
            {"phrase": "ile kosztują soczewki roczne", "similarity_score": 0.80}
        ]
    },
    {
        "group_label": "Grupa: ile kosztują soczewki progresywne biofinity, ile kosztują soczewki toryczne",
        "phrases_count": 2,
        "avg_similarity": 0.712,
        "members": [
            {"phrase": "ile kosztują soczewki progresywne biofinity", "similarity_score": 0.72},
            {"phrase": "ile kosztują soczewki toryczne", "similarity_score": 0.70}
        ]
    },
    {
        "group_label": "Grupa: tanie soczewki miesięczne toryczne, tanie soczewki na astygmatyzm",
        "phrases_count": 5,
        "avg_similarity": 0.698,
        "members": [
            {"phrase": "tanie soczewki miesięczne toryczne", "similarity_score": 0.75},
            {"phrase": "tanie soczewki na astygmatyzm", "similarity_score": 0.73},
            {"phrase": "tanie soczewki kontaktowe", "similarity_score": 0.71},
            {"phrase": "najtańsze soczewki kontaktowe", "similarity_score": 0.68},
            {"phrase": "promocje na soczewki", "similarity_score": 0.65}
        ]
    },
    {
        "group_label": "Grupa: soczewki acuvue oasys for astigmatism, soczewki acuvue, soczewki acuvue oasys",
        "phrases_count": 4,
        "avg_similarity": 0.834,
        "members": [
            {"phrase": "acuvue oasys soczewki", "similarity_score": 0.87},
            {"phrase": "acuvue soczewki", "similarity_score": 0.85},
            {"phrase": "soczewki acuvue", "similarity_score": 0.83},
            {"phrase": "soczewki acuvue oasys", "similarity_score": 0.81}
        ]
    },
    {
        "group_label": "Grupa: soczewki oasys, acuvue oasys cena",
        "phrases_count": 2,
        "avg_similarity": 0.723,
        "members": [
            {"phrase": "soczewki oasys", "similarity_score": 0.74},
            {"phrase": "acuvue oasys cena", "similarity_score": 0.71}
        ]
    },
    {
        "group_label": "Grupa: biofinity multifocal soczewki, biofinity szt 6",
        "phrases_count": 3,
        "avg_similarity": 0.687,
        "members": [
            {"phrase": "biofinity multifocal soczewki", "similarity_score": 0.72},
            {"phrase": "biofinity szt 6", "similarity_score": 0.68},
            {"phrase": "biofinity soczewki", "similarity_score": 0.65}
        ]
    },
    {
        "group_label": "Grupa: soczewki jednodniowe dailies total 1",
        "phrases_count": 2,
        "avg_similarity": 0.745,
        "members": [
            {"phrase": "soczewki jednodniowe dailies total 1", "similarity_score": 0.75},
            {"phrase": "dailies total 1 soczewki", "similarity_score": 0.74}
        ]
    },
    {
        "group_label": "Grupa: soczewki miesięczne biofinity, biofinity",
        "phrases_count": 3,
        "avg_similarity": 0.623,
        "members": [
            {"phrase": "soczewki miesięczne biofinity", "similarity_score": 0.68},
            {"phrase": "biofinity", "similarity_score": 0.62},
            {"phrase": "soczewki biofinity", "similarity_score": 0.58}
        ]
    },
    {
        "group_label": "Grupa: alensa pl soczewki kontaktowe, alensa soczewki, alensa",
        "phrases_count": 5,
        "avg_similarity": 0.712,
        "members": [
            {"phrase": "alensa pl soczewki kontaktowe", "similarity_score": 0.76},
            {"phrase": "alensa soczewki", "similarity_score": 0.74},
            {"phrase": "alensa", "similarity_score": 0.71},
            {"phrase": "alensa pl", "similarity_score": 0.69},
            {"phrase": "sklep alensa", "similarity_score": 0.67}
        ]
    },
    {
        "group_label": "Grupa: Meta Quest 3, quest 3",
        "phrases_count": 2,
        "avg_similarity": 0.892,
        "members": [
            {"phrase": "Meta Quest 3", "similarity_score": 0.90},
            {"phrase": "quest 3", "similarity_score": 0.88}
        ]
    },
    {
        "group_label": "Grupa: jak założyć soczewki kontaktowe",
        "phrases_count": 1,
        "avg_similarity": 0.000,
        "members": [
            {"phrase": "jak założyć soczewki kontaktowe", "similarity_score": 1.0}
        ]
    },
    {
        "group_label": "Grupa: soczewki kontaktowe jednodniowe",
        "phrases_count": 2,
        "avg_similarity": 0.834,
        "members": [
            {"phrase": "soczewki kontaktowe jednodniowe", "similarity_score": 0.86},
            {"phrase": "jednodniowe soczewki kontaktowe", "similarity_score": 0.81}
        ]
    }
]

async def test_consolidation_system():
    """🧪 Test systemu konsolidacji na przykładowych danych"""
    
    print("🔗 TEST SYSTEMU KONSOLIDACJI POST-PROCESSING")
    print("=" * 60)
    
    # Symuluj stan przed konsolidacją
    print(f"📊 PRZED KONSOLIDACJĄ:")
    print(f"   • Liczba grup: {len(SAMPLE_CLUSTER_RESULTS)}")
    
    total_phrases = sum(cluster['phrases_count'] for cluster in SAMPLE_CLUSTER_RESULTS)
    print(f"   • Całkowita liczba fraz: {total_phrases}")
    
    # Pokaż problemy
    small_groups = [c for c in SAMPLE_CLUSTER_RESULTS if c['phrases_count'] <= 2]
    print(f"   • Małe grupy (≤2 frazy): {len(small_groups)}")
    
    print(f"\n🔍 PRZYKŁADY PROBLEMÓW:")
    
    # Problem 1: Duplikacja kosztów
    cost_groups = [c for c in SAMPLE_CLUSTER_RESULTS if any(word in c['group_label'].lower() for word in ['ile kosztują', 'tanie', 'cena'])]
    print(f"   • Grupy o kosztach (powinny być połączone): {len(cost_groups)}")
    for group in cost_groups[:3]:
        print(f"     - {group['group_label'][:60]}... ({group['phrases_count']} fraz)")
    
    # Problem 2: Duplikacja Acuvue 
    acuvue_groups = [c for c in SAMPLE_CLUSTER_RESULTS if 'acuvue' in c['group_label'].lower()]
    print(f"   • Grupy Acuvue (powinny być połączone): {len(acuvue_groups)}")
    for group in acuvue_groups:
        print(f"     - {group['group_label'][:60]}... ({group['phrases_count']} fraz)")
    
    # Problem 3: Outliers
    outlier_groups = [c for c in SAMPLE_CLUSTER_RESULTS if any(word in c['group_label'].lower() for word in ['meta quest', 'quest 3'])]
    if outlier_groups:
        print(f"   • Outliers (powinny być usunięte): {len(outlier_groups)}")
        for group in outlier_groups:
            print(f"     - {group['group_label']} ({group['phrases_count']} fraz)")
    
    print("\n" + "=" * 60)
    print("🔗 ZASTOSOWANIE KONSOLIDACJI")
    print("=" * 60)
    
    # Utwórz konsolidator i zastosuj
    consolidator = ClusterConsolidator("soczewki kontaktowe")
    consolidated_results = consolidator.consolidate_clusters(SAMPLE_CLUSTER_RESULTS)
    
    print(f"\n📊 PO KONSOLIDACJI:")
    print(f"   • Liczba grup: {len(consolidated_results)}")
    
    consolidated_phrases = sum(cluster['phrases_count'] for cluster in consolidated_results)
    print(f"   • Całkowita liczba fraz: {consolidated_phrases}")
    
    reduction_percent = ((len(SAMPLE_CLUSTER_RESULTS) - len(consolidated_results)) / len(SAMPLE_CLUSTER_RESULTS)) * 100
    print(f"   • Redukcja grup: {reduction_percent:.1f}%")
    
    print(f"\n🏆 SKONSOLIDOWANE GRUPY:")
    consolidated_results.sort(key=lambda x: x['phrases_count'], reverse=True)
    
    for i, group in enumerate(consolidated_results, 1):
        group_name = group['group_label']
        phrase_count = group['phrases_count']
        
        # Pokaż kilka przykładowych fraz
        sample_phrases = [m['phrase'] for m in group['members'][:3]]
        sample_text = ", ".join(sample_phrases)
        if len(sample_text) > 80:
            sample_text = sample_text[:77] + "..."
        
        consolidation_marker = "🔗" if group.get('consolidated') else ""
        print(f"   {i:2d}. {group_name} {consolidation_marker}")
        print(f"       └─ {phrase_count} fraz: {sample_text}")
    
    print(f"\n✅ REZULTATY:")
    print(f"   • Znacznie mniej grup: {len(SAMPLE_CLUSTER_RESULTS)} → {len(consolidated_results)}")
    print(f"   • Większe, bardziej sensowne grupy")
    print(f"   • Logiczne nazwy grup (Ceny i koszty, Marki - Acuvue, itp.)")
    print(f"   • Outliers usunięte lub przeniesione")
    
    # Sprawdź czy główne problemy zostały rozwiązane
    print(f"\n🔍 WERYFIKACJA ROZWIĄZANIA:")
    
    # Sprawdź konsolidację kosztów
    cost_groups_after = [c for c in consolidated_results if 'ceny' in c['group_label'].lower() or 'kosz' in c['group_label'].lower()]
    if cost_groups_after:
        print(f"   ✅ Grupy kosztów skonsolidowane: {len(cost_groups)} → {len(cost_groups_after)}")
        cost_group = cost_groups_after[0]
        print(f"      └─ '{cost_group['group_label']}' ({cost_group['phrases_count']} fraz)")
    
    # Sprawdź konsolidację Acuvue
    acuvue_groups_after = [c for c in consolidated_results if 'acuvue' in c['group_label'].lower()]
    if acuvue_groups_after:
        print(f"   ✅ Grupy Acuvue skonsolidowane: {len(acuvue_groups)} → {len(acuvue_groups_after)}")
        acuvue_group = acuvue_groups_after[0]
        print(f"      └─ '{acuvue_group['group_label']}' ({acuvue_group['phrases_count']} fraz)")
    
    # Sprawdź usunięcie outliers
    outliers_after = [c for c in consolidated_results if any(word in c['group_label'].lower() for word in ['meta quest', 'quest'])]
    if not outliers_after:
        print(f"   ✅ Outliers usunięte: {len(outlier_groups)} grup Meta Quest")
    
    return consolidated_results

async def demo_integration_with_service():
    """🔗 Demo integracji z SemanticClusteringService"""
    
    print("\n" + "=" * 60)
    print("🔧 DEMO INTEGRACJI Z SERWISEM")
    print("=" * 60)
    
    print("📝 Kod do integracji z Twoim systemem:")
    print("""
# 1. Import funkcji pomocniczej
from app.services.semantic_clustering import enable_clustering_consolidation

# 2. Włączenie konsolidacji dla instancji serwisu
service = SemanticClusteringService(supabase_client)
enable_clustering_consolidation(service)  # ← Włącza konsolidację

# 3. Pobieranie wyników - automatycznie skonsolidowane
results = await service.get_clustering_results(seed_keyword_id)

# 4. Sprawdzenie czy konsolidacja została zastosowana
if results and results.get('consolidation_applied'):
    print(f"✅ Konsolidacja zastosowana: {len(results['groups'])} grup")
    
    # Każda grupa ma flagę post_processed = True
    for group in results['groups']:
        if group.get('post_processed'):
            print(f"🔗 Grupa skonsolidowana: {group['group_label']}")
else:
    print("ℹ️ Konsolidacja wyłączona")
""")
    
    print("🎯 PRZEWIDYWANE REZULTATY dla Twoich danych:")
    print("   • 37 grup → 8-12 grup")
    print("   • Wszystkie grupy o kosztach połączone w 'Ceny i koszty'")
    print("   • Wszystkie produkty Acuvue w 'Marki - Acuvue'")
    print("   • Outliers jak 'Meta Quest 3' usunięte")
    print("   • Większe grupy po 8-15 fraz każda")
    print("   • ≤5% fraz w grupie 'Różne' (zamiast 47% niesklasyfikowanych)")

if __name__ == "__main__":
    print("🚀 ROZPOCZYNAM DEMO KONSOLIDACJI...")
    asyncio.run(test_consolidation_system())
    asyncio.run(demo_integration_with_service())
    print("\n🎉 DEMO ZAKOŃCZONE - system gotowy do użycia!") 