"""
Exemples de requêtes API pour Wakif AI
Copie-colle ces exemples dans ton terminal ou Postman
"""

# ====================================
# 1. VÉRIFIER LE STATUT DU SERVEUR
# ====================================

# GET - Vérifier que le serveur est en ligne
curl -X GET "http://localhost:8000/"

# Réponse attendue:
# {
#   "status": "online ✅",
#   "agent": "Wakif AI 🇲🇦",
#   "version": "2.0.0",
#   ...
# }


# ====================================
# 2. CHAT SIMPLE - DARIJA
# ====================================

# Question simple en Darija
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "السلام عليكم",
    "user_id": "user_123"
  }'

# Exemple avec conversions:
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "شنو معنا الحب؟",
    "user_id": "user_123"
  }'

# Question qui nécessite une recherche:
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "شنو أخبار الطقس دابا؟",
    "user_id": "user_123"
  }'


# ====================================
# 3. CHAT AVEC HISTORIQUE
# ====================================

# Conversation avec contexte antérieur
curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "و كاينة احتمالية دلماطار نهار غدا؟",
    "user_id": "user_123",
    "history": [
      {
        "role": "user",
        "content": "شنو أخبار الطقس دابا؟"
      },
      {
        "role": "assistant",
        "content": "الطقس دابا غادي يكون جميل الحمدلله..."
      }
    ]
  }'


# ====================================
# 4. CONVERSATION EN FRANÇAIS
# ====================================

curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "Quelles sont les dernières actualités?",
    "user_id": "user_123"
  }'


# ====================================
# 5. CONVERSATION EN ANGLAIS
# ====================================

curl -X POST "http://localhost:8000/chat" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "What is machine learning?",
    "user_id": "user_123"
  }'


# ====================================
# 6. STATISTIQUES API
# ====================================

# Vérifier l'utilisation de l'API Brave Search
curl -X GET "http://localhost:8000/stats"

# Réponse:
# {
#   "total_searches": 5,
#   "searches_remaining": 995,
#   "usage_percentage": 0.5,
#   "recent_searches": [...],
#   "cache_stats": {...},
#   "warning": "✅ Utilisation normale"
# }


# ====================================
# 7. HISTORIQUE UTILISATEUR
# ====================================

# Récupérer l'historique d'un utilisateur
curl -X GET "http://localhost:8000/memory/user/user_123?limit=10"

# Réponse:
# {
#   "user_id": "user_123",
#   "history": [
#     {
#       "timestamp": "2024-01-15T10:30:45.123456",
#       "message": "السلام عليكم",
#       "response": "و عليكم السلام ورحمة الله...",
#       "used_search": false
#     }
#   ]
# }


# ====================================
# 8. STATISTIQUES DE MÉMOIRE
# ====================================

# Statistiques globales
curl -X GET "http://localhost:8000/memory/stats"

# Réponse:
# {
#   "total_conversations": 45,
#   "unique_users": 12,
#   "searches_used": 8,
#   "memory_file_size_kb": 234.5
# }


# ====================================
# 9. SANTÉ DU SYSTÈME
# ====================================

curl -X GET "http://localhost:8000/health"


# ====================================
# 10. EXEMPLES AVEC PYTHON
# ====================================

"""
import requests

BASE_URL = "http://localhost:8000"

# Simple chat
def chat(message, user_id="default"):
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": message,
            "user_id": user_id
        }
    )
    return response.json()

# Avec historique
def chat_with_history(message, history, user_id="default"):
    response = requests.post(
        f"{BASE_URL}/chat",
        json={
            "message": message,
            "history": history,
            "user_id": user_id
        }
    )
    return response.json()

# Exemple d'utilisation
result = chat("السلام عليكم", user_id="user_123")
print(result["response"])

# Vérifier les stats
stats = requests.get(f"{BASE_URL}/stats").json()
print(f"Recherches utilisées: {stats['total_searches']}/1000")
"""


# ====================================
# 11. STREAMING RESPONSE (optionnel)
# ====================================

# Pour les réponses longues
curl -X POST "http://localhost:8000/chat-stream" \
  -H "Content-Type: application/json" \
  -d '{
    "message": "شرح لي الذكاء الاصطناعي بالتفصيل",
    "user_id": "user_123"
  }'


# ====================================
# NOTES
# ====================================

"""
✅ Tips pour utiliser l'API:

1. Toujours inclure user_id pour le tracking
2. L'historique aide le model à comprendre le contexte
3. Les requêtes "nécessitant recherche" utilisent l'API Brave
4. Le cache économise les appels API (TTL: 2h)
5. Vérifier /stats régulièrement pour ne pas dépasser 1000

🔐 Sécurité:
- Ne partage pas ta clé Brave API
- Utilise des variables d'environnement (.env)
- Protège l'endpoint /memory pour les données sensibles

⚡ Performance:
- Les réponses mises en cache sont instantanées
- Les recherches prennent 2-5 secondes
- Cache local (SQLite) pour les conversations
"""
