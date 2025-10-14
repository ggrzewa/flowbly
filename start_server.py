#!/usr/bin/env python3
"""
Skrypt startowy dla serwera FlowBly
Uruchamia uvicorn z odpowiednimi parametrami logowania
"""

import uvicorn
import logging
import os

if __name__ == "__main__":
    # Konfiguracja logowania uvicorn
    log_config = {
        "version": 1,
        "disable_existing_loggers": False,
        "formatters": {
            "default": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
            "access": {
                "format": "%(asctime)s | %(levelname)s | %(name)s | %(message)s",
                "datefmt": "%Y-%m-%d %H:%M:%S"
            },
        },
        "handlers": {
            "default": {
                "formatter": "default",
                "class": "logging.StreamHandler",
                "stream": "ext://sys.stdout",
            },
        },
        "root": {
            "level": "INFO",
            "handlers": ["default"],
        },
        "loggers": {
            "uvicorn": {"level": "INFO"},
            "uvicorn.access": {"level": "WARNING"},
            "uvicorn.error": {"level": "INFO"},
        },
    }
    
    # Uruchom serwer
    uvicorn.run(
        "app.main:app",
        host="0.0.0.0",
        port=8000,
        log_config=log_config,
        access_log=False,  # Wyłącz access logi
        use_colors=False,  # Wyłącz kolorowe logi
    ) 