"""
Hajj Voice Assistant - BILINGUAL (cleaned)
Uses the existing translation system from utils.translations
"""
import time
import re
import logging
import hashlib
from pathlib import Path
import sys

import streamlit as st
from audio_recorder_streamlit import audio_recorder

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.voice_processor import VoiceProcessor
from utils.translations import t  # existing translation function

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# Language Detection / Session defaults
# ---------------------------
if 'language' not in st.session_state:
    # default to English code 'en' (use 'ar' for Arabic)
    st.session_state.language = 'en'

# convenience boolean for Arabic UI
def is_arabic_code(code):
    return code in ('ar', 'arabic', 'العربية')

# ---------------------------
# Streamlit Config
# ---------------------------
st.set_page_config(
    page_title=t('voice_page_title', st.session_state.language),
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------
# Styles (RTL support for Arabic)
# ---------------------------
lang_code = st.session_state.language
is_arabic = is_arabic_code(lang_code)

rtl_class = 'rtl' if is_arabic else ''
text_align = 'right' if is_arabic else 'left'
flex_direction = 'row-reverse' if is_arabic else 'row'
return_position = 'right: 20px;' if is_arabic else 'left: 20px;'
transform_direction = 'translateX(5px)' if is_arabic else 'translateX(-5px)'
icon_transform = 'translateX(3px)' if is_arabic else 'translateX(-3px)'
arrow_icon = '←' if not is_arabic else '→'

st.markdown(f"""
<style>
.stApp {{
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  background-attachment: fixed;
  overflow: hidden !important;
  height: 100vh;
}}
#MainMenu, footer, header {{visibility: hidden;}}
.main .block-container {{
  padding: 0.75rem 1rem;
  max-width: 1400px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  direction: {'rtl' if is_arabic else 'ltr'};
}}

/* Return Button Styles */
.return-button-container {{
  position: fixed;
  top: 20px;
  {return_position}
  z-index: 2000;
}}
.return-button {{
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.75rem 1.5rem;
  background: rgba(96, 165, 250, 0.15);
  backdrop-filter: blur(20px);
  border: 2px solid rgba(96, 165, 250, 0.3);
  border-radius: 1rem;
  color: #60a5fa;
  font-weight: 600;
  font-size: 0.95rem;
  text-decoration: none;
  transition: all 0.3s ease;
  box-shadow: 0 4px 20px rgba(96, 165, 250, 0.2);
  cursor: pointer;
  direction: {'rtl' if is_arabic else 'ltr'};
}}
.return-button:hover {{
  background: rgba(96, 165, 250, 0.25);
  border-color: rgba(96, 165, 250, 0.5);
  transform: {transform_direction};
  box-shadow: 0 6px 30px rgba(96, 165, 250, 0.4);
  color: #93c5fd;
}}
.return-button .icon {{
  font-size: 1.2rem;
  transition: transform 0.3s ease;
}}
.return-button:hover .icon {{
  transform: {icon_transform};
}}

.voice-header{{text-align:center;padding:0.75rem 0;margin-bottom:0.5rem;}}
.voice-title{{
  font-size:2.2rem;font-weight:800;letter-spacing:2px;
  background:linear-gradient(135deg,#60a5fa 0%,#a78bfa 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  margin-bottom:0.25rem;
}}
.voice-subtitle{{color:rgba(255,255,255,0.85);font-size:0.95rem;}}
.voice-container{{
  display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;
  flex:1;min-height:0;padding:0 1rem;
}}
.voice-left{{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  background:rgba(255,255,255,0.03);border-radius:2rem;padding:1.5rem;
  backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.08);
  box-shadow:0 8px 32px rgba(0,0,0,0.25);overflow:hidden;
}}
.voice-avatar{{width:180px;height:180px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;font-size:90px;
  background:linear-gradient(135deg,#60a5fa 0%,#a78bfa 100%);
  box-shadow:0 20px 60px rgba(96,165,250,0.35);
  border:6px solid rgba(255,255,255,0.15);
  animation:float 3s ease-in-out infinite;
}}
.voice-avatar.listening{{animation:pulse-listening 0.8s infinite;box-shadow:0 0 80px rgba(96,165,250,0.8);}}
.voice-avatar.speaking{{animation:pulse-speaking 0.6s infinite;box-shadow:0 0 80px rgba(167,139,250,0.8);}}
.voice-ring{{position:absolute;border:3px solid rgba(96,165,250,0.3);
  border-radius:50%;top:50%;left:50%;transform:translate(-50%,-50%);
  animation:expand 3s ease-out infinite;
}}
.voice-ring-1{{width:200px;height:200px;animation-delay:0s;}}
.voice-ring-2{{width:240px;height:240px;animation-delay:1s;}}
.voice-ring-3{{width:280px;height:280px;animation-delay:2s;}}
@keyframes float{{0%,100%{{transform:translateY(0);}}50%{{transform:translateY(-15px);}}}}
@keyframes pulse-listening{{0%,100%{{transform:scale(1);}}50%{{transform:scale(1.1);}}}}
@keyframes pulse-speaking{{0%,100%{{transform:scale(1);}}50%{{transform:scale(1.15);}}}}
@keyframes expand{{0%{{transform:translate(-50%,-50%) scale(0.8);opacity:0.8;}}100%{{transform:translate(-50%,-50%) scale(1.5);opacity:0;}}}}
.record-label{{margin-top:1rem;color:white;font-weight:600;text-transform:uppercase;letter-spacing:1.5px;}}
.voice-right{{display:flex;flex-direction:column;gap:1rem;height:100%;min-height:0;overflow:hidden;}}
.transcript-container,.response-container{{
  background:rgba(255,255,255,0.04);border-radius:1.5rem;padding:1.25rem;
  backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,0.08);
  box-shadow:0 8px 32px rgba(0,0,0,0.22);flex:1;min-height:0;
  display:flex;flex-direction:column;overflow:hidden;
}}
.panel-header{{display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;
  padding-bottom:0.75rem;border-bottom:2px solid rgba(255,255,255,0.08);
  flex-direction: {flex_direction};
}}
.panel-icon{{font-size:1.75rem;}}
.panel-title{{font-size:1.2rem;font-weight:700;color:white;margin:0;}}
.panel-badge{{margin-{'right' if is_arabic else 'left'}:auto;padding:0.3rem 0.8rem;border-radius:1rem;
  font-weight:600;font-size:0.75rem;background:rgba(96,165,250,0.16);
  color:#60a5fa;border:1px solid rgba(96,165,250,0.2);
}}
.panel-badge.active{{background:rgba(34,197,94,0.16);color:#22c55e;
  border-color:rgba(34,197,94,0.25);animation:badge-pulse 1s infinite;
}}
@keyframes badge-pulse{{0%,100%{{opacity:1;}}50%{{opacity:0.6;}}}}
.transcript-text,.response-content{{
  color:rgba(255,255,255,0.92);font-size:1.1rem;line-height:1.6;
  flex:1;overflow-y:auto;padding-{'left' if is_arabic else 'right'}:0.5rem;
  text-align:{text_align};
}}
.transcript-text.empty,.response-content.empty{{
  color:rgba(255,255,255,0.45);font-style:italic;overflow:hidden;
}}
.metadata-card{{background:rgba(255,255,255,0.03);border-radius:1rem;padding:0.9rem;
  margin-top:0.75rem;border-{'right' if is_arabic else 'left'}:4px solid #60a5fa;
  text-align:{text_align};
}}
.metadata-title{{font-size:0.85rem;font-weight:600;color:#60a5fa;
  margin-bottom:0.5rem;text-transform:uppercase;letter-spacing:1px;
}}
.metadata-list{{list-style:none;margin:0;padding:0;}}
.metadata-list li{{padding:0.25rem 0;color:rgba(255,255,255,0.85);}}
.metadata-list li:before{{content:"→ ";color:#60a5fa;font-weight:bold;margin-{'left' if is_arabic else 'right'}:0.5rem;}}
.status-indicator{{position:fixed;top:15px;{'left' if is_arabic else 'right'}:15px;
  padding:0.6rem 1.25rem;background:rgba(0,0,0,0.75);border-radius:2rem;
  color:white;font-weight:600;font-size:0.85rem;backdrop-filter:blur(10px);
  border:1px solid rgba(255,255,255,0.12);z-index:1000;
  display:flex;align-items:center;gap:0.5rem;
  direction: {'rtl' if is_arabic else 'ltr'};
}}
.status-dot{{width:10px;height:10px;border-radius:50%;background:#22c55e;animation:dot-pulse 1.5s infinite;}}
.status-dot.listening{{background:#ef4444;}}
.status-dot.speaking{{background:#a78bfa;}}
@keyframes dot-pulse{{0%,100%{{opacity:1;}}50%{{opacity:0.4;}}}}
@media (max-width:1024px){{
  .voice-container{{grid-template-columns:1fr;gap:1rem;}}
  .voice-avatar{{width:140px;height:140px;font-size:70px;}}
  .return-button-container {{top: 10px;{'right' if is_arabic else 'left'}: 10px;}}
  .return-button {{padding: 0.6rem 1.2rem;font-size: 0.85rem;}}
}}
audio {{display: none !important;visibility: hidden !important;height: 0 !important;
  width: 0 !important;overflow: hidden !important;
}}
.audio-recorder-container {{display: flex;justify-content: center;align-items: center;margin: 1.5rem 0;}}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Initialize components and cached resources
# ---------------------------
@st.cache_resource
def initialize_voice_system():
    return VoiceProcessor()

voice_processor = initialize_voice_system()

# Optional: initialize a voice graph if available

def _hash_bytes(b: bytes) -> str:
    """Generate SHA-256 for audio bytes"""
    return hashlib.sha256(b).hexdigest()

# ---------------------------
# Build initial state for voice graph (if used)
# ---------------------------
def build_initial_state(audio_bytes):
    return {
        "audio_bytes": audio_bytes,
        "transcript": "",
        "detected_language": "ar" if is_arabic else "en",
        "transcription_confidence": 0.0,
        "user_input": "",
        "intent": "",
        "intent_confidence": 0.0,
        "intent_reasoning": "",
        "is_arabic": is_arabic,
        "urgency": "low",
        "response": "",
        "response_tone": "",
        "key_points": [],
        "suggested_actions": [],
        "includes_warning": False,
        "verification_steps": [],
        "official_sources": [],
        "response_audio": b"",
        "error": "",
        "messages_history": st.session_state.get("voice_messages", []),
    }

# ---------------------------
# Default session state keys
# ---------------------------
defaults = {
    "voice_messages": [],
    "last_audio_hash": None,
    "is_recording": False,
    "is_processing": False,
    "is_speaking": False,
    "pending_audio": None,
    "current_transcript": "",
    "current_response": "",
    "current_metadata": {},
    "status": t('voice_status_ready', st.session_state.language),
    # store pending raw bytes across reruns
    "pending_audio_bytes": None,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v


# ---------------------------
# Return button and header
# ---------------------------
st.markdown(f"""
<div class="return-button-container">
  <a href="/" class="return-button" target="_self">
    <span class="icon">{arrow_icon}</span>
    <span>{t('voice_return_button', st.session_state.language)}</span>
  </a>
</div>
""", unsafe_allow_html=True)

st.markdown(f"""
<div class="voice-header">
  <div>🕋<span class="voice-title"> {t('voice_main_title', st.session_state.language)}</span> <span style="font-size:0.7em;color:#60a5fa;">LIVE + STREAMING</span></div>
  <div class="voice-subtitle">{t('voice_subtitle', st.session_state.language)}</div>
</div>
""", unsafe_allow_html=True)

# Status indicator
status_dot_class = (
    "listening" if st.session_state.is_recording
    else "processing" if st.session_state.is_processing
    else "speaking" if st.session_state.is_speaking
    else ""
)
st.markdown(f"""
<div class="status-indicator">
  <div class="status-dot {status_dot_class}"></div>
  <span>{st.session_state.status}</span>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# Main UI layout: left (recorder/avatar) and right (transcript/response)
# ---------------------------
st.markdown('<div class="voice-container">', unsafe_allow_html=True)
col_left, col_right = st.columns(2)

with col_left:
    avatar_class = (
        "listening" if st.session_state.is_recording
        else "speaking" if st.session_state.is_speaking
        else "processing" if st.session_state.is_processing
        else ""
    )

    waveform_html = ""
    if st.session_state.is_recording:
        waveform_html = """
        <div class="waveform">
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
        </div>
        """

    recording_label = f"🔴 {t('voice_recording', st.session_state.language)}" if st.session_state.is_recording else f"🎤 {t('voice_press_to_speak', st.session_state.language)}"

    st.markdown(f"""
    <div class="voice-left" style="position:relative;">
      <div style="position:relative;">
        <div class="voice-ring voice-ring-1"></div>
        <div class="voice-ring voice-ring-2"></div>
        <div class="voice-ring voice-ring-3"></div>
        <div class="voice-avatar {avatar_class}">🕋</div>
      </div>
     
      {waveform_html}
      <div class="record-label">{recording_label}</div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div class='audio-recorder-container'>", unsafe_allow_html=True)
    audio_bytes = audio_recorder(
        text="",
        recording_color="#ef4444",
        neutral_color="#60a5fa",
        icon_name="microphone",
        icon_size="4x",
        key="audio_recorder"
    )
    st.markdown("</div>", unsafe_allow_html=True)

with col_right:
    # transcript and response display
    transcript = st.session_state.current_transcript or t('voice_speak_now', st.session_state.language)
    response_text = st.session_state.current_response or t('voice_response_placeholder', st.session_state.language)

    # sanitize from HTML tags
    clean_transcript = re.sub(r"<.*?>", "", transcript)
    clean_response = re.sub(r"<.*?>", "", response_text)

    # Build metadata HTML (safe insertion)
    meta = st.session_state.current_metadata or {}
    meta_html_parts = []

    if meta.get("key_points"):
        key_points_html = "".join(f"<li>{p}</li>" for p in meta["key_points"])
        meta_html_parts.append(f"""
        <div class="metadata-card">
            <div class="metadata-title">💡 {t('voice_key_points', st.session_state.language)}</div>
            <ul class="metadata-list">{key_points_html}</ul>
        </div>
        """)

    if meta.get("suggested_actions"):
        suggested_html = "".join(f"<li>{a}</li>" for a in meta["suggested_actions"])
        meta_html_parts.append(f"""
        <div class="metadata-card" style="border-left-color:#a78bfa;">
            <div class="metadata-title" style="color:#a78bfa;">✅ {t('voice_suggested_actions', st.session_state.language)}</div>
            <ul class="metadata-list">{suggested_html}</ul>
        </div>
        """)

    if meta.get("verification_steps"):
        verify_html = "".join(f"<li>{s}</li>" for s in meta["verification_steps"])
        meta_html_parts.append(f"""
        <div class="metadata-card" style="border-left-color:#ef4444;">
            <div class="metadata-title" style="color:#ef4444;">⚠️ {t('voice_verification_steps', st.session_state.language)}</div>
            <ul class="metadata-list">{verify_html}</ul>
        </div>
        """)

    meta_html = "".join(meta_html_parts)

    panel_html = f"""
    <div class="transcript-container">
      <div class="panel-header">
        <div class="panel-icon">🎤</div>
        <h3 class="panel-title">Live Transcript</h3>
        <div class="panel-badge">{'● ' + (t('voice_status_listening', st.session_state.language) if st.session_state.is_recording else t('voice_status_ready', st.session_state.language))}</div>
      </div>
      <div class="transcript-text">{clean_transcript}</div>
    </div>

    <div class="response-container" style="margin-top:1rem;">
      <div class="panel-header">
        <div class="panel-icon">🤖</div>
        <h3 class="panel-title">AI Response</h3>
        <div class="panel-badge">{'● ' + (t('voice_status_speaking', st.session_state.language) if st.session_state.is_speaking else t('voice_status_ready', st.session_state.language))}</div>
      </div>
      <div class="response-content">{clean_response}</div>
      {meta_html}
    </div>
    """
    st.markdown(panel_html, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Play pending audio (if any)
# ---------------------------
if st.session_state.pending_audio:
    try:
        st.audio(st.session_state.pending_audio, format="audio/mp3", start_time=0)
    except Exception as e:
        logger.warning("Failed to play pending audio: %s", e)
    # clear the pending audio once we've queued it for play
    st.session_state.pending_audio = None
    st.session_state.is_speaking = False
    st.session_state.status = t('voice_status_ready', st.session_state.language)

# ---------------------------
# Processing pipeline when audio is recorded
# ---------------------------
if audio_bytes:
    audio_hash = _hash_bytes(audio_bytes)
    if audio_hash == st.session_state.last_audio_hash:
        # same audio as before; ignore
        logger.debug("Received same audio as last processed; ignoring.")
    elif st.session_state.is_processing:
        logger.debug("Already processing audio; ignoring new audio input.")
    else:
        # New audio: process it
        st.session_state.last_audio_hash = audio_hash
        st.session_state.is_recording = False
        st.session_state.is_processing = True
        # store the raw bytes so they persist across reruns
        st.session_state.pending_audio_bytes = audio_bytes
        st.session_state.status = t('voice_status_transcribing', st.session_state.language) if 'voice_status_transcribing' in globals() else "Transcribing..."
        st.session_state.current_metadata = {}
        st.rerun()

        # We re-run to update UI first; subsequent run will continue below after rerun returns.
else:
    # No audio input; ensure recording flag is off
    if st.session_state.is_recording:
        st.session_state.is_recording = False
        st.session_state.status = t('voice_status_ready', st.session_state.language)

# The actual heavy processing should be performed when we detect last_audio_hash has been set
# and is_processing is True. To avoid long-running blocking operations in the same Streamlit run,
# we perform those operations in a controlled block below only when audio_bytes is not present
# (i.e., after the st.rerun forced a second rendering). This keeps UI responsive.

# If we're in processing state and there's a last_audio_hash but no audio_bytes in current run,
# it likely means we've been re-rendered to perform the heavy work.
if st.session_state.is_processing and not audio_bytes and st.session_state.last_audio_hash:
    # NOTE: In this run we don't have the original audio_bytes object (Streamlit audio_recorder resets it).
    pending_audio_bytes = st.session_state.get("pending_audio_bytes", None)
    if not pending_audio_bytes:
        # Nothing to process; gracefully bail out
        st.session_state.is_processing = False
        st.session_state.status = t('voice_status_ready', st.session_state.language)
    else:
        try:
            logger.info("Transcribing audio...")
            transcription_result = voice_processor.transcribe_audio(pending_audio_bytes)
            transcript = transcription_result.get("text", "")
            language = transcription_result.get("language", st.session_state.language)
            st.session_state.current_transcript = transcript or t('voice_no_speech', language)
            st.session_state.language = language
            st.session_state.status = t('voice_status_analyzing', language) if 'voice_status_analyzing' in globals() else "Analyzing intent..."

            # Intent detection
            logger.info("Detecting intent...")
            intent_result = voice_processor.detect_voice_intent(transcript, language)
            intent = intent_result.get("intent", "GENERAL_HAJJ")
            is_arabic = intent_result.get("is_arabic", is_arabic_code(language))

            # Generate response
            logger.info("Generating response for intent: %s", intent)
            if intent == "GREETING":
                result = voice_processor.generate_voice_greeting(transcript, is_arabic)
            elif intent == "DATABASE":
                result = voice_processor.generate_database_response(transcript, is_arabic)
            else:
                result = voice_processor.generate_general_response(transcript, is_arabic)

            response_text = result.get("response", t('voice_try_again', language))
            # store metadata
            st.session_state.current_metadata = {
                k: result.get(k, []) for k in ("key_points", "suggested_actions", "verification_steps", "official_sources")
            }

            # Instead of streaming word-by-word, set the full response at once
            st.session_state.is_processing = False
            st.session_state.current_response = response_text
            st.session_state.status = t('voice_status_generating_audio', language) if 'voice_status_generating_audio' in globals() else "Preparing audio..."

            # Append conversation history
            st.session_state.voice_messages.append({"role": "user", "content": transcript})
            st.session_state.voice_messages.append({"role": "assistant", "content": response_text})

            # Generate TTS
            logger.info("Generating TTS...")
            audio_response = voice_processor.text_to_speech(response_text, language)

            if audio_response:
                st.session_state.pending_audio = audio_response
                st.session_state.is_speaking = True
                st.session_state.status = t('voice_status_speaking', language)
            else:
                st.session_state.pending_audio = None
                st.session_state.status = t('voice_status_ready', language)

        except Exception as e:
            logger.exception("Error during audio processing: %s", e)
            st.session_state.current_transcript = f"❌ {str(e)}"
            st.session_state.current_response = t('voice_error_occurred', st.session_state.language)
            st.session_state.status = t('voice_status_error', st.session_state.language)
            st.session_state.pending_audio = None
        finally:
            st.session_state.is_processing = False
            # clear pending bytes once processed
            st.session_state.pending_audio_bytes = None
            # re-render to show final transcript/response/audio controls
            st.rerun()