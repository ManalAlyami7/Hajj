import streamlit as st
from openai import OpenAI
import io
import base64
from audio_recorder_streamlit import audio_recorder

# ---------------------------------------
# Page Configuration
# ---------------------------------------
st.set_page_config(
    page_title="Hajj Voice Assistant",
    page_icon="🕋",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# ---------------------------------------
# Custom CSS
# ---------------------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        background-attachment: fixed;
    }
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    .title {
        text-align: center;
        color: white;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
    }

    .subtitle {
        text-align: center;
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.2rem;
        margin-bottom: 2rem;
    }

    .chat-bubble-user {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1.2rem;
        border-radius: 1rem 1rem 0.2rem 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        animation: slideInRight 0.3s ease-out;
    }

    .chat-bubble-bot {
        background: rgba(255, 255, 255, 0.95);
        color: #333;
        padding: 1.2rem;
        border-radius: 1rem 1rem 1rem 0.2rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
        animation: slideInLeft 0.3s ease-out;
    }

    @keyframes slideInRight {
        from {
            opacity: 0;
            transform: translateX(20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    @keyframes slideInLeft {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }

    /* Recording button container */
    .recorder-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2rem auto;
        padding: 2rem;
        background: rgba(255, 255, 255, 0.1);
        border-radius: 2rem;
        backdrop-filter: blur(10px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
    }

    .status-text {
        text-align: center;
        color: white;
        font-size: 1.1rem;
        margin: 1rem 0;
        font-weight: 500;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.2);
    }

    .stButton > button {
        width: 100%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 1rem 2rem;
        border-radius: 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }

    .stButton > button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }

    /* Audio player styling */
    .stAudio {
        margin: 1rem auto;
        max-width: 500px;
    }

    /* Success/Error messages */
    .stSuccess, .stError, .stSpinner > div {
        background: rgba(255, 255, 255, 0.95) !important;
        border-radius: 1rem !important;
        padding: 1rem !important;
    }

    /* Avatar container with animation */
    .avatar-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2rem auto;
        position: relative;
    }
    
    /* Pulsing avatar */
    .avatar {
        width: 150px;
        height: 150px;
        background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 80px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        animation: pulse 2s ease-in-out infinite;
        position: relative;
        z-index: 2;
    }
    
    /* Animated rings */
    .ring {
        position: absolute;
        border: 3px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        animation: ripple 2s ease-out infinite;
    }
    
    .ring-1 {
        width: 170px;
        height: 170px;
        animation-delay: 0s;
    }
    
    .ring-2 {
        width: 210px;
        height: 210px;
        animation-delay: 0.5s;
    }
    
    .ring-3 {
        width: 250px;
        height: 250px;
        animation-delay: 1s;
    }
    
    /* Active state for voice input */
    .avatar.active {
        animation: pulse-active 0.5s ease-in-out infinite;
        box-shadow: 0 20px 80px rgba(255, 255, 255, 0.5);
    }
    
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.05);
        }
    }
    
    @keyframes pulse-active {
        0%, 100% {
            transform: scale(1);
        }
        50% {
            transform: scale(1.15);
        }
    }
    
    @keyframes ripple {
        0% {
            transform: scale(1);
            opacity: 1;
        }
        100% {
            transform: scale(1.5);
            opacity: 0;
        }
    }
</style>
""", unsafe_allow_html=True)

# ---------------------------------------
# Initialize OpenAI Client
# ---------------------------------------
@st.cache_resource
def get_openai_client():
    api_key = st.secrets.get("key", None)
    if not api_key:
        st.error("Please add your OPENAI_API_KEY to Streamlit secrets")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()

# ---------------------------------------
# Transcribe Audio
# ---------------------------------------
def transcribe_audio(audio_bytes):
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en"
        )
        return transcript.text
    except Exception as e:
        st.error(f"Transcription error: {str(e)}")
        return None

# ---------------------------------------
# AI Response (ChatGPT)
# ---------------------------------------
def get_ai_response(user_message):
    try:
        system_prompt = """You are a knowledgeable and friendly Hajj assistant.
        You help pilgrims with:
        - Hajj & Umrah rituals and steps
        - Travel and booking questions
        - Visa and document requirements
        - Accommodation and transport
        - Health, safety, and cultural etiquette
        Answer clearly, concisely, and respectfully."""
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(st.session_state.messages)
        messages.append({"role": "user", "content": user_message})
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=400
        )
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"AI response error: {str(e)}")
        return None

# ---------------------------------------
# Text-to-Speech
# ---------------------------------------
def text_to_speech(text):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        return response.content
    except Exception as e:
        st.error(f"TTS error: {str(e)}")
        return None

# ---------------------------------------
# Session State Setup
# ---------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None
if "is_listening" not in st.session_state:
    st.session_state.is_listening = False

# ---------------------------------------
# UI Header
# ---------------------------------------
st.markdown('<div class="title">🕋 Hajj Voice Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your intelligent voice guide for Hajj & Umrah</div>', unsafe_allow_html=True)

# Animated avatar with rings
avatar_active = "active" if st.session_state.is_listening else ""
st.markdown(f"""
<div class="avatar-container">
    <div class="ring ring-1"></div>
    <div class="ring ring-2"></div>
    <div class="ring ring-3"></div>
    <div class="avatar {avatar_active}">🕋</div>
</div>
""", unsafe_allow_html=True)

# ---------------------------------------
# Recording Section
# ---------------------------------------
st.markdown('<div class="status-text">🎤 Press and hold the button to record your question</div>', unsafe_allow_html=True)

st.markdown('<div class="recorder-container">', unsafe_allow_html=True)
audio_bytes = audio_recorder(
    text="",
    recording_color="#ff1744",      # Bright red when recording
    neutral_color="#ef4444",        # Red when idle
    icon_name="microphone",
    icon_size="3x",
    pause_threshold=2.0,
    sample_rate=16000
)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------
# Process Audio
# ---------------------------------------
if audio_bytes and audio_bytes != st.session_state.last_audio:
    st.session_state.last_audio = audio_bytes
    st.session_state.is_listening = True
    
    # Show audio playback
    st.audio(audio_bytes, format="audio/wav")
    
    with st.spinner("📝 Transcribing your voice..."):
        transcript = transcribe_audio(audio_bytes)
    
    if transcript:
        st.success(f"🗣️ You said: *{transcript}*")
        st.session_state.messages.append({"role": "user", "content": transcript})
        
        with st.spinner("🧠 Thinking..."):
            ai_response = get_ai_response(transcript)
        
        if ai_response:
            st.session_state.messages.append({"role": "assistant", "content": ai_response})
            
            with st.spinner("🔊 Generating speech response..."):
                audio_response = text_to_speech(ai_response)
            
            if audio_response:
                st.success("✅ Response ready!")
                st.audio(audio_response, format="audio/mp3", autoplay=True)
            
            st.session_state.is_listening = False
            st.rerun()
else:
    st.session_state.is_listening = False

# ---------------------------------------
# Display Conversation
# ---------------------------------------
st.markdown("---")
if st.session_state.messages:
    st.markdown("<h3 style='color: white; text-align: center; margin: 2rem 0;'>🗨️ Conversation History</h3>", unsafe_allow_html=True)
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            st.markdown(f"<div class='chat-bubble-user'>👤 <strong>You:</strong><br>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            st.markdown(f"<div class='chat-bubble-bot'>🤖 <strong>Assistant:</strong><br>{msg['content']}</div>", unsafe_allow_html=True)

# ---------------------------------------
# Clear Button
# ---------------------------------------
if st.session_state.messages:
    st.markdown("<br>", unsafe_allow_html=True)
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🧹 Clear Conversation", use_container_width=True):
            st.session_state.messages = []
            st.session_state.last_audio = None
            st.rerun()