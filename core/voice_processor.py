"""
Voice Processor Module - UPGRADED WITH DEEPGRAM + ELEVENLABS
Handles audio transcription and AI responses with faster services.
Production-ready with better performance.
"""

import streamlit as st
from deepgram import DeepgramClient, PrerecordedOptions
from elevenlabs.client import ElevenLabs
from elevenlabs import VoiceSettings
import io
from typing import Dict, Optional
import logging

from core.voice_models import (
    VoiceIntentClassification,
    VoiceResponse,
    DatabaseVoiceResponse
)
from core.database import DatabaseManager
from core.voice_llm import LLMManager

# Configure logging
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class VoiceProcessor:
    """Processes recorded audio and interacts with LLM + Database with Deepgram & ElevenLabs."""
    
    def __init__(self):
        """Initialize Voice Processor with Deepgram, ElevenLabs, database, and LLM manager."""
        self.deepgram_client = self._get_deepgram_client()
        self.elevenlabs_client = self._get_elevenlabs_client()
        self.db = DatabaseManager()
        self.llm = LLMManager()

    # --- Internal Methods -----------------------------------------------------
    @st.cache_resource
    def _get_deepgram_client(_self):
        """Get cached Deepgram client from Streamlit secrets."""
        api_key = st.secrets.get("DEEPGRAM_API_KEY")
        if not api_key:
            logger.error("Deepgram API key not found in Streamlit secrets.")
            st.error("⚠️ Please add your `DEEPGRAM_API_KEY` to Streamlit secrets.")
            st.stop()
        return DeepgramClient(api_key)

    @st.cache_resource
    def _get_elevenlabs_client(_self):
        """Get cached ElevenLabs client from Streamlit secrets."""
        api_key = st.secrets.get("ELEVENLABS_API_KEY")
        if not api_key:
            logger.error("ElevenLabs API key not found in Streamlit secrets.")
            st.error("⚠️ Please add your `ELEVENLABS_API_KEY` to Streamlit secrets.")
            st.stop()
        return ElevenLabs(api_key=api_key)

    # --- Audio Transcription --------------------------------------------------
    def transcribe_audio(self, audio_bytes: bytes) -> Dict:
        """Transcribe recorded audio into text using Deepgram (much faster than Whisper)."""
        try:
            logger.info("🎙️ Sending audio to Deepgram for transcription...")

            # Configure Deepgram options for best accuracy and speed
            options = PrerecordedOptions(
                model="nova-2",  # Latest and fastest model
                language="multi",  # Auto-detect language (supports Arabic, English, etc.)
                smart_format=True,  # Auto-formatting
                detect_language=True,  # Language detection
                punctuate=True,
                diarize=False,
                utterances=False,
            )

            # Create payload with audio bytes
            payload = {"buffer": audio_bytes}

            # Transcribe audio
            response = self.deepgram_client.listen.prerecorded.v("1").transcribe_file(
                payload, options
            )

            # Extract results
            transcript_data = response.results.channels[0].alternatives[0]
            text = transcript_data.transcript or ""
            
            # Get detected language
            detected_language = None
            if response.results.channels[0].detected_language:
                detected_language = response.results.channels[0].detected_language
            
            # Map Deepgram language codes to your system
            language_map = {
                "ar": "arabic",
                "en": "english",
                "ur": "urdu",
                "id": "indonesian",
                "tr": "turkish"
            }
            
            language = language_map.get(detected_language, "english")
            
            # Auto-detect Arabic if language detection failed
            if not detected_language:
                language = "arabic" if any("\u0600" <= ch <= "\u06FF" for ch in text) else "english"

            # Replace words that sound like "Hajj" but transcribed incorrectly
            words_like_hajj = ['hatch', 'hatching', 'head', 'hadj', 'haj', 'hajji', 'haji', 'hajje', 'hajjeh']
            for word in words_like_hajj:
                text = text.replace(word, 'Hajj')
                text = text.replace(word.capitalize(), 'Hajj')

            # Get confidence and duration
            confidence = transcript_data.confidence or 0.0
            duration = response.metadata.duration or 0.0

            result = {
                "text": text.strip(),
                "language": language,
                "confidence": confidence,
                "duration": duration
            }

            logger.info(f"🎙️ Deepgram Transcribed: '{text[:60]}...' (lang: {language}, confidence: {confidence:.2f})")
            return result

        except Exception as e:
            logger.error(f"❌ Deepgram transcription failed: {e}")
            return {
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "error": str(e)
            }

    # --- LLM Integration ------------------------------------------------------
    def detect_voice_intent(self, user_input: str, language: str) -> Dict:
        """Detect the user's intent from spoken input."""
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

    def ask_for_more_info(self, user_input: str, language: str) -> Dict:
        """Generate a request for more information from the user."""
        return self.llm.ask_for_more_info(user_input, language)

    # --- Text-to-Speech -------------------------------------------------------
    def text_to_speech(self, text: str, language: str = "en") -> Optional[bytes]:
        """Convert text to speech using ElevenLabs (much faster and better quality)."""
        if not text or not text.strip():
            logger.warning("⚠️ Empty text provided to TTS.")
            return None

        # ElevenLabs voice mapping based on language
        # You can customize these voices from your ElevenLabs account
        voice_map = {
            "ar": "pNInz6obpgDQGcFmaJgB",  # Adam - good for Arabic
            "arabic": "pNInz6obpgDQGcFmaJgB",
            "en": "21m00Tcm4TlvDq8ikWAM",  # Rachel - clear English female
            "english": "21m00Tcm4TlvDq8ikWAM",
            "ur": "21m00Tcm4TlvDq8ikWAM",  # Rachel
            "urdu": "21m00Tcm4TlvDq8ikWAM",
            "id": "21m00Tcm4TlvDq8ikWAM",  # Rachel
            "indonesian": "21m00Tcm4TlvDq8ikWAM",
            "tr": "21m00Tcm4TlvDq8ikWAM",  # Rachel
            "turkish": "21m00Tcm4TlvDq8ikWAM",
        }

        voice_id = voice_map.get(language, "21m00Tcm4TlvDq8ikWAM")

        try:
            logger.info(f"🔊 Generating TTS with ElevenLabs for: '{text[:60]}...'")

            # Generate audio with ElevenLabs Turbo v2 (fastest model)
            audio_generator = self.elevenlabs_client.text_to_speech.convert(
                voice_id=voice_id,
                optimize_streaming_latency=4,  # Maximum optimization for speed
                output_format="mp3_44100_128",  # Good quality, fast
                text=text.strip(),
                model_id="eleven_turbo_v2_5",  # Fastest model
                voice_settings=VoiceSettings(
                    stability=0.5,
                    similarity_boost=0.75,
                    style=0.0,
                    use_speaker_boost=True
                )
            )

            # Collect audio bytes
            audio_bytes = b"".join(audio_generator)
            
            logger.info(f"🔊 ElevenLabs TTS generated successfully (lang: {language})")
            return audio_bytes

        except Exception as e:
            logger.error(f"❌ ElevenLabs TTS generation failed: {e}")
            return None