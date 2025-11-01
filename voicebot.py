import streamlit as st
import openai
from openai import OpenAI
import numpy as np
import io
import base64
from audio_recorder_streamlit import audio_recorder
import time

# Page configuration
st.set_page_config(
    page_title="Hajj Voice Assistant",
    page_icon="🕋",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# Custom CSS for beautiful gradient background and animations
st.markdown("""
<style>
    /* Main gradient background */
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        background-attachment: fixed;
    }
    
    /* Hide default Streamlit elements */
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}
    
    /* Center container */
    .main .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 800px;
    }
    
    /* Avatar container with animation */
    .avatar-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 4rem auto;
        position: relative;
    }
    
    /* Pulsing avatar */
    .avatar {
        width: 200px;
        height: 200px;
        background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 100px;
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
        width: 220px;
        height: 220px;
        animation-delay: 0s;
    }
    
    .ring-2 {
        width: 260px;
        height: 260px;
        animation-delay: 0.5s;
    }
    
    .ring-3 {
        width: 300px;
        height: 300px;
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
    
    /* Title styling */
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
    
    /* Chat messages */
    .chat-message {
        background: rgba(255, 255, 255, 0.95);
        padding: 1.5rem;
        border-radius: 1rem;
        margin: 1rem 0;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.1);
    }
    
    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
    
    .assistant-message {
        background: rgba(255, 255, 255, 0.95);
        color: #333;
    }
    
    /* Button styling */
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
    
    /* Status indicator */
    .status {
        text-align: center;
        color: white;
        font-size: 1rem;
        margin: 1rem 0;
        padding: 0.5rem;
        background: rgba(255, 255, 255, 0.2);
        border-radius: 1rem;
        backdrop-filter: blur(10px);
    }
</style>
""", unsafe_allow_html=True)

# Initialize OpenAI client
@st.cache_resource
def get_openai_client():
    api_key = st.secrets.get("key", None)
    if not api_key:
        st.error("Please add your OPENAI_API_KEY to Streamlit secrets")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()

# Initialize session state
if "messages" not in st.session_state:
    st.session_state.messages = []
if "is_listening" not in st.session_state:
    st.session_state.is_listening = False

# Header
st.markdown('<div class="title">🕋 Hajj Voice Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your intelligent guide for Hajj pilgrimage</div>', unsafe_allow_html=True)

# Avatar with animated rings
avatar_active = "active" if st.session_state.is_listening else ""
st.markdown(f"""
<div class="avatar-container">
    <div class="ring ring-1"></div>
    <div class="ring ring-2"></div>
    <div class="ring ring-3"></div>
    <div class="avatar {avatar_active}">🕋</div>
</div>
""", unsafe_allow_html=True)

# Function to transcribe audio
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

# Function to get AI response
def get_ai_response(user_message):
    try:
        # System prompt for Hajj assistant
        system_prompt = """You are a knowledgeable and friendly Hajj assistant for a travel company. 
        You help pilgrims with:
        - Hajj and Umrah rituals and procedures
        - Travel packages and booking information
        - Visa requirements and documentation
        - Accommodation and transportation
        - Important dates and schedules
        - Health and safety guidelines
        - Cultural etiquette and tips
        
        Provide clear, concise, and helpful responses. Be respectful and understanding of the spiritual significance of the pilgrimage."""
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(st.session_state.messages)
        messages.append({"role": "user", "content": user_message})
        
        response = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.7,
            max_tokens=500
        )
        
        return response.choices[0].message.content
    except Exception as e:
        st.error(f"AI response error: {str(e)}")
        return None

# Function to convert text to speech
def text_to_speech(text):
    try:
        response = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=text
        )
        return response.content
    except Exception as e:
        st.error(f"Text-to-speech error: {str(e)}")
        return None

# Status indicator
if st.session_state.is_listening:
    st.markdown('<div class="status">🎤 Listening...</div>', unsafe_allow_html=True)
else:
    st.markdown('<div class="status">Click the button below to speak</div>', unsafe_allow_html=True)

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a respectful and multilingual Hajj assistant that helps pilgrims with guidance, safety, and information."}
    ]

# ----------------------------
# Red Recording Button
# ----------------------------
st.markdown('<div class="recorder-box">', unsafe_allow_html=True)
audio_bytes = audio_recorder(
    text="🎙️ Hold to speak",
    recording_color="#dc2626",   # 🔴 Red
    neutral_color="#ef4444",     # Slightly lighter red when idle
    icon_size="3x",
)
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# Process Audio
# ----------------------------
if audio_bytes:
    st.audio(audio_bytes, format="audio/wav")
    with st.spinner("📝 Transcribing your voice..."):
        transcript = transcribe_audio(audio_bytes)
    if transcript:
        st.session_state.messages.append({"role": "user", "content": transcript})
        st.success(f"🗣️ You said: {transcript}")

        with st.spinner("🤖 Thinking..."):
            reply = get_ai_response(st.session_state.messages)
        if reply:
            st.session_state.messages.append({"role": "assistant", "content": reply})
            text_to_speech(reply)
        else:
            st.error("No response from assistant.")
    else:
        st.error("Could not transcribe audio.")

# ----------------------------
# Display Chat
# ----------------------------
st.markdown("---")
st.markdown('<div class="chat-container">', unsafe_allow_html=True)
for msg in st.session_state.messages[1:]:
    role = msg["role"]
    bubble = "chat-bubble-user" if role == "user" else "chat-bubble-assistant"
    st.markdown(f'<div class="{bubble}">{msg["content"]}</div>', unsafe_allow_html=True)
st.markdown('</div>', unsafe_allow_html=True)

# ----------------------------
# Controls
# ----------------------------
if st.button("🧹 Clear Conversation", use_container_width=True):
    st.session_state.messages = st.session_state.messages[:1]
    st.rerun()