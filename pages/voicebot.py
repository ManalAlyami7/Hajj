"""
Hajj Voice Assistant - Pure Streamlit Version
No HTML rendering issues - uses only Streamlit native components
"""
import time
import re
import logging
import base64
import hashlib
from pathlib import Path
import sys
from datetime import datetime

import streamlit as st
from audio_recorder_streamlit import audio_recorder

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.voice_processor import VoiceProcessor
from utils.translations import t
from core.voice_graph import VoiceGraphBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# Memory Management
# ---------------------------
class ConversationMemory:
    """Manages conversation memory for voice assistant"""
    
    def __init__(self, max_turns=10):
        self.max_turns = max_turns
        if 'voice_memory' not in st.session_state:
            st.session_state.voice_memory = {
                'messages': [],
                'user_context': {},
                'session_start': datetime.now().isoformat()
            }
    
    def add_message(self, role: str, content: str):
        message = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        st.session_state.voice_memory['messages'].append(message)
        
        max_messages = self.max_turns * 2
        if len(st.session_state.voice_memory['messages']) > max_messages:
            st.session_state.voice_memory['messages'] = \
                st.session_state.voice_memory['messages'][-max_messages:]
        
        logger.info(f"Added {role} message to memory. Total messages: {len(st.session_state.voice_memory['messages'])}")
    
    def get_conversation_history(self, limit=None):
        messages = st.session_state.voice_memory['messages']
        if limit:
            messages = messages[-(limit * 2):]
        return messages
    
    def get_formatted_history(self, limit=5):
        messages = self.get_conversation_history(limit)
        if not messages:
            return "No previous conversation."
        
        formatted = []
        for msg in messages:
            role_label = "User" if msg['role'] == 'user' else "Assistant"
            formatted.append(f"{role_label}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def update_context(self, key: str, value: any):
        st.session_state.voice_memory['user_context'][key] = value
        logger.info(f"Updated context: {key} = {value}")
    
    def get_context(self, key: str, default=None):
        return st.session_state.voice_memory['user_context'].get(key, default)
    
    def extract_entities(self, text: str):
        agencies = re.findall(r'(?:agency|company|office)\s+([A-Z][A-Za-z\s]+)', text, re.IGNORECASE)
        if agencies:
            self.update_context('last_agency_mentioned', agencies[0].strip())
        
        locations = re.findall(r'(?:in|at|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text)
        if locations:
            self.update_context('last_location_mentioned', locations[0].strip())
    
    def clear_memory(self):
        st.session_state.voice_memory = {
            'messages': [],
            'user_context': {},
            'session_start': datetime.now().isoformat()
        }
        logger.info("Memory cleared")
    
    def get_memory_summary(self):
        return {
            'total_messages': len(st.session_state.voice_memory['messages']),
            'session_duration': self._get_session_duration(),
            'context': st.session_state.voice_memory['user_context']
        }
    
    def _get_session_duration(self):
        start = datetime.fromisoformat(st.session_state.voice_memory['session_start'])
        duration = datetime.now() - start
        minutes = int(duration.total_seconds() / 60)
        return f"{minutes} min"


# ---------------------------
# Session State Initialization
# ---------------------------
def initialize_session_state():
    """Initialize all required session states"""
    defaults = {
        "last_audio_hash": None,
        "is_processing": False,
        "is_speaking": False,
        "pending_audio": None,
        "pending_audio_bytes": None,
        "current_transcript": "",
        "current_response": "",
        "current_metadata": {},
        "status": "Ready",
        "language": "en",
        "font_size": "normal",
        "high_contrast": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

initialize_session_state()
memory = ConversationMemory(max_turns=10)

# Page config
st.set_page_config(
    page_title="🕋 Voice Assistant",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

def init_voice_graph():
    voice_processor = VoiceProcessor()
    graph_builder = VoiceGraphBuilder(voice_processor)
    workflow = graph_builder.build()
    return voice_processor, workflow

voice_processor, workflow = init_voice_graph()

def is_arabic_code(code):
    return code in ('ar', 'arabic', 'العربية')

is_arabic = is_arabic_code(st.session_state.language)

# ---------------------------
# Handle Actions
# ---------------------------
def handle_clear_memory():
    """Clear memory and reset states"""
    memory.clear_memory()
    st.session_state.current_transcript = ""
    st.session_state.current_response = ""
    st.session_state.current_metadata = {}
    st.session_state.last_audio_hash = None
    st.session_state.pending_audio = None
    st.session_state.pending_audio_bytes = None
    logger.info("Memory and states cleared successfully")

# ---------------------------
# Styles
# ---------------------------
font_sizes = {"normal": 1.0, "large": 1.15, "xlarge": 1.3}
font_multiplier = font_sizes[st.session_state.font_size]

if st.session_state.high_contrast:
    bg_gradient = "linear-gradient(135deg, #000000 0%, #1a1a1a 100%)"
    accent_primary = "#FFD700"
    accent_secondary = "#FFA500"
else:
    bg_gradient = "linear-gradient(135deg, #2D1B4E 0%, #4A2C6D 50%, #6B4891 100%)"
    accent_primary = "#FF8C42"
    accent_secondary = "#FFA07A"

st.markdown(f"""
<style>
.stApp {{
    background: {bg_gradient};
    background-attachment: fixed;
}}
#MainMenu, footer, header {{visibility: hidden;}}
.main .block-container {{
    padding-top: 2rem;
    max-width: 1400px;
}}
/* Hide default audio element */
audio {{display: none !important;}}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Top Controls Bar (Pure Streamlit)
# ---------------------------
st.markdown("### 🕋 Hajj Guardian Voice Assistant")
st.markdown("---")

# Create columns for top controls
col1, col2, col3, col4, col5, col6, col7 = st.columns([1, 1, 1, 1, 1, 1, 2])

with col1:
    if st.button("← Home"):
        st.switch_page("app.py")

with col2:
    memory_summary = memory.get_memory_summary()
    st.metric("Messages", memory_summary['total_messages'])

with col3:
    st.metric("Time", memory_summary['session_duration'])

with col4:
    status_emoji = "🔴" if st.session_state.is_processing else "🟢"
    st.metric("Status", f"{status_emoji} {st.session_state.status}")

with col5:
    lang_options = {"en": "🇬🇧 EN", "ar": "🇸🇦 AR", "ur": "🇵🇰 UR"}
    if st.button(lang_options[st.session_state.language]):
        langs = ["en", "ar", "ur"]
        current_idx = langs.index(st.session_state.language)
        st.session_state.language = langs[(current_idx + 1) % len(langs)]
        st.rerun()

with col6:
    font_labels = {"normal": "Aa", "large": "AA", "xlarge": "𝐀𝐀"}
    if st.button(font_labels[st.session_state.font_size]):
        sizes = ["normal", "large", "xlarge"]
        current_idx = sizes.index(st.session_state.font_size)
        st.session_state.font_size = sizes[(current_idx + 1) % len(sizes)]
        st.rerun()

with col7:
    col7a, col7b = st.columns(2)
    with col7a:
        contrast_label = "◑ High Contrast" if st.session_state.high_contrast else "◐ Normal"
        if st.button(contrast_label):
            st.session_state.high_contrast = not st.session_state.high_contrast
            st.rerun()
    
    with col7b:
        if st.button("🔄 New Conversation"):
            handle_clear_memory()
            st.rerun()

st.markdown("---")

# ---------------------------
# Main Layout
# ---------------------------
col_left, col_right = st.columns([1, 1])

with col_left:
    st.markdown("### 🕋 Voice Input")
    
    # Status indicator
    if st.session_state.is_speaking:
        st.info("🔊 Speaking...")
    elif st.session_state.is_processing:
        st.warning("👂 Listening...")
    else:
        st.success("🎤 Ready - Click to speak")
    
    # Audio recorder
    audio_bytes = audio_recorder(
        text="",
        recording_color="#FF8C42",
        neutral_color="#6B4891",
        icon_size="3x",
        key="audio_recorder"
    )
    
    st.markdown("---")
    st.info(f"""
    **How to use:**
    1. Click the microphone button
    2. Speak your question
    3. Click again to stop recording
    4. Wait for the response
    """)

with col_right:
    # Transcript
    st.markdown("### 🗣️ Your Question")
    transcript = st.session_state.current_transcript or t('voice_speak_now', st.session_state.language)
    
    if st.session_state.is_processing:
        with st.spinner("Processing your question..."):
            st.markdown(f"**{transcript}**")
    else:
        st.markdown(f"**{transcript}**")
    
    st.markdown("---")
    
    # Response
    st.markdown("### 🕋 Guardian's Response")
    response_text = st.session_state.current_response or t('voice_response_placeholder', st.session_state.language)
    
    if st.session_state.is_speaking:
        with st.spinner("Speaking..."):
            st.markdown(response_text)
    else:
        st.markdown(response_text)
    
    # Metadata if available
    if st.session_state.current_metadata:
        metadata = st.session_state.current_metadata
        
        if metadata.get('key_points'):
            with st.expander("📌 Key Points"):
                for point in metadata['key_points']:
                    st.markdown(f"• {point}")
        
        if metadata.get('suggested_actions'):
            with st.expander("✅ Suggested Actions"):
                for action in metadata['suggested_actions']:
                    st.markdown(f"• {action}")

# ---------------------------
# Audio Processing Logic
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

# Play pending audio
if st.session_state.get('pending_audio'):
    logger.info("Playing pending audio response...")
    try:
        st.audio(st.session_state.pending_audio, format="audio/mp3", autoplay=True)
    except Exception as e:
        logger.warning("Failed to play pending audio: %s", e)
    
    st.session_state.pending_audio = None
    st.session_state.is_speaking = False
    st.session_state.status = "Completed"
    time.sleep(1)
    st.session_state.status = "Ready"

# Handle new audio input
if audio_bytes and not st.session_state.is_processing:
    audio_hash = _hash_bytes(audio_bytes)
    
    if audio_hash != st.session_state.last_audio_hash:
        st.session_state.last_audio_hash = audio_hash
        st.session_state.pending_audio_bytes = audio_bytes
        st.session_state.is_processing = True
        st.session_state.status = "Analyzing"
        st.rerun()

# Process pending audio
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
        
        st.session_state.current_transcript = transcript or "No speech detected"
        st.session_state.current_response = response_text or "Could not understand the question"
        
        st.session_state.current_metadata = {
            "key_points": result.get("key_points", []),
            "suggested_actions": result.get("suggested_actions", []),
            "verification_steps": result.get("verification_steps", []),
            "official_sources": result.get("official_sources", []),
        }
        
        if response_audio:
            st.session_state.pending_audio = response_audio
            st.session_state.is_speaking = True
            st.session_state.status = "Speaking"
        else:
            st.session_state.status = "Ready"
        
        if transcript:
            memory.add_message('user', transcript)
            memory.extract_entities(transcript)
        if response_text:
            memory.add_message('assistant', response_text)
    
    except Exception as e:
        logger.exception("Error during voice processing: %s", e)
        st.session_state.current_transcript = f"❌ Error: {str(e)}"
        st.session_state.current_response = "An error occurred during processing."
        st.session_state.status = "Error"
        st.session_state.pending_audio = None
    
    finally:
        st.session_state.is_processing = False
        st.session_state.status = "Ready"
        st.session_state.pending_audio_bytes = None
        st.rerun()