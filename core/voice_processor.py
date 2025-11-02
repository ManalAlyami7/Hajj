"""
Voice Processor Module
Handles audio transcription, intent detection, and response generation for voice
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

logger = logging.getLogger(__name__)


class VoiceProcessor:
    """Manages voice-specific AI operations"""
    
    def __init__(self):
        """Initialize Voice Processor with OpenAI client"""
        self.client = self._get_client()
    
    @st.cache_resource
    def _get_client(_self):
        """Get cached OpenAI client"""
        api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("key")
        if not api_key:
            logger.error("OpenAI API key not found")
            st.error("⚠️ Please add your OPENAI_API_KEY to Streamlit secrets")
            st.stop()
        return OpenAI(api_key=api_key)
    
    def transcribe_audio(self, audio_bytes: bytes) -> Dict:
        """
        Transcribe audio to text with language detection
        
        Args:
            audio_bytes: Raw audio data
        
        Returns:
            Dict with text, language, confidence
        """
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"
            
            # Transcribe with verbose output for language detection
            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="verbose_json"
            )
            
            result = {
                "text": transcript.text,
                "language": getattr(transcript, 'language', 'en'),
                "confidence": 1.0  # Whisper doesn't provide confidence
            }
            
            logger.info(f"Transcribed: '{result['text']}' (lang: {result['language']})")
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
        Generate database/verification response for voice
        
        Args:
            user_input: User's query about agencies
            is_arabic: Whether to respond in Arabic
        
        Returns:
            Dict with response, verification steps, warning, sources
        """
        system_prompt = f"""You are a fraud-prevention voice assistant for Hajj pilgrims.

CRITICAL CONTEXT:
- 415 fake Hajj offices closed in 2025
- 269,000+ unauthorized pilgrims stopped
- URGENT: User needs immediate verification guidance

Generate a voice response that:
1. Acknowledges their query
2. Provides clear verification steps (3-4 steps)
3. Issues strong warning about fake agencies
4. Lists official sources
5. Keep it BRIEF for voice but COMPREHENSIVE
{'6. Respond in Arabic' if is_arabic else '6. Respond in English'}

User query: {user_input}"""
        
        try:
            response = self.client.beta.chat.completions.parse(
                model="gpt-4o-mini",
                messages=[
                    {"role": "system", "content": system_prompt},
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
            logger.error(f"Database voice response failed: {e}")
            return self._fallback_database_response(is_arabic)
    
    def _fallback_database_response(self, is_arabic: bool) -> Dict:
        """Fallback database response"""
        if is_arabic:
            return {
                "response": "تحذير هام! تم إغلاق 415 مكتب حج مزيف. تحقق من ترخيص الوكالة قبل الحجز.",
                "verification_steps": [
                    "تحقق من قاعدة بيانات وزارة الحج",
                    "تأكد من موقع المكتب الفعلي",
                    "اقرأ التقييمات الموثوقة"
                ],
                "warning_message": "احجز فقط من خلال الوكالات المعتمدة!",
                "official_sources": ["وزارة الحج والعمرة"],
                "tone": "urgent"
            }
        else:
            return {
                "response": "⚠️ CRITICAL: 415 fake Hajj offices were closed. Always verify agency authorization before booking!",
                "verification_steps": [
                    "Check Ministry of Hajj official database",
                    "Verify physical office location",
                    "Read authentic reviews",
                    "Confirm authorization status"
                ],
                "warning_message": "Book ONLY through AUTHORIZED agencies!",
                "official_sources": ["Ministry of Hajj and Umrah"],
                "tone": "urgent"
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
            
            logger.info(f"TTS generated for: '{text[:50]}...'")
            return response.content
            
        except Exception as e:
            logger.error(f"TTS failed: {e}")
            return None
