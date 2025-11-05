"""
Voice Processor Module - STREAMING VERSION
Handles real-time audio transcription, streaming responses, and live feedback
Optional enhanced version - use this if you want streaming AI responses
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


class VoiceProcessor:
    """Enhanced Voice Processor with streaming support"""
    
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
    
    def transcribe_audio(self, audio_bytes: bytes) -> Dict:
        """
        Transcribe audio to text with language detection
        """
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"

            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json",
                temperature=0
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
        """Detect intent with urgency level"""
        if not user_input or not user_input.strip():
            logger.warning("Empty user_input provided")
            return {
                "intent": "GENERAL_HAJJ",
                "confidence": 0.0,
                "reasoning": "Empty input",
                "is_arabic": False,
                "urgency": "low"
            }
        
        intent_prompt = f"""
Classify this voice message into ONE category:

1️⃣ GREETING: greetings like hello, hi, salam, السلام عليكم, مرحبا
2️⃣ DATABASE: questions about Hajj agencies, authorization, company verification
3️⃣ GENERAL_HAJJ: general Hajj questions (rituals, requirements, documents)

Message: {user_input}

Provide structured classification with intent, confidence, reasoning, is_arabic, urgency.
"""
        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": "You classify voice intents."},
                    {"role": "user", "content": intent_prompt}
                ],
                response_format=VoiceIntentClassification,
                temperature=0
            )
            
            intent_data = response.choices[0].message.parsed
            
            return {
                "intent": intent_data.intent,
                "confidence": intent_data.confidence,
                "reasoning": intent_data.reasoning,
                "is_arabic": intent_data.is_arabic,
                "urgency": intent_data.urgency
            }
            
        except Exception as e:
            logger.error(f"Intent detection failed: {e}")
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
            "reasoning": "Keyword matching (fallback)",
            "is_arabic": any("\u0600" <= ch <= "\u06FF" for ch in user_input),
            "urgency": urgency
        }
    
    def generate_response_streaming(
        self, 
        user_input: str, 
        intent: str,
        is_arabic: bool = False
    ) -> Generator[str, None, None]:
        """
        Generate streaming response word-by-word (OPTIONAL - for advanced use)
        """
        system_prompt = self._build_prompt(intent, is_arabic)
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
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
    
    def _build_prompt(self, intent: str, is_arabic: bool) -> str:
        """Build system prompt based on intent"""
        if intent == "GREETING":
            return f"""You are a friendly Hajj voice assistant. Generate a warm greeting:
1. Acknowledge warmly
2. Offer help with Hajj agencies
3. Keep it BRIEF (2-3 sentences)
{'4. Respond in Arabic' if is_arabic else '4. Respond in English'}"""
        
        elif intent == "DATABASE":
            return f"""You are a fraud-prevention voice assistant for Hajj pilgrims.
CRITICAL: 415 fake offices closed in 2025, 269,000+ unauthorized pilgrims stopped.
Provide clear verification guidance.
{'Respond in Arabic' if is_arabic else 'Respond in English'}"""
        
        else:
            return f"""You are a knowledgeable Hajj voice assistant.
Help with: Hajj & Umrah rituals, travel requirements, health guidelines.
ALWAYS emphasize using AUTHORIZED agencies.
{'Respond in Arabic' if is_arabic else 'Respond in English'}"""
    
    def generate_voice_greeting(self, user_input: str, is_arabic: bool = False) -> Dict:
        """Generate greeting response"""
        system_prompt = self._build_prompt("GREETING", is_arabic)
        
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
            logger.error(f"Greeting generation failed: {e}")
            return {
                "response": "السلام عليكم! كيف يمكنني مساعدتك؟" if is_arabic else "Hello! How can I assist you?",
                "tone": "warm",
                "key_points": ["Greeting"],
                "suggested_actions": ["Ask about agencies"],
                "includes_warning": False
            }
    
    def generate_database_response(self, user_input: str, is_arabic: bool = False) -> Dict:
        """Generate database/verification response"""
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": self._build_prompt("DATABASE", is_arabic)},
                    {"role": "user", "content": user_input}
                ],
                response_format=DatabaseVoiceResponse,
                temperature=0.5
            )
            
            db_data = response.choices[0].message.parsed
            
            return {
                "response": db_data.response,
                "verification_steps": db_data.verification_steps,
                "warning_message": db_data.warning_message,
                "official_sources": db_data.official_sources,
                "tone": db_data.tone
            }
            
        except Exception as e:
            logger.error(f"Database response failed: {e}")
            if is_arabic:
                return {
                    "response": "تحذير! تحقق من ترخيص الوكالة قبل الحجز.",
                    "verification_steps": ["تحقق من قاعدة بيانات وزارة الحج"],
                    "warning_message": "احجز فقط من خلال الوكالات المعتمدة!",
                    "official_sources": ["وزارة الحج والعمرة"],
                    "tone": "urgent"
                }
            else:
                return {
                    "response": "⚠️ CRITICAL: Always verify agency authorization before booking!",
                    "verification_steps": ["Check Ministry of Hajj database"],
                    "warning_message": "Book ONLY through AUTHORIZED agencies!",
                    "official_sources": ["Ministry of Hajj and Umrah"],
                    "tone": "urgent"
                }
    
    def generate_general_response(self, user_input: str, is_arabic: bool = False, context: list = None) -> Dict:
        """Generate general Hajj information response"""
        system_prompt = self._build_prompt("GENERAL_HAJJ", is_arabic)
        
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            if context:
                messages.extend(context[-6:])
            
            messages.append({"role": "user", "content": user_input})
            
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=messages,
                response_format=VoiceResponse,
                temperature=0.6
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
            logger.error(f"General response failed: {e}")
            return {
                "response": "I can help you with Hajj information. Please ask your question.",
                "tone": "warm",
                "key_points": [],
                "suggested_actions": [],
                "includes_warning": False
            }
    
    def text_to_speech(self, text: str, language: str = "en") -> Optional[bytes]:
        """Convert text to speech audio"""
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