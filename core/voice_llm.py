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
    

    
    def detect_intent(self, user_input: str, language: str, context_string=None) -> Dict:
        """
        Detect user intent using LLM with structured output
        Returns: Dict with intent, confidence, and reasoning

        """
        
        
        intent_prompt = f"""
You are a fraud-prevention assistant for Hajj pilgrims. Analyze the conversation history and current message to classify the user's intent.

INTENT CATEGORIES:

1️⃣ GREETING: 
   - Greetings like hello, hi, how are you, salam, السلام عليكم, مرحبا
   - User asks about your capabilities or services ("what can you do?", "how can you help?")
   - User wants to start a conversation
   - No specific agency information is provided
   - If user want to know the developer or the author

2️⃣ DATABASE: 
   - Questions about verifying specific Hajj agencies, checking authorization, company details
   - User mentions agency names, locations, or asks for authorized agencies
   - Queries requiring database lookup:
     • Count of agencies, list of countries/cities with agencies
     • "Is X authorized?", details about Y agency
     • Agency's address, email, phone, location, contact info
     • Checking if an agency is authorized or not
     • Asking about Hajj offices in specific city or country
     • Mentioning company names (like "Royal City", "Al-Safa", etc.)
   
   **CONTEXT-AWARE DATABASE CLASSIFICATION:**
   - If user says "are they authorized?", "what's their address?", "tell me more about them"
     → Check context: if an agency was mentioned previously → DATABASE
   - If user provides agency name after being asked → DATABASE
   - Follow-up questions about previously mentioned agency → DATABASE
   
   **Response Requirements:**
   - Respond in the same language as the user message

3️⃣ GENERAL_HAJJ: 
   - General Hajj-related questions (rituals, requirements, documents, safety, procedures)
   - Questions about Hajj process, visa, costs, timing, health requirements
   - Travel tips, what to bring, health advice
   - Hajj regulations and rules

4️⃣ NEEDS_INFO: 
   - Message is too vague or lacks details needed for accurate response
   - user input is cut off, incomplete, or uses ambiguous words like 'you', 'me', etc.,
   - Examples:
     • "I want to verify an agency" (which agency?)
     • "Tell me about Hajj companies" (what specifically?)
     • "Is this authorized?" (which company? - unless mentioned in context)
     • "Check this company" (need company name - unless in context)
   
   **EXCEPTION:** If conversation context contains agency reference, DON'T mark as NEEDS_INFO

CRITICAL CONTEXT:
- 415 fake Hajj offices closed in 2025
- 269,000+ unauthorized pilgrims stopped
- Mission: prevent fraud, protect pilgrims
- For DATABASE questions, we need specific agency names or clear location criteria
- Mark as NEEDS_INFO if user should provide more details

**CONTEXT-AWARE RULES:**
1. Check conversation context for agency references before marking NEEDS_INFO
2. Pronouns like "they", "them", "their", "it" → Look in context for referent
3. "This company", "that agency" → Check if identified in previous messages
4. Follow-up questions → Consider previous topic and continue classification
5. User providing info after NEEDS_INFO response → Mark as DATABASE

---

**CURRENT MESSAGE:** {user_input}

**CONVERSATION CONTEXT:**
{context_string}

---

Analyze the conversation history and current message. Classify the intent, provide confidence score (0.0-1.0), 
and explain your reasoning.
"""
        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You classify user intents for a Hajj agency verification system."},
                    {"role": "user", "content": intent_prompt}],
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
        
    def generate_greeting(self, user_input: str, language: str, context_string=None) -> str:
        """Generate natural greeting response with structured output"""
        is_arabic = language == "العربية"
        context_string = context_string if context_string else ""
        
        system_prompt = f"""You are a friendly Hajj and fraud prevention assistant designed to protect pilgrims form scams and help them verify hajj agencies authorized from Ministry of Hajj and Umrah. 
Generate a short, warm, natural greeting (max 3 sentences) that:
- Acknowledges the user's greeting
- Respond friendly when user ask about how are doing or how are you
- Expresses willingness to help
- Make sure you help and understand the user
- Mentions you can help verify Hajj companies
- Detect User language and use it in your response
- Uses emojis appropriately
 If the user asks about your developer, generate a **new, friendly response every time** that has the **same meaning** as:
  "I’m the result of the hard work of three brilliant girls! 💡 Their goal is to make Hajj agency verification simple and trustworthy."
- Respond in Arabic **if the user input contains any Arabic text**, otherwise respond in English
explain your reasoning and what you provide briefly.
User input: {user_input}
Use this context if helpful: {context_string}
Keep the response concise, friendly, and professional."""

        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                    
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
    
    def generate_general_answer(self, user_input: str, language: str, context_string=None) -> str:
        """Generate answer for general Hajj questions"""
        system_prompt = f"""You are a helpful assistant specialized in Hajj information. 
Be concise, factual, and helpful. Focus on practical information.
Detect if the user's question is in Arabic or English, and respond in the same language.
you designed to protect pilgrims form scams and help them verify hajj agencies authorized from Ministry of Hajj and Umrah
- Always respond in the same language as the user question.
- Speak naturally, like a caring assistant giving helpful information.
- Avoid bullet points, numbering, or reading URLs or links.
 - Make sure you help and understand the user
  Detect User language and use it in your response

- User question: {user_input}
- Use this Context if helpful: {context_string}
- Make sure your info is up-to-date
Avoid religious rulings or fatwa - stick to practical guidance."""
        
        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input},
                ],
                temperature=0.6,
                max_tokens=400
            )
            return response.choices[0].message.content.strip()
            
        except Exception as e:
            logger.error(f"General answer generation failed: {e}")
            return "I encountered an error. Please try rephrasing your question."
    
    def generate_sql(self, user_input: str, language: str ,context_string= None) -> Optional[Dict]:
        """
        Generate SQL query from user input with structured output
        Returns: Dict with sql_query, query_type, filters, explanation, safety_checked
        """
        sql_prompt = self._get_sql_system_prompt(language, context_string) + f"\n\nUser Question: {user_input}"
        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a SQL expert that generates safe queries for a Hajj agency database."},
                    {"role": "user", "content": sql_prompt},
        
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
    
    def generate_summary(self, user_input: str, language: str, row_count: int, sample_rows: List[Dict], context_string=None) -> Dict:
        """
        Generate natural, friendly, and structured summary of query results.
        Adds assistant-like sentences and recommendations based on intent.
        """
        if row_count == 0:
            return {
                "summary": "No results found. Try rephrasing your question or broadening the search." if language == "english" else "لم يتم العثور على نتائج. حاول إعادة صياغة السؤال.",
            }

        
        data_preview = json.dumps(sample_rows[:50], ensure_ascii=False)

        summary_prompt = f"""
        You are a multilingual fraud-prevention and travel assistant for Hajj pilgrims. 
        Your task is to summarize the database query results in a warm, natural, and voice-friendly way.

        User question: {user_input}
        Language: {language}
        Data: {data_preview}

        🎯 GOAL:
        Provide a natural spoken summary that sounds like you're talking to the listener — not reading a list or a table.

        Guidelines:
        - Always Acknowledge the user's question
        - translate any word and any database column based on the user language
        - Always respond in the same language as the user question.
        - Speak naturally, like a caring assistant giving helpful information.
        
        - Avoid bullet points, numbering, or reading URLs or links.
        - Mention only the most important details such as agency name, city, country, whether it's authorized, and rating if available.
        - Summarize multiple agencies conversationally, e.g.:
        - "I found several authorized agencies in Makkah. One of them is Al Huda Hajj Company, based in Saudi Arabia. It's an authorized agency with good reviews."
        - "Another trusted one is Royal City Hajj Agency located in Riyadh."
        - Keep your tone friendly, respectful, and professional.
        - Include helpful connecting phrases like "In general", "You might want to know that", or "Most of them are authorized".
        - Do not say column names or data labels — integrate information naturally.
        - Never output or read raw SQL, brackets, quotes, or database field names.
        - End with a gentle offer to assist further, such as:
        - "Would you like me to check more agencies for you?"
        - "Would you like to hear their contact details?"
        - Use emojis sparingly to enhance friendliness.
         Detect User language and use it in your response

        📞 CRITICAL - NUMBER FORMATTING RULES:
        Use NUMERIC DIGITS for all numbers, not spelled-out words:
        ✅ CORRECT FORMAT:
        - Ratings: "3.8 stars" or "4.6 ⭐" (NOT "three point eight stars")
        - Reviews: "217 reviews" (NOT "two hundred seventeen reviews")
        - Phone numbers: "+966 12 345 6789" (NOT "plus nine six six twelve...")
        - Counts: "5 agencies" (NOT "five agencies")

        ❌ NEVER spell out numbers like:
        - "three point eight stars" → Use "3.8 stars"
        - "two hundred seventeen reviews" → Use "217 reviews"
        - "plus nine six six" → Use "+966"
        - "four hundred seventy-one" → Use "471"

        Make sure you help and understand the user


        EXAMPLES OF CORRECT OUTPUT:
        "Al Haramain Travel is located in Amman, Jordan. They have a rating of 3.8 stars based on 217 reviews."
        "PT. Al Haramain Jaya Wisata in Jakarta, Indonesia has a rating of 4.6 stars from 39 reviews."
        "You can contact them at +966 12 533 3399."
        Use this context if helpful: {context_string}

        The response should sound fluid and natural, with ALL numbers written as digits for clear display and proper TTS pronunciation.
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
            logger.info("Summary generated successfully.")


            return {
                "summary": final_summary,
            }

        except Exception as e:
            logger.error(f"Structured summary generation failed: {e}")
            return {
                "summary": f"📊 Found {row_count} matching records.",
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
    def _get_sql_system_prompt(language: str, context_string=None) -> str:
        """Get SQL generation system prompt"""
        return f"""
    You are a multilingual SQL fraud-prevention expert protecting Hajj pilgrims.

    🎯 MISSION: Generate an SQL query for database analysis on Hajj agencies.
    Do NOT generalize to world data — always query from the table 'agencies'.
    Use the CONTEXT and USER QUESTION to create a safe, accurate SQL SELECT query.
    Context: {context_string}

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
    4. translate city and country, etc if needed based on user language

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

    Make sure you help and understand the user



    Q: "هل شركة الهدى معتمدة؟"
    → ELECT DISTINCT hajj_company_en, hajj_company_ar, formatted_address, city, country, email, contact_Info, rating_reviews, is_authorized, google_maps_link
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
    
    def ask_for_more_info(self, user_input: str, language: str, context_string=None) -> Dict:
        
        is_arabic = language == "العربية"
        
        # Simple cutoff/ambiguous detection (words like 'you', 'me', or very short incomplete input)
        cutoff_keywords = ["you", "me", "i", "it", "this", "that", "check", "verify", "agency"]
        is_cutoff = any(user_input.lower().strip().endswith(word) for word in cutoff_keywords) \
                    or len(user_input.strip()) < 5
        
        prompt = f"""
    You are a helpful Hajj verification assistant.
    Express willingness to help
    Make sure you help and understand the user
    The user's question: "{user_input}" needs more details to provide accurate information.
    Context: {context_string}

    Examples of vague questions:
    - "I want to verify an agency" (which agency?)
    - "Tell me about Hajj companies" (what specifically?)
    - "Is this authorized?" (which company?)
    - "Check this company" (need company name)

    If the user input is cut off, incomplete, or uses ambiguous words like 'you', 'me', etc.,
    prompt them to clarify politely.

    Ask for specific details in a friendly way:
    1. Agency name (if verifying a company)
    2. Location (city/country)
    3. What specifically they want to know

    Use Arabic if user input is Arabic, otherwise English.
    Use emojis appropriately.
    Keep it brief but friendly.
    Add a simple example of a more specific question.

    """

        if is_cutoff:
            prompt += "\nNote: The user's input may be incomplete or vague. Please ask them to clarify."


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
