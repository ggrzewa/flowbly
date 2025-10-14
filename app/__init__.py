"""Pakiet aplikacji.

Inicjuje globalną konfigurację logowania **zaraz po zaimportowaniu pakietu `app`**, więc działa zarówno przy uruchamianiu skryptów, jak
i w procesach tworzonych przez `uvicorn --reload`.
"""
import logging
import os
import sys
from datetime import datetime

# --------------------------------------------------
# GLOBALNE LOGOWANIE
# --------------------------------------------------
# WYMUSZONE NA INFO - bez czytania zmiennych środowiskowych
# Aby włączyć DEBUG, zmień poniższą linię na: log_level = logging.DEBUG
# --------------------------------------------------
log_level = logging.INFO

# Konfiguracja formattera
formatter = logging.Formatter(
    "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
    datefmt="%Y-%m-%d %H:%M:%S"
)

# Konfiguracja handlera
handler = logging.StreamHandler()
handler.setFormatter(formatter)

# Konfiguracja root loggera
root_logger = logging.getLogger()
root_logger.setLevel(log_level)

# Dodaj handler tylko jeśli jeszcze nie istnieje
if not root_logger.handlers:
    root_logger.addHandler(handler)

# WYCISZ BIBLIOTEKI HTTP - one generują za dużo śmieci
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("httpcore").setLevel(logging.WARNING)
logging.getLogger("hpack").setLevel(logging.WARNING)
logging.getLogger("h2").setLevel(logging.WARNING)
logging.getLogger("h11").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("requests").setLevel(logging.WARNING)

# WYCISZ MODUŁY APLIKACJI KTÓRE GENERUJĄ ZA DUŻO DEBUG LOGÓW
logging.getLogger("serp_parser_complete").setLevel(logging.INFO)
logging.getLogger("autocomplete_parser_complete").setLevel(logging.INFO)
logging.getLogger("flowbly_parser_v2").setLevel(logging.INFO)

# Aplikacyjne loggery na właściwym poziomie
logging.getLogger("app").setLevel(log_level)
logging.getLogger("main").setLevel(log_level)
logging.getLogger("seo_orchestrator").setLevel(log_level)
logging.getLogger("semantic_clustering").setLevel(log_level)

print(f"2025-07-09 {datetime.now().strftime('%H:%M:%S')} | INFO | app | Globalne logowanie zainicjalizowane. Poziom: INFO") 