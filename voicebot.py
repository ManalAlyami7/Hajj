import streamlit as st
from openai import OpenAI
import io
import base64
import tempfile
import time
import speech_recognition as sr

# -----------------------------
# Page configuration
# -----------------------------
st.set_page_config(
    page_title="Hajj Voice Assistant",
    page_icon="🕋",
    layout="centered",
    initial_sidebar_state="collapsed"
)

# -----------------------------
# Custom CSS
# -----------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 50%, #f093fb 100%);
        background-attachment: fixed;
        color: white;
        font-family: 'Inter', sans-serif;
    }

    #MainMenu, footer, header {visibility: hidden;}

    .block-container {
        padding-top: 3rem;
        padding-bottom: 3rem;
        max-width: 800px;
    }

    .title {
        text-align: center;
        font-size: 2.5rem;
        font-weight: 700;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 10px rgba(0, 0, 0, 0.2);
        animation: fadeInDown 1s ease;
    }

    .subtitle {
        text-align: center;
        color: rgba(255,255,255,0.9);
        font-size: 1.2rem;
        margin-bottom: 2rem;
        animation: fadeInDown 1.3s ease;
    }

    @keyframes fadeInDown {
        from {opacity: 0; transform: translateY(-20px);}
        to {opacity: 1; transform: translateY(0);}
    }

    .avatar-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 3rem auto;
        position: relative;
    }

    .avatar {
        width: 180px;
        height: 180px;
        background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 90px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        animation: pulse 2s ease-in-out infinite;
        z-index: 2;
    }

    .avatar.active {
        animation: pulse-active 0.5s ease-in-out infinite;
        box-shadow: 0 20px 80px rgba(255, 255, 255, 0.5);
    }

    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.05); }
    }

    @keyframes pulse-active {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.15); }
    }

    .speak-button {
        display: block;
        width: 100%;
        text-align: center;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        padding: 1rem 2rem;
        border-radius: 2rem;
        font-size: 1.1rem;
        font-weight: 600;
        border: none;
        cursor: pointer;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
        transition: all 0.3s ease;
    }

    .speak-button:hover {
        transform: scale(1.05);
        box-shadow: 0 6px 20px rgba(0, 0, 0, 0.3);
    }

    .status {
        text-align: center;
        color: white;
        margin: 1rem 0;
        font-size: 1rem;
        background: rgba(255, 255, 255, 0.2);
        padding: 0.5rem;
        border-radius: 1rem;
        backdrop-filter: blur(10px);
    }

    .chat-message {
        background: rgba(255, 255, 255, 0.95);
        color: #333;
        padding: 1.2rem;
        border-radius: 1rem;
        margin: 0.5rem 0;
    }

    .user-message {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Initialize OpenAI client
# -----------------------------
@st.cache_resource(show_spinner=False)
def get_openai_client():
    api_key = st.secrets.get("key", None)
    if not api_key:
        st.error("⚠️ Please add your OPENAI_API_KEY to Streamlit secrets")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()

# -----------------------------
# Session State
# -----------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []

# -----------------------------
# Header
# -----------------------------
st.markdown('<div class="title">🕋 Hajj Voice Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Your intelligent guide for Hajj pilgrimage</div>', unsafe_allow_html=True)

# -----------------------------
# Avatar display
# -----------------------------
st.markdown(f"""
<div class="avatar-container">
    <div class="avatar">🕋</div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Record voice input
# -----------------------------
recognizer = sr.Recognizer()
mic = sr.Microphone()

st.markdown('<div class="status">Click “🎤 Speak Now” and start talking...</div>', unsafe_allow_html=True)
speak_button = st.button("🎤 Speak Now", key="speak", help="Press to record your question")

if speak_button:
    with mic as source:
        st.markdown('<div class="status">🎙️ Listening...</div>', unsafe_allow_html=True)
        recognizer.adjust_for_ambient_noise(source)
        audio_data = recognizer.listen(source, timeout=6, phrase_time_limit=10)
    
    with tempfile.NamedTemporaryFile(delete=False, suffix=".wav") as tmpfile:
        tmpfile.write(audio_data.get_wav_data())
        audio_path = tmpfile.name

    # -----------------------------
    # Transcribe audio
    # -----------------------------
    with st.spinner("Transcribing your message..."):
        with open(audio_path, "rb") as audio_file:
            transcript = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file
            ).text

    if transcript:
        # Prevent duplicate message on rerun
        if st.session_state.messages and transcript == st.session_state.messages[-1]["content"]:
            st.stop()

        st.session_state.messages.append({"role": "user", "content": transcript})

        # -----------------------------
        # Get AI response
        # -----------------------------
        with st.spinner("Thinking..."):
            system_prompt = """
            You are a knowledgeable and friendly Hajj assistant.
            Respond in the same language as the user's message (Arabic or English).
            Provide accurate information about:
            - Hajj and Umrah rituals
            - Travel packages and bookings
            - Visa and documentation
            - Accommodation and safety
            - Cultural etiquette
            """

            messages = [{"role": "system", "content": system_prompt}]
            messages.extend(st.session_state.messages)

            ai_response = client.chat.completions.create(
                model="gpt-4o-mini",
                messages=messages,
                temperature=0.6
            ).choices[0].message.content

        st.session_state.messages.append({"role": "assistant", "content": ai_response})

        # -----------------------------
        # Text-to-Speech
        # -----------------------------
        with st.spinner("Generating voice response..."):
            speech = client.audio.speech.create(
                model="tts-1",
                voice="alloy",
                input=ai_response
            )
            audio_bytes = speech.read()

        st.audio(io.BytesIO(audio_bytes), format="audio/mp3")

        st.rerun()

# -----------------------------
# Display conversation history
# -----------------------------
st.markdown("---")
st.markdown("### 💬 Conversation History")

for msg in st.session_state.messages:
    role = msg["role"]
    content = msg["content"]
    if role == "user":
        st.markdown(f'<div class="chat-message user-message">👤 {content}</div>', unsafe_allow_html=True)
    else:
        st.markdown(f'<div class="chat-message">🕋 {content}</div>', unsafe_allow_html=True)

if st.session_state.messages:
    if st.button("🧹 Clear Conversation"):
        st.session_state.messages = []
        st.rerun()