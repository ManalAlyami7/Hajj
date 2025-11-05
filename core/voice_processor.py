"""
Voice Processor Module - PRODUCTION READY
Handles audio transcription, intent detection, and response generation for voice
"""

import streamlit as st
import io
import logging
import base64
import requests
from typing import Dict, Optional
from core.voice_models import (
    VoiceIntentClassification,
    VoiceResponse,
    DatabaseVoiceResponse
)
from core.database import DatabaseManager

logger = logging.getLogger(__name__)

class VoiceProcessor:
    """Manages voice-specific AI operations"""

    def __init__(self):
        """Initialize Voice Processor with OpenRouter client"""
        self.api_key = st.secrets.get('openrouter_key')
        if not self.api_key:
            logger.error("OpenRouter API key not found")
            st.error("⚠️ Please add your OPENROUTER_API_KEY to Streamlit secrets")
            st.stop()
        self.db = DatabaseManager()  # Initialize database manager

    # --------------------------
    # AUDIO TRANSCRIPTION
    # --------------------------
    def transcribe_audio(self, audio_bytes: bytes) -> Dict:
        """Transcribe audio using OpenRouter's transcription model"""
        try:
            base64_audio = base64.b64encode(audio_bytes).decode("utf-8")
            payload = {
                "model": "gemini-audio-transcribe",
                "input_audio": {
                    "data": base64_audio,
                    "format": "wav"
                }
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.post(
                "https://openrouter.ai/api/v1/audio/transcriptions",
                headers=headers,
                json=payload
            )
            result = response.json()
            text = result.get("text", "")
            language = "ar" if any("\u0600" <= ch <= "\u06FF" for ch in text) else "en"
            return {"text": text, "language": language, "confidence": 1.0}
        except Exception as e:
            logger.error(f"Transcription failed: {e}")
            return {"text": "", "language": "en", "confidence": 0.0, "error": str(e)}

    # --------------------------
    # VOICE INTENT DETECTION
    # --------------------------
    def detect_voice_intent(self, user_input: str, language: str = "en") -> Dict:
        """Detect intent with urgency for voice interactions"""
        if not user_input.strip():
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
- Urgency (low/medium/high)
"""

        try:
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "You classify voice intents with urgency assessment."},
                    {"role": "user", "content": intent_prompt}
                ],
                "temperature": 0
            }
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json"
            }
            response = requests.post(
                "https://openrouter.ai/api/v1/chat/completions",
                headers=headers,
                json=payload
            )
            data = response.json()
            content = data["choices"][0]["message"]["content"]

            # Assume model returns a dict-like JSON
            return {
                "intent": content.get("intent", "GENERAL_HAJJ"),
                "confidence": content.get("confidence", 0.7),
                "reasoning": content.get("reasoning", ""),
                "is_arabic": content.get("is_arabic", False),
                "urgency": content.get("urgency", "medium")
            }
        except Exception as e:
            logger.error(f"Voice intent detection failed: {e}")
            return self._fallback_intent_detection(user_input)

    def _fallback_intent_detection(self, user_input: str) -> Dict:
        """Fallback intent detection using keywords"""
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
            "reasoning": "Keyword-based fallback",
            "is_arabic": any("\u0600" <= ch <= "\u06FF" for ch in user_input),
            "urgency": urgency
        }

    # --------------------------
    # VOICE GREETING GENERATION
    # --------------------------
    def generate_voice_greeting(self, user_input: str, is_arabic: bool = False) -> Dict:
        """Generate a warm greeting for voice"""
        system_prompt = f"""You are a friendly Hajj voice assistant. Generate a brief greeting (2-3 sentences max).
Respond in {'Arabic' if is_arabic else 'English'}.
Provide tone, key points, and suggested actions."""
        try:
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                "temperature": 0.7
            }
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            content = response.json()["choices"][0]["message"]["content"]

            return {
                "response": content.get("response", "Hello! How can I help?"),
                "tone": content.get("tone", "warm"),
                "key_points": content.get("key_points", []),
                "suggested_actions": content.get("suggested_actions", []),
                "includes_warning": content.get("includes_warning", False)
            }
        except Exception as e:
            logger.error(f"Voice greeting generation failed: {e}")
            fallback = "السلام عليكم! 🌙 كيف يمكنني مساعدتك؟" if is_arabic else "Hello! 👋 How can I assist you today?"
            return {"response": fallback, "tone": "warm", "key_points": ["Greeting", "Offer help"], "suggested_actions": [], "includes_warning": False}

    # --------------------------
    # DATABASE RESPONSE
    # --------------------------
    def generate_database_response(self, user_input: str, is_arabic: bool = False) -> Dict:
        """Generate database-based response using real data"""
        actual_data = None
        sql_query = None

        try:
            sql_query = self._generate_sql_for_voice(user_input, is_arabic)
            if sql_query:
                df, error = self.db.execute_query(sql_query)
                if df is not None and not df.empty:
                    actual_data = df
        except Exception as e:
            logger.error(f"Database query failed: {e}")

        system_prompt = self._build_database_prompt(user_input, is_arabic, actual_data)
        try:
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                "temperature": 0.5
            }
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            content = response.json()["choices"][0]["message"]["content"]
            return {
                "response": content.get("response", ""),
                "verification_steps": content.get("verification_steps", []),
                "warning_message": content.get("warning_message", ""),
                "official_sources": content.get("official_sources", []),
                "tone": content.get("tone", "neutral"),
                "actual_data": actual_data,
                "sql_query": sql_query
            }
        except Exception as e:
            logger.error(f"Database voice response failed: {e}")
            return self._fallback_database_response(is_arabic, actual_data)

    def _generate_sql_for_voice(self, user_input: str, is_arabic: bool) -> Optional[str]:
        """Generate SQL query safely"""
        sql_prompt = f"""Generate safe SELECT SQL query for Hajj agencies based on voice input:
User input: {user_input}"""
        try:
            payload = {
                "model": "gpt-4o-mini",
                "messages": [
                    {"role": "system", "content": "Generate only SELECT queries."},
                    {"role": "user", "content": sql_prompt}
                ],
                "temperature": 0
            }
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            sql = response.json()["choices"][0]["message"]["content"].strip()
            if sql.upper().startswith("SELECT"):
                return self.db.sanitize_sql(sql)
            return None
        except Exception as e:
            logger.error(f"SQL generation failed: {e}")
            return None

    def _build_database_prompt(self, user_input: str, is_arabic: bool, actual_data) -> str:
        """Build database prompt including real results if available"""
        data_context = ""
        if actual_data is not None and not actual_data.empty:
            total = len(actual_data)
            authorized = len(actual_data[actual_data['is_authorized'] == 'Yes']) if 'is_authorized' in actual_data.columns else 0
            sample = actual_data.head(5).to_dict('records')
            data_context = f"""
ACTUAL DATABASE RESULTS:
- Total agencies found: {total}
- Authorized agencies: {authorized}
- Sample: {sample}
"""
        else:
            data_context = "NO RESULTS FOUND. Advise user to check spelling, city, or country names."

        base_prompt = f"""You are a fraud-prevention voice assistant for Hajj pilgrims.
{data_context}
Respond in {'Arabic' if is_arabic else 'English'}, keep it brief but comprehensive.
Provide verification steps, warnings, and official sources.
User query: {user_input}"""
        return base_prompt

    def _fallback_database_response(self, is_arabic: bool, actual_data=None) -> Dict:
        """Fallback response with or without actual data"""
        if actual_data is not None and not actual_data.empty:
            count = len(actual_data)
            auth_count = len(actual_data[actual_data['is_authorized'] == 'Yes']) if 'is_authorized' in actual_data.columns else 0
            response = f"وجدت {count} وكالة، منها {auth_count} معتمدة." if is_arabic else f"Found {count} agencies, {auth_count} authorized."
        else:
            response = "تحقق من الترخيص قبل الحجز!" if is_arabic else "Always verify authorization before booking!"
        return {
            "response": response,
            "verification_steps": ["Check Ministry of Hajj database", "Verify location", "Read authentic reviews"] if not is_arabic else ["تحقق من قاعدة بيانات وزارة الحج", "تأكد من موقع المكتب", "اقرأ التقييمات"],
            "warning_message": "احجز فقط من خلال الوكالات المعتمدة!" if is_arabic else "Book ONLY through AUTHORIZED agencies!",
            "official_sources": ["وزارة الحج والعمرة"] if is_arabic else ["Ministry of Hajj and Umrah"],
            "tone": "urgent",
            "actual_data": actual_data,
            "sql_query": None
        }

    # --------------------------
    # GENERAL Hajj RESPONSE
    # --------------------------
    def generate_general_response(self, user_input: str, is_arabic: bool = False, context: list = None) -> Dict:
        """General Hajj info response"""
        system_prompt = f"""You are a knowledgeable Hajj voice assistant.
- Hajj & Umrah rituals
- Travel requirements
- Health & safety guidelines
Respond in {'Arabic' if is_arabic else 'English'}, brief 3-4 sentences, clear instructions."""

        try:
            messages = [{"role": "system", "content": system_prompt}]
            if context:
                messages.extend(context[-6:])
            messages.append({"role": "user", "content": user_input})
            payload = {"model": "gpt-4o-mini", "messages": messages, "temperature": 0.6}
            headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
            response = requests.post("https://openrouter.ai/api/v1/chat/completions", headers=headers, json=payload)
            content = response.json()["choices"][0]["message"]["content"]
            return {
                "response": content.get("response", ""),
                "tone": content.get("tone", "warm"),
                "key_points": content.get("key_points", []),
                "suggested_actions": content.get("suggested_actions", []),
                "includes_warning": content.get("includes_warning", False)
            }
        except Exception as e:
            logger.error(f"General response failed: {e}")
            fallback = "I can help you with Hajj and Umrah information. Please ask your question."
            return {"response": fallback, "tone": "warm", "key_points": [], "suggested_actions": [], "includes_warning": False}

    # --------------------------
    # TEXT TO SPEECH
    # --------------------------
    def text_to_speech(self, text: str, language: str = "en") -> Optional[bytes]:
        """Convert text to speech using OpenRouter TTS"""
        if not text.strip():
            return None
        voice_map = {"ar": "onyx", "en": "alloy"}
        voice = voice_map.get(language, "alloy")
        payload = {"model": "gemini-tts-basic", "voice": voice, "input_text": text}
        headers = {"Authorization": f"Bearer {self.api_key}", "Content-Type": "application/json"}
        try:
            response = requests.post("https://openrouter.ai/api/v1/audio/speech", headers=headers, json=payload)
            audio_base64 = response.json().get("audio_data")
            return base64.b64decode(audio_base64) if audio_base64 else None
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return None
