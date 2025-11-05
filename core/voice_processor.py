"""
Voice Processor Module - STREAMING VERSION
Handles real-time audio transcription, streaming responses, and live feedback
"""

import streamlit as st
from openai import OpenAI
import io
from typing import Dict, Optional, Generator
import logging
from core.voice_models import (
    VoiceIntentClassification,
    VoiceResponse,
    DatabaseVoiceResponse
)
from core.database import DatabaseManager

logger = logging.getLogger(__name__)


class StreamingVoiceProcessor:
    """Manages voice-specific AI operations with streaming support"""
    
    def __init__(self):
        """Initialize Voice Processor with OpenAI client"""
        self.client = self._get_client()
        self.db = DatabaseManager()
    
    @st.cache_resource
    def _get_client(_self):
        """Get cached OpenAI client"""
        api_key = st.secrets.get('key')
        if not api_key:
            logger.error("OpenAI API key not found")
            st.error("⚠️ Please add your OPENAI_API_KEY to Streamlit secrets")
            st.stop()
        return OpenAI(api_key=api_key)
    
    def transcribe_audio_streaming(self, audio_bytes: bytes) -> Dict:
        """
        Transcribe audio with immediate feedback
        Optimized for real-time display
        
        Args:
            audio_bytes: Raw audio data
        
        Returns:
            Dict with text, language, confidence
        """
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"

            # Use verbose_json for language detection
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                temperature=0  # More deterministic
            )

            text = transcript.text if hasattr(transcript, 'text') else ""
            language = getattr(transcript, "language", None)
            
            if not language:
                language = "ar" if any("\u0600" <= ch <= "\u06FF" for ch in text) else "en"

            result = {
                "text": text,
                "language": language,
                "confidence": 1.0,
                "duration": getattr(transcript, "duration", 0)
            }

            logger.info(f"Transcribed: '{result['text'][:50]}...' (lang: {result['language']})")
            return result

        except Exception as e:
            logger.error(f"Transcription failed: {e}")
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
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You classify voice intents with urgency assessment."},
                    {"role": "user", "content": intent_prompt}
                ],
                response_format=VoiceIntentClassification,
                temperature=0
            )
            
            intent_data = response.choices[0].message.parsed
            
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
    
    def generate_response_streaming(
        self, 
        user_input: str, 
        intent: str,
        is_arabic: bool = False,
        context: list = None
    ) -> Generator[str, None, None]:
        """
        Generate streaming response word-by-word
        
        Args:
            user_input: User's query
            intent: Detected intent
            is_arabic: Whether to respond in Arabic
            context: Conversation history
        
        Yields:
            Response chunks as they're generated
        """
        # Build system prompt based on intent
        if intent == "GREETING":
            system_prompt = self._build_greeting_prompt(is_arabic)
        elif intent == "DATABASE":
            system_prompt = self._build_database_prompt_streaming(user_input, is_arabic)
        else:
            system_prompt = self._build_general_prompt(is_arabic)
        
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            if context:
                messages.extend(context[-6:])
            
            messages.append({"role": "user", "content": user_input})
            
            # Stream the response
            stream = self.client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.7,
                stream=True
            )
            
            for chunk in stream:
                if chunk.choices[0].delta.content:
                    yield chunk.choices[0].delta.content
            
        except Exception as e:
            logger.error(f"Streaming response failed: {e}")
            yield "I apologize, but I encountered an error. Please try again."
    
    def _build_greeting_prompt(self, is_arabic: bool) -> str:
        """Build greeting system prompt"""
        return f"""You are a friendly Hajj voice assistant. Generate a warm greeting:
1. Acknowledge the greeting warmly
2. Offer help with Hajj agencies and questions
3. Keep it BRIEF for voice (2-3 sentences max)
4. Use natural speaking style
{'5. Respond in Arabic' if is_arabic else '5. Respond in English'}"""
    
    def _build_database_prompt_streaming(self, user_input: str, is_arabic: bool) -> str:
        """Build database query prompt with real-time context"""
        # Try to get database results
        actual_data = None
        try:
            sql_query = self._generate_sql_for_voice(user_input, is_arabic)
            if sql_query:
                df, error = self.db.execute_query(sql_query)
                if df is not None and not df.empty:
                    actual_data = df
                    logger.info(f"Found {len(df)} results from database")
        except Exception as e:
            logger.error(f"Database query failed: {e}")
        
        data_context = ""
        if actual_data is not None and not actual_data.empty:
            total = len(actual_data)
            authorized = len(actual_data[actual_data['is_authorized'] == 'Yes']) if 'is_authorized' in actual_data.columns else 0
            sample = actual_data.head(3).to_dict('records')
            
            data_context = f"""
ACTUAL DATABASE RESULTS FOUND:
- Total agencies found: {total}
- Authorized agencies: {authorized}
- Sample records: {sample}

IMPORTANT: Reference these ACTUAL results in your response!
"""
        else:
            data_context = "NO RESULTS FOUND in database. Guide user to rephrase or check spelling."
        
        return f"""You are a fraud-prevention voice assistant for Hajj pilgrims.

CRITICAL CONTEXT:
- 415 fake Hajj offices closed in 2025
- 269,000+ unauthorized pilgrims stopped

{data_context}

Generate a response that:
1. {'References the ACTUAL agencies found' if actual_data is not None else 'Explains no results were found'}
2. Provides clear verification steps
3. Issues warning about fake agencies
4. Keep it BRIEF for voice but COMPREHENSIVE
{'5. Respond in Arabic' if is_arabic else '5. Respond in English'}"""
    
    def _build_general_prompt(self, is_arabic: bool) -> str:
        """Build general Hajj information prompt"""
        return f"""You are a knowledgeable Hajj voice assistant. Help with:
- Hajj & Umrah rituals
- Travel requirements
- Health & safety guidelines

CRITICAL: Always emphasize using AUTHORIZED agencies.

Voice guidelines:
- Keep responses BRIEF (3-4 sentences for voice)
- Use clear, simple language
- Include key actions user should take
{'- Respond in Arabic' if is_arabic else '- Respond in English'}"""
    
    def _generate_sql_for_voice(self, user_input: str, is_arabic: bool) -> Optional[str]:
        """Generate SQL query from voice input using AI"""
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

LOCATION HANDLING:
- Use LIKE with % for fuzzy matching
- Include Arabic AND English variations

User voice input: {user_input}

Rules:
1. ONLY return SELECT queries
2. Use is_authorized = 'Yes' when asking about verified agencies
3. Use LOWER() for case-insensitive English text
4. Limit to 50 results
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
            
            sql = response.choices[0].message.content.strip()
            
            if sql.startswith("```"):
                sql = sql.split("```")[1]
                if sql.startswith("sql"):
                    sql = sql[3:]
            sql = sql.strip().rstrip(';')
            
            if sql == "NO_SQL" or not sql.upper().startswith("SELECT"):
                return None
            
            return self.db.sanitize_sql(sql)
            
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return None
    
    def text_to_speech_streaming(self, text: str, language: str = "en") -> Optional[bytes]:
        """
        Convert text to speech audio with optimized settings
        
        Args:
            text: Text to convert
            language: Language for voice selection
        
        Returns:
            Audio bytes or None if failed
        """
        if not text or not text.strip():
            logger.warning("Empty text provided to TTS")
            return None
        
        voice_map = {
            "ar": "onyx",
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
                input=text,
                speed=1.0
            )
            
            logger.info(f"TTS generated for: '{text[:50]}...'")
            return response.content
            
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return None