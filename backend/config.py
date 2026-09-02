"""
Fichier de configuration pour Wakif AI
Stockage des variables d'environnement
"""

import os
from dotenv import load_dotenv

# Charger les variables d'environnement
load_dotenv()

# Configuration Brave Search API
BRAVE_API_KEY = os.getenv(
    "BRAVE_API_KEY",
    "BSAcFTixd0I6LMOEpASq6uLALTvt2H9"  # Clé par défaut
)

# Configuration du cache
CACHE_TTL_MINUTES = int(os.getenv("CACHE_TTL_MINUTES", "120"))

# Configuration du server
HOST = os.getenv("HOST", "0.0.0.0")
PORT = int(os.getenv("PORT", "8000"))
DEBUG = os.getenv("DEBUG", "False") == "True"

# Configuration Ollama
OLLAMA_HOST = os.getenv("OLLAMA_HOST", "http://localhost:11434")
OLLAMA_MODEL = os.getenv("OLLAMA_MODEL", "atlas-9b")

# Configuration du routing intelligent
SEARCH_URGENCY_THRESHOLD = int(os.getenv("SEARCH_URGENCY_THRESHOLD", "1"))

# Configuration de logging
LOG_LEVEL = os.getenv("LOG_LEVEL", "INFO")

# Limites API
MAX_SEARCHES_LIMIT = 1000
WARNING_THRESHOLD = 800  # Avertir à 80%

print("""
🇲🇦 Wakif AI - Configuration Chargée
=====================================
✅ Brave Search API: Configurée
✅ Cache: Activé (TTL: {} minutes)
✅ Ollama Model: {}
✅ Limite Recherches: {}/{}
""".format(
    CACHE_TTL_MINUTES,
    OLLAMA_MODEL,
    "?" ,
    MAX_SEARCHES_LIMIT
))
