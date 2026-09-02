from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from agent import ask_wakif, get_stats
from memory_manager import memory


app = FastAPI(
    title="Wakif AI 🇲🇦",
    description="أفضل مساعد ذكي مغربي - Best Moroccan AI Assistant",
    version="2.0.0"
)

# السماح للواجهة الأمامية (frontend) بالتواصل مع الـ API عبر CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class ChatRequest(BaseModel):
    message: str
    history: list = []
    user_id: str = "default"


@app.get("/")
def home():
    return {
        "status": "online ✅",
        "agent": "Wakif AI 🇲🇦",
        "version": "2.0.0",
        "description": "أفضل مساعد ذكي مغربي",
        "features": [
            "🤖 Darija المغربية",
            "🔍 بحث ذكي (Brave Search)",
            "💰 توفير API (1000 بحث)",
            "🧠 ذاكرة المحادثة",
            "📍 معلومات دقيقة وموثوقة",
            "⚡ تخزين مؤقت ذكي"
        ],
        "endpoints": {
            "chat": "POST /chat",
            "stats": "GET /stats",
            "memory": "GET /memory/stats",
            "docs": "GET /docs"
        }
    }


@app.get("/stats")
def stats():
    """الإحصائيات والمراقبة - Search API Statistics"""
    return get_stats()


@app.get("/memory/stats")
def memory_stats():
    """إحصائيات الذاكرة - Memory Statistics"""
    return memory.get_stats()


@app.get("/memory/user/{user_id}")
def user_history(user_id: str, limit: int = 10):
    """الحصول على تاريخ المستخدم"""
    return {
        "user_id": user_id,
        "history": memory.get_user_history(user_id, limit)
    }


@app.post("/chat")
def chat(request: ChatRequest):
    """
    نقطة المحادثة الرئيسية
    
    POST /chat
    {
        "message": "السؤال بالدارجة أو الفرنسية أو الإنجليزية",
        "user_id": "user_123",
        "history": [
            {"role": "user", "content": "..."},
            {"role": "assistant", "content": "..."}
        ]
    }
    """
    
    result = ask_wakif(
        request.message,
        request.history
    )

    # حفظ في الذاكرة
    memory.add_conversation(
        user_id=request.user_id,
        message=request.message,
        response=result["response"],
        used_search=result["used_search"]
    )

    return {
        "response": result["response"],
        "search_used": result["used_search"],
        "search_results": result["search_results_count"],
        "user_id": request.user_id
    }


@app.post("/chat-stream")
def chat_stream(request: ChatRequest):
    """
    نسخة streaming للردود الطويلة
    """
    result = ask_wakif(
        request.message,
        request.history
    )
    
    # حفظ في الذاكرة
    memory.add_conversation(
        user_id=request.user_id,
        message=request.message,
        response=result["response"],
        used_search=result["used_search"]
    )
    
    return {
        "response": result["response"],
        "search_used": result["used_search"],
        "search_results": result["search_results_count"],
        "user_id": request.user_id
    }


@app.get("/health")
def health_check():
    """فحص صحة النظام"""
    return {
        "status": "healthy ✅",
        "api_stats": get_stats(),
        "memory_stats": memory.get_stats()
    }
