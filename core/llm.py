"""
LLM Manager Module - FIXED VERSION
Key Fix: Improved company name matching in generate_summary()
- Now uses extracted_company from context instead of raw user input
- Better fuzzy matching with normalized text
- Handles both Arabic and English company names
Added Urdu language detection and response generation
"""

import random
import streamlit as st
from openai import OpenAI
import io
import re
from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field
from rapidfuzz import fuzz
import logging
import json
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# -----------------------------
# Pydantic Models for Structured Outputs
# -----------------------------

class IntentClassification(BaseModel):
    """Structured output for intent detection"""
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
    extracted_company: Optional[str] = Field(
        None,
        description="Company name mentioned in user input (if any). Extract Arabic or English name."
    )


class SQLQueryGeneration(BaseModel):
    """Structured output for SQL query generation"""
    sql_query: Optional[str] = Field(
        None,
        description="The generated SQL SELECT query, or None if no safe query can be generated"
    )
    query_type: Literal["simple", "aggregation", "complex", "no_sql"] = Field(
        description="Type of query generated"
    )
    filters_applied: List[str] = Field(
        default_factory=list,
        description="List of filters or conditions applied in the query"
    )
    explanation: str = Field(
        description="Human-readable explanation of what the query does"
    )
    safety_checked: bool = Field(
        description="Whether the query passed safety validation"
    )
    extracted_company: Optional[str] = Field(
        None,
        description="Company name extracted from query context"
    )


class QuerySummary(BaseModel):
    """Structured output for query result summarization"""
    summary: str = Field(
        description="Natural language summary of the query results"
    )
  

class GreetingResponse(BaseModel):
    """Structured output for greeting responses"""
    greeting: str = Field(
        description="The friendly greeting message"
    )
    tone: Literal["formal", "casual", "warm"] = Field(
        description="Tone of the greeting"
    )
    includes_offer_to_help: bool = Field(
        description="Whether the greeting includes an offer to help"
    )
    
    
class NEEDSInfoResponse(BaseModel):
    """Structured output for needs info responses"""
    needs_info: str = Field(
        description="The message asking user for more specific information"
    )
    suggestions: List[str] = Field(
        default_factory=list,
        description="List of example queries the user could try"
    )
    missing_info: List[str] = Field(
        default_factory=list,
        description="List of specific information pieces needed"
    )
    sample_query: str = Field(
        description="An example of a well-formed query"
    )
    user_lang: Literal["English", "العربية"] = Field(
        description="Language to respond in"
    )


class LLMManager:
    """Manages OpenAI API calls with error handling, rate limiting, and context memory"""
    
    def __init__(self):
        """Initialize OpenAI client and company memory"""
        self.client = self._get_client()
        self.voice_map = {
            "العربية": "onyx",
            "English": "alloy",
            "اردو": "nova"  # Nova voice for Urdu
        }
        if "chat_memory" not in st.session_state:
            st.session_state.chat_memory = []
    
    @st.cache_resource
    def _get_client(_self):
        """Get cached OpenAI client"""
        api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("key")
        if not api_key:
            logger.error("OpenAI API key not found")
            st.warning("⚠️ OpenAI API key missing in Streamlit secrets")
            st.stop()
        return OpenAI(api_key=api_key)
    
    def build_chat_context(self, limit: Optional[int] = 20) -> List[Dict[str, str]]:
        """Build chat context from recent messages"""
        if "chat_memory" not in st.session_state:
            return []
    
        recent = st.session_state.chat_memory if limit is None else st.session_state.chat_memory[-limit:]
    
        context = []
        for msg in recent:
            if "dataframe" in msg or "result_data" in msg:
                continue
            context.append({"role": msg["role"], "content": msg["content"]})
    
        return context
        
    def update_last_company(self, company_name: Optional[str]):
        """Update the last mentioned company in session state"""
        if company_name:
            st.session_state["last_company_name"] = company_name
            logger.info(f"💾 Company memory updated: {company_name}")
    
    def _is_followup_question(self, text: str) -> bool:
        """Detect if a question is a follow-up"""
        text_lower = text.lower().strip()
        
        if len(text_lower.split()) <= 6:
            followup_keywords_ar = [
                "موقع", "عنوان", "موجود", "معتمد", "مصرح", "رقم", "ايميل", 
                "تفاصيل", "تقييم", "خريطة","تفاصيل", "تقييم", "تقييمات", "مراجعات", "نجوم", "النجوم", "جيد",
                "وين", "كيف", "متى", "هل هي", "هل هو", "فين", "ايش", "شنو", "موجودة",
                "في الرياض", "في مكة", "في جدة", "في المدينة"
            ]
            followup_keywords_en = [
                "location", "address", "where", "authorized", "phone", "email", 
                "details", "rating","reviews", "stars", "good", "map", "is it", "contact", "info", "number",
                "in riyadh", "in makkah", "in jeddah", "in medina", "there", "located"
            ]

            # Urdu follow-up keywords
            followup_keywords_ur = [
                "کہاں", "پتہ", "مقام", "نمبر", "ای میل", "تفصیل", "رابطہ",
                "منظور شدہ", "مجاز", "کیا ہے", "ریٹنگ", "اسٹار", "جائزے", "اچھی","ریاض میں", "مکہ میں", "جدہ میں"
            ]
            
            all_keywords = followup_keywords_ar + followup_keywords_en + followup_keywords_ur
            return any(kw in text_lower for kw in all_keywords)
        
        return False

    def detect_intent(self, user_input: str, language: str) -> Dict:
        """Detect user intent using LLM with structured output and company extraction"""
        
        last_company = st.session_state.get("last_company_name", "")
        original_input = user_input
        
        # Auto-enrich vague follow-up questions with last company context
        if last_company and self._is_followup_question(user_input):
            if language == "العربية":
                user_input = f"هل شركة {last_company} {original_input.strip()}"
            elif language == "اردو":
                user_input = f"کیا {last_company} {original_input.strip()}"
            else:
                user_input = f"Is {last_company} {original_input.strip()}"
            logger.info(f"🔗 Context auto-enriched: '{original_input}' → '{user_input}'")

        intent_prompt = f"""
You are a fraud-prevention assistant for Hajj pilgrims. 
Use the full conversation context and any previously mentioned company.

🧠 CONTEXT MEMORY:
Last company mentioned in conversation: {last_company if last_company else 'None'}

🎯 CRITICAL FOLLOW-UP DETECTION:
If user asks a follow-up question like:
- Arabic: "وين موقعها؟" / "هل هي معتمدة؟" / "أعطني التفاصيل" / "رقم التواصل؟" / "هل موجودة في الرياض؟" / "كم عدد التقييمات؟" / "ما هو التقييم؟" / "كم تقييم هذه الشركة؟" / "كم النجوم؟" / "هل تقييمها جيد؟"
- English: "Where is it located?" / "Is it authorized?" / "Give me details" / "Contact number?" / "Is it in Riyadh?" / "How many reviews?" / "What's the rating?" / "How many stars?" / "Is its rating good?"
- Urdu: "یہ کہاں ہے؟" / "کیا یہ منظور شدہ ہے؟" / "تفصیل دیں" / "رابطہ نمبر؟" / "کیا ریاض میں ہے؟" / "کتنے جائزے ہیں؟" / "ریٹنگ کیا ہے؟" / "کتنے اسٹار ملے؟" / "کیا ریٹنگ اچھی ہے؟"

AND there's a last_company in memory, then:
1. Classify as DATABASE
2. Extract that last_company as the company name
3. Set high confidence (0.95+)
4. Reasoning should mention "follow-up question about [company name] - checking if it exists in [location/context]"

📋 Classify this message into ONE of four categories:

1️⃣ GREETING: 
- Greetings like hello, hi, how are you, salam, السلام عليكم, مرحبا, السلام علیکم, آداب
- No specific agency information is provided
- User asks about your capabilities or services
- User just wants to chat or start conversation

2️⃣ DATABASE: 
- Questions about verifying specific Hajj agencies
- Checking authorization, company details, locations, contacts
- User mentions agency names, locations, or asks for authorized agencies
- Count of agencies, list of countries/cities with agencies
- Is X authorized, details about Y agency
- Asking for an agency's address, email, phone, location, contact info
- Checking if an agency is authorized or not
- Asking about Hajj offices in a specific city or country
- Mentioning or asking about a company name

3️⃣ GENERAL_HAJJ: 
- General Hajj-related questions (rituals, requirements, documents, safety, procedures)
- Not about specific agencies

4️⃣ NEEDS_INFO: 
- Message is too vague or lacks details needed to provide accurate information
- Examples: "I want to verify an agency" (which agency?)
- "Tell me about Hajj companies" (what specifically?)
- "Is this authorized?" (which company? - unless last_company exists)
- "Check this company" (need company name - unless last_company exists)

🔍 COMPANY EXTRACTION:
Extract any company name mentioned in the user's message and return it in 'extracted_company'.

Examples of company mentions:
- "شركة جبل عمر" → extracted_company: "جبل عمر"
- "Royal City Agency" → extracted_company: "Royal City"
- "وكالة الهدى" → extracted_company: "الهدى"
- "Al Safa Travel" → extracted_company: "Al Safa"
- "jabal omar" → extracted_company: "jabal omar"
- "جبل عمر کمپنی" → extracted_company: "جبل عمر"
- "الہدیٰ ایجنسی" → extracted_company: "الہدیٰ"

🚨 CRITICAL CONTEXT:
- 415 fake Hajj offices closed in 2025
- 269,000+ unauthorized pilgrims stopped
- Mission: prevent fraud, protect pilgrims
- For DATABASE questions, we need specific agency names or clear location criteria

Message: {user_input}

Classify the intent, extract company name if mentioned, provide confidence score, and explain your reasoning.
"""
        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You classify user intents and extract company names for a Hajj agency verification system. Pay special attention to follow-up questions that reference previously mentioned companies."},
                    {"role": "user", "content": intent_prompt},
                    *self.build_chat_context(limit=5)
                ],
                response_format=IntentClassification,
                temperature=0
            )
            
            intent_data = response.choices[0].message.parsed
            
            # Update company memory if new company detected
            if intent_data.extracted_company:
                self.update_last_company(intent_data.extracted_company)
            
            logger.info(f"Intent: {intent_data.intent} | Confidence: {intent_data.confidence} | Company: {intent_data.extracted_company or 'None'}")
            logger.info(f"Reasoning: {intent_data.reasoning}")
            
            return {
                "intent": intent_data.intent,
                "confidence": intent_data.confidence,
                "reasoning": intent_data.reasoning,
                "extracted_company": intent_data.extracted_company
            }
            
        except Exception as e:
            logger.error(f"Structured intent detection failed: {e}")
            return self._fallback_intent_detection(user_input)
    
    def _fallback_intent_detection(self, user_input: str) -> Dict:
        """Fallback intent detection using heuristics when API fails"""
        ui = user_input.lower()
        
        # Urdu greetings
        if any(g in ui for g in ["hello", "hi", "salam", "السلام", "مرحبا", "آداب", "السلام علیکم"]):
            intent = "GREETING"
        elif any(k in ui for k in ["company", "agency", "معتمد", "شركات", "authorized", "وكالة", "کمپنی", "ایجنسی", "منظور شدہ"]):
            if len(ui.split()) < 4 and not any(specific in ui for specific in ["royal", "alhuda", "مكة", "جدة", "riyadh", "مکہ"]):
                intent = "NEEDS_INFO"
            else:
                intent = "DATABASE"
        else:
            intent = "GENERAL_HAJJ"
        
        return {
            "intent": intent,
            "confidence": 0.7,
            "reasoning": "Determined by keyword matching (fallback)",
            "extracted_company": None
        }
        
    def generate_greeting(self, user_input: str, language: str) -> str:
        """Generate natural greeting response with structured output"""
        is_arabic = language == "العربية"
        is_urdu = language == "اردو"
        
        system_prompt = """You are a friendly Hajj and fraud prevention assistant designed to protect pilgrims from scams and help them verify hajj agencies authorized from Ministry of Hajj and Umrah. 
Generate a short, warm, natural greeting (max 3 sentences) that:
- Acknowledges the user's greeting
- Expresses willingness to help
- Mentions you can help verify Hajj companies
- Uses emojis appropriately
- Respond in Arabic if the user input contains Arabic text
- Respond in Urdu if the user input contains Urdu text (اردو)
- Otherwise respond in English
Explain your reasoning and what you provide briefly.

Keep the response concise, friendly, and professional."""

        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                    *self.build_chat_context()
                ],
                response_format=GreetingResponse,
                temperature=0.7
            )
            
            greeting_data = response.choices[0].message.parsed
            logger.info(f"Greeting generated with tone: {greeting_data.tone}")
            return greeting_data.greeting
            
        except Exception as e:
            logger.error(f"Structured greeting generation failed: {e}")
            if is_urdu:
                return "السلام علیکم! 👋 میں آپ کی کیسے مدد کر سکتا ہوں؟"
            elif is_arabic:
                return "السلام عليكم! 👋 كيف يمكنني مساعدتك؟"
            else:
                return "Hello! 👋 How can I help you today?"
    
    def generate_general_answer(self, user_input: str, language: str) -> str:
        """Generate answer for general Hajj questions"""
        system_prompt = """You are a helpful assistant specialized in Hajj information. 
Be concise, factual, and helpful. Focus on practical information.
Detect if the user's question is in Arabic, English, or Urdu, and respond in the same language.
You are designed to protect pilgrims from scams and help them verify hajj agencies authorized from Ministry of Hajj and Umrah
Avoid religious rulings or fatwa - stick to practical guidance."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                    *self.build_chat_context()
                ],
                temperature=0.6,
                max_tokens=400
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"General answer generation failed: {e}")
            return "I encountered an error. Please try rephrasing your question."
    
    def generate_sql(self, user_input: str, language: str) -> Optional[Dict]:
        """Generate SQL query from user input with structured output and context awareness"""
        
        last_company = st.session_state.get("last_company_name", "")
        
        # Detect specific field requests
        field_mapping = {
            "rating": "rating_reviews",
            "تقييم": "rating_reviews", 
            "درجہ بندی": "rating_reviews",
            "تقييمات": "rating_reviews",
            "مراجعات": "rating_reviews",
            "النجوم": "rating_reviews",
            "نجوم": "rating_reviews",
            "جيد": "rating_reviews",  # "هل تقييمها جيد؟"
            "stars": "rating_reviews",
            "good": "rating_reviews",
            "ریٹنگ": "rating_reviews",
            "اسٹار": "rating_reviews",
            "اچھی": "rating_reviews",  # "کیا ریٹنگ اچھی ہے؟"
            "contact": "contact_Info",
            "رقم": "contact_Info",
            "نمبر": "contact_Info",
            "email": "email",
            "ايميل": "email",
            "ای میل": "email",
            "address": "formatted_address",
            "عنوان": "formatted_address",
            "پتہ": "formatted_address",
            "location": 'city, country, "المدينة", "الدولة", formatted_address' if language == "العربية" else "city, country, formatted_address",
            "موقع": '"المدينة", "الدولة", formatted_address', 
            "مقام": '"المدينة", "الدولة", formatted_address',
            "المدينة": '"المدينة"',  
            "الدولة": '"الدولة"',  
            }
        
        requested_fields = []
        user_lower = user_input.lower()
        for keyword, field in field_mapping.items():
            if keyword in user_lower:
                requested_fields.append(field)
        
        # Build SELECT clause
        if requested_fields:
            select_clause = f"SELECT {', '.join(set(requested_fields))}, hajj_company_ar, hajj_company_en"
        else:
            select_clause = "SELECT *"
        
        if last_company and self._is_followup_question(user_input):
            context_note = f"\n\n⚠️ IMPORTANT CONTEXT: User is asking a follow-up question about '{last_company}' (mentioned previously in conversation). Generate SQL query specifically for this company using this SELECT clause: {select_clause}"
        else:
            context_note = f"\n\n💡 Use this SELECT clause: {select_clause}"
        
        sql_prompt = self._get_sql_system_prompt(language) + f"\n\nUser Question: {user_input}{context_note}"
        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a SQL expert that generates safe queries for a Hajj agency database. Pay special attention to context notes about previously mentioned companies. Support Arabic, English, and Urdu queries."},
                    {"role": "user", "content": sql_prompt},
                    *self.build_chat_context()
                ],
                response_format=SQLQueryGeneration,
                temperature=0
            )
            
            sql_data = response.choices[0].message.parsed
            
            if sql_data.extracted_company:
                self.update_last_company(sql_data.extracted_company)
            
            logger.info(f"SQL generated - Type: {sql_data.query_type}, Safety: {sql_data.safety_checked}")
            logger.info(f"Explanation: {sql_data.explanation}")
            print(sql_data.sql_query)
            
            if sql_data.sql_query and sql_data.safety_checked:
                return {
                    "sql_query": sql_data.sql_query,
                    "query_type": sql_data.query_type,
                    "filters": sql_data.filters_applied,
                    "explanation": sql_data.explanation
                }
            else:
                logger.warning(f"No safe SQL generated: {sql_data.explanation}")
                return None
            
        except Exception as e:
            logger.error(f"Structured SQL generation failed: {e}")
            return None
        
    def generate_summary(self, user_input: str, language: str, row_count: int, sample_rows: List[Dict]) -> Dict:
        """
        🔧 FIXED VERSION v2 - Improved company name matching + LLM-powered responses
        
        KEY CHANGES:
        1. Uses extracted_company from session state instead of raw user input
        2. Better fuzzy matching with normalized company names
        3. Handles partial matches more intelligently
        4. Fallback to showing all results if exact match fails
        5. Always uses LLM with focused prompts for all question types
        """
        
        # Auto-detect language from user input
        detected_language = self._detect_language_from_text(user_input)
        if detected_language:
            language = detected_language
            logger.info(f"🌐 Language auto-detected from input: {language}")
        
        last_company = st.session_state.get("last_company_name", "")
        
        # Detect if user asking for specific field only
        specific_field_request = None
        user_lower = user_input.lower()
        if any(kw in user_lower for kw in [
            # English
            "rating", "stars", "reviews", "how many reviews", "what is the rating", "is its rating good",
            # Arabic
            "تقييم", "تقييمات", "مراجعات", "النجوم", "نجوم", "كم عدد التقييمات", "ما هو التقييم", "كم تقييم", "هل تقييمها جيد",
            # Urdu
            "ریٹنگ", "اسٹار", "جائزے", "کتنے جائزے", "ریٹنگ کیا ہے", "کیا ریٹنگ اچھی ہے", "کتنے اسٹار", "درجہ بندی"
        ]):
            specific_field_request = "rating"
        elif any(kw in user_lower for kw in ["contact", "رقم", "نمبر", "phone"]):
            specific_field_request = "contact"
        elif any(kw in user_lower for kw in ["email", "ايميل", "ای میل"]):
            specific_field_request = "email"
        elif any(kw in user_lower for kw in ["address", "عنوان", "پتہ"]):
            specific_field_request = "address"
        
        # Handle zero rows
        if row_count == 0:
            location_keywords_ar = ["في", "الرياض", "جدة", "مكة", "المدينة"]
            location_keywords_en = ["in", "riyadh", "jeddah", "makkah", "medina"]
            location_keywords_ur = ["میں", "ریاض", "جدہ", "مکہ", "مدینہ"]
            is_location_query = any(kw in user_input.lower() for kw in location_keywords_ar + location_keywords_en + location_keywords_ur)

            if last_company and is_location_query:
                if language == "العربية":
                    return {"summary": f"لم أجد شركة {last_company} في الموقع المحدد. ✨\n\nهل تريد معرفة الموقع الفعلي لشركة {last_company}؟ أو البحث عن شركات أخرى معتمدة؟"}
                elif language == "اردو":
                    return {"summary": f"مجھے {last_company} مخصوص جگہ پر نہیں ملی۔ ✨\n\nکیا آپ {last_company} کی اصل جگہ جاننا چاہتے ہیں؟ یا دوسری منظور شدہ ایجنسیاں تلاش کرنا چاہتے ہیں؟"}
                else:
                    return {"summary": f"I couldn't find {last_company} in the specified location. ✨\n\nWould you like to know the actual location of {last_company}? Or search for other authorized agencies in that area?"}
            else:
                if language == "اردو":
                    return {"summary": "کوئی نتیجہ نہیں ملا۔ براہ کرم اپنا سوال دوبارہ لکھیں۔"}
                elif language == "العربية":
                    return {"summary": "لم يتم العثور على نتائج. حاول إعادة صياغة السؤال."}
                else:
                    return {"summary": "No results found. Try rephrasing your question or broadening the search."}
        
        # Prepare requested columns
        all_columns = [
            "hajj_company_en",
            "hajj_company_ar",
            "formatted_address",
            "city",
            "country",
            "email",
            "contact_Info",
            "rating_reviews",
            "is_authorized",
            "google_maps_link",
            '"المدينة"',  
            '"الدولة"'
        ]

        requested_columns = []
        user_input_lower = user_input.lower()

        if any(k in user_input_lower for k in ["contact details", "تفاصیل رابطہ", "تفاصيل الاتصال"]):
            requested_columns.extend(["email", "contact_info", "google_maps_link"])  # 🔧 تغيير contact_Info

        if any(k in user_input_lower for k in ["address", "پتہ", "العنوان"]):
            requested_columns.append("formatted_address")

        if any(k in user_input_lower for k in ["contact", "رابطہ نمبر", "رقم التواصل", "تواصل"]):
            requested_columns.append("contact_info")  # 🔧 تغيير contact_Info

        if any(k in user_input_lower for k in ["email", "ای میل", "البريد الإلكتروني"]):
            requested_columns.append("email")

        # 🆕 إضافة: دعم الأعمدة العربية
        if any(k in user_input_lower for k in ["city", "شہر", "المدينة", "مدينة"]):
            if language == "العربية":
                requested_columns.append('"المدينة"')  # 🆕 استخدام العمود العربي
            else:
                requested_columns.append("city")

        if any(k in user_input_lower for k in ["country", "ملک", "الدولة", "دولة", "بلد"]):
            if language == "العربية":
                requested_columns.append('"الدولة"')  # 🆕 استخدام العمود العربي
            else:
                requested_columns.append("country")

        if any(k in user_input_lower for k in ["status", "حالت", "الحالة", "authorization", "منظور شدہ", "معتمد"]):
            requested_columns.append("is_authorized")

        if any(k in user_input_lower for k in ["map", "نقشہ", "رابط قوقل ماب", "google maps links", "خريطة"]):
            requested_columns.append("google_maps_link")

        if not requested_columns:
            requested_columns = all_columns

        # Use extracted company name for better matching
        search_name = last_company.lower().strip() if last_company else user_input.lower().strip()
        
        # Remove common prefixes/suffixes for better matching
        search_name = re.sub(r'\b(company|agency|شركة|وكالة|مؤسسة|کمپنی|ایجنسی)\b', '', search_name, flags=re.IGNORECASE).strip()
        
        logger.info(f"🔍 Searching for company: '{search_name}'")
        
        threshold = 60  # Lower threshold for more flexible matching
        matching_rows = []

        for row in sample_rows:
            name_en = row.get("hajj_company_en", "").lower()
            name_ar = row.get("hajj_company_ar", "").lower()
            
            # Clean names for better matching
            name_en_clean = re.sub(r'\b(company|agency|establishment)\b', '', name_en, flags=re.IGNORECASE).strip()
            name_ar_clean = re.sub(r'\b(شركة|وكالة|مؤسسة|کمپنی|ایجنسی)\b', '', name_ar).strip()
            
            score_en = max(
                fuzz.token_set_ratio(search_name, name_en),
                fuzz.token_set_ratio(search_name, name_en_clean),
                fuzz.partial_ratio(search_name, name_en)
            )
            score_ar = max(
                fuzz.token_set_ratio(search_name, name_ar),
                fuzz.token_set_ratio(search_name, name_ar_clean),
                fuzz.partial_ratio(search_name, name_ar)
            )
            
            best_score = max(score_en, score_ar)
            
            if best_score >= threshold:
                matching_rows.append((row, best_score))
                logger.info(f"✓ Match found: {row.get('hajj_company_en', 'N/A')} (score: {best_score})")

        # Sort by score (best matches first)
        matching_rows.sort(key=lambda x: x[1], reverse=True)
        matching_rows = [row for row, score in matching_rows]

        # Handle no matches - show all results with a note
        if len(matching_rows) == 0:
            logger.warning(f"❌ No fuzzy matches found for '{search_name}', showing all {row_count} results")
            matching_rows = sample_rows[:10]  # Show top 10 results
            no_exact_match_note = f"\n\n💡 Note: No exact match found for '{last_company or search_name}'. Showing top results instead:"

        # Handle multiple matches
        elif len(matching_rows) > 1:
            if language == "اردو":
                prompt_user = f"مجھے {len(matching_rows)} کمپنیاں ملیں جو آپ کی تلاش سے مماثل ہیں۔ ✨ براہ کرم درج ذیل آپشنز میں سے صحیح کمپنی کا نام بتائیں:\n"
                prompt_user += "\n".join([f"- {row['hajj_company_en']} ({row['hajj_company_ar']})" for row in matching_rows[:5]])
            elif language == "العربية":
                prompt_user = f"لقد وجدت {len(matching_rows)} شركات قد تطابق ما كتبته. ✨ يرجى تحديد اسم الشركة بالضبط من بين الخيارات التالية:\n"
                prompt_user += "\n".join([f"- {row['hajj_company_en']} ({row['hajj_company_ar']})" for row in matching_rows[:5]])
            else:
                prompt_user = f"I found {len(matching_rows)} companies matching your input. ✨ Please specify the exact company name from the following options:\n"
                prompt_user += "\n".join([f"- {row['hajj_company_en']} ({row['hajj_company_ar']})" for row in matching_rows[:5]])
            return {"summary": prompt_user}

        # Prepare FULL data for context (not just requested columns)
        data_preview = matching_rows[:50]  # Send all columns
        data_preview_json = json.dumps(data_preview, ensure_ascii=False)

        # Build focused instruction for LLM based on specific field request
        if specific_field_request:
            if specific_field_request == "rating":
                focus_instruction = f"""
            🎯 CRITICAL: User is asking ONLY about RATING/REVIEWS/STARS
            - Show ONLY: rating_reviews field
            - Handle different question types:

            1. "كم عدد التقييمات؟" / "How many reviews?" / "کتنے جائزے؟"
            → Extract count only: "3 تقييمات" / "3 reviews" / "3 جائزے"

            2. "ما هو التقييم؟" / "What is the rating?" / "ریٹنگ کیا ہے؟"
            → Show full rating: "3.7 من 5" / "3.7 out of 5" / "3.7 میں سے 5"

            3. "كم النجوم؟" / "How many stars?" / "کتنے اسٹار؟"
            → Show stars: "3.7 نجوم" / "3.7 stars" / "3.7 اسٹار"

            4. "هل تقييمها جيد؟" / "Is its rating good?" / "کیا ریٹنگ اچھی ہے؟"
            → Evaluate and answer: "نعم، التقييم جيد (3.7 من 5)" / "Yes, good rating (3.7/5)" / "ہاں، اچھی ریٹنگ ہے (3.7/5)"

            5. "كم تقييم هذه الشركة؟" → Show full: "3.7 (بناءً على 3 تقييمات)"

            Examples:
            - Arabic: "تقييم الشركة: 3.7 ⭐ (بناءً على 3 تقييمات)"
            - English: "Company rating: 3.7 ⭐ (based on 3 reviews)"
            - Urdu: "کمپنی کی ریٹنگ: 3.7 ⭐ (3 جائزوں کی بنیاد پر)"

            DO NOT show: address, email, contact, city, country unless asked
            """
            elif specific_field_request == "contact":
                focus_instruction = f"\n\n🎯 CRITICAL: User is asking ONLY about CONTACT NUMBER\n- Show ONLY: contact_Info field\n- Format: Direct phone number answer\n- Example Arabic: 'رقم التواصل: +966...'\n- DO NOT show other fields"
            elif specific_field_request == "email":
                focus_instruction = f"\n\n🎯 CRITICAL: User is asking ONLY about EMAIL\n- Show ONLY: email field\n- Format: Direct email answer\n- DO NOT show other fields"
            elif specific_field_request == "address":
                if language == "العربية":
                    focus_instruction = f'\n\n🎯 CRITICAL: User is asking ONLY about ADDRESS/LOCATION\n- Show ONLY: formatted_address, "المدينة", "الدولة", google_maps_link\n- Format: Address with map link\n- Use Arabic columns for city and country\n- DO NOT show: email, contact, rating'
                else:
                    focus_instruction = f"\n\n🎯 CRITICAL: User is asking ONLY about ADDRESS/LOCATION\n- Show ONLY: formatted_address, city, country, google_maps_link\n- Format: Address with map link\n- DO NOT show: email, contact, rating"
            else:
                focus_instruction = "\n\n🎯 Show all relevant information"
        
        # But tell LLM to focus only on requested columns
        if requested_columns and len(requested_columns) <= 3:  # Specific question
            if not specific_field_request:  # If we didn't already set focus_instruction
                focus_instruction = f"\n\n🎯 USER ASKED SPECIFICALLY ABOUT: {', '.join(requested_columns)}\n- Display ONLY these fields in your response\n- Do NOT show other fields (city, country, email, etc.) unless they are in the requested list\n- Keep the response focused and concise"
        else:  # General question
            if not specific_field_request:  # If we didn't already set focus_instruction
                focus_instruction = "\n\n🎯 This is a general query - show all relevant information"

        summary_prompt = f"""
    You are a multilingual fraud-prevention and travel assistant for Hajj agencies.

    🚨 CRITICAL LANGUAGE RULE:
    - User question language: {language}
    - You MUST respond in {language} ONLY
    - If language is "العربية", respond COMPLETELY in Arabic
    - If language is "اردو", respond COMPLETELY in Urdu
    - If language is "English", respond COMPLETELY in English
    - Do NOT mix languages in your response

    Your task:
    → Summarize SQL query results clearly and naturally, with a warm, conversational tone that feels friendly and professional.

    User question: {user_input}
    Data: {data_preview_json}
    {focus_instruction}

    Instructions:
    - ALWAYS respond in {language}
    - Always acknowledge the user's question in {language}
    - Arabic examples: "بناءً على البيانات، وجدت لك النتائج التالية:" أو "إليك ما وجدته:"
    - Urdu examples: "ڈیٹا کی بنیاد پر، میں نے آپ کے لیے یہ نتائج پائے:" یا "یہ ہے جو مجھے ملا:"
    - English examples: "Here are the results I found for you:" or "Based on the data, here's what I found:"
    - Be concise and clear - especially for single-field questions, keep it SHORT (1-2 lines)
    - Highlight number of matching records ONLY if multiple companies found
    - Provide actionable advice if relevant
    - Use emojis sparingly to enhance friendliness
    - For single-field questions (rating, contact, email): Answer in 1-2 sentences maximum
    - For general questions: Use a mix of sentences and bullet points

    Important behavior for company search:
    - If the user mentions a company/agency name:
        * Display all companies whose names match or partially match the search term.
        * If there are multiple matches, include a short friendly note explaining that there are multiple companies and all relevant options are shown.
        * Always include the Google Maps link if available.
        * Limit listing to up to 10 companies.

    Columns to include in summary: {requested_columns}

    🚨 CRITICAL LANGUAGE-SPECIFIC RULES:
    - If {language} is "العربية":
    * Translate ALL field names to Arabic
    * Use "المدينة" column for city data (NOT city column)  # 🆕
    * Use "الدولة" column for country data (NOT country column)  # 🆕
    * city → المدينة (from "المدينة" column)
    * country → الدولة (from "الدولة" column)
    * email → البريد الإلكتروني
    * contact_Info → رقم التواصل
    * rating_reviews → التقييم
    * is_authorized → مصرح / معتمد (translate "Yes" to "نعم، معتمد" and "No" to "لا، غير معتمد")
    * formatted_address → العنوان
    * google_maps_link → رابط خرائط جوجل

    - If {language} is "اردو":
    * Translate ALL field names to Urdu
    * city → شہر
    * country → ملک
    * email → ای میل
    * contact_Info → رابطہ نمبر
    * rating_reviews → درجہ بندی
    * is_authorized → منظور شدہ / مجاز (translate "Yes" to "جی ہاں، منظور شدہ" and "No" to "نہیں، غیر منظور شدہ")
    * formatted_address → پتہ
    * google_maps_link → گوگل میپس لنک

    - If {language} is "English":
    * Keep all field names in English
    * is_authorized → translate to "Yes, Authorized" or "No, Not Authorized"

    Behavior based on user question:
    - Always include Google Maps Link if available
    - Ensure response is complete and readable, no truncated or missing information
    - You are designed to protect pilgrims from scams and help them verify Hajj agencies authorized by the Ministry of Hajj and Umrah

    🌍 OUTPUT FORMAT:

    If {language} is "العربية", use this format:
    - الاسم (بالعربية / بالإنجليزية):
    - المدينة:
    - الدولة:
    - البريد الإلكتروني:
    - رقم التواصل:
    - التقييم:
    - الحالة: (نعم، معتمد / لا، غير معتمد)
    - رابط خرائط جوجل

    If {language} is "اردو", use this format:
    - نام (عربی / انگریزی):
    - شہر:
    - ملک:
    - ای میل:
    - رابطہ نمبر:
    - درجہ بندی:
    - حالت: (جی ہاں، منظور شدہ / نہیں، غیر منظور شدہ)
    - گوگل میپس لنک

    If {language} is "English", use this format:
    - Name (Arabic / English):
    - City:
    - Country:
    - Email:
    - Contact Info:
    - Rating:
    - Status: (Yes, Authorized / No, Not Authorized)
    - Google Maps Link

    - Keep tone friendly, professional, and natural IN {language}
    - Mix sentences and bullets; add small friendly phrases if appropriate
    - Do NOT invent any data
    - If multiple rows, list up to 10 agencies with key details
    - REMEMBER: Your ENTIRE response must be in {language}
    """

        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a helpful assistant summarizing Hajj agency data in a friendly and structured way."},
                    {"role": "user", "content": summary_prompt}
                ],
                response_format=QuerySummary,
                temperature=0.6
            )

            summary_data = response.choices[0].message.parsed
            final_summary = f"{summary_data.summary}"
            logger.info("✅ Summary generated successfully.")

            return {"summary": final_summary}

        except Exception as e:
            logger.error(f"❌ Structured summary generation failed: {e}")
            if language == "اردو":
                return {"summary": f"📊 {row_count} مماثل ریکارڈز ملے۔"}
            elif language == "العربية":
                return {"summary": f"📊 تم العثور على {row_count} سجلات متطابقة."}
            else:
                return {"summary": f"📊 Found {row_count} matching records."}

    def text_to_speech(self, text: str, language: str) -> Optional[io.BytesIO]:
        """Convert text to speech using OpenAI TTS"""
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
        """
        Detect if text is Arabic or English based on character analysis
        Returns: "العربية" or "English" or "اردو" or None
        """
        if not text:
            return None
        
        # Count Arabic and English characters
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        # Urdu-specific Unicode ranges (overlaps with Arabic but has additional characters)
        urdu_specific_chars = sum(1 for c in text if c in 'ٹڈڑںھےۓپچژکگ')
        english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        
        total_chars = arabic_chars + english_chars
        if total_chars == 0:
            return None
        
        # If Urdu-specific characters detected, consider it Urdu
        if urdu_specific_chars > 0:
            return "اردو"
        
        # If more than 30% Arabic characters, consider it Arabic
        if arabic_chars / total_chars > 0.3:
            return "العربية"
        else:
            return "English"
    
    def ask_for_more_info(self, user_input: str, language: str) -> Dict:
        """Generate structured response asking user for more specific information"""
        is_arabic = language == "العربية"
        is_urdu = language == "اردو"
        
        last_company = st.session_state.get("last_company_name", "")
        
        # If there's a company in memory but user didn't mention it, add context
        # If there's a company in memory but user didn't mention it, add context
        if last_company and "agency" not in user_input.lower() and "شركة" not in user_input and "وكالة" not in user_input and "کمپنی" not in user_input and "ایجنسی" not in user_input:
            user_input += f" (Note: User was previously asking about '{last_company}')"
            
        prompt = f"""You are a helpful Hajj verification assistant.
The user's question: "{user_input}" needs more details to provide accurate information.

Examples of vague questions:
- English: "I want to verify an agency" (which agency?) / "Tell me about Hajj companies" (what specifically?) / "Is this authorized?" (which company?) / "Check this company" (need company name)
- Arabic: "أريد التحقق من وكالة" (أي وكالة؟) / "أخبرني عن شركات الحج" (ماذا تحديداً؟) / "هل هذه معتمدة؟" (أي شركة؟) / "وين موقعها؟" without context (which company's location?)
- Urdu: "میں ایک ایجنسی کی تصدیق کرنا چاہتا ہوں" (کون سی ایجنسی؟) / "مجھے حج کمپنیوں کے بارے میں بتائیں" (خاص طور پر کیا؟) / "کیا یہ منظور شدہ ہے؟" (کون سی کمپنی؟) / "یہ کہاں ہے؟" without context (which company's location?)

Ask for specific details in a friendly way. Focus on:
1. Agency name (if verifying a company)
2. Location (city/country)
3. What specifically they want to know

Use Urdu if user input is Urdu (contains اردو script characters like ٹ، ڈ، ڑ، پ، چ)
Use Arabic if user input is Arabic (contains العربية script)
Otherwise use English
Keep it brief but friendly (2-3 sentences max).
Add a simple example of a more specific question.
"""
        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You help users provide more specific Hajj agency queries."},
                    {"role": "user", "content": prompt}
                ],
                response_format=NEEDSInfoResponse,
                temperature=0.7
            )
            
            info_data = response.choices[0].message.parsed
            return {
                "needs_info": info_data.needs_info,
                "suggestions": info_data.suggestions,
                "missing_info": info_data.missing_info,
                "sample_query": info_data.sample_query
            }
                
        except Exception as e:
            logger.error(f"More info prompt generation failed: {e}")
            # Fallback with minimal structured response
            if is_urdu:
                return {
                    "needs_info": "معاف کیجیے، کیا آپ مزید تفصیلات فراہم کر سکتے ہیں؟ 🤔 مثال کے طور پر، آپ کس کمپنی کی تصدیق کرنا چاہتے ہیں؟",
                    "suggestions": ["کیا الہدیٰ حج ایجنسی منظور شدہ ہے؟", "مجھے مکہ میں حج ایجنسیاں دکھائیں", "جبل عمر کمپنی کا پتہ کیا ہے؟"],
                    "missing_info": ["ایجنسی کا نام", "مقام", "مخصوص تفصیلات"],
                    "sample_query": "کیا الہدیٰ حج ایجنسی منظور شدہ ہے؟"
                }
            elif is_arabic:
                return {
                    "needs_info": "عذراً، هل يمكنك تقديم المزيد من التفاصيل؟ 🤔 على سبيل المثال، ما اسم الشركة التي تريد التحقق منها؟",
                    "suggestions": ["هل شركة الهدى للحج معتمدة؟", "أريد التحقق من وكالات الحج في مكة", "ما هو عنوان شركة جبل عمر؟"],
                    "missing_info": ["اسم الوكالة", "الموقع", "التفاصيل المحددة"],
                    "sample_query": "هل شركة الهدى للحج معتمدة؟"
                }
            else:
                return {
                    "needs_info": "Could you provide more details? 🤔 For example, which company would you like to verify?",
                    "suggestions": ["Is Al Huda Hajj Agency authorized?", "Show me authorized agencies in Makkah", "What is the address of Jabal Omar Agency?"],
                    "missing_info": ["agency name", "location", "specific details"],
                    "sample_query": "Is Al Huda Hajj Agency authorized?"
                }
    
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
- "المدينة" (city in Arabic - use this for Arabic queries)  
- "الدولة" (country in Arabic - use this for Arabic queries)  

--------------------------------------------
🎯 LANGUAGE-SPECIFIC COLUMN USAGE:
- For Arabic queries: Use "المدينة" and "الدولة" columns
- For English/Urdu queries: Use city and country columns
- Example Arabic: SELECT "المدينة", "الدولة" FROM agencies WHERE...
- Example English: SELECT city, country FROM agencies WHERE...

--------------------------------------------
🔍 LANGUAGE DETECTION RULES:
1. Detect if the user's question is in Arabic, English, or Urdu. And respond in the same language.
2. Respond with SQL query **only**, no text.
3. Keep text fragments (LIKE clauses) in Arabic, English, and Urdu for robustness
4. Translate city and country if needed based on user language.

--------------------------------------------
🚨 CRITICAL DATABASE CONTEXT:
- 415 fake offices closed in 2025
- 269,000+ unauthorized pilgrims stopped
- Database mixes Arabic, English, and typos.
- Always focus on verifying **authorization** and **agency location**, not world geography.

--------------------------------------------
📘 QUERY INTERPRETATION RULES:

1. "Authorized" / "معتمد" / "منظور شدہ" → add `AND is_authorized = 'Yes'`
2. "Is X authorized?" / "هل X معتمد؟" / "کیا X منظور شدہ ہے؟" → check `is_authorized` for company name
   - If the user explicitly mentions a company or agency using any of these words:
       ["شركة", "وكالة", "مؤسسة", "agency", "company", "travel", "tour", "establishment", "کمپنی", "ایجنسی"]
       then treat it as an exact company name request.
       Use **flexible LIKE matching** with LOWER(TRIM()):
       WHERE (LOWER(TRIM(hajj_company_ar)) LIKE LOWER('%الاسم%') 
              OR LOWER(TRIM(hajj_company_en)) LIKE LOWER('%name%'))
   - Otherwise (for general keywords like "الحرمين" or "الهدى" or "الہدیٰ" without context),
       use LIKE for partial matches.
3. "Number of ..." or "How many ..." or "كم عدد" or "کتنے" → use `SELECT COUNT(*)`
4. "Countries" or "number of countries" or "الدول" or "ممالک" → use:
    - `SELECT COUNT(DISTINCT country)` if asking how many
    - `SELECT DISTINCT country` if asking for list
    - Always based on agencies table
5. "Cities" or "number of cities" or "المدن" or "شہر" → same logic as above but for `city`
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
Handle Arabic, English, Urdu, and typos.

Mecca → (city LIKE '%مكة%' OR city LIKE '%مکہ%' OR LOWER(city) LIKE '%mecca%' OR LOWER(city) LIKE '%makkah%' OR LOWER(city) LIKE '%makka%')
Medina → (city LIKE '%المدينة%' OR city LIKE '%مدینہ%' OR LOWER(city) LIKE '%medina%' OR LOWER(city) LIKE '%madinah%')
Riyadh → (city LIKE '%الرياض%' OR city LIKE '%ریاض%' OR LOWER(city) LIKE '%riyadh%' OR LOWER(city) LIKE '%ar riyadh%')
Saudi Arabia → (country LIKE '%السعودية%' OR country LIKE '%سعودی عرب%' OR LOWER(country) LIKE '%saudi%' OR country LIKE '%المملكة%')
Pakistan → (country LIKE '%باكستان%' OR country LIKE '%پاکستان%' OR LOWER(country) LIKE '%pakistan%')
Egypt → (country LIKE '%مصر%' OR LOWER(country) LIKE '%egypt%')
India → (country LIKE '%الهند%' OR country LIKE '%انڈیا%' OR country LIKE '%بھارت%' OR LOWER(country) LIKE '%india%')
Indonesia → (country LIKE '%إندونيسيا%' OR country LIKE '%انڈونیشیا%' OR LOWER(country) LIKE '%indonesia%')

--------------------------------------------
🏁 OUTPUT RULES:
- Output **only** one valid SQL SELECT query.
- If no logical SQL can be formed → output `NO_SQL`
- Always include LIMIT 100 unless COUNT or DISTINCT is used.

--------------------------------------------
⚙️ COMPANY NAME MATCHING (CRITICAL):
**This is the MOST IMPORTANT rule for accurate results**

- Split company name into individual KEY words (ignore common words like شركة, مؤسسة, وكالة, company, agency)
- Use separate LIKE condition for EACH key word with AND operator
- This handles extra words, different word order, spaces, and variations
- Always use LOWER() for case-insensitive matching
- Use LIMIT 100 (not LIMIT 1) to catch all variations

❌ WRONG Pattern (too strict):
WHERE LOWER(hajj_company_ar) LIKE '%شركة%اثراء%الجود%لخدمات%الحجاج%'
(This fails if words not consecutive or have extra text between them)

✅ CORRECT Pattern (flexible):
WHERE (LOWER(hajj_company_ar) LIKE '%اثراء%' 
       AND LOWER(hajj_company_ar) LIKE '%الجود%' 
       AND LOWER(hajj_company_ar) LIKE '%لخدمات%' 
       AND LOWER(hajj_company_ar) LIKE '%الحجاج%')
   OR (LOWER(hajj_company_en) LIKE '%athraa%' 
       AND LOWER(hajj_company_en) LIKE '%jood%')

Real Examples:
1. User asks: "اثراء الجود لخدمات الحجاج"
   Should match ALL of these:
   - "شركة اثراء الجود لخدمات الحجاج شركة شخص واحد" ✅
   - "اثراء الجود - خدمات الحجاج والعمرة" ✅
   - "مؤسسة اثراء الجود للحج" ✅
   
   Query: 
   WHERE (LOWER(hajj_company_ar) LIKE '%اثراء%' 
          AND LOWER(hajj_company_ar) LIKE '%الجود%')

2. User asks: "jabal omar"
   Should match:
   - "Jabal Omar Development Company" ✅
   - "JABAL OMAR - REAL ESTATE" ✅
   
   Query:
   WHERE (LOWER(hajj_company_en) LIKE '%jabal%' 
          AND LOWER(hajj_company_en) LIKE '%omar%')

3. User asks: "الهدى للحج"
   Query:
   WHERE (LOWER(hajj_company_ar) LIKE '%الهدى%' 
          AND LOWER(hajj_company_ar) LIKE '%الحج%')

--------------------------------------------
✅ EXAMPLES:

Q: "هل شركة جبل عمر معتمدة؟"
→ SELECT DISTINCT hajj_company_en, hajj_company_ar, formatted_address, city, country, email, contact_info, rating_reviews, is_authorized, google_maps_link
FROM agencies
WHERE (LOWER(hajj_company_ar) LIKE '%جبل%' AND LOWER(hajj_company_ar) LIKE '%عمر%'
       OR LOWER(hajj_company_en) LIKE '%jabal%' AND LOWER(hajj_company_en) LIKE '%omar%')
LIMIT 100;

Q: "کیا جبل عمر منظور شدہ ہے؟"
→ SELECT DISTINCT hajj_company_en, hajj_company_ar, formatted_address, city, country, email, contact_Info, rating_reviews, is_authorized, google_maps_link
FROM agencies
WHERE (LOWER(TRIM(hajj_company_ar)) LIKE '%جبل%عمر%' 
       OR LOWER(TRIM(hajj_company_en)) LIKE '%jabal%omar%')
LIMIT 1;

Q: "is jabal omar authorized?"
→ SELECT DISTINCT hajj_company_en, hajj_company_ar, formatted_address, city, country, email, contact_Info, rating_reviews, is_authorized, google_maps_link
FROM agencies
WHERE (LOWER(TRIM(hajj_company_ar)) LIKE '%جبل%عمر%' 
       OR LOWER(TRIM(hajj_company_en)) LIKE '%jabal%omar%')
LIMIT 1;

Q: "یہ کہاں ہے؟" (with context: about "جبل عمر")
→ SELECT formatted_address, city, country, google_maps_link 
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

Q: "کیا یہ ریاض میں ہے؟" (with context: about "جبل عمر")
→ SELECT hajj_company_en, hajj_company_ar, city, country, formatted_address
FROM agencies
WHERE (LOWER(TRIM(hajj_company_ar)) LIKE '%جبل%عمر%'
       OR LOWER(TRIM(hajj_company_en)) LIKE '%jabal%omar%')
  AND (city LIKE '%الرياض%' OR city LIKE '%ریاض%' OR LOWER(city) LIKE '%riyadh%')
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

Q: "مکہ میں منظور شدہ ایجنسیاں"
→ SELECT * FROM agencies 
WHERE is_authorized = 'Yes' 
  AND (city LIKE '%مكة%' OR city LIKE '%مکہ%' OR LOWER(city) LIKE '%mecca%' OR LOWER(city) LIKE '%makkah%') 
LIMIT 100;

Q: "كم عدد الشركات في المدينة؟"
→ SELECT COUNT(*) FROM agencies 
WHERE ("المدينة" LIKE '%المدينة%' OR "المدينة" LIKE '%مدینہ%' OR LOWER(city) LIKE '%medina%' OR LOWER(city) LIKE '%madinah%');

Q: "وكالات معتمدة في الرياض"
→ SELECT hajj_company_ar, hajj_company_en, "المدينة", "الدولة", formatted_address, is_authorized 
FROM agencies 
WHERE is_authorized = TRUE 
  AND ("المدينة" LIKE '%الرياض%' OR "المدينة" LIKE '%ریاض%' OR LOWER(city) LIKE '%riyadh%') 
LIMIT 100;

Q: "شركات في السعودية"
→ SELECT hajj_company_ar, hajj_company_en, "المدينة", "الدولة" 
FROM agencies 
WHERE ("الدولة" LIKE '%السعودية%' OR "الدولة" LIKE '%سعودی%' OR LOWER(country) LIKE '%saudi%') 
LIMIT 100;

Q: "مدینہ میں کتنی کمپنیاں ہیں؟"
→ SELECT COUNT(*) FROM agencies 
WHERE (city LIKE '%المدينة%' OR city LIKE '%مدینہ%' OR LOWER(city) LIKE '%medina%' OR LOWER(city) LIKE '%madinah%');

Q: "How many countries have agencies?"
→ SELECT COUNT(DISTINCT country) FROM agencies;

Q: "کتنے ممالک میں ایجنسیاں ہیں؟"
→ SELECT COUNT(DISTINCT country) FROM agencies;

Q: "رابطہ نمبر؟" (with context: about "الهدى")
→ SELECT contact_Info, hajj_company_ar, hajj_company_en 
FROM agencies 
WHERE (LOWER(TRIM(hajj_company_ar)) LIKE '%الهدى%'
       OR LOWER(TRIM(hajj_company_en)) LIKE '%huda%')
LIMIT 1;

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
        """Extract SQL query from LLM response"""
        if not response_text:
            return None
        
        # Try code blocks
        code_block_pattern = r'```(?:sql)?\s*(SELECT[\s\S]*?)```'
        match = re.search(code_block_pattern, response_text, re.IGNORECASE)
        if match:
            return match.group(1).strip().rstrip(';')
        
        # Try plain SELECT
        select_pattern = r'(SELECT\s+.*?(?:;|$))'
        match = re.search(select_pattern, response_text, re.IGNORECASE | re.DOTALL)
        if match:
            return match.group(1).strip().rstrip(';')
        
        if "NO_SQL" in response_text:
            return "NO_SQL"
        
        return None
