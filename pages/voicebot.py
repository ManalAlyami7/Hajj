"""
Hajj Voice Assistant - 
Uses the existing translation system from utils.translations
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
from utils.translations import t  # existing translation function
from core.voice_graph import VoiceGraphBuilder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# ---------------------------
# Memory Management
# ---------------------------
class ConversationMemory:
    """Manages conversation memory for voice assistant"""
    
    def __init__(self, max_turns=10):
        """
        Initialize memory
        max_turns: Maximum number of conversation turns to remember (user+assistant = 1 turn)
        """
        self.max_turns = max_turns
        if 'voice_memory' not in st.session_state:
            st.session_state.voice_memory = {
                'messages': [],  # List of {role, content, timestamp}
                'user_context': {},  # Persistent user context (agencies mentioned, locations, etc.)
                'session_start': datetime.now().isoformat()
            }
    
    def add_message(self, role: str, content: str):
        """Add a message to memory"""
        message = {
            'role': role,  # 'user' or 'assistant'
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        st.session_state.voice_memory['messages'].append(message)
        
        # Trim to max_turns (keep most recent)
        # Each turn = user message + assistant message = 2 messages
        max_messages = self.max_turns * 2
        if len(st.session_state.voice_memory['messages']) > max_messages:
            st.session_state.voice_memory['messages'] = \
                st.session_state.voice_memory['messages'][-max_messages:]
        
        logger.info(f"Added {role} message to memory. Total messages: {len(st.session_state.voice_memory['messages'])}")
    
    def get_conversation_history(self, limit=None):
        """
        Get conversation history
        limit: Number of recent turns to retrieve (None = all)
        """
        messages = st.session_state.voice_memory['messages']
        if limit:
            messages = messages[-(limit * 2):]  # limit turns * 2 messages per turn
        return messages
    
    def get_formatted_history(self, limit=5):
        """Get formatted history string for LLM context"""
        messages = self.get_conversation_history(limit)
        if not messages:
            return "No previous conversation."
        
        formatted = []
        for msg in messages:
            role_label = "User" if msg['role'] == 'user' else "Assistant"
            formatted.append(f"{role_label}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def update_context(self, key: str, value: any):
        """Update persistent user context"""
        st.session_state.voice_memory['user_context'][key] = value
        logger.info(f"Updated context: {key} = {value}")
    
    def get_context(self, key: str, default=None):
        """Get value from persistent context"""
        return st.session_state.voice_memory['user_context'].get(key, default)
    
    def extract_entities(self, text: str):
        """
        Extract and store important entities from user input
        (agencies mentioned, locations, etc.)
        """
        # Extract agency names (simple pattern - improve as needed)
        agencies = re.findall(r'(?:agency|company|office)\s+([A-Z][A-Za-z\s]+)', text, re.IGNORECASE)
        if agencies:
            self.update_context('last_agency_mentioned', agencies[0].strip())
        
        # Extract locations (simple pattern)
        locations = re.findall(r'(?:in|at|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text)
        if locations:
            self.update_context('last_location_mentioned', locations[0].strip())
    
    def clear_memory(self):
        """Clear all memory (useful for new session)"""
        st.session_state.voice_memory = {
            'messages': [],
            'user_context': {},
            'session_start': datetime.now().isoformat()
        }
        logger.info("Memory cleared")
    
    def get_memory_summary(self):
        """Get a summary of current memory state"""
        return {
            'total_messages': len(st.session_state.voice_memory['messages']),
            'session_duration': self._get_session_duration(),
            'context': st.session_state.voice_memory['user_context']
        }
    
    def _get_session_duration(self):
        """Calculate session duration"""
        start = datetime.fromisoformat(st.session_state.voice_memory['session_start'])
        duration = datetime.now() - start
        minutes = int(duration.total_seconds() / 60)
        return f"{minutes} minutes"


# ---------------------------
# Language Detection / Session defaults
# ---------------------------
if 'language' not in st.session_state:
    st.session_state.language = 'en'

# ---------------------------
# Centralized State Initialization
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
        "status": t('voice_status_ready', st.session_state.language),
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

# Initialize states
initialize_session_state()

# Initialize memory
memory = ConversationMemory(max_turns=10)

lang_code = st.session_state.language
st.set_page_config(
    page_title=t('voice_page_title', st.session_state.language),
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
# Handle Clear Memory Button
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

# Check if clear memory button was clicked
if st.session_state.get('clear_memory_clicked', False):
    handle_clear_memory()
    st.session_state.clear_memory_clicked = False
    st.rerun()

# ---------------------------
# Styles (RTL support for Arabic)
# ---------------------------
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

/* Memory Badge */
.memory-badge {{
  position: fixed;
  top: 15px;
  {'left' if is_arabic else 'right'}: 210px;
  padding: 0.6rem 1.25rem;
  background: rgba(167, 139, 250, 0.15);
  backdrop-filter: blur(20px);
  border: 1px solid rgba(167, 139, 250, 0.3);
  border-radius: 2rem;
  color: #a78bfa;
  font-weight: 600;
  font-size: 0.75rem;
  z-index: 1000;
  display: flex;
  align-items: center;
  gap: 0.5rem;
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
  border-radius: 2rem;
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
.record-label{{margin-top:1rem;color:white;font-weight:600;letter-spacing:1.5px;}}
.voice-right{{display:flex;flex-direction:column;gap:1rem;height:100%;min-height:0;overflow:hidden;}}

/* LIGHTER, CLEARER PANELS */
.transcript-container,.response-container{{
  background: rgba(248, 250, 252, 0.95);
  border-radius: 1.5rem;
  padding: 1.25rem;
  backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.9);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.15);
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}}

.panel-header{{
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid rgba(15, 23, 42, 0.1);
  flex-direction: {flex_direction};
}}
.panel-icon{{font-size:1.75rem;}}
.panel-title{{
  font-size: 1.2rem;
  font-weight: 700;
  color: #0f172a;
  margin: 0;
}}
.panel-badge{{
  margin-{'right' if is_arabic else 'left'}: auto;
  padding: 0.3rem 0.8rem;
  border-radius: 1rem;
  font-weight: 600;
  font-size: 0.75rem;
  background: rgba(96, 165, 250, 0.2);
  color: #1e40af;
  border: 1px solid rgba(96, 165, 250, 0.3);
}}
.panel-badge.active{{
  background: rgba(34, 197, 94, 0.2);
  color: #166534;
  border-color: rgba(34, 197, 94, 0.3);
  animation: badge-pulse 1s infinite;
}}
@keyframes badge-pulse{{0%,100%{{opacity:1;}}50%{{opacity:0.6;}}}}

.transcript-text, .response-content{{
  color: #1e293b;
  font-size: 1.1rem;
  line-height: 1.6;
  flex: 1;
  overflow-y: auto;
  padding-{'left' if is_arabic else 'right'}: 0.5rem;
  text-align: {text_align};
  font-weight: 500;
}}

.transcript-text.empty, .response-content.empty{{
  color: #64748b;
  font-style: italic;
  overflow: hidden;
  font-weight: normal;
}}

.metadata-card{{
  background: rgba(248, 250, 252, 0.9);
  border-radius: 1rem;
  padding: 0.9rem;
  margin-top: 0.75rem;
  border-{'right' if is_arabic else 'left'}: 4px solid #60a5fa;
  text-align: {text_align};
  border: 1px solid rgba(15, 23, 42, 0.1);
}}
.metadata-title{{
  font-size: 0.85rem;
  font-weight: 600;
  color: #1e40af;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}}
.metadata-list{{
  list-style: none;
  margin: 0;
  padding: 0;
}}
.metadata-list li{{
  padding: 0.25rem 0;
  color: #374151;
  font-weight: 500;
}}
.metadata-list li:before{{
  content: "→ ";
  color: #60a5fa;
  font-weight: bold;
  margin-{'left' if is_arabic else 'right'}: 0.5rem;
}}
/* Clear Memory Button */ 
/* Clear Memory / New Conversation Button */ 
.clear-memory-btn {{
    position: fixed;
    top: 15px;
    {'left' if is_arabic else 'right'}: 15px;
    padding: 0.6rem 1.25rem;
    background: rgba(255, 255, 255, 0.75); 
    backdrop-filter: blur(20px);
    -webkit-backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.3);
    color: #1e293b;
    font-weight: 600;
  font-size: 0.85rem;
    z-index: 1000;
    cursor: pointer;
    transition: all 0.3s ease;
    border-radius: 2rem;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    box-shadow: 0 4px 15px rgba(255, 255, 255, 0.2);
}}

.clear-memory-btn:hover {{
    background: rgba(255, 255, 255, 0.9);
    border-color: rgba(255, 255, 255, 0.6);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(255, 255, 255, 0.35);
}}

.clear-memory-btn:active {{
    transform: translateY(0);
    box-shadow: 0 2px 10px rgba(255, 255, 255, 0.3);
    background: rgba(248, 250, 252, 0.85);
}}

.clear-memory-btn:focus {{
    outline: 2px solid rgba(255, 255, 255, 0.5);
    outline-offset: 2px;
}}
.status-indicator{{
  position: fixed;
  top: 15px;
  {'left' if is_arabic else 'right'}: 390px;
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
  direction: {'rtl' if is_arabic else 'ltr'};
}}
.status-dot{{
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #22c55e;
  animation: dot-pulse 1.5s infinite;
}}
.status-dot.listening{{background: #ef4444;}}
.status-dot.speaking{{background: #a78bfa;}}
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

button:hover {{
    opacity: 0.9;
}}
.audio-recorder-container {{display: flex;justify-content: center;align-items: center;margin: 1.5rem 0;}}

[data-testid="stButton-clear_memory_btn"] {{
    display: none !important;
    visibility: hidden !important;
    height: 0 !important;
    width: 0 !important;
    padding: 0 !important;
    margin: 0 !important;
    border: none !important;
}}


</style>
""", unsafe_allow_html=True)

# ---------------------------
# Initialize components
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
# UI Elements
# ---------------------------

# Return button
st.markdown(f"""
<div class="return-button-container">
  <a href="/" class="return-button" target="_self">
    <span class="icon">{arrow_icon}</span>
    <span>{t('voice_return_button', st.session_state.language)}</span>
  </a>
</div>
""", unsafe_allow_html=True)

# Compact top bar
st.markdown('<div style="margin-bottom: 1rem;"></div>', unsafe_allow_html=True)

# --- Memory Badge, Clear Button & Status ---
memory_summary = memory.get_memory_summary()

status_class = (
    "speaking" if st.session_state.is_speaking
    else "listening" if st.session_state.is_processing
    else ""
)
status_text = st.session_state.status or "Ready"

# Create columns for top controls
col_mem, col_clear, col_status = st.columns(3)

with col_mem:
    st.markdown(f"""
    <div class="memory-badge">
        🧠 {memory_summary['total_messages']} messages | ⏱️ {memory_summary['session_duration']}
    </div>
    """, unsafe_allow_html=True)

with col_clear:
    # 2️⃣ Visible custom button triggering the hidden Streamlit button
    st.markdown(f"""
    <button class="clear-memory-btn" 
        onclick="document.querySelector('[data-testid=\\'stButton-clear_memory_btn\\'] button').click()">
        + {t('voice_clear_memory', st.session_state.language)}
    </button>
    """, unsafe_allow_html=True)

    # # 3️⃣ Hidden actual button (logic intact)
    # if st.button("", key="clear_memory_btn", use_container_width=False):
    #     st.session_state.clear_memory_clicked = True
    #     st.rerun()

with col_status:
    st.markdown(f"""
    <div class="status-indicator">
        <div class="status-dot {status_class}"></div>
        {status_text}
    </div>
    """, unsafe_allow_html=True)

st.markdown(f"""
<div class="voice-header">
  <div>🕋<span class="voice-title"> {t('voice_main_title', st.session_state.language)}</span></div>
  <div class="voice-subtitle">{t('voice_subtitle', st.session_state.language)}</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# Main UI layout
# ---------------------------
st.markdown('<div class="voice-container">', unsafe_allow_html=True)
col_left, col_right = st.columns(2)
with col_left:
    avatar_class = (
        "speaking" if st.session_state.is_speaking
        else "processing" if st.session_state.is_processing
        else ""
    )
    
    # 1. Define waveform HTML based on state (now uses is_speaking)
    waveform_html = ""
    if st.session_state.is_speaking:
        waveform_html = """
        <div class="waveform">
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
            <div class="waveform-bar"></div>
        </div>
        """
    
    # 2. Define the user-facing status label
    recording_label = (
        f"🔊 {t('voice_speaking', st.session_state.language)}" if st.session_state.is_speaking
        else f"🎤 {t('voice_press_to_speak', st.session_state.language)}"
    )

    # 3. Build the complete HTML string
    # Note: The CSS class 'voice-left' already defines the flex properties
    html_content = f"""
    <div class="voice-left" style="position:relative;"> 
      <div style="position:relative;">
        <div class="voice-ring voice-ring-1"></div>
        <div class="voice-ring voice-ring-2"></div>
        <div class="voice-ring voice-ring-3"></div>
        <div class="voice-avatar {avatar_class}">🕋</div>
      </div>
      <div class="record-label">{recording_label}</div>
    </div>
    """
    
    st.markdown(html_content, unsafe_allow_html=True)

    # Render audio_input right after inside the same column
    audio_bytes = st.audio_input(
        label="",
        key="audio_recorder",
        help="Click to start recording, click again to stop"
    )
with col_right:
    transcript = st.session_state.current_transcript or t('voice_speak_now', st.session_state.language)
    response_text = st.session_state.current_response or t('voice_response_placeholder', st.session_state.language)

    import html
    clean_transcript = html.escape(transcript)
    clean_response = html.escape(response_text)

    # ✅ Transcript panel first
    st.markdown(f"""
    <div class="transcript-container">
      <div class="panel-header">
        <div class="panel-icon">🗣️</div>
        <h3 class="panel-title">Spoken Request</h3>
        <div class="panel-badge">
            {'● ' + (t('voice_status_listening', st.session_state.language)
            if st.session_state.is_speaking
            else t('voice_status_ready', st.session_state.language))}
        </div>
      </div>
      <div class="transcript-text">{clean_transcript}</div>
    </div>
    """, unsafe_allow_html=True)

    # ✅ Response container
    st.markdown(f"""
    <div class="response-container" style="margin-top:1rem;">
      <div class="panel-header">
        <div class="panel-icon">🕋</div>
        <h3 class="panel-title">Assistant Response</h3>
        <div class="panel-badge">
            {'● ' + (t('voice_status_speaking', st.session_state.language)
            if st.session_state.is_speaking
            else t('voice_status_ready', st.session_state.language))}
        </div>
      </div>
      <div class='response-content'>{clean_response}</div> 
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

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
    
    st.session_state.pending_audio = None
    st.session_state.is_speaking = False
    st.session_state.status = t('voice_status_completed', st.session_state.language)
    
    # Optional: Reset to "Ready" after a brief delay
    time.sleep(2)
    
    st.session_state.status = t('voice_status_ready', st.session_state.language)

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

        # Get conversation history for context
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
            "messages_history": memory.get_conversation_history(limit=5),  # Pass memory to workflow
            "conversation_context": conversation_history  # Formatted history string
        }

        result = workflow.invoke(initial_state)
        
        transcript = result.get("transcript", "")
        response_text = result.get("response", "")
        response_audio = result.get("response_audio", None)

        # Update session state
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

        # ADD TO MEMORY
        if transcript:
            memory.add_message('user', transcript)
            memory.extract_entities(transcript)  # Extract entities for context
        if response_text:
            memory.add_message('assistant', response_text)

    except Exception as e:
        logger.exception("Error during voice processing: %s", e)
        st.session_state.current_transcript = f"❌ Error: {str(e)}"
        st.session_state.current_response = t('voice_error_processing', st.session_state.language) if 'voice_error_processing' in globals() else "An error occurred during processing."
        st.session_state.status = t('voice_status_error', st.session_state.language)
        st.session_state.pending_audio = None
    
    finally:
        st.session_state.is_processing = False
        st.session_state.status = t('voice_status_ready', st.session_state.language)
        st.session_state.pending_audio_bytes = None
        st.rerun()
