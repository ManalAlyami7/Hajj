"""
Hajj Chatbot - Main Application
Production-ready Streamlit chatbot for Hajj agency verification
"""

import streamlit as st
from datetime import datetime
import pytz

# Import core modules
from core.database import DatabaseManager
from core.llm import LLMManager
from core.graph import ChatGraph
from ui.chat import ChatInterface
from ui.sidebar import SidebarInterface
from utils.translations import t, TRANSLATIONS
from utils.validators import validate_user_input
from utils.state import initialize_session_state, save_chat_memory, load_chat_memory

# -----------------------------
# Page Configuration
# -----------------------------
st.set_page_config(
    page_title="Hajj Chatbot",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# Custom CSS
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
        max-width: 1400px;
    }
    
    .header-container {
        background: rgba(255, 255, 255, 0.95);
        backdrop-filter: blur(10px);
        border-radius: 20px;
        padding: 2rem;
        margin-bottom: 2rem;
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.1);
        text-align: center;
        animation: fadeInDown 0.6s ease-out;
    }
    
    .main-title {
        font-size: 3rem;
        font-weight: 700;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin: 0;
    }
    
    .subtitle {
        color: #666;
        font-size: 1.1rem;
        margin-top: 0.5rem;
    }
    
    .stChatMessage {
        background: rgba(255, 255, 255, 0.95) !important;
        backdrop-filter: blur(10px);
        border-radius: 18px !important;
        padding: 1.5rem !important;
        margin: 1rem 0 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08) !important;
        border: 1px solid rgba(255, 255, 255, 0.3);
        transition: transform 0.2s ease;
    }
    
    .stChatMessage:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 25px rgba(0, 0, 0, 0.12) !important;
    }
    
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1e3a5f 0%, #2c5f8d 100%);
    }
    
    [data-testid="stSidebar"] .element-container {
        color: white;
    }
    
    [data-testid="stSidebar"] h3 {
        color: white !important;
        font-weight: 600;
        margin-top: 1rem;
    }
    
    .stat-card {
        background: linear-gradient(135deg, rgba(255, 255, 255, 0.1) 0%, rgba(255, 255, 255, 0.05) 100%);
        backdrop-filter: blur(10px);
        padding: 1.5rem;
        border-radius: 15px;
        text-align: center;
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.1);
        margin: 0.5rem 0;
        border: 1px solid rgba(255, 255, 255, 0.2);
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.2);
    }
    
    .stat-number {
        font-size: 2.5rem;
        font-weight: 700;
        background: linear-gradient(135deg, #ffd89b 0%, #19547b 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        margin-bottom: 0.5rem;
    }
    
    .stat-label {
        color: rgba(255, 255, 255, 0.9);
        font-size: 0.95rem;
        font-weight: 500;
        text-transform: uppercase;
        letter-spacing: 1px;
    }
    
    .stButton button {
        background: rgba(255, 255, 255, 0.1) !important;
        color: white !important;
        border: 1px solid rgba(255, 255, 255, 0.3) !important;
        border-radius: 12px !important;
        padding: 0.75rem 1rem !important;
        font-weight: 500 !important;
        transition: all 0.3s ease !important;
        text-align: left !important;
    }
    
    .stButton button:hover {
        background: rgba(255, 255, 255, 0.2) !important;
        transform: translateX(8px);
        border-color: rgba(255, 255, 255, 0.5) !important;
    }
    
    .stRadio > div {
        background: rgba(255, 255, 255, 0.1);
        padding: 0.5rem;
        border-radius: 10px;
    }
    
    .stRadio label {
        color: white !important;
    }
    
    .stDownloadButton button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%) !important;
        color: white !important;
        border: none !important;
        border-radius: 10px !important;
        padding: 0.6rem 1.5rem !important;
        font-weight: 600 !important;
        transition: all 0.3s ease !important;
    }
    
    .stDownloadButton button:hover {
        transform: translateY(-2px);
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4) !important;
    }
    
    .rtl {
        direction: rtl;
        text-align: right;
    }
    
    @keyframes fadeInDown {
        from {
            opacity: 0;
            transform: translateY(-30px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    ::-webkit-scrollbar {
        width: 8px;
        height: 8px;
    }
    
    ::-webkit-scrollbar-track {
        background: rgba(255, 255, 255, 0.1);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: rgba(255, 255, 255, 0.3);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: rgba(255, 255, 255, 0.5);
    }
</style>
""", unsafe_allow_html=True)
# ...existing code...
def _trim_session_memory(max_messages: int = 80, max_message_chars: int = 1000):
    """Keep only the last N chat messages and truncate long texts to save memory."""
    if "chat_memory" in st.session_state and isinstance(st.session_state.chat_memory, list):
        # keep last N messages
        st.session_state.chat_memory = st.session_state.chat_memory[-max_messages:]
        # truncate long message contents
        for m in st.session_state.chat_memory:
            if isinstance(m.get("content"), str) and len(m["content"]) > max_message_chars:
                m["content"] = m["content"][: max_message_chars - 3] + "..."
            # keep dataframe preview small if present
            if isinstance(m.get("dataframe"), list):
                m["dataframe"] = m["dataframe"][:50]

    # free known heavy objects if present
    st.session_state.pop("last_result_df", None)
    st.session_state.pop("openai_client", None)


# ...existing code...
# -----------------------------
# Initialize Application
# -----------------------------
def main():
    """Main application entry point"""
    
    # Initialize session state
    # Call after session init/load to enforce limits
    initialize_session_state()
    # load existing chat memory (if your flow loads elsewhere, keep a single call)
    try:
        load_chat_memory()
    except Exception:
        # ignore load errors but proceed to trimming
        pass

    _trim_session_memory()
    # persist trimmed memory
    try:
        save_chat_memory()
    except Exception:
        pass
    
    # Initialize core managers
    db_manager = DatabaseManager()
    llm_manager = LLMManager()
    chat_graph = ChatGraph(db_manager, llm_manager)
    
    # Initialize UI components
    sidebar = SidebarInterface(db_manager)
    chat_ui = ChatInterface(chat_graph, llm_manager)
    
    # Render sidebar
    sidebar.render()
    
    # Render header
    lang = st.session_state.language
    st.markdown(f"""
    <div class="header-container{' rtl' if lang == 'العربية' else ''}">
        <h1>
            🕋 <span class="main-title">{t('main_title', lang)}</span>
        </h1>
        <p class="subtitle">{t('subtitle', lang)}</p>
    </div>
    """, unsafe_allow_html=True)
    
    # Voice assistant button
   
   # if st.button("🎙️ " + t("voice_assistant", lang)):
      #  try:
           # st.switch_page("pages/voicebot.py")
       # except Exception:
           # st.info(t("voice_not_available", lang))
    
    # Render chat interface
    chat_ui.render()

if __name__ == "__main__":
    main()
