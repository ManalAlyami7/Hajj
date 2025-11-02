import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from openai import OpenAI
import openai
from datetime import datetime
import pytz
import io
import re
from typing import Optional, Dict, List
from deep_translator import GoogleTranslator
from typing_extensions import TypedDict
import urllib.parse
from pydantic import BaseModel, Field



# LangGraph imports
from langgraph.graph import StateGraph, START, END
from langchain_openai import ChatOpenAI


import json
import os

def load_chat_memory():
    """Load chat history from file if it exists."""
    if os.path.exists("chat_history.json"):
        with open("chat_history.json", "r", encoding="utf-8") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return []
    return []

def save_chat_memory():
    """Save chat history to file."""
    with open("chat_history.json", "w", encoding="utf-8") as f:
        json.dump(st.session_state.chat_memory, f, ensure_ascii=False, indent=2)

if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = load_chat_memory()
if st.button("🎙️ Go to Voice Assistant"):
        # Set URL to main page
    st.markdown(f'<meta http-equiv="refresh" content="0; url=/" />', unsafe_allow_html=True)
# -----------------------------
# TRANSLATIONS DICTIONARY (unchanged)

llm = ChatOpenAI(
    model_name="gpt-5-nano",
    temperature=0,
    openai_api_key=st.secrets["key"])
class IntentSchema(BaseModel):
    intent: str = Field(description="One of: GREETING, DATABASE, GENERAL_HAJJ")
    confidence: float = Field(description="Confidence score between 0 and 1")

class GreetingSchema(BaseModel):
    greeting_text: str = Field(description="Friendly greeting to the user in natural language.")
    tone: str = Field(description="The tone of the greeting, e.g., 'warm', 'formal', 'friendly'.")
    language: str = Field(description="Language used in the greeting, e.g., 'English' or 'Arabic'.")
    contains_emoji: bool = Field(description="True if the greeting contains emojis.")
class GeneralAnswerSchema(BaseModel):
    answer: str = Field(description="A concise, factual response to the user's general Hajj-related question.")
    topic: str = Field(description="The detected topic or category, e.g. 'visa', 'documents', 'transport', 'rituals'.")
    confidence: float = Field(description="Confidence level in understanding the question, from 0 to 1.")
class SQLResult(BaseModel):
    sql_query: str = Field(description="The generated SQL SELECT query.")
    reasoning: str = Field(description="Short reasoning for how the SQL matches the user question.")
    is_valid: bool = Field(description="True if the SQL is executable, False if the user input was too vague.")


class SummarySchema(BaseModel):
    """Schema for structured summarization output."""
    summary: str = Field(..., description="Concise summary of the SQL query results.")
    is_valid: bool = Field(..., description="Whether summarization was successful and consistent with the data.")
    reasoning: str = Field(..., description="Short explanation or reasoning behind the summary.")


# -----------------------------
TRANSLATIONS = {
    "English": {
        # (same translations as you had; truncated in this snippet to keep file short)
        "page_title": "Hajj Chatbot",
        "main_title": "Hajj Data Intelligence",
        "subtitle": "Ask anything about Hajj companies worldwide • AI-powered • Real-time data",
        "assistant_title": "🕋 Hajj Assistant",
        "assistant_subtitle": "Your AI-powered guide",
        "language_title": "🌐 language",
        "stats_title": "📊 Live Statistics",
        "examples_title": "💡 Quick Examples",
        "clear_chat": "🧹 Clear Chat History",
        "features_title": "ℹ️ Features",
        "total_agencies": "Total Agencies",
        "authorized": "Authorized",
        "countries": "Countries",
        "cities": "Cities",
        "ex_all_auth": "🔍 All authorized companies",
        "ex_all_auth_q": "Show me all authorized Hajj companies",
        "ex_saudi": "🇸🇦 Companies in Saudi Arabia",
        "ex_saudi_q": "List companies in Saudi Arabia",
        "ex_by_country": "📊 Agencies by country",
        "ex_by_country_q": "How many agencies are in each country?",
        "ex_emails": "📧 Companies with emails",
        "ex_emails_q": "Find companies with email addresses",
        "feat_ai": "AI-Powered Search",
        "feat_ai_desc": "Natural language queries",
        "feat_multilingual": "Multilingual",
        "feat_multilingual_desc": "Arabic & English support",
        "feat_viz": "Data Visualization",
        "feat_viz_desc": "Interactive tables",
        "feat_secure": "Secure",
        "feat_secure_desc": "SQL injection protection",
        "welcome_msg": "Welcome! 👋\n\nI'm your Hajj Data Assistant. Ask me anything about Hajj companies, locations, or authorization status!",
        "input_placeholder": "Ask your question here... 💬",
        "thinking": "🤔 Analyzing your question...",
        "searching": "🔍 Searching database...",
        "generating_sql": "🧠 Generating SQL query...",
        "executing_query": "💾 Executing query...",
        "found_results": "✅ Found {count} results",
        "sql_generated": "✅ SQL query generated",
        "query_failed": "❌ Query failed",
        "results_badge": "📊 {count} Results",
        "authorized_badge": "🔒 {count} Authorized",
        "executed_caption": "Executed in database • {count} rows returned",
        "greeting": "Hello! 👋\n\nI'm doing great, thank you! I'm here to help you find information about Hajj companies. What would you like to know?",
        "no_results": "No results found. Try rephrasing the question or broadening the search.",
        "sql_error": "A database error occurred. Try rephrasing your question.",
        "intent_error": "⚠️ Intent detection issue",
        "general_error": "Sorry, I encountered an error.",
        "hint_rephrase": "💡 Try rephrasing your question or use different keywords",
        "no_sql": "Sorry, I couldn't convert that to a safe SQL query. Try rephrasing or ask for general results.",
    },
    "العربية": {
        # (Arabic translations likewise — keep the same as your original)
        "page_title": "روبوت الحج",
        "main_title": "معلومات بيانات الحج الذكية",
        "subtitle": "اسأل عن شركات الحج حول العالم • مدعوم بالذكاء الاصطناعي • بيانات فورية",
        "assistant_title": "🕋 مساعد الحج",
        "assistant_subtitle": "دليلك الذكي المدعوم بالذكاء الاصطناعي",
        "language_title": "🌐 اللغة",
        "stats_title": "📊 الإحصائيات المباشرة",
        "examples_title": "💡 أمثلة سريعة",
        "clear_chat": "🧹 مسح سجل المحادثة",
        "features_title": "ℹ️ المميزات",
        "total_agencies": "إجمالي الشركات",
        "authorized": "المعتمدة",
        "countries": "الدول",
        "cities": "المدن",
        "ex_all_auth": "🔍 جميع الشركات المعتمدة",
        "ex_all_auth_q": "أظهر لي جميع شركات الحج المعتمدة",
        "ex_saudi": "🇸🇦 شركات في السعودية",
        "ex_saudi_q": "اعرض الشركات في المملكة العربية السعودية",
        "ex_by_country": "📊 الشركات حسب الدولة",
        "ex_by_country_q": "كم عدد الشركات في كل دولة؟",
        "ex_emails": "📧 شركات لديها بريد إلكتروني",
        "ex_emails_q": "ابحث عن الشركات التي لديها بريد إلكتروني",
        "feat_ai": "بحث ذكي",
        "feat_ai_desc": "استعلامات باللغة الطبيعية",
        "feat_multilingual": "متعدد اللغات",
        "feat_multilingual_desc": "دعم العربية والإنجليزية",
        "feat_viz": "تصور البيانات",
        "feat_viz_desc": "جداول تفاعلية",
        "feat_export": "تصدير النتائج",
        "feat_secure": "آمن",
        "feat_secure_desc": "حماية من هجمات SQL",
        "welcome_msg": "السلام عليكم ورحمة الله وبركاته! 🌙\n\nأهلاً بك في مساعد معلومات الحج الذكي. كيف يمكنني مساعدتك اليوم؟",
        "input_placeholder": "اكتب سؤالك هنا... 💬",
        "thinking": "🤔 جارٍ تحليل سؤالك...",
        "searching": "🔍 جارٍ البحث في قاعدة البيانات...",
        "generating_sql": "🧠 جارٍ إنشاء استعلام SQL...",
        "executing_query": "💾 جارٍ تنفيذ الاستعلام...",
        "found_results": "✅ تم العثور على {count} نتيجة",
        "sql_generated": "✅ تم إنشاء استعلام SQL",
        "query_failed": "❌ فشل الاستعلام",
        "results_badge": "📊 {count} نتيجة",
        "authorized_badge": "🔒 {count} معتمدة",
        "view_sql": "🔍 عرض استعلام SQL",
        "executed_caption": "تم التنفيذ في قاعدة البيانات • {count} صف تم إرجاعه",
        "greeting": "وعليكم السلام ورحمة الله وبركاته! 🌙\n\nالحمد لله، أنا بخير! أنا هنا لمساعدتك في العثور على معلومات شركات الحج. كيف يمكنني مساعدتك؟",
        "no_results": "لم يتم العثور على نتائج. حاول إعادة صياغة السؤال أو توسيع نطاق البحث.",
        "sql_error": "حدث خطأ في قاعدة البيانات. حاول إعادة صياغة سؤالك.",
        "intent_error": "⚠️ مشكلة في اكتشاف النية",
        "general_error": "عذراً، واجهت مشكلة في الإجابة.",
        "hint_rephrase": "💡 حاول إعادة صياغة سؤالك أو استخدم كلمات مفتاحية مختلفة",
        "no_sql": "عذراً، لا يمكن تحويل هذا الطلب إلى استعلام SQL آمن. حاول إعادة صياغة السؤال.",
    }
}

if "openai_client" not in st.session_state:
    try:
        st.session_state.openai_client = OpenAI(api_key=st.secrets["OPENAI_API_KEY"])
    except:
        st.session_state.openai_client = None


def t(key: str, lang: str = "English", **kwargs) -> str:
    """Get translation for key in specified new_language with optional formatting"""
    text = TRANSLATIONS.get(lang, TRANSLATIONS["English"]).get(key, key)
    if kwargs:
        return text.format(**kwargs)
    return text

    

def get_current_time() -> float:
    """Get current timestamp in Riyadh timezone"""
    riyadh_tz = pytz.timezone('Asia/Riyadh')
    return datetime.now(riyadh_tz).timestamp()

def format_time(timestamp: float) -> str:
    """Format timestamp to readable time in Riyadh timezone"""
    riyadh_tz = pytz.timezone('Asia/Riyadh')
    dt = datetime.fromtimestamp(timestamp, riyadh_tz)
    return dt.strftime("%I:%M %p")

def is_vague_input(user_input):
    """Detect if the user input is too vague for SQL generation."""
    keywords = ["agency", "company", "office", "وكالة", "شركة"]
    stripped = user_input.lower().strip()
    # Treat as vague if it contains only generic words or is too short
    if len(stripped.split()) < 3 and any(k in stripped for k in keywords):
        return True
    return False

def tts_to_bytesio(text, voice="alloy"):
    """
    Returns BytesIO of TTS audio ready for st.audio
    """
    try:
        if "openai_client" not in st.session_state or st.session_state.openai_client is None:
            if "key" in st.secrets:
                st.session_state.openai_client = ChatOpenAI(api_key=st.secrets["key"])
            else:
                st.error("❌ OpenAI API key missing")
                return None
        
        client = st.session_state.openai_client

        # Force voice to supported value
        if voice not in ["nova", "shimmer", "echo", "onyx", "fable", "alloy", "ash", "sage", "coral"]:
            voice = "alloy"

        response = client.audio.speech.create(
            model="tts-1",
            voice=voice,
            input=text,
            response_format="mp3"
        )
        
        audio_bytes = io.BytesIO(response.content)
        audio_bytes.seek(0)
        return audio_bytes
        
    except Exception as e:
        st.error(f"❌ TTS Error: {e}")
        return None

def fuzzy_normalize(text: str) -> str:
    """Normalize text for fuzzy matching"""
    # Remove diacritics and special characters
    import unicodedata
    normalized = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    # Convert to lowercase and remove extra spaces
    normalized = ' '.join(normalized.lower().split())
    return normalized


def heuristic_sql_fallback(question: str) -> Optional[str]:
    q = question.lower().strip()

    # Detect if the user input looks like an agency, hotel, or company name
    if len(q.split()) <= 6 and not any(w in q for w in ["all", "list", "show", "count", "how many"]):
        return f"""
        SELECT DISTINCT hajj_company_en, hajj_company_ar, formatted_address, city, country, email, contact_Info, rating_reviews, is_authorized
        FROM agencies
        WHERE LOWER(hajj_company_en) LIKE '%{q}%'
           OR LOWER(hajj_company_ar) LIKE '%{q}%'
           OR LOWER(formatted_address) LIKE '%{q}%'
           OR LOWER(city) LIKE '%{q}%'
        LIMIT 50
        """

    # Common user intents
    if "authorized" in q or "معتمدة" in q:
        return "SELECT * FROM agencies WHERE is_authorized = 'Yes' LIMIT 100"

    if "unauthorized" in q or "غير معتمدة" in q:
        return "SELECT * FROM agencies WHERE is_authorized = 'No' LIMIT 100"

    if "email" in q:
        return "SELECT * FROM agencies WHERE email IS NOT NULL AND email != '' LIMIT 100"

    if "country" in q or "countries" in q or "دول" in q:
        if "how many" in q or "كم" in q:
            return "SELECT COUNT(DISTINCT country) FROM agencies"
        return "SELECT DISTINCT country FROM agencies LIMIT 100"

    if "city" in q or "cities" in q or "مدن" in q:
        if "how many" in q or "كم" in q:
            return "SELECT COUNT(DISTINCT city) FROM agencies"
        return "SELECT DISTINCT city FROM agencies LIMIT 100"

    if any(word in q for word in ["all", "show", "list", "عرض", "قائمة"]):
        return "SELECT * FROM agencies LIMIT 100"

    return None


def build_chat_context(limit: int = 6) -> List[Dict[str, str]]:
    """Build chat context from recent messages"""
    context = [{"role": "system", "content": """You are a helpful assistant specializing in Hajj-related information.
    - Be concise and accurate
    - Use Arabic when user asks in Arabic
    - Stick to factual information
    - Avoid religious rulings or fatwa
    - Focus on practical information"""}]
    
    recent = st.session_state.chat_memory[-limit:] if len(st.session_state.chat_memory) > limit else st.session_state.chat_memory
    
    for msg in recent:
        if "dataframe" in msg:  # Skip messages with data results
            continue
        context.append({
            "role": msg["role"],
            "content": msg["content"]
        })
    
    return context
# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Hajj Chatbot",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Custom CSS
# -----------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', 'Cairo', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
        max-width: 1400px;
    }
    
    .header-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        text-align: center;
        animation: fadeInDown 0.6s ease-out;
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .subtitle {
        color: #666;
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    .stChatMessage {
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px);
        border-radius: 18px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: transform 0.2s ease;
    }
    
    .stChatMessage:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.12) !important;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #2c5f8d 100%);
    }
    
    [data-testid="stSidebar"] .element-container {
        color: white;
    }
    
    [data-testid="stSidebar"] h3 {
        color: white !important;
        font-weight: 600;
        margin-top: 1rem;
    }
    
    .stat-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        margin: 0.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.95rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton button {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        text-align: left !important;
    }
    
    .stButton button:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        transform: translateX(8px);
        border-color: rgba(255, 255, 255, 0.5) !important;
    }
    
    .stRadio > div {
        background: rgba(255, 255, 255, 0.1);
        padding: 0.5rem;
        border-radius: 10px;
    }
    
    .stRadio label {
        color: white !important;
    }
    
    .stDownloadButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stDownloadButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    .streamlit-expanderHeader {
        background: rgba(102, 126, 234, 0.1);
        border-radius: 10px;
        font-weight: 600;
        color: #667eea;
    }
    
    .caption {
        color: #999;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    
    .badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 20px;
        font-size: 0.85rem;
        font-weight: 600;
        margin: 0.25rem;
    }
    
    .badge-success {
        background: linear-gradient(135deg, #11998e 0%, #38ef7d 100%);
        color: white;
    }
    
    .badge-info {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .rtl {
        direction: rtl;
        text-align: right;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.3);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.5);
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Utility Functions
# -----------------------------
def sanitize_sql(sql_query: str) -> Optional[str]:
    """Reject dangerous queries and ensure SELECT only"""
    if not sql_query:
        return None
    dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'EXEC', 'EXECUTE', 'TRUNCATE']
    upper = sql_query.upper()
    for kw in dangerous:
        if kw in upper:
            return None
    if not sql_query.strip().upper().startswith("SELECT"):
        return None
    return sql_query.strip().rstrip(';')

def extract_sql_from_response(response_text: str) -> Optional[str]:
    """Extract SQL query from LLM response"""
    if not response_text:
        return None

    
    # Try code blocks first
    code_block_pattern = r'```(?:sql)?\s*(SELECT[\s\S]*?)```'
    match = re.search(code_block_pattern, response_text, re.IGNORECASE)
    if match:
        return match.group(1).strip().rstrip(';')
    
    # Try plain SELECT statement
    select_pattern = r'(SELECT\s+.*?(?:;|$))'
    match = re.search(select_pattern, response_text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip().rstrip(';')
    
    if "NO_SQL" in response_text:
        return "NO_SQL"
    
    return None
cache = {}

# -----------------------------
# Database & OpenAI Setup
# -----------------------------
@st.cache_resource
def get_database_engine():
    """Initialize database engine"""
    try:
        return create_engine("sqlite:///hajj_companies.db")
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        st.stop()

engine = get_database_engine()

@st.cache_resource
def get_openai_client():
    """Initialize OpenAI client"""
    api_key = st.secrets.get("key", None)
    if not api_key:
        st.warning("⚠️ OpenAI API key missing in Streamlit secrets")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()

@st.cache_data(ttl=300)


def get_db_stats():
    """Fetch database statistics with normalization for multilingual names"""
    try:
        with engine.connect() as conn:
            return {
                'total': pd.read_sql(text("SELECT COUNT(DISTINCT hajj_company_en) AS count FROM agencies"), conn).iloc[0]['count'],
                'authorized':  pd.read_sql(text("SELECT COUNT(DISTINCT hajj_company_en) AS count FROM agencies WHERE is_authorized = 'Yes'"), conn).iloc[0]['count'],
                'countries': pd.read_sql(text("SELECT COUNT(DISTINCT country) AS count FROM agencies"), conn).iloc[0]['count'],
                'cities': pd.read_sql(text("SELECT COUNT(DISTINCT city) AS count FROM agencies"), conn).iloc[0]['count']
            }

    except Exception as e:
        print("Error:", e)
        return {'total': 0, 'authorized': 0, 'countries': 0, 'cities': 0}

# -----------------------------
# Session State Initialization
# -----------------------------
if "new_language" not in st.session_state:
    st.session_state.new_language = "English"
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = []
if "last_result_df" not in st.session_state:
    st.session_state.last_result_df = None
if "selected_question" not in st.session_state:
    st.session_state.selected_question = None

# Sidebar simplified (kept core interactions)
with st.sidebar:
    st.markdown(f"<h2 style='text-align: center; color: white; margin-bottom: 0;'>{t('assistant_title', st.session_state.new_language)}</h2>", unsafe_allow_html=True)
    st.markdown(f"<p style='text-align: center; color: rgba(255,255,255,0.7); font-size: 0.9rem;'>{t('assistant_subtitle', st.session_state.new_language)}</p>", unsafe_allow_html=True)
    st.markdown("---")

    # new_language Toggle
    st.markdown(f"<h3>{t('language_title', st.session_state.new_language)}</h3>", unsafe_allow_html=True)
    new_language_choice = st.radio(
        "",
        ["English 🇬🇧", "العربية 🇸🇦"],
        index=0 if st.session_state.new_language == "English" else 1,
        horizontal=True,
        label_visibility="collapsed",
        key="lang_radio"
    )
    
    # Handle new_language change
    new_language = "العربية" if "العربية" in new_language_choice else "English"
    if new_language != st.session_state.new_language:
        st.session_state.new_language = new_language
        if len(st.session_state.chat_memory) == 0 or (len(st.session_state.chat_memory) == 1 and st.session_state.chat_memory[0]["role"] == "assistant"):
            st.session_state.chat_memory = [{
                "role": "assistant",
                "content": t("welcome_msg", st.session_state.new_language),
                "timestamp": get_current_time()
            }]
        st.rerun()

    st.markdown("---")
    
    # Database Statistics
    st.markdown(f"<h3>{t('stats_title', st.session_state.new_language)}</h3>", unsafe_allow_html=True)
    stats = get_db_stats()
    stat_items = [
        ("total", "total_agencies", "🏢"),
        ("authorized", "authorized", "✅"),
        ("countries", "countries", "🌍"),
        ("cities", "cities", "🏙️")
    ]
    
    for key, label_key, icon in stat_items:
        html_card = f"""
        <div class="stat-card">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>
            <div class="stat-number">{stats.get(key, 0):,}</div>
            <div class="stat-label">{t(label_key, st.session_state.new_language)}</div>
        </div>
        """
        st.markdown(html_card, unsafe_allow_html=True)

    st.markdown("---")
    
    # Example Questions
    st.markdown(f"<h3>{t('examples_title', st.session_state.new_language)}</h3>", unsafe_allow_html=True)
    example_questions = [
        ("ex_all_auth", "ex_all_auth_q"),
        ("ex_saudi", "ex_saudi_q"),
        ("ex_by_country", "ex_by_country_q"),
        ("ex_emails", "ex_emails_q"),
    ]
    
    for i, (display_key, question_key) in enumerate(example_questions):
     if st.button(t(display_key, st.session_state.new_language), key=f"example_{i}", use_container_width=True):
        st.session_state.selected_question = t(question_key, st.session_state.new_language)


    st.markdown("---")
    
    # Clear Chat Button
    if st.button(t("clear_chat", st.session_state.new_language), use_container_width=True, type="primary"):
        st.session_state.chat_memory = [{
            "role": "assistant",
            "content": t("welcome_msg", st.session_state.new_language),
            "timestamp": get_current_time()
        }]
        st.session_state.last_result_df = None
        save_chat_memory()
        st.rerun()

    st.markdown("---")
    
    # Features Section
    st.markdown(f"<h3>{t('features_title', st.session_state.new_language)}</h3>", unsafe_allow_html=True)
    st.markdown(f"""
    <div style='color: rgba(255,255,255,0.9); font-size: 0.9rem; line-height: 1.8;'>
        <p>✨ <b>{t('feat_ai', st.session_state.new_language)}</b><br/>{t('feat_ai_desc', st.session_state.new_language)}</p>
        <p>🌍 <b>{t('feat_multilingual', st.session_state.new_language)}</b><br/>{t('feat_multilingual_desc', st.session_state.new_language)}</p>
        <p>📊 <b>{t('feat_viz', st.session_state.new_language)}</b><br/>{t('feat_viz_desc', st.session_state.new_language)}</p>
        <p>💾 <b>{t('feat_export', st.session_state.new_language)}</b><br/>{t('feat_export_desc', st.session_state.new_language)}</p>
        <p>🔒 <b>{t('feat_secure', st.session_state.new_language)}</b><br/>{t('feat_secure_desc', st.session_state.new_language)}</p>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------

# -----------------------------------------------
# 🕋 Header
# -----------------------------------------------
st.markdown(f"""
<div class="header-container{' rtl' if st.session_state.new_language == 'العربية' else ''}">
    <h1>
        🕋 <span class="main-title">{t('main_title', st.session_state.new_language)}</span>
    </h1>
    <p class="subtitle">{t('subtitle', st.session_state.new_language)}</p>
</div>
""", unsafe_allow_html=True)


# -----------------------------------------------
# 💬 Chat History Display
# -----------------------------------------------
for idx, msg in enumerate(st.session_state.chat_memory):
    role = msg.get("role", "assistant")
    avatar = "🕋" if role == "assistant" else "👤"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg.get("content", ""))
        if msg.get("timestamp"):
            st.markdown(
                f"<div style='color: #777; font-size:0.8rem'>🕐 {format_time(msg['timestamp'])}</div>",
                unsafe_allow_html=True
            )

# -----------------------------------------------
# 💬 Chat Input + Auto-Send Example Questions
# -----------------------------------------------
placeholder_text = (
    "اكتب سؤالك هنا... 💬" if st.session_state.new_language == "العربية"
    else "Ask your question here... 💬"
)

# Initialize state variables
if "user_input" not in st.session_state:
    st.session_state.user_input = ""
if "selected_question" not in st.session_state:
    st.session_state.selected_question = ""
if "auto_submit" not in st.session_state:
    st.session_state.auto_submit = False

# Handle normal user typing
user_input = st.chat_input(placeholder_text)

# If user typed something, store it
if user_input:
    st.session_state.user_input = user_input

# If user clicked an example — trigger auto-send
if st.session_state.selected_question:
    st.session_state.user_input = st.session_state.selected_question
    st.session_state.auto_submit = True
    st.session_state.selected_question = None  # reset after use

# Send automatically if triggered by example
if st.session_state.auto_submit and st.session_state.user_input:
    user_input = st.session_state.user_input
    st.session_state.auto_submit = False  # reset after sending
else:
    # Normal case — wait for user to press Enter
    user_input = st.session_state.user_input or user_input

# -----------------------------
# LangGraph State schema
# -----------------------------
class GraphState(TypedDict, total=False):
    user_input: str
    language: str
    intent: str
    is_vague: bool
    sql_query: Optional[str]
    raw_sql_text: Optional[str]
    sql_error: Optional[str]
    result_rows: Optional[List[Dict]]
    columns: Optional[List[str]]
    row_count: Optional[int]
    summary: Optional[str]
    greeting_text: Optional[str]
    general_answer: Optional[str]

# -----------------------------
# Node implementations
# Each node accepts the shared 'state' dict and returns a partial dict update.
# -----------------------------
def node_detect_intent(state: GraphState) -> dict:
    user_input = state.get("user_input", "")
    language = state.get("language", "English")
    # Heuristics quick check
    is_arabic = any("\u0600" <= ch <= "\u06FF" for ch in user_input)
    state_update = {"is_vague": is_vague_input(user_input)}
    intent = None
    structured_llm = client.with_structured_output(IntentSchema)



    # Build intent prompt (kept consistent with previous prompt)
    intent_prompt = f"""
You are a fraud-prevention assistant for Hajj pilgrims. Classify this message into ONE of three categories:

1️⃣ GREETING: greetings like hello, hi, how are you, salam, السلام عليكم, مرحبا. 
   - No specific agency information is provided.
   - User just wants to chat or start conversation.

2️⃣ DATABASE: questions about verifying specific Hajj agencies, checking authorization, company details, locations, contacts, etc.
   - User mentions agency names, locations, or asks for authorized agencies.

3️⃣ GENERAL_HAJJ: general Hajj-related questions (rituals, requirements, documents, safety, procedures).

CRITICAL CONTEXT:
- 415 fake Hajj offices closed in 2025
- 269,000+ unauthorized pilgrims stopped
- Mission: prevent fraud, protect pilgrims
- Always emphasize verification and authorization for DATABASE questions

Message: {user_input}
language: {language}{" (Arabic)" if is_arabic else " (English)"}

Return JSON ONLY in this format:
{{
  "intent": "GREETING" | "DATABASE" | "GENERAL_HAJJ",
  "confidence": float (0.0–1.0)
}}
"""
    try:
        resp = structured_llm.chat.completions.create(
            model="gpt-4o-mini",
            messages=[{"role":"system","content":"You classify intents. Respond with one word."},
                      {"role":"user","content": intent_prompt}, *build_chat_context()],
            temperature=0,
            max_tokens=8
        )
        candidate = resp.choices[0].message.content.strip().upper()
        if candidate in ("GREETING", "DATABASE", "GENERAL_HAJJ"):
             intent = resp.intent.upper()
             confidence = float(resp.confidence)
    except Exception as e:
        # fallback heuristics
        st.warning(f"⚠️ Intent detection error: {e}")
       
    state_update["intent"] = intent
    state_update["confidence"] = confidence  # Placeholder for confidence
    return state_update

def node_respond_greeting(state: GraphState) -> dict:
    user_input = state.get("user_input", "")
    lang = state.get("language", "English")
    is_arabic = lang == "العربية" or any("\u0600" <= ch <= "\u06FF" for ch in user_input)
    structured_llm = client.with_structured_output(GreetingSchema)

    greeting_prompt = {
        "role": "system",
        "content": """You are a friendly Hajj assistant. Generate a warm, natural greeting that:
1. Acknowledges the user's greeting
2. Expresses willingness to help
3. Mentions you can help with Hajj company information
4. Keeps response under 3 sentences
5. Uses emojis appropriately""" + (" Respond in Arabic." if is_arabic else " Respond in English.")
    }
    try:
        greeting_response = structured_llm.invoke(
            [greeting_prompt, {"role":"user","content": user_input}, *build_chat_context()],
            max_tokens=150
        )
        greeting_text = greeting_response.answer.strip()
    except Exception:
        greeting_text = t("greeting", "العربية") if is_arabic else t("greeting", "English")

    return {"greeting_text": greeting_text}

def node_respond_general(state: GraphState) -> dict:
    # Use LLM to answer general Hajj questions (non-database)
    user_input = state.get("user_input", "")

    structured_llm = llm.with_structured_output(GeneralAnswerSchema)
    try:
        context = [{"role":"system","content":"You are a helpful assistant specialized in Hajj information. Be concise and factual."},
                   {"role":"user","content": user_input}, *build_chat_context()]
        resp = structured_llm.invoke(context, max_tokens=400)
        answer = resp.choices[0].message.content.strip()
    except Exception as e:
        answer = t("general_error", state.get("language", "English"))
    return {"general_answer": answer}

def node_generate_sql(state: GraphState) -> dict:
    user_input = state.get("user_input", "")
    language = state.get("language", "English")
    normalized_input = fuzzy_normalize(user_input)
    structured_llm = llm.with_structured_output(SQLResult)

    sql_prompt = f"""
    You are a multilingual SQL fraud-prevention expert protecting Hajj pilgrims.

    🎯 MISSION: Generate an SQL query for database analysis on Hajj agencies.
    Do NOT generalize to world data — always query from the table 'agencies'.

    TABLE STRUCTURE:
    - hajj_company_ar
    - hajj_company_en
    - formatted_address
    - city
    - country
    - email
    - contact_Info
    - rating_reviews
    - is_authorized ('Yes' or 'No')

    CURRENT LANGUAGE: {language}

    USER QUESTION (original): {user_input}
    NORMALIZED VERSION: {normalized_input}
    --------------------------------------------
    🔍 LANGUAGE DETECTION RULES:
    1. Detect if the user's question is in Arabic or English.
    2. Respond with SQL query **only**, no text.
    3. Keep text fragments (LIKE clauses) in both Arabic and English for robustness.
    --------------------------------------------

    🚨 CRITICAL DATABASE CONTEXT:
    - 415 fake offices closed in 2025
    - 269,000+ unauthorized pilgrims stopped
    - Database mixes Arabic, English, and typos.
    - Always focus on verifying **authorization** and **agency location**, not world geography.

    --------------------------------------------
    📘 QUERY INTERPRETATION RULES:

    1. "Authorized" → add `AND is_authorized = 'Yes'`
    2. "Is X authorized?" → check `is_authorized` for company name
    3. "Number of ..." or "How many ..." → use `SELECT COUNT(*)`
    4. "Countries" or "number of countries" → use:
    - `SELECT COUNT(DISTINCT country)` if asking how many
    - `SELECT DISTINCT country` if asking for list
    - Always based on agencies table
    5. "Cities" or "number of cities" → same logic as above but for `city`
    6. Never assume or add “Saudi Arabia” unless mentioned explicitly.
    7. When user asks about “countries that have agencies” → use `DISTINCT country` from `agencies`
    8. Always return agency-related data only, not external or world data.
    9    --------------------------------------------

    🌍 LOCATION MATCHING PATTERNS:
    Use flexible LIKE and LOWER() conditions for cities/countries.
    Handle Arabic, English, and typos.

    Mecca → (city LIKE '%مكة%' OR LOWER(city) LIKE '%mecca%' OR LOWER(city) LIKE '%makkah%' OR LOWER(city) LIKE '%makka%')
    Medina → (city LIKE '%المدينة%' OR LOWER(city) LIKE '%medina%' OR LOWER(city) LIKE '%madinah%')
    Riyadh → (city LIKE '%الرياض%' OR LOWER(city) LIKE '%riyadh%' OR LOWER(city) LIKE '%ar riyadh%')
    Saudi Arabia → (country LIKE '%السعودية%' OR LOWER(country) LIKE '%saudi%' OR country LIKE '%المملكة%')
    Pakistan → (country LIKE '%باكستان%' OR LOWER(country) LIKE '%pakistan%' OR country LIKE '%پاکستان%')
    Egypt → (country LIKE '%مصر%' OR LOWER(country) LIKE '%egypt%')

    --------------------------------------------
    🏁 OUTPUT RULES:
    - Output **only** one valid SQL SELECT query.
    - If no logical SQL can be formed → output `NO_SQL`
    - Always include LIMIT 100 unless COUNT or DISTINCT is used.

    --------------------------------------------
    ✅ EXAMPLES:
📘 QUERY INTERPRETATION RULES:
...
⚙️ For company name searches:
Always normalize and deduplicate company names.
Use LOWER(TRIM()) and SELECT DISTINCT to avoid case duplicates.


    Q: "هل شركة الهدى معتمدة؟"
    → ELECT DISTINCT hajj_company_en, hajj_company_ar, formatted_address, city, country, email, contact_Info, rating_reviews, is_authorized
FROM agencies
WHERE (LOWER(TRIM(hajj_company_en)) LIKE LOWER('%alhuda%')
   OR LOWER(TRIM(hajj_company_ar)) LIKE LOWER('%الهدى%'))
LIMIT 50;
    Q: "Authorized agencies in Makkah"
    → SELECT * FROM agencies WHERE is_authorized = 'Yes' AND (city LIKE '%مكة%' OR LOWER(city) LIKE '%mecca%' OR LOWER(city) LIKE '%makkah%') LIMIT 100;

    Q: "كم عدد الشركات في المدينة؟"
    → SELECT COUNT(*) FROM agencies WHERE (city LIKE '%المدينة%' OR LOWER(city) LIKE '%medina%' OR LOWER(city) LIKE '%madinah%');

    Q: "How many countries have agencies?"
    → SELECT COUNT(DISTINCT country) FROM agencies;

    Q: "List of countries that have agencies"
    → SELECT DISTINCT country FROM agencies LIMIT 100;

    Q: "Number of authorized countries"
    → SELECT COUNT(DISTINCT country) FROM agencies WHERE is_authorized = 'Yes';

    Q: "Countries with authorized agencies"
    → SELECT DISTINCT country FROM agencies WHERE is_authorized = 'Yes' LIMIT 100;

    Q: "Show all cities where agencies exist"
    → SELECT DISTINCT city FROM agencies LIMIT 100;
    """
    raw_sql = None
    try:
        sql_resp = structured_llm.invoke(
            [{"role":"system","content":"You output only a SELECT query or NO_SQL."},
                      {"role":"user","content": sql_prompt}, *build_chat_context()]
        )

       # Directly access parsed fields
        raw_sql = sql_resp.sql_query.strip()
        is_valid = sql_resp.is_valid
        reasoning = sql_resp.reasoning
        sql_query = extract_sql_from_response(raw_sql)
        if sql_query == "NO_SQL":
            sql_query = None

    except Exception as e:
        sql_query = None
        reasoning = f"Error: {e}"

    # Fallback if invalid or empty
    if not raw_sql or not sql_query or not is_valid:
        sql_query = heuristic_sql_fallback(user_input)
        reasoning = reasoning or "Fallback heuristic used due to invalid or vague input."

    sql_query = sanitize_sql(sql_query) if sql_query else None

    return {
        "sql_query": sql_query,
        "raw_sql_text": raw_sql if raw_sql else None,
        "is_valid": is_valid,
        "reasoning": reasoning
    }

def node_execute_sql(state: GraphState) -> dict:
    sql_query = state.get("sql_query")
    if not sql_query:
        return {"sql_error": "No SQL to execute."}
    try:
        with engine.connect() as conn:
            df = pd.read_sql(text(sql_query), conn)
            rows = df.to_dict(orient="records")
            cols = list(df.columns)
            rc = len(df)
            return {"result_rows": rows, "columns": cols, "row_count": rc}
    except Exception as e:
        return {"sql_error": str(e)}

def node_summarize_results(state: GraphState) -> dict:
    user_input = state.get("user_input", "")
    language = state.get("language", "English")
    row_count = int(state.get("row_count", 0) or 0)
    rows = state.get("result_rows", [])[:20]  # sample

    if row_count == 0:
        no_results_msg = t("no_results", language)
        return {"summary": no_results_msg}

    # Build summary prompt similar to your previous summary prompts
    sample_text = rows
    structured_llm = llm.with_structured_output(SummarySchema)
    summary_prompt = f"""
You are a multilingual fraud-prevention analyst for Hajj agencies.
Your task is to summarize SQL query results clearly and concisely in 
{'Arabic' if st.session_state.new_language == 'العربية' else 'English'}.

Context:
- User question: {user_input}
- Total rows returned: {row_count}
- Sample results: {sample_text}

INSTRUCTIONS:
1. Adapt the tone and structure to the user’s intent:
   - If the query lists *agencies*, summarize as bullet points with ✅/❌ authorization indicators.
   - If the query counts *countries, cities, or agencies*, give a numeric summary.
   - If it’s a location-based query (e.g., Makkah, Egypt), mention key countries or cities.
2. Keep it concise — 1–3 sentences or short bullets.
3. Avoid restating the full query. Focus on insights.
4. Use language consistent with the user’s input ({'Arabic' if st.session_state.new_language == 'العربية' else 'English'}).
5. When possible, highlight:
   - How many are authorized vs unauthorized
   - Notable countries or cities
   - Example agency names

OUTPUT STYLE:
- For agency results → numbered or bulleted list (up to 10)
- For counts → one clear sentence
- For locations → short analytical summary
- For emails or contacts → mention availability and samples 
- summarize based on what the user asked and highlight key insights

Examples:

🔹 **English (agencies example):**
✅ 10 agencies found related to “Al-Rahma”:
1. AL RAHMA HAJJ & UMRA TRAVEL AGENCY — Cairo, Egypt — ✅ Authorized  
2. Al Salam & Al Rahma Co. — Makkah, Saudi Arabia — ✅ Authorized  
3. Dar Al Rahma — Jeddah, Saudi Arabia — ❌ Not Authorized  
→ 7 of 10 agencies are authorized.

🔹 **Arabic (count example):**
تم العثور على **45 وكالة معتمدة** في المدينة المنورة.  
تعمل معظم الوكالات من **السعودية** و **مصر**، مع تقييمات عالية للخدمة.

🔹 **English (count example):**
There are 45 authorized agencies in Medina, mostly from Saudi Arabia and Egypt.

Now summarize the query results based on the above rules.
"""
    try:
        summ_resp = structured_llm.invoke(
            [{"role":"system","content":"You summarize data concisely."},
                      {"role":"user","content": summary_prompt}, *build_chat_context()],
          
            max_tokens=250
        )
        answer_text = summ_resp.summary.strip()
    except Exception:
        answer_text = f"📊 Found {row_count} matching records."

    return {"summary": answer_text}

# -----------------------------
# Build LangGraph graph
# -----------------------------
def build_stategraph():
    builder = StateGraph(GraphState)


    # Add nodes
    builder.add_node("detect_intent", node_detect_intent)
    builder.add_node("respond_greeting", node_respond_greeting)
    builder.add_node("respond_general", node_respond_general)
    builder.add_node("generate_sql", node_generate_sql)
    builder.add_node("execute_sql", node_execute_sql)
    builder.add_node("summarize_results", node_summarize_results)

    # Edges
    builder.add_edge(START, "detect_intent")

    # Based on detect_intent.intent return different next nodes.
    # We use add_conditional_edges - key extractor returns the intent string.
    def intent_key(state):
        # state here is the TypedDict; we return the matching mapping key
        return state.get("intent", "GENERAL_HAJJ")

    builder.add_conditional_edges("detect_intent", intent_key, {
        "GREETING": "respond_greeting",
        "GENERAL_HAJJ": "respond_general",
        "DATABASE": "generate_sql"
    })

    # Database chain
    builder.add_edge("generate_sql", "execute_sql")
    builder.add_edge("execute_sql", "summarize_results")
    builder.add_edge("summarize_results", END)

    # Other branches terminate
    builder.add_edge("respond_greeting", END)
    builder.add_edge("respond_general", END)

    graph = builder.compile()
    return graph

# Compile graph once and reuse
GRAPH = build_stategraph()

# -----------------------------
# Helper UI functions
# -----------------------------
def show_result_summary(df: pd.DataFrame) -> None:
    #for _, row in df.iterrows():
       # name = row.get("hajj_company_en", "Unknown Agency")
       # addr = row.get("formatted_address", "")
       # auth = row.get("is_authorized", "Unknown")

        # Create clickable Google Maps link
        #if addr:
           #maps_url = f"https://www.google.com/maps/search/?api=1&query={urllib.parse.quote(addr)}"
          #  st.markdown(f"**{name}**<br>📍 [{addr}]({maps_url})", unsafe_allow_html=True)
       # else:
           # st.markdown(f"**{name}**<br>📍 Address not available")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"<div style='display:inline-block;padding:6px;background:#667eea;color:white;border-radius:8px;'>📊 {len(df)} Results</div>", unsafe_allow_html=True)
    
    with col2:
        if "is_authorized" in df.columns:
            auth_count = len(df[df["is_authorized"] == "Yes"])
            st.markdown(f"<div style='display:inline-block;padding:6px;background:#38ef7d;color:white;border-radius:8px;'>🔒 {auth_count} Authorized</div>", unsafe_allow_html=True)




 
# -----------------------------
# Handle user input: invoke graph and present outputs
# -----------------------------
if user_input:
    # Append user message to chat
    st.session_state.chat_memory.append({
        "role": "user",
        "content": user_input,
        "timestamp": get_current_time()
    })
    save_chat_memory()


    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
        st.markdown(
            f"<div style='color: #777; font-size:0.8rem'>🕐 {format_time(get_current_time())}</div>",
            unsafe_allow_html=True
        )

    # Prepare initial state and invoke graph
    init_state: GraphState = {"user_input": user_input, "language": st.session_state.new_language}

    with st.chat_message("assistant", avatar="🕋"):
        # ✅ use spinner as context manager
        with st.spinner(f"{t('thinking', st.session_state.new_language)}..."):
            try:
                # Invoke the graph (synchronous). This returns the final state dict.
                final_state = GRAPH.invoke(init_state)
            except Exception as e:
                # If LangGraph runtime error
                err_msg = f"{t('general_error', st.session_state.new_language)} {e}"
                st.error(err_msg)
                st.session_state.chat_memory.append({
                    "role": "assistant",
                    "content": err_msg,
                    "timestamp": get_current_time()
                })
                save_chat_memory()

                final_state = {}

        # -----------------------------

        # GREETING section
        # -----------------------------
        if final_state.get("greeting_text"):
            greeting_text = final_state["greeting_text"]

            # Display the greeting text
            st.markdown(greeting_text)

            # Determine voice based on language
            voice = "alloy-ar" if st.session_state.new_language == "العربية" else "alloy"

            # Generate TTS audio
            audio_bytes = tts_to_bytesio(greeting_text, voice)

            # Play audio automatically if generated
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")

            # Optional button to replay the audio
            if st.button("🎙️ Listen again", key=f"tts_greet_{len(st.session_state.chat_memory)}"):
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")

            # Save message in chat memory
            st.session_state.chat_memory.append({
                "role": "assistant",
                "content": greeting_text,
                "timestamp": get_current_time()
            })
            save_chat_memory()


        # -----------------------------
        # GENERAL_HAJJ section
        # -----------------------------
        elif final_state.get("general_answer"):
            ans = final_state["general_answer"]
            st.markdown(ans)
            st.session_state.chat_memory.append({
                "role": "assistant",
                "content": ans,
                "timestamp": get_current_time()
            })
            save_chat_memory()


        # -----------------------------
        # DATABASE path outputs
        # -----------------------------
        elif final_state.get("summary") or final_state.get("result_rows") is not None:
            # Show summary
            summary = final_state.get("summary", "")
            st.markdown(summary)
                        # 🔊 تشغيل الصوت + زر السبيكر للملخص
            voice = "alloy-ar" if st.session_state.new_language == "العربية" else "alloy"
            audio_bytes = tts_to_bytesio(summary, voice)
            if audio_bytes:
                st.audio(audio_bytes, format="audio/mp3")
            if st.button("🎙️ Listen again", key=f"tts_summary_{len(st.session_state.chat_memory)}"):
                if audio_bytes:
                    st.audio(audio_bytes, format="audio/mp3")

            rows = final_state.get("result_rows", [])
            row_count = final_state.get("row_count", 0)
            sql_q = final_state.get("sql_query", "")

            # Convert to DataFrame for display/download if rows exist
            if rows:
                df = pd.DataFrame(rows)
                show_result_summary(df)

                st.session_state.chat_memory.append({
                    "role": "assistant",
                    "content": summary,
                    "dataframe": df,
                    "timestamp": get_current_time()
                })
                save_chat_memory()

                st.session_state.last_result_df = df
            else:
                # No data rows
                st.warning(summary)
                st.session_state.chat_memory.append({
                    "role": "assistant",
                    "content": summary,
                    "timestamp": get_current_time()
                })
                save_chat_memory()

        # -----------------------------
        # Fallback
        # -----------------------------
        else:
            fallback = t("general_error", st.session_state.new_language)
            st.error(fallback)
            st.session_state.chat_memory.append({
                "role": "assistant",
                "content": fallback,
                "timestamp": get_current_time()
            })
            save_chat_memory()
