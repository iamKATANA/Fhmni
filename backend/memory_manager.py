"""
Système de gestion de la mémoire pour Wakif AI
Stocke l'historique des conversations
"""

import json
import os
from datetime import datetime
from typing import List, Dict

MEMORY_FILE = "wakif_memory.json"


class ConversationMemory:
    def __init__(self, memory_file=MEMORY_FILE):
        self.memory_file = memory_file
        self.conversations = self._load_memory()
    
    def _load_memory(self) -> List[Dict]:
        """Charger la mémoire depuis le disque"""
        if os.path.exists(self.memory_file):
            try:
                with open(self.memory_file, 'r', encoding='utf-8') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def _save_memory(self):
        """Sauvegarder la mémoire sur le disque"""
        with open(self.memory_file, 'w', encoding='utf-8') as f:
            json.dump(self.conversations, f, ensure_ascii=False, indent=2)
    
    def add_conversation(self, user_id: str, message: str, response: str, used_search: bool = False):
        """Ajouter une conversation à la mémoire"""
        self.conversations.append({
            "user_id": user_id,
            "timestamp": datetime.now().isoformat(),
            "message": message,
            "response": response,
            "used_search": used_search
        })
        self._save_memory()
    
    def get_user_history(self, user_id: str, limit: int = 10) -> List[Dict]:
        """Récupérer l'historique d'un utilisateur"""
        user_conversations = [
            conv for conv in self.conversations 
            if conv["user_id"] == user_id
        ]
        return user_conversations[-limit:]
    
    def search_memory(self, query: str) -> List[Dict]:
        """Chercher dans la mémoire"""
        query_lower = query.lower()
        results = []
        
        for conv in self.conversations:
            if query_lower in conv["message"].lower() or query_lower in conv["response"].lower():
                results.append(conv)
        
        return results
    
    def get_stats(self) -> Dict:
        """Statistiques de la mémoire"""
        unique_users = len(set(conv["user_id"] for conv in self.conversations))
        searches_used = len([conv for conv in self.conversations if conv.get("used_search")])
        
        return {
            "total_conversations": len(self.conversations),
            "unique_users": unique_users,
            "searches_used": searches_used,
            "memory_file_size_kb": os.path.getsize(self.memory_file) / 1024 if os.path.exists(self.memory_file) else 0
        }


# Instance globale
memory = ConversationMemory()
