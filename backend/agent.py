import logging
import re
from datetime import datetime

import requests

from search import get_search_stats, web_search
from search_router import build_search_query, get_search_freshness, needs_search

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SYSTEM_PROMPT = """
Tu es Wakif AI 🇲🇦, un assistant marocain naturel, utile et conversationnel.

Règles de base:
- Réponds dans la langue du message de l'utilisateur quand c'est clair.
- Si le message est simple, réponds simplement.
- Si le message est plus complexe, réponds de façon utile et claire.
- Garde un style marocain naturel, ni robotique ni trop formel.
- Ne te vante pas ni ne prétends être le "meilleur AI" sans raison.

🧠 COMPRÉHENSION DU MAROCAIN / DARIJA
Comprends le marocain naturel, y compris l'arabizi, les fautes, les variantes et les phrases courtes.

Exemples utiles:
- "Rasy ki darni liom" = "راسي كيضرني اليوم"
- "Rass diali kay darni" = "راسي كيضرني"
- "Chr7 lia chno hwa" = "شرح ليا شنو هو"
- "Chno hwa" = "شنو هو"
- "Kifach kaykhdem" = "كيفاش كيخدم"
- "Wach nta mred" = "واش نتا مريض"
- "Kat 3rf Dofus Touch" = "كتعرف Dofus Touch"
- "Ch7al taman" = "شحال الثمن"
- "Fin kayn" = "فين كاين"
- "3lach" = "علاش"
- "Nta m3aya?" = "نتا معايا؟"

Tu peux rencontrer:
- Darija/arabizi
- mélanges français/anglais
- fautes de frappe et sans accents
- phrases très courtes
- références au message précédent
- messages implicites

Si l'utilisateur dit "chr7 lia", "chno hwa", "w kifach?", "w ch7al?", ou "fin?", utilise l'historique pour comprendre le sujet.

Si le sens est clair, réponds directement. Ne demandes pas de reformulation sauf si l'ambiguïté est réelle.

🧠 CONTEXT
Le contexte précédent compte. La phrase actuelle peut être la suite logique d'un message précédent.

Exemple:
Utilisateur: "Kat 3rf Dofus Touch ?"
Wakif AI: "إييه، Dofus Touch هي..."
Utilisateur: "Chr7 lia chno hwa"

Le sens est alors: "شرح ليا شنو هي Dofus Touch".

Exemple 2:
Utilisateur: "Chno ahsan téléphone ?"
Wakif AI: "..."
Utilisateur: "W iPhone ?"

Le sens est: "و iPhone شنو الوضع ديالو؟"

🔎 SEARCH
Utilise la recherche seulement si la réponse doit être actuelle, variable, ou factuelle.

Recherche adaptée pour:
- météo
- actualités
- prix actuels
- résultats de matchs
- dates / événements actuels
- infos récentes

Ne fais pas de recherche pour:
- questions générales
- définitions simples
- conversations sociales
- questions basées sur la connaissance stable

Si une question semble demander une réponse générale, réponds directement sans recherche.

🚫 ÉVITER LES ERREURS COURANTES
- Ne dis pas que la question est trop difficile si elle est claire.
- Ne demande pas de reformulation inutile.
- N'utilise pas un gros dictionnaire de phrases codées en dur.
- Ne réponds pas par un faux "je ne comprends pas" si le sens est évident.
- Ne génère pas d'hallucination sur des infos actuelles sans preuve.

🎯 STYLE DE RÉPONSE
- Réponds dans le style de l'utilisateur.
- Si l'utilisateur parle Darija/Arabizi, réponds souvent en Darija naturelle.
- Reste simple, naturel, utile, et rapide.
- Évite les phrases figées comme "Je peux t'aider" à chaque réponse.
- Réponds avec un vrai contenu utile.
"""


def normalize_for_logs(message: str) -> str:
    """Normalize a message for internal debugging without translating it."""
    text = " ".join((message or "").split()).lower()
    text = re.sub(r"[^a-z0-9\s\u0600-\u06ff]+", " ", text)
    text = re.sub(r"(.)\1{2,}", r"\1\1", text)
    return text.strip()


def detect_language(message: str) -> str:
    text = (message or "").lower()
    if re.search(r"[\u0600-\u06ff]", text):
        return "arabic"
    if any(token in text for token in ["bonjour", "salut", "merci", "francais", "oui", "non"]):
        return "french"
    if any(token in text for token in ["hello", "thanks", "what", "where", "how", "when", "why"]):
        return "english"
    return "mixed"


def detect_intent(message: str) -> str:
    text = normalize_for_logs(message)
    if re.search(r"^(salam|salut|bonjour|hello|hi|hey)", text):
        return "greeting"
    if re.search(r"(smitk|smitek|chkon|who are you|who are u)", text):
        return "identity"
    if any(term in text for term in ["weather", "meteo", "ljaw", "taqs", "الطقس", "الجو"]):
        return "weather"
    if any(term in text for term in ["match", "matches", "botola", "resultat", "résultat", "score", "الدوري", "بطولة"]):
        return "sports"
    if any(term in text for term in ["taman", "prix", "price", "السعر", "الثمن"]):
        return "price"
    if any(term in text for term in ["akhbar", "news", "actualité", "اخبار", "أخبار"]):
        return "news"
    if any(term in text for term in ["chno", "shno", "kifach", "wach", "3lach", "fin", "chr7", "شرح", "شنو"]):
        return "general_question"
    return "conversation"


def format_history(history):
    if not history:
        return ""

    lines = ["=== HISTORIQUE DE LA CONVERSATION ==="]
    for msg in history[-10:]:
        if not isinstance(msg, dict):
            continue
        role = str(msg.get("role", "")).strip()
        content = str(msg.get("content", "")).strip()
        if not content:
            continue
        if role == "user":
            lines.append(f"Utilisateur: {content}")
        elif role == "assistant":
            lines.append(f"Wakif AI: {content}")
    lines.append("=== FIN HISTORIQUE ===")
    return "\n".join(lines) + "\n\n"


def get_direct_answer(message: str):
    """Keep this path intentionally tiny: greetings and identity only."""
    text = " ".join((message or "").split()).strip().lower()
    if not text:
        return None

    greeting_patterns = [
        r"^(salut|salam|bonjour|hello|hi|hey|slm|slt)$",
        r"^(salam|slm)\s+(3likom|alaykom|alaykoum)$",
    ]
    if any(re.search(pattern, text) for pattern in greeting_patterns):
        return "Wa 3likom salam 🇲🇦 Kidayr? Chno bghiti n3awnk fih?"

    if re.fullmatch(r"(chno|chnou|shno|shnu)\s+(smitk|smitek|smiytek|smia\s+dyalk)", text):
        return "Smiti Wakif AI 🇲🇦"

    if re.fullmatch(r"(smitk|smitek|smiytek|smia\s+dyalk)\??", text):
        return "Smiti Wakif AI 🇲🇦"

    if re.search(r"^(chkon\s+nta|chkon\s+nti|who\s+are\s+you|tu\s+es\s+qui|wach\s+nta\s+ai|wach\s+nta\s+bot)$", text):
        return "Ana Wakif AI 🇲🇦, assistant intelligent marocain. N9dar n3awnk bzzaf."

    if re.fullmatch(r"(kif\s+dayr|kif\s+dayra|kidayr|kidayra|kifach\s+dayr|ca\s+va|how\s+are\s+you)\??", text):
        return "Labas الحمد لله 😄 W nta?"

    return None


def _is_result_recent(result: dict, freshness: str | None) -> bool:
    """Filter out stale results when the question is current."""
    age = (result or {}).get("age") or ""
    age_lower = age.lower().strip()
    if not age_lower:
        return True

    year_match = re.search(r"\b(19|20)\d{2}\b", age_lower)
    if year_match:
        match_year = int(year_match.group(0))
        if match_year < datetime.now().year:
            return False

    relative = re.search(r"(\d+)\s*(year|years|month|months|week|weeks|day|days|hour|hours|minute|minutes)", age_lower)
    if relative:
        value = int(relative.group(1))
        unit = relative.group(2)
        if unit.startswith("year") and value >= 1:
            return False
        if unit.startswith("month") and value >= 1 and freshness in {"pd", "pw"}:
            return False
        if unit.startswith("week") and value >= 1 and freshness == "pd":
            return False

    return True


def ask_wakif(user_message, history=None):
    """Main orchestration for direct answer, search routing, and model response."""
    history = history or []
    message = str(user_message or "").strip()

    direct_answer = get_direct_answer(message)
    if direct_answer:
        return {
            "response": direct_answer,
            "used_search": False,
            "search_results_count": 0,
        }

    should_search = needs_search(message, history)
    normalized_message = normalize_for_logs(message)
    detected_language = detect_language(message)
    detected_intent = detect_intent(message)

    logger.debug("USER MESSAGE: %s", message)
    logger.debug("HISTORY COUNT: %s", len(history))
    logger.debug("NORMALIZED MESSAGE: %s", normalized_message)
    logger.debug("DETECTED LANGUAGE: %s", detected_language)
    logger.debug("DETECTED INTENT: %s", detected_intent)
    logger.debug("SEARCH NEEDED: %s", should_search)

    search_results = []
    search_context = ""
    if should_search:
        search_query = build_search_query(message)
        freshness = get_search_freshness(message)
        logger.debug("SEARCH QUERY: %s", search_query)
        logger.debug("SEARCH FRESHNESS: %s", freshness)
        raw_results = web_search(search_query, freshness=freshness)
        search_results = [r for r in (raw_results or []) if _is_result_recent(r, freshness)]

        if search_results:
            search_context = "\n\n".join(
                [
                    f"Résultat:\nTitre: {result['title']}\nDescription: {result['snippet']}\nURL: {result['url']}\nAge: {result.get('age') or 'inconnue'}"
                    for result in search_results
                ]
            )
        else:
            search_context = (
                f"Aucune source web fiable n'a été trouvée pour cette demande le {datetime.now().strftime('%Y-%m-%d')}. "
                "Le modèle doit répondre avec prudence et ne pas inventer d'information récente."
            )

    full_prompt = SYSTEM_PROMPT + "\n\n"
    full_prompt += f"Date actuelle: {datetime.now().strftime('%Y-%m-%d')}\n\n"
    if history:
        full_prompt += format_history(history)
    if search_context:
        full_prompt += "=== CONTEXTE WEB ===\n"
        full_prompt += search_context + "\n=== FIN CONTEXTE WEB ===\n\n"
    full_prompt += (
        "=== QUESTION ACTUELLE ===\n"
        f"Utilisateur: {message}\n\n"
        "Réponds directement à la question en tenant compte du contexte et de l'historique.\n"
        "Si le sens est clair, réponds sans demander de reformulation inutile.\n"
        "Wakif AI:\n"
    )

    try:
        ollama_response = requests.post(
            "http://localhost:11434/api/generate",
            json={
                "model": "wakif-ai-v2:latest",
                "prompt": full_prompt,
                "stream": False,
            },
            timeout=30,
        )

        if ollama_response.status_code == 200:
            data = ollama_response.json()
            response_text = data.get("response", "Je n'ai pas de réponse exploitable.")
        else:
            response_text = f"Erreur Ollama (HTTP {ollama_response.status_code})"
    except requests.exceptions.ConnectionError:
        response_text = "Le service Ollama n'est pas disponible. Vérifie que 'ollama serve' est lancé."
    except Exception as exc:
        logger.error("Erreur Ollama: %s", exc)
        response_text = f"Erreur générative: {exc}"

    return {
        "response": response_text,
        "used_search": should_search and bool(search_results),
        "search_results_count": len(search_results),
    }


def get_stats():
    """Return search statistics for API monitoring."""
    return get_search_stats()
