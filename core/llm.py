import re
import io
import json
import logging
import streamlit as st
from typing import Optional, List, Dict
from pydantic import BaseModel, Field
import openai

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_company_name(name: str) -> str:
    if not name:
        return ""
    name = name.lower()
    name = " ".join(name.split())
    name = re.sub(r'[^\w\s]', '', name)
    return name

def detect_intent(self, user_input: str, language: Optional[str] = None) -> Dict:
    arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
    english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
    total = arabic_chars + english_chars
    if total == 0:
        return "English"
    return "العربية" if arabic_chars / total > 0.3 else "English"

class LLMManager:
    def __init__(self):
        if "chat_memory" not in st.session_state:
            st.session_state.chat_memory = []
        if "last_company_name" not in st.session_state:
            st.session_state.last_company_name = ""

        self.voice_map = {"العربية": "onyx", "English": "alloy"}

        # -----------------------------
        # OpenAI API key
        # -----------------------------
        self.api_key = st.secrets.get("key")
        if not self.api_key:
            logger.error("OpenAI API key missing")
            st.warning("⚠️ OpenAI API key missing in Streamlit secrets")
            st.stop()
        openai.api_key = self.api_key
        self.client = openai

    # -----------------------------
    # Memory management
    # -----------------------------
    def store_last_company(self, company_name: str):
        if company_name:
            st.session_state.last_company_name = normalize_company_name(company_name)

    def get_last_company(self) -> str:
        return st.session_state.get("last_company_name", "")

    def add_user_message(self, user_input: str):
        st.session_state.chat_memory.append({"role": "user", "content": user_input})

    def add_assistant_message(self, assistant_reply: str):
        st.session_state.chat_memory.append({"role": "assistant", "content": assistant_reply})

    def build_chat_context(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        mem = st.session_state.chat_memory
        return mem if limit is None else mem[-limit:]

    # -----------------------------
    # Unified OpenAI call
    # -----------------------------
    def _chat_completion(self, messages: List[Dict], temperature=0.4) -> str:
        try:
            response = openai.ChatCompletion.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=temperature
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            logger.error(f"OpenAI ChatCompletion failed: {e}")
            return "حدث خطأ أثناء معالجة طلبك."

    # -----------------------------
    # Generic ask
    # -----------------------------
    def ask(self, user_input: str) -> str:
        self.add_user_message(user_input)
        context = self.build_chat_context(limit=10)
        messages = [{"role": "system", "content": "You are a helpful Hajj assistant."}]
        messages.extend(context)
        messages.append({"role": "user", "content": user_input})
        reply = self._chat_completion(messages)
        self.add_assistant_message(reply)
        return reply

    # -----------------------------
    # Fallback intent detection
    # -----------------------------
    def _fallback_intent_detection(self, user_input: str) -> Dict:
        ui = user_input.lower()
        if any(g in ui for g in ["hello", "hi", "salam", "السلام", "مرحبا"]):
            intent = "GREETING"
        elif any(k in ui for k in ["company", "agency", "معتمد", "شركات", "authorized", "وكالة"]):
            intent = "DATABASE" if len(ui.split()) >= 4 else "NEEDS_INFO"
        else:
            intent = "GENERAL_HAJJ"
        return {"intent": intent, "confidence": 0.7, "reasoning": "Determined by keyword matching (fallback)"}

    # -----------------------------
    # Intent detection
    # -----------------------------
    def detect_intent(self, user_input: str) -> Dict:
        context = self.build_chat_context(limit=10)
        prompt = f"Classify this message and extract any company name: {user_input}"
        messages = [{"role": "system", "content": prompt}]
        messages.extend(context)
        messages.append({"role": "user", "content": user_input})
        response_text = self._chat_completion(messages)
        try:
            return json.loads(response_text)
        except json.JSONDecodeError:
            return self._fallback_intent_detection(user_input)

    # -----------------------------
    # Greeting generation
    # -----------------------------
    def generate_greeting(self, user_input: str, language: str) -> str:
        is_arabic = language == "العربية"
        system_prompt = f"""
        You are a friendly Hajj and fraud prevention assistant.
        Respond in {language} only, max 3 sentences.
        Be warm, professional, acknowledge greeting, offer help verifying Hajj companies.
        """
        context = self.build_chat_context(limit=10)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(context)
        messages.append({"role": "user", "content": user_input})
        reply = self._chat_completion(messages)
        self.add_assistant_message(reply)
        if not reply:
            return "السلام عليكم! 👋 كيف يمكنني مساعدتك؟" if is_arabic else "Hello! 👋 How can I help you today?"
        return reply

    # -----------------------------
    # General Hajj answer
    # -----------------------------
    def generate_general_answer(self, user_input: str, language: str) -> str:
        system_prompt = f"""
        You are a helpful Hajj assistant. Respond in {language} only. Be factual, concise, friendly.
        """
        context = self.build_chat_context(limit=10)
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(context)
        messages.append({"role": "user", "content": user_input})
        reply = self._chat_completion(messages)
        self.add_assistant_message(reply)
        if not reply:
            return "حدث خطأ. يرجى إعادة صياغة سؤالك." if language == "العربية" else "I encountered an error. Please try rephrasing your question."
        return reply

    # -----------------------------
    # SQL generation
    # -----------------------------
    def generate_sql(self, user_input: str, language: str) -> Optional[Dict]:
        sql_prompt = f"Generate SQL query for Hajj agencies based on user question (language: {language}): {user_input}"
        context = self.build_chat_context(limit=10)
        messages = [{"role": "system", "content": sql_prompt}]
        messages.extend(context)
        messages.append({"role": "user", "content": user_input})
        response_text = self._chat_completion(messages)
        try:
            sql_data = json.loads(response_text)
            if sql_data.get("sql_query") and sql_data.get("safety_checked"):
                return {
                    "sql_query": sql_data.get("sql_query"),
                    "query_type": sql_data.get("query_type"),
                    "filters": sql_data.get("filters_applied", []),
                    "explanation": sql_data.get("explanation"),
                    "safety_checked": sql_data.get("safety_checked")
                }
        except json.JSONDecodeError:
            logger.error("SQL generation JSON decode failed.")
        return None

    # -----------------------------
    # Query summary
    # -----------------------------
    def generate_summary(self, user_input: str, language: str, row_count: int, sample_rows: List[Dict]) -> Dict:
        if row_count == 0:
            return {"summary": "لم يتم العثور على نتائج." if language=="العربية" else "No results found."}

        if sample_rows:
            last_agency = sample_rows[0].get("hajj_company_en") or sample_rows[0].get("hajj_company_ar")
            self.store_last_company(last_agency)

        data_preview = json.dumps(sample_rows[:50], ensure_ascii=False)
        summary_prompt = f"""
        Summarize the following Hajj agency data in {language} for the user query: {user_input}
        Data: {data_preview}
        Respond in friendly, professional tone. Include Google Maps link.
        """
        context = self.build_chat_context(limit=10)
        messages = [{"role": "system", "content": summary_prompt}]
        messages.extend(context)
        messages.append({"role": "user", "content": user_input})
        response_text = self._chat_completion(messages)
        try:
            return {"summary": json.loads(response_text).get("summary", "")}
        except json.JSONDecodeError:
            return {"summary": f"📊 Found {row_count} matching records."}

    # -----------------------------
    # Ask for more info
    # -----------------------------
    def ask_for_more_info(self, user_input: str, language: str) -> Dict:
        system_prompt = f"""
        Ask user for more details if their question is vague. Respond in {language} only.
        Output JSON with keys: needs_info, suggestions, missing_info, sample_query
        """
        messages = [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": user_input}
        ]
        response_text = self._chat_completion(messages)
        try:
            info_data = json.loads(response_text)
            return {
                "needs_info": info_data.get("needs_info", ""),
                "suggestions": info_data.get("suggestions", []),
                "missing_info": info_data.get("missing_info", []),
                "sample_query": info_data.get("sample_query", "")
            }
        except json.JSONDecodeError:
            is_arabic = language=="العربية"
            return {
                "needs_info": "عذراً، هل يمكنك تقديم المزيد من التفاصيل؟ 🤔" if is_arabic else "Could you provide more details? 🤔",
                "suggestions": ["هل شركة الهدى للحج معتمدة؟"] if is_arabic else ["Is Al Huda Hajj Agency authorized?"],
                "missing_info": ["اسم الوكالة", "الموقع"] if is_arabic else ["agency name", "location"],
                "sample_query": "هل شركة الهدى للحج معتمدة؟" if is_arabic else "Is Al Huda Hajj Agency authorized?"
            }

    # -----------------------------
    # Text to Speech
    # -----------------------------
    def text_to_speech(self, text: str, language: str) -> Optional[io.BytesIO]:
        voice = self.voice_map.get(language, "alloy")
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text,
                response_format="mp3"
            )
            audio_bytes = io.BytesIO(response.content)
            audio_bytes.seek(0)
            return audio_bytes
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return None
