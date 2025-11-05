"""
Voice Processor Module - OPENROUTER VERSION
Uses OpenRouter for AI models (Claude, GPT, Gemini, etc.)
Supports OpenAI for Whisper (transcription) and TTS
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
    """Voice Processor with OpenRouter for AI and OpenAI for audio"""
    
    def __init__(self):
        """Initialize with OpenRouter and OpenAI clients"""
        self.openrouter_client = self._get_openrouter_client()
        self.openai_client = self._get_openai_client()
        self.db = DatabaseManager()
        
        # Default model (can be changed)
        self.model = "anthropic/claude-3.5-sonnet"  # Or any OpenRouter model
    
    @st.cache_resource
    def _get_openrouter_client(_self):
        """Get cached OpenRouter client"""
        api_key = st.secrets.get('openrouter_key')
        if not api_key:
            logger.error("OpenRouter API key not found")
            st.error("⚠️ Please add your openrouter_key to Streamlit secrets")
            st.stop()
        
        # OpenRouter uses OpenAI-compatible API
        return OpenAI(
            base_url="https://openrouter.ai/api/v1",
            api_key=api_key,
        )
    
    @st.cache_resource
    def _get_openai_client(_self):
        """Get cached OpenAI client for Whisper and TTS"""
        api_key = st.secrets.get('key')  # Your OpenAI key
        if not api_key:
            logger.warning("OpenAI API key not found - Whisper/TTS disabled")
            return None
        return OpenAI(api_key=api_key)
    
    def transcribe_audio(self, audio_bytes: bytes) -> Dict:
        """Transcribe audio using OpenAI Whisper"""
        if not self.openai_client:
            return {
                "text": "",
                "language": "en",
                "confidence": 0.0,
                "error": "OpenAI client not configured"
            }
        
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"

            transcript = self.openai_client.audio.transcriptions.create(
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
        """Detect intent using OpenRouter model"""
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

Respond with a JSON object containing:
- intent: one of ["GREETING", "DATABASE", "GENERAL_HAJJ"]
- confidence: float between 0 and 1
- reasoning: brief explanation
- is_arabic: boolean
- urgency: one of ["low", "medium", "high"]
"""
        
        try:
            response = self.openrouter_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": "You classify voice intents. Return only valid JSON."},
                    {"role": "user", "content": intent_prompt}
                ],
                temperature=0,
                response_format={"type": "json_object"}
            )
            
            import json
            intent_data = json.loads(response.choices[0].message.content)
            
            return {
                "intent": intent_data.get("intent", "GENERAL_HAJJ"),
                "confidence": float(intent_data.get("confidence", 0.7)),
                "reasoning": intent_data.get("reasoning", ""),
                "is_arabic": intent_data.get("is_arabic", False),
                "urgency": intent_data.get("urgency", "medium")
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
        Generate streaming response using OpenRouter (TRUE STREAMING)
        This returns a generator that yields text chunks in real-time
        """
        system_prompt = self._build_prompt(intent, is_arabic)
        
        try:
            messages = [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_input}
            ]
            
            # Stream from OpenRouter
            stream = self.openrouter_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.7,
                stream=True  # Enable streaming
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
        """Generate greeting response using OpenRouter"""
        system_prompt = self._build_prompt("GREETING", is_arabic)
        
        try:
            response = self.openrouter_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.7
            )
            
            response_text = response.choices[0].message.content
            
            return {
                "response": response_text,
                "tone": "warm",
                "key_points": ["Greeting"],
                "suggested_actions": ["Ask about agencies", "Ask about Hajj"],
                "includes_warning": False
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
        """Generate database/verification response using OpenRouter"""
        system_prompt = self._build_prompt("DATABASE", is_arabic)
        
        try:
            response = self.openrouter_client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_input}
                ],
                temperature=0.5
            )
            
            response_text = response.choices[0].message.content
            
            return {
                "response": response_text,
                "verification_steps": [
                    "Check official Ministry database",
                    "Verify physical office location",
                    "Read authentic reviews"
                ],
                "warning_message": "Book ONLY through AUTHORIZED agencies!",
                "official_sources": ["Ministry of Hajj and Umrah"],
                "tone": "urgent"
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
                    "response": "⚠️ CRITICAL: Always verify agency authorization!",
                    "verification_steps": ["Check Ministry database"],
                    "warning_message": "Book ONLY through AUTHORIZED agencies!",
                    "official_sources": ["Ministry of Hajj"],
                    "tone": "urgent"
                }
    
    def generate_general_response(self, user_input: str, is_arabic: bool = False, context: list = None) -> Dict:
        """Generate general Hajj information response using OpenRouter"""
        system_prompt = self._build_prompt("GENERAL_HAJJ", is_arabic)
        
        try:
            messages = [{"role": "system", "content": system_prompt}]
            
            if context:
                messages.extend(context[-6:])
            
            messages.append({"role": "user", "content": user_input})
            
            response = self.openrouter_client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=0.6
            )
            
            response_text = response.choices[0].message.content
            
            return {
                "response": response_text,
                "tone": "informative",
                "key_points": ["Hajj information"],
                "suggested_actions": ["Ask follow-up questions"],
                "includes_warning": "authorized" in response_text.lower()
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
        """Convert text to speech using OpenAI TTS"""
        if not self.openai_client:
            logger.warning("OpenAI client not configured - TTS disabled")
            return None
        
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
            response = self.openai_client.audio.speech.create(
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
    
    def set_model(self, model_name: str):
        """Change the OpenRouter model"""
        self.model = model_name
        logger.info(f"Model changed to: {model_name}")