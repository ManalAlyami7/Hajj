"""
Hajj Voice Assistant - Real-time STT & TTS
Custom audio recorder with live transcription and streaming responses
"""

import streamlit as st
from audio_recorder_streamlit import audio_recorder
import time

# Import core modules
from core.voice_processor import VoiceProcessor
from core.voice_graph import VoiceGraphBuilder
from ui.voice_interface import VoiceInterface, RealTimeVoiceStyles
from utils.state import get_current_time

# ---------------------------------------
# Page Configuration
# ---------------------------------------
st.set_page_config(
    page_title="Hajj Voice Assistant",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------
# Apply Custom CSS
# ---------------------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        background-attachment: fixed;
        overflow: hidden;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .main .block-container {
        padding: 1rem;
        max-width: 1400px;
        height: 100vh;
        overflow: hidden;
    }

    /* Header Section */
    .voice-header {
        text-align: center;
        padding: 1.5rem 0;
        margin-bottom: 1rem;
    }

    .voice-title {
        color: white;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        letter-spacing: 2px;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .voice-subtitle {
        color: rgba(255, 255, 255, 0.8);
        font-size: 1.1rem;
        font-weight: 400;
    }

    /* Main Layout - Split Screen */
    .voice-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2rem;
        height: calc(100vh - 200px);
        padding: 0 2rem;
    }

    /* Left Panel - Avatar & Recorder */
    .voice-left {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 2rem;
        padding: 2rem;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    /* Avatar Container */
    .voice-avatar-container {
        position: relative;
        margin-bottom: 2rem;
    }
    
    .voice-avatar {
        width: 200px;
        height: 200px;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 100px;
        box-shadow: 0 20px 60px rgba(96, 165, 250, 0.4);
        animation: float 3s ease-in-out infinite;
        position: relative;
        z-index: 2;
        border: 6px solid rgba(255, 255, 255, 0.2);
    }

    .voice-avatar.listening {
        animation: pulse-listening 0.8s ease-in-out infinite;
        box-shadow: 0 0 80px rgba(96, 165, 250, 0.8);
    }

    .voice-avatar.speaking {
        animation: pulse-speaking 0.6s ease-in-out infinite;
        box-shadow: 0 0 80px rgba(167, 139, 250, 0.8);
    }
    
    /* Rings around avatar */
    .voice-ring {
        position: absolute;
        border: 3px solid rgba(96, 165, 250, 0.3);
        border-radius: 50%;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        animation: expand 3s ease-out infinite;
    }
    
    .voice-ring-1 { width: 220px; height: 220px; animation-delay: 0s; }
    .voice-ring-2 { width: 260px; height: 260px; animation-delay: 1s; }
    .voice-ring-3 { width: 300px; height: 300px; animation-delay: 2s; }
    
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
        0% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.8; }
        100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; }
    }

    .record-button-container {
        margin-top: 2rem;
    }

    .record-label {
        margin-top: 1.5rem;
        color: white;
        font-size: 1.2rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* Right Panel - Live Transcript & Response */
    .voice-right {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }

    .transcript-container, .response-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 1.5rem;
        padding: 2rem;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        flex: 1;
        overflow-y: auto;
        min-height: 0;
    }

    .panel-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
    }

    .panel-icon {
        font-size: 2rem;
    }

    .panel-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: white;
        margin: 0;
    }

    .panel-badge {
        margin-left: auto;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(96, 165, 250, 0.2);
        color: #60a5fa;
        border: 1px solid rgba(96, 165, 250, 0.3);
    }

    .panel-badge.active {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
        border-color: rgba(34, 197, 94, 0.3);
        animation: badge-pulse 1s ease-in-out infinite;
    }

    @keyframes badge-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    /* Transcript Text */
    .transcript-text {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.3rem;
        line-height: 1.8;
        min-height: 100px;
        font-weight: 400;
    }

    .transcript-text.empty {
        color: rgba(255, 255, 255, 0.4);
        font-style: italic;
    }

    /* Response Content */
    .response-content {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.2rem;
        line-height: 1.8;
        min-height: 100px;
    }

    .response-content.empty {
        color: rgba(255, 255, 255, 0.4);
        font-style: italic;
    }

    /* Metadata Cards */
    .metadata-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 1rem;
        padding: 1rem;
        margin-top: 1rem;
        border-left: 4px solid #60a5fa;
    }

    .metadata-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #60a5fa;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .metadata-list {
        list-style: none;
        padding: 0;
        margin: 0.5rem 0 0 0;
    }

    .metadata-list li {
        padding: 0.3rem 0;
        color: rgba(255, 255, 255, 0.8);
    }

    .metadata-list li:before {
        content: "→ ";
        color: #60a5fa;
        font-weight: bold;
        margin-right: 0.5rem;
    }

    /* Status Indicator */
    .status-indicator {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 0.75rem 1.5rem;
        background: rgba(0, 0, 0, 0.8);
        border-radius: 2rem;
        color: white;
        font-weight: 600;
        font-size: 0.9rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
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
        animation: dot-pulse 1.5s ease-in-out infinite;
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

    /* Back Button */
    .stButton > button {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 2rem !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px) !important;
    }

    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        border-color: rgba(255, 255, 255, 0.4) !important;
        transform: translateY(-2px);
    }

    /* Hide default audio recorder */
    .stAudio {
        display: none !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
    }

    /* Responsive */
    @media (max-width: 1024px) {
        .voice-container {
            grid-template-columns: 1fr;
            height: auto;
        }
        
        .voice-left {
            min-height: 400px;
        }
        
        .voice-title {
            font-size: 2rem;
        }
        
        .voice-avatar {
            width: 150px;
            height: 150px;
            font-size: 75px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------
# Back Button
# ---------------------------------------
if st.button("⬅️ Back to Chat", key="back_button"):
    try:
        st.switch_page("app.py")
    except Exception:
        st.markdown('<meta http-equiv="refresh" content="0; url=/" />', unsafe_allow_html=True)

# ---------------------------------------
# Initialize Components
# ---------------------------------------
@st.cache_resource
def initialize_voice_system():
    """Initialize voice processor and graph"""
    processor = VoiceProcessor()
    graph_builder = VoiceGraphBuilder(processor)
    graph = graph_builder.build()
    return processor, graph

voice_processor, voice_graph = initialize_voice_system()

# ---------------------------------------
# Session State Initialization
# ---------------------------------------
if "voice_messages" not in st.session_state:
    st.session_state.voice_messages = []

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

if "is_recording" not in st.session_state:
    st.session_state.is_recording = False

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

if "is_speaking" not in st.session_state:
    st.session_state.is_speaking = False

if "current_transcript" not in st.session_state:
    st.session_state.current_transcript = ""

if "current_response" not in st.session_state:
    st.session_state.current_response = ""

if "current_metadata" not in st.session_state:
    st.session_state.current_metadata = {}

if "status" not in st.session_state:
    st.session_state.status = "Ready"

# ---------------------------------------
# Header
# ---------------------------------------
st.markdown("""
<div class="voice-header">
    <div class="voice-title">🕋 Hajj Voice Assistant</div>
    <div class="voice-subtitle">Real-time Speech Recognition & AI Responses</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------
# Status Indicator (Using VoiceInterface)
# ---------------------------------------
VoiceInterface.render_status_indicator(
    st.session_state.status,
    st.session_state.is_recording,
    st.session_state.is_speaking
)

# ---------------------------------------
# Main Layout - Split Screen
# ---------------------------------------
st.markdown('<div class="voice-container">', unsafe_allow_html=True)

# Left Panel - Avatar & Recorder (Using VoiceInterface)
col_left, col_right = st.columns(2)

with col_left:
    VoiceInterface.render_avatar(
        is_recording=st.session_state.is_recording,
        is_speaking=st.session_state.is_speaking
    )
    
    # Hidden audio recorder
    audio_bytes = audio_recorder(
        text="",
        recording_color="#ef4444",
        neutral_color="#3b82f6",
        icon_name="microphone",
        icon_size="2x",
        pause_threshold=2.0,
        sample_rate=16000,
        key="voice_recorder"
    )

# Right Panel - Transcript & Response (Using VoiceInterface)
with col_right:
    st.markdown('<div class="voice-right">', unsafe_allow_html=True)
    
    # Live Transcript
    VoiceInterface.render_live_transcript(
        transcript=st.session_state.current_transcript,
        is_active=st.session_state.is_recording or st.session_state.is_processing
    )
    
    # Live Response
    VoiceInterface.render_live_response(
        response=st.session_state.current_response,
        metadata=st.session_state.current_metadata,
        is_speaking=st.session_state.is_speaking
    )
    
    st.markdown('</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------
# Process Audio Input (Real-time)
# ---------------------------------------
if audio_bytes and audio_bytes != st.session_state.last_audio:
    st.session_state.last_audio = audio_bytes
    st.session_state.is_recording = False
    st.session_state.is_processing = True
    st.session_state.status = "Processing..."
    
    # Initialize state
    initial_state = {
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
        "messages_history": st.session_state.voice_messages
    }
    
    try:
        # Run the graph
        final_state = voice_graph.invoke(initial_state)
        
        # Extract results
        transcript = final_state.get("transcript", "")
        response = final_state.get("response", "")
        response_audio = final_state.get("response_audio", b"")
        error = final_state.get("error", "")
        
        # Extract metadata
        metadata = {
            "intent": final_state.get("intent", ""),
            "confidence": final_state.get("intent_confidence", 0.0),
            "tone": final_state.get("response_tone", "warm"),
            "urgency": final_state.get("urgency", "low"),
            "key_points": final_state.get("key_points", []),
            "suggested_actions": final_state.get("suggested_actions", []),
            "verification_steps": final_state.get("verification_steps", []),
            "official_sources": final_state.get("official_sources", [])
        }
        
        if error:
            st.session_state.status = "Error"
            st.session_state.current_transcript = f"❌ {error}"
            st.session_state.is_processing = False
            
        elif transcript and response:
            # Update transcript
            st.session_state.current_transcript = transcript
            st.session_state.status = "Speaking..."
            
            # Update response
            st.session_state.current_response = response
            st.session_state.current_metadata = metadata
            
            # Update message history
            st.session_state.voice_messages.append({
                "role": "user",
                "content": transcript
            })
            st.session_state.voice_messages.append({
                "role": "assistant",
                "content": response
            })
            
            # Play audio response
            st.session_state.is_processing = False
            st.session_state.is_speaking = True
            
            if response_audio:
                # Audio container (hidden but autoplay)
                st.audio(response_audio, format="audio/mp3", autoplay=True)
                
                # Estimate speaking time (rough: 150 words per minute)
                words = len(response.split())
                speak_time = (words / 150) * 60  # seconds
                time.sleep(min(speak_time, 10))  # Max 10 seconds
                
            st.session_state.is_speaking = False
            st.session_state.status = "Ready"
            
        st.rerun()
        
    except Exception as e:
        st.session_state.status = "Error"
        st.session_state.current_transcript = f"❌ Error: {str(e)}"
        st.session_state.is_processing = False
        st.rerun()

# Update recording status
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


# ---------------------------------------
# Page Configuration
# ---------------------------------------
st.set_page_config(
    page_title="Hajj Voice Assistant",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------
# Enhanced Custom CSS with Custom Recorder
# ---------------------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
        background-attachment: fixed;
        overflow: hidden;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .main .block-container {
        padding: 1rem;
        max-width: 1400px;
        height: 100vh;
        overflow: hidden;
    }

    /* Header Section */
    .voice-header {
        text-align: center;
        padding: 1.5rem 0;
        margin-bottom: 1rem;
    }

    .voice-title {
        color: white;
        font-size: 2.8rem;
        font-weight: 800;
        margin-bottom: 0.5rem;
        text-shadow: 0 4px 20px rgba(0, 0, 0, 0.5);
        letter-spacing: 2px;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
    }

    .voice-subtitle {
        color: rgba(255, 255, 255, 0.8);
        font-size: 1.1rem;
        font-weight: 400;
    }

    /* Main Layout - Split Screen */
    .voice-container {
        display: grid;
        grid-template-columns: 1fr 1fr;
        gap: 2rem;
        height: calc(100vh - 200px);
        padding: 0 2rem;
    }

    /* Left Panel - Avatar & Recorder */
    .voice-left {
        display: flex;
        flex-direction: column;
        align-items: center;
        justify-content: center;
        background: rgba(255, 255, 255, 0.03);
        border-radius: 2rem;
        padding: 2rem;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
    }

    /* Avatar Container */
    .voice-avatar-container {
        position: relative;
        margin-bottom: 2rem;
    }
    
    .voice-avatar {
        width: 200px;
        height: 200px;
        background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 100px;
        box-shadow: 0 20px 60px rgba(96, 165, 250, 0.4);
        animation: float 3s ease-in-out infinite;
        position: relative;
        z-index: 2;
        border: 6px solid rgba(255, 255, 255, 0.2);
    }

    .voice-avatar.listening {
        animation: pulse-listening 0.8s ease-in-out infinite;
        box-shadow: 0 0 80px rgba(96, 165, 250, 0.8);
    }

    .voice-avatar.speaking {
        animation: pulse-speaking 0.6s ease-in-out infinite;
        box-shadow: 0 0 80px rgba(167, 139, 250, 0.8);
    }
    
    /* Rings around avatar */
    .voice-ring {
        position: absolute;
        border: 3px solid rgba(96, 165, 250, 0.3);
        border-radius: 50%;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        animation: expand 3s ease-out infinite;
    }
    
    .voice-ring-1 { width: 220px; height: 220px; animation-delay: 0s; }
    .voice-ring-2 { width: 260px; height: 260px; animation-delay: 1s; }
    .voice-ring-3 { width: 300px; height: 300px; animation-delay: 2s; }
    
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
        0% { transform: translate(-50%, -50%) scale(0.8); opacity: 0.8; }
        100% { transform: translate(-50%, -50%) scale(1.5); opacity: 0; }
    }

    /* Custom Record Button */
    .record-button-container {
        margin-top: 2rem;
    }

    .record-button {
        width: 120px;
        height: 120px;
        border-radius: 50%;
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        border: none;
        cursor: pointer;
        position: relative;
        box-shadow: 0 10px 40px rgba(239, 68, 68, 0.4);
        transition: all 0.3s ease;
        display: flex;
        align-items: center;
        justify-content: center;
    }

    .record-button:hover {
        transform: scale(1.1);
        box-shadow: 0 15px 60px rgba(239, 68, 68, 0.6);
    }

    .record-button.recording {
        animation: record-pulse 1s ease-in-out infinite;
        background: linear-gradient(135deg, #ef4444 0%, #f97316 100%);
    }

    @keyframes record-pulse {
        0%, 100% { box-shadow: 0 0 0 0 rgba(239, 68, 68, 0.7); }
        50% { box-shadow: 0 0 0 20px rgba(239, 68, 68, 0); }
    }

    .record-icon {
        width: 50px;
        height: 50px;
        background: white;
        border-radius: 50%;
        transition: all 0.3s ease;
    }

    .record-button.recording .record-icon {
        border-radius: 8px;
        width: 40px;
        height: 40px;
    }

    .record-label {
        margin-top: 1.5rem;
        color: white;
        font-size: 1.2rem;
        font-weight: 600;
        text-transform: uppercase;
        letter-spacing: 2px;
    }

    /* Right Panel - Live Transcript & Response */
    .voice-right {
        display: flex;
        flex-direction: column;
        gap: 1.5rem;
    }

    .transcript-container, .response-container {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 1.5rem;
        padding: 2rem;
        backdrop-filter: blur(20px);
        border: 1px solid rgba(255, 255, 255, 0.1);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.3);
        flex: 1;
        overflow-y: auto;
        min-height: 0;
    }

    .panel-header {
        display: flex;
        align-items: center;
        gap: 0.75rem;
        margin-bottom: 1.5rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid rgba(255, 255, 255, 0.1);
    }

    .panel-icon {
        font-size: 2rem;
    }

    .panel-title {
        font-size: 1.3rem;
        font-weight: 700;
        color: white;
        margin: 0;
    }

    .panel-badge {
        margin-left: auto;
        padding: 0.3rem 0.8rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
        background: rgba(96, 165, 250, 0.2);
        color: #60a5fa;
        border: 1px solid rgba(96, 165, 250, 0.3);
    }

    .panel-badge.active {
        background: rgba(34, 197, 94, 0.2);
        color: #22c55e;
        border-color: rgba(34, 197, 94, 0.3);
        animation: badge-pulse 1s ease-in-out infinite;
    }

    @keyframes badge-pulse {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.6; }
    }

    /* Transcript Text */
    .transcript-text {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.3rem;
        line-height: 1.8;
        min-height: 100px;
        font-weight: 400;
    }

    .transcript-text.empty {
        color: rgba(255, 255, 255, 0.4);
        font-style: italic;
    }

    /* Response Content */
    .response-content {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.2rem;
        line-height: 1.8;
        min-height: 100px;
    }

    .response-content.empty {
        color: rgba(255, 255, 255, 0.4);
        font-style: italic;
    }

    /* Metadata Cards */
    .metadata-card {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 1rem;
        padding: 1rem;
        margin-top: 1rem;
        border-left: 4px solid #60a5fa;
    }

    .metadata-title {
        font-size: 0.9rem;
        font-weight: 600;
        color: #60a5fa;
        margin-bottom: 0.5rem;
        text-transform: uppercase;
        letter-spacing: 1px;
    }

    .metadata-content {
        color: rgba(255, 255, 255, 0.8);
        font-size: 1rem;
        line-height: 1.6;
    }

    .metadata-list {
        list-style: none;
        padding: 0;
        margin: 0.5rem 0 0 0;
    }

    .metadata-list li {
        padding: 0.3rem 0;
        color: rgba(255, 255, 255, 0.8);
    }

    .metadata-list li:before {
        content: "→ ";
        color: #60a5fa;
        font-weight: bold;
        margin-right: 0.5rem;
    }

    /* Status Indicator */
    .status-indicator {
        position: fixed;
        top: 20px;
        right: 20px;
        padding: 0.75rem 1.5rem;
        background: rgba(0, 0, 0, 0.8);
        border-radius: 2rem;
        color: white;
        font-weight: 600;
        font-size: 0.9rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
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
        animation: dot-pulse 1.5s ease-in-out infinite;
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

    /* Back Button */
    .stButton > button {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.2) !important;
        border-radius: 2rem !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
        backdrop-filter: blur(10px) !important;
    }

    .stButton > button:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        border-color: rgba(255, 255, 255, 0.4) !important;
        transform: translateY(-2px);
    }

    /* Hide default audio recorder */
    .stAudio {
        display: none !important;
    }

    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 8px;
    }

    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.05);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.2);
        border-radius: 10px;
    }

    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.3);
    }

    /* Responsive */
    @media (max-width: 1024px) {
        .voice-container {
            grid-template-columns: 1fr;
            height: auto;
        }
        
        .voice-left {
            min-height: 400px;
        }
        
        .voice-title {
            font-size: 2rem;
        }
        
        .voice-avatar {
            width: 150px;
            height: 150px;
            font-size: 75px;
        }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------
# Back Button
# ---------------------------------------
if st.button("⬅️ Back to Chat", key="back_button"):
    try:
        st.switch_page("app.py")
    except Exception:
        st.markdown('<meta http-equiv="refresh" content="0; url=/" />', unsafe_allow_html=True)

# ---------------------------------------
# Initialize Components
# ---------------------------------------
@st.cache_resource
def initialize_voice_system():
    """Initialize voice processor and graph"""
    processor = VoiceProcessor()
    graph_builder = VoiceGraphBuilder(processor)
    graph = graph_builder.build()
    return processor, graph

voice_processor, voice_graph = initialize_voice_system()

# ---------------------------------------
# Session State Initialization
# ---------------------------------------
if "voice_messages" not in st.session_state:
    st.session_state.voice_messages = []

if "last_audio" not in st.session_state:
    st.session_state.last_audio = None

if "is_recording" not in st.session_state:
    st.session_state.is_recording = False

if "is_processing" not in st.session_state:
    st.session_state.is_processing = False

if "is_speaking" not in st.session_state:
    st.session_state.is_speaking = False

if "current_transcript" not in st.session_state:
    st.session_state.current_transcript = ""

if "current_response" not in st.session_state:
    st.session_state.current_response = ""

if "current_metadata" not in st.session_state:
    st.session_state.current_metadata = {}

if "status" not in st.session_state:
    st.session_state.status = "Ready"

# ---------------------------------------
# Header
# ---------------------------------------
st.markdown("""
<div class="voice-header">
    <div class="voice-title">🕋 Hajj Voice Assistant</div>
    <div class="voice-subtitle">Real-time Speech Recognition & AI Responses</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------
# Status Indicator
# ---------------------------------------
status_dot_class = ""
if st.session_state.is_recording:
    status_dot_class = "listening"
elif st.session_state.is_speaking:
    status_dot_class = "speaking"

st.markdown(f"""
<div class="status-indicator">
    <div class="status-dot {status_dot_class}"></div>
    <span>{st.session_state.status}</span>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------
# Main Layout - Split Screen
# ---------------------------------------
st.markdown('<div class="voice-container">', unsafe_allow_html=True)

# Left Panel - Avatar & Recorder
col_left, col_right = st.columns(2)

with col_left:
    # Avatar state
    avatar_class = ""
    if st.session_state.is_recording:
        avatar_class = "listening"
    elif st.session_state.is_speaking:
        avatar_class = "speaking"
    
    st.markdown(f"""
    <div class="voice-left">
        <div class="voice-avatar-container">
            <div class="voice-ring voice-ring-1"></div>
            <div class="voice-ring voice-ring-2"></div>
            <div class="voice-ring voice-ring-3"></div>
            <div class="voice-avatar {avatar_class}">🕋</div>
        </div>
        
        <div class="record-button-container">
            <div class="record-label">
                {'🔴 Recording...' if st.session_state.is_recording else '🎤 Press to Speak'}
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Hidden audio recorder
    audio_bytes = audio_recorder(
        text="",
        recording_color="#ef4444",
        neutral_color="#3b82f6",
        icon_name="microphone",
        icon_size="2x",
        pause_threshold=2.0,
        sample_rate=16000,
        key="voice_recorder"
    )

# Right Panel - Transcript & Response
with col_right:
    # Transcript Panel
    transcript_badge_class = "active" if st.session_state.is_recording or st.session_state.is_processing else ""
    transcript_text = st.session_state.current_transcript if st.session_state.current_transcript else "Speak now..."
    transcript_class = "empty" if not st.session_state.current_transcript else ""
    
    st.markdown(f"""
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
    """, unsafe_allow_html=True)
    
    # Response Panel
    response_badge_class = "active" if st.session_state.is_speaking else ""
    response_text = st.session_state.current_response if st.session_state.current_response else "Response will appear here..."
    response_class = "empty" if not st.session_state.current_response else ""
    
    # Build metadata HTML
    metadata_html = ""
    if st.session_state.current_metadata:
        meta = st.session_state.current_metadata
        
        # Key Points
        if meta.get("key_points"):
            points_html = "".join([f"<li>{point}</li>" for point in meta["key_points"]])
            metadata_html += f"""
            <div class="metadata-card">
                <div class="metadata-title">💡 Key Points</div>
                <ul class="metadata-list">{points_html}</ul>
            </div>
            """
        
        # Suggested Actions
        if meta.get("suggested_actions"):
            actions_html = "".join([f"<li>{action}</li>" for action in meta["suggested_actions"]])
            metadata_html += f"""
            <div class="metadata-card" style="border-left-color: #a78bfa;">
                <div class="metadata-title" style="color: #a78bfa;">✅ Suggested Actions</div>
                <ul class="metadata-list">{actions_html}</ul>
            </div>
            """
        
        # Verification Steps
        if meta.get("verification_steps"):
            steps_html = "".join([f"<li>{step}</li>" for step in meta["verification_steps"]])
            metadata_html += f"""
            <div class="metadata-card" style="border-left-color: #ef4444;">
                <div class="metadata-title" style="color: #ef4444;">⚠️ Verification Steps</div>
                <ul class="metadata-list">{steps_html}</ul>
            </div>
            """
    
    st.markdown(f"""
    <div class="response-container">
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
    """, unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------
# Process Audio Input (Real-time)
# ---------------------------------------
if audio_bytes and audio_bytes != st.session_state.last_audio:
    st.session_state.last_audio = audio_bytes
    st.session_state.is_recording = False
    st.session_state.is_processing = True
    st.session_state.status = "Processing..."
    
    # Initialize state
    initial_state = {
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
        "messages_history": st.session_state.voice_messages
    }
    
    try:
        # Run the graph
        final_state = voice_graph.invoke(initial_state)
        
        # Extract results
        transcript = final_state.get("transcript", "")
        response = final_state.get("response", "")
        response_audio = final_state.get("response_audio", b"")
        error = final_state.get("error", "")
        
        # Extract metadata
        metadata = {
            "intent": final_state.get("intent", ""),
            "confidence": final_state.get("intent_confidence", 0.0),
            "tone": final_state.get("response_tone", "warm"),
            "urgency": final_state.get("urgency", "low"),
            "key_points": final_state.get("key_points", []),
            "suggested_actions": final_state.get("suggested_actions", []),
            "verification_steps": final_state.get("verification_steps", []),
            "official_sources": final_state.get("official_sources", [])
        }
        
        if error:
            st.session_state.status = "Error"
            st.session_state.current_transcript = f"❌ {error}"
            st.session_state.is_processing = False
            
        elif transcript and response:
            # Update transcript
            st.session_state.current_transcript = transcript
            st.session_state.status = "Speaking..."
            
            # Update response
            st.session_state.current_response = response
            st.session_state.current_metadata = metadata
            
            # Update message history
            st.session_state.voice_messages.append({
                "role": "user",
                "content": transcript
            })
            st.session_state.voice_messages.append({
                "role": "assistant",
                "content": response
            })
            
            # Play audio response
            st.session_state.is_processing = False
            st.session_state.is_speaking = True
            
            if response_audio:
                # Audio container (hidden but autoplay)
                st.audio(response_audio, format="audio/mp3", autoplay=True)
                
                # Estimate speaking time (rough: 150 words per minute)
                words = len(response.split())
                speak_time = (words / 150) * 60  # seconds
                time.sleep(min(speak_time, 10))  # Max 10 seconds
                
            st.session_state.is_speaking = False
            st.session_state.status = "Ready"
            
        st.rerun()
        
    except Exception as e:
        st.session_state.status = "Error"
        st.session_state.current_transcript = f"❌ Error: {str(e)}"
        st.session_state.is_processing = False
        st.rerun()

# Update recording status
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