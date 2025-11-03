# voicebot.py
"""
Hajj Voice Assistant (Cleaned + Fixed)
- Fixed HTML showing as code blocks
- Preserved visual design and structure
- Removed redundant duplication
"""

import time
import re
import streamlit as st
from audio_recorder_streamlit import audio_recorder

# Core imports (must exist in your project)
from core.voice_processor import VoiceProcessor
from core.voice_graph import VoiceGraphBuilder
from ui.voice_interface import RealTimeVoiceStyles

# ---------------------------
# Streamlit Config
# ---------------------------
st.set_page_config(
    page_title="Hajj Voice Assistant",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------
# Styles
# ---------------------------
st.markdown(RealTimeVoiceStyles.get_styles(), unsafe_allow_html=True)

# ---------------------------
# Init components
# ---------------------------
@st.cache_resource
def initialize_voice_system():
    processor = VoiceProcessor()
    graph_builder = VoiceGraphBuilder(processor)
    return processor, graph_builder.build()

voice_processor, voice_graph = initialize_voice_system()

# ---------------------------
# Session State
# ---------------------------
defaults = {
    "voice_messages": [],
    "last_audio": None,
    "is_recording": False,
    "is_processing": False,
    "is_speaking": False,
    "current_transcript": "",
    "current_response": "",
    "current_metadata": {},
    "status": "Ready",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ---------------------------
# UI Header
# ---------------------------
st.markdown("""
<div class="voice-header">
  <div class="voice-title">🕋 Hajj Voice Assistant</div>
  <div class="voice-subtitle">Real-time Speech Recognition & AI Responses</div>
</div>
""", unsafe_allow_html=True)

# Status
status_dot_class = (
    "listening" if st.session_state.is_recording
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
# Main Layout
# ---------------------------
st.markdown('<div class="voice-container">', unsafe_allow_html=True)
col_left, col_right = st.columns(2)

# Left: Avatar + Recorder
with col_left:
    avatar_class = (
        "listening" if st.session_state.is_recording
        else "speaking" if st.session_state.is_speaking
        else ""
    )
    st.markdown(f"""
    <div class="voice-left" style="position:relative;">
      <div style="position:relative;">
        <div class="voice-ring voice-ring-1"></div>
        <div class="voice-ring voice-ring-2"></div>
        <div class="voice-ring voice-ring-3"></div>
        <div class="voice-avatar {avatar_class}">🕋</div>
      </div>
      <div class="record-label">
        {'🔴 Recording...' if st.session_state.is_recording else '🎤 Press to Speak'}
      </div>
    </div>
    """, unsafe_allow_html=True)

    audio_bytes = audio_recorder(
        text="",
        recording_color="#ef4444",
        neutral_color="#3b82f6",
        icon_name="microphone",
        icon_size="2x",
        pause_threshold=2.0,
        sample_rate=16000,
        key="voice_recorder",
    )

# Right: Transcript + Response
with col_right:
    transcript_badge = "active" if st.session_state.is_recording or st.session_state.is_processing else ""
    transcript = st.session_state.current_transcript or "Speak now..."
    response_badge = "active" if st.session_state.is_speaking else ""
    response_text = st.session_state.current_response or "Response will appear here..."

    # Clean any accidental HTML in AI text
    clean_response = re.sub(r"<.*?>", "", response_text)
    clean_transcript = re.sub(r"<.*?>", "", transcript)

    # Metadata HTML
    # --- Metadata Rendering (fixed) ---
    meta_html_parts = []
    meta = st.session_state.current_metadata

    if meta:
        # Key Points
        if meta.get("key_points"):
            key_points_html = "".join(f"<li>{re.escape(p)}</li>" for p in meta["key_points"])
            meta_html_parts.append(f"""
            <div class="metadata-card">
                <div class="metadata-title">💡 Key Points</div>
                <ul class="metadata-list">{key_points_html}</ul>
            </div>
            """)

        # Suggested Actions
        if meta.get("suggested_actions"):
            suggested_html = "".join(f"<li>{re.escape(a)}</li>" for a in meta["suggested_actions"])
            meta_html_parts.append(f"""
            <div class="metadata-card" style="border-left-color:#a78bfa;">
                <div class="metadata-title" style="color:#a78bfa;">✅ Suggested Actions</div>
                <ul class="metadata-list">{suggested_html}</ul>
            </div>
            """)

        # Verification Steps
        if meta.get("verification_steps"):
            verify_html = "".join(f"<li>{re.escape(s)}</li>" for s in meta["verification_steps"])
            meta_html_parts.append(f"""
            <div class="metadata-card" style="border-left-color:#ef4444;">
                <div class="metadata-title" style="color:#ef4444;">⚠️ Verification Steps</div>
                <ul class="metadata-list">{verify_html}</ul>
            </div>
            """)

    meta_html = "".join(meta_html_parts)

    # Build full panel HTML
    panel_html = f"""
    <div class="transcript-container">
      <div class="panel-header">
        <div class="panel-icon">🎤</div>
        <h3 class="panel-title">Live Transcript</h3>
        <div class="panel-badge {transcript_badge}">
          {'● Listening' if st.session_state.is_recording else '○ Ready'}
        </div>
      </div>
      <div class="transcript-text">{clean_transcript}</div>
    </div>
    <div class="response-container" style="margin-top:1rem;">
      <div class="panel-header">
        <div class="panel-icon">🤖</div>
        <h3 class="panel-title">AI Response</h3>
        <div class="panel-badge {response_badge}">
          {'● Speaking' if st.session_state.is_speaking else '○ Ready'}
        </div>
      </div>
      <div class="response-content">{clean_response}</div>
    
    </div>
    """
    st.markdown(panel_html, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Process Audio
# ---------------------------
def build_initial_state(audio_bytes):
    return {
        "audio_bytes": audio_bytes,
        "transcript": "",
        "response": "",
        "response_audio": b"",
        "error": "",
        "key_points": [],
        "suggested_actions": [],
        "verification_steps": [],
        "official_sources": [],
        "messages_history": st.session_state.voice_messages,
    }

if audio_bytes and audio_bytes != st.session_state.last_audio:
    st.session_state.last_audio = audio_bytes
    st.session_state.is_recording = False
    st.session_state.is_processing = True
    st.session_state.status = "Processing..."

    try:
        final_state = voice_graph.invoke(build_initial_state(audio_bytes))
        transcript = final_state.get("transcript", "")
        response = final_state.get("response", "")
        response_audio = final_state.get("response_audio", b"")
        error = final_state.get("error", "")

        if error:
            st.session_state.current_transcript = f"❌ {error}"
            st.session_state.status = "Error"
        else:
            st.session_state.current_transcript = transcript
            st.session_state.current_response = response
            st.session_state.current_metadata = {
                "key_points": final_state.get("key_points", []),
                "suggested_actions": final_state.get("suggested_actions", []),
                "verification_steps": final_state.get("verification_steps", []),
            }
            st.session_state.voice_messages.append({"role": "user", "content": transcript})
            st.session_state.voice_messages.append({"role": "assistant", "content": response})
            st.session_state.is_processing = False
            st.session_state.is_speaking = True
            st.session_state.status = "Speaking..."
            if response_audio:
                st.audio(response_audio, format="audio/mp3", autoplay=True)
                time.sleep(2)
            st.session_state.is_speaking = False
            st.session_state.status = "Ready"

        st.rerun()

    except Exception as e:
        st.session_state.current_transcript = f"❌ Error: {e}"
        st.session_state.status = "Error"
        st.session_state.is_processing = False
        st.rerun()

elif audio_bytes:
    if not st.session_state.is_recording and not st.session_state.is_processing:
        st.session_state.is_recording = True
        st.session_state.status = "Listening..."
        st.rerun()
else:
    if st.session_state.is_recording:
        st.session_state.is_recording = False
        st.session_state.status = "Ready"
        st.rerun()
