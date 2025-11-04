# voicebot.py
"""
Hajj Voice Assistant - PRODUCTION READY
- Fixed audio processing flow
- Fixed state management
- Robust error handling
"""

import time
import re
import streamlit as st
import sys
from pathlib import Path
import logging

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.voice_processor import VoiceProcessor
from core.voice_graph import VoiceGraphBuilder

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
st.markdown("""
<style>
.stApp {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  background-attachment: fixed;
  overflow: hidden !important;
  height: 100vh;
}
#MainMenu, footer, header {visibility: hidden;}
.main .block-container {
  padding: 0.75rem 1rem;
  max-width: 1400px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}
.voice-header{text-align:center;padding:0.75rem 0;margin-bottom:0.5rem;}
.voice-title{
  font-size:2.2rem;font-weight:800;letter-spacing:2px;
  background:linear-gradient(135deg,#60a5fa 0%,#a78bfa 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  margin-bottom:0.25rem;
}
.voice-subtitle{color:rgba(255,255,255,0.85);font-size:0.95rem;}
.voice-container{
  display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;
  flex:1;min-height:0;padding:0 1rem;
}
.voice-left{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  background:rgba(255,255,255,0.03);border-radius:2rem;padding:1.5rem;
  backdrop-filter:blur(20px);border:1px solid rgba(255,255,255,0.08);
  box-shadow:0 8px 32px rgba(0,0,0,0.25);overflow:hidden;
}
.voice-avatar{width:180px;height:180px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;font-size:90px;
  background:linear-gradient(135deg,#60a5fa 0%,#a78bfa 100%);
  box-shadow:0 20px 60px rgba(96,165,250,0.35);
  border:6px solid rgba(255,255,255,0.15);
  animation:float 3s ease-in-out infinite;
}
.voice-avatar.listening{animation:pulse-listening 0.8s infinite;box-shadow:0 0 80px rgba(96,165,250,0.8);}
.voice-avatar.speaking{animation:pulse-speaking 0.6s infinite;box-shadow:0 0 80px rgba(167,139,250,0.8);}
.voice-ring{position:absolute;border:3px solid rgba(96,165,250,0.3);
  border-radius:50%;top:50%;left:50%;transform:translate(-50%,-50%);
  animation:expand 3s ease-out infinite;
}
.voice-ring-1{width:200px;height:200px;animation-delay:0s;}
.voice-ring-2{width:240px;height:240px;animation-delay:1s;}
.voice-ring-3{width:280px;height:280px;animation-delay:2s;}
@keyframes float{0%,100%{transform:translateY(0);}50%{transform:translateY(-15px);}}
@keyframes pulse-listening{0%,100%{transform:scale(1);}50%{transform:scale(1.1);}}
@keyframes pulse-speaking{0%,100%{transform:scale(1);}50%{transform:scale(1.15);}}
@keyframes expand{0%{transform:translate(-50%,-50%) scale(0.8);opacity:0.8;}100%{transform:translate(-50%,-50%) scale(1.5);opacity:0;}}
.record-label{margin-top:1rem;color:white;font-weight:600;text-transform:uppercase;letter-spacing:1.5px;}
.voice-right{display:flex;flex-direction:column;gap:1rem;height:100%;min-height:0;overflow:hidden;}
.transcript-container,.response-container{
  background:rgba(255,255,255,0.04);border-radius:1.5rem;padding:1.25rem;
  backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,0.08);
  box-shadow:0 8px 32px rgba(0,0,0,0.22);flex:1;min-height:0;
  display:flex;flex-direction:column;overflow:hidden;
}
.panel-header{display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;
  padding-bottom:0.75rem;border-bottom:2px solid rgba(255,255,255,0.08);}
.panel-icon{font-size:1.75rem;}
.panel-title{font-size:1.2rem;font-weight:700;color:white;margin:0;}
.panel-badge{margin-left:auto;padding:0.3rem 0.8rem;border-radius:1rem;
  font-weight:600;font-size:0.75rem;background:rgba(96,165,250,0.16);
  color:#60a5fa;border:1px solid rgba(96,165,250,0.2);}
.panel-badge.active{background:rgba(34,197,94,0.16);color:#22c55e;
  border-color:rgba(34,197,94,0.25);animation:badge-pulse 1s infinite;}
@keyframes badge-pulse{0%,100%{opacity:1;}50%{opacity:0.6;}}
.transcript-text,.response-content{
  color:rgba(255,255,255,0.92);font-size:1.1rem;line-height:1.6;
  flex:1;overflow-y:auto;padding-right:0.5rem;
}
.transcript-text.empty,.response-content.empty{
  color:rgba(255,255,255,0.45);font-style:italic;overflow:hidden;
}
.metadata-card{background:rgba(255,255,255,0.03);border-radius:1rem;padding:0.9rem;
  margin-top:0.75rem;border-left:4px solid #60a5fa;}
.metadata-title{font-size:0.85rem;font-weight:600;color:#60a5fa;
  margin-bottom:0.5rem;text-transform:uppercase;letter-spacing:1px;}
.metadata-list{list-style:none;margin:0;padding:0;}
.metadata-list li{padding:0.25rem 0;color:rgba(255,255,255,0.85);}
.metadata-list li:before{content:"→ ";color:#60a5fa;font-weight:bold;margin-right:0.5rem;}
.status-indicator{position:fixed;top:15px;right:15px;padding:0.6rem 1.25rem;
  background:rgba(0,0,0,0.75);border-radius:2rem;color:white;font-weight:600;
  font-size:0.85rem;backdrop-filter:blur(10px);
  border:1px solid rgba(255,255,255,0.12);z-index:1000;
  display:flex;align-items:center;gap:0.5rem;
}
.status-dot{width:10px;height:10px;border-radius:50%;background:#22c55e;animation:dot-pulse 1.5s infinite;}
.status-dot.listening{background:#ef4444;}
.status-dot.speaking{background:#a78bfa;}
@keyframes dot-pulse{0%,100%{opacity:1;}50%{opacity:0.4;}}
@media (max-width:1024px){
  .voice-container{grid-template-columns:1fr;gap:1rem;}
  .voice-avatar{width:140px;height:140px;font-size:70px;}
}
</style>
""", unsafe_allow_html=True)

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
  <div>🕋<span class="voice-title"> Hajj Voice Assistant</span></div>
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

    audio_bytes = st.audio_input("Click to start recording", key="audio_input")

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
      {meta_html}
    </div>
    """
    st.markdown(panel_html, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Process Audio
# ---------------------------
# ---------------------------
# Process Audio
# ---------------------------
def build_initial_state(audio_bytes):
    """Build initial state for voice graph with all required fields"""
    return {
        "audio_bytes": audio_bytes,
        "transcript": "",
        "detected_language": "en",
        "transcription_confidence": 0.0,
        "user_input": "",
        "intent": "",
        "intent_confidence": 0.0,
        "intent_reasoning": "",
        "is_arabic": False,
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
        "messages_history": st.session_state.voice_messages,
    }

if audio_bytes:
    # Detect new recording
    if audio_bytes != st.session_state.last_audio and not st.session_state.is_processing:
        st.session_state.last_audio = audio_bytes
        st.session_state.is_recording = False
        st.session_state.is_processing = True
        st.session_state.status = "Processing..."
        st.rerun()  # Update UI

    # Process audio only once per recording
    if st.session_state.is_processing and audio_bytes == st.session_state.last_audio:
        try:
            logger.info("Starting audio processing")
            audio_data = audio_bytes.read() if hasattr(audio_bytes, "read") else audio_bytes

            if not audio_data:
                raise ValueError("Empty audio data received")

            # Invoke voice graph
            final_state = voice_graph.invoke(build_initial_state(audio_data))

            # Extract results safely
            transcript = final_state.get("transcript", "")
            response = final_state.get("response", "")
            response_audio = final_state.get("response_audio", b"")
            error = final_state.get("error", "")

            if error:
                st.session_state.current_transcript = f"❌ {error}"
                st.session_state.current_response = "Please try again."
                st.session_state.status = "Error"
            elif not transcript:
                st.session_state.current_transcript = "❌ No speech detected"
                st.session_state.current_response = "Please speak clearly and try again."
                st.session_state.status = "Ready"
            else:
                st.session_state.current_transcript = transcript
                st.session_state.current_response = response
                st.session_state.current_metadata = {
                    "key_points": final_state.get("key_points", []),
                    "suggested_actions": final_state.get("suggested_actions", []),
                    "verification_steps": final_state.get("verification_steps", []),
                }

                # Update conversation history
                if transcript:
                    st.session_state.voice_messages.append({"role": "user", "content": transcript})
                if response:
                    st.session_state.voice_messages.append({"role": "assistant", "content": response})

                # Play TTS if available
                if response_audio:
                    st.session_state.is_speaking = True
                    st.audio(response_audio, format="audio/mp3", autoplay=True)
                    st.session_state.is_speaking = False

                st.session_state.status = "Ready"

        except Exception as e:
            st.session_state.current_transcript = f"❌ Error: {str(e)}"
            st.session_state.current_response = "An error occurred. Please try again."
            st.session_state.status = "Error"
            logger.error(f"Audio processing error: {e}")

        finally:
            st.session_state.is_processing = False
            st.rerun()

else:
    # Reset recording state if no audio
    if st.session_state.is_recording:
        st.session_state.is_recording = False
        st.session_state.status = "Ready"
