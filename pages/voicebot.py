"""
Hajj Voice Assistant - Enhanced Version
Features:
- Warmer, more welcoming color palette
- Smooth animations for active states
- Language selector (Arabic, English, Urdu)
- Accessibility options (font size, high contrast)
- Improved icon animations
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
# Memory Management (unchanged)
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
        return f"{minutes} minutes"


# ---------------------------
# Session State Initialization
# ---------------------------
def initialize_session_state():
    """Initialize all required session states including accessibility"""
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
        "font_size": "normal",  # normal, large, xlarge
        "high_contrast": False,
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

initialize_session_state()
memory = ConversationMemory(max_turns=10)

# Page config
st.set_page_config(
    page_title="🕋 Voice Assistant - Hajj & Umrah",
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

if st.session_state.get('clear_memory_clicked', False):
    handle_clear_memory()
    st.session_state.clear_memory_clicked = False
    st.rerun()

# ---------------------------
# Dynamic Styles with Accessibility
# ---------------------------
rtl_class = 'rtl' if is_arabic else ''
text_align = 'right' if is_arabic else 'left'
flex_direction = 'row-reverse' if is_arabic else 'row'
return_position = 'right: 20px;' if is_arabic else 'left: 20px;'
transform_direction = 'translateX(5px)' if is_arabic else 'translateX(-5px)'
icon_transform = 'translateX(3px)' if is_arabic else 'translateX(-3px)'
arrow_icon = '←' if not is_arabic else '→'

# Font size multipliers
font_sizes = {
    "normal": 1.0,
    "large": 1.2,
    "xlarge": 1.4
}
font_multiplier = font_sizes[st.session_state.font_size]

# Color scheme (warmer palette)
if st.session_state.high_contrast:
    # High contrast mode
    bg_gradient = "linear-gradient(135deg, #000000 0%, #1a1a1a 100%)"
    text_color = "#FFFFFF"
    panel_bg = "rgba(255, 255, 255, 0.95)"
    panel_text = "#000000"
    accent_primary = "#FFD700"
    accent_secondary = "#FFA500"
else:
    # Normal warm mode
    bg_gradient = "linear-gradient(135deg, #2D1B4E 0%, #4A2C6D 50%, #6B4891 100%)"
    text_color = "rgba(255, 255, 255, 0.95)"
    panel_bg = "rgba(255, 248, 245, 0.95)"
    panel_text = "#2D1B4E"
    accent_primary = "#FF8C42"
    accent_secondary = "#FFA07A"

st.markdown(f"""
<style>
/* Root variables for easy theming */
:root {{
    --font-multiplier: {font_multiplier};
    --bg-gradient: {bg_gradient};
    --text-color: {text_color};
    --panel-bg: {panel_bg};
    --panel-text: {panel_text};
    --accent-primary: {accent_primary};
    --accent-secondary: {accent_secondary};
}}

.stApp {{
    background: var(--bg-gradient);
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

/* ========================================
   TOP BAR CONTROLS WITH ANIMATIONS
   ======================================== */

/* Accessibility Controls - Top Right */
.accessibility-controls {{
    position: fixed;
    top: 15px;
    {'left' if is_arabic else 'right'}: 15px;
    display: flex;
    gap: 0.75rem;
    z-index: 2000;
    direction: {'rtl' if is_arabic else 'ltr'};
}}

.control-btn {{
    padding: 0.6rem 1rem;
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 2rem;
    color: white;
    font-weight: 600;
    font-size: calc(0.85rem * var(--font-multiplier));
    cursor: pointer;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    display: flex;
    align-items: center;
    gap: 0.5rem;
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
}}

.control-btn:hover {{
    background: rgba(255, 140, 66, 0.25);
    border-color: var(--accent-primary);
    transform: translateY(-2px);
    box-shadow: 0 6px 20px rgba(255, 140, 66, 0.3);
}}

.control-btn.active {{
    background: var(--accent-primary);
    border-color: var(--accent-primary);
    color: #2D1B4E;
}}

/* Language Selector Dropdown */
.language-selector {{
    position: relative;
}}

.language-dropdown {{
    position: absolute;
    top: calc(100% + 0.5rem);
    {'left' if is_arabic else 'right'}: 0;
    background: rgba(255, 255, 255, 0.95);
    backdrop-filter: blur(20px);
    border-radius: 1rem;
    padding: 0.5rem;
    min-width: 150px;
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    opacity: 0;
    visibility: hidden;
    transform: translateY(-10px);
    transition: all 0.3s ease;
}}

.language-selector:hover .language-dropdown {{
    opacity: 1;
    visibility: visible;
    transform: translateY(0);
}}

.lang-option {{
    padding: 0.75rem 1rem;
    color: #2D1B4E;
    cursor: pointer;
    border-radius: 0.5rem;
    transition: all 0.2s ease;
    font-weight: 600;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}

.lang-option:hover {{
    background: var(--accent-primary);
    color: white;
}}

.lang-option.active {{
    background: rgba(255, 140, 66, 0.2);
    color: var(--accent-primary);
}}

/* Memory Badge */
.memory-badge {{
    position: fixed;
    top: 80px;
    {'left' if is_arabic else 'right'}: 15px;
    padding: 0.6rem 1.25rem;
    background: rgba(255, 140, 66, 0.2);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 140, 66, 0.4);
    border-radius: 2rem;
    color: var(--accent-primary);
    font-weight: 600;
    font-size: calc(0.75rem * var(--font-multiplier));
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: 0.5rem;
    animation: slideInRight 0.5s ease;
}}

/* Return Button */
.return-button-container {{
    position: fixed;
    top: 15px;
    {return_position}
    z-index: 2000;
}}

.return-button {{
    display: inline-flex;
    align-items: center;
    gap: 0.5rem;
    padding: 0.6rem 1.25rem;
    background: rgba(255, 255, 255, 0.15);
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.25);
    border-radius: 2rem;
    color: white;
    font-weight: 600;
    font-size: calc(0.9rem * var(--font-multiplier));
    text-decoration: none !important;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
    cursor: pointer;
}}

.return-button:hover {{
    background: rgba(255, 255, 255, 0.25);
    border-color: rgba(255, 255, 255, 0.4);
    transform: {transform_direction};
    box-shadow: 0 6px 20px rgba(0, 0, 0, 0.2);
    text-decoration: none !important;
}}

.return-button .icon {{
    font-size: calc(1.2rem * var(--font-multiplier));
    transition: transform 0.3s ease;
}}

.return-button:hover .icon {{
    transform: {icon_transform};
}}

/* Status Indicator */
.status-indicator {{
    position: fixed;
    top: 15px;
    {'left' if is_arabic else 'right'}: 440px;
    padding: 0.6rem 1.25rem;
    background: rgba(0, 0, 0, 0.2);
    border-radius: 2rem;
    color: white;
    font-weight: 600;
    font-size: calc(0.85rem * var(--font-multiplier));
    backdrop-filter: blur(10px);
    border: 1px solid rgba(255, 255, 255, 0.15);
    z-index: 1000;
    display: flex;
    align-items: center;
    gap: 0.5rem;
}}

.status-dot {{
    width: 10px;
    height: 10px;
    border-radius: 50%;
    background: #22c55e;
    animation: dot-pulse 1.5s infinite;
}}

.status-dot.listening {{
    background: var(--accent-primary);
    box-shadow: 0 0 15px var(--accent-primary);
}}

.status-dot.speaking {{
    background: var(--accent-secondary);
    box-shadow: 0 0 15px var(--accent-secondary);
}}

/* ========================================
   HEADER
   ======================================== */

.voice-header {{
    text-align: center;
    padding: 0.75rem 0;
    margin-bottom: 2rem;
    animation: fadeInDown 0.6s ease;
}}

.voice-title {{
    font-size: calc(2.2rem * var(--font-multiplier));
    font-weight: 800;
    letter-spacing: 2px;
    background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    margin-bottom: 0.25rem;
}}

.voice-subtitle {{
    color: var(--text-color);
    font-size: calc(0.95rem * var(--font-multiplier));
    opacity: 0.9;
}}

/* ========================================
   MAIN LAYOUT
   ======================================== */

.voice-container {{
    display: grid;
    grid-template-columns: 1fr 1fr;
    gap: 1.5rem;
    flex: 1;
    min-height: 0;
    padding: 0 1rem;
}}

/* ========================================
   LEFT PANEL - AVATAR & RECORDER
   ======================================== */

.voice-left {{
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    background: rgba(255, 255, 255, 0.05);
    border-radius: 2rem;
    padding: 2rem;
    backdrop-filter: blur(20px);
    border: 1px solid rgba(255, 255, 255, 0.1);
    box-shadow: 0 8px 32px rgba(0, 0, 0, 0.25);
    position: relative;
    overflow: hidden;
    animation: fadeInLeft 0.6s ease;
}}

.voice-avatar {{
    width: 180px;
    height: 180px;
    border-radius: 50%;
    display: flex;
    align-items: center;
    justify-content: center;
    font-size: 90px;
    background: linear-gradient(135deg, var(--accent-primary) 0%, var(--accent-secondary) 100%);
    box-shadow: 0 20px 60px rgba(255, 140, 66, 0.4);
    border: 6px solid rgba(255, 255, 255, 0.2);
    animation: float 3s ease-in-out infinite;
    transition: all 0.3s ease;
    position: relative;
    z-index: 2;
}}

.voice-avatar.listening {{
    animation: pulse-listening 0.8s infinite, float 3s ease-in-out infinite;
    box-shadow: 0 0 80px var(--accent-primary);
    transform: scale(1.05);
}}

.voice-avatar.speaking {{
    animation: pulse-speaking 0.6s infinite, float 3s ease-in-out infinite;
    box-shadow: 0 0 80px var(--accent-secondary);
    transform: scale(1.1);
}}

/* Animated Rings */
.voice-ring {{
    position: absolute;
    border: 3px solid rgba(255, 140, 66, 0.3);
    border-radius: 50%;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    animation: expand 3s ease-out infinite;
    z-index: 1;
}}

.voice-ring-1 {{
    width: 200px;
    height: 200px;
    animation-delay: 0s;
}}

.voice-ring-2 {{
    width: 240px;
    height: 240px;
    animation-delay: 1s;
}}

.voice-ring-3 {{
    width: 280px;
    height: 280px;
    animation-delay: 2s;
}}

/* Glowing Icon Animation */
@keyframes icon-glow {{
    0%, 100% {{
        filter: drop-shadow(0 0 5px var(--accent-primary));
    }}
    50% {{
        filter: drop-shadow(0 0 20px var(--accent-primary));
    }}
}}

.voice-avatar.listening,
.voice-avatar.speaking {{
    animation: icon-glow 1s infinite, float 3s ease-in-out infinite;
}}

.record-label {{
    margin-top: 1.5rem;
    color: white;
    font-weight: 600;
    font-size: calc(1rem * var(--font-multiplier));
    letter-spacing: 1.5px;
    text-align: center;
}}

/* ========================================
   RIGHT PANEL - TRANSCRIPT & RESPONSE
   ======================================== */

.voice-right {{
    display: flex;
    flex-direction: column;
    gap: 1rem;
    height: 100%;
    min-height: 0;
    overflow: hidden;
    animation: fadeInRight 0.6s ease;
}}

.transcript-container,
.response-container {{
    background: var(--panel-bg);
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
    transition: all 0.3s ease;
}}

.transcript-container:hover,
.response-container:hover {{
    box-shadow: 0 12px 40px rgba(255, 140, 66, 0.2);
    border-color: var(--accent-primary);
}}

.panel-header {{
    display: flex;
    align-items: center;
    gap: 0.75rem;
    margin-bottom: 0.75rem;
    padding-bottom: 0.75rem;
    border-bottom: 2px solid rgba(45, 27, 78, 0.1);
    flex-direction: {flex_direction};
}}

.panel-icon {{
    font-size: calc(1.75rem * var(--font-multiplier));
    animation: none;
    transition: transform 0.3s ease;
}}

/* Animated Icon on Active State */
.panel-header.active .panel-icon {{
    animation: bounce 1s infinite;
}}

.panel-title {{
    font-size: calc(1.2rem * var(--font-multiplier));
    font-weight: 700;
    color: var(--panel-text);
    margin: 0;
}}

.panel-badge {{
    margin-{'right' if is_arabic else 'left'}: auto;
    padding: 0.3rem 0.8rem;
    border-radius: 1rem;
    font-weight: 600;
    font-size: calc(0.75rem * var(--font-multiplier));
    background: rgba(96, 165, 250, 0.2);
    color: #1e40af;
    border: 1px solid rgba(96, 165, 250, 0.3);
    transition: all 0.3s ease;
}}

.panel-badge.active {{
    background: rgba(255, 140, 66, 0.3);
    color: var(--accent-primary);
    border-color: var(--accent-primary);
    animation: badge-pulse 1s infinite;
}}

.transcript-text,
.response-content {{
    color: var(--panel-text);
    font-size: calc(1.1rem * var(--font-multiplier));
    line-height: 1.6;
    flex: 1;
    overflow-y: auto;
    padding-{'left' if is_arabic else 'right'}: 0.5rem;
    text-align: {text_align};
    font-weight: 500;
}}

.transcript-text.empty,
.response-content.empty {{
    color: #64748b;
    font-style: italic;
    font-weight: normal;
}}

/* ========================================
   ANIMATIONS
   ======================================== */

@keyframes fadeInDown {{
    from {{
        opacity: 0;
        transform: translateY(-20px);
    }}
    to {{
        opacity: 1;
        transform: translateY(0);
    }}
}}

@keyframes fadeInLeft {{
    from {{
        opacity: 0;
        transform: translateX(-30px);
    }}
    to {{
        opacity: 1;
        transform: translateX(0);
    }}
}}

@keyframes fadeInRight {{
    from {{
        opacity: 0;
        transform: translateX(30px);
    }}
    to {{
        opacity: 1;
        transform: translateX(0);
    }}
}}

@keyframes slideInRight {{
    from {{
        opacity: 0;
        transform: translateX(20px);
    }}
    to {{
        opacity: 1;
        transform: translateX(0);
    }}
}}

@keyframes float {{
    0%, 100% {{
        transform: translateY(0);
    }}
    50% {{
        transform: translateY(-15px);
    }}
}}

@keyframes pulse-listening {{
    0%, 100% {{
        transform: scale(1);
    }}
    50% {{
        transform: scale(1.1);
    }}
}}

@keyframes pulse-speaking {{
    0%, 100% {{
        transform: scale(1);
    }}
    50% {{
        transform: scale(1.15);
    }}
}}

@keyframes expand {{
    0% {{
        transform: translate(-50%, -50%) scale(0.8);
        opacity: 0.8;
    }}
    100% {{
        transform: translate(-50%, -50%) scale(1.5);
        opacity: 0;
    }}
}}

@keyframes bounce {{
    0%, 100% {{
        transform: translateY(0);
    }}
    50% {{
        transform: translateY(-10px);
    }}
}}

@keyframes dot-pulse {{
    0%, 100% {{
        opacity: 1;
    }}
    50% {{
        opacity: 0.4;
    }}
}}

@keyframes badge-pulse {{
    0%, 100% {{
        opacity: 1;
    }}
    50% {{
        opacity: 0.6;
    }}
}}

/* ========================================
   RESPONSIVE DESIGN
   ======================================== */

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
    
    .accessibility-controls {{
        flex-wrap: wrap;
        gap: 0.5rem;
    }}
    
    .return-button-container {{
        top: 10px;
        {'right' if is_arabic else 'left'}: 10px;
    }}
    
    .memory-badge {{
        top: 70px;
        font-size: calc(0.7rem * var(--font-multiplier));
    }}
}}

/* Hide audio element */
audio {{
    display: none !important;
    visibility: hidden !important;
}}

</style>
""", unsafe_allow_html=True)

# ---------------------------
# UI COMPONENTS
# ---------------------------

# Accessibility Controls (Top Right)
st.markdown(f"""
<div class="accessibility-controls">
    <!-- Language Selector -->
    <div class="language-selector">
        <div class="control-btn">
            🌐 {'اللغة' if is_arabic else 'Language'}
        </div>
        <div class="language-dropdown">
            <div class="lang-option {'active' if st.session_state.language == 'en' else ''}" onclick="window.location.href='?lang=en'">
                🇬🇧 English
            </div>
            <div class="lang-option {'active' if st.session_state.language == 'ar' else ''}" onclick="window.location.href='?lang=ar'">
                🇸🇦 العربية
            </div>
            <div class="lang-option {'active' if st.session_state.language == 'ur' else ''}" onclick="window.location.href='?lang=ur'">
                🇵🇰 اردو
            </div>
        </div>
    </div>
    
    <!-- Font Size Toggle -->
    <div class="control-btn {'active' if st.session_state.font_size != 'normal' else ''}" 
         onclick="document.getElementById('font_size_btn').click()">
        {'🔤' if st.session_state.font_size == 'normal' else '🔠'}
        {'Aa' if not is_arabic else 'أ'}
    </div>
    
    <!-- High Contrast Toggle -->
    <div class="control-btn {'active' if st.session_state.high_contrast else ''}"
         onclick="document.getElementById('contrast_btn').click()">
        {'◐' if not st.session_state.high_contrast else '◑'}
    </div>
</div>
""", unsafe_allow_html=True)

# Hidden buttons for functionality
col1, col2 = st.columns(2)
with col1:
    if st.button("", key="font_size_btn"):
        sizes = ["normal", "large", "xlarge"]
        current_idx = sizes.index(st.session_state.font_size)
        st.session_state.font_size = sizes[(current_idx + 1) % len(sizes)]
        st.rerun()

with col2:
    if st.button("", key="contrast_btn"):
        st.session_state.high_contrast = not st.session_state.high_contrast
        st.rerun()

# Return button
st.markdown(f"""
<div class="return-button-container">
    <a href="/" class="return-button" target="_self">
        <span class="icon">{arrow_icon}</span>
        <span>{t('voice_return_button', st.session_state.language)}</span>
    </a>
</div>
""", unsafe_allow_html=True)

# Memory Badge & Status
memory_summary = memory.get_memory_summary()
st.markdown(f"""
<div class="memory-badge">
    🧠 {memory_summary['total_messages']} messages | ⏱️ {memory_summary['session_duration']}
</div>
""", unsafe_allow_html=True)

status_class = (
    "speaking" if st.session_state.is_speaking
    else "listening" if st.session_state.is_processing
    else ""
)
status_text = st.session_state.status or "Ready"

st.markdown(f"""
<div class="status-indicator">
    <div class="status-dot {status_class}"></div>
    {status_text}
</div>
""", unsafe_allow_html=True)

# Header
st.markdown(f"""
<div class="voice-header">
    <div>🕋<span class="voice-title">{t('voice_main_title', st.session_state.language)}</span></div>
    <div class="voice-subtitle">{t('voice_subtitle', st.session_state.language)}</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------
# Main Layout
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
    <div class="voice-left">
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
        help="Click to start recording, click again to stop"
    )

with col_right:
    transcript = st.session_state.current_transcript or t('voice_speak_now', st.session_state.language)
    response_text = st.session_state.current_response or t('voice_response_placeholder', st.session_state.language)
    
    import html
    clean_transcript = html.escape(transcript)
    clean_response = html.escape(response_text)
    
    # Determine if panels are active
    transcript_active = "active" if st.session_state.is_processing else ""
    response_active = "active" if st.session_state.is_speaking else ""
    
    # Transcript panel
    st.markdown(f"""
    <div class="transcript-container">
        <div class="panel-header {transcript_active}">
            <div class="panel-icon">🗣️</div>
            <h3 class="panel-title">{t('voice_transcript_title', st.session_state.language)}</h3>
            <div class="panel-badge {'active' if st.session_state.is_processing else ''}">
                {'● ' + t('voice_status_listening', st.session_state.language) if st.session_state.is_processing 
                 else t('voice_status_ready', st.session_state.language)}
            </div>
        </div>
        <div class="transcript-text">{clean_transcript}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # Response panel
    st.markdown(f"""
    <div class="response-container" style="margin-top:1rem;">
        <div class="panel-header {response_active}">
            <div class="panel-icon">🕋</div>
            <h3 class="panel-title">{t('voice_response_title', st.session_state.language)}</h3>
            <div class="panel-badge {'active' if st.session_state.is_speaking else ''}">
                {'● ' + t('voice_status_speaking', st.session_state.language) if st.session_state.is_speaking
                 else t('voice_status_ready', st.session_state.language)}
            </div>
        </div>
        <div class='response-content'>{clean_response}</div>
    </div>
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Audio Processing Logic (unchanged from original)
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
        st.markdown("<div style='display:none'>", unsafe_allow_html=True)
        st.audio(st.session_state.pending_audio, format="audio/mp3", autoplay=True)
        st.markdown("</div>", unsafe_allow_html=True)
    except Exception as e:
        logger.warning("Failed to play pending audio: %s", e)
    
    st.session_state.pending_audio = None
    st.session_state.is_speaking = False
    st.session_state.status = t('voice_status_completed', st.session_state.language)
    time.sleep(2)
    st.session_state.status = t('voice_status_ready', st.session_state.language)

# Handle new audio input
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