import streamlit as st
from openai import OpenAI
import io
from audio_recorder_streamlit import audio_recorder
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
import operator
import time

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
# Enhanced Custom CSS
# ---------------------------------------
st.markdown("""
<style>
    .stApp {
        background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
        background-attachment: fixed;
        overflow: hidden;
    }
    
    #MainMenu {visibility: hidden;}
    footer {visibility: hidden;}
    header {visibility: hidden;}

    /* Main Container - Fixed height, no scroll */
    .main .block-container {
        padding: 2rem 1rem;
        max-width: 1200px;
        height: 90vh;
        overflow: hidden;
        display: flex;
        flex-direction: column;
        justify-content: center;
    }

    /* Header Section */
    .header-container {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 1rem;
    }

    .title {
        color: white;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
        text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        letter-spacing: 1px;
    }

    .subtitle {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        margin-bottom: 0.3rem;
        font-weight: 500;
    }

    .powered-by {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.85rem;
        margin-top: 0.3rem;
    }

    /* Avatar Section */
    .avatar-section {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 1rem auto;
        padding: 1.5rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 2rem;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .avatar-container {
        position: relative;
        margin-bottom: 1rem;
    }
    
    .avatar {
        width: 160px;
        height: 160px;
        background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 80px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
        animation: pulse 2s ease-in-out infinite;
        position: relative;
        z-index: 2;
        border: 5px solid rgba(255, 255, 255, 0.3);
    }
    
    .ring {
        position: absolute;
        border: 3px solid rgba(255, 255, 255, 0.2);
        border-radius: 50%;
        animation: ripple 2.5s ease-out infinite;
    }
    
    .ring-1 { width: 180px; height: 180px; animation-delay: 0s; }
    .ring-2 { width: 220px; height: 220px; animation-delay: 0.7s; }
    .ring-3 { width: 260px; height: 260px; animation-delay: 1.4s; }
    
    .avatar.active {
        animation: pulse-active 0.6s ease-in-out infinite;
        box-shadow: 0 25px 80px rgba(126, 34, 206, 0.6);
        border-color: rgba(255, 255, 255, 0.6);
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.03); }
    }
    
    @keyframes pulse-active {
        0%, 100% { transform: scale(1); box-shadow: 0 25px 80px rgba(126, 34, 206, 0.6); }
        50% { transform: scale(1.1); box-shadow: 0 30px 100px rgba(126, 34, 206, 0.9); }
    }
    
    @keyframes ripple {
        0% { transform: scale(0.95); opacity: 0.8; }
        100% { transform: scale(1.6); opacity: 0; }
    }

    /* Status Badge */
    .status-badge {
        display: inline-block;
        padding: 0.7rem 1.8rem;
        background: rgba(255, 255, 255, 0.15);
        border-radius: 2rem;
        color: white;
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }

    .status-badge.listening {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        animation: glow 1.5s ease-in-out infinite;
    }

    @keyframes glow {
        0%, 100% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.5); }
        50% { box-shadow: 0 0 40px rgba(239, 68, 68, 0.8); }
    }

    /* Workflow Status */
    .workflow-status {
        background: rgba(255, 255, 255, 0.1);
        padding: 0.8rem;
        border-radius: 1rem;
        margin: 1rem 0;
        text-align: center;
        color: white;
        font-weight: 500;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.15);
        font-size: 0.85rem;
    }

    .workflow-step {
        display: inline-block;
        padding: 0.3rem 0.8rem;
        background: rgba(126, 34, 206, 0.3);
        border-radius: 1rem;
        margin: 0 0.2rem;
        font-size: 0.75rem;
    }

    /* Toast Notification - Fixed position */
    .toast-notification {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 2rem;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        z-index: 9999;
        max-width: 600px;
        width: 90%;
        animation: toastFadeIn 0.5s ease-out;
    }

    .toast-notification.fade-out {
        animation: toastFadeOut 0.5s ease-out forwards;
    }

    @keyframes toastFadeIn {
        from {
            opacity: 0;
            transform: translate(-50%, -60%);
        }
        to {
            opacity: 1;
            transform: translate(-50%, -50%);
        }
    }

    @keyframes toastFadeOut {
        from {
            opacity: 1;
            transform: translate(-50%, -50%);
        }
        to {
            opacity: 0;
            transform: translate(-50%, -60%);
        }
    }

    .toast-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #e5e7eb;
    }

    .toast-icon {
        font-size: 2.5rem;
        margin-right: 1rem;
    }

    .toast-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1a1a1a;
    }

    .toast-content {
        color: #374151;
        line-height: 1.6;
        font-size: 1rem;
    }

    .toast-transcript {
        background: #f3f4f6;
        padding: 1rem;
        border-radius: 1rem;
        margin: 1rem 0;
        font-style: italic;
        color: #4b5563;
    }

    .toast-response {
        margin-top: 1rem;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 1rem;
    }

    .toast-intent {
        display: inline-block;
        padding: 0.3rem 1rem;
        background: #7e22ce;
        color: white;
        border-radius: 1rem;
        font-size: 0.85rem;
        margin: 0.5rem 0;
    }

    /* Buttons */
    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        border-radius: 3rem;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        border: 2px solid transparent;
    }

    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.6);
        border-color: rgba(255, 255, 255, 0.3);
    }

    /* Hide scrollbar */
    ::-webkit-scrollbar {
        display: none;
    }

    /* Processing indicators */
    .stSpinner > div {
        border-color: rgba(126, 34, 206, 0.3) !important;
        border-top-color: #7e22ce !important;
    }

    /* Success/Error messages - as toasts */
    .stSuccess, .stError, .stInfo {
        position: fixed !important;
        top: 20px !important;
        right: 20px !important;
        z-index: 9999 !important;
        max-width: 400px !important;
        animation: slideInRight 0.3s ease-out !important;
    }

    @keyframes slideInRight {
        from { transform: translateX(100%); }
        to { transform: translateX(0); }
    }

    /* Responsive */
    @media (max-width: 768px) {
        .title { font-size: 2rem; }
        .subtitle { font-size: 0.95rem; }
        .avatar { width: 120px; height: 120px; font-size: 60px; }
        .toast-notification { width: 95%; padding: 1.5rem; }
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
        st.error("⚠️ Please add your OPENAI_API_KEY to Streamlit secrets")
        st.stop()
    return OpenAI(api_key=api_key)

client = get_openai_client()

# ---------------------------------------
# LangGraph State Definition
# ---------------------------------------
class HajjAssistantState(TypedDict):
    """State for the Hajj Assistant workflow"""
    user_input: str
    transcript: str
    intent: str
    response: str
    audio_bytes: bytes
    response_audio: bytes
    error: str
    messages_history: Annotated[list, operator.add]
    is_arabic: bool

# ---------------------------------------
# Node Functions
# ---------------------------------------
def transcribe_audio_node(state: HajjAssistantState) -> HajjAssistantState:
    """Node: Transcribe audio to text using Whisper"""
    try:
        audio_file = io.BytesIO(state["audio_bytes"])
        audio_file.name = "audio.wav"
        transcript = client.audio.transcriptions.create(
            model="whisper-1",
            file=audio_file,
            language="en"
        )
        state["transcript"] = transcript.text
        state["user_input"] = transcript.text
    except Exception as e:
        state["error"] = f"Transcription error: {str(e)}"
    return state

def detect_intent_node(state: HajjAssistantState) -> HajjAssistantState:
    """Node: Detect user intent"""
    try:
        intent_prompt = f"""
Classify this message into ONE category:

1️⃣ GREETING: greetings like hello, hi, salam, السلام عليكم
2️⃣ DATABASE: questions about Hajj agencies, authorization, company verification
3️⃣ GENERAL_HAJJ: general Hajj questions (rituals, requirements, documents)

Message: {state['user_input']}

Respond with ONLY: GREETING, DATABASE, or GENERAL_HAJJ
"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "Classify intents. One word only."},
                {"role": "user", "content": intent_prompt}
            ],
            temperature=0,
            max_tokens=8
        )
        candidate = resp.choices[0].message.content.strip().upper()
        state["intent"] = candidate if candidate in ("GREETING", "DATABASE", "GENERAL_HAJJ") else "GENERAL_HAJJ"
        state["is_arabic"] = any("\u0600" <= ch <= "\u06FF" for ch in state['user_input'])
    except Exception as e:
        state["error"] = f"Intent detection error: {str(e)}"
        state["intent"] = "GENERAL_HAJJ"
    return state

def handle_greeting_node(state: HajjAssistantState) -> HajjAssistantState:
    """Node: Handle greetings"""
    try:
        greeting_prompt = f"""Generate a warm greeting (2-3 sentences with emojis):
        1. Acknowledge the greeting
        2. Offer help with Hajj agencies and questions
        {'3. Respond in Arabic' if state['is_arabic'] else '3. Respond in English'}"""
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": greeting_prompt},
                {"role": "user", "content": state['user_input']}
            ],
            temperature=0.7,
            max_tokens=150
        )
        state["response"] = resp.choices[0].message.content.strip()
    except Exception:
        state["response"] = (
            "السلام عليكم! 🌙 كيف يمكنني مساعدتك اليوم؟"
            if state['is_arabic'] else
            "Hello! 👋 How can I assist you today?"
        )
    return state

def handle_database_node(state: HajjAssistantState) -> HajjAssistantState:
    """Node: Handle database queries"""
    response = f"""🔍 **Agency Verification System**

**Your Question:** {state['user_input']}

⚠️ **Critical Alert:**
• 415 fake Hajj offices closed in 2025
• 269,000+ unauthorized pilgrims stopped
• Always verify before booking!

✅ **Verification Steps:**
1. Check Ministry of Hajj official database
2. Verify authorization status
3. Confirm physical office location
4. Read authentic reviews

🔒 **Book only through AUTHORIZED agencies!**"""
    
    state["response"] = response
    return state

def handle_general_hajj_node(state: HajjAssistantState) -> HajjAssistantState:
    """Node: Handle general Hajj questions"""
    try:
        system_prompt = """You are a knowledgeable Hajj assistant. Help with:
        - Hajj & Umrah rituals
        - Travel requirements
        - Health & safety guidelines
        
        CRITICAL: Always emphasize using AUTHORIZED agencies.
        Context: 415 fake offices closed, 269,000+ unauthorized pilgrims stopped in 2025.
        
        Answer in 2-4 clear sentences."""
        
        messages = [{"role": "system", "content": system_prompt}]
        messages.extend(state.get("messages_history", [])[-6:])
        messages.append({"role": "user", "content": state['user_input']})
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=messages,
            temperature=0.6,
            max_tokens=400
        )
        state["response"] = resp.choices[0].message.content.strip()
    except Exception as e:
        state["response"] = f"Sorry, an error occurred: {str(e)}"
    return state

def text_to_speech_node(state: HajjAssistantState) -> HajjAssistantState:
    """Node: Convert text to speech"""
    try:
        resp = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=state["response"]
        )
        state["response_audio"] = resp.content
    except Exception as e:
        state["error"] = f"TTS error: {str(e)}"
    return state

# ---------------------------------------
# Router Function
# ---------------------------------------
def route_intent(state: HajjAssistantState) -> Literal["greeting", "database", "general_hajj"]:
    """Route based on intent"""
    intent = state.get("intent", "GENERAL_HAJJ")
    return intent.lower() if intent in ("GREETING", "DATABASE") else "general_hajj"

# ---------------------------------------
# Build LangGraph
# ---------------------------------------
@st.cache_resource
def build_hajj_assistant_graph():
    """Build the workflow graph"""
    workflow = StateGraph(HajjAssistantState)
    
    # Add nodes
    workflow.add_node("transcribe", transcribe_audio_node)
    workflow.add_node("detect_intent", detect_intent_node)
    workflow.add_node("greeting", handle_greeting_node)
    workflow.add_node("database", handle_database_node)
    workflow.add_node("general_hajj", handle_general_hajj_node)
    workflow.add_node("tts", text_to_speech_node)
    
    # Define edges
    workflow.set_entry_point("transcribe")
    workflow.add_edge("transcribe", "detect_intent")
    
    # Conditional routing
    workflow.add_conditional_edges(
        "detect_intent",
        route_intent,
        {
            "greeting": "greeting",
            "database": "database",
            "general_hajj": "general_hajj"
        }
    )
    
    # All paths to TTS
    workflow.add_edge("greeting", "tts")
    workflow.add_edge("database", "tts")
    workflow.add_edge("general_hajj", "tts")
    workflow.add_edge("tts", END)
    
    return workflow.compile()

# ---------------------------------------
# Session State
# ---------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None
if "is_listening" not in st.session_state:
    st.session_state.is_listening = False
if "graph" not in st.session_state:
    st.session_state.graph = build_hajj_assistant_graph()
if "show_toast" not in st.session_state:
    st.session_state.show_toast = False
if "toast_data" not in st.session_state:
    st.session_state.toast_data = {}
if "toast_timestamp" not in st.session_state:
    st.session_state.toast_timestamp = 0

# ---------------------------------------
# UI Layout
# ---------------------------------------

# Header
st.markdown("""
<div class="header-container">
    <div class="title">🕋 Hajj Voice Assistant</div>
    <div class="subtitle">Intelligent AI Guide for Hajj & Umrah Pilgrimage</div>
    <div class="powered-by">⚡ Powered by LangGraph & OpenAI</div>
</div>
""", unsafe_allow_html=True)

# Main container with 3 columns
col1, col2, col3 = st.columns([1, 2, 1])

with col2:
    # Avatar section
    avatar_active = "active" if st.session_state.is_listening else ""
    st.markdown(f"""
    <div class="avatar-section">
        <div class="avatar-container">
            <div class="ring ring-1"></div>
            <div class="ring ring-2"></div>
            <div class="ring ring-3"></div>
            <div class="avatar {avatar_active}">🕋</div>
        </div>
        
       
    </div>
    """, unsafe_allow_html=True)
    
    
    
    # Recording button
    audio_bytes = audio_recorder(
        text="Hold to Record",
        recording_color="#ff1744",
        neutral_color="#ef4444",
        icon_name="microphone",
        icon_size="4x",
        pause_threshold=2.0,
        sample_rate=16000,
        key="audio_recorder"
    )

# ---------------------------------------
# Toast Notification Display
# ---------------------------------------
if st.session_state.show_toast:
    current_time = time.time()
    elapsed = current_time - st.session_state.toast_timestamp
    
    if elapsed < 10:  # Show for 10 seconds
        fade_class = "fade-out" if elapsed > 9 else ""
        toast_data = st.session_state.toast_data
        
        st.markdown(f"""
        <div class="toast-notification {fade_class}">
            <div class="toast-header">
                <div class="toast-icon">💬</div>
                <div>
                    <div class="toast-title">Conversation</div>
                    <span class="toast-intent">Intent: {toast_data.get('intent', 'Unknown')}</span>
                </div>
            </div>
            <div class="toast-content">
                <div class="toast-transcript">
                    <strong>You said:</strong> {toast_data.get('transcript', '')}
                </div>
                <div class="toast-response">
                    <strong>Assistant:</strong><br>{toast_data.get('response', '')}
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
    else:
        st.session_state.show_toast = False

# ---------------------------------------
# Process Audio
# ---------------------------------------
if audio_bytes and audio_bytes != st.session_state.last_audio:
    st.session_state.last_audio = audio_bytes
    st.session_state.is_listening = True
    
    with col2:
        with st.spinner("⚙️ Processing through AI workflow..."):
            # Initialize state
            initial_state = {
                "audio_bytes": audio_bytes,
                "user_input": "",
                "transcript": "",
                "intent": "",
                "response": "",
                "response_audio": b"",
                "error": "",
                "messages_history": st.session_state.messages,
                "is_arabic": False
            }
            
            # Run the graph
            final_state = st.session_state.graph.invoke(initial_state)
            
            # Extract results
            transcript = final_state.get("transcript", "")
            intent = final_state.get("intent", "")
            response = final_state.get("response", "")
            response_audio = final_state.get("response_audio", b"")
            error = final_state.get("error", "")
            
            if error:
                st.error(f"❌ {error}")
            elif transcript and response:
                # Update history
                st.session_state.messages.append({"role": "user", "content": transcript})
                st.session_state.messages.append({"role": "assistant", "content": response})
                
                # Set toast data
                st.session_state.show_toast = True
                st.session_state.toast_timestamp = time.time()
                st.session_state.toast_data = {
                    "transcript": transcript,
                    "intent": intent,
                    "response": response
                }
                
                # Play audio response
                if response_audio:
                    st.audio(response_audio, format="audio/mp3", autoplay=True)
                
                st.session_state.is_listening = False
                st.rerun()
else:
    st.session_state.is_listening = False

# Auto-refresh to hide toast after 10 seconds
if st.session_state.show_toast:
    time.sleep(0.1)
    st.rerun()