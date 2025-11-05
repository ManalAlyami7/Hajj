<<<<<<< HEAD
=======
"""
Hajj Voice Assistant - PRODUCTION READY
- Fixed audio processing flow with audio_recorder
- UI updates BEFORE TTS playback
- Robust error handling
- Beautiful design without white rectangle
- Custom styled microphone button
"""
>>>>>>> 172c648 (Update: Improve voicebot behavior)



import re

import streamlit as st
import sys
from pathlib import Path
import logging
import hashlib
import queue
import threading
from audio_recorder_streamlit import audio_recorder

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Ensure project root is on sys.path
ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from core.voice_processor import VoiceProcessor

# ---------------------------
# Streamlit Config
# ---------------------------
st.set_page_config(
    page_title="Hajj Voice Assistant - Live",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# ---------------------------
<<<<<<< HEAD
# Styles (unchanged)
=======
# Styles - Enhanced Design
>>>>>>> 172c648 (Update: Improve voicebot behavior)
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

/* Hide ALL Streamlit default widgets styling */
.stAudioInput, 
div[data-testid="stAudioInput"],
.stAudioInput > div,
div[data-baseweb="audio-input"] {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
  margin: 0 !important;
}

/* Force audio recorder to be transparent */
.audio-recorder-streamlit,
.audio-recorder-streamlit > div {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

/* Return Button Styles */
.return-button-container {
  position: fixed;
  top: 20px;
  left: 20px;
  z-index: 2000;
}

.return-button {
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
}

.return-button:hover {
  background: rgba(96, 165, 250, 0.25);
  border-color: rgba(96, 165, 250, 0.5);
  transform: translateX(-5px);
  box-shadow: 0 6px 30px rgba(96, 165, 250, 0.4);
  color: #93c5fd;
}

.return-button .icon {
  font-size: 1.2rem;
  transition: transform 0.3s ease;
}

.return-button:hover .icon {
  transform: translateX(-3px);
}

.voice-header {
  text-align: center;
  padding: 0.75rem 0;
  margin-bottom: 0.5rem;
}

.voice-title {
  font-size: 2.2rem;
  font-weight: 800;
  letter-spacing: 2px;
  background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
  -webkit-background-clip: text;
  -webkit-text-fill-color: transparent;
  margin-bottom: 0.25rem;
}

.voice-subtitle {
  color: rgba(255, 255, 255, 0.85);
  font-size: 0.95rem;
}

.voice-container {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 1.5rem;
  flex: 1;
  min-height: 0;
  padding: 0 1rem;
}
<<<<<<< HEAD
.voice-avatar.listening{animation:pulse-listening 0.8s infinite;box-shadow:0 0 80px rgba(96,165,250,0.8);}
.voice-avatar.speaking{animation:pulse-speaking 0.6s infinite;box-shadow:0 0 80px rgba(167,139,250,0.8);}
.voice-avatar.processing{animation:rotate-processing 2s linear infinite;box-shadow:0 0 60px rgba(251,191,36,0.6);}
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
@keyframes rotate-processing{0%{transform:rotate(0deg);}100%{transform:rotate(360deg);}}
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
.panel-badge.streaming{background:rgba(251,191,36,0.16);color:#fbbf24;
  border-color:rgba(251,191,36,0.25);animation:badge-pulse 1s infinite;}
@keyframes badge-pulse{0%,100%{opacity:1;}50%{opacity:0.6;}}
.transcript-text,.response-content{
  color:rgba(255,255,255,0.92);font-size:1.1rem;line-height:1.6;
  flex:1;overflow-y:auto;padding-right:0.5rem;
=======

.voice-left {
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
}

.voice-avatar {
  width: 200px;
  height: 200px;
  border-radius: 50%;
  display: flex;
  align-items: center;
  justify-content: center;
  font-size: 100px;
  background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
  box-shadow: 0 20px 60px rgba(96, 165, 250, 0.35);
  border: 6px solid rgba(255, 255, 255, 0.15);
  animation: float 3s ease-in-out infinite;
  position: relative;
  z-index: 10;
}

.voice-avatar.listening {
  animation: pulse-listening 0.8s infinite;
  box-shadow: 0 0 80px rgba(96, 165, 250, 0.8);
>>>>>>> 172c648 (Update: Improve voicebot behavior)
}

.voice-avatar.speaking {
  animation: pulse-speaking 0.6s infinite;
  box-shadow: 0 0 80px rgba(167, 139, 250, 0.8);
}
<<<<<<< HEAD
/* Streaming cursor effect */
.streaming-text::after {
  content: '▋';
  animation: blink 1s infinite;
  color: #60a5fa;
}
@keyframes blink {
  0%, 50% { opacity: 1; }
  51%, 100% { opacity: 0; }
}
/* Live indicator */
.live-indicator {
  display: inline-flex;
  align-items: center;
  gap: 0.5rem;
  padding: 0.25rem 0.75rem;
  background: rgba(239, 68, 68, 0.16);
  border: 1px solid rgba(239, 68, 68, 0.3);
  border-radius: 1rem;
  color: #ef4444;
  font-size: 0.75rem;
  font-weight: 600;
}
.live-dot {
  width: 8px;
  height: 8px;
  border-radius: 50%;
  background: #ef4444;
  animation: live-pulse 1.5s infinite;
}
@keyframes live-pulse {
  0%, 100% { opacity: 1; transform: scale(1); }
  50% { opacity: 0.5; transform: scale(1.2); }
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
.status-dot.processing{background:#fbbf24;}
.status-dot.speaking{background:#a78bfa;}
@keyframes dot-pulse{0%,100%{opacity:1;}50%{opacity:0.4;}}
@media (max-width:1024px){
  .voice-container{grid-template-columns:1fr;gap:1rem;}
  .voice-avatar{width:140px;height:140px;font-size:70px;}
  .return-button-container {
    top: 10px;
    left: 10px;
=======

.voice-ring {
  position: absolute;
  border: 3px solid rgba(96, 165, 250, 0.3);
  border-radius: 50%;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  animation: expand 3s ease-out infinite;
  z-index: 5;
}

.voice-ring-1 {
  width: 220px;
  height: 220px;
  animation-delay: 0s;
}

.voice-ring-2 {
  width: 270px;
  height: 270px;
  animation-delay: 1s;
}

.voice-ring-3 {
  width: 320px;
  height: 320px;
  animation-delay: 2s;
}

@keyframes float {
  0%, 100% { transform: translateY(0); }
  50% { transform: translateY(-15px); }
}

@keyframes pulse-listening {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.1); }
}

@keyframes pulse-speaking {
  0%, 100% { transform: scale(1); }
  50% { transform: scale(1.15); }
}

@keyframes expand {
  0% {
    transform: translate(-50%, -50%) scale(0.8);
    opacity: 0.8;
>>>>>>> 172c648 (Update: Improve voicebot behavior)
  }
  100% {
    transform: translate(-50%, -50%) scale(1.5);
    opacity: 0;
  }
}

.record-label {
  margin-top: 1.5rem;
  color: white;
  font-weight: 600;
  text-transform: uppercase;
  letter-spacing: 1.5px;
  font-size: 0.9rem;
  z-index: 20;
}

.voice-right {
  display: flex;
  flex-direction: column;
  gap: 1rem;
  height: 100%;
  min-height: 0;
  overflow: hidden;
}

.transcript-container, .response-container {
  background: rgba(255, 255, 255, 0.04);
  border-radius: 1.5rem;
  padding: 1.25rem;
  backdrop-filter: blur(18px);
  border: 1px solid rgba(255, 255, 255, 0.08);
  box-shadow: 0 8px 32px rgba(0, 0, 0, 0.22);
  flex: 1;
  min-height: 0;
  display: flex;
  flex-direction: column;
  overflow: hidden;
}

.panel-header {
  display: flex;
  align-items: center;
  gap: 0.75rem;
  margin-bottom: 0.75rem;
  padding-bottom: 0.75rem;
  border-bottom: 2px solid rgba(255, 255, 255, 0.08);
}

.panel-icon {
  font-size: 1.75rem;
}

.panel-title {
  font-size: 1.2rem;
  font-weight: 700;
  color: white;
  margin: 0;
}

.panel-badge {
  margin-left: auto;
  padding: 0.3rem 0.8rem;
  border-radius: 1rem;
  font-weight: 600;
  font-size: 0.75rem;
  background: rgba(96, 165, 250, 0.16);
  color: #60a5fa;
  border: 1px solid rgba(96, 165, 250, 0.2);
}

.panel-badge.active {
  background: rgba(34, 197, 94, 0.16);
  color: #22c55e;
  border-color: rgba(34, 197, 94, 0.25);
  animation: badge-pulse 1s infinite;
}

@keyframes badge-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.6; }
}

.transcript-text, .response-content {
  color: rgba(255, 255, 255, 0.92);
  font-size: 1.1rem;
  line-height: 1.6;
  flex: 1;
  overflow-y: auto;
  padding-right: 0.5rem;
}

.transcript-text.empty, .response-content.empty {
  color: rgba(255, 255, 255, 0.45);
  font-style: italic;
  overflow: hidden;
}

.metadata-card {
  background: rgba(255, 255, 255, 0.03);
  border-radius: 1rem;
  padding: 0.9rem;
  margin-top: 0.75rem;
  border-left: 4px solid #60a5fa;
}

.metadata-title {
  font-size: 0.85rem;
  font-weight: 600;
  color: #60a5fa;
  margin-bottom: 0.5rem;
  text-transform: uppercase;
  letter-spacing: 1px;
}

.metadata-list {
  list-style: none;
  margin: 0;
  padding: 0;
}

.metadata-list li {
  padding: 0.25rem 0;
  color: rgba(255, 255, 255, 0.85);
}

.metadata-list li:before {
  content: "→ ";
  color: #60a5fa;
  font-weight: bold;
  margin-right: 0.5rem;
}

.status-indicator {
  position: fixed;
  top: 15px;
  right: 15px;
  padding: 0.6rem 1.25rem;
  background: rgba(0, 0, 0, 0.75);
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
}

.status-dot {
  width: 10px;
  height: 10px;
  border-radius: 50%;
  background: #22c55e;
  animation: dot-pulse 1.5s infinite;
}

.status-dot.listening {
  background: #ef4444;
}

.status-dot.speaking {
  background: #a78bfa;
}

@keyframes dot-pulse {
  0%, 100% { opacity: 1; }
  50% { opacity: 0.4; }
}

/* Hide audio element completely */
audio {
  display: none !important;
  visibility: hidden !important;
  height: 0 !important;
  width: 0 !important;
  overflow: hidden !important;
  position: absolute !important;
  left: -9999px !important;
}

/* Audio Recorder Custom Container - Make it transparent */
.audio-recorder-container {
  display: flex;
  justify-content: center;
  align-items: center;
  margin: 0;
  padding: 0;
  position: absolute;
  top: 50%;
  left: 50%;
  transform: translate(-50%, -50%);
  z-index: 30;
  background: transparent !important;
  border: none !important;
}

/* Force audio recorder component to be fully transparent */
.audio-recorder-container > div,
.audio-recorder-container > div > div,
.audio-recorder-container iframe {
  background: transparent !important;
  border: none !important;
  box-shadow: none !important;
}

/* Streamlit specific overrides */
[data-testid="stAudioInput"],
[data-testid="stAudioInput"] > div,
.stAudioInput,
.stAudioInput > div {
  background: transparent !important;
  border: none !important;
  padding: 0 !important;
  margin: 0 !important;
}

@media (max-width: 1024px) {
  .voice-container {
    grid-template-columns: 1fr;
    gap: 1rem;
  }
  
  .voice-avatar {
    width: 160px;
    height: 160px;
    font-size: 80px;
  }
  
  .voice-ring-1 {
    width: 180px;
    height: 180px;
  }
  
  .voice-ring-2 {
    width: 220px;
    height: 220px;
  }
  
  .voice-ring-3 {
    width: 260px;
    height: 260px;
  }
  
  .return-button-container {
    top: 10px;
    left: 10px;
  }
  
  .return-button {
    padding: 0.6rem 1.2rem;
    font-size: 0.85rem;
  }
}
/* Waveform animation for listening */
.waveform {
  display: flex;
  align-items: center;
  justify-content: center;
  gap: 3px;
  height: 40px;
  margin-top: 1rem;
}
.waveform-bar {
  width: 4px;
  background: linear-gradient(180deg, #60a5fa, #a78bfa);
  border-radius: 2px;
  animation: waveform 1s ease-in-out infinite;
}
.waveform-bar:nth-child(1) { animation-delay: 0s; }
.waveform-bar:nth-child(2) { animation-delay: 0.1s; }
.waveform-bar:nth-child(3) { animation-delay: 0.2s; }
.waveform-bar:nth-child(4) { animation-delay: 0.3s; }
.waveform-bar:nth-child(5) { animation-delay: 0.4s; }
@keyframes waveform {
  0%, 100% { height: 10px; }
  50% { height: 30px; }
}
</style>
""", unsafe_allow_html=True)

# ---------------------------
# Init components
# ---------------------------
@st.cache_resource
def initialize_voice_system():
    return VoiceProcessor()

voice_processor = initialize_voice_system()

def _hash_bytes(b: bytes) -> str:
    """Generate hash for audio bytes"""
    return hashlib.sha256(b).hexdigest()

# ---------------------------
# Session State
# ---------------------------
defaults = {
    "voice_messages": [],
    "last_audio_hash": None,
    "is_recording": False,
    "is_processing": False,
    "is_speaking": False,
    "pending_audio": None,  # Store audio to play after UI update
    "current_transcript": "",
    "current_response": "",
    "streaming_response": "",
    "current_metadata": {},
    "status": "Ready",
    "language": "en",
    "show_live_indicator": False,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

<<<<<<< HEAD
   
=======
# ---------------------------
# Return Button (Top Left)
# ---------------------------
st.markdown("""
<div class="return-button-container">
  <a href="/" class="return-button" target="_self">
    <span class="icon">←</span>
    <span>العودة للدردشة</span>
  </a>
</div>
""", unsafe_allow_html=True)
>>>>>>> 172c648 (Update: Improve voicebot behavior)

   # 
st.markdown("""
<div class="voice-header">
<<<<<<< HEAD
  <div>🕋<span class="voice-title"> Hajj Voice Assistant</span> <span style="font-size:0.7em;color:#60a5fa;">LIVE</span></div>
  <div class="voice-subtitle">Real-time Speech Recognition & Streaming AI Responses</div>
=======
  <div>🕋<span class="voice-title"> مساعد الحج الصوتي</span></div>
  <div class="voice-subtitle">التعرف على الكلام في الوقت الفعلي واستجابات الذكاء الاصطناعي</div>
>>>>>>> 172c648 (Update: Improve voicebot behavior)
</div>
""", unsafe_allow_html=True)

# Status Indicator
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
# Main Layout
# ---------------------------
st.markdown('<div class="voice-container">', unsafe_allow_html=True)
col_left, col_right = st.columns(2)

# Left: Avatar + Recorder
with col_left:
    avatar_class = (
        "listening" if st.session_state.is_recording
        else "speaking" if st.session_state.is_speaking
        else "processing" if st.session_state.is_processing
        else ""
    )
    
    # Waveform display when listening
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
    
    st.markdown(f"""
    <div class="voice-left">
      <div style="position:relative; width: 100%; height: 300px; display: flex; align-items: center; justify-content: center;">
        <div class="voice-ring voice-ring-1"></div>
        <div class="voice-ring voice-ring-2"></div>
        <div class="voice-ring voice-ring-3"></div>
        <div class="voice-avatar {avatar_class}">🕋</div>
        <div class="audio-recorder-container">
          <!-- Audio recorder will be inserted here -->
        </div>
      </div>
      <div class="record-label">
<<<<<<< HEAD
        {'🔴 Recording...' if st.session_state.is_recording 
         else '⚙️ Processing...' if st.session_state.is_processing
         else '🔊 Speaking...' if st.session_state.is_speaking
         else '🎤 Press to Speak'}
=======
        {'🔴 جاري التسجيل...' if st.session_state.is_recording else '🎤 اضغط للتحدث'}
>>>>>>> 172c648 (Update: Improve voicebot behavior)
      </div>
      {waveform_html}
    </div>
    """, unsafe_allow_html=True)

    # Audio Recorder Component - Injected into the container above
    audio_bytes = audio_recorder(
        text="",
        recording_color="#ef4444",
        neutral_color="#60a5fa",
        icon_name="microphone",
        icon_size="3x",
        key="audio_recorder"
    )

# Right: Transcript + Response
with col_right:
<<<<<<< HEAD
    # Transcript Panel
    transcript_badge_class = ""
    transcript_badge_text = "○ Ready"
    
    if st.session_state.is_recording:
        transcript_badge_class = "active"
        transcript_badge_text = "● Recording"
    elif st.session_state.is_processing:
        transcript_badge_class = "streaming"
        transcript_badge_text = "⚙ Processing"
    
    transcript = st.session_state.current_transcript or "Speak now..."
=======
    transcript_badge = "active" if st.session_state.is_recording or st.session_state.is_processing else ""
    transcript = st.session_state.current_transcript or "تحدث الآن..."
    response_badge = "active" if st.session_state.is_speaking else ""
    response_text = st.session_state.current_response or "سيظهر الرد هنا..."

    # Clean any HTML tags
    clean_response = re.sub(r"<.*?>", "", response_text)
>>>>>>> 172c648 (Update: Improve voicebot behavior)
    clean_transcript = re.sub(r"<.*?>", "", transcript)
    
    # Add streaming class if processing
    transcript_class = "streaming-text" if st.session_state.is_processing else ""
    
    # Response Panel
    response_badge_class = ""
    response_badge_text = "○ Ready"
    
    if st.session_state.is_streaming_response:
        response_badge_class = "streaming"
        response_badge_text = "⚡ Streaming"
        response_text = st.session_state.streaming_response
    elif st.session_state.is_speaking:
        response_badge_class = "active"
        response_badge_text = "🔊 Speaking"
        response_text = st.session_state.current_response
    else:
        response_text = st.session_state.current_response or "Response will appear here..."
    
    clean_response = re.sub(r"<.*?>", "", response_text)
    response_class = "streaming-text" if st.session_state.is_streaming_response else ""
    
    # Build Metadata HTML
    meta_html_parts = []
    meta = st.session_state.current_metadata

    if meta:
        if meta.get("key_points"):
            key_points_html = "".join(f"<li>{re.escape(str(p))}</li>" for p in meta["key_points"])
            meta_html_parts.append(f"""
            <div class="metadata-card">
                <div class="metadata-title">💡 النقاط الرئيسية</div>
                <ul class="metadata-list">{key_points_html}</ul>
            </div>
            """)

        if meta.get("suggested_actions"):
            suggested_html = "".join(f"<li>{re.escape(str(a))}</li>" for a in meta["suggested_actions"])
            meta_html_parts.append(f"""
            <div class="metadata-card" style="border-left-color:#a78bfa;">
                <div class="metadata-title" style="color:#a78bfa;">✅ الإجراءات المقترحة</div>
                <ul class="metadata-list">{suggested_html}</ul>
            </div>
            """)

        if meta.get("verification_steps"):
            verify_html = "".join(f"<li>{re.escape(str(s))}</li>" for s in meta["verification_steps"])
            meta_html_parts.append(f"""
            <div class="metadata-card" style="border-left-color:#ef4444;">
                <div class="metadata-title" style="color:#ef4444;">⚠️ خطوات التحقق</div>
                <ul class="metadata-list">{verify_html}</ul>
            </div>
            """)

    meta_html = "".join(meta_html_parts)

    # Display Panels
    panel_html = f"""
    <div class="transcript-container">
      <div class="panel-header">
        <div class="panel-icon">🎤</div>
<<<<<<< HEAD
        <h3 class="panel-title">Live Transcript</h3>
        <div class="panel-badge {transcript_badge_class}">{transcript_badge_text}</div>
=======
        <h3 class="panel-title">النص المباشر</h3>
        <div class="panel-badge {transcript_badge}">
          {'● جاري الاستماع' if st.session_state.is_recording else '○ جاهز'}
        </div>
>>>>>>> 172c648 (Update: Improve voicebot behavior)
      </div>
      <div class="transcript-text {transcript_class}">{clean_transcript}</div>
    </div>
    <div class="response-container" style="margin-top:1rem;">
      <div class="panel-header">
        <div class="panel-icon">🤖</div>
<<<<<<< HEAD
        <h3 class="panel-title">AI Response</h3>
        <div class="panel-badge {response_badge_class}">{response_badge_text}</div>
=======
        <h3 class="panel-title">رد الذكاء الاصطناعي</h3>
        <div class="panel-badge {response_badge}">
          {'● يتحدث' if st.session_state.is_speaking else '○ جاهز'}
        </div>
>>>>>>> 172c648 (Update: Improve voicebot behavior)
      </div>
      <div class="response-content {response_class}">{clean_response}</div>
      {meta_html}
    </div>
    """
    st.markdown(panel_html, unsafe_allow_html=True)

st.markdown("</div>", unsafe_allow_html=True)

# ---------------------------
# Play Pending Audio (AFTER UI is rendered)
# ---------------------------
if st.session_state.pending_audio:
    logger.info("Playing pending audio response...")
    
    st.markdown("<div style='display:none'>", unsafe_allow_html=True)
    st.audio(st.session_state.pending_audio, format="audio/mp3", autoplay=True)
    st.markdown("</div>", unsafe_allow_html=True)
    
    st.session_state.pending_audio = None
    st.session_state.is_speaking = False
    st.session_state.status = "جاهز"

# ---------------------------
# Process Audio with Real-Time Updates
# ---------------------------
if audio_bytes:
    audio_hash = _hash_bytes(audio_bytes)
    
    if audio_hash != st.session_state.last_audio_hash and not st.session_state.is_processing:
        logger.info(f"New audio detected: {audio_hash[:8]}...")
        
        st.session_state.last_audio_hash = audio_hash
        st.session_state.is_recording = False
        st.session_state.is_processing = True
<<<<<<< HEAD
        st.session_state.status = "Transcribing..."
        st.session_state.current_metadata = {}
=======
        st.session_state.status = "جاري معالجة الصوت..."
>>>>>>> 172c648 (Update: Improve voicebot behavior)
        
        try:
            # Step 1: Transcribe audio
            logger.info("Transcribing audio...")
            transcription_result = voice_processor.transcribe_audio(audio_bytes)
            
            transcript = transcription_result.get("text", "")
            language = transcription_result.get("language", "en")
            
<<<<<<< HEAD
            if not transcript:
                logger.warning("No speech detected")
                st.session_state.current_transcript = "❌ No speech detected"
                st.session_state.current_response = "Please speak clearly and try again."
                st.session_state.status = "Ready"
                st.session_state.is_processing = False
                st.rerun()
            
            # Update transcript immediately
            st.session_state.current_transcript = transcript
            st.session_state.language = language
            st.session_state.status = "Analyzing intent..."
            st.rerun()
            
            # Step 2: Detect intent
            logger.info("Detecting intent...")
            intent_result = voice_processor.detect_voice_intent(transcript, language)
            intent = intent_result.get("intent", "GENERAL_HAJJ")
            is_arabic = intent_result.get("is_arabic", False)
            
            st.session_state.status = "Generating response..."
            st.rerun()
            
            # Step 3: Generate response based on intent
            logger.info(f"Generating {intent} response...")
            
            if intent == "GREETING":
                result = voice_processor.generate_voice_greeting(transcript, is_arabic)
                response_text = result["response"]
=======
            # Extract results
            transcript = final_state.get("transcript", "")
            response = final_state.get("response", "")
            response_audio = final_state.get("response_audio", b"")
            error = final_state.get("error", "")
            
            if error:
                logger.error(f"Voice graph error: {error}")
                st.session_state.current_transcript = f"❌ {error}"
                st.session_state.current_response = "يرجى المحاولة مرة أخرى."
                st.session_state.status = "خطأ"
                st.session_state.pending_audio = None
                
            elif not transcript:
                logger.warning("No speech detected")
                st.session_state.current_transcript = "❌ لم يتم اكتشاف كلام"
                st.session_state.current_response = "يرجى التحدث بوضوح والمحاولة مرة أخرى."
                st.session_state.status = "جاهز"
                st.session_state.pending_audio = None
                
            else:
                logger.info(f"Success - Transcript: {transcript[:50]}...")
                
                # Update UI state FIRST
                st.session_state.current_transcript = transcript
                st.session_state.current_response = response
>>>>>>> 172c648 (Update: Improve voicebot behavior)
                st.session_state.current_metadata = {
                    "key_points": result.get("key_points", []),
                    "suggested_actions": result.get("suggested_actions", []),
                }
<<<<<<< HEAD
            elif intent == "DATABASE":
                result = voice_processor.generate_database_response(transcript, is_arabic)
                response_text = result["response"]
                st.session_state.current_metadata = {
                    "verification_steps": result.get("verification_steps", []),
                    "official_sources": result.get("official_sources", []),
                }
            else:
                result = voice_processor.generate_general_response(transcript, is_arabic)
                response_text = result["response"]
                st.session_state.current_metadata = {
                    "key_points": result.get("key_points", []),
                    "suggested_actions": result.get("suggested_actions", []),
                }
            
            # Update response
            st.session_state.current_response = response_text
            st.session_state.status = "Preparing audio..."
            
            # Update conversation history
            st.session_state.voice_messages.append({"role": "user", "content": transcript})
            st.session_state.voice_messages.append({"role": "assistant", "content": response_text})
            
            # Step 4: Generate TTS
            logger.info("Generating speech...")
            audio_response = voice_processor.text_to_speech(response_text, language)
            
            if audio_response:
                st.session_state.pending_audio = audio_response
                st.session_state.is_speaking = True
                st.session_state.status = "Speaking..."
            else:
                st.session_state.status = "Ready"
            
        except Exception as e:
            logger.error(f"Audio processing error: {e}", exc_info=True)
            st.session_state.current_transcript = f"❌ Error: {str(e)}"
            st.session_state.current_response = "An error occurred. Please try again."
            st.session_state.status = "Error"
=======
                
                # Update conversation history
                if transcript:
                    st.session_state.voice_messages.append({
                        "role": "user",
                        "content": transcript
                    })
                if response:
                    st.session_state.voice_messages.append({
                        "role": "assistant",
                        "content": response
                    })
                
                # Store audio to play AFTER UI updates
                if response_audio and len(response_audio) > 0:
                    logger.info("Storing audio for playback after UI update...")
                    st.session_state.pending_audio = response_audio
                    st.session_state.is_speaking = True
                    st.session_state.status = "يتحدث..."
                else:
                    st.session_state.pending_audio = None
                    st.session_state.status = "جاهز"
        
        except Exception as e:
            logger.error(f"Audio processing error: {e}", exc_info=True)
            st.session_state.current_transcript = f"❌ خطأ: {str(e)}"
            st.session_state.current_response = "حدث خطأ. يرجى المحاولة مرة أخرى."
            st.session_state.status = "خطأ"
            st.session_state.pending_audio = None
>>>>>>> 172c648 (Update: Improve voicebot behavior)
        
        finally:
            st.session_state.is_processing = False
            st.rerun()

else:
    if st.session_state.is_recording:
        st.session_state.is_recording = False
<<<<<<< HEAD
          
        st.session_state.status = "Ready"
      
=======
        st.session_state.status = "جاهز"
>>>>>>> 172c648 (Update: Improve voicebot behavior)
