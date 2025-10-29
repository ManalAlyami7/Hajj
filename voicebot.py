import streamlit as st
from openai import OpenAI
import tempfile
import os

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
# Enhanced CSS Styling
# -----------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700&family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', 'Cairo', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        background-attachment: fixed;
    }
    
    .block-container {
        padding-top: 2rem;
        padding-bottom: 2rem;
    }
    
    /* Voice Interface Card */
    .voice-interface {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(20px);
        border-radius: 30px;
        padding: 3rem 2rem;
        margin: 2rem auto;
        max-width: 900px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.15);
        text-align: center;
        animation: slideIn 0.6s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateY(30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Voice Visualizer */
    .voice-visualizer {
        width: 220px;
        height: 220px;
        border-radius: 50%;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        margin: 2rem auto;
        display: flex;
        align-items: center;
        justify-content: center;
        position: relative;
        animation: voicePulse 2s ease-in-out infinite;
        box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4);
        cursor: pointer;
        transition: transform 0.3s ease;
    }
    
    .voice-visualizer:hover {
        transform: scale(1.05);
    }
    
    @keyframes voicePulse {
        0%, 100% { 
            transform: scale(1); 
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4), 0 0 0 0 rgba(102, 126, 234, 0.7); 
        }
        50% { 
            transform: scale(1.05); 
            box-shadow: 0 10px 40px rgba(102, 126, 234, 0.4), 0 0 0 30px rgba(102, 126, 234, 0); 
        }
    }
    
    .voice-visualizer.recording {
        animation: voiceRecording 1s ease-in-out infinite;
        background: linear-gradient(135deg, #f093fb 0%, #f5576c 100%);
    }
    
    @keyframes voiceRecording {
        0%, 100% { 
            transform: scale(1); 
            box-shadow: 0 10px 40px rgba(245, 87, 108, 0.5), 0 0 0 0 rgba(245, 87, 108, 0.7); 
        }
        50% { 
            transform: scale(1.1); 
            box-shadow: 0 10px 40px rgba(245, 87, 108, 0.5), 0 0 0 40px rgba(245, 87, 108, 0); 
        }
    }
    
    .voice-icon {
        font-size: 5rem;
        filter: drop-shadow(0 4px 10px rgba(0, 0, 0, 0.2));
    }
    
    /* Text Styles */
    .voice-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 1rem;
    }
    
    .voice-text {
        font-size: 1.3rem;
        color: #667eea;
        margin-top: 1.5rem;
        font-weight: 600;
    }
    
    .voice-status {
        font-size: 1rem;
        color: #888;
        margin-top: 0.5rem;
        line-height: 1.6;
    }
    
    .voice-hint {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.1) 0%, rgba(118, 75, 162, 0.1) 100%);
        border-left: 4px solid #667eea;
        padding: 1rem 1.5rem;
        border-radius: 10px;
        margin: 1.5rem 0;
        text-align: left;
    }
    
    /* Feature Cards */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(200px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    .feature-card {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
        border-radius: 15px;
        padding: 1.5rem;
        text-align: center;
        transition: all 0.3s ease;
        border: 1px solid rgba(102, 126, 234, 0.2);
    }
    
    .feature-card:hover {
        transform: translateY(-5px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.2);
        border-color: rgba(102, 126, 234, 0.4);
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    .feature-title {
        font-weight: 600;
        color: #667eea;
        margin-bottom: 0.5rem;
    }
    
    .feature-desc {
        font-size: 0.9rem;
        color: #666;
    }
    
    /* Back Button */
    .stButton button {
        background: rgba(255, 255, 255, 0.9) !important;
        color: #667eea !important;
        border: 2px solid #667eea !important;
        border-radius: 12px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stButton button:hover {
        background: #667eea !important;
        color: white !important;
        transform: translateX(-5px);
        box-shadow: 0 5px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    /* Upload Area */
    .uploadedFile {
        background: linear-gradient(135deg, rgba(102, 126, 234, 0.05) 0%, rgba(118, 75, 162, 0.05) 100%);
        border-radius: 15px;
        padding: 1.5rem;
        border: 2px dashed #667eea;
    }
    
    /* Audio Player */
    audio {
        width: 100%;
        border-radius: 10px;
        margin: 1rem 0;
    }
    
    /* Response Card */
    .response-card {
        background: linear-gradient(135deg, rgba(17, 153, 142, 0.1) 0%, rgba(56, 239, 125, 0.1) 100%);
        border-radius: 15px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        border-left: 4px solid #11998e;
    }
    
    .response-text {
        color: #333;
        line-height: 1.6;
        font-size: 1.05rem;
    }
    
    /* Divider */
    .custom-divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #667eea, transparent);
        margin: 2rem 0;
        border: none;
    }
    
    /* RTL Support */
    .rtl {
        direction: rtl;
        text-align: right;
    }
    
    /* Loading Animation */
    .loading-dots {
        display: inline-block;
        animation: loadingDots 1.5s infinite;
    }
    
    @keyframes loadingDots {
        0%, 20% { content: '.'; }
        40% { content: '..'; }
        60%, 100% { content: '...'; }
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Initialize session states
# -----------------------------
if "show_voice_interface" not in st.session_state:
    st.session_state.show_voice_interface = True
if "language" not in st.session_state:
    st.session_state.language = "العربية"
if "chat_memory" not in st.session_state:
    st.session_state.chat_memory = []
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False

# Get language
lang = st.session_state.language
is_arabic = lang == "العربية"

# -----------------------------
# Translations
# -----------------------------
translations = {
    "English": {
        "title": "🎤 Voice Assistant for Hajj Shield",
        "subtitle": "Speak naturally, get instant verification",
        "instruction": "Click and speak or upload audio",
        "status": "Your voice will be converted to text automatically",
        "upload_label": "🎙️ Record or upload audio file",
        "converting": "Converting speech to text...",
        "success": "Transcription successful!",
        "transcribed": "Transcribed Text",
        "search_btn": "🔍 Search Now",
        "error": "Transcription error",
        "tts_title": "🔊 Listen to Responses",
        "listen_btn": "🔊 Listen to Last Response",
        "generating": "Generating audio...",
        "audio_error": "Audio generation error",
        "back": "← Back to Home",
        "hint_title": "💡 Voice Tips",
        "hint_text": "• Speak clearly and at normal speed\n• Mention company name or location\n• Ask about authorization status\n• You can speak in Arabic or English",
        "feature1_title": "Multi-Language",
        "feature1_desc": "Arabic & English support",
        "feature2_title": "Real-Time",
        "feature2_desc": "Instant transcription",
        "feature3_title": "Accurate",
        "feature3_desc": "Powered by Whisper AI",
        "no_response": "No responses yet. Start a conversation first!",
    },
    "العربية": {
        "title": "🎤 المساعد الصوتي لدرع الحج",
        "subtitle": "تحدث بشكل طبيعي، احصل على التحقق الفوري",
        "instruction": "اضغط وتحدث أو ارفع ملف صوتي",
        "status": "سيتم تحويل صوتك إلى نص تلقائياً",
        "upload_label": "🎙️ سجل صوتك أو ارفع ملف صوتي",
        "converting": "جارٍ تحويل الصوت إلى نص...",
        "success": "تم التحويل بنجاح!",
        "transcribed": "النص المحول",
        "search_btn": "🔍 بحث الآن",
        "error": "حدث خطأ في التحويل",
        "tts_title": "🔊 الاستماع للردود",
        "listen_btn": "🔊 استمع للرد الأخير",
        "generating": "جارٍ توليد الصوت...",
        "audio_error": "حدث خطأ في توليد الصوت",
        "back": "→ العودة للرئيسية",
        "hint_title": "💡 نصائح صوتية",
        "hint_text": "• تحدث بوضوح وبسرعة عادية\n• اذكر اسم الشركة أو الموقع\n• اسأل عن حالة الاعتماد\n• يمكنك التحدث بالعربية أو الإنجليزية",
        "feature1_title": "متعدد اللغات",
        "feature1_desc": "دعم العربية والإنجليزية",
        "feature2_title": "فوري",
        "feature2_desc": "تحويل فوري للصوت",
        "feature3_title": "دقيق",
        "feature3_desc": "مدعوم بتقنية Whisper AI",
        "no_response": "لا توجد ردود بعد. ابدأ محادثة أولاً!",
    }
}

def t(key):
    return translations[lang].get(key, key)

# -----------------------------
# Main Layout
# -----------------------------
st.markdown("<div class='voice-interface'>", unsafe_allow_html=True)

# Back Button
col1, col2, col3 = st.columns([2, 6, 2])
with col1:
    if st.button(t("back"), key="back_button"):
        st.session_state.show_voice_interface = False
        st.switch_page("Home.py")

# Title Section
st.markdown(f"""
<h1 class='voice-title'>{t("title")}</h1>
<p style='font-size: 1.1rem; color: #666; margin-bottom: 2rem;'>{t("subtitle")}</p>
""", unsafe_allow_html=True)

# Voice Visualizer
recording_class = "recording" if st.session_state.is_recording else ""
st.markdown(f"""
<div class='voice-visualizer {recording_class}'>
    <div class='voice-icon'>🎤</div>
</div>
""", unsafe_allow_html=True)

# Instructions
st.markdown(f"""
<div class='voice-text'>{t("instruction")} 🎧</div>
<div class='voice-status'>{t("status")}</div>
""", unsafe_allow_html=True)

# Voice Tips
st.markdown(f"""
<div class='voice-hint {"rtl" if is_arabic else ""}'>
    <strong>{t("hint_title")}</strong><br>
    {t("hint_text").replace(chr(10), '<br>')}
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Audio Input Section
# -----------------------------
st.markdown("<br>", unsafe_allow_html=True)

col1, col2, col3 = st.columns([1, 3, 1])
with col2:
    audio_file = st.file_uploader(
        t("upload_label"),
        type=["wav", "mp3", "m4a", "ogg", "webm"],
        key="audio_upload",
        label_visibility="collapsed"
    )

if audio_file is not None:
    # Display audio player
    st.audio(audio_file, format=f"audio/{audio_file.type.split('/')[-1]}")
    
    # Transcribe button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 " + t("converting").replace("...", ""), type="primary", use_container_width=True):
            st.session_state.is_recording = True
            
            with st.spinner("🔄 " + t("converting")):
                try:
                    # Transcribe audio
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        language="ar" if is_arabic else "en"
                    )
                    transcribed_text = transcription.text
                    
                    st.session_state.is_recording = False
                    
                    # Success message
                    st.success("✅ " + t("success"))
                    
                    # Display transcribed text in a card
                    st.markdown(f"""
                    <div class='response-card {"rtl" if is_arabic else ""}'>
                        <strong style='color: #667eea;'>📝 {t("transcribed")}:</strong><br>
                        <div class='response-text'>{transcribed_text}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Search button
                    col1, col2, col3 = st.columns([1, 2, 1])
                    with col2:
                        if st.button(t("search_btn"), type="primary", use_container_width=True, key="search_now"):
                            st.session_state.selected_question = transcribed_text
                            st.session_state.show_voice_interface = False
                            st.switch_page("Home.py")
                
                except Exception as e:
                    st.session_state.is_recording = False
                    st.error(f"❌ {t('error')}: {str(e)}")

# Features Grid
st.markdown("<br>", unsafe_allow_html=True)
st.markdown("""
<div class='feature-grid'>
    <div class='feature-card'>
        <div class='feature-icon'>🌍</div>
        <div class='feature-title'>""" + t("feature1_title") + """</div>
        <div class='feature-desc'>""" + t("feature1_desc") + """</div>
    </div>
    <div class='feature-card'>
        <div class='feature-icon'>⚡</div>
        <div class='feature-title'>""" + t("feature2_title") + """</div>
        <div class='feature-desc'>""" + t("feature2_desc") + """</div>
    </div>
    <div class='feature-card'>
        <div class='feature-icon'>🎯</div>
        <div class='feature-title'>""" + t("feature3_title") + """</div>
        <div class='feature-desc'>""" + t("feature3_desc") + """</div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Text-to-Speech Section
# -----------------------------
st.markdown("<hr class='custom-divider'>", unsafe_allow_html=True)

st.markdown(f"""
<h2 style='color: #667eea; text-align: center; margin: 2rem 0 1rem 0;'>
    {t("tts_title")}
</h2>
""", unsafe_allow_html=True)

if st.session_state.chat_memory and len(st.session_state.chat_memory) > 1:
    # Find last assistant response
    last_response = None
    for msg in reversed(st.session_state.chat_memory):
        if msg.get("role") == "assistant":
            last_response = msg
            break
    
    if last_response:
        response_text = last_response.get("content", "")
        
        # Display response preview
        st.markdown(f"""
        <div class='response-card {"rtl" if is_arabic else ""}'>
            <strong style='color: #11998e;'>💬 {t("transcribed") if is_arabic else "Last Response"}:</strong><br>
            <div class='response-text'>{response_text[:200]}{'...' if len(response_text) > 200 else ''}</div>
        </div>
        """, unsafe_allow_html=True)
        
        # TTS Button
        col1, col2, col3 = st.columns([1, 2, 1])
        with col2:
            if st.button(t("listen_btn"), type="primary", use_container_width=True):
                with st.spinner("🎵 " + t("generating")):
                    try:
                        # Generate speech
                        speech_response = client.audio.speech.create(
                            model="tts-1",
                            voice="alloy",  # Use "shimmer" for female voice
                            input=response_text[:1000]  # Limit to 1000 chars
                        )
                        
                        # Save and play audio
                        with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                            tmp_file.write(speech_response.content)
                            tmp_file_path = tmp_file.name
                        
                        with open(tmp_file_path, "rb") as audio:
                            st.audio(audio.read(), format="audio/mp3")
                        
                        # Clean up
                        try:
                            os.unlink(tmp_file_path)
                        except:
                            pass
                    
                    except Exception as e:
                        st.error(f"❌ {t('audio_error')}: {str(e)}")
    else:
        st.info("ℹ️ " + t("no_response"))
else:
    st.info("ℹ️ " + t("no_response"))

st.markdown("</div>", unsafe_allow_html=True)