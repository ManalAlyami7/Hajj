"""
Hajj Voice Assistant
Leverages VoiceInterface for UI components
"""
import streamlit as st
from audio_recorder_streamlit import audio_recorder
from core.voice_processor import VoiceProcessor
from core.voice_graph import VoiceGraphBuilder
from ui.voice_interface import VoiceInterface, RealTimeVoiceStyles
from utils.translations import t

# Page config
st.set_page_config(
    page_title="Hajj Voice Assistant",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Apply voice interface styles
st.markdown(RealTimeVoiceStyles.get_styles(), unsafe_allow_html=True)

# Initialize components
@st.cache_resource
def initialize_voice_system():
    processor = VoiceProcessor()
    graph_builder = VoiceGraphBuilder(processor)
    return processor, graph_builder.build()

processor, voice_graph = initialize_voice_system()

# Session state initialization
if "voice_state" not in st.session_state:
    st.session_state.voice_state = {
        "is_recording": False,
        "is_speaking": False,
        "transcript": "",
        "response": "",
        "metadata": {},
        "last_audio": None
    }

# Layout
col1, col2 = st.columns([1, 2])

with col1:
    # Render avatar and recording interface
    VoiceInterface.render_avatar(
        is_recording=st.session_state.voice_state["is_recording"],
        is_speaking=st.session_state.voice_state["is_speaking"]
    )
    
    # Audio recorder
    audio_bytes = audio_recorder(
        text="",
        recording_color="#ef4444",
        neutral_color="#3b82f6",
        pause_threshold=2.0
    )

with col2:
    # Live transcript panel
    VoiceInterface.render_live_transcript(
        transcript=st.session_state.voice_state["transcript"],
        is_active=st.session_state.voice_state["is_recording"]
    )
    
    # Response panel with metadata
    VoiceInterface.render_live_response(
        response=st.session_state.voice_state["response"],
        metadata=st.session_state.voice_state["metadata"],
        is_speaking=st.session_state.voice_state["is_speaking"]
    )

# Process audio when received
if audio_bytes and audio_bytes != st.session_state.voice_state["last_audio"]:
    st.session_state.voice_state["last_audio"] = audio_bytes
    st.session_state.voice_state["is_recording"] = True

    try:
        # Process through voice graph
        result = voice_graph.invoke({
            "audio_bytes": audio_bytes,
            "language": st.session_state.get("language", "English")
        })

        # Update state with results
        st.session_state.voice_state.update({
            "transcript": result.get("transcript", ""),
            "response": result.get("response", ""),
            "metadata": {
                "key_points": result.get("key_points", []),
                "suggested_actions": result.get("actions", []),
                "verification_steps": result.get("verification", [])
            },
            "is_recording": False,
            "is_speaking": bool(result.get("response_audio"))
        })

        # Play audio response if available
        if result.get("response_audio"):
            st.audio(result["response_audio"], format="audio/mp3", autoplay=True)
            st.session_state.voice_state["is_speaking"] = False

        st.rerun()

    except Exception as e:
        st.error(f"❌ {str(e)}")
        st.session_state.voice_state["is_recording"] = False