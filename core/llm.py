"""
LLM Manager Module
Handles OpenAI API interactions for chat and TTS with structured outputs
Enhanced with company memory tracking for context-aware conversations
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
            "العربية": "onyx",  # Deeper voice for Arabic
            "English": "alloy"
        }
        # Initialize company memory tracking
        if "last_company_name" not in st.session_state:
            st.session_state["last_company_name"] = None
            logger.info("🆕 Initialized company memory tracking")
    
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
        """
        Build chat context from recent messages
        - limit: max number of messages to include, None = all
        """
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
        """
        Update the last mentioned company in session state
        This enables context-aware follow-up questions
        """
        if company_name:
            st.session_state["last_company_name"] = company_name
            logger.info(f"💾 Company memory updated: {company_name}")
    
    def _is_followup_question(self, text: str) -> bool:
        """
        Detect if a question is a follow-up (vague reference to previous context)
        Short questions with location/detail keywords are likely follow-ups
        """
        text_lower = text.lower().strip()
        
        # Short questions (4 words or less) are candidates for follow-ups
        if len(text_lower.split()) <= 4:
            followup_keywords_ar = [
                "موقع", "عنوان", "موجود", "معتمد", "مصرح", "رقم", "ايميل", 
                "تفاصيل", "تقييم", "خريطة", "وين", "كيف", "متى", 
                "هل هي", "هل هو", "فين", "ايش", "شنو"
            ]
            followup_keywords_en = [
                "location", "address", "where", "authorized", "phone", "email", 
                "details", "rating", "map", "is it", "contact", "info", "number"
            ]
            
            all_keywords = followup_keywords_ar + followup_keywords_en
            return any(kw in text_lower for kw in all_keywords)
        
        return False

    def detect_intent(self, user_input: str, language: str) -> Dict:
        """
        Detect user intent using LLM with structured output and company extraction
        Automatically enriches follow-up questions with company context
        Returns: Dict with intent, confidence, reasoning, and extracted_company
        """
        
        last_company = st.session_state.get("last_company_name", "")
        original_input = user_input
        
        # Auto-enrich vague follow-up questions with last company context
        if last_company and self._is_followup_question(user_input):
            if language == "العربية":
                user_input = f"{user_input.strip()} (للشركة: {last_company})"
            else:
                user_input = f"{user_input.strip()} (about {last_company})"
            logger.info(f"🔗 Context auto-enriched: '{original_input}' → '{user_input}'")

        intent_prompt = f"""
You are a fraud-prevention assistant for Hajj pilgrims. 
Use the full conversation context and any previously mentioned company.

🧠 CONTEXT MEMORY:
Last company mentioned in conversation: {last_company if last_company else 'None'}

🎯 CRITICAL FOLLOW-UP DETECTION:
If user asks a follow-up question like:
- Arabic: "وين موقعها؟" / "هل هي معتمدة؟" / "أعطني التفاصيل" / "رقم التواصل؟"
- English: "Where is it located?" / "Is it authorized?" / "Give me details" / "Contact number?"

AND there's a last_company in memory, then:
1. Classify as DATABASE
2. Extract that last_company as the company name
3. Set high confidence (0.95+)
4. Reasoning should mention "follow-up question about [company name]"

📋 Classify this message into ONE of four categories:

1️⃣ GREETING: 
- Greetings like hello, hi, how are you, salam, السلام عليكم, مرحبا
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
                    *self.build_chat_context(limit=5)  # Include recent context for better understanding
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
            # Fallback to heuristics
            return self._fallback_intent_detection(user_input)
    
    def _fallback_intent_detection(self, user_input: str) -> Dict:
        """Fallback intent detection using heuristics when API fails"""
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
            "reasoning": "Determined by keyword matching (fallback)",
            "extracted_company": None
        }
        
    def generate_greeting(self, user_input: str, language: str) -> str:
        """Generate natural greeting response with structured output"""
        is_arabic = language == "العربية"
        
        system_prompt = """You are a friendly Hajj and fraud prevention assistant designed to protect pilgrims from scams and help them verify hajj agencies authorized from Ministry of Hajj and Umrah. 
Generate a short, warm, natural greeting (max 3 sentences) that:
- Acknowledges the user's greeting
- Expresses willingness to help
- Mentions you can help verify Hajj companies
- Uses emojis appropriately
- Respond in Arabic **if the user input contains any Arabic text**, otherwise respond in English
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
            return "Hello! 👋 How can I help you today?" if not is_arabic else "السلام عليكم! 👋 كيف يمكنني مساعدتك؟"
    
    def generate_general_answer(self, user_input: str, language: str) -> str:
        """Generate answer for general Hajj questions"""
        system_prompt = """You are a helpful assistant specialized in Hajj information. 
Be concise, factual, and helpful. Focus on practical information.
Detect if the user's question is in Arabic or English, and respond in the same language.
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
        """
        Generate SQL query from user input with structured output and context awareness
        Automatically includes company context for follow-up questions
        Returns: Dict with sql_query, query_type, filters, explanation, safety_checked
        """
        
        last_company = st.session_state.get("last_company_name", "")
        
        # If user asks follow-up without mentioning company, inject context note
        if last_company and self._is_followup_question(user_input):
            context_note = f"\n\n⚠️ IMPORTANT CONTEXT: User is asking a follow-up question about '{last_company}' (mentioned previously in conversation). Generate SQL query specifically for this company."
        else:
            context_note = ""
        
        sql_prompt = self._get_sql_system_prompt(language) + f"\n\nUser Question: {user_input}{context_note}"
        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a SQL expert that generates safe queries for a Hajj agency database. Pay special attention to context notes about previously mentioned companies."},
                    {"role": "user", "content": sql_prompt},
                    *self.build_chat_context()
                ],
                response_format=SQLQueryGeneration,
                temperature=0
            )
            
            sql_data = response.choices[0].message.parsed
            
            # Update company memory if extracted from SQL context
            if sql_data.extracted_company:
                self.update_last_company(sql_data.extracted_company)
            
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
        Auto-detects language from user input for accurate responses.
        """
        # Auto-detect language from user input (override parameter if needed)
        detected_language = self._detect_language_from_text(user_input)
        if detected_language:
            language = detected_language
            logger.info(f"🌐 Language auto-detected from input: {language}")
        
        if row_count == 0:
            return {
                "summary": "No results found. Try rephrasing your question or broadening the search." if language == "English" else "لم يتم العثور على نتائج. حاول إعادة صياغة السؤال.",
            }

        
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
    
    def _detect_language_from_text(self, text: str) -> Optional[str]:
        """
        Detect if text is Arabic or English based on character analysis
        Returns: "العربية" or "English" or None
        """
        if not text:
            return None
        
        # Count Arabic and English characters
        arabic_chars = sum(1 for c in text if '\u0600' <= c <= '\u06FF')
        english_chars = sum(1 for c in text if c.isalpha() and c.isascii())
        
        total_chars = arabic_chars + english_chars
        if total_chars == 0:
            return None
        
        # If more than 30% Arabic characters, consider it Arabic
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
        
        last_company = st.session_state.get("last_company_name", "")
        
        # If there's a company in memory but user didn't mention it, add context
        if last_company and "agency" not in user_input.lower() and "شركة" not in user_input and "وكالة" not in user_input:
            user_input += f" (Note: User was previously asking about '{last_company}')"
            
        prompt = f"""You are a helpful Hajj verification assistant.
The user's question: "{user_input}" needs more details to provide accurate information.

Examples of vague questions:
- "I want to verify an agency" (which agency?)
- "Tell me about Hajj companies" (what specifically?)
- "Is this authorized?" (which company?)
- "Check this company" (need company name)
- "وين موقعها؟" without context (which company's location?)

Ask for specific details in a friendly way. Focus on:
1. Agency name (if verifying a company)
2. Location (city/country)
3. What specifically they want to know

Use Arabic if user input is Arabic, otherwise English.
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
            if is_arabic:
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