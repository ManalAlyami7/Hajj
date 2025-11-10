"""
LLM Manager Module - Memory-Free Version
Handles OpenAI API interactions with robust custom memory system
"""

import random
import streamlit as st
from openai import OpenAI
import io
import re
from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field
import logging
import json
import sqlite3
from datetime import datetime

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def normalize_company_name(name: str) -> str:
    """Normalize company names for consistent memory storage and search."""
    if not name:
        return ""
    name = name.lower()
    name = " ".join(name.split())
    name = re.sub(r'[^\w\s]', '', name)
    return name

# -----------------------------
# Pydantic Models for Structured Outputs
# -----------------------------

class IntentClassification(BaseModel):
    intent: Literal["GREETING", "DATABASE", "GENERAL_HAJJ", "NEEDS_INFO"] = Field(
        description="The classified intent of the user's message"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score of the classification (0-1)"
    )
    reasoning: str = Field(
        description="Brief explanation of why this intent was chosen"
    )


class SQLQueryGeneration(BaseModel):
    sql_query: Optional[str] = Field(None, description="The generated SQL SELECT query, or None if no safe query can be generated")
    query_type: Literal["simple", "aggregation", "complex", "no_sql"] = Field(description="Type of query generated")
    filters_applied: List[str] = Field(default_factory=list, description="List of filters or conditions applied in the query")
    explanation: str = Field(description="Human-readable explanation of what the query does")
    safety_checked: bool = Field(description="Whether the query passed safety validation")


class QuerySummary(BaseModel):
    summary: str = Field(description="Natural language summary of the query results")
  

class GreetingResponse(BaseModel):
    greeting: str = Field(description="The friendly greeting message")
    tone: Literal["formal", "casual", "warm"] = Field(description="Tone of the greeting")
    includes_offer_to_help: bool = Field(description="Whether the greeting includes an offer to help")
    
    
class NEEDSInfoResponse(BaseModel):
    needs_info: str = Field(description="The message asking user for more specific information")
    suggestions: List[str] = Field(default_factory=list, description="List of example queries the user could try")
    missing_info: List[str] = Field(default_factory=list, description="List of specific information pieces needed")
    sample_query: str = Field(description="An example of a well-formed query")
    user_lang: Literal["English", "العربية"] = Field(description="Language to respond in")


class LLMManager:
    """بديل مضمون للذاكرة بدون Langchain"""
    
    def __init__(self, max_history=20):
        self.max_history = max_history
        self._init_session_state()
    
    def _init_session_state(self):
        """تهيئة حالة الجلسة إذا لم تكن موجودة"""
        if "chat_memory" not in st.session_state:
            st.session_state.chat_memory = []
        if "last_company_name" not in st.session_state:
            st.session_state.last_company_name = ""
        if "conversation_context" not in st.session_state:
            st.session_state.conversation_context = []
    
    def add_message(self, role: str, content: str):
        """إضافة رسالة للذاكرة"""
        self._init_session_state()
        message = {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        st.session_state.chat_memory.append(message)
        
        # الحفاظ على حجم الذاكرة
        if len(st.session_state.chat_memory) > self.max_history:
            st.session_state.chat_memory = st.session_state.chat_memory[-self.max_history:]
    
    def get_recent_messages(self, limit: int = 10) -> List[Dict]:
        """الحصول على آخر الرسائل"""
        self._init_session_state()
        return st.session_state.chat_memory[-limit:] if st.session_state.chat_memory else []
    
    def get_conversation_context(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """الحصول على سياق المحادثة (متوافق مع الكود الأصلي)"""
        messages = self.get_recent_messages(limit or self.max_history)
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]
    
    def store_last_company(self, company_name: str):
        """تخزين آخر شركة تم السؤال عنها"""
        if company_name:
            normalized_name = normalize_company_name(company_name)
            st.session_state.last_company_name = normalized_name
    
    def get_last_company(self) -> str:
        """الحصول على آخر شركة"""
        return st.session_state.get("last_company_name", "")
    
    def clear_memory(self):
        """مسح الذاكرة (للاستخدام في التطوير)"""
        st.session_state.chat_memory = []
        st.session_state.last_company_name = ""
        st.session_state.conversation_context = []


class LLMManager:
    """إدارة الذكاء الاصطناعي مع ذاكرة مضمونة"""
    
    def __init__(self):
        self.memory = LLMManager(max_history=20)
        self.client = self._init_openai_client()
        
        # أصوات TTS حسب اللغة
        self.voice_map = {
            "العربية": "onyx",
            "English": "alloy"
        }
    
    def _init_openai_client(self):
        """تهيئة عميل OpenAI"""
        api_key = st.secrets.get("key")
        if not api_key:
            logger.error("OpenAI API key not found")
            st.warning("⚠️ OpenAI API key missing in Streamlit secrets")
            st.stop()
        return OpenAI(api_key=api_key)
    
    def store_last_company(self, company_name: str):
        """تخزين آخر شركة (واجهة متوافقة)"""
        self.memory.store_last_company(company_name)
    
    def get_last_company(self) -> str:
        """الحصول على آخر شركة (واجهة متوافقة)"""
        return self.memory.get_last_company()
    
    def add_user_message(self, user_input: str):
        """إضافة رسالة مستخدم"""
        self.memory.add_message("user", user_input)
    
    def add_assistant_message(self, assistant_reply: str):
        """إضافة رسالة مساعد"""
        self.memory.add_message("assistant", assistant_reply)
    
    def build_chat_context(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """بناء سياق المحادثة (واجهة متوافقة)"""
        return self.memory.get_conversation_context(limit)
    
    def ask(self, user_input: str) -> str:
        """
        بديل عن conversation.predict مع الذاكرة المضمونة
        """
        # بناء السياق من الذاكرة
        context_messages = self.build_chat_context(limit=10)
        
        # إعداد الرسائل للنموذج
        messages = []
        
        # إضافة رسائل السياق
        for msg in context_messages:
            messages.append({"role": msg["role"], "content": msg["content"]})
        
        # إضافة الرسالة الحالية
        messages.append({"role": "user", "content": user_input})
        
        try:
            # استدعاء OpenAI مباشرة
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.4,
                max_tokens=1000
            )
            
            assistant_reply = response.choices[0].message.content.strip()
            
            # تخزين في الذاكرة
            self.add_user_message(user_input)
            self.add_assistant_message(assistant_reply)
            
            return assistant_reply
            
        except Exception as e:
            logger.error(f"Ask method failed: {e}")
            return "I apologize, but I encountered an error. Please try again."
    
    def detect_intent(self, user_input: str, language: str) -> Dict:
        """
        كشف النية باستخدام الذاكرة المضمونة
        """
        # بناء السياق من الذاكرة
        context = self.build_chat_context(limit=5)
        context_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context])
        
        intent_prompt = f"""
        You are a fraud-prevention assistant for Hajj pilgrims.
        
        📋 Classify this message into ONE of four categories:
        
        1️⃣ GREETING: Greetings, hello, hi, how are you, salam, السلام عليكم, مرحبا
        
        2️⃣ DATABASE: Questions about verifying specific Hajj agencies, authorization, company details
        
        3️⃣ GENERAL_HAJJ: General Hajj-related questions (rituals, requirements, procedures)
        
        4️⃣ NEEDS_INFO: Vague messages that need more details
        
        Conversation Context:
        {context_text}
        
        Message: {user_input}
        
        Extract any company name mentioned and classify the intent.
        Return JSON with: intent, confidence, reasoning, extracted_company
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are an intent classification expert. Always return valid JSON."},
                    {"role": "user", "content": intent_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            intent_data = json.loads(response.choices[0].message.content)
            logger.info(f"Intent detected: {intent_data.get('intent')}")
            
            # تخزين الشركة إذا وجدت
            extracted_company = intent_data.get('extracted_company')
            if extracted_company:
                self.store_last_company(extracted_company)
            
            return intent_data
            
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
            return self._fallback_intent_detection(user_input)
    
    def _fallback_intent_detection(self, user_input: str) -> Dict:
        """كشف النية الاحتياطي"""
        ui = user_input.lower()
        
        if any(g in ui for g in ["hello", "hi", "salam", "السلام", "مرحبا"]):
            intent = "GREETING"
        elif any(k in ui for k in ["company", "agency", "معتمد", "شركات", "authorized", "وكالة"]):
            intent = "DATABASE" if len(ui.split()) >= 4 else "NEEDS_INFO"
        else:
            intent = "GENERAL_HAJJ"
        
        return {
            "intent": intent,
            "confidence": 0.7,
            "reasoning": "Determined by keyword matching (fallback)",
            "extracted_company": ""
        }
    
    def generate_greeting(self, user_input: str, language: str) -> str:
        """توليد تحية باستخدام الذاكرة"""
        context = self.build_chat_context(limit=5)
        context_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context])
        
        system_prompt = """
        You are a friendly Hajj and fraud prevention assistant.
        - Respond in Arabic if the user input contains Arabic text; otherwise, respond in English.
        - Generate a short, warm, natural greeting (max 3 sentences)
        - Acknowledge the user's greeting and express willingness to help
        - Mention you can help verify Hajj companies
        - Use emojis appropriately
        """
        
        try:
            prompt = f"{system_prompt}\nConversation Context:\n{context_text}\n\nUser says: {user_input}"
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=200
            )
            
            greeting = response.choices[0].message.content.strip()
            
            # تحديث الذاكرة
            self.add_user_message(user_input)
            self.add_assistant_message(greeting)
            
            return greeting
            
        except Exception as e:
            logger.error(f"Greeting generation failed: {e}")
            return "Hello! 👋 How can I help you today?" if language != "العربية" else "السلام عليكم! 👋 كيف يمكنني مساعدتك؟"
    
    def generate_general_answer(self, user_input: str, language: str) -> str:
        """إجابة عامة باستخدام الذاكرة"""
        context = self.build_chat_context(limit=5)
        context_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context])
        
        system_prompt = """You are a helpful assistant specialized in Hajj information. 
        Be concise, factual, and helpful. Focus on practical information.
        Detect if the user's question is in Arabic or English, and respond in the same language.
        You are designed to protect pilgrims from scams and help them verify hajj agencies authorized from Ministry of Hajj and Umrah
        Avoid religious rulings or fatwa - stick to practical guidance."""
        
        try:
            prompt = f"{system_prompt}\nConversation Context:\n{context_text}\n\nUser asks: {user_input}"
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.4,
                max_tokens=500
            )
            
            answer = response.choices[0].message.content.strip()
            
            # تحديث الذاكرة
            self.add_user_message(user_input)
            self.add_assistant_message(answer)
            
            return answer
            
        except Exception as e:
            logger.error(f"General answer generation failed: {e}")
            return "I encountered an error. Please try rephrasing your question." if language != "العربية" else "حدث خطأ. يرجى إعادة صياغة سؤالك."
    
    def generate_sql(self, user_input: str, language: str) -> Optional[Dict]:
        """توليد استعلام SQL باستخدام الذاكرة"""
        context = self.build_chat_context(limit=3)
        context_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context])
        
        sql_prompt = self._get_sql_system_prompt(language) + f"\n\nConversation Context:\n{context_text}\n\nUser Question: {user_input}"
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Always return valid JSON."},
                    {"role": "user", "content": sql_prompt}
                ],
                temperature=0.1,
                response_format={"type": "json_object"}
            )
            
            sql_data = json.loads(response.choices[0].message.content)
            
            return {
                "sql_query": sql_data.get("sql_query"),
                "query_type": sql_data.get("query_type"),
                "filters": sql_data.get("filters_applied", []),
                "explanation": sql_data.get("explanation")
            } if sql_data.get("sql_query") and sql_data.get("safety_checked") else None
            
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return None
    
    def generate_summary(self, user_input: str, language: str, row_count: int, sample_rows: List[Dict]) -> Dict:
        """توليد ملخص باستخدام الذاكرة"""
        if row_count == 0:
            return {"summary": "No results found." if language == "English" else "لم يتم العثور على نتائج."}
        
        # تخزين آخر شركة إذا وجدت
        first_row = sample_rows[0]
        last_agency = first_row.get("hajj_company_en") or first_row.get("hajj_company_ar")
        if last_agency:
            self.store_last_company(last_agency)
        
        context = self.build_chat_context(limit=3)
        context_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context])
        data_preview = json.dumps(sample_rows[:50], ensure_ascii=False)
        
        summary_prompt = f"""
        You are a multilingual fraud-prevention and travel assistant for Hajj agencies.
        
        🚨 CRITICAL LANGUAGE RULE:
        - Respond in {language} ONLY
        
        Conversation Context:
        {context_text}
        
        User question: {user_input}
        Data: {data_preview}
        
        Generate a friendly, professional summary in {language}.
        """
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": f"You are a helpful assistant. Respond in {language} only."},
                    {"role": "user", "content": summary_prompt}
                ],
                temperature=0.4,
                max_tokens=800
            )
            
            summary = response.choices[0].message.content.strip()
            
            return {"summary": summary}
            
        except Exception as e:
            logger.error(f"Summary generation failed: {e}")
            return {"summary": f"📊 Found {row_count} matching records."}
    
    def ask_for_more_info(self, user_input: str, language: str) -> Dict:
        """طلب مزيد من المعلومات باستخدام الذاكرة"""
        context = self.build_chat_context(limit=3)
        context_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context])
        
        system_prompt = f"""
        You are a helpful Hajj verification assistant.
        Ask the user for more specific details if their question is vague.
        Respond in {language} ONLY.
        Return valid JSON with: needs_info, suggestions, missing_info, sample_query
        """
        
        try:
            prompt = f"{system_prompt}\nConversation Context:\n{context_text}\n\nUser's vague question: \"{user_input}\""
            
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": prompt}
                ],
                temperature=0.3,
                response_format={"type": "json_object"}
            )
            
            info_data = json.loads(response.choices[0].message.content)
            
            return {
                "needs_info": info_data.get("needs_info", ""),
                "suggestions": info_data.get("suggestions", []),
                "missing_info": info_data.get("missing_info", []),
                "sample_query": info_data.get("sample_query", "")
            }
            
        except Exception as e:
            logger.error(f"More info prompt generation failed: {e}")
            is_arabic = language == "العربية"
            return {
                "needs_info": "Could you provide more details? 🤔" if not is_arabic else "عذراً، هل يمكنك تقديم المزيد من التفاصيل؟ 🤔",
                "suggestions": ["Is Al Huda Hajj Agency authorized?"] if not is_arabic else ["هل شركة الهدى للحج معتمدة؟"],
                "missing_info": ["agency name", "location"] if not is_arabic else ["اسم الوكالة", "الموقع"],
                "sample_query": "Is Al Huda Hajj Agency authorized?" if not is_arabic else "هل شركة الهدى للحج معتمدة؟"
            }
    
    def text_to_speech(self, text: str, language: str) -> Optional[io.BytesIO]:
        """تحويل النص إلى كلام (بدون تغيير)"""
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
    
    def _detect_language_from_text(self, text: str) -> Optional[str]:
        """كشف اللغة من النص (بدون تغيير)"""
        if not text:
            return None
        
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        
        total_chars = arabic_chars + english_chars
        if total_chars == 0:
            return None
        
        if arabic_chars / total_chars > 0.3:
            return "العربية"
        else:
            return "English"
    
    @staticmethod
    def _get_sql_system_prompt(language: str) -> str:
        """نص SQL system prompt (بدون تغيير)"""
        return f"""
        You are a multilingual SQL fraud-prevention expert protecting Hajj pilgrims.
        Generate an SQL query for database analysis on Hajj agencies.
        Always return valid JSON with: sql_query, query_type, filters_applied, explanation, safety_checked
        
        TABLE STRUCTURE:
        - hajj_company_ar, hajj_company_en, formatted_address, city, country, email, 
        - contact_Info, rating_reviews, is_authorized, google_maps_link, link_valid
        
        Respond in {language} for explanations.
        """
    
    @staticmethod
    def _extract_sql_from_response(response_text: str) -> Optional[str]:
        """استخراج SQL من الرد (بدون تغيير)"""
        if not response_text:
            return None
        
        code_block_pattern = r'```(?:sql)?\s*(SELECT[\s\S]*?)```'
        match = re.search(code_block_pattern, response_text, re.IGNORECASE)
        if match:
            return match.group(1).strip().rstrip(';')
        
        select_pattern = r'(SELECT\s+.*?(?:;|$))'
        match = re.search(select_pattern, response_text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip().rstrip(';')
        if "NO_SQL" in response_text:
            return "NO_SQL"
        return None
