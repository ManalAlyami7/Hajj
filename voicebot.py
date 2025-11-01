import streamlit as st
import openai
from openai import OpenAI
import numpy as np
import io
import base64
import pyaudio
import wave
import time

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
# Custom CSS (Gradient Background + Animation)
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

    .chat-message {
        background: rgba(255, 255, 255, 0.95);
        padding: 1.2rem;
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

    .listening-indicator {
        width: 90px;
        height: 90px;
        border-radius: 50%;
        background: linear-gradient(135deg, #ff1744 0%, #d32f2f 100%);
        border: 4px solid rgba(255, 255, 255, 0.3);
        display: flex;
        align-items: center;
        justify-content: center;
        font-size: 40px;
        margin: 2rem auto;
        box-shadow: 0 10px 40px rgba(211, 47, 47, 0.4);
        animation: record-pulse 1s ease-in-out infinite;
    }
    
    .listening-indicator.active {
        animation: record-pulse-active 0.5s ease-in-out infinite;
        box-shadow: 0 15px 60px rgba(255, 23, 68, 0.8);
    }
    
    @keyframes record-pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }
    
    @keyframes record-pulse-active {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.15); }
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
# Record Audio with Silence Detection
# ---------------------------------------
def record_with_silence_detection(duration_max=60, silence_threshold=-35, silence_duration=2.0, sample_rate=16000):
    CHUNK = 1024
    FORMAT = pyaudio.paInt16
    CHANNELS = 1
    
    try:
        p = pyaudio.PyAudio()
        stream = p.open(format=FORMAT, channels=CHANNELS, rate=sample_rate, input=True, frames_per_buffer=CHUNK)
        st.info("🎤 Listening... Speak now (auto-stop on silence)")
        
        frames = []
        silence_chunks = 0
        silence_chunks_needed = int((silence_duration * sample_rate) / CHUNK)
        start_time = time.time()
        
        while time.time() - start_time < duration_max:
            data = stream.read(CHUNK, exception_on_overflow=False)
            frames.append(data)
            
            audio_chunk = np.frombuffer(data, dtype=np.int16).astype(np.float32)
            rms = np.sqrt(np.mean(audio_chunk ** 2))
            energy_db = 20 * np.log10(rms + 1e-10)
            
            if energy_db < silence_threshold:
                silence_chunks += 1
            else:
                silence_chunks = 0
            
            if silence_chunks >= silence_chunks_needed:
                st.success("✅ Stopped (silence detected)")
                break
        
        stream.stop_stream()
        stream.close()
        p.terminate()
        
        wav_buffer = io.BytesIO()
        with wave.open(wav_buffer, 'wb') as wav_file:
            wav_file.setnchannels(CHANNELS)
            wav_file.setsampwidth(p.get_sample_size(FORMAT))
            wav_file.setframerate(sample_rate)
            wav_file.writeframes(b''.join(frames))
        return wav_buffer.getvalue()
        
    except Exception as e:
        st.error(f"Microphone error: {e}")
        return None

# ---------------------------------------
# Session State Setup
# ---------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "listening" not in st.session_state:
    st.session_state.listening = False

# ---------------------------------------
# UI
# ---------------------------------------
st.markdown('<div class="title">🕋 Hajj Voice Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your intelligent voice guide for Hajj & Umrah</div>', unsafe_allow_html=True)

if st.session_state.listening:
    st.markdown('<div class="listening-indicator active">🎙️</div>', unsafe_allow_html=True)
    audio_bytes = record_with_silence_detection()
    
    if audio_bytes:
        with st.spinner("📝 Transcribing..."):
            transcript = transcribe_audio(audio_bytes)
        if transcript:
            st.session_state.messages.append({"role": "user", "content": transcript})
            with st.spinner("🧠 Thinking..."):
                ai_response = get_ai_response(transcript)
            if ai_response:
                st.session_state.messages.append({"role": "assistant", "content": ai_response})
                with st.spinner("🔊 Speaking..."):
                    audio_response = text_to_speech(ai_response)
                if audio_response:
                    audio_base64 = base64.b64encode(audio_response).decode()
                    st.markdown(f'<audio autoplay><source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
    st.session_state.listening = False
    st.rerun()

else:
    st.markdown('<div class="listening-indicator">🎙️</div>', unsafe_allow_html=True)
    if st.button("Start Listening", use_container_width=True):
        st.session_state.listening = True
        st.rerun()

st.markdown("---")
if st.session_state.messages:
    st.markdown("<h3>🗨️ Conversation</h3>", unsafe_allow_html=True)
    chat_container = st.container()
    for msg in st.session_state.messages:
        if msg["role"] == "user":
            chat_container.markdown(f"<div class='chat-bubble-user'>{msg['content']}</div>", unsafe_allow_html=True)
        else:
            chat_container.markdown(f"<div class='chat-bubble-bot'>{msg['content']}</div>", unsafe_allow_html=True)
            
if st.session_state.messages:
    if st.button("🧹 Clear Conversation"):
        st.session_state.messages = []
        st.rerun()
