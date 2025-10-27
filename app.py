import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from openai import OpenAI
from datetime import datetime
import time

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
    .css-1d391kg {
        background: linear-gradient(180deg, #1e3a5f 0%, #2c5f8d 100%);
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
    return create_engine("sqlite:///hajj_companies.db")

engine = get_database_engine()

# --- OpenAI client ---
@st.cache_resource
def get_openai_client():
    api_key = st.secrets.get("key", None)
    if not api_key:
        st.warning("⚠️ OpenAI API key missing in Streamlit secrets.")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()

# --- Get database statistics ---
@st.cache_data(ttl=300)
def get_db_stats():
    try:
        with engine.connect() as conn:
            total_agencies = pd.read_sql(text("SELECT COUNT(*) as count FROM agencies"), conn).iloc[0]['count']
            authorized = pd.read_sql(text("SELECT COUNT(*) as count FROM agencies WHERE is_authorized = 'Yes'"), conn).iloc[0]['count']
            countries = pd.read_sql(text("SELECT COUNT(DISTINCT country) as count FROM agencies"), conn).iloc[0]['count']
            cities = pd.read_sql(text("SELECT COUNT(DISTINCT city) as count FROM agencies"), conn).iloc[0]['count']
            return {'total': total_agencies, 'authorized': authorized, 'countries': countries, 'cities': cities}
    except:
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
        for key, label in zip(
            ["total", "countries", "authorized", "cities"],
            ["Total Agencies", "Countries", "Authorized", "Cities"]
        ):
            html = f"""
            <div class="stat-card">
                <div class="stat-number">{stats[key]}</div>
                <div class="stat-label">{label}</div>
            </div>
            """
            if key in ["total", "countries"]:
                col1.markdown(html, unsafe_allow_html=True)
            else:
                col2.markdown(html, unsafe_allow_html=True)

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

intro_text_en = """
<div style='text-align: center; padding: 1rem; background: white; border-radius: 10px; margin-bottom: 2rem;'>
    <p style='color: #666; margin: 0;'>Ask questions about Hajj companies, their cities, countries, emails, or authorization status.</p>
</div>
"""
intro_text_ar = """
<div style='text-align: center; padding: 1rem; background: white; border-radius: 10px; margin-bottom: 2rem;'>
    <p style='color: #666; margin: 0;'>اسأل عن شركات الحج، المدن، الدول، البريد الإلكتروني أو حالة الاعتماد.</p>
</div>
"""
st.markdown(intro_text_ar if language == "العربية" else intro_text_en, unsafe_allow_html=True)

# --- Session State ---
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = [{
        "role": "assistant",
        "content": "السلام عليكم! Welcome to the Hajj Data Chatbot. Ask me about Hajj companies or select an example from the sidebar.",
        "timestamp": time.time()
    }]
if "last_result_df" not in st.session_state:
    st.session_state.last_result_df = None
if "selected_question" not in st.session_state:
    st.session_state.selected_question = None

# --- Display Chat ---
for msg in st.session_state.chat_memory:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        if msg.get("timestamp"):
            st.caption(datetime.fromtimestamp(msg["timestamp"]).strftime("🕓 %I:%M %p"))
        if "dataframe" in msg:
            st.dataframe(msg["dataframe"], use_container_width=True)
            csv = msg["dataframe"].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Results (CSV)",
                data=csv,
                file_name="hajj_companies_results.csv",
                mime="text/csv",
                key=f"download_{msg['timestamp']}"
            )

# --- Handle Input ---
if st.session_state.selected_question:
    user_input = st.session_state.selected_question
    st.session_state.selected_question = None
else:
    user_input = st.chat_input("Ask a question about Hajj companies..." if language == "English" else "اسأل عن شركات الحج...")

if user_input:
    st.session_state.chat_memory.append({"role": "user", "content": user_input, "timestamp": time.time()})
    with st.chat_message("user"):
        st.markdown(user_input)

    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            # --- Intent Detection ---
            intent_prompt = f"""
Analyze the user's message and classify it into one of these categories:
1. GREETING - if it's a greeting like hi, hello, how are you, etc.
2. DATABASE - if it's asking for specific data about Hajj companies (names, locations, emails, authorization status)
3. GENERAL_HAJJ - if it's asking general questions about Hajj (rituals, requirements, history, etc.)

User message: {user_input}

Respond with only one word: GREETING, DATABASE, or GENERAL_HAJJ
"""

            try:
                intent_response = client.chat.completions.create(
                    model="gpt-4o-mini",
                    messages=[
                        {"role": "system", "content": "You are an intent classification assistant."},
                        {"role": "user", "content": intent_prompt}
                    ]
                )
                intent = intent_response.choices[0].message.content.strip().upper()
            except:
                intent = "DATABASE"

            # --- GREETING ---
            if intent == "GREETING":
                greeting_text = "السلام عليكم ورحمة الله وبركاته! كيف يمكنني مساعدتك اليوم؟" if any("\u0600" <= ch <= "\u06FF" for ch in user_input) else "Hello! How can I assist you today?"
                st.markdown(greeting_text)
                st.session_state.chat_memory.append({"role": "assistant", "content": greeting_text, "timestamp": time.time()})

            # --- GENERAL_HAJJ ---
            elif intent == "GENERAL_HAJJ":
                hajj_prompt = f"""
You are a multilingual Hajj assistant. Answer in the user's language.
User question: {user_input}
"""
                try:
                    hajj_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a knowledgeable Hajj assistant."},
                            {"role": "user", "content": hajj_prompt}
                        ]
                    )
                    answer_text = hajj_response.choices[0].message.content.strip()
                except:
                    answer_text = "عذراً، لم أتمكن من الإجابة على سؤالك." if language == "العربية" else "Sorry, I couldn’t answer your question."
                st.markdown(answer_text)
                st.session_state.chat_memory.append({"role": "assistant", "content": answer_text, "timestamp": time.time()})

            # --- DATABASE ---
            else:
                sql_prompt = f"""
You are a Text-to-SQL assistant. The table 'agencies' has columns:
hajj_company_ar, hajj_company_en, city, country, email, is_authorized.
Convert the user's question into a SQL query or return "NO_SQL".

Question: {user_input}
"""
                try:
                    sql_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a Text-to-SQL assistant."},
                            {"role": "user", "content": sql_prompt}
                        ]
                    )
                    sql_query = sql_response.choices[0].message.content.strip().strip("`").replace("sql", "").strip()
                    if sql_query == "NO_SQL" or not sql_query.upper().startswith("SELECT"):
                        sql_query = None
                except:
                    sql_query = None

                result_df, sql_error = None, None
                if sql_query:
                    try:
                        with engine.connect() as conn:
                            result_df = pd.read_sql(text(sql_query), conn)
                    except Exception as e:
                        sql_error = str(e)

                if result_df is not None and not result_df.empty:
                    row_count = len(result_df)
                    summary = result_df.head(20).to_dict(orient="records")
                    rephrase_prompt = f"""
You are a multilingual assistant summarizing database results.
always answer in the user's language.
User question: {user_input}
Results (first 20 of {row_count}): {summary}
"""
                    try:
                        rephrase_response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "You are a summarization assistant."},
                                {"role": "user", "content": rephrase_prompt}
                            ]
                        )
                        answer_text = rephrase_response.choices[0].message.content.strip()
                    except:
                        answer_text = "Here are the results found."

                    st.markdown(answer_text)
                    st.dataframe(result_df, use_container_width=True)
                    csv = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button("📥 Download Results (CSV)", csv, "hajj_results.csv", "text/csv")
                    with st.expander("🔍 View SQL Query"):
                        st.code(sql_query, language="sql")

                    st.session_state.chat_memory.append({
                        "role": "assistant",
                        "content": answer_text,
                        "dataframe": result_df,
                        "timestamp": time.time()
                    })
                elif sql_error:
                    st.error("⚠️ Database error. Try rephrasing your question.")
                    with st.expander("Details"):
                        st.code(f"SQL: {sql_query}\n\nError: {sql_error}")
                else:
                    no_res = "عذراً، لم أجد نتائج مطابقة." if language == "العربية" else "I couldn't find any matching results."
                    st.info(no_res)
                    st.session_state.chat_memory.append({"role": "assistant", "content": no_res, "timestamp": time.time()})
