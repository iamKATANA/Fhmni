import os
import logging
import requests
from datetime import datetime

logger = logging.getLogger(__name__)

BRAVE_API_KEY = os.getenv("BRAVE_API_KEY", "BSAcFTixd0I6LMOEpASq6uLALTvt2H9")
BRAVE_API_URL = "https://api.search.brave.com/res/v1/web/search"

search_log = []


def web_search(query: str, max_results: int = 3, freshness: str | None = None):
    """Recherche sur Brave Search avec extraction du nœud 'web'
    
    freshness: filtre de fraîcheur Brave - "pd" (24h), "pw" (semaine),
               "pm" (mois), "py" (année), ou None (pas de filtre).
    """
    
    logger.debug(f"[SEARCH] Starting search for query: '{query}' (freshness={freshness})")
    
    try:
        headers = {
            "Accept": "application/json",
            "X-Subscription-Token": BRAVE_API_KEY
        }
        
        params = {
            "q": query,
            "count": max_results,
        }
        if freshness:
            params["freshness"] = freshness
        
        response = requests.get(BRAVE_API_URL, headers=headers, params=params, timeout=10)
        logger.debug(f"[SEARCH] API response status: {response.status_code}")
        response.raise_for_status()
        
        data = response.json()
        logger.debug(f"[SEARCH] API response keys: {data.keys()}")
        
        search_log.append({
            "query": query,
            "timestamp": datetime.now().isoformat(),
            "results_count": 1
        })
        
        results = []
        
        # Extraction correcte depuis le nœud 'web' de la réponse Brave
        if "web" in data and "results" in data["web"]:
            web_results = data["web"]["results"][:max_results]
            logger.debug(f"[SEARCH] Found {len(web_results)} results in web node")
            
            for result in web_results:
                results.append({
                    "title": result.get("title", ""),
                    "snippet": result.get("description", ""),
                    "url": result.get("url", ""),
                    "age": result.get("age", "")
                })
        else:
            logger.warning(f"[SEARCH] No web results found in payload. Keys: {data.keys()}")
        
        logger.debug(f"[SEARCH] Returning {len(results)} results")
        return results
    
    except Exception as e:
        logger.error(f"[SEARCH] Error: {e}")
        return []


def get_search_stats():
    """Retourne les statistiques d'utilisation"""
    return {
        "total_searches": len(search_log),
        "searches_remaining": 1000 - len(search_log),
        "usage_percentage": round((len(search_log) / 1000) * 100, 2),
    }