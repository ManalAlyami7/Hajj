import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from openai import OpenAI
from datetime import datetime
import time
import re

# --- Page Configuration ---
st.set_page_config(
    page_title="🕋 Hajj Chatbot",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# --- Custom CSS for better UI ---
st.markdown("""
<style>
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    .stTitle {
        color: #1e3a5f;
        font-weight: 700;
        text-align: center;
        padding: 1rem 0;
    }
    .stChatMessage {
        background-color: white;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    .example-question {
        background: white;
        padding: 0.75rem 1rem;
        border-radius: 10px;
        margin: 0.5rem 0;
        border-left: 4px solid #2c5f8d;
        cursor: pointer;
        transition: all 0.3s ease;
    }
    .example-question:hover {
        transform: translateX(5px);
        box-shadow: 0 4px 12px rgba(0,0,0,0.15);
    }
    .stat-card {
        background: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
        margin: 0.5rem 0;
    }
    .stat-number {
        font-size: 2rem;
        font-weight: bold;
        color: #2c5f8d;
    }
    .stat-label {
        color: #666;
        font-size: 0.9rem;
    }
</style>
""", unsafe_allow_html=True)

# --- Connect to local database ---
@st.cache_resource
def get_database_engine():
    """Initialize and return database engine"""
    try:
        return create_engine("sqlite:///hajj_companies.db")
    except Exception as e:
        st.error(f"Database connection failed: {e}")
        st.stop()

engine = get_database_engine()

# --- OpenAI client ---
@st.cache_resource
def get_openai_client():
    """Initialize OpenAI client with API key"""
    api_key = st.secrets.get("key", None)
    if not api_key:
        st.warning("⚠️ OpenAI API key missing in Streamlit secrets.")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()

# --- Get database statistics ---
@st.cache_data(ttl=300)
def get_db_stats():
    """Fetch database statistics with error handling"""
    try:
        with engine.connect() as conn:
            stats = {
                'total': pd.read_sql(text("SELECT COUNT(*) as count FROM agencies"), conn).iloc[0]['count'],
                'authorized': pd.read_sql(text("SELECT COUNT(*) as count FROM agencies WHERE is_authorized = 'Yes'"), conn).iloc[0]['count'],
                'countries': pd.read_sql(text("SELECT COUNT(DISTINCT country) as count FROM agencies"), conn).iloc[0]['count'],
                'cities': pd.read_sql(text("SELECT COUNT(DISTINCT city) as count FROM agencies"), conn).iloc[0]['count']
            }
            return stats
    except Exception as e:
        st.error(f"Failed to load statistics: {e}")
        return None

def sanitize_sql(sql_query):
    """Basic SQL injection prevention"""
    dangerous_keywords = ['DROP', 'DELETE', 'INSERT', 'UPDATE', 'ALTER', 'CREATE', 'EXEC', 'EXECUTE']
    sql_upper = sql_query.upper()
    for keyword in dangerous_keywords:
        if keyword in sql_upper:
            return None
    return sql_query

def extract_sql_from_response(response_text):
    """Extract SQL query from markdown code blocks or plain text"""
    # Try to find SQL in code blocks
    code_block_pattern = r'```(?:sql)?\s*(SELECT.*?)```'
    match = re.search(code_block_pattern, response_text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip()
    
    # Try to find SELECT statement directly
    select_pattern = r'(SELECT\s+.*?(?:;|$))'
    match = re.search(select_pattern, response_text, re.IGNORECASE | re.DOTALL)
    if match:
        return match.group(1).strip().rstrip(';')
    
    return None

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🕋 Hajj Data Assistant")
    st.markdown("---")

    # Language Toggle
    language = st.radio("🌐 Language", ["English", "العربية"], horizontal=True)

    # Database Statistics
    st.markdown("### 📊 Database Statistics")
    stats = get_db_stats()
    if stats:
        col1, col2 = st.columns(2)
        stat_items = [
            ("total", "Total Agencies", col1),
            ("countries", "Countries", col1),
            ("authorized", "Authorized", col2),
            ("cities", "Cities", col2)
        ]
        
        for key, label, col in stat_items:
            html = f"""
            <div class="stat-card">
                <div class="stat-number">{stats[key]}</div>
                <div class="stat-label">{label}</div>
            </div>
            """
            col.markdown(html, unsafe_allow_html=True)

    st.markdown("---")

    # Example Questions
    st.markdown("### 💡 Example Questions")
    example_questions = [
        "Show me all authorized Hajj companies",
        "List companies in Saudi Arabia",
        "How many agencies are in each country?",
        "Find companies with email addresses",
        "أظهر لي الشركات المعتمدة",
        "ما هي الشركات في مكة؟"
    ]
    for i, question in enumerate(example_questions):
        if st.button(question, key=f"example_{i}", use_container_width=True):
            st.session_state.selected_question = question

    st.markdown("---")

    # Clear Chat
    if st.button("🧹 Clear Chat History", use_container_width=True):
        st.session_state.chat_memory = []
        st.session_state.last_result_df = None
        st.rerun()

    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    This chatbot helps you explore Hajj company data using natural language.
    - 🌍 Multilingual (Arabic/English)
    - 🔍 Natural language queries
    - 📊 Data visualization
    - 💾 Export results
    """)

# --- Main Content ---
st.title("🕋 Hajj Data Chatbot")

intro_text = {
    "English": """
    <div style='text-align: center; padding: 1rem; background: white; border-radius: 10px; margin-bottom: 2rem;'>
        <p style='color: #666; margin: 0;'>Ask questions about Hajj companies, their cities, countries, emails, or authorization status.</p>
    </div>
    """,
    "العربية": """
    <div style='text-align: center; padding: 1rem; background: white; border-radius: 10px; margin-bottom: 2rem;'>
        <p style='color: #666; margin: 0;'>اسأل عن شركات الحج، المدن، الدول، البريد الإلكتروني أو حالة الاعتماد.</p>
    </div>
    """
}
st.markdown(intro_text[language], unsafe_allow_html=True)

# --- Session State Initialization ---
if "chat_memory" not in st.session_state:
    welcome_msg = "السلام عليكم! أهلاً بك في روبوت معلومات الحج. كيف يمكنني مساعدتك؟" if language == "العربية" else "Welcome to the Hajj Data Chatbot! How can I assist you today?"
    st.session_state.chat_memory = [{
        "role": "assistant",
        "content": welcome_msg,
        "timestamp": time.time()
    }]
if "last_result_df" not in st.session_state:
    st.session_state.last_result_df = None
if "selected_question" not in st.session_state:
    st.session_state.selected_question = None

# --- Display Chat History ---
for msg in st.session_state.chat_memory:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("timestamp"):
            st.caption(datetime.fromtimestamp(msg["timestamp"]).strftime("🕓 %I:%M %p"))
        if "dataframe" in msg and msg["dataframe"] is not None:
            st.dataframe(msg["dataframe"], use_container_width=True)
            csv = msg["dataframe"].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Results (CSV)",
                data=csv,
                file_name=f"hajj_companies_{int(msg['timestamp'])}.csv",
                mime="text/csv",
                key=f"download_{msg['timestamp']}"
            )

# --- Handle User Input ---
user_input = None
if st.session_state.selected_question:
    user_input = st.session_state.selected_question
    st.session_state.selected_question = None
else:
    placeholder_text = "اسأل عن شركات الحج..." if language == "العربية" else "Ask a question about Hajj companies..."
    user_input = st.chat_input(placeholder_text)

if user_input:
    # Add user message
    st.session_state.chat_memory.append({
        "role": "user",
        "content": user_input,
        "timestamp": time.time()
    })
    
    with st.chat_message("user"):
        st.markdown(user_input)
        st.caption(datetime.fromtimestamp(time.time()).strftime("🕓 %I:%M %p"))

    # Process query
    with st.chat_message("assistant"):
        with st.spinner("🤔 Processing your question..."):
            
            # --- Step 1: Intent Detection ---
            intent_prompt = f"""Analyze this message and classify it as one word:
- GREETING: greetings like hello, hi, how are you
- DATABASE: questions about Hajj company data (names, locations, emails, authorization)
- GENERAL_HAJJ: general Hajj questions (rituals, requirements, history)

Message: {user_input}

Respond with exactly one word: GREETING, DATABASE, or GENERAL_HAJJ"""

            intent = "DATABASE"  # Default fallback
            try:
                intent_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You classify user intents. Respond with only one word."},
                        {"role": "user", "content": intent_prompt}
                    ],
                    temperature=0,
                    max_tokens=10
                )
                intent = intent_response.choices[0].message.content.strip().upper()
            except Exception as e:
                st.warning(f"Intent detection failed: {e}")

            # --- Handle GREETING ---
            if intent == "GREETING":
                is_arabic = any("\u0600" <= ch <= "\u06FF" for ch in user_input)
                greeting_text = "السلام عليكم ورحمة الله وبركاته! كيف يمكنني مساعدتك اليوم؟" if is_arabic else "Hello! How can I assist you with Hajj company information today?"
                st.markdown(greeting_text)
                st.session_state.chat_memory.append({
                    "role": "assistant",
                    "content": greeting_text,
                    "timestamp": time.time()
                })

            # --- Handle GENERAL_HAJJ ---
            elif intent == "GENERAL_HAJJ":
                try:
                    hajj_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a knowledgeable Islamic scholar assistant specializing in Hajj. Respond in the user's language (Arabic or English)."},
                            {"role": "user", "content": user_input}
                        ],
                        temperature=0.7
                    )
                    answer_text = hajj_response.choices[0].message.content.strip()
                    st.markdown(answer_text)
                    st.session_state.chat_memory.append({
                        "role": "assistant",
                        "content": answer_text,
                        "timestamp": time.time()
                    })
                except Exception as e:
                    error_msg = "عذراً، واجهت مشكلة في الإجابة على سؤالك." if language == "العربية" else "Sorry, I encountered an error answering your question."
                    st.error(f"{error_msg}\n\nError: {e}")

            # --- Handle DATABASE Query ---
            else:
                # Generate SQL
                sql_prompt = f"""Convert this question to SQL for the 'agencies' table with columns:
- hajj_company_ar (Arabic company name)
- hajj_company_en (English company name)
- city (city name)
- country (country name)
- email (email address)
- is_authorized ('Yes' or 'No')

Question: {user_input}

IMPORTANT RULES:
1. Use LIKE with wildcards (%) for city/country names to handle variations (e.g., "Mecca", "Makkah", "مكة")
2. For authorization, use: is_authorized = 'Yes'
3. Use LOWER() for case-insensitive matching
4. Return complete company information including both Arabic and English names
5. Limit results to 100 rows unless specifically asked for more

EXAMPLES:
- "authorized agencies in Mecca" → SELECT * FROM agencies WHERE is_authorized = 'Yes' AND LOWER(city) LIKE '%mecca%' OR LOWER(city) LIKE '%makkah%' LIMIT 100
- "companies in Saudi Arabia" → SELECT * FROM agencies WHERE LOWER(country) LIKE '%saudi%' LIMIT 100

Return ONLY the SQL SELECT query, nothing else. If the question cannot be answered with SQL, return "NO_SQL"."""

                sql_query = None
                try:
                    sql_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a SQL expert. Generate only valid SELECT queries."},
                            {"role": "user", "content": sql_prompt}
                        ],
                        temperature=0
                    )
                    raw_sql = sql_response.choices[0].message.content.strip()
                    
                    # Extract and clean SQL
                    sql_query = extract_sql_from_response(raw_sql)
                    
                    if sql_query and sql_query != "NO_SQL":
                        sql_query = sanitize_sql(sql_query)
                
                except Exception as e:
                    st.error(f"SQL generation failed: {e}")

                # Execute SQL
                result_df = None
                sql_error = None
                
                if sql_query:
                    try:
                        with engine.connect() as conn:
                            result_df = pd.read_sql(text(sql_query), conn)
                    except Exception as e:
                        sql_error = str(e)

                # Present results
                if result_df is not None and not result_df.empty:
                    row_count = len(result_df)
                    preview_data = result_df.head(20).to_dict(orient="records")
                    
                    # Generate natural language summary
                    summary_prompt = f"""Summarize these database results in the user's language ({"Arabic" if language == "العربية" else "English"}):

Question: {user_input}
Total results: {row_count}
Sample data: {preview_data}

Provide a brief, natural summary."""

                    try:
                        summary_response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "You summarize database results naturally."},
                                {"role": "user", "content": summary_prompt}
                            ]
                        )
                        answer_text = summary_response.choices[0].message.content.strip()
                    except:
                        answer_text = f"Found {row_count} results." if language == "English" else f"تم العثور على {row_count} نتيجة."

                    st.markdown(answer_text)
                    st.dataframe(result_df, use_container_width=True)
                    
                    # Download button
                    csv = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Results (CSV)",
                        data=csv,
                        file_name=f"hajj_results_{int(time.time())}.csv",
                        mime="text/csv"
                    )
                    
                    # Show SQL query (always visible for transparency)
                    with st.expander("🔍 View Generated SQL Query", expanded=False):
                        st.code(sql_query, language="sql")
                        st.caption(f"Retrieved {row_count} rows from database")

                    st.session_state.chat_memory.append({
                        "role": "assistant",
                        "content": answer_text,
                        "dataframe": result_df,
                        "timestamp": time.time()
                    })
                
                elif sql_error:
                    error_msg = "حدث خطأ في قاعدة البيانات. حاول إعادة صياغة سؤالك." if language == "العربية" else "A database error occurred. Try rephrasing your question."
                    st.error(error_msg)
                    with st.expander("🔧 Technical Details"):
                        st.code(f"Generated SQL:\n{sql_query}\n\nError:\n{sql_error}")
                    
                    st.session_state.chat_memory.append({
                        "role": "assistant",
                        "content": error_msg,
                        "timestamp": time.time()
                    })
                
                else:
                    no_results_msg = "عذراً، لم أجد أي نتائج مطابقة لسؤالك." if language == "العربية" else "I couldn't find any results matching your question."
                    st.info(no_results_msg)
                    
                    # Show what was attempted
                    if sql_query:
                        st.caption("💡 Try rephrasing your question or use different keywords (e.g., 'Makkah' instead of 'Mecca')")
                        with st.expander("🔍 Generated SQL Query"):
                            st.code(sql_query, language="sql")
                    
                    st.session_state.chat_memory.append({
                        "role": "assistant",
                        "content": no_results_msg,
                        "timestamp": time.time()
                    })

        # Show timestamp
        st.caption(datetime.fromtimestamp(time.time()).strftime("🕓 %I:%M %p"))