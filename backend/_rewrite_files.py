from pathlib import Path

root = Path(r'C:\Users\anasw\Desktop\Wakif AI\backend')

search_router = '''import logging
import re

logger = logging.getLogger(__name__)

WEATHER_KEYWORDS = ["météo", "weather", "tqas", "ljaw", "taqs", "tqs", "jaw", "meteo", "weather in"]
TODAY_KEYWORDS = ["daba", "lyoum", "liom", "aujourd'hui", "maintenant", "today", "now"]
TOMORROW_KEYWORDS = ["demain", "ghda", "tomorrow"]
WEEK_KEYWORDS = ["had simana", "had ssimana", "cette semaine", "this week", "هاد السيمانة", "هاد الاسبوع", "simana", "semaine"]
MONTH_KEYWORDS = ["had chhar", "had char", "ce mois", "this month", "هاد الشهر", "chhar", "mois"]
CURRENT_TIME_SIGNALS = TODAY_KEYWORDS + WEEK_KEYWORDS + MONTH_KEYWORDS + ["today", "this week", "this month", "now"]
WEATHER_SIGNALS = WEATHER_KEYWORDS + ["الطقس", "الجو"]
NEWS_SIGNALS = ["akhbar", "news", "actualité", "actu", "اخبار", "أخبار"]
PRICE_SIGNALS = ["prix", "price", "taman", "tarif", "saman", "السعر", "الثمن", "تمن"]
SPORTS_SIGNALS = ["match", "matchs", "matches", "botola", "score", "resultat", "résultat", "league", "ligue", "champions", "النتيجة", "الماتش", "الدوري", "بطولة"]
GENERAL_EXCLUSIONS = ["comment", "how", "kif", "kifach", "kifash", "pourquoi", "why", "fach", "3lach", "explain", "definition", "what is", "shno", "شنو", "علاش", "كيفاش", "فاش الفرق"]


def normalize_darija_text(text: str) -> str:
    """Nettoyage léger pour aider la détection de contexte sans forcer une traduction."""
    t = " ".join((text or "").split()).lower()
    t = t.replace("\u200c", " ")
    t = re.sub(r"[\u2019\']", "", t)
    t = re.sub(r"(.)\1{2,}", r"\1\1", t)
    t = t.replace("3", "ع")
    t = t.replace("7", "ح")
    t = t.replace("9", "ق")
    t = t.replace("5", "خ")
    t = t.replace("2", "ء")
    t = t.replace("6", "ط")
    t = t.replace("8", "غ")
    return t


def get_search_freshness(message: str) -> str:
    """Filtre de fraîcheur Brave adapté à la question."""
    text = normalize_darija_text(message)
    if any(word in text for word in TODAY_KEYWORDS + TOMORROW_KEYWORDS):
        return "pd"
    if any(word in text for word in WEEK_KEYWORDS):
        return "pw"
    if any(word in text for word in MONTH_KEYWORDS):
        return "pm"
    return "pw"


def build_search_query(message: str) -> str:
    """Construit une requête de recherche pour les besoins de recherche actuels."""
    text = normalize_darija_text(message)

    if any(word in text for word in SPORTS_SIGNALS):
        if any(word in text for word in WEEK_KEYWORDS + MONTH_KEYWORDS):
            return "Botola Pro fixtures this week Morocco"
        return "Botola Pro fixtures today Morocco"

    if any(word in text for word in WEATHER_SIGNALS):
        city_match = re.search(r"(?:f|a|in|dans)\s+([a-zà-ÿ]+)", text)
        city = city_match.group(1) if city_match else ""
        city = {"casa": "Casablanca Morocco", "casablanca": "Casablanca Morocco", "rabat": "Rabat Morocco", "marrakech": "Marrakech Morocco"}.get(city, city)
        when = "tomorrow" if any(word in text for word in TOMORROW_KEYWORDS) else "today"
        if city:
            return f"weather in {city} {when}"
        return f"weather {when}"

    return message


def needs_search(message: str, history: list | None = None) -> bool:
    """Détermine si une recherche web est vraiment nécessaire."""
    text = normalize_darija_text(message)
    history_text = " ".join(str(msg.get("content", "")) for msg in (history or []) if isinstance(msg, dict))
    combined = (text + " " + normalize_darija_text(history_text)).strip()

    if any(sig in combined for sig in WEATHER_SIGNALS) and any(sig in combined for sig in CURRENT_TIME_SIGNALS):
        logger.debug("needs_search: weather + recent-time context => true")
        return True

    if any(sig in combined for sig in PRICE_SIGNALS) and any(sig in combined for sig in CURRENT_TIME_SIGNALS + ["today", "this week", "this month", "now"]):
        logger.debug("needs_search: pricing + current-time context => true")
        return True

    if any(sig in combined for sig in NEWS_SIGNALS) and any(sig in combined for sig in CURRENT_TIME_SIGNALS):
        logger.debug("needs_search: news + current-time context => true")
        return True

    if any(sig in combined for sig in SPORTS_SIGNALS) and any(sig in combined for sig in CURRENT_TIME_SIGNALS + ["match", "matches", "botola", "resultat", "résultat", "score"]):
        logger.debug("needs_search: sports + current context => true")
        return True

    if any(sig in combined for sig in GENERAL_EXCLUSIONS):
        if not any(sig in combined for sig in WEATHER_SIGNALS + PRICE_SIGNALS + NEWS_SIGNALS + SPORTS_SIGNALS):
            logger.debug(f"needs_search: explanatory/general question -> false: {message}")
            return False

    matched = [sig for sig in WEATHER_SIGNALS + PRICE_SIGNALS + NEWS_SIGNALS + SPORTS_SIGNALS if sig in combined]
    should_search = bool(matched)
    logger.debug(f"needs_search: message='{message}' normalized='{text}' -> should_search={should_search}, matched={matched}")
    return should_search
'''

agent_text = '''import logging
import re
from datetime import datetime

import requests

from search import get_search_stats, web_search
from search_router import build_search_query, get_search_freshness, needs_search

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

SYSTEM_PROMPT = """
نتا Wakif AI 🇲🇦 — مساعد ذكي مغربي، طبيعي، ودود، وذكي، كتكلم الدارجة المغربية، الفرنسية، والإنجليزية.

🎯 القاعدة الأساسية:
- جاوب بنفس اللغة اللي المستخدم كيتكلم بها.
- إذا كان السؤال قصير وسهل، جاوب قصير، طبيعي، وملائم.
- إذا كان السؤال أكبر أو يحتاج معلومات جديدة، رد بطريقة منظمة ومفيدة.
- حافظ على الطابع المغربي الحقيقي، بدون تعقيد، بدون جمل ميّتة، بدون تعبيرات "الذكاء الاصطناعي" الروتينية.
- لا تكرر نفس الجملة أو نفس القالب في كل رد.

🧠 COMPRÉHENSION DU MAROCAIN / DARIJA
نتا خاصك تفهم الدارجة المغربية الطبيعية، ماشي غير العربية الفصحى.

المستخدم يقدر يكتب:
- بالدارجة العربية
- بالفرنسية
- بالإنجليزية
- بالArabizi
- بمزيج بينهم
- بأخطاء إملائية
- باختصارات
- بلا accents
- بحروف مكررة
- بطريقة غير رسمية

ما تحكمش على السؤال من الكتابة فقط.
حاول فهم المعنى المقصود.

أمثلة:
"Rasy ki darni liom" = "راسي كيضرني اليوم"
"Rass diali kay darni" = "راسي كيضرني"
"Chr7 lia chno hwa" = "شرح ليا شنو هو"
"Chno hwa" = "شنو هو"
"Kifach kaykhdem" = "كيفاش كيخدم"
"Wach nta mred" = "واش نتا مريض"
"Kat 3rf Dofus Touch" = "كتعرف Dofus Touch"
"Ch7al taman" = "شحال الثمن"
"Fin kayn" = "فين كاين"
"3lach" = "علاش"
"Nta m3aya?" = "نتا معايا؟"

فهم السياق قبل ما تجاوب.
إذا قال المستخدم: "Chr7 lia" أو "Chno hwa" أو "W kifach?" أو "W ch7al?" أو "Fin?" فاستعمل آخر messages باش تعرف شنو الموضوع.

ما تقولش: "ما فهمتش" إلا إذا كان المعنى فعلاً غير واضح.
ما تطلبش من المستخدم يعاود يصيغ السؤال إلا إذا كانت هناك حاجة حقيقية لذلك.
إذا فهمتي المقصود، جاوب مباشرة وبطريقة طبيعية.

🇲🇦 STYLE
جاوب بنفس اللغة والأسلوب ديال المستخدم.
إذا المستخدم كيكتب Darija/Arabizi، جاوب غالباً بالدارجة المغربية.
ما تحاولش تحول كل جواب للفصحى.
ما تستعملش Darija مصطنعة أو مبالغ فيها.
خلي الجواب طبيعي بحال واحد مغربي كيهضر معاه.
ما تكرر: "أكيد، نقدر نساعدك" أو "قل لي شنو بغيتي" أو "ما فهمتش" في كل جواب.
كل جواب خاصو يكون عندو معنى ومعلومة مفيدة.

🧠 CONTEXT
السياق السابق مهم.
الرسالة الحالية قد تكون continuation للرسالة السابقة.

مثال:
User: "Kat 3rf Dofus Touch?"
Assistant: "إييه، Dofus Touch هي..."
User: "Chr7 lia chno hwa"

المقصود: "شرح ليا شنو هي Dofus Touch".
جاوب مباشرة على Dofus Touch.

مثال آخر:
User: "Chno ahsan téléphone?"
Assistant: "..."
User: "W iPhone?"

المقصود: "و iPhone شنو الوضع ديالو؟"
استعمل السياق.

🛑 DON'T BE OVERLY CAUTIOUS
ما تقولش أن سؤال بسيط "صعيب".
ما تقولش أنك "ما قادرش تفهم" سؤال واضح.
ما تطلبش clarification بلا سبب.
ما تمدحش Wakif AI بلا سبب.
إذا سأل المستخدم عن أفضل AI، جاوب بشكل محايد.

🔎 SEARCH
استعمل البحث فقط عندما تكون المعلومة محتاجة تكون حديثة أو متغيرة.
البحث مناسب لـ:
- الأخبار
- الطقس
- الأسعار الحالية
- نتائج المباريات
- المواعيد الحالية
- الأحداث الحالية
- معلومات حديثة
- التوفر الحالي

ما تحتاجش search للأسئلة العامة والمعرفة المستقرة.
حتى إذا كان السؤال بالدارجة، فهم السؤال أولاً ثم قرر واش خاص search.

🎯 RESPONSE
قبل الإجابة:
1. فهم اللغة.
2. فهم Arabizi إن وجد.
3. فهم الأخطاء المحتملة.
4. اقرأ السياق.
5. حدد نية المستخدم.
6. قرر واش search ضروري.
7. جاوب مباشرة.

لا تظهر هذه الخطوات للمستخدم.

📌 قواعد الجودة:
- إذا عندك خبرة أو معلومة مؤكدة، اعطها بشكل مباشر وموثوق.
- إذا ما عندكش تأكيد، قل صراحة: "ما عندي ماتأكد من هادشي" أو "ما لقيتش معلومة موثوقة".
- لا تختلق أحداث، تواريخ، أرقام، أو أسعار.
- إذا السؤال يحتاج بحث حديث، استخدم البحث، ثم خدم فقط المعلومات الحالية.
- إذا النتائج قديمة أو ناقصة، قلها بوضوح ولا تحاول تخمين شيء.
- لا تمدح Wakif AI تلقائياً في كل جواب.
- إذا المستخدم سأل عن "أفضل AI" أو "أفضل agent" أو "أفضل chatbot"، قارن بشكل محايد، ولا ترفع Wakif AI كأفضل تلقائياً فقط لأنه المساعد الحالي.

💬 أسلوب الرد:
- ودود، سريع، واضح، ومباشر.
- لا تظهر التفكير الداخلي أو التردد المفرط.
- تجنب الخلط بين اللغات إلا إذا كان المستخدم هو اللي طلبها.
- استخدم أسلوب محادثة حقيقية، مثل: "أكيد،" "واخا،" "حظًا"، "هونيك"، لكن بدون مبالغة.
- كل جواب يكون عملي ومفيد، حتى لو قصير.
"""


def normalize_for_logs(message: str) -> str:
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
    if any(term in text for term in ["weather", "météo", "ljaw", "taqs", "alkaw", "الطقس"]):
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
        role = msg.get("role", "")
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
    """Réponses ultra simples uniquement."""
    text = " ".join(message.split()).strip().lower()
    if not text:
        return None

    greeting_patterns = [
        r"^(salut|salam|bonjour|hello|hi|hey|slm|slt)$",
        r"^(salam|slm)\s+(3likom|alaykom|alaykoum)$",
    ]
    if any(re.search(pattern, text) for pattern in greeting_patterns):
        return "Wa 3likom salam 🇲🇦❤️ Kidayr? Chno bghiti n3awnk fih?"

    if re.fullmatch(r"(chno|chnou|shno|shnu)\s+(smitk|smitek|smiytek|smia\s+dyalk)", text):
        return "Smiti Wakif AI 🇲🇦"

    if re.fullmatch(r"(smitk|smitek|smiytek|smia\s+dyalk)\??", text):
        return "Smiti Wakif AI 🇲🇦"

    if re.search(r"^(chkon\s+nta|chkon\s+nti|who\s+are\s+you|tu\s+es\s+qui|wach\s+nta\s+ai|wach\s+nta\s+bot)$", text):
        return "Ana Wakif AI 🇲🇦, assistant intelligent مغربي. Kanقدر نفهم الدارجة، français و English ونعاونك ف بزاف ديال الحوايج."

    if re.fullmatch(r"(kif\s+dayr|kif\s+dayra|kidayr|kidayra|kifach\s+dayr|ca\s+va|how\s+are\s+you)\??", text):
        return "Labas الحمد لله 😄 W nta?"

    return None


def _is_result_recent(result: dict, freshness: str | None) -> bool:
    """Reject stale web results when the answer should be current."""
    age = (result or {}).get("age") or ""
    age_lower = age.lower().strip()
    if not age_lower:
        return True

    if re.search(r"\b(19|20)\d{2}\b", age_lower):
        match_year = int(re.search(r"\b(19|20)\d{2}\b", age_lower).group(0))
        if match_year < datetime.now().year:
            return False

    relative_match = re.search(r"(\d+)\s*(year|years|month|months|week|weeks|day|days|hour|hours|minute|minutes)", age_lower)
    if relative_match:
        value = int(relative_match.group(1))
        unit = relative_match.group(2)
        if unit.startswith("year") and value >= 1:
            return False
        if unit.startswith("month") and value >= 1 and freshness in {"pd", "pw"}:
            return False
        if unit.startswith("week") and value >= 1 and freshness == "pd":
            return False

    return True


def ask_wakif(user_message, history=None):
    """معالج رئيسي للرد على المستخدم."""
    history = history or []
    direct_answer = get_direct_answer(user_message)
    if direct_answer:
        return {
            "response": direct_answer,
            "used_search": False,
            "search_results_count": 0,
        }

    should_search = needs_search(user_message, history)
    normalized_message = normalize_for_logs(user_message)
    detected_language = detect_language(user_message)
    detected_intent = detect_intent(user_message)

    logger.debug("USER MESSAGE: %s", user_message)
    logger.debug("HISTORY COUNT: %s", len(history))
    logger.debug("NORMALIZED MESSAGE: %s", normalized_message)
    logger.debug("DETECTED LANGUAGE: %s", detected_language)
    logger.debug("DETECTED INTENT: %s", detected_intent)
    logger.debug("SEARCH NEEDED: %s", should_search)

    search_results = []
    search_context = ""
    if should_search:
        search_query = build_search_query(user_message)
        freshness = get_search_freshness(user_message)
        logger.debug("SEARCH QUERY: %s", search_query)
        logger.debug("SEARCH FRESHNESS: %s", freshness)
        raw_results = web_search(search_query, freshness=freshness)
        search_results = [r for r in (raw_results or []) if _is_result_recent(r, freshness)]

        if search_results:
            search_context = "\n\n".join([
                f"📰 مصدر:\nالعنوان: {result['title']}\nالمحتوى: {result['snippet']}\nالرابط: {result['url']}\nتاريخ النتيجة: {result.get('age') or 'غير معروف'}"
                for result in search_results
            ])
        else:
            today_str = datetime.now().strftime("%Y-%m-%d")
            search_context = f"تاريخ اليوم هو {today_str}. ما لقيتش نتائج حديثة كافية في البحث. لا تستخدم أي معلومة قديمة. قل للمستخدم بصراحة أنك ما عندكش تأكيد على هذا الموضوع اليوم، وما تخترعش تواريخ ولا أحداث."

    full_prompt = SYSTEM_PROMPT + "\n\n"
    full_prompt += format_history(history)
    if search_context:
        full_prompt += "=== CONTEXTE WEB ===\n"
        full_prompt += search_context + "\n=== FIN CONTEXTE WEB ===\n\n"
    full_prompt += f"=== NOUVEAU MESSAGE ===\nUtilisateur: {user_message}\n\nRéponds directement à la question en tenant compte du contexte et de l'historique.\nWakif AI:\n"

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
            response_text = data.get("response", "معاذ الله، ما جات جواب.")
        else:
            response_text = f"معاذ الله، مشكلة مع Ollama (HTTP {ollama_response.status_code})"
    except requests.exceptions.ConnectionError:
        response_text = "معاذ الله، Ollama ما هي مشتغلة. شحال 'ollama serve' تشتغل؟"
    except Exception as e:
        logger.error("Erreur ollama: %s", e)
        response_text = f"معاذ الله، حصلت مشكلة: {str(e)}"

    return {
        "response": response_text,
        "used_search": should_search and bool(search_results),
        "search_results_count": len(search_results),
    }


def get_stats():
    """الحصول على إحصائيات استخدام API."""
    return get_search_stats()
'''

(root / 'search_router.py').write_text(search_router, encoding='utf-8')
(root / 'agent.py').write_text(agent_text, encoding='utf-8')
print('done')
