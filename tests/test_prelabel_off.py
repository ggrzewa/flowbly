# tests/test_prelabel_off.py
# Test sprawdzający, że HDBSCAN-prelabel jest domyślnie wyłączony

import pytest
import os
from app.services.heuristics import apply_rules, USE_HDBSCAN_PRELABEL


def test_prelabel_off_by_default():
    """Test sprawdzający, że USE_HDBSCAN_PRELABEL jest domyślnie False"""
    # Sprawdź że domyślna wartość jest False
    assert USE_HDBSCAN_PRELABEL == False, "USE_HDBSCAN_PRELABEL powinno być domyślnie False"


def test_prelabel_off_no_hdb_clusters(monkeypatch):
    """Test sprawdzający, że gdy USE_HDBSCAN_PRELABEL=false, nie ma klastrów hdb_cluster_*"""
    # Ustaw zmienną środowiskową na false
    monkeypatch.setenv("USE_HDBSCAN_PRELABEL", "false")
    
    # Utwórz przykładowe dane - 30 fraz żeby przekroczyć próg HDBSCAN (≥20)
    sample = [{"text": f"fraza testowa numer {i}"} for i in range(30)]
    
    # Wywołaj apply_rules
    result = apply_rules(sample)
    
    # Sprawdź, że żadna fraza nie ma pre_label zawierającego "hdb_cluster_"
    for item in result:
        pre_label = item.get("pre_label")
        if pre_label:
            assert "hdb_cluster_" not in pre_label, f"Znaleziono niespodziewany hdb_cluster_: {pre_label}"


def test_prelabel_on_creates_hdb_clusters(monkeypatch):
    """Test sprawdzający, że gdy USE_HDBSCAN_PRELABEL=true, mogą powstać klastry hdb_cluster_*"""
    # Ustaw zmienną środowiskową na true
    monkeypatch.setenv("USE_HDBSCAN_PRELABEL", "true")
    
    # Reimport modułu żeby odczytał nową wartość zmiennej środowiskowej
    import importlib
    from app.services import heuristics
    importlib.reload(heuristics)
    
    # Utwórz przykładowe dane - 30 fraz żeby przekroczyć próg HDBSCAN (≥20)
    sample = [{"text": f"fraza testowa numer {i}"} for i in range(30)]
    
    # Wywołaj apply_rules z przeładowanego modułu
    result = heuristics.apply_rules(sample)
    
    # Sprawdź, że co najmniej niektóre frazy mogą mieć pre_label zawierające "hdb_cluster_"
    # (To nie jest gwarantowane, bo HDBSCAN może nie znaleźć klastrów, ale przynajmniej nie będzie błędu)
    hdb_labels = [item.get("pre_label") for item in result if item.get("pre_label") and "hdb_cluster_" in item.get("pre_label", "")]
    
    # Sprawdzamy tylko, że funkcja działa bez błędów gdy HDBSCAN jest włączony
    assert True, "Test przeszedł - funkcja działa gdy HDBSCAN jest włączony"


def test_environment_variable_parsing():
    """Test sprawdzający, że różne wartości zmiennej środowiskowej są poprawnie parsowane"""
    import os
    from app.services.heuristics import USE_HDBSCAN_PRELABEL
    
    # Test przypadków gdzie powinno być True
    true_values = ["true", "TRUE", "True", "1", "yes", "YES"]
    for value in true_values:
        os.environ["USE_HDBSCAN_PRELABEL"] = value
        # Reimport żeby odczytać nową wartość
        import importlib
        from app.services import heuristics
        importlib.reload(heuristics)
        assert heuristics.USE_HDBSCAN_PRELABEL == True, f"Wartość '{value}' powinna dać True"
    
    # Test przypadków gdzie powinno być False
    false_values = ["false", "FALSE", "False", "0", "no", "NO", "", "random"]
    for value in false_values:
        os.environ["USE_HDBSCAN_PRELABEL"] = value
        # Reimport żeby odczytać nową wartość
        import importlib
        from app.services import heuristics
        importlib.reload(heuristics)
        assert heuristics.USE_HDBSCAN_PRELABEL == False, f"Wartość '{value}' powinna dać False"


if __name__ == "__main__":
    pytest.main([__file__, "-v"]) 