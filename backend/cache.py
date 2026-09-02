"""
Système de cache pour éviter les recherches répétées
Économise les appels API Brave Search
"""

from datetime import datetime, timedelta
import json


class SearchCache:
    def __init__(self, ttl_minutes=60):
        """
        Cache pour les résultats de recherche
        
        Args:
            ttl_minutes: Durée de vie du cache en minutes
        """
        self.cache = {}
        self.ttl = timedelta(minutes=ttl_minutes)
    
    def get(self, query: str):
        """Récupérer un résultat du cache"""
        if query in self.cache:
            entry = self.cache[query]
            if datetime.now() - entry["timestamp"] < self.ttl:
                return entry["results"]
            else:
                # Cache expiré
                del self.cache[query]
        return None
    
    def set(self, query: str, results: list):
        """Stocker un résultat dans le cache"""
        self.cache[query] = {
            "results": results,
            "timestamp": datetime.now()
        }
    
    def clear(self):
        """Vider le cache"""
        self.cache.clear()
    
    def get_stats(self):
        """Statistiques du cache"""
        return {
            "cached_queries": len(self.cache),
            "entries": [
                {
                    "query": query,
                    "age_minutes": (datetime.now() - entry["timestamp"]).total_seconds() / 60,
                    "ttl_minutes": self.ttl.total_seconds() / 60
                }
                for query, entry in self.cache.items()
            ]
        }


# Instance globale du cache
search_cache = SearchCache(ttl_minutes=120)
