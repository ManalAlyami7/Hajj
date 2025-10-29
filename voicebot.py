import streamlit as st
from openai import OpenAI
import tempfile
import os

# -----------------------------
# Helper: Initialize OpenAI client
# -----------------------------
def get_openai_client():
    """Initialize OpenAI client from Streamlit secrets"""
    api_key = st.secrets.get("OPENAI_API_KEY", None)
    if not api_key:
        st.warning("⚠️ OpenAI API key missing. Add it to Streamlit secrets.")
        st.stop()
    return OpenAI(api_key=api_key)

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Voice Bot Assistant",
    page_icon="🎤",
    layout="centered"
)

# -----------------------------
# Modern CSS Styling with Animations
# -----------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&display=swap');
    
    * {
        font-family: 'Inter', sans-serif;
    }
    
    .main {
        background: linear-gradient(135deg, #0f172a 0%, #1e293b 100%);
        background-attachment: fixed;
    }
    
    .block-container {
        padding: 3rem 1rem;
        max-width: 800px;
    }
    
    /* Main Card */
    .voice-card {
        background: rgba(255, 255, 255, 0.98);
        backdrop-filter: blur(20px);
        border-radius: 32px;
        padding: 3rem 2.5rem;
        box-shadow: 0 25px 80px rgba(0, 0, 0, 0.3);
        animation: fadeInUp 0.6s ease-out;
    }
    
    @keyframes fadeInUp {
        from {
            opacity: 0;
            transform: translateY(40px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    /* Title */
    .voice-title {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        text-align: center;
        margin-bottom: 0.5rem;
        line-height: 1.2;
    }
    
    .voice-subtitle {
        font-size: 1.1rem;
        color: #64748b;
        text-align: center;
        margin-bottom: 3rem;
        font-weight: 500;
    }
    
    /* Animated Microphone Button */
    .mic-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 3rem 0;
        position: relative;
    }
    
    .mic-button {
        width: 200px;
        height: 200px;
        border-radius: 50%;
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%);
        display: flex;
        align-items: center;
        justify-content: center;
        cursor: pointer;
        position: relative;
        transition: all 0.4s cubic-bezier(0.4, 0, 0.2, 1);
        box-shadow: 0 20px 60px rgba(59, 130, 246, 0.4);
        animation: pulse 3s ease-in-out infinite;
    }
    
    .mic-button:hover {
        transform: scale(1.08);
        box-shadow: 0 25px 70px rgba(59, 130, 246, 0.5);
    }
    
    .mic-button.active {
        background: linear-gradient(135deg, #ef4444 0%, #f97316 100%);
        animation: recording 1.2s ease-in-out infinite;
    }
    
    @keyframes pulse {
        0%, 100% {
            transform: scale(1);
            box-shadow: 0 20px 60px rgba(59, 130, 246, 0.4), 0 0 0 0 rgba(59, 130, 246, 0.7);
        }
        50% {
            transform: scale(1.03);
            box-shadow: 0 20px 60px rgba(59, 130, 246, 0.4), 0 0 0 35px rgba(59, 130, 246, 0);
        }
    }
    
    @keyframes recording {
        0%, 100% {
            transform: scale(1);
            box-shadow: 0 20px 60px rgba(239, 68, 68, 0.5), 0 0 0 0 rgba(239, 68, 68, 0.8);
        }
        50% {
            transform: scale(1.08);
            box-shadow: 0 20px 60px rgba(239, 68, 68, 0.5), 0 0 0 45px rgba(239, 68, 68, 0);
        }
    }
    
    .mic-icon {
        font-size: 5.5rem;
        filter: drop-shadow(0 6px 15px rgba(0, 0, 0, 0.25));
    }
    
    /* Status Text */
    .status-text {
        text-align: center;
        font-size: 1.2rem;
        color: #3b82f6;
        font-weight: 600;
        margin: 1.5rem 0;
        animation: fadeIn 0.5s ease-in;
    }
    
    .status-hint {
        text-align: center;
        font-size: 0.95rem;
        color: #94a3b8;
        margin-bottom: 2rem;
        line-height: 1.6;
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    /* Info Card */
    .info-card {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.08) 0%, rgba(139, 92, 246, 0.08) 100%);
        border-left: 4px solid #3b82f6;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 2rem 0;
    }
    
    .info-title {
        font-weight: 600;
        color: #1e293b;
        margin-bottom: 0.75rem;
        font-size: 1.05rem;
    }
    
    .info-list {
        color: #475569;
        line-height: 1.8;
        font-size: 0.95rem;
    }
    
    /* Feature Grid */
    .feature-grid {
        display: grid;
        grid-template-columns: repeat(3, 1fr);
        gap: 1.25rem;
        margin: 2.5rem 0;
    }
    
    .feature-item {
        background: linear-gradient(135deg, rgba(59, 130, 246, 0.05) 0%, rgba(139, 92, 246, 0.05) 100%);
        border-radius: 16px;
        padding: 1.5rem 1rem;
        text-align: center;
        transition: all 0.3s ease;
        border: 1px solid rgba(59, 130, 246, 0.15);
    }
    
    .feature-item:hover {
        transform: translateY(-5px);
        box-shadow: 0 12px 35px rgba(59, 130, 246, 0.15);
        border-color: rgba(59, 130, 246, 0.3);
    }
    
    .feature-icon {
        font-size: 2.5rem;
        margin-bottom: 0.5rem;
    }
    
    .feature-label {
        font-weight: 600;
        color: #3b82f6;
        font-size: 0.9rem;
        margin-bottom: 0.25rem;
    }
    
    .feature-desc {
        font-size: 0.85rem;
        color: #64748b;
    }
    
    /* Response Card */
    .response-card {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.08) 0%, rgba(5, 150, 105, 0.08) 100%);
        border-left: 4px solid #10b981;
        border-radius: 16px;
        padding: 1.5rem;
        margin: 1.5rem 0;
        animation: slideIn 0.4s ease-out;
    }
    
    @keyframes slideIn {
        from {
            opacity: 0;
            transform: translateX(-20px);
        }
        to {
            opacity: 1;
            transform: translateX(0);
        }
    }
    
    .response-label {
        font-weight: 600;
        color: #10b981;
        margin-bottom: 0.75rem;
        font-size: 1rem;
    }
    
    .response-text {
        color: #1e293b;
        line-height: 1.7;
        font-size: 1rem;
    }
    
    /* Buttons */
    .stButton button {
        background: linear-gradient(135deg, #3b82f6 0%, #8b5cf6 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 14px !important;
        padding: 0.85rem 2rem !important;
        font-weight: 600 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        box-shadow: 0 8px 25px rgba(59, 130, 246, 0.3) !important;
    }
    
    .stButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 12px 35px rgba(59, 130, 246, 0.4) !important;
    }
    
    /* File Uploader */
    .uploadedFile {
        background: rgba(59, 130, 246, 0.05);
        border-radius: 14px;
        padding: 1.25rem;
        border: 2px dashed #3b82f6;
        transition: all 0.3s ease;
    }
    
    .uploadedFile:hover {
        border-color: #8b5cf6;
        background: rgba(139, 92, 246, 0.05);
    }
    
    /* Audio Player */
    audio {
        width: 100%;
        border-radius: 12px;
        margin: 1.5rem 0;
    }
    
    /* Divider */
    .divider {
        height: 2px;
        background: linear-gradient(90deg, transparent, #e2e8f0, transparent);
        margin: 2.5rem 0;
        border: none;
    }
    
    /* Loading Spinner */
    .stSpinner > div {
        border-color: #3b82f6 transparent transparent transparent !important;
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background: linear-gradient(135deg, rgba(16, 185, 129, 0.1) 0%, rgba(5, 150, 105, 0.1) 100%);
        border-left: 4px solid #10b981;
        border-radius: 12px;
    }
    
    .stError {
        background: linear-gradient(135deg, rgba(239, 68, 68, 0.1) 0%, rgba(220, 38, 38, 0.1) 100%);
        border-left: 4px solid #ef4444;
        border-radius: 12px;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .voice-title {
            font-size: 2rem;
        }
        
        .mic-button {
            width: 160px;
            height: 160px;
        }
        
        .mic-icon {
            font-size: 4.5rem;
        }
        
        .feature-grid {
            grid-template-columns: 1fr;
            gap: 1rem;
        }
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------
# Initialize Session State
# -----------------------------
if "is_recording" not in st.session_state:
    st.session_state.is_recording = False
if "transcribed_text" not in st.session_state:
    st.session_state.transcribed_text = None
if "last_response" not in st.session_state:
    st.session_state.last_response = None

# -----------------------------
# Main Interface
# -----------------------------
st.markdown("<div class='voice-card'>", unsafe_allow_html=True)

# Header
st.markdown("""
<h1 class='voice-title'>Voice Bot Assistant</h1>
<p class='voice-subtitle'>Speak naturally and let AI understand you</p>
""", unsafe_allow_html=True)

# Animated Microphone Button
recording_class = "active" if st.session_state.is_recording else ""
st.markdown(f"""
<div class='mic-container'>
    <div class='mic-button {recording_class}'>
        <div class='mic-icon'>🎤</div>
    </div>
</div>
""", unsafe_allow_html=True)

# Status Text
if st.session_state.is_recording:
    st.markdown("<div class='status-text'>🔴 Recording in progress...</div>", unsafe_allow_html=True)
else:
    st.markdown("<div class='status-text'>Ready to listen</div>", unsafe_allow_html=True)

st.markdown("<div class='status-hint'>Click below to upload audio or record your voice</div>", unsafe_allow_html=True)

# -----------------------------
# Audio Upload Section
# -----------------------------
st.markdown("<br>", unsafe_allow_html=True)



if audio_file is not None:
    # Display audio player
    st.audio(audio_file, format=f"audio/{audio_file.type.split('/')[-1]}")
    
    # Transcribe button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🎯 Transcribe Audio", type="primary", use_container_width=True):
            st.session_state.is_recording = True
            
            with st.spinner("🔄 Converting speech to text..."):
                try:
                    client = get_openai_client()
                    
                    # Transcribe audio using Whisper
                    transcription = client.audio.transcriptions.create(
                        model="whisper-1",
                        file=audio_file,
                        response_format="text"
                    )
                    
                    st.session_state.transcribed_text = transcription
                    st.session_state.is_recording = False
                    
                    # Success message
                    st.success("✅ Transcription completed successfully!")
                    
                    # Display transcribed text
                    st.markdown(f"""
                    <div class='response-card'>
                        <div class='response-label'>📝 Transcribed Text:</div>
                        <div class='response-text'>{transcription}</div>
                    </div>
                    """, unsafe_allow_html=True)
                    
                    # Store as last response for TTS
                    st.session_state.last_response = transcription
                    
                except Exception as e:
                    st.session_state.is_recording = False
                    st.error(f"❌ Transcription error: {str(e)}")

# -----------------------------
# UX Tips Section
# -----------------------------
st.markdown("""
<div class='info-card'>
    <div class='info-title'>💡 Voice Interaction Tips</div>
    <div class='info-list'>
        • Speak clearly at a normal pace for best results<br>
        • Supported formats: WAV, MP3, M4A, OGG, WebM, FLAC<br>
        • Maximum file size: 25 MB<br>
        • Works with multiple languages automatically<br>
        • Background noise may affect accuracy
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Features Grid
# -----------------------------
st.markdown("""
<div class='feature-grid'>
    <div class='feature-item'>
        <div class='feature-icon'>🌍</div>
        <div class='feature-label'>Multi-Language</div>
        <div class='feature-desc'>Auto-detect language</div>
    </div>
    <div class='feature-item'>
        <div class='feature-icon'>⚡</div>
        <div class='feature-label'>Real-Time</div>
        <div class='feature-desc'>Instant transcription</div>
    </div>
    <div class='feature-item'>
        <div class='feature-icon'>🎯</div>
        <div class='feature-label'>High Accuracy</div>
        <div class='feature-desc'>Powered by Whisper AI</div>
    </div>
</div>
""", unsafe_allow_html=True)

# -----------------------------
# Text-to-Speech Section
# -----------------------------
if st.session_state.last_response:
    st.markdown("<hr class='divider'>", unsafe_allow_html=True)
    
    st.markdown("""
    <h2 style='color: #3b82f6; text-align: center; margin: 2rem 0 1.5rem 0; font-size: 1.8rem;'>
        🔊 Listen to Response
    </h2>
    """, unsafe_allow_html=True)
    
    # Display response preview
    preview_text = st.session_state.last_response[:200]
    if len(st.session_state.last_response) > 200:
        preview_text += "..."
    
    st.markdown(f"""
    <div class='response-card'>
        <div class='response-label'>💬 Text Preview:</div>
        <div class='response-text'>{preview_text}</div>
    </div>
    """, unsafe_allow_html=True)
    
    # TTS Button
    col1, col2, col3 = st.columns([1, 2, 1])
    with col2:
        if st.button("🔊 Generate Audio", type="primary", use_container_width=True):
            with st.spinner("🎵 Generating audio..."):
                try:
                    client = get_openai_client()
                    
                    # Generate speech using TTS
                    speech_response = client.audio.speech.create(
                        model="tts-1",
                        voice="alloy",
                        input=st.session_state.last_response[:4000]  # Limit to 4000 chars
                    )
                    
                    # Save and play audio
                    with tempfile.NamedTemporaryFile(delete=False, suffix=".mp3") as tmp_file:
                        tmp_file.write(speech_response.content)
                        tmp_file_path = tmp_file.name
                    
                    with open(tmp_file_path, "rb") as audio:
                        st.audio(audio.read(), format="audio/mp3")
                    
                    st.success("✅ Audio generated successfully!")
                    
                    # Clean up
                    try:
                        os.unlink(tmp_file_path)
                    except:
                        pass
                
                except Exception as e:
                    st.error(f"❌ Audio generation error: {str(e)}")

st.markdown("</div>", unsafe_allow_html=True)

# -----------------------------
# Footer
# -----------------------------
st.markdown("""
<div style='text-align: center; margin-top: 3rem; padding: 2rem; color: #94a3b8; font-size: 0.9rem;'>
    <p>Powered by OpenAI Whisper & TTS • Built with Streamlit</p>
    <p style='margin-top: 0.5rem;'>🎤 Professional voice interaction with modern UX principles</p>
</div>
""", unsafe_allow_html=True)
