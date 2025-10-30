import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from openai import OpenAI
from datetime import datetime
import pytz
import re
from typing import Optional, Dict, List
from deep_translator import GoogleTranslator

# -----------------------------
# TRANSLATIONS DICTIONARY
# -----------------------------
TRANSLATIONS = {
    "English": {
        # Header
        "page_title": "Hajj Chatbot",
        "main_title": "Hajj Data Intelligence",
        "subtitle": "Ask anything about Hajj companies worldwide • AI-powered • Real-time data",
        
        # Sidebar
        "assistant_title": "🕋 Hajj Assistant",
        "assistant_subtitle": "Your AI-powered guide",
        "language_title": "🌐 language",
        "stats_title": "📊 Live Statistics",
        "examples_title": "💡 Quick Examples",
        "clear_chat": "🧹 Clear Chat History",
        "features_title": "ℹ️ Features",
        
        # Stats
        "total_agencies": "Total Agencies",
        "authorized": "Authorized",
        "countries": "Countries",
        "cities": "Cities",
        
        # Examples
        "ex_all_auth": "🔍 All authorized companies",
        "ex_all_auth_q": "Show me all authorized Hajj companies",
        "ex_saudi": "🇸🇦 Companies in Saudi Arabia",
        "ex_saudi_q": "List companies in Saudi Arabia",
        "ex_by_country": "📊 Agencies by country",
        "ex_by_country_q": "How many agencies are in each country?",
        "ex_emails": "📧 Companies with emails",
        "ex_emails_q": "Find companies with email addresses",
        
        # Features
        "feat_ai": "AI-Powered Search",
        "feat_ai_desc": "Natural language queries",
        "feat_multilingual": "Multilingual",
        "feat_multilingual_desc": "Arabic & English support",
        "feat_viz": "Data Visualization",
        "feat_viz_desc": "Interactive tables",
        "feat_export": "Export Results",
        "feat_export_desc": "Download as CSV",
        "feat_secure": "Secure",
        "feat_secure_desc": "SQL injection protection",
        
        # Chat
        "welcome_msg": "Welcome! 👋\n\nI'm your Hajj Data Assistant. Ask me anything about Hajj companies, locations, or authorization status!",
        "input_placeholder": "Ask your question here... 💬",
        "thinking": "🤔 Analyzing your question...",
        "searching": "🔍 Searching database...",
        "generating_sql": "🧠 Generating SQL query...",
        "executing_query": "💾 Executing query...",
        "found_results": "✅ Found {count} results",
        "sql_generated": "✅ SQL query generated",
        "query_failed": "❌ Query failed",
        
        # Results
        "results_badge": "📊 {count} Results",
        "columns_badge": "✅ {count} Columns",
        "authorized_badge": "🔒 {count} Authorized",
        "download_csv": "📥 Download Results (CSV)",
        "view_sql": "🔍 View SQL Query",
        "executed_caption": "Executed in database • {count} rows returned",
        
        # Messages
        "greeting": "Hello! 👋\n\nI'm doing great, thank you! I'm here to help you find information about Hajj companies. What would you like to know?",
        "no_results": "No results found. Try rephrasing the question or broadening the search.",
        "sql_error": "A database error occurred. Try rephrasing your question.",
        "intent_error": "⚠️ Intent detection issue",
        "general_error": "Sorry, I encountered an error.",
        "hint_rephrase": "💡 Try rephrasing your question or use different keywords",
        "no_sql": "Sorry, I couldn't convert that to a safe SQL query. Try rephrasing or ask for general results.",
    },
    "العربية": {
        # Header
        "page_title": "روبوت الحج",
        "main_title": "معلومات بيانات الحج الذكية",
        "subtitle": "اسأل عن شركات الحج حول العالم • مدعوم بالذكاء الاصطناعي • بيانات فورية",
        
        # Sidebar
        "assistant_title": "🕋 مساعد الحج",
        "assistant_subtitle": "دليلك الذكي المدعوم بالذكاء الاصطناعي",
        "language_title": "🌐 اللغة",
        "stats_title": "📊 الإحصائيات المباشرة",
        "examples_title": "💡 أمثلة سريعة",
        "clear_chat": "🧹 مسح سجل المحادثة",
        "features_title": "ℹ️ المميزات",
        
        # Stats
        "total_agencies": "إجمالي الشركات",
        "authorized": "المعتمدة",
        "countries": "الدول",
        "cities": "المدن",
        
        # Examples
        "ex_all_auth": "🔍 جميع الشركات المعتمدة",
        "ex_all_auth_q": "أظهر لي جميع شركات الحج المعتمدة",
        "ex_saudi": "🇸🇦 شركات في السعودية",
        "ex_saudi_q": "اعرض الشركات في المملكة العربية السعودية",
        "ex_by_country": "📊 الشركات حسب الدولة",
        "ex_by_country_q": "كم عدد الشركات في كل دولة؟",
        "ex_emails": "📧 شركات لديها بريد إلكتروني",
        "ex_emails_q": "ابحث عن الشركات التي لديها بريد إلكتروني",
        
        # Features
        "feat_ai": "بحث ذكي",
        "feat_ai_desc": "استعلامات باللغة الطبيعية",
        "feat_multilingual": "متعدد اللغات",
        "feat_multilingual_desc": "دعم العربية والإنجليزية",
        "feat_viz": "تصور البيانات",
        "feat_viz_desc": "جداول تفاعلية",
        "feat_export": "تصدير النتائج",
        "feat_export_desc": "تحميل بصيغة CSV",
        "feat_secure": "آمن",
        "feat_secure_desc": "حماية من هجمات SQL",
        
        # Chat
        "welcome_msg": "السلام عليكم ورحمة الله وبركاته! 🌙\n\nأهلاً بك في مساعد معلومات الحج الذكي. كيف يمكنني مساعدتك اليوم؟",
        "input_placeholder": "اكتب سؤالك هنا... 💬",
        "thinking": "🤔 جارٍ تحليل سؤالك...",
        "searching": "🔍 جارٍ البحث في قاعدة البيانات...",
        "generating_sql": "🧠 جارٍ إنشاء استعلام SQL...",
        "executing_query": "💾 جارٍ تنفيذ الاستعلام...",
        "found_results": "✅ تم العثور على {count} نتيجة",
        "sql_generated": "✅ تم إنشاء استعلام SQL",
        "query_failed": "❌ فشل الاستعلام",
        
        # Results
        "results_badge": "📊 {count} نتيجة",
        "columns_badge": "✅ {count} عمود",
        "authorized_badge": "🔒 {count} معتمدة",
        "download_csv": "📥 تحميل النتائج (CSV)",
        "view_sql": "🔍 عرض استعلام SQL",
        "executed_caption": "تم التنفيذ في قاعدة البيانات • {count} صف تم إرجاعه",
        
        # Messages
        "greeting": "وعليكم السلام ورحمة الله وبركاته! 🌙\n\nالحمد لله، أنا بخير! أنا هنا لمساعدتك في العثور على معلومات شركات الحج. كيف يمكنني مساعدتك؟",
        "no_results": "لم يتم العثور على نتائج. حاول إعادة صياغة السؤال أو توسيع نطاق البحث.",
        "sql_error": "حدث خطأ في قاعدة البيانات. حاول إعادة صياغة سؤالك.",
        "intent_error": "⚠️ مشكلة في اكتشاف النية",
        "general_error": "عذراً، واجهت مشكلة في الإجابة.",
        "hint_rephrase": "💡 حاول إعادة صياغة سؤالك أو استخدم كلمات مفتاحية مختلفة",
        "no_sql": "عذراً، لا يمكن تحويل هذا الطلب إلى استعلام SQL آمن. حاول إعادة صياغة السؤال.",
    }
}

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

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="🕋 Hajj Chatbot",
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
def normalize_text(name):
                if not name or not isinstance(name, str) or name.strip() == "":
                    return None
                name = name.strip()
                if name in cache:
                    return cache[name]
                try:
                    translated = translator.translate(name)
                    normalized = translated.strip().lower()
                except Exception:
                    normalized = name.lower()
                cache[name] = normalized
                return normalized

# -----------------------------
# Database & OpenAI Setup
# -----------------------------
@st.cache_resource
def get_database_engine():
    """Initialize database engine"""
    try:
        return create_engine("sqlite:///hajj_companies_Update.db")
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
            # Fetch distinct names
            countries_df = pd.read_sql(text("SELECT DISTINCT country FROM agencies"), conn)
            cities_df = pd.read_sql(text("SELECT DISTINCT city FROM agencies"), conn)

            translator = GoogleTranslator(source='auto', target='en')

            # Apply translation-based normalization
            countries_df['normalized'] = countries_df['country'].apply(normalize_text)
            cities_df['normalized'] = cities_df['city'].apply(normalize_text)

            # Count unique normalized names
            unique_countries = countries_df['normalized'].nunique()
            unique_cities = cities_df['normalized'].nunique()

            # Query total and authorized counts
            total = pd.read_sql(text("SELECT COUNT(DISTINCT hajj_company_en) AS count FROM agencies"), conn).iloc[0]['count']
            authorized = pd.read_sql(text("SELECT COUNT(DISTINCT hajj_company_en) AS count FROM agencies WHERE is_authorized = 'Yes'"), conn).iloc[0]['count']

            return {
                'total': total,
                'authorized': authorized,
                'countries': unique_countries,
                'cities': unique_cities
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

# -----------------------------
# Sidebar
# -----------------------------
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
# Main Header
# -----------------------------
st.markdown(f"""
<div class="header-container{' rtl' if st.session_state.new_language == 'العربية' else ''}">
    <h1>
        🕋 <span class="main-title">{t('main_title', st.session_state.new_language)}</span>
    </h1>
    <p class="subtitle">{t('subtitle', st.session_state.new_language)}</p>
</div>
""", unsafe_allow_html=True)
# -----------------------------
# Initialize Session State
# -----------------------------
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = [{
        "role": "assistant",
        "content": t("welcome_msg", st.session_state.new_language),
        "timestamp": get_current_time()
    }]

if "last_result_df" not in st.session_state:
    st.session_state.last_result_df = None

if "selected_question" not in st.session_state:
    st.session_state.selected_question = None
def fuzzy_normalize(text: str) -> str:
    """Normalize text for fuzzy matching"""
    # Remove diacritics and special characters
    import unicodedata
    normalized = unicodedata.normalize('NFKD', text).encode('ASCII', 'ignore').decode('ASCII')
    # Convert to lowercase and remove extra spaces
    normalized = ' '.join(normalized.lower().split())
    return normalized
def heuristic_sql_fallback(question: str) -> Optional[str]:
    """Generate SQL query based on simple heuristics when AI fails"""
    question = question.lower()
    
    # Basic patterns
    if any(word in question for word in ['all', 'show', 'list']):
        return "SELECT * FROM agencies LIMIT 100"
        
    if 'authorized' in question or 'autorized' in question:
        return "SELECT * FROM agencies WHERE is_authorized = 'Yes' LIMIT 100"
        
    if 'saudi' in question or 'ksa' in question:
        return "SELECT * FROM agencies WHERE LOWER(Country) LIKE '%saudi%' LIMIT 100"
        
    if 'email' in question:
        return "SELECT * FROM agencies WHERE email IS NOT NULL AND email != '' LIMIT 100"
        
    return None
def show_result_summary(df: pd.DataFrame) -> None:
    """Display summary statistics and columns for results"""
    col1, col2, col3 = st.columns(3)
    with col1:
        st.markdown(f"<div class='badge badge-info'>📊 {len(df)} Results</div>", unsafe_allow_html=True)
    with col2:
        st.markdown(f"<div class='badge badge-success'>✅ {len(df.columns)} Columns</div>", unsafe_allow_html=True)
    with col3:
        if "is_authorized" in df.columns:
            auth_count = len(df[df["is_authorized"] == "Yes"])
            st.markdown(f"<div class='badge badge-success'>🔒 {auth_count} Authorized</div>", unsafe_allow_html=True)
    
    st.dataframe(df, use_container_width=True, height=300)

def show_download_button(df: pd.DataFrame) -> None:
    """Display download button for results"""
    csv = df.to_csv(index=False).encode("utf-8")
    st.download_button(
        label=t("download_csv", st.session_state.new_language),
        data=csv,
        file_name=f"hajj_data_{int(datetime.now().timestamp())}.csv",
        mime="text/csv"
    )

def show_sql_expander(sql_query: str, row_count: int) -> None:
    """Display SQL query in expandable section"""
    with st.expander(t("view_sql", st.session_state.new_language)):
        st.code(sql_query, language="sql")
        st.caption(t("executed_caption", st.session_state.new_language, count=row_count))
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
# Display Chat History
# -----------------------------
for idx, msg in enumerate(st.session_state.chat_memory):
    role = msg.get("role", "assistant")
    avatar = "🕋" if role == "assistant" else "👤"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg.get("content", ""))
        if msg.get("timestamp"):
            st.markdown(
                f"<div class='caption'>🕐 {datetime.fromtimestamp(msg['timestamp']).strftime('%I:%M %p')}</div>",
                unsafe_allow_html=True
            )

        if "dataframe" in msg and msg["dataframe"] is not None:
            df = msg["dataframe"]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"<div class='badge badge-info'>📊 {len(df)} Results</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='badge badge-success'>✅ {len(df.columns)} Columns</div>", unsafe_allow_html=True)
            with col3:
                if "is_authorized" in df.columns:
                    auth_count = len(df[df["is_authorized"] == "Yes"])
                    st.markdown(f"<div class='badge badge-success'>🔒 {auth_count} Authorized</div>", unsafe_allow_html=True)

            st.dataframe(df, use_container_width=True, height=300)

            csv = df.to_csv(index=False).encode("utf-8")
            st.download_button(
                label="📥 CSV",
                data=csv,
                file_name=f"hajj_data_{int(msg['timestamp'])}.csv",
                mime="text/csv",
                key=f"download_{idx}"
            )

# -----------------------------
# Handle User Input
# -----------------------------
placeholder_text = "اكتب سؤالك هنا... 💬" if st.session_state.new_language == "العربية" else "Ask your question here... 💬"
user_input = st.session_state.selected_question or st.chat_input(placeholder_text)
st.session_state.selected_question = None

if user_input:
    # Record user message
    st.session_state.chat_memory.append({
        "role": "user",
        "content": user_input,
        "timestamp": get_current_time()
    })

    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
        st.markdown(f"<div class='caption'>🕐 {format_time(get_current_time())}</div>", unsafe_allow_html=True)

    # Assistant thinking...
    with st.chat_message("assistant", avatar="🕋"):
        with st.spinner("🤔 Analyzing your question..."):
            # -----------------------------
            # Intent Detection
            # -----------------------------
            try:
               # Intent Detection - UPDATED
                intent_prompt = f"""You are a fraud prevention assistant for Hajj pilgrims. Classify this message:

                GREETING: greetings like hello, hi, how are you, salam, if no agency info is provided and user want to chat.
                DATABASE: questions about verifying specific Hajj agencies, checking authorization, company details, locations, contacts, etc.
                GENERAL_HAJJ: general Hajj questions (rituals, requirements)

                CRITICAL CONTEXT:
                - 415 fake Hajj offices were closed in 2025
                - 269,000+ unauthorized pilgrims were stopped
                - Our mission is to prevent fraud and protect pilgrims
                - Always emphasize verification and authorization

                Message: {user_input}

                Respond with ONE WORD: GREETING, DATABASE, or GENERAL_HAJJ"""
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You classify intents. Respond with one word."},
                        {"role": "user", "content": intent_prompt}
                    ],
                    temperature=0,
                    max_tokens=8
                )
                candidate = resp.choices[0].message.content.strip().upper()
                if candidate in ("GREETING", "DATABASE", "GENERAL_HAJJ"):
                    intent = candidate
            except Exception as e:
                st.warning(f"⚠️ Intent detection issue: {e}")

            # -----------------------------
            # Handle GREETING Intent
            # -----------------------------
            if intent == "GREETING":
                is_arabic = any("\u0600" <= ch <= "\u06FF" for ch in user_input)
                
                # Create a conversational prompt based on language
                greeting_prompt = {
                    "role": "system",
                    "content": """You are a friendly Hajj assistant. Generate a warm, natural greeting that:
                    1. Acknowledges the user's greeting
                    2. Expresses willingness to help
                    3. Mentions you can help with Hajj company information
                    4. Keeps response under 3 sentences
                    5. Uses emojis appropriately
                    """ + ("6. Respond in Arabic" if is_arabic else "6. Respond in English")
                }

                try:
                    greeting_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            greeting_prompt,
                            {"role": "user", "content": user_input}
                        ],
                        temperature=0.7,
                        max_tokens=150
                    )
                    
                    greeting_text = greeting_response.choices[0].message.content.strip()
                    
                    # Fallback greetings if API fails
                    if not greeting_text:
                        greeting_text = (
                            "السلام عليكم ورحمة الله وبركاته! 🌙\n\nكيف يمكنني مساعدتك في البحث عن معلومات شركات الحج؟"
                            if is_arabic else
                            "Hello! 👋\n\nHow can I help you find information about Hajj companies today?"
                        )
                        
                except Exception:
                    # Fallback on API failure
                    greeting_text = (
                        "السلام عليكم ورحمة الله وبركاته! 🌙\n\nكيف يمكنني مساعدتك في البحث عن معلومات شركات الحج؟"
                        if is_arabic else
                        "Hello! 👋\n\nHow can I help you find information about Hajj companies today?"
                    )

                st.markdown(greeting_text)
                st.session_state.chat_memory.append({
                    "role": "assistant",
                    "content": greeting_text,
                    "timestamp": get_current_time()
                })

            # -----------------------------
            # Handle GENERAL_HAJJ Intent
            # -----------------------------
            elif intent == "GENERAL_HAJJ":
                try:
                    context = build_chat_context(limit=6)
                    context.append({"role": "user", "content": user_input})
                    hajj_resp = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=context,
                        temperature=0.6,
                        max_tokens=400
                    )
                    answer_text = hajj_resp.choices[0].message.content.strip()
                    st.markdown(answer_text)
                    st.session_state.chat_memory.append({
                        "role": "assistant",
                        "content": answer_text,
                        "timestamp": get_current_time()
                    })
                except Exception as e:
                    err = "عذراً، واجهت مشكلة في الإجابة." if st.session_state.new_language == "العربية" else "Sorry, I encountered an error."
                    st.error(f"{err} {e}")
                    st.session_state.chat_memory.append({
                        "role": "assistant",
                        "content": f"{err} {e}",
                        "timestamp": get_current_time()
                    })

            # -----------------------------
            # Handle DATABASE Intent
            # -----------------------------
            else:
                with st.status("🔍 Searching database...", expanded=True):
                    st.write("🧠 Generating SQL query...")

                    normalized_input = fuzzy_normalize(user_input)
                  
                    # SQL Generation - UPDATED FOR FRAUD PREVENTION
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

    USER QUESTION:
    {user_input}

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
    --------------------------------------------

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

    Q: "هل شركة الهدى معتمدة؟"
    → SELECT * FROM agencies WHERE (hajj_company_ar LIKE '%الهدى%' OR LOWER(hajj_company_en) LIKE '%alhuda%') LIMIT 10;

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

                    sql_query = None
                    try:
                        sql_resp = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "You output only a SELECT query or NO_SQL."},
                                {"role": "user", "content": sql_prompt}
                            ],
                            temperature=0
                        )
                        raw_sql = sql_resp.choices[0].message.content.strip()
                        sql_query = extract_sql_from_response(raw_sql)
                        if sql_query == "NO_SQL":
                            sql_query = None
                    except Exception as e:
                        st.write(f"❌ SQL generation failed: {e}")
                        sql_query = None

                    # -----------------------------
                    # Heuristic fallback
                    # -----------------------------
                    if not sql_query:
                        heur_sql = heuristic_sql_fallback(user_input)
                        if heur_sql:
                            sql_query = heur_sql

                    sql_query = sanitize_sql(sql_query) if sql_query else None
                    result_df, sql_error = None, None

                    # -----------------------------
                    # Execute SQL
                    # -----------------------------
                    if sql_query:
                        st.write("💾 Executing query...")
                        try:
                            with engine.connect() as conn:
                                result_df = pd.read_sql(text(sql_query), conn)

                                st.write(f"✅ Found {len(result_df)} results")
                        except Exception as e:
                            sql_error = str(e)
                            st.write(f"❌ Query failed: {e}")
                    else:
                        msg = (
                            "عذراً، لا يمكن تحويل هذا الطلب إلى استعلام SQL آمن."
                            if st.session_state.new_language == "العربية"
                            else "Sorry, I couldn't convert that to a safe SQL query."
                        )
                        st.warning(msg)
                        st.session_state.chat_memory.append({
                            "role": "assistant",
                            "content": msg,
                            "timestamp": get_current_time()
                        })

                # -----------------------------
                # Present Results
                # -----------------------------
                if result_df is not None and not result_df.empty:
                    row_count = len(result_df)
                    sample = result_df.head(20).to_dict(orient="records")
                    summary_prompt = f"""
Summarize these SQL query results concisely in {'Arabic' if st.session_state.new_language == 'العربية' else 'English'}.
Question: {user_input}
Total rows: {row_count}
Sample: {sample}
Give 1–3 short sentences of insights.
"""
                    try:
                        summ_resp = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "You summarize data concisely."},
                                {"role": "user", "content": summary_prompt}
                            ],
                            temperature=0.5,
                            max_tokens=200
                        )
                        answer_text = summ_resp.choices[0].message.content.strip()
                    except Exception:
                        answer_text = (
                            f"📊 Found {row_count} matching records."
                            if st.session_state.new_language == "English"
                            else f"📊 تم العثور على {row_count} نتيجة."
                        )

                    st.markdown(answer_text)
                    show_result_summary(result_df)
                    show_download_button(result_df)
                    show_sql_expander(sql_query, row_count)

                    st.session_state.chat_memory.append({
                        "role": "assistant",
                        "content": answer_text,
                        "dataframe": result_df,
                        "timestamp": get_current_time()
                    })
                    st.session_state.last_result_df = result_df

                elif sql_error:
                    st.error(f"❌ Query failed: {sql_error}")
                    st.session_state.chat_memory.append({
                        "role": "assistant",
                        "content": f"Query failed: {sql_error}",
                        "timestamp": get_current_time()
                    })
                else:
                    no_results = (
                        "لم يتم العثور على نتائج."
                        if st.session_state.new_language == "العربية"
                        else "No results found."
                    )
                    st.warning(no_results)
                    st.session_state.chat_memory.append({
                        "role": "assistant",
                        "content": no_results,
                        "timestamp": get_current_time()
                    })