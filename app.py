import streamlit as st
import pandas as pd
from sqlalchemy import create_engine, text
from openai import OpenAI
from rapidfuzz import process, fuzz

# --- Connect to local database ---
engine = create_engine("sqlite:///hajj_companies.db")
api_key = st.secrets["key"]
client = OpenAI(api_key=api_key)

# --- Streamlit setup ---
st.set_page_config(page_title="🕋 Hajj Chatbot", page_icon="🕋", layout="centered")
st.title("🕋 Hajj Data Chatbot")
st.caption("Ask questions about Hajj companies, their cities, countries, emails, or authorization status.")

# --- Memory (list of messages) ---
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = []

# --- Display chat history ---
for msg in st.session_state.chat_memory:
    with st.chat_message(msg["role"]):
        st.markdown(msg["content"])

# --- Fuzzy filter function ---
def fuzzy_filter(df, columns, query, threshold=80):
    mask = pd.Series(False, index=df.index)
    for col in columns:
        matches = process.extract(query, df[col], scorer=fuzz.token_sort_ratio, limit=None)
        for value, score, idx in matches:
            if score >= threshold:
                mask[idx] = True
    return df[mask]

# --- User input ---
if user_input := st.chat_input("Ask a question about Hajj companies..."):
    st.session_state.chat_memory.append({"role": "user", "content": user_input})
    with st.chat_message("user"):
        st.markdown(user_input)

    # --- Step 1: Generate SQL query ---
    prompt_sql = f"""
You are a Text-to-SQL assistant for a database of Hajj agencies.
The database has a table 'agencies' with columns:
- hajj_company_ar
- hajj_company_en
- city
- country
- email
- is_authorized

Convert the following user question into a valid SQL query.
If no valid SQL can be generated from the question, reply politely.
Return only the SQL query.
Question: {user_input}
"""
    try:
        sql_response = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You are a Text-to-SQL and translation assistant for Hajj agencies."},
                {"role": "user", "content": prompt_sql}
            ]
        )
        sql_query = sql_response.choices[0].message.content.strip("`").replace("sql", "").strip()
    except Exception as e:
        sql_query = None
        st.error(f"Error generating SQL: {e}")

    # --- Step 2: Execute SQL & Fuzzy Search ---
    try:
        if sql_query:
            with engine.connect() as conn:
                result_df = pd.read_sql(text(sql_query), conn)

            # Apply fuzzy search on key columns
            result_df = fuzzy_filter(
                result_df,
                columns=["hajj_company_ar", "hajj_company_en", "city", "country"],
                query=user_input,
                threshold=80
            )
        else:
            result_df = pd.DataFrame()
    except Exception as e:
        result_df = pd.DataFrame({"Error": [str(e)]})

    # --- Step 3: Rephrase results naturally (multilingual) ---
    if not result_df.empty:
        summary_data = result_df.head(10).to_dict(orient="records")
        rephrase_prompt = f"""
You are a multilingual assistant explaining results naturally.
- Detect the user's language automatically (Arabic or English).
- Reply in the same language.
- Do NOT mention SQL or databases.

User question: {user_input}
Conversation so far: {st.session_state.chat_memory}
Database results: {summary_data}
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
        except Exception:
            answer_text = "I found some results, but couldn't summarize them right now."
    else:
        # Detect Arabic
        if any("\u0600" <= ch <= "\u06FF" for ch in user_input):
            answer_text = "لم أجد نتائج مطابقة في قاعدة البيانات. يرجى المحاولة مرة أخرى أو توضيح السؤال أكثر."
        else:
            answer_text = "I couldn't find any matching results in the database. Please try another query or provide more details."

    # --- Step 4: Display & Save Assistant Response ---
    with st.chat_message("assistant"):
        st.markdown(answer_text)

    st.session_state.chat_memory.append({"role": "assistant", "content": answer_text})

# --- Optional: Clear chat memory ---
if st.sidebar.button("🧹 Clear Memory"):
    st.session_state.chat_memory = []
    st.experimental_rerun()
