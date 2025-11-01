import streamlit as st
from openai import OpenAI
import io
from audio_recorder_streamlit import audio_recorder
from typing import TypedDict, Annotated, Literal
from langgraph.graph import StateGraph, END
from langgraph.prebuilt import ToolNode
import operator

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
        from { opacity: 0; transform: translateX(20px); }
        to { opacity: 1; transform: translateX(0); }
    }

    @keyframes slideInLeft {
        from { opacity: 0; transform: translateX(-20px); }
        to { opacity: 1; transform: translateX(0); }
    }

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

    .avatar-container {
        display: flex;
        justify-content: center;
        align-items: center;
        margin: 2rem auto;
        position: relative;
    }
    
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
    
    .ring {
        position: absolute;
        border: 3px solid rgba(255, 255, 255, 0.3);
        border-radius: 50%;
        animation: ripple 2s ease-out infinite;
    }
    
    .ring-1 { width: 170px; height: 170px; animation-delay: 0s; }
    .ring-2 { width: 210px; height: 210px; animation-delay: 0.5s; }
    .ring-3 { width: 250px; height: 250px; animation-delay: 1s; }
    
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
    
    @keyframes ripple {
        0% { transform: scale(1); opacity: 1; }
        100% { transform: scale(1.5); opacity: 0; }
    }

    .graph-status {
        background: rgba(255, 255, 255, 0.15);
        padding: 0.8rem;
        border-radius: 1rem;
        margin: 1rem auto;
        text-align: center;
        color: white;
        font-weight: 500;
        backdrop-filter: blur(10px);
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
# Node Functions (Tools)
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
        st.success(f"🗣️ Transcribed: *{transcript.text}*")
    except Exception as e:
        state["error"] = f"Transcription error: {str(e)}"
        st.error(state["error"])
    return state

def detect_intent_node(state: HajjAssistantState) -> HajjAssistantState:
    """Node: Detect user intent (GREETING, DATABASE, GENERAL_HAJJ)"""
    try:
        intent_prompt = f"""
You are a fraud-prevention assistant for Hajj pilgrims. Classify this message into ONE of three categories:

1️⃣ GREETING: greetings like hello, hi, how are you, salam, السلام عليكم, مرحبا
2️⃣ DATABASE: questions about verifying Hajj agencies, authorization, company details, locations
3️⃣ GENERAL_HAJJ: general Hajj questions (rituals, requirements, documents, safety)

CONTEXT: 415 fake offices closed in 2025, 269,000+ unauthorized pilgrims stopped

Message: {state['user_input']}

Respond with ONLY ONE WORD: GREETING, DATABASE, or GENERAL_HAJJ
"""
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[
                {"role": "system", "content": "You classify intents. Respond with one word."},
                {"role": "user", "content": intent_prompt}
            ],
            temperature=0,
            max_tokens=8
        )
        candidate = resp.choices[0].message.content.strip().upper()
        state["intent"] = candidate if candidate in ("GREETING", "DATABASE", "GENERAL_HAJJ") else "GENERAL_HAJJ"
        
        # Detect if Arabic
        state["is_arabic"] = any("\u0600" <= ch <= "\u06FF" for ch in state['user_input'])
        
        st.info(f"🎯 Intent detected: **{state['intent']}**")
    except Exception as e:
        state["error"] = f"Intent detection error: {str(e)}"
        state["intent"] = "GENERAL_HAJJ"
    return state

def handle_greeting_node(state: HajjAssistantState) -> HajjAssistantState:
    """Node: Handle greeting intent"""
    try:
        greeting_prompt = {
            "role": "system",
            "content": f"""You are a friendly Hajj assistant. Generate a warm greeting that:
            1. Acknowledges the user's greeting
            2. Expresses willingness to help
            3. Mentions you can verify Hajj companies and answer questions
            4. Keep it under 3 sentences with emojis
            {'5. Respond in Arabic' if state['is_arabic'] else '5. Respond in English'}"""
        }
        
        resp = client.chat.completions.create(
            model="gpt-4o-mini",
            messages=[greeting_prompt, {"role": "user", "content": state['user_input']}],
            temperature=0.7,
            max_tokens=150
        )
        state["response"] = resp.choices[0].message.content.strip()
    except Exception:
        state["response"] = (
            "السلام عليكم! 🌙 كيف يمكنني مساعدتك؟"
            if state['is_arabic'] else
            "Hello! 👋 How can I help you today?"
        )
    return state

def handle_database_node(state: HajjAssistantState) -> HajjAssistantState:
    """Node: Handle database queries about Hajj agencies"""
    response = f"""🔍 **Agency Verification Mode**

Your question: "{state['user_input']}"

⚠️ **Critical Security Alert:**
- 415 fake Hajj offices closed in 2025
- 269,000+ unauthorized pilgrims stopped
- Fraud prevention is our priority

💡 **How to verify agencies:**
1. Check official Ministry of Hajj database
2. Verify authorization status
3. Confirm physical office location
4. Read reviews and ratings

🔒 **Always book through AUTHORIZED agencies only!**

*Note: Connect your database to enable live queries. Add SQL generation logic from your original code.*"""
    
    state["response"] = response
    return state

def handle_general_hajj_node(state: HajjAssistantState) -> HajjAssistantState:
    """Node: Handle general Hajj questions"""
    try:
        system_prompt = """You are a knowledgeable Hajj assistant helping pilgrims with:
        - Hajj & Umrah rituals and procedures
        - Travel requirements and visa information
        - Health, safety, and cultural etiquette
        
        CRITICAL: Always emphasize using AUTHORIZED agencies.
        Context: 415 fake offices closed in 2025, 269,000+ unauthorized pilgrims stopped.
        
        Answer clearly in 2-4 sentences."""
        
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
        state["response"] = f"Sorry, error occurred: {str(e)}"
    return state

def text_to_speech_node(state: HajjAssistantState) -> HajjAssistantState:
    """Node: Convert text response to speech"""
    try:
        resp = client.audio.speech.create(
            model="tts-1",
            voice="alloy",
            input=state["response"]
        )
        state["response_audio"] = resp.content
        st.success("✅ Audio response generated!")
    except Exception as e:
        state["error"] = f"TTS error: {str(e)}"
        st.error(state["error"])
    return state

# ---------------------------------------
# Router Function
# ---------------------------------------
def route_intent(state: HajjAssistantState) -> Literal["greeting", "database", "general_hajj"]:
    """Route to appropriate handler based on intent"""
    intent = state.get("intent", "GENERAL_HAJJ")
    if intent == "GREETING":
        return "greeting"
    elif intent == "DATABASE":
        return "database"
    else:
        return "general_hajj"

# ---------------------------------------
# Build LangGraph Workflow
# ---------------------------------------
@st.cache_resource
def build_hajj_assistant_graph():
    """Build the LangGraph workflow"""
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
    
    # Conditional routing based on intent
    workflow.add_conditional_edges(
        "detect_intent",
        route_intent,
        {
            "greeting": "greeting",
            "database": "database",
            "general_hajj": "general_hajj"
        }
    )
    
    # All paths lead to TTS
    workflow.add_edge("greeting", "tts")
    workflow.add_edge("database", "tts")
    workflow.add_edge("general_hajj", "tts")
    workflow.add_edge("tts", END)
    
    return workflow.compile()

# ---------------------------------------
# Session State Setup
# ---------------------------------------
if "messages" not in st.session_state:
    st.session_state.messages = []
if "last_audio" not in st.session_state:
    st.session_state.last_audio = None
if "is_listening" not in st.session_state:
    st.session_state.is_listening = False
if "graph" not in st.session_state:
    st.session_state.graph = build_hajj_assistant_graph()

# ---------------------------------------
# UI Header
# ---------------------------------------
st.markdown('<div class="title">🕋 Hajj Voice Assistant</div>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Powered by LangGraph AI Workflow</div>', unsafe_allow_html=True)

# Animated avatar
avatar_active = "active" if st.session_state.is_listening else ""
st.markdown(f"""
<div class="avatar-container">
    <div class="ring ring-1"></div>
    <div class="ring ring-2"></div>
    <div class="ring ring-3"></div>
    <div class="avatar {avatar_active}">🕋</div>
</div>
""", unsafe_allow_html=True)

# Graph status
st.markdown('<div class="graph-status">🔄 LangGraph: Transcribe → Intent → Route → Response → TTS</div>', unsafe_allow_html=True)

# ---------------------------------------
# Recording Section
# ---------------------------------------
st.markdown('<div class="status-text">🎤 Press and hold to record</div>', unsafe_allow_html=True)

st.markdown('<div class="recorder-container">', unsafe_allow_html=True)
audio_bytes = audio_recorder(
    text="",
    recording_color="#ff1744",
    neutral_color="#ef4444",
    icon_name="microphone",
    icon_size="3x",
    pause_threshold=2.0,
    sample_rate=16000
)
st.markdown('</div>', unsafe_allow_html=True)

# ---------------------------------------
# Process Audio with LangGraph
# ---------------------------------------
if audio_bytes and audio_bytes != st.session_state.last_audio:
    st.session_state.last_audio = audio_bytes
    st.session_state.is_listening = True
    
    st.audio(audio_bytes, format="audio/wav")
    
    with st.spinner("⚙️ Processing through LangGraph workflow..."):
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
        response = final_state.get("response", "")
        response_audio = final_state.get("response_audio", b"")
        
        if transcript and response:
            # Update conversation history
            st.session_state.messages.append({"role": "user", "content": transcript})
            st.session_state.messages.append({"role": "assistant", "content": response})
            
            # Play audio response
            if response_audio:
                st.audio(response_audio, format="audio/mp3", autoplay=True)
            
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