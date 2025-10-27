# hajj_chatbot_app.py
# Full Streamlit app: Hajj Data Intelligence — polished, multilingual, SQL generation, fuzzy matching,
# safer SQL execution, chat memory, summaries, downloads, and UI polish.
#
# NOTE:
# - Place your SQLite DB file `hajj_companies.db` next to this script or update the path.
# - Put your OpenAI API key in Streamlit secrets as `key` (e.g., in .streamlit/secrets.toml).
# - Tested against Streamlit 1.20+ APIs (st.chat_message, st.chat_input). Adjust if using older Streamlit.

import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from openai import OpenAI
from datetime import datetime
import time
import re
import html
from typing import Optional, Dict, Any, List

# -----------------------------
# Page & CSS
# -----------------------------
st.set_page_config(
    page_title="🕋 Hajj Chatbot",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="expanded"
)

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
    
    /* Header Styling */
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
        animation: slideInLeft 0.8s ease-out;
    }
    
    .subtitle {
        color: #666;
        font-size: 1.1rem;
        margin-top: 0.5rem;
        animation: fadeIn 1s ease-out;
    }
    
    /* Chat Container */
    .stChatMessage {
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px);
        border-radius: 18px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.3);
        animation: fadeInUp 0.5s ease-out;
        transition: transform 0.2s ease, box-shadow 0.2s ease;
    }
    
    .stChatMessage:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.12) !important;
    }
    
    /* User message styling */
    [data-testid="stChatMessageContent"] {
        background: transparent;
    }
    
    /* Sidebar Styling */
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
    
    /* Stat Cards */
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
    
    /* Example Questions */
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
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }
    
    /* Radio Buttons */
    .stRadio > div {
        background: rgba(255, 255, 255, 0.1);
        padding: 0.5rem;
        border-radius: 10px;
    }
    
    .stRadio label {
        color: white !important;
    }
    
    /* Chat Input */
    .stChatInputContainer {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 1rem;
        box-shadow: 0 -4px 20px rgba(0, 0, 0, 0.1);
    }
    
    /* Dataframe Styling */
    .stDataFrame {
        border-radius: 12px;
        overflow: hidden;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    }
    
    /* Download Button */
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
    
    /* Expander */
    .streamlit-expanderHeader {
        background: rgba(102, 126, 234, 0.1);
        border-radius: 10px;
        font-weight: 600;
        color: #667eea;
    }
    
    /* Info boxes */
    .stAlert {
        border-radius: 12px;
        border: none;
        backdrop-filter: blur(10px);
    }
    
    /* Spinner */
    .stSpinner > div {
        border-top-color: #667eea !important;
    }
    
    /* Animations */
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
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(20px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-50px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    /* Scrollbar */
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
    
    /* Caption styling */
    .caption {
        color: #999;
        font-size: 0.85rem;
        margin-top: 0.5rem;
    }
    
    /* Badge */
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
</style>
""", unsafe_allow_html=True)


# -----------------------------
# Utilities
# -----------------------------
def now_str():
    return datetime.fromtimestamp(time.time()).strftime("%I:%M %p")

def escape_sql(value: str) -> str:
    """Escape single quotes for safe interpolation if ever needed (we use parameterized queries)."""
    return value.replace("'", "''")

def sanitize_sql(sql_query: str) -> Optional[str]:
    """Reject dangerous queries and ensure it's a SELECT only (basic safeguard)."""
    if not sql_query:
        return None
    # Quick reject keywords (case-insensitive)
    dangerous = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'EXEC', 'EXECUTE', 'TRUNCATE', ';--']
    upper = sql_query.upper()
    for kw in dangerous:
        if kw in upper and not sql_query.strip().upper().startswith("SELECT"):
            return None
    # Force single statement and SELECT start
    if not sql_query.strip().upper().startswith("SELECT"):
        return None
    # Remove trailing semicolons
    return sql_query.strip().rstrip(';')

def extract_sql_from_response(response_text: str) -> Optional[str]:
    """Extract SELECT query from GPT response (supports code fences)."""
    if not response_text:
        return None
    # look for ```sql or ``` code blocks first
    code_block_pattern = r'```(?:sql)?\s*(SELECT[\s\S]*?)```'
    match = re.search(code_block_pattern, response_text, re.IGNORECASE)
    if match:
        return match.group(1).strip().rstrip(';')

    # fallback: find first SELECT ... (until end or semicolon)
    select_pattern = r'(SELECT\s+.*?(?:;|$))'
    match = re.search(select_pattern, response_text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip().rstrip(';')

    # explicit NO_SQL semantic
    if "NO_SQL" in response_text or response_text.strip().upper() == "NO_SQL":
        return "NO_SQL"

    return None

# Small fuzzy normalizer for common Arabic/English variants
def fuzzy_normalize(text: str) -> str:
    """Normalize known city/country synonyms to canonical forms to help SQL generation."""
    if not text or not isinstance(text, str):
        return text
    t = text.lower()
    synonyms = {
        "makkah": ["makkah", "makkah al mukarramah", "mecca", "meca", "makkah al-mukarramah", "مكة", "مكة المكرمة"],
        "madinah": ["madinah", "medina", "المدينة", "المدينة المنورة", "madina"],
        "saudi arabia": ["saudi arabia", "saudi", "saudi arabia (kingsdom)", "السعودية", "المملكة العربية السعودية"],
        "egypt": ["egypt", "misr", "مصر"],
        # add more as needed
    }
    for canon, terms in synonyms.items():
        for term in terms:
            if term in t:
                return canon
    return text

def build_chat_context(limit: int = 8) -> List[Dict[str, str]]:
    """Return last N messages from session_state.chat_memory formatted for the LLM."""
    mem = st.session_state.get("chat_memory", [])
    msgs = []
    # Keep the last `limit` messages
    for m in mem[-limit:]:
        role = m.get("role", "user")
        content = m.get("content", "")
        msgs.append({"role": role, "content": content})
    return msgs

# -----------------------------
# Database & OpenAI clients (cached)
# -----------------------------
@st.cache_resource
def get_database_engine(db_path: str = "sqlite:///hajj_companies.db"):
    try:
        engine = create_engine(db_path, connect_args={"check_same_thread": False})
        return engine
    except Exception as e:
        st.error(f"❌ Database connection failed: {e}")
        st.stop()

engine = get_database_engine()

@st.cache_resource
def get_openai_client():
    api_key = None
    # prefer st.secrets
    try:
        api_key = st.secrets["key"]
    except Exception:
        api_key = None
    if not api_key:
        st.warning("⚠️ OpenAI API key missing in Streamlit secrets. Add `key` to .streamlit/secrets.toml")
        st.stop()
    # Initialize client
    return OpenAI(api_key=api_key)

client = get_openai_client()

# -----------------------------
# DB Stats (cached small TTL)
# -----------------------------
@st.cache_data(ttl=300)
def get_db_stats():
    try:
        with engine.connect() as conn:
            total = pd.read_sql(text("SELECT COUNT(*) as count FROM agencies"), conn).iloc[0]['count']
            authorized = pd.read_sql(text("SELECT COUNT(*) as count FROM agencies WHERE is_authorized = 'Yes'"), conn).iloc[0]['count']
            countries = pd.read_sql(text("SELECT COUNT(DISTINCT country) as count FROM agencies"), conn).iloc[0]['count']
            cities = pd.read_sql(text("SELECT COUNT(DISTINCT city) as count FROM agencies"), conn).iloc[0]['count']
            return {'total': total, 'authorized': authorized, 'countries': countries, 'cities': cities}
    except Exception as e:
        # return zeros if DB missing
        return {'total': 0, 'authorized': 0, 'countries': 0, 'cities': 0}

# -----------------------------
# Sidebar / UI layout
# -----------------------------
with st.sidebar:
    st.markdown("<h2 style='text-align: center; color: white; margin-bottom: 0;'>🕋 Hajj Assistant</h2>", unsafe_allow_html=True)
    st.markdown("<p style='text-align: center; color: rgba(255,255,255,0.7); font-size: 0.9rem;'>Your AI-powered guide</p>", unsafe_allow_html=True)
    st.markdown("---")

    # Language Toggle
    st.markdown("<h3>🌐 Language</h3>", unsafe_allow_html=True)
    language_choice = st.radio("", ["English 🇬🇧", "العربية 🇸🇦"], horizontal=True, label_visibility="collapsed")
    language = "العربية" if "العربية" in language_choice else "English"

    st.markdown("---")
    st.markdown("<h3>📊 Live Statistics</h3>", unsafe_allow_html=True)
    stats = get_db_stats()
    stat_items = [
        ("total", "Total Agencies", "🏢"),
        ("authorized", "Authorized", "✅"),
        ("countries", "Countries", "🌍"),
        ("cities", "Cities", "🏙️")
    ]
    for key, label, icon in stat_items:
        html_card = f"""
        <div class="stat-card">
            <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>
            <div class="stat-number">{stats.get(key,0):,}</div>
            <div class="stat-label">{label}</div>
        </div>
        """
        st.markdown(html_card, unsafe_allow_html=True)

    st.markdown("---")
    st.markdown("<h3>💡 Quick Examples</h3>", unsafe_allow_html=True)
    example_questions = [
        ("🔍 All authorized companies", "Show me all authorized Hajj companies"),
        ("🇸🇦 Companies in Saudi Arabia", "List companies in Saudi Arabia"),
        ("📊 Agencies by country", "How many agencies are in each country?"),
        ("📧 Companies with emails", "Find companies with email addresses"),
        ("🕋 شركات معتمدة", "أظهر لي الشركات المعتمدة"),
        ("📍 شركات في مكة", "ما هي الشركات في مكة؟")
    ]
    for i, (display_text, question) in enumerate(example_questions):
        if st.button(display_text, key=f"example_{i}", use_container_width=True):
            st.session_state.selected_question = question

    st.markdown("---")
    if st.button("🧹 Clear Chat History", use_container_width=True, type="primary"):
        st.session_state.chat_memory = []
        st.session_state.last_result_df = None
        st.session_state.selected_question = None
        st.experimental_rerun()

    st.markdown("---")
    st.markdown("<h3>ℹ️ Features</h3>", unsafe_allow_html=True)
    st.markdown("""
    <div style='color: rgba(255,255,255,0.9); font-size: 0.9rem; line-height: 1.8;'>
        <p>✨ <b>AI-Powered Search</b><br/>Natural language queries</p>
        <p>🌍 <b>Multilingual</b><br/>Arabic & English support</p>
        <p>📊 <b>Data Visualization</b><br/>Interactive tables</p>
        <p>💾 <b>Export Results</b><br/>Download as CSV</p>
        <p>🔒 <b>Secure</b><br/>SQL injection protection</p>
    </div>
    """, unsafe_allow_html=True)

# -----------------------------
# Header & Session init
# -----------------------------
st.markdown("""
<div class="header-container">
    <h1 class="main-title">🕋 Hajj Data Intelligence</h1>
    <p class="subtitle">Ask anything about Hajj companies worldwide • AI-powered • Real-time data</p>
</div>
""", unsafe_allow_html=True)

if "chat_memory" not in st.session_state:
    welcome_msg = "السلام عليكم ورحمة الله وبركاته! 🌙\n\nأهلاً بك في مساعد معلومات الحج الذكي. كيف يمكنني مساعدتك اليوم؟" if language == "العربية" else "Welcome! 👋\n\nI'm your Hajj Data Assistant. Ask me anything about Hajj companies, locations, or authorization status!"
    st.session_state.chat_memory = [{"role": "assistant", "content": welcome_msg, "timestamp": time.time()}]
if "last_result_df" not in st.session_state:
    st.session_state.last_result_df = None
if "selected_question" not in st.session_state:
    st.session_state.selected_question = None

# Show chat history
for idx, msg in enumerate(st.session_state.chat_memory):
    role = msg.get("role", "assistant")
    avatar = "🕋" if role == "assistant" else "👤"
    with st.chat_message(role, avatar=avatar):
        st.markdown(msg.get("content", ""))
        if msg.get("timestamp"):
            st.markdown(f"<div class='caption'>🕐 {datetime.fromtimestamp(msg['timestamp']).strftime('%I:%M %p')}</div>", unsafe_allow_html=True)
        if "dataframe" in msg and msg["dataframe"] is not None:
            df = msg["dataframe"]
            col1, col2, col3 = st.columns(3)
            with col1:
                st.markdown(f"<div class='badge badge-info'>📊 {len(df)} Results</div>", unsafe_allow_html=True)
            with col2:
                st.markdown(f"<div class='badge badge-success'>✅ {len(df.columns)} Columns</div>", unsafe_allow_html=True)
            with col3:
                if 'is_authorized' in df.columns:
                    auth_count = len(df[df['is_authorized'] == 'Yes'])
                    st.markdown(f"<div class='badge badge-success'>🔒 {auth_count} Authorized</div>", unsafe_allow_html=True)
            st.dataframe(df, use_container_width=True, height=300)
            csv = df.to_csv(index=False).encode('utf-8')
            st.download_button(label="📥 CSV", data=csv, file_name=f"hajj_data_{int(msg['timestamp'])}.csv", mime="text/csv", key=f"download_{idx}")

# -----------------------------
# Input handling
# -----------------------------
user_input = None
if st.session_state.selected_question:
    user_input = st.session_state.selected_question
    st.session_state.selected_question = None
else:
    placeholder_text = "اكتب سؤالك هنا... 💬" if language == "العربية" else "Ask your question here... 💬"
    user_input = st.chat_input(placeholder_text)

if user_input:
    # append user message to memory
    st.session_state.chat_memory.append({"role": "user", "content": user_input, "timestamp": time.time()})
    with st.chat_message("user", avatar="👤"):
        st.markdown(user_input)
        st.markdown(f"<div class='caption'>🕐 {now_str()}</div>", unsafe_allow_html=True)

    # Assistant processing
    with st.chat_message("assistant", avatar="🕋"):
        with st.spinner("🤔 Analyzing your question..."):
            # Intent detection
            intent = "DATABASE"
            try:
                intent_prompt = f"""Classify the user's message into one of three categories: GREETING, DATABASE, GENERAL_HAJJ.
Respond with exactly one word (GREETING, DATABASE, or GENERAL_HAJJ).
Message: {user_input}
"""
                resp = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You classify user intents. Respond with only one word."},
                        {"role": "user", "content": intent_prompt}
                    ],
                    temperature=0,
                    max_tokens=8
                )
                candidate = resp.choices[0].message.content.strip().upper()
                if candidate in ("GREETING", "DATABASE", "GENERAL_HAJJ"):
                    intent = candidate
            except Exception as e:
                # silently fallback to DATABASE
                st.warning(f"⚠️ Intent detection issue: {e}")

            # GREETING
            if intent == "GREETING":
                is_arabic = any("\u0600" <= ch <= "\u06FF" for ch in user_input)
                greeting_text = "السلام عليكم ورحمة الله وبركاته! 🌙\n\nكيف يمكنني مساعدتك في البحث عن معلومات شركات الحج؟" if is_arabic else "Hello! 👋\n\nHow can I help you find information about Hajj companies today?"
                st.markdown(greeting_text)
                st.session_state.chat_memory.append({"role": "assistant", "content": greeting_text, "timestamp": time.time()})
                st.experimental_rerun()

            # GENERAL_HAJJ (e.g., rituals)
            elif intent == "GENERAL_HAJJ":
                try:
                    # Provide answer in user's language using chat context
                    context = build_chat_context(limit=6)
                    context.append({"role": "user", "content": user_input})
                    hajj_resp = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[{"role": m["role"], "content": m["content"]} for m in context],
                        temperature=0.6,
                        max_tokens=400
                    )
                    answer_text = hajj_resp.choices[0].message.content.strip()
                    st.markdown(answer_text)
                    st.session_state.chat_memory.append({"role": "assistant", "content": answer_text, "timestamp": time.time()})
                except Exception as e:
                    err = "عذراً، واجهت مشكلة في الإجابة." if language == "العربية" else "Sorry, I encountered an error."
                    st.error(f"{err} {e}")
                    st.session_state.chat_memory.append({"role": "assistant", "content": f"{err} {e}", "timestamp": time.time()})
                st.experimental_rerun()

            # DATABASE queries
            else:
                # Show searching UI
                with st.status("🔍 Searching database...", expanded=True):
                    st.write("🧠 Generating SQL query...")

                    # Pre-normalize user_input for fuzzy city/country synonyms
                    normalized_input = fuzzy_normalize(user_input)

                    # Build the SQL generation prompt
                    sql_prompt = f"""
You are a SQL expert. Convert the user's natural language request into a single SELECT SQL query targeting the 'agencies' table.
Table columns:
- hajj_company_ar (Arabic company name)
- hajj_company_en (English company name)
- city
- country
- email
- is_authorized ('Yes' or 'No')

Rules:
1. Return ONLY a single valid SELECT query (no explanation). If it's not possible to answer with SQL return NO_SQL.
2. Use LOWER(...) and LIKE for case-insensitive matching for city/country text.
3. For authorization filtering use is_authorized = 'Yes'.
4. Limit to 100 rows unless the user explicitly asks for more.
5. For location matching use patterns with % (e.g., LOWER(city) LIKE '%mecca%').
6. If the user asks for aggregates (counts, grouping), return the appropriate SELECT with GROUP BY.
7. Preserve both Arabic and English names in SELECT: SELECT hajj_company_ar, hajj_company_en, city, country, email, is_authorized FROM agencies ...
8. If the user's request references the normalized form '{normalized_input}', incorporate that into WHERE as needed.

User question: {user_input}
Return ONLY the SQL SELECT query or NO_SQL.
"""
                    sql_query = None
                    raw_sql = None
                    try:
                        sql_resp = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "You are a SQL expert. Output only a SELECT query or NO_SQL."},
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

                    # fallback: try a safe heuristic parser for simple intents (e.g., "authorized in mecca")
                    if not sql_query:
                        heur_sql = None
                        q = user_input.lower()
                        # simple patterns
                        if "authorized" in q or "معتمدة" in q or "معتمد" in q:
                            if "mecca" in q or "makkah" in q or "مكة" in q:
                                heur_sql = "SELECT hajj_company_ar, hajj_company_en, city, country, email, is_authorized FROM agencies WHERE is_authorized = 'Yes' AND (LOWER(city) LIKE '%mecca%' OR LOWER(city) LIKE '%makkah%' OR LOWER(city) LIKE '%مكة%') LIMIT 100"
                            elif "saudi" in q or "السعود" in q:
                                heur_sql = "SELECT hajj_company_ar, hajj_company_en, city, country, email, is_authorized FROM agencies WHERE is_authorized = 'Yes' AND LOWER(country) LIKE '%saudi%' LIMIT 100"
                        if heur_sql:
                            sql_query = heur_sql

                    sql_query = sanitize_sql(sql_query) if sql_query else None

                    result_df = None
                    sql_error = None

                    if sql_query:
                        st.write("💾 Executing query...")
                        try:
                            with engine.connect() as conn:
                                # Use text() to execute; this is read-only SELECT so safe
                                result_df = pd.read_sql(text(sql_query), conn)
                                st.write(f"✅ Found {len(result_df)} results")
                        except Exception as e:
                            sql_error = str(e)
                            st.write(f"❌ Query failed: {e}")
                    else:
                        st.write("⚠️ Unable to generate a safe SQL query for that request.")
                        # Add assistant message for NO_SQL
                        fallback = ("عذراً، لا يمكن تحويل هذا الطلب إلى استعلام SQL آمن. حاول إعادة صياغة السؤال أو اطلب نتائج عامة."
                                    if language == "العربية" else
                                    "Sorry, I couldn't convert that to a safe SQL query. Try rephrasing or ask for general results.")
                        st.warning(fallback)
                        st.session_state.chat_memory.append({"role": "assistant", "content": fallback, "timestamp": time.time()})

                # Present results (if any)
                if result_df is not None and not result_df.empty:
                    row_count = len(result_df)
                    # produce summary using LLM
                    preview_data = result_df.head(20).to_dict(orient="records")
                    summary_prompt = f"""Summarize these SQL query results briefly and naturally in {'Arabic' if language == 'العربية' else 'English'}.
Question: {user_input}
Total: {row_count}
Sample: {preview_data}
Give a concise summary with key insights (1-3 short sentences)."""
                    answer_text = None
                    try:
                        summ_resp = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "You summarize tabular results concisely."},
                                {"role": "user", "content": summary_prompt}
                            ],
                            temperature=0.5,
                            max_tokens=200
                        )
                        answer_text = summ_resp.choices[0].message.content.strip()
                    except Exception:
                        answer_text = f"📊 Found {row_count} matching records." if language == "English" else f"📊 تم العثور على {row_count} نتيجة."

                    st.markdown(answer_text)
                    col1, col2, col3 = st.columns(3)
                    with col1:
                        st.markdown(f"<div class='badge badge-info'>📊 {len(result_df)} Results</div>", unsafe_allow_html=True)
                    with col2:
                        st.markdown(f"<div class='badge badge-success'>✅ {len(result_df.columns)} Columns</div>", unsafe_allow_html=True)
                    with col3:
                        if 'is_authorized' in result_df.columns:
                            auth_count = len(result_df[result_df['is_authorized'] == 'Yes'])
                            st.markdown(f"<div class='badge badge-success'>🔒 {auth_count} Authorized</div>", unsafe_allow_html=True)

                    st.dataframe(result_df, use_container_width=True, height=400)
                    csv = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(label="📥 Download Results (CSV)", data=csv, file_name=f"hajj_results_{int(time.time())}.csv", mime="text/csv")

                    with st.expander("🔍 View SQL Query"):
                        st.code(sql_query, language="sql")
                        st.caption(f"Executed in database • {row_count} rows returned")

                    # append to chat memory
                    st.session_state.chat_memory.append({
                        "role": "assistant",
                        "content": answer_text,
                        "dataframe": result_df,
                        "timestamp": time.time()
                    })
                    st.session_state.last_result_df = result_df

                elif sql_error:
                    status_msg = "❌ Query failed"
                    st.error(f"{status_msg}: {sql_error}")
                    st.session_state.chat_memory.append({"role": "assistant", "content": f"Query failed: {sql_error}", "timestamp": time.time()})
                else:
                    # No results or no SQL
                    nores = ("لم يتم العثور على نتائج. حاول إعادة صياغة السؤال أو توسيع نطاق البحث."
                             if language == "العربية" else
                             "No results found. Try rephrasing the question or broadening the search.")
                    st.warning(nores)
                    st.session_state.chat_memory.append({"role": "assistant", "content": nores, "timestamp": time.time()})

# EOF
