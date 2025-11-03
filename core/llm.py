"""
LLM Manager Module
Handles OpenAI API interactions for chat and TTS with structured outputs
"""

import random
import streamlit as st
from openai import OpenAI
import io
import re
from typing import Optional, List, Dict, Literal
from pydantic import BaseModel, Field
import logging

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


class QuerySummary(BaseModel):
    """Structured output for query result summarization"""
    summary: str = Field(
        description="Natural language summary of the query results"
    )
    key_insights: List[str] = Field(
        default_factory=list,
        description="Key insights or highlights from the data"
    )
    total_results: int = Field(
        description="Total number of results found"
    )
    authorized_count: Optional[int] = Field(
        None,
        description="Number of authorized agencies (if applicable)"
    )
    top_locations: List[str] = Field(
        default_factory=list,
        description="Top cities or countries mentioned"
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
    """Manages OpenAI API calls with error handling and rate limiting"""
    
    def __init__(self):
        """Initialize OpenAI client"""
        self.client = self._get_client()
        self.voice_map = {
            "العربية": "onyx",  # Deeper voice for Arabic
            "English": "alloy"
        }
    
    @st.cache_resource
    def _get_client(_self):
        """Get cached OpenAI client"""
        api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("key")
        if not api_key:
            logger.error("OpenAI API key not found")
            st.warning("⚠️ OpenAI API key missing in Streamlit secrets")
            st.stop()
        return OpenAI(api_key=api_key)
    
    def build_chat_context(self, limit: int = 6) -> List[Dict[str, str]]:
        """
        Build chat context from recent messages
        Excludes messages with dataframes
        """
        if "chat_memory" not in st.session_state:
            return []
        
        context = []
        recent = st.session_state.chat_memory[-limit:] if len(st.session_state.chat_memory) > limit else st.session_state.chat_memory
        
        for msg in recent:
            if "dataframe" in msg or "result_data" in msg:
                continue
            context.append({
                "role": msg["role"],
                "content": msg["content"]
            })
        
        return context
    
    def detect_intent(self, user_input: str, language: str) -> Dict:
        """
        Detect user intent using LLM with structured output
        Returns: Dict with intent, confidence, and reasoning
        """
        intent_prompt = f"""
        You are a fraud-prevention assistant for Hajj pilgrims. Classify this message into ONE of four categories:

        1️⃣ GREETING: greetings like hello, hi, how are you, salam, السلام عليكم, مرحبا. 
        - No specific agency information is provided.
        - User just wants to chat or start conversation.

        2️⃣ DATABASE: questions about verifying specific Hajj agencies, checking authorization, company details, locations, contacts, etc.
        - User mentions agency names, locations, or asks for authorized agencies.

        3️⃣ GENERAL_HAJJ: general Hajj-related questions (rituals, requirements, documents, safety, procedures).

        4️⃣ NEEDS_INFO: message is too vague or lacks details needed to provide accurate information, such as:
        - "I want to verify an agency" (which agency?)
        - "Tell me about Hajj companies" (what specifically?)
        - "Is this authorized?" (which company?)
        - "Check this company" (need company name)

        CRITICAL CONTEXT:
        - 415 fake Hajj offices closed in 2025
        - 269,000+ unauthorized pilgrims stopped
        - Mission: prevent fraud, protect pilgrims
        - For DATABASE questions, we need specific agency names or clear location criteria
        - Mark as NEEDS_INFO if user should provide more details

        Message: {user_input}

        Classify the intent, provide confidence score, and explain your reasoning.
        """
        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You classify user intents for a Hajj agency verification system."},
                    {"role": "user", "content": intent_prompt},
                    *self.build_chat_context()
                ],
                response_format=IntentClassification,
                temperature=0
            )
            
            intent_data = response.choices[0].message.parsed
            logger.info(f"Intent detected: {intent_data.intent} (confidence: {intent_data.confidence})")
            
            return {
                "intent": intent_data.intent,
                "confidence": intent_data.confidence,
                "reasoning": intent_data.reasoning
            }
            
        except Exception as e:
            logger.error(f"Structured intent detection failed: {e}")
            # Fallback to heuristics
            return self._fallback_intent_detection(user_input)
    
    def _fallback_intent_detection(self, user_input: str) -> Dict:
        """Fallback intent detection using heuristics"""
        ui = user_input.lower()
        
        if any(g in ui for g in ["hello", "hi", "salam", "السلام", "مرحبا"]):
            intent = "GREETING"
        elif any(k in ui for k in ["company", "agency", "معتمد", "شركات", "authorized", "وكالة"]):
            # Check if query is too vague
            if len(ui.split()) < 4 and not any(specific in ui for specific in ["royal", "alhuda", "مكة", "جدة", "riyadh"]):
                intent = "NEEDS_INFO"
            else:
                intent = "DATABASE"
        else:
            intent = "GENERAL_HAJJ"
        
        return {
            "intent": intent,
            "confidence": 0.7,
            "reasoning": "Determined by keyword matching (fallback)"
        }
        
    def generate_greeting(self, user_input: str, language: str) -> str:
        """Generate natural greeting response with structured output"""
        is_arabic = language == "العربية"
        
        system_prompt = """You are a friendly Hajj assistant. Generate a warm, natural greeting that:
1. Acknowledges the user's greeting
2. Expresses willingness to help
3. Mentions you can help with Hajj company verification
4. Keep response under 3 sentences
5. Use emojis appropriately""" + (" Respond in Arabic." if is_arabic else " Respond in English.")
        
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
            return "Hello! 👋 How can I help you today?" if not is_arabic else "السلام عليكم! 👋 كيف يمكنني مساعدتك؟"
    
    def generate_general_answer(self, user_input: str, language: str) -> str:
        """Generate answer for general Hajj questions"""
        system_prompt = """You are a helpful assistant specialized in Hajj information. 
Be concise, factual, and helpful. Focus on practical information.
Avoid religious rulings - stick to practical guidance."""
        
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
        """
        Generate SQL query from user input with structured output
        Returns: Dict with sql_query, query_type, filters, explanation, safety_checked
        """
        sql_prompt = self._get_sql_system_prompt(language) + f"\n\nUser Question: {user_input}"
        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a SQL expert that generates safe queries for a Hajj agency database."},
                    {"role": "user", "content": sql_prompt},
                    *self.build_chat_context()
                ],
                response_format=SQLQueryGeneration,
                temperature=0
            )
            
            sql_data = response.choices[0].message.parsed
            
            logger.info(f"SQL generated - Type: {sql_data.query_type}, Safety: {sql_data.safety_checked}")
            logger.info(f"Explanation: {sql_data.explanation}")
            
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
        Generate natural, friendly, and structured summary of query results.
        Adds assistant-like sentences and recommendations based on intent.
        """
        if row_count == 0:
            return {
                "summary": "No results found. Try rephrasing your question or broadening the search." if language == "English" else "لم يتم العثور على نتائج. حاول إعادة صياغة السؤال.",
                "key_insights": [],
                "total_results": 0,
                "authorized_count": None,
                "top_locations": []
            }

        

        summary_prompt = f"""
You are a multilingual fraud-prevention and travel assistant for Hajj agencies.

Your task:
→ Summarize SQL query results clearly and naturally, with a warm, conversational tone that feels friendly and professional.

Context:
- User question: {user_input}
- Total rows returned: {row_count}
- Language: {language}
- Use Arabic if user language is العربية, otherwise English.

INSTRUCTIONS:
1. Start with a short, friendly intro if applicable like “Sure, here’s what I found!” or “أكيد! هذا ما وجدته لك 👇”.
2. Summarize the main results:
   - If the query lists *agencies*, use bullet points (✅ Authorized / ❌ Not Authorized).
   - If the query counts *countries, cities, or agencies*, give a clear numeric summary.
   - If it’s location-based, mention key cities or regions.
3. Always include **authorization status** and **location** for agencies.
4. If contact details (email, phone, website) exist in the data, include them naturally from the results.
5. End with a friendly or reassuring closing line, for example:
   - “Go ahead, this agency looks legitimate.”  
   - “You can contact them confidently.”  
   - “Let me know if you’d like me to verify another one.”
6. Maintain a consistent, polite tone in the selected language.
7. Do NOT invent or guess any data — only summarize what’s actually in the database results.
8. Keep responses concise and easy to read.

---

### 🔹 English (verification example)
✅ Royal City Travel — Cairo, Egypt — Authorized  
This agency is verified and officially recognized. Go ahead — it’s safe to proceed!

### 🔹 Arabic (authorization example)
وكالة **المدينة المتميزة للحج** — جدة، السعودية — ✅ معتمدة  
يمكنك الاعتماد عليها بثقة. هل ترغب أن أتحقق من وكالة أخرى؟

---

### Example outputs

**English Example:**
Sure, here’s what I found!  
Abdullah Ali Abdullah Bin Mahfouz & Partners Company is authorized to serve domestic pilgrims in Saudi Arabia.  
You can contact them at +966 55 123 4567 or info@mahfouzgroup.com.  
Go ahead — this agency looks legitimate and ready to assist you.

**Arabic Example:**
أكيد! هذا ما وجدته لك 👇  
شركة عبدالله علي عبدالله بن محفوظ وشركاه مصرح لها بخدمة الحجاج داخل المملكة.  
يمكنك التواصل معهم على الرقم +966551234567 أو عبر البريد info@mahfouz.com.  
تفضل، وكالة موثوقة يمكنك الاعتماد عليها.

---

Now summarize the query results following these instructions.
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

            logger.info(f"Summary generated with {len(summary_data.key_insights)} insights")

            return {
                "summary": final_summary,
                "key_insights": summary_data.key_insights,
                "total_results": summary_data.total_results,
                "authorized_count": summary_data.authorized_count,
                "top_locations": summary_data.top_locations
            }

        except Exception as e:
            logger.error(f"Structured summary generation failed: {e}")
            return {
                "summary": f"📊 Found {row_count} matching records.",
                "key_insights": [],
                "total_results": row_count,
                "authorized_count": None,
                "top_locations": []
            }

    def text_to_speech(self, text: str, language: str) -> Optional[io.BytesIO]:
        """
        Convert text to speech using OpenAI TTS
        Returns BytesIO audio ready for st.audio
        """
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
    
    @staticmethod
    def _get_sql_system_prompt(language: str) -> str:
        """Get SQL generation system prompt"""
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

    CURRENT LANGUAGE: {language}


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
    9    --------------------------------------------

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
📘 QUERY INTERPRETATION RULES:
...
⚙️ For company name searches:
Always normalize and deduplicate company names.
Use LOWER(TRIM()) and SELECT DISTINCT to avoid case duplicates.


    Q: "هل شركة الهدى معتمدة؟"
    → ELECT DISTINCT hajj_company_en, hajj_company_ar, formatted_address, city, country, email, contact_Info, rating_reviews, is_authorized
FROM agencies
WHERE (LOWER(TRIM(hajj_company_en)) LIKE LOWER('%alhuda%')
   OR LOWER(TRIM(hajj_company_ar)) LIKE LOWER('%الهدى%'))
LIMIT 50;
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
    
    def ask_for_more_info(self, user_input: str, language: str) -> Dict:
        """Generate structured response asking user for more specific information"""
        is_arabic = language == "العربية"
        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You help users provide more specific Hajj agency queries."},
                    {"role": "user", "content": user_input}
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
            if is_arabic:
                return {
                    "needs_info": "عذراً، هل يمكنك تقديم المزيد من التفاصيل؟ 🤔",
                    "suggestions": ["هل شركة الهدى للحج معتمدة؟", "أريد التحقق من وكالات الحج في مكة"],
                    "missing_info": ["اسم الوكالة", "الموقع"],
                    "sample_query": "هل شركة الهدى للحج معتمدة؟"
                }
            else:
                return {
                    "needs_info": "Could you provide more details? 🤔",
                    "suggestions": ["Is Al Huda Hajj Agency authorized?", "Show me authorized agencies in Makkah"],
                    "missing_info": ["agency name", "location"],
                    "sample_query": "Is Al Huda Hajj Agency authorized?"
                }