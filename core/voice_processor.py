"""
Voice Processor Module - PRODUCTION READY
Handles audio transcription, intent detection, and response generation for voice
"""

import streamlit as st
from openai import OpenAI
import openrouter
import io
from typing import Dict, Optional
import logging
from core.voice_models import (
    VoiceIntentClassification,
    VoiceResponse,
    DatabaseVoiceResponse
)
from core.database import DatabaseManager  # ADD THIS IMPORT

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """Manages voice-specific AI operations"""
    
    def __init__(self):
        """Initialize Voice Processor with OpenAI client"""
        self.client = self._get_client()
        self.db = DatabaseManager() # INITIALIZE DATABASE MANAGER
    
    @st.cache_resource
    def _get_client(_self):
        api_key = st.secrets.get('openrouter_key')  # new key
        if not api_key:
            logger.error("OpenRouter API key not found")
            st.error("⚠️ Please add your OPENROUTER_API_KEY to Streamlit secrets")
            st.stop()
        return openrouter.OpenRouterClient(api_key=api_key, base_url="https://openrouter.ai/api/v1")

    def _normalize_transcription(self, transcription) -> str:
        """Return a plain transcript string from various SDK return types."""
        try:
            # dict-like
            return transcription.text
            # if hasattr(transcription, "get"):
            #     return transcription.get("text") or transcription.get("transcript") or str(transcription)
            # # object with attribute .text
            # if hasattr(transcription, "text"):
            #     return transcription.text or str(transcription)
            # # fallback to string
            # return str(transcription)
        except Exception:
            return ""
    
    def transcribe_audio(self, audio_bytes: bytes) -> Dict:
        """
        Transcribe audio to text with language detection
        Returns a normalized dict (always dict => safe .get usage).
        
        Whisper API Response Formats:
        - "json": Returns object with .text attribute only
        - "verbose_json": Returns object with .text, .language, .duration, etc.
        
        Args:
            audio_bytes: Raw audio data
        
        Returns:
            Dict with text, language, confidence
        """
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"

            # Use verbose_json to get language detection
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"  # Provides language detection
            )
            text = transcript['text']  # extract manually


            # Extract text using normalization
            text = self._normalize_transcription(text)
            
            # Extract language if available (verbose_json provides this)
            language = getattr(transcript, "language", None)
            if not language:
                # Fallback: detect from text if it contains Arabic characters
                language = "ar" if any("\u0600" <= ch <= "\u06FF" for ch in text) else "en"

            result = {
                "text": text,
                "language": language,
                "confidence": 1.0  # Whisper doesn't provide confidence scores
            }

            logger.info(f"Transcribed: '{result['text'][:50]}...' (lang: {result['language']})")
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            import traceback
            logger.error(traceback.format_exc())
            return {
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "error": str(e)
            }
    
    def detect_voice_intent(self, user_input: str, language: str = "en") -> Dict:
        """
        Detect intent with urgency level for voice interactions
        
        Args:
            user_input: Transcribed user text
            language: Detected language
        
        Returns:
            Dict with intent, confidence, reasoning, urgency
        """
        # CRITICAL: Validate input before processing
        if not user_input or not user_input.strip():
            logger.warning("Empty user_input provided to detect_voice_intent")
            return {
                "intent": "GENERAL_HAJJ",
                "confidence": 0.0,
                "reasoning": "Empty input",
                "is_arabic": False,
                "urgency": "low"
            }
        
        intent_prompt = f"""
Classify this voice message into ONE category with confidence and urgency:

1️⃣ GREETING: greetings like hello, hi, salam, السلام عليكم, مرحبا
2️⃣ DATABASE: questions about Hajj agencies, authorization, company verification
3️⃣ GENERAL_HAJJ: general Hajj questions (rituals, requirements, documents)


Message: {user_input}

CRITICAL CONTEXT:
- 415 fake Hajj offices closed in 2025
- 269,000+ unauthorized pilgrims stopped
- Voice interaction requires quick, clear guidance

Assess:
- Intent category
- Confidence (0-1)
- Reasoning
- Is it Arabic?
- Urgency (low/medium/high) - HIGH if asking about agency verification

Provide structured classification.
"""
        
        try:
            response = self.client.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You classify voice intents with urgency assessment."},
                    {"role": "user", "content": intent_prompt}
                ],
                response_format=VoiceIntentClassification,
                temperature=0
            )
            
            intent_data = response['choices'][0]['message']['content']

            
            logger.info(f"Intent: {intent_data.intent} (confidence: {intent_data.confidence}, urgency: {intent_data.urgency})")
            
            return {
                "intent": intent_data.intent,
                "confidence": intent_data.confidence,
                "reasoning": intent_data.reasoning,
                "is_arabic": intent_data.is_arabic,
                "urgency": intent_data.urgency
            }
            
        except Exception as e:
            logger.error(f"Voice intent detection failed: {e}")
            return self._fallback_intent_detection(user_input)
    
    def _fallback_intent_detection(self, user_input: str) -> Dict:
        """Fallback intent detection using heuristics"""
        ui = user_input.lower()
        
        if any(g in ui for g in ["hello", "hi", "salam", "السلام", "مرحبا"]):
            intent = "GREETING"
            urgency = "low"
        elif any(k in ui for k in ["agency", "company", "authorized", "معتمد", "شركة", "وكالة", "verify"]):
            intent = "DATABASE"
            urgency = "high"
        else:
            intent = "GENERAL_HAJJ"
            urgency = "medium"
        
        return {
            "intent": intent,
            "confidence": 0.7,
            "reasoning": "Determined by keyword matching (fallback)",
            "is_arabic": any("\u0600" <= ch <= "\u06FF" for ch in user_input),
            "urgency": urgency
        }
    
    def generate_voice_greeting(self, user_input: str, is_arabic: bool = False) -> Dict:
        """
        Generate greeting response optimized for voice
        
        Args:
            user_input: User's greeting
            is_arabic: Whether to respond in Arabic
        
        Returns:
            Dict with response, tone, key_points, suggested_actions
        """
        system_prompt = f"""You are a friendly Hajj voice assistant. Generate a warm greeting:
1. Acknowledge the greeting warmly
2. Offer help with Hajj agencies and questions
3. Keep it BRIEF for voice (2-3 sentences max)
4. Use natural speaking style
{'5. Respond in Arabic' if is_arabic else '5. Respond in English'}

Also provide:
- Tone assessment
- Key points covered
- Suggested actions user can take"""
        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                response_format=VoiceResponse,
                temperature=0.7
            )
            
            voice_data = response.choices[0].message.parsed
            
            return {
                "response": voice_data.response,
                "tone": voice_data.tone,
                "key_points": voice_data.key_points,
                "suggested_actions": voice_data.suggested_actions,
                "includes_warning": voice_data.includes_warning
            }
            
        except Exception as e:
            logger.error(f"Voice greeting generation failed: {e}")
            return {
                "response": "السلام عليكم! 🌙 كيف يمكنني مساعدتك؟" if is_arabic else "Hello! 👋 How can I assist you today?",
                "tone": "warm",
                "key_points": ["Greeting", "Offer to help"],
                "suggested_actions": ["Ask about agencies", "Ask about Hajj requirements"],
                "includes_warning": False
            }
    
    def generate_database_response(self, user_input: str, is_arabic: bool = False) -> Dict:
        """
        Generate database/verification response for voice WITH REAL DATA
        
        Args:
            user_input: User's query about agencies
            is_arabic: Whether to respond in Arabic
        
        Returns:
            Dict with response, verification steps, warning, sources, and actual data
        """
        
        # STEP 1: Try to get actual database results
        actual_data = None
        sql_query = None
        
        try:
            # Generate SQL query using AI
            sql_query = self._generate_sql_for_voice(user_input, is_arabic)
            
            if sql_query:
                logger.info(f"Generated SQL: {sql_query}")
                df, error = self.db.execute_query(sql_query)
                
                if df is not None and not df.empty:
                    actual_data = df
                    logger.info(f"Found {len(df)} results from database")
                elif error:
                    logger.warning(f"SQL execution error: {error}")
        except Exception as e:
            logger.error(f"Database query failed: {e}")
        
        # STEP 2: Generate voice response with context from actual data
        system_prompt = self._build_database_prompt(user_input, is_arabic, actual_data)
        
        try:
            response = self.client.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                response_format=DatabaseVoiceResponse,
                temperature=0.5
            )
            
            db_data = response['choices'][0]['message']['content']
            
            result = {
                "response": db_data.response,
                "verification_steps": db_data.verification_steps,
                "warning_message": db_data.warning_message,
                "official_sources": db_data.official_sources,
                "tone": db_data.tone,
                "actual_data": actual_data,  # Include actual DataFrame
                "sql_query": sql_query
            }
            
            return result
            
        except Exception as e:
            logger.error(f"Database voice response failed: {e}")
            return self._fallback_database_response(is_arabic, actual_data)
    
    def _generate_sql_for_voice(self, user_input: str, is_arabic: bool) -> Optional[str]:
        """
        Generate SQL query from voice input using AI
        """
        sql_generation_prompt = f"""Generate SQL query for this voice request about Hajj agencies.

Database table 'agencies' columns:
- hajj_company_ar (Arabic name)
- hajj_company_en (English name)
- city
- country
- email
- contact_Info
- formatted_address
- rating_reviews
- is_authorized ('Yes' or 'No')
- google_maps_link
- link_valid 

LOCATION HANDLING:
- Use LIKE with % for fuzzy matching
- Include Arabic AND English variations
- Example for Mecca: (city LIKE '%مكة%' OR LOWER(city) LIKE '%mecca%' OR LOWER(city) LIKE '%makkah%')

User voice input: {user_input}

Rules:
1. ONLY return SELECT queries
2. Use is_authorized = 'Yes' when user asks about verified/authorized agencies
3. Use LOWER() for case-insensitive English text
4. Limit to 50 results unless specified
5. Return ONLY the SQL query, no explanation

If cannot generate safe SQL, return: NO_SQL"""

        try:
            response = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You are a SQL expert. Generate only SELECT queries."},
                    {"role": "user", "content": sql_generation_prompt}
                ],
                temperature=0
            )
            
            sql = response['choices'][0]['message']['content'].strip()
            
            # Clean SQL (remove markdown formatting if present)
            if sql.startswith("```"):
                sql = sql.split("```")[1]
                if sql.startswith("sql"):
                    sql = sql[3:]
            sql = sql.strip().rstrip(';')
            
            if sql == "NO_SQL" or not sql.upper().startswith("SELECT"):
                return None
            
            # Validate with database manager
            return self.db.sanitize_sql(sql)
            
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return None
    
    def _build_database_prompt(self, user_input: str, is_arabic: bool, actual_data) -> str:
        """Build system prompt with actual data context"""
        
        data_context = ""
        if actual_data is not None and not actual_data.empty:
            # Summarize actual results
            total = len(actual_data)
            authorized = len(actual_data[actual_data['is_authorized'] == 'Yes']) if 'is_authorized' in actual_data.columns else 0
            
            # Get sample records
            sample = actual_data.head(5).to_dict('records')
            
            data_context = f"""
ACTUAL DATABASE RESULTS FOUND:
- Total agencies found: {total}
- Authorized agencies: {authorized}
- Sample records: {sample}

IMPORTANT: Reference these ACTUAL results in your response!
"""
        else:
            data_context = """
NO RESULTS FOUND in database for this query.
User may need to:
1. Rephrase their question
2. Try different city/country names
3. Check spelling
"""
        
        base_prompt = f"""You are a fraud-prevention voice assistant for Hajj pilgrims.

CRITICAL CONTEXT:
- 415 fake Hajj offices closed in 2025
- 269,000+ unauthorized pilgrims stopped
- URGENT: User needs immediate verification guidance

{data_context}

Generate a voice response that:
1. {'References the ACTUAL agencies found' if actual_data is not None and not actual_data.empty else 'Explains no results were found'}
2. Provides clear verification steps (3-4 steps)
3. Issues strong warning about fake agencies
4. Lists official sources
5. Keep it BRIEF for voice but COMPREHENSIVE
{'6. Respond in Arabic' if is_arabic else '6. Respond in English'}

User query: {user_input}"""
        
        return base_prompt
    
    def _fallback_database_response(self, is_arabic: bool, actual_data=None) -> Dict:
        """Enhanced fallback with actual data if available"""
        
        # If we have data, include it in fallback
        if actual_data is not None and not actual_data.empty:
            count = len(actual_data)
            auth_count = len(actual_data[actual_data['is_authorized'] == 'Yes']) if 'is_authorized' in actual_data.columns else 0
            
            if is_arabic:
                response = f"وجدت {count} وكالة، منها {auth_count} معتمدة. تحقق من الترخيص قبل الحجز!"
            else:
                response = f"Found {count} agencies, {auth_count} are authorized. Verify authorization before booking!"
        else:
            if is_arabic:
                response = "تحذير هام! تم إغلاق 415 مكتب حج مزيف. تحقق من ترخيص الوكالة قبل الحجز."
            else:
                response = "⚠️ CRITICAL: 415 fake Hajj offices were closed. Always verify agency authorization before booking!"
        
        if is_arabic:
            return {
                "response": response,
                "verification_steps": [
                    "تحقق من قاعدة بيانات وزارة الحج",
                    "تأكد من موقع المكتب الفعلي",
                    "اقرأ التقييمات الموثوقة"
                ],
                "warning_message": "احجز فقط من خلال الوكالات المعتمدة!",
                "official_sources": ["وزارة الحج والعمرة"],
                "tone": "urgent",
                "actual_data": actual_data,
                "sql_query": None
            }
        else:
            return {
                "response": response,
                "verification_steps": [
                    "Check Ministry of Hajj official database",
                    "Verify physical office location",
                    "Read authentic reviews",
                    "Confirm authorization status"
                ],
                "warning_message": "Book ONLY through AUTHORIZED agencies!",
                "official_sources": ["Ministry of Hajj and Umrah"],
                "tone": "urgent",
                "actual_data": actual_data,
                "sql_query": None
            }
    def generate_general_response(self, user_input: str, is_arabic: bool = False, context: list = None) -> Dict:
        """
        Generate general Hajj information response for voice
        
        Args:
            user_input: User's question
            is_arabic: Whether to respond in Arabic
            context: Previous conversation context
        
        Returns:
            Dict with response and metadata
        """
        system_prompt = f"""You are a knowledgeable Hajj voice assistant. Help with:
- Hajj & Umrah rituals
- Travel requirements
- Health & safety guidelines

CRITICAL: Always emphasize using AUTHORIZED agencies.
Context: 415 fake offices closed, 269,000+ unauthorized pilgrims stopped in 2025.

Voice guidelines:
- Keep responses BRIEF (3-4 sentences for voice)
- Use clear, simple language
- Include key actions user should take
{'- Respond in Arabic' if is_arabic else '- Respond in English'}"""
        
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            if context:
                messages.extend(context[-6:])  # Last 6 messages for context
            
            messages.append({"role": "user", "content": user_input})
            
            response = self.client.beta.completions.parse(
                model="gpt-4o-mini",
                messages=messages,
                response_format=VoiceResponse,
                temperature=0.6
            )
            
            voice_data = response['choices'][0]['message']['content']
            
            return {
                "response": voice_data.response,
                "tone": voice_data.tone,
                "key_points": voice_data.key_points,
                "suggested_actions": voice_data.suggested_actions,
                "includes_warning": voice_data.includes_warning
            }
            
        except Exception as e:
            logger.error(f"General voice response failed: {e}")
            return {
                "response": "I can help you with Hajj and Umrah information. Please ask your question.",
                "tone": "warm",
                "key_points": [],
                "suggested_actions": [],
                "includes_warning": False
            }
    
    def text_to_speech(self, text: str, language: str = "en") -> Optional[bytes]:
        """
        Convert text to speech audio
        
        Args:
            text: Text to convert
            language: Language for voice selection
        
        Returns:
            Audio bytes or None if failed
        """
        # Validate input
        if not text or not text.strip():
            logger.warning("Empty text provided to TTS")
            return None
        
        # Voice mapping
        voice_map = {
            "ar": "onyx",  # Better for Arabic
            "en": "alloy",
            "ur": "alloy",
            "id": "alloy",
            "tr": "alloy"
        }
        
        voice = voice_map.get(language, "alloy")
        
        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text
            )
            audio_bytes = response['content']
            logger.info(f"TTS generated for: '{text[:50]}...'")
            return audio_bytes
            
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return None