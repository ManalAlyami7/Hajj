import streamlit as st
from openai import OpenAI
import tempfile

# -----------------------------
# Helper: Initialize OpenAI client
# -----------------------------
def get_openai_client():
    """Initialize OpenAI client from Streamlit secrets"""
    api_key = st.secrets.get("key", None)
    if not api_key:
        st.warning("⚠️ OpenAI API key missing in Streamlit secrets")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="🎤 Voice Assistant",
    page_icon="🎤",
    layout="wide"
)

# -----------------------------
# Initialize session states
# -----------------------------
if "show_voice_interface" not in st.session_state:
    st.session_state.show_voice_interface = True
if "new_language" not in st.session_state:
    st.session_state.new_language = "العربية"
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = []

# -----------------------------
# Voice Bot Page Layout
# -----------------------------
st.markdown("""
<style>
    .voice-interface {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 3rem;
        margin: 2rem auto;
        max-width: 800px;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.1);
        text-align: center;
    }
    .voice-visualizer {
        width: 200px;
        height: 200px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        margin: 2rem auto;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        animation: voicePulse 1.5s ease-in-out infinite;
    }
    @keyframes voicePulse {
        0%, 100% { transform: scale(1); box-shadow: 0 0 0 0 rgba(102, 126, 234, 0.7); }
        50% { transform: scale(1.05); box-shadow: 0 0 0 20px rgba(102, 126, 234, 0); }
    }
    .voice-text { font-size: 1.5rem; color: #667eea; margin-top: 1.5rem; font-weight: 600; }
    .voice-status { font-size: 1.1rem; color: #666; margin-top: 1rem; }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Voice Interface Container
# -----------------------------
st.markdown("<div class='voice-interface'>", unsafe_allow_html=True)

# Back Button
col1, col2, col3 = st.columns([1, 6, 1])
with col1:
    if st.button("← Back", key="back_button"):
        st.session_state.show_voice_interface = False
        st.switch_page("Home.py")  # Navigate back to home page

# Title
st.markdown(f"""
<h2 style='color: #667eea; margin-bottom: 1rem;'>
    🎤 {'مساعد الصوت للحج' if st.session_state.new_language == 'العربية' else 'Voice Assistant'}
</h2>
""", unsafe_allow_html=True)

# Voice Visualizer
st.markdown("""
<div class='voice-visualizer'>
    <div style='font-size: 4rem;'>🎤</div>
</div>
""", unsafe_allow_html=True)

# Instructions
st.markdown(f"""
<div class='voice-text'>
    {"اضغط على الزر أدناه وتحدث" if st.session_state.new_language == "العربية" else "Click the button below and speak"} 🎧
</div>
<div class='voice-status'>
    {"سيتم تحويل صوتك إلى نص تلقائياً" if st.session_state.new_language == "العربية" else "Your voice will be converted to text automatically"}
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Audio Input (Upload or Record)
# -----------------------------
st.markdown("<br>", unsafe_allow_html=True)
audio_file = st.file_uploader(
    "🎙️ " + ("سجل صوتك أو ارفع ملف صوتي" if st.session_state.new_language == "العربية" else "Record or upload audio"),
    type=["wav", "mp3", "m4a", "ogg"],
    key="audio_upload"
)

if audio_file is not None:
    st.audio(audio_file)

    with st.spinner("🔄 " + ("جارٍ تحويل الصوت إلى نص..." if st.session_state.new_language == "العربية" else "Converting speech to text...")):
        try:
            transcription = client.audio.transcriptions.create(
                model="whisper-1",
                file=audio_file,
                language="ar" if st.session_state.new_language == "العربية" else "en"
            )
            transcribed_text = transcription.text

            st.success("✅ " + ("تم التحويل بنجاح!" if st.session_state.new_language == "العربية" else "Transcription successful!"))
            st.info(f"**{'النص المحول' if st.session_state.new_language == 'العربية' else 'Transcribed Text'}:** {transcribed_text}")

            if st.button("🔍 " + ("بحث" if st.session_state.new_language == "العربية" else "Search"), type="primary"):
                st.session_state.selected_question = transcribed_text
                st.session_state.show_voice_interface = False
                st.switch_page("Home.py")

        except Exception as e:
            st.error(f"❌ {'حدث خطأ في التحويل' if st.session_state.new_language == 'العربية' else 'Transcription error'}: {str(e)}")

# -----------------------------
# Text-to-Speech (TTS) for Responses
# -----------------------------
st.markdown("<br><hr><br>", unsafe_allow_html=True)
st.markdown(f"""
<h3 style='color: #667eea;'>
    🔊 {'الاستماع للردود' if st.session_state.new_language == 'العربية' else 'Listen to Responses'}
</h3>
""", unsafe_allow_html=True)

if st.session_state.chat_memory and len(st.session_state.chat_memory) > 1:
    last_response = st.session_state.chat_memory[-1]
    if last_response.get("role") == "assistant":
        response_text = last_response.get("content", "")
        if st.button("🔊 " + ("استمع للرد الأخير" if st.session_state.new_language == "العربية" else "Listen to Last Response")):
            with st.spinner("🎵 " + ("جارٍ توليد الصوت..." if st.session_state.new_language == "العربية" else "Generating audio...")):
                try:
                    speech_response = client.audio.speech.create(
                        model="tts-1",
                        voice="alloy",
                        input=response_text[:500]
                    )
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                        tmp_file.write(speech_response.content)
                        tmp_file_path = tmp_file.name

                    with open(tmp_file_path, "rb") as audio:
                        st.audio(audio.read(), format="audio/mp3")

                except Exception as e:
                    st.error(f"❌ {'حدث خطأ في توليد الصوت' if st.session_state.new_language == 'العربية' else 'Audio generation error'}: {str(e)}")

st.markdown("</div>", unsafe_allow_html=True)
