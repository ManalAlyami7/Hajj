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


class RobustMemory:
    """بديل مضمون للذاكرة بدون Langchain"""
    
    def __init__(self, max_history=20):
        self.max_history = max_history
        self._init_session_state()
    
    def _init_session_state(self):
        if "chat_memory" not in st.session_state:
            st.session_state.chat_memory = []
        if "last_company_name" not in st.session_state:
            st.session_state.last_company_name = ""
        if "conversation_context" not in st.session_state:
            st.session_state.conversation_context = []
    
    def add_message(self, role: str, content: str):
        self._init_session_state()
        message = {"role": role, "content": content, "timestamp": datetime.now().isoformat()}
        st.session_state.chat_memory.append(message)
        
        if len(st.session_state.chat_memory) > self.max_history:
            st.session_state.chat_memory = st.session_state.chat_memory[-self.max_history:]
    
    def get_recent_messages(self, limit: int = 10) -> List[Dict]:
       
        self._init_session_state()
        return st.session_state.chat_memory[-limit:] if st.session_state.chat_memory else []
    
    def get_conversation_context(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
     
        messages = self.get_recent_messages(limit or self.max_history)
        return [{"role": msg["role"], "content": msg["content"]} for msg in messages]
    
    def store_last_company(self, company_name: str):
       
        if company_name:
            normalized_name = normalize_company_name(company_name)
            st.session_state.last_company_name = normalized_name
    
    def get_last_company(self) -> str:
     
        return st.session_state.get("last_company_name", "")
    
    def clear_memory(self):
       
        st.session_state.chat_memory = []
        st.session_state.last_company_name = ""
        st.session_state.conversation_context = []


class LLMManager:
   
    
    def __init__(self):
        self.memory = RobustMemory(max_history=20)
        self.client = self._init_openai_client()
        
        # أصوات TTS حسب اللغة
        self.voice_map = {
            "العربية": "onyx",
            "English": "alloy"
        }
    
    def _init_openai_client(self):
        api_key = st.secrets.get("key")
        if not api_key:
            logger.error("OpenAI API key not found")
            st.warning("⚠️ OpenAI API key missing in Streamlit secrets")
            st.stop()
        return OpenAI(api_key=api_key)
    
    def store_last_company(self, company_name: str):
        self.memory.store_last_company(company_name)
    
    def get_last_company(self) -> str:
        return self.memory.get_last_company()
    
    def add_user_message(self, user_input: str):
        self.memory.add_message("user", user_input)
    
    def add_assistant_message(self, assistant_reply: str):
        self.memory.add_message("assistant", assistant_reply)
    
    def build_chat_context(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """بناء سياق المحادثة (واجهة متوافقة)"""
        return self.memory.get_conversation_context(limit)
    
    def ask(self, user_input: str) -> str:
        """
        بديل عن conversation.predict مع الذاكرة المضمونة
        """
        try:
            # بناء السياق من الذاكرة
            context_messages = self.build_chat_context(limit=10)
            
            # إعداد الرسائل للنموذج
            messages = []
            
            # إضافة رسائل السياق أولاً
            for msg in context_messages:
                messages.append({"role": msg["role"], "content": msg["content"]})
            
            # إضافة الرسالة الحالية
            messages.append({"role": "user", "content": user_input})
            
            # استدعاء OpenAI مباشرة
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.4,
                max_tokens=1000
            )
            
            assistant_reply = response.choices[0].message.content.strip()
            
            # ✅ تخزين في الذاكرة - هذا كان ناقص!
            self.add_user_message(user_input)
            self.add_assistant_message(assistant_reply)
            
            return assistant_reply
            
        except Exception as e:
            logger.error(f"Ask method failed: {e}")
            return "I apologize, but I encountered an error. Please try again."
    
    def detect_intent(self, user_input: str, language: str) -> Dict:
        """
        Detect user intent using robust memory system
        """
        # بناء السياق من الذاكرة
        context = self.build_chat_context(limit=5)
        context_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context])
        
        intent_prompt = f"""
        You are a fraud-prevention assistant for Hajj pilgrims.
    
        📋 Classify this message into ONE of four categories:
        
        1️⃣ GREETING: Greetings, hello, hi, how are you, salam, السلام عليكم, مرحبا
        
        2️⃣ DATABASE: Questions about verifying specific Hajj agencies, authorization, company details, locations, contacts
        
        3️⃣ GENERAL_HAJJ: General Hajj-related questions (rituals, requirements, documents, safety, procedures)
        
        4️⃣ NEEDS_INFO: Vague messages that need more details
        
        🔍 COMPANY EXTRACTION:
        Extract any company name mentioned in the user's message and return it in 'extracted_company'.
        
        Examples of company mentions:
        - "شركة جبل عمر" → extracted_company: "جبل عمر"
        - "Royal City Agency" → extracted_company: "Royal City"
        - "وكالة الهدى" → extracted_company: "الهدى"
        - "Al Safa Travel" → extracted_company: "Al Safa"
        
        🚨 CRITICAL CONTEXT:
        - 415 fake Hajj offices closed in 2025
        - 269,000+ unauthorized pilgrims stopped
        - Mission: prevent fraud, protect pilgrims
        - For DATABASE questions, we need specific agency names or clear location criteria
        
        Conversation Context:
        {context_text}
        
        User Message: {user_input}
        
        Classify the intent, provide confidence score, and explain your reasoning in JSON format.
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
        """Fallback intent detection using heuristics when API fails"""
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
        """Generate natural greeting response using LLM memory automatically"""
        context = self.build_chat_context(limit=5)
        context_text = "\n".join([f"{msg['role']}: {msg['content']}" for msg in context])
        
        system_prompt = """
        You are a friendly Hajj and fraud prevention assistant designed to protect pilgrims from scams and help them verify Hajj agencies authorized by the Ministry of Hajj and Umrah.
        💡 INSTRUCTIONS:
        - Use the full conversation context automatically (remember user's name, language, and previous messages).
        - Respond in Arabic if the user input contains Arabic text; otherwise, respond in English.
        - Generate a short, warm, natural greeting (max 3 sentences) that:
        - Acknowledges the user's greeting
        - Expresses willingness to help
        - Mentions you can help verify Hajj companies
        - Uses emojis appropriately
        - Keep responses concise, friendly, and professional.
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
        """Generate answer for general Hajj questions using robust memory system"""
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
        """ 
        Generate SQL query from user input with structured output and context awareness
        using robust memory system.
        Returns: Dict with sql_query, query_type, filters, explanation, safety_checked.
        """
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
        """Generate natural, friendly, and structured summary of query results.
           Uses robust memory system and normalizes company names for consistent memory handling.
           Adds assistant-like sentences and recommendations based on user intent.
           Auto-detects language from user input for accurate responses.
           Handles missing or not found data intelligently.
           Responds with only the requested columns unless "all info" is requested. """
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
        - User question language: {language}
        - You MUST respond in {language} ONLY
        - If language is "العربية", respond COMPLETELY in Arabic
        - If language is "English", respond COMPLETELY in English
        - Do NOT mix languages in your response
        
        Your task:
        → Summarize SQL query results clearly and naturally, with a warm, conversational tone that feels friendly and professional.
        
        User question: {user_input}
        Data: {data_preview}
        
        Instructions:
        - ALWAYS respond in {language}
        - Always acknowledge the user's question in {language}
        - Arabic examples: "بناءً على البيانات، وجدت لك النتائج التالية:" أو "إليك ما وجدته:"
        - English examples: "Here are the results I found for you:" or "Based on the data, here's what I found:"
        - Be concise and clear
        - Highlight number of matching records
        - Provide actionable advice if relevant
        - Use emojis sparingly to enhance friendliness
        - Use a mix of sentences and bullet points
        
        Behavior:
        1️⃣ If the user mentions the word "agency" or "company" or "شركة" or "وكالة" in their question:
           - Extract and summarize all available data for the agency/agencies that match the name mentioned.
           - Use all default columns if they request "all information".
           - Always include Google Maps Link.
        
        2️⃣ If the user does NOT mention "agency" or the context is unclear:
           - Politely ask the user to clarify what they would like to know IN {language}.
        
        Columns to include in summary:
        - hajj_company_en, hajj_company_ar, formatted_address, 
        - city, country, email, contact_Info, rating_reviews, is_authorized,
        - google_maps_link
        
        🚨 CRITICAL LANGUAGE-SPECIFIC RULES:
        - If {language} is "العربية":
          * Translate ALL field names to Arabic
          * city → المدينة
          * country → الدولة
          * email → البريد الإلكتروني
          * contact_Info → رقم التواصل
          * rating_reviews → التقييم
          * is_authorized → مصرح / معتمد (translate "Yes" to "نعم، معتمد" and "No" to "لا، غير معتمد")
          * formatted_address → العنوان
          * Google Maps Link → رابط خرائط جوجل
        
        - If {language} is "English":
          * Keep all field names in English
          * is_authorized → translate to "Yes, Authorized" or "No, Not Authorized"
        
        Behavior based on user question:
        - If the user asks about a **specific column**, provide only that column's data IN {language}
        - If the user asks for **all information** or does not specify, provide all default columns IN {language}
        - ALWAYS respond in {language} - this is CRITICAL
        - Include contact info and Google Maps link if available
        - Ensure the response is complete and readable, no truncated or missing information
        - You are designed to protect pilgrims from scams and help them verify hajj agencies authorized from Ministry of Hajj and Umrah
        
        - Always include Google Maps Link exactly as it appears in the column `google_maps_link`.
        
        🌍 OUTPUT FORMAT:
        
        If {language} is "العربية", use this format:
        - الاسم (بالعربية / بالإنجليزية):
        - المدينة:
        - الدولة:
        - البريد الإلكتروني:
        - رقم التواصل:
        - التقييم:
        - الحالة: (نعم، معتمد / لا، غير معتمد)
        - رابط خرائط جوجل:
        
        If {language} is "English", use this format:
        - Name (Arabic / English):
        - City:
        - Country:
        - Email:
        - Contact Info:
        - Rating:
        - Status: (Yes, Authorized / No, Not Authorized)
        - Google Maps Link:
        
        - Keep tone friendly, professional, and natural IN {language}
        - Mix sentences and bullets; add small friendly phrases if appropriate IN {language}
        - Do NOT invent any data
        - If rows count more than 1, list the names and important details of up to 10 agencies, use numbers or bullets and emojis if appropriate
        - REMEMBER: Your ENTIRE response must be in {language}
        
        Feel free to:
        - Mix sentences and bullet points (in {language})
        - Add small friendly phrases like "يمكنك التواصل معهم بثقة." (Arabic) or "You can contact them confidently." (English)
        - Vary sentence structure per agency
        - Keep summary concise and readable
        - BUT ALWAYS IN {language} ONLY
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
        Your task is to ask the user for more specific details if their question is vague.
        Respond in {language} ONLY.
        
        Instructions:
        - Keep the response short (2-3 sentences), friendly, and professional.
        - Ask for agency name, location (city/country/Google Maps link), and what they want to know.
        - Provide one clear example of a well-formed question.
        - Output ONLY valid JSON matching this structure:

        {{
            "needs_info": "<friendly message asking for more details>",
            "suggestions": ["<example suggestion 1>", "<example suggestion 2>"],
            "missing_info": ["<list missing pieces of info>"],
            "sample_query": "<example of a well-formed query>"
        }}
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
        """Get SQL generation system prompt with context awareness"""
        return f"""
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
        - google_maps_link
        - link_valid (boolean)

        --------------------------------------------
        🔍 LANGUAGE DETECTION RULES:
        1. Detect if the user's question is in Arabic or English. And respond in the same language.
        2. Respond with SQL query **only**, no text.
        3. Keep text fragments (LIKE clauses) in both Arabic and English for robustness.
        4. Translate city and country if needed based on user language.

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
        - If the user explicitly mentions a company or agency using any of these words:
            ["شركة", "وكالة", "مؤسسة", "agency", "company", "travel", "tour", "establishment"]
            then treat it as an exact company name request.
            Use **flexible LIKE matching** with LOWER(TRIM()):
            WHERE (LOWER(TRIM(hajj_company_ar)) LIKE LOWER('%الاسم%') 
                    OR LOWER(TRIM(hajj_company_en)) LIKE LOWER('%name%'))
        - Otherwise (for general keywords like "الحرمين" or "الهدى" without context),
            use LIKE for partial matches.
        3. "Number of ..." or "How many ..." → use `SELECT COUNT(*)`
        4. "Countries" or "number of countries" → use:
            - `SELECT COUNT(DISTINCT country)` if asking how many
            - `SELECT DISTINCT country` if asking for list
            - Always based on agencies table
        5. "Cities" or "number of cities" → same logic as above but for `city`
        6. Never assume or add "Saudi Arabia" unless mentioned explicitly.
        7. When user asks about "countries that have agencies" → use `DISTINCT country` from `agencies`
        8. Always return agency-related data only, not external or world data.

        --------------------------------------------
        🔗 FOLLOW-UP QUESTION HANDLING:
        - If a context note mentions a previously mentioned company, focus the query on that company
        - Use flexible LIKE matching to find the company in both Arabic and English columns
        - Example: If context says "about جبل عمر", include:
        WHERE (LOWER(TRIM(hajj_company_ar)) LIKE '%جبل%عمر%' 
                OR LOWER(TRIM(hajj_company_en)) LIKE '%jabal%omar%')

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
        ⚙️ COMPANY NAME MATCHING:
        - Always normalize and deduplicate company names using LOWER(TRIM()).
        - Use SELECT DISTINCT to avoid duplicates.
        - Use flexible LIKE matching with wildcards: LIKE '%term%'

        --------------------------------------------
        ✅ EXAMPLES:

        Q: "هل شركة جبل عمر معتمدة؟"
        → SELECT DISTINCT hajj_company_en, hajj_company_ar, formatted_address, city, country, email, contact_Info, rating_reviews, is_authorized, google_maps_link
        FROM agencies
        WHERE (LOWER(TRIM(hajj_company_ar)) LIKE '%جبل%عمر%' 
            OR LOWER(TRIM(hajj_company_en)) LIKE '%jabal%omar%')
        LIMIT 1;

        Q: "وين موقعها؟" (with context: about "جبل عمر")
        → SELECT formatted_address, city, country, google_maps_link 
        FROM agencies 
        WHERE (LOWER(TRIM(hajj_company_ar)) LIKE '%جبل%عمر%'
            OR LOWER(TRIM(hajj_company_en)) LIKE '%jabal%omar%')
        LIMIT 1;

        Q: "هل موجودة في الرياض؟" (with context: about "جبل عمر")
        → SELECT hajj_company_en, hajj_company_ar, city, country, formatted_address
        FROM agencies
        WHERE (LOWER(TRIM(hajj_company_ar)) LIKE '%جبل%عمر%'
            OR LOWER(TRIM(hajj_company_en)) LIKE '%jabal%omar%')
        AND (city LIKE '%الرياض%' OR LOWER(city) LIKE '%riyadh%')
        LIMIT 1;

        Q: "Authorized agencies in Makkah"
        → SELECT * FROM agencies 
        WHERE is_authorized = 'Yes' 
        AND (city LIKE '%مكة%' OR LOWER(city) LIKE '%mecca%' OR LOWER(city) LIKE '%makkah%') 
        LIMIT 100;

        Q: "كم عدد الشركات في المدينة؟"
        → SELECT COUNT(*) FROM agencies 
        WHERE (city LIKE '%المدينة%' OR LOWER(city) LIKE '%medina%' OR LOWER(city) LIKE '%madinah%');

        Q: "How many countries have agencies?"
        → SELECT COUNT(DISTINCT country) FROM agencies;

        Q: "List of countries that have agencies"
        → SELECT DISTINCT country FROM agencies LIMIT 100;

        Q: "رقم التواصل؟" (with context: about "الهدى")
        → SELECT contact_Info, hajj_company_ar, hajj_company_en 
        FROM agencies 
        WHERE (LOWER(TRIM(hajj_company_ar)) LIKE '%الهدى%'
            OR LOWER(TRIM(hajj_company_en)) LIKE '%huda%')
        LIMIT 1;
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
