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
from datetime import datetime

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
    
    def build_chat_context(self, limit: Optional[int] = None) -> List[Dict[str, str]]:
        """
        Build chat context from all recent messages (or limited number)
        Includes metadata like intent, company, timestamp for stronger memory.
        """
        if "chat_memory" not in st.session_state:
            return []

        # Take all messages if limit=None
        recent = st.session_state.chat_memory if limit is None else st.session_state.chat_memory[-limit:]

        context = []
        for msg in recent:
            # Skip non-chat dataframes or result data
            if "dataframe" in msg or "result_data" in msg:
                continue
            context.append({
                "role": msg["role"],
                "content": msg["content"],
                "intent": msg.get("intent"),
                "company": msg.get("company"),
                "timestamp": msg.get("timestamp")
            })
        return context

    def update_last_company(self, company_name: Optional[str]):
        """
        Update the last mentioned company in session state.
        Enhancement: keep a history of all mentioned companies.
        """
        if company_name:
            # Update last company
            st.session_state["last_company_name"] = company_name

            # Maintain full history of companies
            if "mentioned_companies" not in st.session_state:
                st.session_state["mentioned_companies"] = []
            if company_name not in st.session_state["mentioned_companies"]:
                st.session_state["mentioned_companies"].append(company_name)

            logger.info(f"💾 Company memory updated: {company_name}")
            logger.info(f"📜 Full company history: {st.session_state['mentioned_companies']}")

    def _is_followup_question(self, text: str) -> bool:
        """
        Detect if a question is a follow-up based on:
        - Short length with keywords
        - Reference to previously mentioned companies
        - Explicitly asking about previous messages
        """
        text_lower = text.lower().strip()

        followup_keywords_ar = [
            "موقع", "عنوان", "موجود", "معتمد", "مصرح", "رقم", "ايميل",
            "تفاصيل", "تقييم", "خريطة", "وين", "كيف", "متى",
            "هل هي", "هل هو", "فين", "ايش", "شنو", "موجودة",
            "في الرياض", "في مكة", "في جدة", "في المدينة"
        ]
        followup_keywords_en = [
            "location", "address", "where", "authorized", "phone", "email",
            "details", "rating", "map", "is it", "contact", "info", "number",
            "in riyadh", "in makkah", "in jeddah", "in medina", "there", "located"
        ]

        # Short questions with keywords
        if len(text_lower.split()) <= 6 and any(kw in text_lower for kw in followup_keywords_ar + followup_keywords_en):
            return True

        # Check mentioned companies safely
        mentioned_companies = st.session_state.get("mentioned_companies", [])
        for company in mentioned_companies:
            if company.strip().lower() in text_lower:
                return True

        # Explicit reference to previous messages
        previous_refs = ["الرسالة الأخيرة", "ماذا قلت", "سابقًا", "last message", "previous message"]
        if any(ref in text_lower for ref in previous_refs):
            return True

        return False
    def store_bot_reply(self, reply_text: str, intent: str, extracted_company: Optional[str] = None):
        """Store assistant reply in chat memory with metadata"""
        if "chat_memory" not in st.session_state:
            st.session_state.chat_memory = []
        
        st.session_state.chat_memory.append({
            "role": "assistant",
            "content": reply_text,
            "intent": intent,
            "extracted_company": extracted_company,
            "timestamp": str(datetime.now())
        })
        logger.info(f"💾 Stored assistant reply: {reply_text[:50]}... | Intent: {intent} | Company: {extracted_company or 'None'}")



    def detect_intent(self, user_input: str, language: str) -> Dict:
        """
        Detect user intent using LLM with strong memory.
        Remembers ALL previous user messages and all mentioned companies.
        Returns: Dict with intent, confidence, reasoning, and extracted_company
        """
        # ----------------------------
        # Initialize memory if missing
        # ----------------------------
        if "chat_memory" not in st.session_state:
            st.session_state.chat_memory = []
        if "mentioned_companies" not in st.session_state:
            st.session_state.mentioned_companies = []

        original_input = user_input
        chat_memory = st.session_state.chat_memory
        last_companies = st.session_state.mentioned_companies

        # ----------------------------
        # Detect follow-up
        # ----------------------------
        is_followup = self._is_followup_question(user_input)
        # Detect if user is referring to a previous message
        previous_keywords = [
            "الرسالة الأخيرة", "ماذا قلت", "وش قلت", "جاوبتني", "ردك السابق", 
            "عيد آخر رد", "الرد الأخير", "last message", "previous message", "your last reply"
        ]

        previous_msg_note = ""
        if any(kw in user_input.lower() for kw in previous_keywords):
            previous_msg_note = "User asked about the previous message or previous reply."
            last_msg = None

            if "chat_memory" in st.session_state:
                for msg in reversed(st.session_state.chat_memory):
                    if msg["role"] == "assistant":
                        last_msg = msg["content"]
                        break

            if last_msg:
                user_input = (
                    f"The user is asking about your previous answer. "
                    f"Here was your last response:\n\n{last_msg}\n\n"
                    "Please answer accordingly."
                )
                logger.info("🔁 Added last assistant reply to context.")



        # Auto-enrich vague follow-up with last company
        if last_companies and is_followup:
            last_company = last_companies[-1]
            if language == "العربية":
                user_input = f"هل شركة {last_company} {original_input.strip()}"
            else:
                user_input = f"Is {last_company} {original_input.strip()}"
            logger.info(f"🔗 Context auto-enriched: '{original_input}' → '{user_input}'")

        # ----------------------------
        # Build conversation context
        # ----------------------------
        context_text = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in chat_memory])

        intent_prompt = f"""
        You are a fraud-prevention assistant for Hajj pilgrims.
        Use the full conversation history and all previously mentioned companies.
        Focus on preventing fraud, verifying agencies, and guiding users accurately.

        🧠 CONTEXT MEMORY:
        - Previous messages:
        {context_text if context_text else 'None'}
        - Previously mentioned companies:
        {', '.join(last_companies) if last_companies else 'None'}
        - Note: If user asked about a previous message, include the last assistant reply.

        🎯 FOLLOW-UP DETECTION:
        - If user asks a follow-up question about a company or location:
        Arabic examples: "وين موقعها؟", "هل هي معتمدة؟", "أعطني التفاصيل", "رقم التواصل؟", "هل موجودة في الرياض؟"
        English examples: "Where is it located?", "Is it authorized?", "Give me details", "Contact number?", "Is it in Riyadh?"
        - If a last_company exists, classify as DATABASE with high confidence (0.95+)
        - Reasoning should mention: "Follow-up question about [company] - checking existence/details"

        📋 INTENT CATEGORIES:
        1. GREETING:
        - Greetings like hello, hi, how are you, salam, السلام عليكم, مرحبا
        - No specific agency information
        - User asks about capabilities/services or just wants to chat
        2. DATABASE:
        - Questions about verifying Hajj agencies
        - Authorization, company details, locations, contacts
        - Examples: "Is X authorized?", "Address/email/phone of Y", "Agencies in Riyadh or Mecca"
        3. GENERAL_HAJJ:
        - General Hajj questions (rituals, requirements, safety, procedures)
        - Not about specific agencies
        4. NEEDS_INFO:
        - Vague or incomplete questions
        - Examples: "I want to verify an agency" (which one?), "Tell me about Hajj companies" (specify which)

        🔍 COMPANY EXTRACTION:
        - Extract any company name mentioned in the user's message
        - Examples:
        "شركة جبل عمر" → "جبل عمر"
        "Royal City Agency" → "Royal City"
        "وكالة الهدى" → "الهدى"
        "Al Safa Travel" → "Al Safa"

        🚨 CRITICAL CONTEXT:
        - 415 fake Hajj offices closed in 2025
        - 269,000+ unauthorized pilgrims stopped
        - Mission: prevent fraud and protect pilgrims
        - For DATABASE questions, we need company names or clear location criteria

        Message to classify: {user_input}

        Return JSON with:
        - intent (GREETING, DATABASE, GENERAL_HAJJ, NEEDS_INFO)
        - extracted_company (if any)
        - confidence (0-1)
        - reasoning
        """

            # ----------------------------
        # Call LLM
        # ----------------------------
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You classify user intents and extract company names with full context."},
                    {"role": "user", "content": intent_prompt}
                ],
                response_format=IntentClassification,
                temperature=0
            )
            intent_data = response.choices[0].message.parsed

            # ----------------------------
            # Update company memory
            # ----------------------------
            if intent_data.extracted_company and intent_data.extracted_company not in last_companies:
                st.session_state.mentioned_companies.append(intent_data.extracted_company)
                logger.info(f"💾 Company memory updated: {intent_data.extracted_company}")

            # ----------------------------
            # Save user message
            # ----------------------------
            st.session_state.chat_memory.append({
                "role": "user",
                "content": original_input,
                "intent": intent_data.intent,
                "extracted_company": intent_data.extracted_company,
                "timestamp": str(datetime.now())
            })

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
        mentioned_companies = st.session_state.get("mentioned_companies", [])
        
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
        """Generate natural greeting response with structured output and store in chat memory"""
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
            greeting_text = greeting_data.greeting

            logger.info(f"Greeting generated with tone: {greeting_data.tone}")

            # ----------------------------
            # Store assistant reply using store_bot_reply
            # ----------------------------
            self.store_bot_reply(reply_text=greeting_text, intent="GREETING")

            return greeting_text
        
        except Exception as e:
            logger.error(f"Structured greeting generation failed: {e}")
            fallback = "Hello! 👋 How can I help you today?" if not is_arabic else "السلام عليكم! 👋 كيف يمكنني مساعدتك؟"
            self.store_bot_reply(reply_text=fallback, intent="GREETING")
            return fallback


    
    def generate_general_answer(self, user_input: str, language: str) -> str:
        """Generate answer for general Hajj questions with context and memory storage"""
        system_prompt = """You are a helpful assistant specialized in Hajj information. 
        Be concise, factual, and helpful. Focus on practical information.
        Detect if the user's question is in Arabic or English, and respond in the same language.
        You are designed to protect pilgrims from scams and help them verify hajj agencies authorized from Ministry of Hajj and Umrah.
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

            answer = response.choices[0].message.content.strip()

            # ----------------------------
            # Store assistant reply in memory
            # ----------------------------
            self.store_bot_reply(reply_text=answer, intent="GENERAL_HAJJ")

            return answer

        except Exception as e:
            logger.error(f"General answer generation failed: {e}")
            fallback = "I encountered an error. Please try rephrasing your question."
            self.store_bot_reply(reply_text=fallback, intent="GENERAL_HAJJ")
            return fallback


    
    def generate_sql(self, user_input: str, language: str) -> Optional[Dict]:
        """
        Generate SQL query from user input with structured output, context awareness,
        follow-up handling, and automatic memory storage.
        Returns: Dict with sql_query, query_type, filters, explanation, safety_checked
        """
        # ----------------------------
        # Retrieve last company and chat context
        # ----------------------------
        last_companies = st.session_state.get("mentioned_companies", [])
        last_company = last_companies[-1] if last_companies else None

        # Check if the input is a follow-up and enrich it with last company
        if last_company and self._is_followup_question(user_input):
            if language == "العربية":
                user_input = f"هل شركة {last_company} {user_input.strip()}"
            else:
                user_input = f"Is {last_company} {user_input.strip()}"
            logger.info(f"🔗 Context auto-enriched for SQL: '{user_input}'")

        # Prepare SQL system prompt
        sql_prompt = self._get_sql_system_prompt(language) + f"\n\nUser Question: {user_input}"

        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a SQL expert that generates safe queries for a Hajj agency database. Include context notes about previously mentioned companies."},
                    {"role": "user", "content": sql_prompt},
                    *self.build_chat_context(limit=5)
                ],
                response_format=SQLQueryGeneration,
                temperature=0
            )

            sql_data = response.choices[0].message.parsed

            # ----------------------------
            # Update company memory if extracted from SQL context
            # ----------------------------
            if sql_data.extracted_company:
                self.update_last_company(sql_data.extracted_company)

            # ----------------------------
            # Store assistant response in chat memory
            # ----------------------------
            if sql_data.sql_query and sql_data.safety_checked:
                summary_text = f"SQL query generated safely: {sql_data.sql_query}"
            else:
                summary_text = f"Could not generate safe SQL. Reason: {sql_data.explanation}"

            self.store_bot_reply(
                reply_text=summary_text,
                intent="DATABASE",
                extracted_company=sql_data.extracted_company
            )

            if sql_data.sql_query and sql_data.safety_checked:
                return {
                    "sql_query": sql_data.sql_query,
                    "query_type": sql_data.query_type,
                    "filters": sql_data.filters_applied,
                    "explanation": sql_data.explanation
                }
            else:
                return None

        except Exception as e:
            logger.error(f"Structured SQL generation failed: {e}")
            fallback = "⚠️ Could not generate SQL. Please rephrase your request."
            self.store_bot_reply(reply_text=fallback, intent="DATABASE")
            return None


    
    def generate_summary(self, user_input: str, language: str, row_count: int, sample_rows: List[Dict]) -> Dict:
        """
        Generate natural, friendly, and structured summary of query results.
        Uses chat context, updates company memory, and stores assistant reply.
        """
        # ----------------------------
        # Auto-detect language
        # ----------------------------
        detected_language = self._detect_language_from_text(user_input)
        if detected_language:
            language = detected_language
            logger.info(f"🌐 Language auto-detected from input: {language}")

        # ----------------------------
        # Handle zero results
        # ----------------------------
        last_company = st.session_state.get("last_company_name", "")
        location_keywords_ar = ["في", "الرياض", "جدة", "مكة", "المدينة"]
        location_keywords_en = ["in", "riyadh", "jeddah", "makkah", "medina"]

        if row_count == 0:
            is_location_query = any(kw in user_input.lower() for kw in location_keywords_ar + location_keywords_en)
            if last_company and is_location_query:
                fallback_summary = (
                    f"لم أجد شركة {last_company} في الموقع المحدد. ✨\n\n"
                    "هل تريد معرفة الموقع الفعلي لشركة {last_company}؟ أو البحث عن شركات أخرى؟"
                    if language == "العربية" else
                    f"I couldn't find {last_company} in the specified location. ✨\n\n"
                    "Would you like to know the actual location of {last_company}? Or search for other authorized agencies?"
                )
            else:
                fallback_summary = "No results found. Try rephrasing your question or broadening the search." if language == "English" else "لم يتم العثور على نتائج. حاول إعادة صياغة السؤال."
            
            self.store_bot_reply(reply_text=fallback_summary, intent="DATABASE", extracted_company=last_company)
            return {"summary": fallback_summary}

        # ----------------------------
        # Prepare data preview & prompt
        # ----------------------------
        data_preview = json.dumps(sample_rows[:50], ensure_ascii=False)

        summary_prompt = f"""
        You are a multilingual fraud-prevention assistant for Hajj agencies.

        User question: {user_input}
        Data: {data_preview}

        Instructions:
        - Respond entirely in {language} (Arabic/English), matching user's language.
        - Summarize the query results clearly, friendly, and professionally.
        - Highlight number of matching records and key details.
        - Include company name, address, city, country, contact info, rating, authorization status, and Google Maps link.
        - Use sentences and bullet points, add small friendly phrases sparingly.
        - Do NOT invent data.
        - If multiple results, list up to 10 agencies with important details.
        - If context is unclear or user did not specify a company, politely ask for clarification in {language}.

        Output format ({language}):
        - Name (Arabic / English):
        - City:
        - Country:
        - Email:
        - Contact Info:
        - Rating:
        - Status: (Yes, Authorized / No, Not Authorized)
        - Google Maps Link

        Behavior:
        - If user asks about a specific column, provide only that column's data.
        - Always respond concisely, clearly, and in a friendly tone.
        - Use chat context from previous messages if relevant.
        """

        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You summarize Hajj agency data in a friendly and structured way."},
                    {"role": "user", "content": summary_prompt},
                    *self.build_chat_context(limit=5)
                ],
                response_format=QuerySummary,
                temperature=0.6
            )

            summary_data = response.choices[0].message.parsed
            final_summary = summary_data.summary

            # ----------------------------
            # Update company memory if new company detected
            # ----------------------------
            if hasattr(summary_data, "extracted_company") and summary_data.extracted_company:
                self.update_last_company(summary_data.extracted_company)

            # ----------------------------
            # Store assistant reply
            # ----------------------------
            self.store_bot_reply(reply_text=final_summary, intent="DATABASE", extracted_company=summary_data.extracted_company if hasattr(summary_data, "extracted_company") else last_company)

            logger.info("Summary generated and stored successfully.")
            return {"summary": final_summary}

        except Exception as e:
            logger.error(f"Structured summary generation failed: {e}")
            fallback = f"📊 Found {row_count} matching records."
            self.store_bot_reply(reply_text=fallback, intent="DATABASE")
            return {"summary": fallback}

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
        """Get concise SQL generation prompt with context awareness"""
        return f"""
        You are a multilingual fraud-prevention assistant for Hajj agencies.
        Your task: Generate a valid SQL SELECT query ONLY for the 'agencies' table based on user input.
        Do NOT generalize to world data. Focus on company verification and location.

        Table: agencies
        - hajj_company_ar, hajj_company_en, formatted_address, city, country,
        - email, contact_Info, rating_reviews, is_authorized, google_maps_link, link_valid

        Rules:
        1. Respond in the same language as user input ({language}).
        2. If the user mentions a company, use flexible LIKE matching in both Arabic & English columns.
        3. For follow-up questions, prioritize last mentioned company from context.
        4. Handle locations (Mecca, Medina, Riyadh, Saudi Arabia, Pakistan, Egypt) using flexible LIKE.
        5. "Authorized" → add `AND is_authorized = 'Yes'`.
        6. Counts → use `SELECT COUNT(*)`; Distinct lists → use `SELECT DISTINCT column`.
        7. Limit 100 rows unless COUNT or DISTINCT is used.
        8. Return `NO_SQL` if no logical query can be formed.

        Output: Only one valid SQL SELECT query.

        Examples:
        - "هل شركة جبل عمر معتمدة؟" → SELECT DISTINCT hajj_company_en, hajj_company_ar, formatted_address, city, country, email, contact_Info, rating_reviews, is_authorized, google_maps_link
        FROM agencies
        WHERE (LOWER(TRIM(hajj_company_ar)) LIKE '%جبل%عمر%' OR LOWER(TRIM(hajj_company_en)) LIKE '%jabal%omar%')
        LIMIT 1;

        - "وين موقعها؟" (follow-up about "جبل عمر") → SELECT formatted_address, city, country, google_maps_link
        FROM agencies
        WHERE (LOWER(TRIM(hajj_company_ar)) LIKE '%جبل%عمر%' OR LOWER(TRIM(hajj_company_en)) LIKE '%jabal%omar%')
        LIMIT 1;

        - "Authorized agencies in Makkah" → SELECT * FROM agencies
        WHERE is_authorized = 'Yes' AND (city LIKE '%مكة%' OR LOWER(city) LIKE '%mecca%' OR LOWER(city) LIKE '%makkah%')
        LIMIT 25;

        - "كم عدد الشركات في المدينة؟" → SELECT COUNT(*) FROM agencies
        WHERE (city LIKE '%المدينة%' OR LOWER(city) LIKE '%medina%' OR LOWER(city) LIKE '%madinah%');
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
        """Generate structured response asking user for more specific information, with full context memory"""
        is_arabic = language == "العربية"
        
        # ----------------------------
        # Check for follow-up and last company
        # ----------------------------
        last_company = st.session_state.get("last_company_name", "")
        is_followup = self._is_followup_question(user_input)
        
        if last_company and is_followup and not any(word in user_input.lower() for word in ["agency", "شركة", "وكالة"]):
            user_input += f" (Note: User previously asked about '{last_company}')"
            logger.info(f"🔗 Follow-up question auto-enriched with last company: '{last_company}'")
        
        # ----------------------------
        # Build context from previous chat
        # ----------------------------
        context_text = "\n".join([f"{msg['role'].capitalize()}: {msg['content']}" for msg in self.build_chat_context(limit=10)])
        
        # ----------------------------
        # Prepare prompt
        # ----------------------------
        prompt = f"""
        You are a friendly Hajj verification assistant.
        The user's question: "{user_input}" needs more details to provide accurate information.
        Use previous conversation context:
        {context_text if context_text else 'None'}

        Ask politely for missing details:
        - Agency/company name
        - Location (city/country)
        - Specific information they want

        Use Arabic if user input is Arabic, otherwise English.
        Keep it concise (2-3 sentences) and friendly.
        Give a simple example of a clearer question.
        """
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You help users clarify their Hajj agency queries."},
                    {"role": "user", "content": prompt}
                ],
                response_format=NEEDSInfoResponse,
                temperature=0.7
            )
            
            info_data = response.choices[0].message.parsed
            
            # ----------------------------
            # Update last company if extracted
            # ----------------------------
            if info_data.extracted_company:
                self.update_last_company(info_data.extracted_company)
            
            # ----------------------------
            # Store assistant reply
            # ----------------------------
            self.store_bot_reply(
                reply_text=info_data.needs_info,
                intent="NEEDS_INFO",
                extracted_company=info_data.extracted_company if hasattr(info_data, 'extracted_company') else None
            )
            
            return {
                "needs_info": info_data.needs_info,
                "suggestions": info_data.suggestions,
                "missing_info": info_data.missing_info,
                "sample_query": info_data.sample_query
            }
        
        except Exception as e:
            logger.error(f"More info prompt generation failed: {e}")
            fallback = {
                "needs_info": "عذراً، هل يمكنك تقديم المزيد من التفاصيل؟ 🤔" if is_arabic else "Could you provide more details? 🤔",
                "suggestions": ["هل شركة الهدى للحج معتمدة؟", "أريد التحقق من وكالات الحج في مكة"] if is_arabic else ["Is Al Huda Hajj Agency authorized?", "Show me authorized agencies in Makkah"],
                "missing_info": ["اسم الوكالة", "الموقع", "التفاصيل المحددة"] if is_arabic else ["agency name", "location", "specific details"],
                "sample_query": "هل شركة الهدى للحج معتمدة؟" if is_arabic else "Is Al Huda Hajj Agency authorized?"
            }
            self.store_bot_reply(reply_text=fallback["needs_info"], intent="NEEDS_INFO")
            return fallback
