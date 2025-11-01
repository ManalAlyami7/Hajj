import streamlit as st
from openai import OpenAI
from audio_recorder_streamlit import audio_recorder
import io
import base64

# ----------------------------
# Page Setup & Styles
# ----------------------------
st.set_page_config(page_title="🕋 Hajj Voice Assistant", page_icon="🕋", layout="centered")

st.markdown("""
<style>
.stApp {
    background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    color: #111827;
    font-family: 'Inter', sans-serif;
}
.header {
    text-align:center;
    margin-top: 12px;
    margin-bottom: 8px;
}
.title {
    font-size: 2.3rem;
    font-weight: 700;
    color: white;
    text-shadow: 0 2px 8px rgba(0,0,0,0.25);
}
.subtitle {
    color: rgba(255,255,255,0.9);
    margin-bottom: 1rem;
}
.recorder-box {
    display:flex;
    justify-content:center;
    margin-bottom: 1rem;
}
.chat-container {
    display:flex;
    flex-direction: column;
    gap: 6px;
    padding: 8px;
}
.chat-bubble-user {
    background: #dc2626;
    color: white;
    padding: 12px;
    border-radius: 12px;
    margin: 6px 0;
    max-width: 80%;
    align-self: flex-end;
}
.chat-bubble-assistant {
    background: rgba(255,255,255,0.9);
    color: #111827;
    padding: 12px;
    border-radius: 12px;
    margin: 6px 0;
    max-width: 80%;
    align-self: flex-start;
}
.clear-button {
    margin-top: 12px;
}
</style>
""", unsafe_allow_html=True)

st.markdown('<div class="header"><div class="title">🕋 Hajj Voice Assistant</div><div class="subtitle">Speak to your AI Hajj guide</div></div>', unsafe_allow_html=True)

# ----------------------------
# OpenAI Client
# ----------------------------
@st.cache_resource
def get_client():
    api_key = st.secrets.get("key") or st.secrets.get("OPENAI_API_KEY")
    if not api_key:
        st.error("⚠️ Please add your OpenAI API key to Streamlit secrets under the key 'key' or 'OPENAI_API_KEY'")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_client()

# ----------------------------
# Helper functions
# ----------------------------
def transcribe_audio(audio_bytes: bytes) -> str | None:
    try:
        audio_file = io.BytesIO(audio_bytes)
        audio_file.name = "audio.wav"
        result = client.audio.transcriptions.create(model="whisper-1", file=audio_file)
        return result.text
    except Exception as e:
        st.error(f"Transcription error: {e}")
        return None

def ai_reply(messages):
    try:
        completion = client.chat.completions.create(
            model="gpt-4",
            messages=messages,
            temperature=0.6
        )
        return completion.choices[0].message.content
    except Exception as e:
        st.error(f"AI error: {e}")
        return None

def speak_text(text: str):
    try:
        response = client.audio.speech.create(model="tts-1", voice="alloy", input=text)
        audio_bytes = response.content if hasattr(response, "content") else None
        if audio_bytes:
            b64 = base64.b64encode(audio_bytes).decode()
            st.markdown(f'<audio controls autoplay><source src="data:audio/mp3;base64,{b64}" type="audio/mp3"></audio>', unsafe_allow_html=True)
    except Exception as e:
        st.error(f"TTS error: {e}")

# ----------------------------
# Initialize conversation
# ----------------------------
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
            reply = ai_reply(st.session_state.messages)
        if reply:
            st.session_state.messages.append({"role": "assistant", "content": reply})
            speak_text(reply)
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
    st.experimental_rerun()
