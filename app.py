import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from openai import OpenAI
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
    /* Main container styling */
    .main {
        background: linear-gradient(135deg, #f5f7fa 0%, #c3cfe2 100%);
    }
    
    /* Header styling */
    .stTitle {
        color: #1e3a5f;
        font-weight: 700;
        text-align: center;
        padding: 1rem 0;
    }
    
    /* Chat message styling */
    .stChatMessage {
        background-color: white;
        border-radius: 15px;
        padding: 1rem;
        margin: 0.5rem 0;
        box-shadow: 0 2px 8px rgba(0,0,0,0.1);
    }
    
    /* Sidebar styling */
    .css-1d391kg {
        background: linear-gradient(180deg, #1e3a5f 0%, #2c5f8d 100%);
    }
    
    /* Example questions styling */
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
    
    /* Stats card styling */
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
    
    /* Table styling */
    .dataframe {
        border-radius: 10px;
        overflow: hidden;
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
    api_key = st.secrets["key"]
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
            return {
                'total': total_agencies,
                'authorized': authorized,
                'countries': countries,
                'cities': cities
            }
    except:
        return None

# --- Sidebar ---
with st.sidebar:
    st.markdown("### 🕋 Hajj Data Assistant")
    st.markdown("---")
    
    # Database Statistics
    st.markdown("### 📊 Database Statistics")
    stats = get_db_stats()
    
    if stats:
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats['total']}</div>
                <div class="stat-label">Total Agencies</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats['countries']}</div>
                <div class="stat-label">Countries</div>
            </div>
            """, unsafe_allow_html=True)
        
        with col2:
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats['authorized']}</div>
                <div class="stat-label">Authorized</div>
            </div>
            """, unsafe_allow_html=True)
            
            st.markdown(f"""
            <div class="stat-card">
                <div class="stat-number">{stats['cities']}</div>
                <div class="stat-label">Cities</div>
            </div>
            """, unsafe_allow_html=True)
    
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
    
    # Clear chat button
    if st.button("🧹 Clear Chat History", use_container_width=True):
        st.session_state.chat_memory = []
        st.rerun()
    
    st.markdown("---")
    st.markdown("### ℹ️ About")
    st.markdown("""
    This chatbot helps you explore Hajj company data using natural language.
    
    **Features:**
    - 🌍 Multilingual (Arabic/English)
    - 🔍 Natural language queries
    - 📊 Data visualization
    - 💾 Export results
    """)

# --- Main Content ---
st.title("🕋 Hajj Data Chatbot")
st.markdown("""
<div style='text-align: center; padding: 1rem; background: white; border-radius: 10px; margin-bottom: 2rem;'>
    <p style='color: #666; margin: 0;'>
        Ask questions about Hajj companies, their cities, countries, emails, or authorization status in Arabic or English.
    </p>
</div>
""", unsafe_allow_html=True)

# --- Initialize session state ---
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = []
    # Add welcome message
    st.session_state.chat_memory.append({
        "role": "assistant",
        "content": "السلام عليكم! Welcome to the Hajj Data Chatbot. I can help you find information about Hajj companies. Try asking me a question or click on an example from the sidebar!"
    })

if "last_result_df" not in st.session_state:
    st.session_state.last_result_df = None

if "selected_question" not in st.session_state:
    st.session_state.selected_question = None

# --- Display chat history ---
for msg in st.session_state.chat_memory:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])
        
        # Show table if it exists in the message
        if "dataframe" in msg:
            st.dataframe(msg["dataframe"], use_container_width=True)
            
            # Add download button
            csv = msg["dataframe"].to_csv(index=False).encode('utf-8')
            st.download_button(
                label="📥 Download Results (CSV)",
                data=csv,
                file_name="hajj_companies_results.csv",
                mime="text/csv",
                key=f"download_{msg.get('timestamp', 0)}"
            )

# --- Handle selected example question ---
if st.session_state.selected_question:
    user_input = st.session_state.selected_question
    st.session_state.selected_question = None
else:
    user_input = st.chat_input("Ask a question about Hajj companies...")

# --- Process user input ---
if user_input:
    # Add user message to memory
    st.session_state.chat_memory.append({"role": "user", "content": user_input})

    # Display user message
    with st.chat_message("user"):
        st.markdown(user_input)

    # Show loading spinner
    with st.chat_message("assistant"):
        with st.spinner("🤔 Thinking..."):
            # --- Step 0: Detect intent (greeting, database query, or general Hajj question) ---
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
            except Exception as e:
                intent = "DATABASE"  # Default to database query if intent detection fails
            
            # --- Handle GREETING intent ---
            if intent == "GREETING":
                greeting_prompt = f"""
You are a friendly Hajj information assistant. The user has greeted you.
Respond warmly in the same language they used (Arabic or English).
Keep it brief and friendly, and let them know you can help with:
- Information about Hajj companies and agencies
- General questions about Hajj rituals and requirements

User message: {user_input}
"""
                try:
                    greeting_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a friendly multilingual Hajj assistant."},
                            {"role": "user", "content": greeting_prompt}
                        ]
                    )
                    answer_text = greeting_response.choices[0].message.content.strip()
                except Exception as e:
                    # Fallback greeting
                    if any("\u0600" <= ch <= "\u06FF" for ch in user_input):
                        answer_text = "السلام عليكم ورحمة الله وبركاته! كيف يمكنني مساعدتك اليوم؟ يمكنني مساعدتك في معلومات عن شركات الحج أو الإجابة على أسئلة عامة عن الحج."
                    else:
                        answer_text = "Hello! How can I help you today? I can assist you with information about Hajj companies or answer general questions about Hajj."
                
                st.markdown(answer_text)
                st.session_state.chat_memory.append({
                    "role": "assistant",
                    "content": answer_text
                })
            
            # --- Handle GENERAL_HAJJ intent ---
            elif intent == "GENERAL_HAJJ":
                hajj_prompt = f"""
You are a knowledgeable Hajj information assistant. Answer the user's question about Hajj.
- Detect the user's language (Arabic or English) and respond in the same language
- Provide accurate, helpful information about Hajj rituals, requirements, history, etc.
- Be concise but informative
- If you're not sure, be honest about it

User question: {user_input}

Previous conversation context:
{st.session_state.chat_memory[-5:] if len(st.session_state.chat_memory) > 1 else []}
"""
                try:
                    hajj_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a knowledgeable multilingual Hajj information assistant."},
                            {"role": "user", "content": hajj_prompt}
                        ]
                    )
                    answer_text = hajj_response.choices[0].message.content.strip()
                except Exception as e:
                    if any("\u0600" <= ch <= "\u06FF" for ch in user_input):
                        answer_text = "عذراً، واجهت مشكلة في الإجابة على سؤالك. يرجى المحاولة مرة أخرى."
                    else:
                        answer_text = "I'm sorry, I encountered an issue answering your question. Please try again."
                
                st.markdown(answer_text)
                st.session_state.chat_memory.append({
                    "role": "assistant",
                    "content": answer_text
                })
            
            # --- Handle DATABASE intent ---
            else:
                # --- Step 1: Generate SQL query ---
                prompt_sql = f"""
You are a Text-to-SQL assistant for a database of Hajj agencies.
The database has a table 'agencies' with columns:
- hajj_company_ar (Arabic name)
- hajj_company_en (English name)
- city
- country
- email
- is_authorized (Yes for authorized, No for not authorized)

Convert the following user question into a valid SQL query.
If no valid SQL can be generated from the question, return "NO_SQL".
Return only the SQL query, no explanation, no markdown formatting.

Question: {user_input}
"""

                try:
                    sql_response = client.chat.completions.create(
                        model="gpt-4o-mini",
                        messages=[
                            {"role": "system", "content": "You are a Text-to-SQL assistant for Hajj agencies."},
                            {"role": "user", "content": prompt_sql}
                        ]
                    )
                    sql_query = sql_response.choices[0].message.content.strip().strip("`").replace("sql", "").strip()
                    
                    # Check if it's a valid SQL query
                    if sql_query == "NO_SQL" or not sql_query.upper().startswith("SELECT"):
                        sql_query = None
                        
                except Exception as e:
                    sql_query = None
                    st.error(f"⚠️ Error generating SQL: {e}")

                # --- Step 2: Execute SQL safely ---
                result_df = None
                sql_error = None
                
                if sql_query:
                    try:
                        with engine.connect() as conn:
                            result_df = pd.read_sql(text(sql_query), conn)
                    except Exception as e:
                        sql_error = str(e)
                        result_df = None

                # --- Step 3: Generate natural language response ---
                if result_df is not None and not result_df.empty:
                    summary_data = result_df.head(20).to_dict(orient="records")
                    row_count = len(result_df)

                    rephrase_prompt = f"""
You are a multilingual assistant that explains database results clearly and naturally.
- Detect the user's language automatically (Arabic or English).
- Reply in the same language.
- Do NOT mention SQL, tables, or databases.
- Be concise but friendly, like a helpful guide.
- If there are many results, mention the total count.

User question: {user_input}

Database results (showing first 20 of {row_count} total):
{summary_data}
"""

                    try:
                        rephrase_response = client.chat.completions.create(
                            model="gpt-4o-mini",
                            messages=[
                                {"role": "system", "content": "You are a multilingual summarization assistant."},
                                {"role": "user", "content": rephrase_prompt}
                            ]
                        )
                        answer_text = rephrase_response.choices[0].message.content.strip()
                    except Exception as e:
                        answer_text = "I found some results for you. Please see the table below."
                    
                    # Display answer
                    st.markdown(answer_text)
                    
                    # Display results table
                    st.dataframe(result_df, use_container_width=True)
                    
                    # Add download button
                    csv = result_df.to_csv(index=False).encode('utf-8')
                    st.download_button(
                        label="📥 Download Results (CSV)",
                        data=csv,
                        file_name="hajj_companies_results.csv",
                        mime="text/csv",
                    )
                    
                    # Show SQL query in expander for transparency
                    with st.expander("🔍 View SQL Query"):
                        st.code(sql_query, language="sql")
                    
                    # Save to memory with dataframe
                    st.session_state.chat_memory.append({
                        "role": "assistant",
                        "content": answer_text,
                        "dataframe": result_df,
                        "timestamp": time.time()
                    })
                    
                elif sql_error:
                    # SQL execution error
                    error_msg = "⚠️ I encountered an error while searching the database. Please try rephrasing your question."
                    st.error(error_msg)
                    
                    with st.expander("🔍 Technical Details"):
                        st.code(f"SQL Query:\n{sql_query}\n\nError:\n{sql_error}")
                    
                    st.session_state.chat_memory.append({
                        "role": "assistant",
                        "content": error_msg
                    })
                    
                else:
                    # No results or couldn't generate SQL
                    if any("\u0600" <= ch <= "\u06FF" for ch in user_input):
                        answer_text = "عذراً، لم أتمكن من العثور على نتائج مطابقة. يمكنك تجربة صياغة السؤال بطريقة مختلفة أو اختيار أحد الأمثلة من القائمة الجانبية."
                    else:
                        answer_text = "I couldn't find any matching results. Try rephrasing your question or select an example from the sidebar."
                    
                    st.info(answer_text)
                    
                    st.session_state.chat_memory.append({
                        "role": "assistant",
                        "content": answer_text
                    })

    # Rerun to update the chat
    st.rerun()
