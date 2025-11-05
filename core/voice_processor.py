"""
Voice Processor Module - NO STREAMING VERSION
Handles audio transcription and AI responses without streaming.
Clean, simple, and production-ready.
"""

import streamlit as st
from openai import OpenAI
import io
from typing import Dict, Optional
import logging

from core.voice_models import (
    VoiceIntentClassification,
    VoiceResponse,
    DatabaseVoiceResponse
)
from core.database import DatabaseManager
from core.llm import LLMManager

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class VoiceProcessor:
    """Processes recorded audio and interacts with LLM + Database (non-streaming)."""
    
    def __init__(self):
        """Initialize Voice Processor with OpenAI client, database, and LLM manager."""
        self.client = self._get_client()
        self.db = DatabaseManager()
        self.llm = LLMManager()

    # --- Internal Methods -----------------------------------------------------
    @st.cache_resource
    def _get_client(_self):
        """Get cached OpenAI client safely from Streamlit secrets."""
        api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("key")
        if not api_key:
            logger.error("OpenAI API key not found in Streamlit secrets.")
            st.error("⚠️ Please add your `OPENAI_API_KEY` to Streamlit secrets.")
            st.stop()
        return OpenAI(api_key=api_key)

    # --- Audio Transcription --------------------------------------------------
    def transcribe_audio(self, audio_bytes: bytes) -> Dict:
        """Transcribe recorded audio into text and detect language."""
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"

            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                temperature=0
            )

            text = getattr(transcript, "text", "") or ""
            language = getattr(transcript, "language", None)

            # Auto-detect Arabic if language is missing
            if not language:
                language = "ar" if any("\u0600" <= ch <= "\u06FF" for ch in text) else "en"

            result = {
                "text": text.strip(),
                "language": language,
                "confidence": 1.0,
                "duration": getattr(transcript, "duration", 0)
            }

            logger.info(f"🎙️ Transcribed: '{text[:60]}...' (lang: {language})")
            return result

        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            return {
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "error": str(e)
            }

    # --- LLM Integration ------------------------------------------------------
    def detect_voice_intent(self, user_input: str, language: str) -> Dict:
        """Detect the user’s intent from spoken input."""
        return self.llm.detect_intent(user_input, language)

    def generate_voice_greeting(self, user_input: str, language: str) -> Dict:
        """Generate a contextual voice greeting."""
        return self.llm.generate_greeting(user_input, language)

    def generate_sql_response(self, user_input: str, language: str) -> Dict:
        """Generate an SQL query and its result for voice queries."""
        return self.llm.generate_sql(user_input, language)

    def generate_general_response(self, user_input: str, language: str) -> Dict:
        """Generate a general conversational AI response."""
        return self.llm.generate_general_answer(user_input, language)


    def generate_summary(self, user_input: str, language: str, row_count: int, sample_rows) -> Dict:
        """Summarize a piece of text."""
        return self.llm.generate_summary(user_input, language, row_count, sample_rows)

    # --- Text-to-Speech -------------------------------------------------------
    def text_to_speech(self, text: str, language: str = "en") -> Optional[bytes]:
        """Convert text to speech and return MP3 bytes."""
        if not text or not text.strip():
            logger.warning("⚠️ Empty text provided to TTS.")
            return None

        # Voice mapping based on language
        voice_map = {
            "ar": "onyx",   # Arabic - deep, formal tone
            "en": "alloy",  # English - neutral tone
            "ur": "alloy",
            "id": "alloy",
            "tr": "alloy"
        }

        voice = voice_map.get(language, "alloy")

        try:
            response = self.client.audio.speech.create(
                model="gpt-4o-mini-tts",  # Better quality + faster response
                voice=voice,
                input=text.strip(),
                speed=1.0
            )

            audio_bytes = response.read()
            logger.info(f"🔊 TTS generated for: '{text[:60]}...' (lang: {language})")
            return audio_bytes

        except Exception as e:
            logger.error(f"❌ TTS generation failed: {e}")
            return None
