"""
Hajj Voice Assistant - Modularized Version
Features: Elegant sidebar, language selection, accessibility options, improved UX
Uses modular components and translation system
"""
import time
import logging
import hashlib
from pathlib import Path
import sys
from io import BytesIO
from mutagen.mp3 import MP3

import streamlit as st

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.voice_processor import VoiceProcessor
from utils.translations import t
from core.voice_graph import VoiceGraphBuilder
from utils.voice_memory import ConversationMemory
from ui.voice_sidebar import render_sidebar

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# ---------------------------
# Session State Initialization
# ---------------------------
def initialize_session_state():
    """Initialize all required session states"""
    defaults = {
        "language": 'English',
        "font_size": 'normal',  # normal, large, extra-large
        "high_contrast": False,
        "last_audio_hash": None,
        "is_processing": False,
        "is_speaking": False,
        "pending_audio": None,
        "pending_audio_bytes": None,
        "current_transcript": "",
        "current_response": "",
        "current_metadata": {},
        "status": t("voice_status_ready", "English"),  # default language is English
        "sidebar_state": "expanded",
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v


# Initialize states
initialize_session_state()

# Initialize memory
memory = ConversationMemory(max_turns=10)

# Page config
st.set_page_config(
    page_title=t('voice_page_title', st.session_state.language),
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="expanded",
)

# Initialize voice processor
@st.cache_resource
def init_voice_graph():
    voice_processor = VoiceProcessor()
    graph_builder = VoiceGraphBuilder(voice_processor)
    workflow = graph_builder.build()
    return voice_processor, workflow


voice_processor, workflow = init_voice_graph()

# Language settings
def is_arabic_code(code):
    return code in ('ar', 'arabic', 'العربية')
def is_urdu(code):
    return code in ('ur', 'اردو')


is_arabic = is_arabic_code(st.session_state.language)
is_urdus = is_urdu(st.session_state.language)

# ---------------------------
# Render Sidebar
# ---------------------------
render_sidebar(memory, st.session_state.language)

# ---------------------------
# Dynamic Styling
# ---------------------------
# Font size mapping
font_sizes = {
    'normal': {'base': '1rem', 'title': '2.2rem', 'transcript': '1.1rem', 'panel': '1.2rem'},
    'large': {'base': '1.15rem', 'title': '2.5rem', 'transcript': '1.25rem', 'panel': '1.35rem'},
    'extra-large': {'base': '1.3rem', 'title': '2.8rem', 'transcript': '1.4rem', 'panel': '1.5rem'}
}

current_sizes = font_sizes[st.session_state.font_size]

# Color scheme
if st.session_state.high_contrast:
    bg_gradient = "linear-gradient(135deg, #000000 0%, #1a1a1a 100%)"
    panel_bg = "rgba(255, 255, 255, 0.98)"
    text_primary = "#000000"
    text_secondary = "#333333"
    border_color = "rgba(0, 0, 0, 0.3)"
else:
    bg_gradient = "linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%)"
    panel_bg = "rgba(248, 250, 252, 0.95)"
    text_primary = "#1e293b"
    text_secondary = "#64748b"
    border_color = "rgba(15, 23, 42, 0.1)"

# RTL support
text_align = 'right' if is_arabic or is_urdus else 'left'
flex_direction = 'row-reverse' if is_arabic or is_urdus else 'row'

st.markdown(f"""
<style>
            
/* Global Styles */
.stApp {{
  background: {bg_gradient};
  background-attachment: fixed;
  overflow: hidden !important;
  height: 100vh;
}}

#MainMenu, footer {{visibility: hidden;}}
header {{visibility: visible !important;}}

button[kind="header"] {{
  visibility: visible !important;
  display: flex !important;
}}

.main .block-container {{
  padding: 0.75rem 1rem;
  max-width: 1400px;
  height: 100vh;
  display: flex;
  flex-direction: column;
  direction: {'rtl' if is_arabic or is_urdus else 'ltr'};
}}

/* Sidebar Styling */
[data-testid="stSidebar"] {{
  background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
  border-right: 1px solid rgba(255, 255, 255, 0.1);
}}

[data-testid="stSidebar"] .stMarkdown {{
  color: #e2e8f0;
}}

[data-testid="collapsedControl"] {{
  visibility: visible !important;
  display: flex !important;
  background: rgba(251, 191, 36, 0.9) !important;
  color: white !important;
  border-radius: 0.5rem !important;
  padding: 0.5rem !important;
  margin: 0.5rem !important;
  transition: all 0.3s ease !important;
  z-index: 9999 !important;
}}

[data-testid="collapsedControl"]:hover {{
  background: rgba(245, 158, 11, 1) !important;
  transform: scale(1.05) !important;
}}

header[data-testid="stHeader"] {{
  visibility: visible !important;
  display: block !important;
  background: transparent !important;
}}

header[data-testid="stHeader"] button {{
  visibility: visible !important;
  display: flex !important;
}}

/* Voice Header */
.voice-header {{
  text-align: center;
  padding: 0.75rem 0;
  margin-bottom: 2rem;
}}

.voice-title {{
  font-size: {current_sizes['title']};
  font-weight: 800;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.25rem;
}}

.voice-subtitle {{
  color: rgba(255, 255, 255, 0.85);
  font-size: {current_sizes['base']};
}}

/* Main Container */
.voice-container {{
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  flex: 1;
  min-height: 0;
  padding: 0 1rem;
}}

/* Left Panel - Avatar */
.voice-left {{
  display: flex;
  flex-direction: column;
  align-items: center;
  justify-content: center;
  background: rgba(255, 255, 255, 0.03);
  border-radius: 2rem;
  padding: 1.5rem;
  backdrop-filter: blur(20px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
  overflow: hidden;
  position: relative;
}}

.voice-avatar {{
  width: 180px;
  height: 180px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 90px;
  background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
  box-shadow: 0 20px 60px rgba(251, 191, 36, 0.4);
  border: 6px solid rgba(255, 255, 255, 0.15);
  animation: float 3s ease-in-out infinite;
  transition: all 0.3s ease;
}}

.voice-avatar.listening {{
  animation: pulse-listening 0.8s infinite;
  box-shadow: 0 0 80px rgba(251, 191, 36, 0.8);
}}

.voice-avatar.speaking {{
  animation: pulse-speaking 0.6s infinite;
  box-shadow: 0 0 80px rgba(245, 158, 11, 0.8);
}}

.voice-ring {{
  position: absolute;
  border: 3px solid rgba(251, 191, 36, 0.3);
  border-radius: 50%;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: expand 3s ease-out infinite;
}}

.voice-ring-1 {{width: 200px; height: 200px; animation-delay: 0s;}}
.voice-ring-2 {{width: 240px; height: 240px; animation-delay: 1s;}}
.voice-ring-3 {{width: 280px; height: 280px; animation-delay: 2s;}}

@keyframes float {{
  0%, 100% {{transform: translateY(0);}}
  50% {{transform: translateY(-15px);}}
}}

@keyframes pulse-listening {{
  0%, 100% {{transform: scale(1);}}
  50% {{transform: scale(1.1);}}
}}

@keyframes pulse-speaking {{
  0%, 100% {{transform: scale(1);}}
  50% {{transform: scale(1.15);}}
}}

@keyframes expand {{
  0% {{transform: translate(-50%, -50%) scale(0.8); opacity: 0.8;}}
  100% {{transform: translate(-50%, -50%) scale(1.5); opacity: 0;}}
}}

.record-label {{
  margin-top: 1.5rem;
  color: white;
  font-weight: 600;
  letter-spacing: 1.5px;
  font-size: {current_sizes['base']};
}}

/* Right Panel - Transcript/Response */
.transcript-container, .response-container {{
  background: {panel_bg};
  border-radius: 1.5rem;
  padding: 1.25rem;
  backdrop-filter: blur(18px);
  border: 1px solid {border_color};
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}}

.panel-header {{
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid {border_color};
  flex-direction: {flex_direction};
}}

.panel-icon {{
  font-size: 1.75rem;
  animation: icon-glow 2s ease-in-out infinite;
}}

.panel-icon.active {{
  animation: icon-bounce 0.6s ease-in-out infinite;
}}

@keyframes icon-glow {{
  0%, 100% {{opacity: 1;}}
  50% {{opacity: 0.6;}}
}}

@keyframes icon-bounce {{
  0%, 100% {{transform: translateY(0);}}
  50% {{transform: translateY(-5px);}}
}}

.panel-title {{
  font-size: {current_sizes['panel']};
  font-weight: 700;
  color: {text_primary};
  margin: 0;
}}

.panel-badge {{
  margin-{'right' if is_arabic or is_urdus else 'left'}: auto;
  padding: 0.3rem 0.8rem;
  border-radius: 1rem;
  font-weight: 600;
  font-size: 0.75rem;
  background: rgba(251, 191, 36, 0.2);
  color: #92400e;
  border: 1px solid rgba(251, 191, 36, 0.3);
}}

.panel-badge.active {{
  background: rgba(34, 197, 94, 0.2);
  color: #166534;
  border-color: rgba(34, 197, 94, 0.3);
  animation: badge-pulse 1s infinite;
}}

@keyframes badge-pulse {{
  0%, 100% {{opacity: 1;}}
  50% {{opacity: 0.6;}}
}}

.transcript-text, .response-content {{
  color: {text_primary};
  font-size: {current_sizes['transcript']};
  line-height: 1.6;
  flex: 1;
  overflow-y: auto;
  padding-{'left' if is_arabic or is_urdus else 'right'}: 0.5rem;
  text-align: {text_align};
  font-weight: 500;
}}

.transcript-text.empty, .response-content.empty {{
  color: {text_secondary};
  font-style: italic;
  overflow: hidden;
  font-weight: normal;
}}

/* Status Indicator */
.status-indicator {{
  position: fixed;
  top: 15px;
  {'left' if is_arabic or is_urdus else 'right'}: 15px;
  padding: 0.6rem 1.25rem;
  background: rgba(0, 0, 0, 0.15);
  border-radius: 2rem;
  color: white;
  font-weight: 600;
  font-size: 0.85rem;
  backdrop-filter: blur(10px);
  border: 1px solid rgba(255, 255, 255, 0.12);
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 0.5rem;
  direction: {'rtl' if is_arabic or is_urdus else 'ltr'};
}}

.status-dot {{
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #22c55e;
  animation: dot-pulse 1.5s infinite;
}}

.status-dot.listening {{background: #ef4444;}}
.status-dot.speaking {{background: #f59e0b;}}

@keyframes dot-pulse {{
  0%, 100% {{opacity: 1;}}
  50% {{opacity: 0.4;}}
}}

/* Responsive Design */
@media (max-width: 1024px) {{
  .voice-container {{
    grid-template-columns: 1fr;
    gap: 1rem;
  }}
  
  .voice-avatar {{
    width: 140px;
    height: 140px;
    font-size: 70px;
  }}
}}

/* Hide audio element */
audio {{
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  width: 0 !important;
  overflow: hidden !important;
}}

.audio-recorder-container {{
  display: flex;
  justify-content: center;
  align-items: center;
}}
</style>
""", unsafe_allow_html=True)


# ---------------------------
# Helper Functions
# ---------------------------
def _hash_bytes(b):
    if b is None:
        return None
    if not isinstance(b, (bytes, bytearray)):
        try:
            b = b.getvalue()
        except Exception:
            raise TypeError(f"Unsupported type for hashing: {type(b)}")
    return hashlib.sha256(b).hexdigest()

# ---------------------------
# Interaction Handlers
# ---------------------------

    # The response text remains, but the audio is stopped.
# ---------------------------
# Status Indicator
# ---------------------------
status_class = (
    "speaking" if st.session_state.is_speaking
    else "listening" if st.session_state.is_processing
    else ""
)
status_text = st.session_state.status or t('voice_status_ready', st.session_state.language)

st.markdown(f"""
<div class="status-indicator">
    <div class="status-dot {status_class}"></div>
    {status_text}
</div>
""", unsafe_allow_html=True)

# ---------------------------
# Header
# ---------------------------
st.markdown(f"""
<div class="voice-header">
  <div><span class="voice-title">{t('voice_main_title', st.session_state.language)}</span></div>
  <div class="voice-subtitle">{t('voice_subtitle', st.session_state.language)}</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# Main UI Layout
# ---------------------------
st.markdown('<div class="voice-container">', unsafe_allow_html=True)
col_left, col_right = st.columns(2)

with col_left:
    avatar_class = (
        "speaking" if st.session_state.is_speaking
        else "listening" if st.session_state.is_processing
        else ""
    )
    
    recording_label = (
        f"🔊 {t('voice_speaking', st.session_state.language)}" if st.session_state.is_speaking
        else f"🎤 {t('voice_press_to_speak', st.session_state.language)}"
    )

    st.markdown(f"""
    <div class="voice-left" style="position:relative;"> 
      <div style="position:relative;">
        <div class="voice-ring voice-ring-1"></div>
        <div class="voice-ring voice-ring-2"></div>
        <div class="voice-ring voice-ring-3"></div>
        <div class="voice-avatar {avatar_class}">🕋</div>
      </div>
      <div class="record-label">{recording_label}</div>
    </div>
    """, unsafe_allow_html=True)

    
            
            

    audio_bytes = st.audio_input(
        label="",
        key="audio_recorder",
        help=t('voice_press_to_speak', st.session_state.language)
    )

with col_right:
    transcript = st.session_state.current_transcript or t('voice_speak_now', st.session_state.language)
    response_text = st.session_state.current_response or t('voice_response_placeholder', st.session_state.language)

    import html
    clean_transcript = html.escape(transcript)
    clean_response = html.escape(response_text)

    transcript_icon_class = "active" if st.session_state.is_processing else ""
    response_icon_class = "active" if st.session_state.is_speaking else ""
    
    transcript_badge_class = "active" if st.session_state.is_processing else ""
    response_badge_class = "active" if st.session_state.is_speaking else ""

    # Transcript panel
    st.markdown(f"""
    <div class="transcript-container">
      <div class="panel-header">
        <div class="panel-icon {transcript_icon_class}">🗣️</div>
        <h3 class="panel-title">{t('voice_transcript_title', st.session_state.language)}</h3>
      </div>
      <div class="transcript-text">{clean_transcript}</div>
    </div>
    """, unsafe_allow_html=True)
    if st.session_state.is_speaking:
        if st.button(
            f"🚫 {t('voice_stop_speaking', st.session_state.language)}",
            use_container_width=False,
            type="primary",
            key="stop_button"
        ):
            logger.info("Stop button pressed. Halting speech.")
            # Clear the audio bytes so the playback block doesn't run
            st.session_state.pending_audio = None
            st.session_state.is_speaking = False
            st.session_state.status = t('voice_status_interrupted', st.session_state.language)
            st.rerun()

    # Response panel
    st.markdown(f"""
    <div class="response-container" style="margin-top:1rem;">
      <div class="panel-header">
        <div class="panel-icon {response_icon_class}">🕋</div>
        <h3 class="panel-title">{t('voice_response_title', st.session_state.language)}</h3>
        
        <div class="panel-badge {response_badge_class}">
            {'● ' + (t('voice_status_speaking', st.session_state.language)
            if st.session_state.is_speaking
            else t('voice_status_ready', st.session_state.language))}
        </div>
      </div>
      <div class='response-content'>{clean_response}</div> 
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Play pending audio
# ---------------------------
if st.session_state.get('pending_audio'):
    logger.info("Playing pending audio response...")
    
    try:
        st.markdown("<div style='display:none'>", unsafe_allow_html=True)
        st.audio(st.session_state.pending_audio, format="audio/mp3", autoplay=True)
        st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        logger.warning("Failed to play pending audio: %s", e)

    audio_bytes = st.session_state.pending_audio
    if isinstance(audio_bytes, bytes):
        audio_file = BytesIO(audio_bytes)
    else:
        audio_file = audio_bytes

    audio = MP3(audio_file)
    duration = audio.info.length

    # Simulate speaking
    st.session_state.is_speaking = True
    st.session_state.status = t('voice_status_speaking', st.session_state.language)

    # Block for duration
    time.sleep(duration)

    # Update state after playback ends
    st.session_state.is_speaking = False
    st.session_state.status = t('voice_status_completed', st.session_state.language)
    st.session_state.pending_audio = None

    # ⚠️ Force re-render so Streamlit sees new state
    st.rerun()
# ---------------------------
# Handle new audio input
# ---------------------------
if audio_bytes and not st.session_state.is_processing:
    if hasattr(audio_bytes, 'read'):
        audio = audio_bytes.read()
        audio_bytes.seek(0)
    else:
        audio = audio_bytes
    
    audio_hash = _hash_bytes(audio)
    
    if audio_hash != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = audio_hash
        st.session_state.pending_audio_bytes = audio
        st.session_state.is_processing = True
        st.session_state.status = t('voice_status_analyzing', st.session_state.language)
        st.rerun()

# ---------------------------
# Process pending audio
# ---------------------------
elif st.session_state.is_processing and st.session_state.get("pending_audio_bytes"):
  try:
      logger.info("Running LangGraph workflow on pending audio...")

      pending_audio_bytes = st.session_state.pending_audio_bytes
      conversation_history = memory.get_formatted_history(limit=5)

      initial_state = {
          "audio_bytes": pending_audio_bytes,
          "transcript": "",
          "detected_language": "",
          "transcription_confidence": 0.0,
          "user_input": "",
          "language": "",
          "intent": "",
          "intent_confidence": 0.0,
          "intent_reasoning": "",
          "is_vague": False,
          "is_arabic": False,
          "urgency": "",
          "sql_query": "",
          "sql_params": {},
          "sql_query_type": "",
          "sql_filters": [],
          "sql_explanation": "",
          "sql_error": "",
          "result_rows": [],
          "columns": [],
          "row_count": 0,
          "summary": "",
          "greeting_text": "",
          "general_answer": "",
          "response": "",
          "response_tone": "",
          "key_points": [],
          "suggested_actions": [],
          "includes_warning": False,
          "verification_steps": [],
          "official_sources": [],
          "response_audio": b"",
          "error": "",
          "messages_history": memory.get_conversation_history(limit=5),
          "conversation_context": conversation_history
      }

      result = workflow.invoke(initial_state)

      transcript = result.get("transcript", "")
      response_text = result.get("response", "")
      response_audio = result.get("response_audio", None)

      st.session_state.current_transcript = transcript or t('voice_no_speech', st.session_state.language)
      st.session_state.current_response = response_text or t('voice_could_not_understand', st.session_state.language)

      st.session_state.current_metadata = {
          "key_points": result.get("key_points", []),
          "suggested_actions": result.get("suggested_actions", []),
          "verification_steps": result.get("verification_steps", []),
          "official_sources": result.get("official_sources", []),
      }

      if response_audio:
          st.session_state.pending_audio = response_audio
          st.session_state.is_speaking = True
          st.session_state.status = t('voice_status_speaking', st.session_state.language)
      else:
          st.session_state.status = t('voice_status_ready', st.session_state.language)

      if transcript:
          memory.add_message('user', transcript)
          memory.extract_entities(transcript)
      if response_text:
          memory.add_message('assistant', response_text)

  except Exception as e:
      logger.exception("Error during voice processing: %s", e)
      st.session_state.current_transcript = f"❌ Error: {str(e)}"
      st.session_state.current_response = t('voice_error_processing', st.session_state.language)
      st.session_state.status = t('voice_status_error', st.session_state.language)
      st.session_state.pending_audio = None

  finally:
      st.session_state.is_processing = False
      st.session_state.status = t('voice_status_ready', st.session_state.language)
      st.session_state.pending_audio_bytes = None
      st.rerun()
