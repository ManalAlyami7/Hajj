"""
Voice Processor Module - OPTIMIZED OPENAI VERSION (Streaming)
Drop-in replacement for your existing voice_processor.py
Uses OpenAI Whisper + GPT + TTS with streaming for 2x speed improvement
"""

import streamlit as st
from openai import AsyncOpenAI, OpenAI
import io
from typing import Dict, Optional, AsyncGenerator
import logging
import difflib
from sqlalchemy import text

import asyncio

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
    """
    Optimized Voice Processor with OpenAI streaming.
    Drop-in replacement with 2x performance improvement.
    """
    
    def __init__(self):
        """Initialize Voice Processor with OpenAI client, database, and LLM manager."""
        self.client = self._get_client()
        self.async_client = self._get_async_client()
        self.db = DatabaseManager()
        self.voice_llm = LLMManager()

    # --- Internal Methods -----------------------------------------------------
    @st.cache_resource
    def _get_client(_self):
        """Get cached OpenAI client (sync version for compatibility)."""
        api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("key")
        if not api_key:
            logger.error("OpenAI API key not found in Streamlit secrets.")
            st.error("⚠️ Please add your `OPENAI_API_KEY` to Streamlit secrets.")
            st.stop()
        return OpenAI(api_key=api_key)
    
    @st.cache_resource
    def _get_async_client(_self):
        """Get cached async OpenAI client for streaming."""
        api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("key")
        if not api_key:
            logger.error("OpenAI API key not found in Streamlit secrets.")
            st.error("⚠️ Please add your `OPENAI_API_KEY` to Streamlit secrets.")
            st.stop()
        return AsyncOpenAI(api_key=api_key)


    def get_agency_names(self):
        engine = self.db._create_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT agency_name_ar, agency_name_en FROM agencies"))
            names = [f"{ar} ({en})" if ar and en else ar or en for ar, en in result.fetchall()]
        return names
    
    def clean_transcript_with_db(self, raw_text, agency_names):
        # Normalize text for better matching
        text_lower = raw_text.lower()

        # Try to find partial matches (Arabic or English)
        matched_agency = None
        for name in agency_names:
            name_lower = name.lower()
            # Check if a substring of the correct name appears in the transcript
            if any(part in text_lower for part in name_lower.split()):
                matched_agency = name
                break

            # Or use fuzzy partial ratio
            similarity = difflib.SequenceMatcher(None, text_lower, name_lower).ratio()
            if similarity > 0.6:  # adjustable threshold
                matched_agency = name
                break

        # Construct system prompt with context
        if matched_agency:
            prompt = f"""
            Fix transcription errors in this Arabic-English sentence, 
            but keep this agency name exactly as written: "{matched_agency}".
            Text: {raw_text}
            """
        else:
            prompt = f"""
            Fix transcription errors in this Arabic-English sentence, especially for proper nouns and company names.
            Text: {raw_text}
            """

        response =  self.client.beta.chat.completions.parse(
            model="gpt-4-turbo",
            messages=[{"role": "user", "content": prompt}]
        )

        cleaned = response.choices[0].message.content.strip()

        # If we detected an existing agency, ensure it's in the final text
        if matched_agency and matched_agency.lower() not in cleaned.lower():
            cleaned += f" ({matched_agency})"

        return cleaned



    # --- Audio Transcription (OPTIMIZED) --------------------------------------
    def transcribe_audio(self, audio_bytes: bytes) -> Dict:
        """Transcribe recorded audio into text and detect language (OPTIMIZED)."""
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"
            logger.info("🎙️ Sending audio for transcription...")

            # Context prompt to guide Whisper transcription
            # This helps with domain-specific terms and reduces errors


            # OPTIMIZATION: Use text format instead of verbose_json (faster)
            # OPTIMIZATION: Set temperature to 0 for faster, deterministic results
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",  # FASTER than verbose_json
                temperature=0.0,  # More deterministic = faster
                language=None,  # Auto-detect language
                #prompt=context_prompt  # NEW: Contextual guidance for better accuracy
            )
            
            text = transcript if isinstance(transcript, str) else getattr(transcript, "text", "")
            
            # Auto-detect language from text
            language = "arabic" if any("\u0600" <= ch <= "\u06FF" for ch in text) else "english"
            
            # Fix common transcription errors for "Hajj" (keep as fallback)
            names = self.get_agency_names()

            corrected_text = self.clean_transcript_with_db(text, names)


           

            result = {
                "text": corrected_text.strip(),
                "language": language,
                "confidence": 1.0,
                "duration": 0  # Not available in text format
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
    # --- LLM Integration (SAME AS BEFORE) -------------------------------------
    def detect_voice_intent(self, user_input: str, language: str) -> Dict:
        """Detect the user's intent from spoken input."""
        return self.voice_llm.detect_intent(user_input, language)

    def generate_voice_greeting(self, user_input: str, language: str) -> Dict:
        """Generate a contextual voice greeting."""
        return self.voice_llm.generate_greeting(user_input, language)

    def generate_sql_response(self, user_input: str, language: str) -> Dict:
        """Generate an SQL query and its result for voice queries."""
        return self.voice_llm.generate_sql(user_input, language)

    def generate_general_response(self, user_input: str, language: str) -> Dict:
        """Generate a general conversational AI response."""
        return self.voice_llm.generate_general_answer(user_input, language)

    def generate_summary(self, user_input: str, language: str, row_count: int, sample_rows) -> Dict:
        """Summarize a piece of text."""
        return self.voice_llm.generate_summary(user_input, language, row_count, sample_rows)
    
    def ask_for_more_info(self, user_input: str, language: str) -> Dict:
        """Generate a request for more information from the user."""
        return self.voice_llm.ask_for_more_info(user_input, language)

    # --- Text-to-Speech (OPTIMIZED WITH CHUNKING) -----------------------------
    def text_to_speech(self, text: str, language: str = "en") -> Optional[bytes]:
        """
        Convert text to speech and return MP3 bytes (OPTIMIZED).
        For long text, consider using text_to_speech_chunked() instead.
        """
        if not text or not text.strip():
            logger.warning("⚠️ Empty text provided to TTS.")
            return None

        # Voice mapping based on language
        voice_map = {
            "ar": "onyx",   # Arabic - deep, formal tone
            "arabic": "onyx",
            "en": "alloy",  # English - neutral tone
            "english": "alloy",
            "ur": "alloy",
            "urdu": "alloy",
            "id": "alloy",
            "indonesian": "alloy",
            "tr": "alloy",
            "turkish": "alloy"
        }

        voice = voice_map.get(language, "alloy")

        try:
            # OPTIMIZATION: Use tts-1 instead of tts-1-hd (2x faster)
            # OPTIMIZATION: Increase speed to 1.1 (10% faster speech)
            response = self.client.audio.speech.create(
                model="tts-1",  # FASTER than tts-1-hd
                voice=voice,
                input=text.strip()[:4096],  # Limit to 4096 chars for speed
                speed=1.1,  # 10% faster speech
                response_format="mp3"
            )

            audio_bytes = response.read()
            logger.info(f"🔊 TTS generated for: '{text[:60]}...' (lang: {language})")
            return audio_bytes

        except Exception as e:
            logger.error(f"❌ TTS generation failed: {e}")
            return None
    
    # --- NEW: STREAMING TTS FOR LONG TEXT ------------------------------------
    def text_to_speech_chunked(self, text: str, language: str = "en") -> list[bytes]:
        """
        Convert long text to speech in chunks for faster perceived latency.
        Returns list of audio chunks that can be played sequentially.
        """
        if not text or not text.strip():
            return []
        
        # Split text into sentences
        import re
        sentences = re.split(r'(?<=[.!?])\s+', text.strip())
        
        audio_chunks = []
        current_chunk = ""
        
        voice_map = {
            "ar": "onyx", "arabic": "onyx",
            "en": "alloy", "english": "alloy",
            "ur": "alloy", "urdu": "alloy",
            "id": "alloy", "indonesian": "alloy",
            "tr": "alloy", "turkish": "alloy"
        }
        voice = voice_map.get(language, "alloy")
        
        try:
            for sentence in sentences:
                current_chunk += sentence + " "
                
                # Generate audio when chunk is big enough (40-150 chars)
                if len(current_chunk) >= 40:
                    response = self.client.audio.speech.create(
                        model="tts-1",
                        voice=voice,
                        input=current_chunk.strip(),
                        speed=1.1
                    )
                    audio_chunks.append(response.read())
                    current_chunk = ""
            
            # Generate remaining text
            if current_chunk.strip():
                response = self.client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=current_chunk.strip(),
                    speed=1.1
                )
                audio_chunks.append(response.read())
            
            return audio_chunks
            
        except Exception as e:
            logger.error(f"❌ Chunked TTS failed: {e}")
            return []
    
    # --- NEW: ASYNC STREAMING FOR MAXIMUM SPEED -------------------------------
    async def text_to_speech_stream_async(
        self, 
        text_generator: AsyncGenerator[str, None],
        language: str = "en"
    ) -> AsyncGenerator[bytes, None]:
        """
        Stream TTS generation as text is being generated by LLM.
        Use this with streaming LLM responses for minimum latency.
        
        Example:
            async for audio_chunk in processor.text_to_speech_stream_async(llm_stream):
                # Play audio_chunk immediately
        """
        voice_map = {
            "ar": "onyx", "arabic": "onyx",
            "en": "alloy", "english": "alloy",
            "ur": "alloy", "urdu": "alloy",
            "id": "alloy", "indonesian": "alloy",
            "tr": "alloy", "turkish": "alloy"
        }
        voice = voice_map.get(language, "alloy")
        
        accumulated_text = ""
        
        try:
            async for text_chunk in text_generator:
                accumulated_text += text_chunk
                
                # Generate audio at sentence boundaries
                if len(accumulated_text) >= 40 and text_chunk[-1] in '.!?\n':
                    response = await self.async_client.audio.speech.create(
                        model="tts-1",
                        voice=voice,
                        input=accumulated_text.strip(),
                        speed=1.1
                    )
                    
                    audio_bytes = await response.aread()
                    yield audio_bytes
                    accumulated_text = ""
            
            # Generate remaining text
            if accumulated_text.strip():
                response = await self.async_client.audio.speech.create(
                    model="tts-1",
                    voice=voice,
                    input=accumulated_text.strip(),
                    speed=1.1
                )
                audio_bytes = await response.aread()
                yield audio_bytes
                
        except Exception as e:
            logger.error(f"❌ Async streaming TTS failed: {e}")