import logging
import re

logger = logging.getLogger(__name__)

WEATHER_KEYWORDS = [
    "meteo", "weather", "tqas", "ljaw", "taqs", "tqs", "jaw", "meteo", "weather in",
    "météo", "الطقس", "الجو"
]
TODAY_KEYWORDS = ["daba", "lyoum", "liom", "aujourdhui", "aujourd'hui", "maintenant", "today", "now", "lyoum", "اليوم"]
TOMORROW_KEYWORDS = ["demain", "ghda", "tomorrow", "غدا", "غدا"]
WEEK_KEYWORDS = ["had simana", "had ssimana", "cette semaine", "this week", "simana", "semaine", "هاد السيمانة", "هاد الاسبوع", "اسبوع", "الأسبوع"]
MONTH_KEYWORDS = ["had chhar", "had char", "ce mois", "this month", "chhar", "mois", "هاد الشهر", "الشهر"]
CURRENT_TIME_SIGNALS = TODAY_KEYWORDS + WEEK_KEYWORDS + MONTH_KEYWORDS + ["today", "this week", "this month", "now"]
WEATHER_SIGNALS = WEATHER_KEYWORDS
NEWS_SIGNALS = ["akhbar", "news", "actualité", "actu", "اخبار", "أخبار", "actualité"]
PRICE_SIGNALS = ["prix", "price", "taman", "tarif", "saman", "السعر", "الثمن", "تمن", "prix actuel"]
SPORTS_SIGNALS = ["match", "matchs", "matches", "botola", "score", "resultat", "résultat", "league", "ligue", "champions", "الماتش", "النتيجة", "الدوري", "بطولة", "botola pro"]
GENERAL_EXCLUSIONS = [
    "comment", "how", "kif", "kifach", "kifash", "pourquoi", "why", "fach", "3lach", "explain",
    "definition", "what is", "shno", "شنو", "علاش", "كيفاش", "فاش الفرق"
]


def normalize_darija_text(text: str) -> str:
    """Light normalization to help context detection without over-translating."""
    t = " ".join((text or "").split()).lower()
    t = t.replace("\u200c", " ")
    t = re.sub(r"[’'`\u2019]", "", t)
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)
    replacements = {
        "3": "ع",
        "7": "ح",
        "9": "ق",
        "5": "خ",
        "2": "ء",
        "6": "ط",
        "8": "غ",
        "@": "a",
        "_": " ",
    }
    for old, new in replacements.items():
        t = t.replace(old, new)
    return t.strip()


def get_search_freshness(message: str) -> str:
    """Return a Brave freshness filter appropriate to the user ask."""
    text = normalize_darija_text(message)
    if any(word in text for word in TODAY_KEYWORDS + TOMORROW_KEYWORDS):
        return "pd"
    if any(word in text for word in WEEK_KEYWORDS):
        return "pw"
    if any(word in text for word in MONTH_KEYWORDS):
        return "pm"
    return "pw"


def build_search_query(message: str) -> str:
    """Build a good Brave query for current and time-sensitive questions."""
    text = normalize_darija_text(message)

    if any(word in text for word in WEATHER_SIGNALS):
        city = ""
        city_map = {
            "casa": "Casablanca Morocco",
            "casablanca": "Casablanca Morocco",
            "rabat": "Rabat Morocco",
            "marrakech": "Marrakech Morocco",
            "fes": "Fes Morocco",
            "meknes": "Meknes Morocco",
            "tanger": "Tangier Morocco",
            "agadir": "Agadir Morocco",
        }
        for candidate, canonical in city_map.items():
            if candidate in text:
                city = canonical
                break
        when = "tomorrow" if any(word in text for word in TOMORROW_KEYWORDS) else "today"
        if city:
            return f"weather in {city} {when}"
        return f"weather in Morocco {when}"

    if any(word in text for word in SPORTS_SIGNALS):
        if any(word in text for word in WEEK_KEYWORDS + MONTH_KEYWORDS):
            return "Botola Pro fixtures this week Morocco"
        return "Botola Pro fixtures today Morocco"

    if any(word in text for word in PRICE_SIGNALS):
        product = "" 
        for candidate in ["iphone", "samsung", "dofus", "or", "gold", "car", "voiture"]:
            if candidate in text:
                product = candidate
                break
        if product:
            return f"current price {product} Morocco"
        return "current prices Morocco"

    return message


def needs_search(message: str, history: list | None = None) -> bool:
    """Decide whether a web search is genuinely necessary."""
    text = normalize_darija_text(message)
    history_text = " ".join(
        str(msg.get("content", "")) for msg in (history or []) if isinstance(msg, dict)
    )
    combined = (text + " " + normalize_darija_text(history_text)).strip()

    if any(sig in combined for sig in WEATHER_SIGNALS) and any(sig in combined for sig in CURRENT_TIME_SIGNALS):
        logger.debug("needs_search: weather + current time => true")
        return True

    if any(sig in combined for sig in PRICE_SIGNALS) and any(sig in combined for sig in CURRENT_TIME_SIGNALS):
        logger.debug("needs_search: price + current time => true")
        return True

    if any(sig in combined for sig in NEWS_SIGNALS) and any(sig in combined for sig in CURRENT_TIME_SIGNALS):
        logger.debug("needs_search: news + current time => true")
        return True

    if any(sig in combined for sig in SPORTS_SIGNALS) and (
        any(sig in combined for sig in CURRENT_TIME_SIGNALS)
        or any(sig in combined for sig in ["match", "matches", "botola", "resultat", "résultat", "score"])
    ):
        logger.debug("needs_search: sports + current context => true")
        return True

    if any(sig in combined for sig in GENERAL_EXCLUSIONS):
        if not any(sig in combined for sig in WEATHER_SIGNALS + PRICE_SIGNALS + NEWS_SIGNALS + SPORTS_SIGNALS):
            logger.debug("needs_search: general/explanatory question => false")
            return False

    matched = [sig for sig in WEATHER_SIGNALS + PRICE_SIGNALS + NEWS_SIGNALS + SPORTS_SIGNALS if sig in combined]
    should_search = bool(matched)
    logger.debug("needs_search: message='%s' normalized='%s' -> should_search=%s matched=%s", message, text, should_search, matched)
    return should_search
