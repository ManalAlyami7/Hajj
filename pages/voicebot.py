# voicebot.py
"""
Cleaned & rewritten Hajj Voice Assistant (single-file)
- Consolidated CSS, layout, and logic
- Keeps original visual design and features
"""
import time
import streamlit as st
from audio_recorder_streamlit import audio_recorder

# core modules (keep as in your project)
from core.voice_processor import VoiceProcessor
from core.voice_graph import VoiceGraphBuilder
from ui.voice_interface import VoiceInterface, RealTimeVoiceStyles
from utils.state import get_current_time

# ---------------------------
# Page config + Single CSS
# ---------------------------
st.set_page_config(
    page_title="Hajj Voice Assistant",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

CSS = r"""
<style>
/* --- consolidated CSS (keeps the original style & animations) --- */
.stApp {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  background-attachment: fixed;
  overflow: hidden !important;
  height: 100vh;
}
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }

.main .block-container {
  padding: 0.75rem 1rem;
  max-width: 1400px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* Header */
.voice-header { text-align: center; padding: 0.75rem 0; margin-bottom: 0.5rem; }
.voice-title {
  font-size: 2.2rem; font-weight: 800; letter-spacing: 2px;
  background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
  -webkit-background-clip: text; -webkit-text-fill-color: transparent;
  margin-bottom: 0.25rem;
}
.voice-subtitle { color: rgba(255,255,255,0.85); font-size: 0.95rem; }

/* Grid */
.voice-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  flex: 1;
  min-height: 0;
  padding: 0 1rem;
}

/* Left */
.voice-left {
  display:flex; flex-direction:column; align-items:center; justify-content:center;
  background: rgba(255,255,255,0.03); border-radius: 2rem; padding: 1.5rem;
  backdrop-filter: blur(20px); border: 1px solid rgba(255,255,255,0.08);
  box-shadow: 0 8px 32px rgba(0,0,0,0.25); overflow: hidden;
}
.voice-avatar { width:180px; height:180px; border-radius:50%; display:flex; align-items:center; justify-content:center; font-size:90px;
  background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%); box-shadow: 0 20px 60px rgba(96,165,250,0.35); border:6px solid rgba(255,255,255,0.15);
  animation: float 3s ease-in-out infinite;
}
.voice-avatar.listening { animation: pulse-listening 0.8s infinite; box-shadow: 0 0 80px rgba(96,165,250,0.8); }
.voice-avatar.speaking { animation: pulse-speaking 0.6s infinite; box-shadow: 0 0 80px rgba(167,139,250,0.8); }
.voice-ring { position:absolute; border:3px solid rgba(96,165,250,0.3); border-radius:50%; top:50%; left:50%; transform:translate(-50%,-50%); animation: expand 3s ease-out infinite; }
.voice-ring-1{ width:200px;height:200px; animation-delay:0s;}
.voice-ring-2{ width:240px;height:240px; animation-delay:1s;}
.voice-ring-3{ width:280px;height:280px; animation-delay:2s;}

@keyframes float{0%,100%{transform:translateY(0);}50%{transform:translateY(-15px);}}
@keyframes pulse-listening{0%,100%{transform:scale(1);}50%{transform:scale(1.1);}}
@keyframes pulse-speaking{0%,100%{transform:scale(1);}50%{transform:scale(1.15);}}
@keyframes expand{0%{transform:translate(-50%,-50%) scale(0.8);opacity:0.8;}100%{transform:translate(-50%,-50%) scale(1.5);opacity:0;}}

/* Record button (visual only - actual recording handled by audio_recorder) */
.record-button-container { margin-top: 1rem; }
.record-label { margin-top:1rem; color:white; font-weight:600; text-transform:uppercase; letter-spacing:1.5px; }

/* Right */
.voice-right { display:flex; flex-direction:column; gap:1rem; height:100%; min-height:0; overflow:hidden; }

.transcript-container, .response-container {
  background: rgba(255,255,255,0.04); border-radius:1.5rem; padding:1.25rem; backdrop-filter: blur(18px);
  border: 1px solid rgba(255,255,255,0.08); box-shadow: 0 8px 32px rgba(0,0,0,0.22); flex:1; min-height:0; display:flex; flex-direction:column; overflow:hidden;
}
.panel-header { display:flex; align-items:center; gap:0.75rem; margin-bottom:0.75rem; padding-bottom:0.75rem; border-bottom:2px solid rgba(255,255,255,0.08); }
.panel-icon { font-size:1.75rem; }
.panel-title { font-size:1.2rem; font-weight:700; color:white; margin:0; }
.panel-badge { margin-left:auto; padding:0.3rem 0.8rem; border-radius:1rem; font-weight:600; font-size:0.75rem; background: rgba(96,165,250,0.16); color:#60a5fa; border:1px solid rgba(96,165,250,0.2); }
.panel-badge.active { background: rgba(34,197,94,0.16); color:#22c55e; border-color: rgba(34,197,94,0.25); animation: badge-pulse 1s infinite; }
@keyframes badge-pulse{0%,100%{opacity:1;}50%{opacity:0.6;}}

.transcript-text, .response-content { color: rgba(255,255,255,0.92); font-size:1.1rem; line-height:1.6; flex:1; overflow-y:auto; padding-right:0.5rem; }
.transcript-text.empty, .response-content.empty { color: rgba(255,255,255,0.45); font-style:italic; overflow:hidden; }

.metadata-card { background: rgba(255,255,255,0.03); border-radius:1rem; padding:0.9rem; margin-top:0.75rem; border-left:4px solid #60a5fa; }
.metadata-title { font-size:0.85rem; font-weight:600; color:#60a5fa; margin-bottom:0.5rem; text-transform:uppercase; letter-spacing:1px; }
.metadata-list { list-style:none; margin:0; padding:0; }
.metadata-list li { padding:0.25rem 0; color: rgba(255,255,255,0.85); }
.metadata-list li:before { content:"→ "; color:#60a5fa; font-weight:bold; margin-right:0.5rem; }

/* Status indicator */
.status-indicator { position:fixed; top:15px; right:15px; padding:0.6rem 1.25rem; background: rgba(0,0,0,0.75); border-radius:2rem; color:white; font-weight:600; font-size:0.85rem; backdrop-filter: blur(10px); border:1px solid rgba(255,255,255,0.12); z-index:1000; display:flex; align-items:center; gap:0.5rem; }
.status-dot { width:10px; height:10px; border-radius:50%; background:#22c55e; animation: dot-pulse 1.5s infinite; }
.status-dot.listening { background:#ef4444; }
.status-dot.speaking { background:#a78bfa; }
@keyframes dot-pulse{0%,100%{opacity:1;}50%{opacity:0.4;}}

/* Responsive */
@media (max-width:1024px) {
  .voice-container { grid-template-columns: 1fr; gap:1rem; }
  .voice-avatar { width:140px; height:140px; font-size:70px;}
  .voice-ring-1{width:160px;height:160px;}
  .voice-ring-2{width:190px;height:190px;}
  .voice-ring-3{width:220px;height:220px;}
}
</style>
"""

st.markdown(CSS, unsafe_allow_html=True)

# ---------------------------
# Helper: initialize voice system
# ---------------------------
@st.cache_resource
def initialize_voice_system():
    processor = VoiceProcessor()
    graph_builder = VoiceGraphBuilder(processor)
    graph = graph_builder.build()
    return processor, graph

voice_processor, voice_graph = initialize_voice_system()

# ---------------------------
# Session state defaults
# ---------------------------
def init_session_state():
    defaults = {
        "voice_messages": [],
        "last_audio": None,
        "is_recording": False,
        "is_processing": False,
        "is_speaking": False,
        "current_transcript": "",
        "current_response": "",
        "current_metadata": {},
        "status": "Ready"
    }
    for k, v in defaults.items():
        if k not in st.session_state:
            st.session_state[k] = v

init_session_state()

# ---------------------------
# UI rendering helpers
# ---------------------------
def render_header():
    st.markdown(
        """
        <div class="voice-header">
            <div class="voice-title">🕋 Hajj Voice Assistant</div>
            <div class="voice-subtitle">Real-time Speech Recognition & AI Responses</div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def render_status_indicator():
    status_dot_class = ""
    if st.session_state.is_recording:
        status_dot_class = "listening"
    elif st.session_state.is_speaking:
        status_dot_class = "speaking"
    st.markdown(
        f"""
        <div class="status-indicator">
            <div class="status-dot {status_dot_class}"></div>
            <span>{st.session_state.status}</span>
        </div>
        """,
        unsafe_allow_html=True,
    )

def left_panel_render():
    avatar_class = ""
    if st.session_state.is_recording:
        avatar_class = "listening"
    elif st.session_state.is_speaking:
        avatar_class = "speaking"

    st.markdown(
        f"""
        <div class="voice-left" style="position:relative;">
            <div style="position:relative;">
                <div class="voice-ring voice-ring-1"></div>
                <div class="voice-ring voice-ring-2"></div>
                <div class="voice-ring voice-ring-3"></div>
                <div class="voice-avatar {avatar_class}">🕋</div>
            </div>

            <div class="record-button-container">
                <div class="record-label">{'🔴 Recording...' if st.session_state.is_recording else '🎤 Press to Speak'}</div>
            </div>
        </div>
        """,
        unsafe_allow_html=True,
    )

def right_panel_render():
    # Transcript
    transcript_badge_class = "active" if st.session_state.is_recording or st.session_state.is_processing else ""
    transcript_text = st.session_state.current_transcript or "Speak now..."
    transcript_class = "" if st.session_state.current_transcript else "empty"

    # Response
    response_badge_class = "active" if st.session_state.is_speaking else ""
    response_text = st.session_state.current_response or "Response will appear here..."
    response_class = "" if st.session_state.current_response else "empty"

    # Build metadata HTML
    metadata_html = ""
    meta = st.session_state.current_metadata or {}
    if meta:
        if meta.get("key_points"):
            points = "".join([f"<li>{p}</li>" for p in meta["key_points"]])
            metadata_html += f"""
            <div class="metadata-card">
                <div class="metadata-title">💡 Key Points</div>
                <ul class="metadata-list">{points}</ul>
            </div>
            """
        if meta.get("suggested_actions"):
            actions = "".join([f"<li>{a}</li>" for a in meta["suggested_actions"]])
            metadata_html += f"""
            <div class="metadata-card" style="border-left-color:#a78bfa;">
                <div class="metadata-title" style="color:#a78bfa;">✅ Suggested Actions</div>
                <ul class="metadata-list">{actions}</ul>
            </div>
            """
        if meta.get("verification_steps"):
            steps = "".join([f"<li>{s}</li>" for s in meta["verification_steps"]])
            metadata_html += f"""
            <div class="metadata-card" style="border-left-color:#ef4444;">
                <div class="metadata-title" style="color:#ef4444;">⚠️ Verification Steps</div>
                <ul class="metadata-list">{steps}</ul>
            </div>
            """

    st.markdown(
        f"""
        <div class="transcript-container">
            <div class="panel-header">
                <div class="panel-icon">🎤</div>
                <h3 class="panel-title">Live Transcript</h3>
                <div class="panel-badge {transcript_badge_class}">
                    {'●' if transcript_badge_class else '○'} {'Listening' if st.session_state.is_recording else 'Transcribing' if st.session_state.is_processing else 'Ready'}
                </div>
            </div>
            <div class="transcript-text {transcript_class}">{transcript_text}</div>
        </div>

        <div class="response-container" style="margin-top:1rem;">
            <div class="panel-header">
                <div class="panel-icon">🤖</div>
                <h3 class="panel-title">AI Response</h3>
                <div class="panel-badge {response_badge_class}">
                    {'●' if response_badge_class else '○'} {'Speaking' if st.session_state.is_speaking else 'Ready'}
                </div>
            </div>
            <div class="response-content {response_class}">{response_text}</div>
            {metadata_html}
        </div>
        """,
        unsafe_allow_html=True,
    )

# ---------------------------
# Rendering layout
# ---------------------------
render_header()
render_status_indicator()

# two columns inside grid
st.markdown('<div class="voice-container">', unsafe_allow_html=True)
col_left, col_right = st.columns(2)

with col_left:
    left_panel_render()
    # Hidden audio recorder (visual button is still the recorder)
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

with col_right:
    right_panel_render()

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------
# Audio processing & graph invocation
# ---------------------------
def build_initial_state(audio_bytes):
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
        "response_tone": "warm",
        "key_points": [],
        "suggested_actions": [],
        "includes_warning": False,
        "verification_steps": [],
        "official_sources": [],
        "response_audio": b"",
        "error": "",
        "messages_history": st.session_state.voice_messages,
    }

def handle_final_state(final_state):
    transcript = final_state.get("transcript", "")
    response = final_state.get("response", "")
    response_audio = final_state.get("response_audio", b"")
    error = final_state.get("error", "")
    metadata = {
        "intent": final_state.get("intent", ""),
        "confidence": final_state.get("intent_confidence", 0.0),
        "tone": final_state.get("response_tone", "warm"),
        "urgency": final_state.get("urgency", "low"),
        "key_points": final_state.get("key_points", []),
        "suggested_actions": final_state.get("suggested_actions", []),
        "verification_steps": final_state.get("verification_steps", []),
        "official_sources": final_state.get("official_sources", []),
    }

    if error:
        st.session_state.status = "Error"
        st.session_state.current_transcript = f"❌ {error}"
        st.session_state.is_processing = False
    elif transcript and response:
        st.session_state.current_transcript = transcript
        st.session_state.current_response = response
        st.session_state.current_metadata = metadata
        st.session_state.voice_messages.append({"role": "user", "content": transcript})
        st.session_state.voice_messages.append({"role": "assistant", "content": response})
        st.session_state.is_processing = False
        st.session_state.is_speaking = True
        st.session_state.status = "Speaking..."
        if response_audio:
            try:
                st.audio(response_audio, format="audio/mp3", autoplay=True)
            except Exception:
                # fallback: attempt to play if bytes are raw wav/mp3
                try:
                    st.audio(response_audio)
                except Exception:
                    pass
            # estimate speaking time (cap small)
            words = len(response.split())
            speak_time = (words / 150) * 60
            time.sleep(min(speak_time, 3))  # short pause to improve UX
        # finish speaking
        st.session_state.is_speaking = False
        st.session_state.status = "Ready"

# main processing logic
if audio_bytes and audio_bytes != st.session_state.last_audio:
    st.session_state.last_audio = audio_bytes
    st.session_state.is_recording = False
    st.session_state.is_processing = True
    st.session_state.status = "Processing..."

    initial_state = build_initial_state(audio_bytes)

    try:
        final_state = voice_graph.invoke(initial_state)
        handle_final_state(final_state)
        # rerun to update UI immediately
        st.rerun()
    except Exception as e:
        st.session_state.status = "Error"
        st.session_state.current_transcript = f"❌ Error: {str(e)}"
        st.session_state.is_processing = False
        st.rerun()

# update recording flags when audio_bytes exists but didn't change
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
