#!/usr/bin/env python3
# test_logging.py - test logowania w serwisach

import logging
import sys
import os

# Dodaj ścieżkę do app
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'app'))

# Konfiguracja logowania
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s | %(levelname)s | %(name)s | %(message)s',
    handlers=[logging.StreamHandler()],
    force=True
)

# Ustaw poziom logowania dla głównych modułów
logging.getLogger("app").setLevel(logging.INFO)
logging.getLogger("app.services").setLevel(logging.INFO)
logging.getLogger("app.api").setLevel(logging.INFO)

print("🔍 Testuję logowanie w serwisach...")

# Test 1: Logger w main
logger = logging.getLogger("main")
logger.info("✅ Logger main działa!")

# Test 2: Logger w services
try:
    from app.services.heuristics import logger as heuristics_logger
    heuristics_logger.info("✅ Logger heuristics działa!")
except ImportError as e:
    print(f"❌ Błąd importu heuristics: {e}")

try:
    from app.services.semantic_assign import logger as assign_logger
    assign_logger.info("✅ Logger semantic_assign działa!")
except ImportError as e:
    print(f"❌ Błąd importu semantic_assign: {e}")

# Test 3: Logger w api
try:
    from app.api.full_analysis import logger as orchestrator_logger
    orchestrator_logger.info("✅ Logger orchestrator działa!")
except ImportError as e:
    print(f"❌ Błąd importu orchestrator: {e}")

print("🎯 Test logowania zakończony!") 