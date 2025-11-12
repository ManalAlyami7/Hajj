"""
Voice Processor Module - OPTIMIZED OPENAI VERSION
"""

import streamlit as st
from openai import AsyncOpenAI, OpenAI
import io
from typing import Dict, Optional, AsyncGenerator
import logging
import re
from sqlalchemy import text
from num2words import num2words
from functools import lru_cache
from rapidfuzz import process, fuzz

from core.voice_models import (
    VoiceIntentClassification,
    VoiceResponse,
    DatabaseVoiceResponse
)
from core.database import DatabaseManager
from core.voice_llm import LLMManager

logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)


class VoiceQueryProcessor:
    """Handles agency name matching and query processing"""
    
    def __init__(self, db, voice_llm):
        self.db = db
        self.voice_llm = voice_llm
        self.client = self.voice_llm._get_client()

    @lru_cache(maxsize=1)
    def get_all_agency_names(self) -> list:
        """Get ALL 7000+ agency names (CACHED for performance)"""
        engine = self.db._create_engine()
        
        with engine.connect() as conn:
            result = conn.execute(
                text("SELECT hajj_company_ar, hajj_company_en FROM agencies")
            )
            
            names = []
            for ar, en in result.fetchall():
                if ar and ar.strip():
                    names.append(ar.strip())
                if en and en.strip() and en != ar:
                    names.append(en.strip())
            
            logger.info(f"📊 Cached {len(names)} agency names")
            return names

    def get_relevant_agencies_for_prompt(
        self, 
        conversation_context: list = None,
        limit: int = 15
    ) -> list:
        """Get strategic subset of agencies for Whisper prompt"""
        relevant_names = []
        
        # Strategy 1: Extract from conversation
        if conversation_context:
            all_agencies = self.get_all_agency_names()
            for msg in conversation_context[-3:]:
                if isinstance(msg, str):
                    for agency in all_agencies:
                        if agency.lower() in msg.lower():
                            if agency not in relevant_names:
                                relevant_names.append(agency)
                                if len(relevant_names) >= limit:
                                    return relevant_names
        
        # Strategy 2: Get top agencies
        top_agencies = self._get_top_agencies(limit=limit)
        for agency in top_agencies:
            if agency not in relevant_names:
                relevant_names.append(agency)
                if len(relevant_names) >= limit:
                    return relevant_names
        
        # Strategy 3: Random sample
        if len(relevant_names) < limit:
            import random
            all_names = self.get_all_agency_names()
            remaining = [n for n in all_names if n not in relevant_names]
            sample_size = min(limit - len(relevant_names), len(remaining))
            if sample_size > 0:
                relevant_names.extend(random.sample(remaining, sample_size))
        
        return relevant_names[:limit]

    def _get_top_agencies(self, limit: int = 20) -> list:
        """Get most popular/established agencies"""
        engine = self.db._create_engine()
        
        try:
            with engine.connect() as conn:
                result = conn.execute(text("""
                    SELECT hajj_company_en, hajj_company_ar 
                    FROM agencies 
                    ORDER BY id ASC 
                    LIMIT :limit
                """), {"limit": limit})
                
                names = []
                for en, ar in result.fetchall():
                    if en and en.strip():
                        names.append(en.strip())
                    if ar and ar.strip() and ar != en:
                        names.append(ar.strip())
                
                return names[:limit]
        except Exception as e:
            logger.warning(f"Could not fetch top agencies: {e}")
            return []

    def correct_transcript_large_scale(
    self, 
    raw_text: str,
    threshold: int = 85  # ✅ Balanced threshold
) -> str:
        """
        Optimized transcript correction that PRESERVES THE FULL QUERY.
        Handles partial agency names and transliteration variations.
        """
        all_agencies = self.get_all_agency_names()
        
        # Stage 0: Quick exact match
        agency_set = {name.lower(): name for name in all_agencies}
        raw_lower = raw_text.lower().strip()
        
        if raw_lower in agency_set:
            match = agency_set[raw_lower]
            logger.info(f"✅ Exact match (full text): {match}")
            return match
        
        # Stage 1: Check if ANY agency name appears as EXACT substring
        for agency in all_agencies:
            agency_lower = agency.lower()
            if agency_lower in raw_lower:
                import re
                pattern = r'\b' + re.escape(agency_lower) + r'\b'
                if re.search(pattern, raw_lower, re.IGNORECASE):
                    logger.info(f"✅ Exact substring match: {agency} (no correction needed)")
                    return raw_text
        
        # Stage 2: Extract potential agency name from query
        candidate = self._extract_agency_mention(raw_text)
        
        if not candidate or len(candidate) < 3:
            logger.info(f"ℹ️ No agency name detected in query")
            return raw_text
        
        # ✅ NEW: Stage 2.5 - Check for PARTIAL name matches
        # Many users say partial names like "Namaa al-Barakah" instead of full name
        # Match against agency name BEGINNINGS
        candidate_lower = candidate.lower()
        
        best_partial_match = None
        best_partial_score = 0
        
        for agency in all_agencies:
            agency_lower = agency.lower()
            agency_words = agency_lower.split()
            candidate_words = candidate_lower.split()
            
            # Check if candidate matches the BEGINNING of agency name
            if len(candidate_words) <= len(agency_words):
                # Compare word by word from the start
                match_count = 0
                for cw, aw in zip(candidate_words, agency_words):
                    # Use fuzzy matching for each word to handle "Namaa"/"Nama"/"Namma"
                    word_similarity = fuzz.ratio(cw, aw)
                    if word_similarity >= 80:  # Allow slight variations
                        match_count += 1
                
                # If most words match, it's likely this agency
                match_ratio = match_count / len(candidate_words) if candidate_words else 0
                
                if match_ratio >= 0.7:  # At least 70% of words match
                    # Calculate overall similarity
                    overall_score = fuzz.token_sort_ratio(candidate_lower, agency_lower)
                    
                    if overall_score > best_partial_score:
                        best_partial_score = overall_score
                        best_partial_match = agency
        
        if best_partial_match and best_partial_score >= 75:
            corrected = self._replace_agency_in_query(raw_text, candidate, best_partial_match)
            logger.info(f"✅ Partial name match: {best_partial_match} (score: {best_partial_score}) → replaced in context")
            return corrected
        
        # Stage 3: Standard fuzzy match on extracted candidate
        matches = process.extract(
            candidate,
            all_agencies,
            scorer=fuzz.token_sort_ratio,
            score_cutoff=threshold,
            limit=3
        )
        
        if matches:
            best_match = matches[0]
            matched_agency = best_match[0]
            match_score = best_match[1]
            
            # Check for ambiguity
            if len(matches) > 1:
                second_score = matches[1][1]
                if abs(match_score - second_score) < 5:
                    logger.warning(f"⚠️ Ambiguous match: {matched_agency} vs {matches[1][0]} - keeping original")
                    return raw_text
            
            # Verify word overlap
            candidate_words = set(candidate.lower().split())
            matched_words = set(matched_agency.lower().split())
            
            if len(candidate_words & matched_words) / len(candidate_words) < 0.4:
                logger.warning(f"⚠️ Low word overlap between '{candidate}' and '{matched_agency}' - keeping original")
                return raw_text
            
            corrected = self._replace_agency_in_query(raw_text, candidate, matched_agency)
            logger.info(f"✅ Fuzzy match: {matched_agency} (score: {match_score}) → replaced in context")
            return corrected
        
        # Stage 4: Try token_set_ratio (better for partial matches)
        matches = process.extract(
            candidate,
            all_agencies,
            scorer=fuzz.token_set_ratio,  # ✅ Better for subset matching
            score_cutoff=80,
            limit=1
        )
        
        if matches:
            matched_agency = matches[0][0]
            match_score = matches[0][1]
            
            corrected = self._replace_agency_in_query(raw_text, candidate, matched_agency)
            logger.info(f"✅ Token set match: {matched_agency} (score: {match_score}) → replaced in context")
            return corrected
        
        # No confident match found
        logger.info(f"ℹ️ No confident match found, returning original: {raw_text}")
        return raw_text

    def _replace_agency_in_query(self, original_query: str, extracted_part: str, corrected_name: str) -> str:
        """
        Replace the extracted agency mention with the corrected name in the original query.
        Preserves the rest of the query text.
        
        Example:
            original: "Is Al Raja Travels authorized?"
            extracted: "Al Raja Travels"
            corrected: "Al-Rajah Travels"
            result: "Is Al-Rajah Travels authorized?"
        """
        import re
        
        # Try exact replacement first (case-insensitive)
        pattern = re.compile(re.escape(extracted_part), re.IGNORECASE)
        result = pattern.sub(corrected_name, original_query, count=1)
        
        # If no replacement happened, try fuzzy word-by-word
        if result == original_query:
            # Split into words and find approximate position
            words = original_query.split()
            extracted_words = extracted_part.split()
            
            # Find best matching sequence
            for i in range(len(words) - len(extracted_words) + 1):
                window = ' '.join(words[i:i+len(extracted_words)])
                similarity = fuzz.ratio(window.lower(), extracted_part.lower())
                
                if similarity > 70:  # Found approximate match
                    # Replace this window
                    words[i:i+len(extracted_words)] = [corrected_name]
                    result = ' '.join(words)
                    break
        
        return result

    def _extract_agency_mention(self, text: str) -> str:
        """
        Extract likely agency name from query, preserving multi-word names.
        
        Examples:
            "Is Al Tayyar authorized?" → "Al Tayyar"
            "Check Royal Hajj Company for me" → "Royal Hajj Company"
            "مرخص شركة الحج المباركة" → "شركة الحج المباركة"
        """
        import re
        
        # Remove common query phrases
        noise_patterns = [
            r'\b(is|are|was|were|check|verify|find|show|tell me about|what about|give me)\b',
            r'\b(authorized|licensed|verified|approved|legitimate|registered)\b',
            r'\b(hajj|umrah|agency|company|operator|travel|travels|tourism)\b',
            r'\b(for me|please|thanks|thank you|kya|hai|mujhe|chahiye)\b',
            r'[?!.،؟]',
        ]
        
        cleaned = text
        for pattern in noise_patterns:
            cleaned = re.sub(pattern, ' ', cleaned, flags=re.IGNORECASE)
        
        # Clean up extra spaces
        cleaned = ' '.join(cleaned.split())
        
        # If result is reasonable, return it
        if 3 <= len(cleaned) <= 100 and cleaned.strip():
            return cleaned.strip()
        
        # Fallback: return original
        return text


class VoiceProcessor:
    """Optimized Voice Processor with OpenAI"""
    
    def __init__(self):
        self.client = self._get_client()
        self.async_client = self._get_async_client()
        self.db = DatabaseManager()
        self.voice_llm = LLMManager()

    @st.cache_resource
    def _get_client(_self):
        """Get cached OpenAI client"""
        api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("key")
        if not api_key:
            logger.error("OpenAI API key not found")
            st.error("⚠️ Please add your `OPENAI_API_KEY` to Streamlit secrets.")
            st.stop()
        return OpenAI(api_key=api_key)
    
    @st.cache_resource
    def _get_async_client(_self):
        """Get cached async OpenAI client"""
        api_key = st.secrets.get("OPENAI_API_KEY") or st.secrets.get("key")
        if not api_key:
            logger.error("OpenAI API key not found")
            st.error("⚠️ Please add your `OPENAI_API_KEY` to Streamlit secrets.")
            st.stop()
        return AsyncOpenAI(api_key=api_key)

    def _detect_language(self, text: str) -> str:
        """Enhanced language detection: Arabic, English, Urdu, mixed"""
        arabic_chars = sum(1 for ch in text if "\u0600" <= ch <= "\u06FF")
        urdu_specific = sum(1 for ch in text if ch in 'ٹڈڑںہھےۓپچژگ')
        latin_chars = sum(1 for ch in text if ch.isalpha() and ord(ch) < 128)
        total_alpha = len([ch for ch in text if ch.isalpha()])
        
        if total_alpha == 0:
            return "unknown"
        
        arabic_pct = arabic_chars / total_alpha
        latin_pct = latin_chars / total_alpha
        
        # Urdu detection
        if urdu_specific > 0 and arabic_pct > 0.3:
            return "urdu"
        
        if arabic_pct > 0.3:
            urdu_kw = self._contains_urdu_keywords(text)
            arabic_kw = self._contains_arabic_keywords(text)
            
            if urdu_kw and not arabic_kw:
                return "urdu"
            elif arabic_kw and not urdu_kw:
                return "arabic"
            elif urdu_kw and arabic_kw:
                return "urdu"
            else:
                return "arabic"
        
        if latin_pct > 0.8:
            if self._is_roman_urdu(text):
                return "roman_urdu"
            return "english"
        
        if arabic_pct > 0.2 and latin_pct > 0.2:
            return "mixed_urdu" if urdu_specific > 0 else "mixed_arabic"
        
        return "english"

    def _contains_urdu_keywords(self, text: str) -> bool:
        """Check for common Urdu words"""
        urdu_keywords = [
            'ہے', 'کا', 'کی', 'کے', 'میں', 'نے', 'کو', 'سے', 'پر', 'اور',
            'یا', 'کیا', 'کہ', 'تھا', 'تھی', 'گیا', 'آیا', 'ہوں', 'ہو',
            'چاہیے', 'لیے', 'بھی', 'ابھی', 'کیوں', 'کیسے', 'کہاں', 'کب'
        ]
        return any(kw in text.lower() for kw in urdu_keywords)

    def _contains_arabic_keywords(self, text: str) -> bool:
        """Check for common Arabic words"""
        arabic_keywords = [
            'في', 'من', 'إلى', 'على', 'هذا', 'هذه', 'الذي', 'التي',
            'كان', 'يكون', 'ليس', 'لا', 'نعم', 'كيف', 'أين', 'متى',
            'لماذا', 'ماذا', 'هل', 'قد', 'لقد'
        ]
        return any(kw in text.lower() for kw in arabic_keywords)

    def _is_roman_urdu(self, text: str) -> bool:
        """Detect Roman Urdu"""
        roman_urdu_patterns = [
            r'\bhai\b', r'\bhoon\b', r'\bho\b', r'\bka\b', r'\bki\b',
            r'\bke\b', r'\bmein\b', r'\bne\b', r'\bko\b', r'\bse\b',
            r'\bpar\b', r'\baur\b', r'\bkya\b', r'\bkeh\b', r'\btha\b',
            r'\bthi\b', r'\bgaya\b', r'\baya\b', r'\bchahiye\b', r'\bliye\b',
            r'\bbhi\b', r'\babhi\b', r'\bkyun\b', r'\bkaise\b', r'\bkahan\b',
            r'\bkab\b', r'\bmujhe\b', r'\btumhe\b', r'\bunhe\b', r'\bhamein\b',
            r'\bnahi\b'
        ]
        
        matches = sum(1 for pattern in roman_urdu_patterns if re.search(pattern, text.lower()))
        return matches >= 2

    def transcribe_audio(self, audio_bytes: bytes, conversation_context: list = None) -> Dict:
        """Transcribe audio with intelligent prompting"""
        try:
            audio_file = io.BytesIO(audio_bytes)
            audio_file.name = "audio.wav"
            logger.info("🎙️ Sending audio for transcription...")

            proc = VoiceQueryProcessor(self.db, self.voice_llm)
            relevant_agencies = proc.get_relevant_agencies_for_prompt(
                conversation_context=conversation_context,
                limit=15
            )
            
            context_prompt = self._build_whisper_prompt(
                agency_names=relevant_agencies,
                conversation_context=conversation_context
            )

            transcript = self.client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                response_format="text",
                temperature=0.0,
                language=None,
                prompt=context_prompt
            )
            
            text = transcript if isinstance(transcript, str) else getattr(transcript, "text", "")
            language = self._detect_language(text)
            
            # Post-processing correction
            cleaned_text = proc.correct_transcript_large_scale(
                raw_text=text,
                threshold=82
            )

            result = {
                "text": cleaned_text.strip(),
                "language": language,
                "confidence": 1.0,
                "duration": 0,
                "original_text": text
            }

            logger.info(f"🎙️ Transcribed: '{text[:60]}...' → '{cleaned_text[:60]}...'")
            return result

        except Exception as e:
            logger.error(f"❌ Transcription failed: {e}")
            return {"text": "", "language": "en", "confidence": 0.0, "error": str(e)}

    def _build_whisper_prompt(
        self, 
        agency_names: list,
        conversation_context: list = None,
        max_chars: int = 800
    ) -> str:
        """Build Whisper prompt with strategic agency subset"""
        domain_keywords = [
            "Hajj", "Umrah", "pilgrimage", "authorized", "licensed", "verified",
            "agency", "operator", "booking", "package", "visa", "registration",
            "Makkah", "Madinah", "Saudi Arabia"
        ]
        
        prompt_parts = []
        
        prompt_parts.append(
            "Hajj and Umrah agency verification query. "
            "User asking about pilgrimage agencies, authorization status, packages, or bookings."
        )
        
        if agency_names and len(agency_names) > 0:
            top_names = agency_names[:8]
            agency_str = ", ".join(top_names)
            prompt_parts.append(f"Example agencies: {agency_str}.")
        
        prompt_parts.append(f"Terms: {', '.join(domain_keywords[:10])}.")
        
        if conversation_context and len(conversation_context) > 0:
            last_msg = conversation_context[-1]
            if isinstance(last_msg, str) and len(last_msg) < 80:
                prompt_parts.append(f"Context: {last_msg[:70]}")
        
        prompt_parts.append("Languages: English, Arabic, Urdu.")
        
        full_prompt = " ".join(prompt_parts)
        
        if len(full_prompt) > max_chars:
            full_prompt = (
                f"Hajj agency query. Examples: {', '.join(agency_names[:5])}. "
                f"Terms: Hajj, Umrah, authorized, licensed, booking, visa."
            )
        
        return full_prompt

    def preprocess_phone_numbers(self, text: str) -> str:
        """Make phone numbers TTS-friendly"""
        phone_pattern = r'(\+?\d[\d\s\-]{6,20}\d)'

        def repl(match: re.Match):
            number = match.group(0)
            formatted = ''.join([c + ' ' if c.isdigit() else c for c in number])
            return formatted.strip()

        return re.sub(phone_pattern, repl, text)

    def text_to_speech(self, text: str, language: str = "en") -> bytes | None:
        """Convert text to speech"""
        if not text or not text.strip():
            logger.warning("⚠️ Empty text provided to TTS")
            return None

        voice_map = {
            "ar": "echo", "arabic": "echo",
            "en": "alloy", "english": "alloy",
            "ur": "alloy", "urdu": "alloy",
            "roman_urdu": "alloy", "mixed_urdu": "alloy", "mixed_arabic": "alloy"
        }
        voice = voice_map.get(language.lower(), "alloy")

        text = self.preprocess_phone_numbers(text)

        if language.lower() in ["ar", "arabic"]:
            def number_to_words(match: re.Match):
                if ' ' in match.group(0) or '+' in match.group(0):
                    return match.group(0)
                return num2words(int(match.group(0)), lang='ar')

            text = re.sub(r'\b\d+\b', number_to_words, text)
            speed = 1.0
        else:
            speed = 1.1

        try:
            response = self.client.audio.speech.create(
                model="tts-1",
                voice=voice,
                input=text.strip()[:4096],
                speed=speed,
                response_format="mp3"
            )
            audio_bytes = response.read()
            logger.info(f"🔊 TTS generated for: '{text[:60]}...'")
            return audio_bytes

        except Exception as e:
            logger.error(f"❌ TTS generation failed: {e}")
            return None