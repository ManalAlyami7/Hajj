"""
Hajj Chatbot - Main Application
Modern, elegant design with professional Golden Islamic theme
COMPLETE GOLDEN THEME FILE
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
    page_title="Hajj Assistant Chatbot",
    page_icon="🕋",
    layout="wide",
    initial_sidebar_state="expanded"
)

# -----------------------------
# GOLDEN THEME CSS - COMPLETE
# -----------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Cairo:wght@400;600;700;800&family=Noto+Nastaliq+Urdu:wght@400;600;700&display=swap');
    
    /* ===== Golden Theme Variables ===== */
    :root {
        --color-primary-gold: #d4af37;
        --color-secondary-gold: #b8941f;
        --color-dark-gold: #9d7a1a;
        --color-light-gold: #e6c345;
        --color-gold-glow: rgba(212, 175, 55, 0.3);
        --color-bg-light: #f8fafc;
        --color-bg-mid: #e2e8f0;
    }
    
    /* ===== Global Styles ===== */
    * {
        font-family: 'Poppins', 'Cairo', sans-serif;
        transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    }
    
    /* ===== Main Background ===== */
    .main {
        background: linear-gradient(135deg, var(--color-bg-light) 0%, var(--color-bg-mid) 100%);
        background-attachment: fixed;
    }
    
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 2.5rem;
        max-width: 1600px;
    }
    
    /* ===== Header Section - GOLDEN ===== */
    .header-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 3rem 2.5rem;
        margin-bottom: 2.5rem;
        box-shadow: 0 10px 40px rgba(212, 175, 55, 0.15);
        text-align: center;
        border: 2px solid var(--color-primary-gold);
        animation: fadeInDown 0.6s ease-out;
        position: relative;
        overflow: hidden;
    }
    
    .header-container::before {
        content: '';
        position: absolute;
        top: 0;
        left: 0;
        right: 0;
        height: 5px;
        background: linear-gradient(90deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 50%, var(--color-primary-gold) 100%);
        animation: shimmer 3s infinite;
    }
    
    @keyframes shimmer {
        0%, 100% { opacity: 1; }
        50% { opacity: 0.7; }
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
    
    .main-title {
        font-size: 3.5rem;
        font-weight: 900;
        color: #1f2937;
        margin: 0;
        letter-spacing: -0.5px;
    }
    
    .title-highlight {
        background: linear-gradient(135deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
        filter: drop-shadow(0 2px 4px var(--color-gold-glow));
    }
    
    .subtitle {
        color: #64748b;
        font-size: 1.25rem;
        margin-top: 1rem;
        font-weight: 500;
        line-height: 1.6;
    }
    
    .header-badge {
        display: inline-block;
        background: linear-gradient(135deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 100%);
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        font-size: 0.9rem;
        font-weight: 700;
        margin-top: 1rem;
        box-shadow: 0 4px 15px var(--color-gold-glow);
    }
    
    /* ===== Chat Messages - GOLDEN ===== */
    .stChatMessage {
        background: white !important;
        backdrop-filter: blur(10px);
        border-radius: 20px !important;
        padding: 2rem !important;
        margin: 1.5rem 0 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06) !important;
        border: 2px solid #e2e8f0;
        transition: all 0.3s ease !important;
        animation: slideUp 0.3s ease-out;
    }
    
    @keyframes slideUp {
        from {
            opacity: 0;
            transform: translateY(10px);
        }
        to {
            opacity: 1;
            transform: translateY(0);
        }
    }
    
    .stChatMessage:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(212, 175, 55, 0.2) !important;
        border-color: var(--color-primary-gold);
    }
    
    /* User Message - Golden Light */
    .stChatMessage[data-testid*="user"] {
        background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%) !important;
        border-left: 5px solid var(--color-primary-gold);
    }
    
    /* Assistant Message */
    .stChatMessage[data-testid*="assistant"] {
        background: linear-gradient(135deg, #f9fafb 0%, #f8fafc 100%) !important;
        border-left: 5px solid var(--color-secondary-gold);
    }
    
    /* ===== SIDEBAR - GOLDEN DARK ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f2e 0%, #0f1419 100%) !important;
        border-right: 3px solid var(--color-primary-gold) !important;
        box-shadow: 2px 0 20px var(--color-gold-glow) !important;
    }
    
    [data-testid="stSidebar"] .block-container {
        padding: 2rem 1.5rem !important;
    }
    
    /* Sidebar Text - ALL WHITE */
    [data-testid="stSidebar"],
    [data-testid="stSidebar"] *,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label,
    [data-testid="stSidebar"] .stMarkdown {
        color: #f8fafc !important;
    }
    
    /* Sidebar Headers - GOLDEN */
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: var(--color-primary-gold) !important;
        font-weight: 800 !important;
        text-shadow: 0 2px 8px var(--color-gold-glow) !important;
    }
    
    /* Hide Navigation */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Sidebar Buttons - GOLDEN */
    [data-testid="stSidebar"] .stButton > button,
    [data-testid="stSidebar"] button {
        background: linear-gradient(135deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 100%) !important;
        color: white !important;
        border: 2px solid var(--color-primary-gold) !important;
        border-radius: 14px !important;
        padding: 1rem 1.5rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2) !important;
        box-shadow: 0 4px 15px var(--color-gold-glow) !important;
    }
    
    [data-testid="stSidebar"] .stButton > button:hover,
    [data-testid="stSidebar"] button:hover {
        background: linear-gradient(135deg, var(--color-light-gold) 0%, var(--color-primary-gold) 100%) !important;
        transform: translateY(-3px) !important;
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.5) !important;
    }
    
    /* Collapsed Sidebar Button - GOLDEN */
    [data-testid="collapsedControl"] {
        background: linear-gradient(135deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 100%) !important;
        color: white !important;
        border-radius: 0.5rem !important;
        padding: 0.5rem !important;
        box-shadow: 0 4px 12px var(--color-gold-glow) !important;
        transition: all 0.3s ease !important;
    }
    
    [data-testid="collapsedControl"]:hover {
        background: linear-gradient(135deg, var(--color-secondary-gold) 0%, var(--color-dark-gold) 100%) !important;
        transform: scale(1.05) !important;
        box-shadow: 0 6px 16px rgba(212, 175, 55, 0.5) !important;
    }
    
    /* Stat Cards - GOLDEN */
    .stat-card {
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.08) 100%) !important;
        backdrop-filter: blur(10px);
        padding: 2rem;
        border-radius: 18px;
        text-align: center;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.2);
        margin: 1rem 0;
        border: 2px solid rgba(212, 175, 55, 0.4);
        transition: all 0.3s ease;
    }
    
    .stat-card:hover {
        transform: translateY(-5px) scale(1.02);
        box-shadow: 0 10px 30px var(--color-gold-glow);
        border-color: var(--color-primary-gold);
    }
    
    .stat-number {
        font-size: 3rem;
        font-weight: 900;
        color: var(--color-primary-gold) !important;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 8px var(--color-gold-glow);
        line-height: 1;
    }
    
    .stat-label {
        color: #f8fafc !important;
        font-size: 1rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    /* Radio Buttons - GOLDEN */
    [data-testid="stSidebar"] .stRadio > div {
        background: rgba(212, 175, 55, 0.1) !important;
        padding: 1rem;
        border-radius: 14px;
        border: 2px solid rgba(212, 175, 55, 0.3);
    }
    
    [data-testid="stSidebar"] .stRadio label {
        color: #f8fafc !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }
    
    /* Dividers - GOLDEN */
    [data-testid="stSidebar"] hr {
        border-color: rgba(212, 175, 55, 0.3) !important;
        border-width: 2px !important;
        margin: 2rem 0 !important;
    }
    
    /* Chat Input - GOLDEN */
    .stChatInput > div {
        border-radius: 24px;
        border: 2px solid var(--color-primary-gold);
        background: white;
        box-shadow: 0 4px 20px rgba(212, 175, 55, 0.15);
        transition: all 0.3s ease;
    }
    
    .stChatInput > div:focus-within {
        border-color: var(--color-secondary-gold);
        box-shadow: 0 0 0 4px var(--color-gold-glow);
    }
    
    .stChatInput input {
        color: #1f2937 !important;
        font-size: 1.05rem !important;
        font-weight: 500;
    }
    
    /* Primary Buttons - GOLDEN */
    button[kind="primary"],
    .stButton > button[kind="primary"],
    div[data-testid="stButton"] > button[kind="primary"] {
        background: linear-gradient(135deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 100%) !important;
        border: none !important;
        box-shadow: 0 4px 15px var(--color-gold-glow) !important;
        color: white !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        padding: 0.75rem 1.5rem !important;
        transition: all 0.3s ease !important;
    }
    
    button[kind="primary"]:hover {
        transform: translateY(-2px) !important;
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.5) !important;
        background: linear-gradient(135deg, var(--color-light-gold) 0%, var(--color-primary-gold) 100%) !important;
    }
    
    /* Secondary Buttons - GOLDEN */
    button[kind="secondary"],
    .stButton > button[kind="secondary"] {
        background: white !important;
        border: 2px solid var(--color-primary-gold) !important;
        color: var(--color-secondary-gold) !important;
        font-weight: 600 !important;
        border-radius: 12px !important;
        transition: all 0.3s ease !important;
    }
    
    button[kind="secondary"]:hover {
        background: linear-gradient(135deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 100%) !important;
        color: white !important;
        transform: translateY(-2px) !important;
    }
    
    /* Scrollbar - GOLDEN */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 100%);
        border-radius: 10px;
        box-shadow: 0 2px 8px var(--color-gold-glow);
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, var(--color-light-gold) 0%, var(--color-primary-gold) 100%);
    }
    
    /* Loading - GOLDEN */
    .stSpinner > div {
        border-color: var(--color-primary-gold) !important;
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-left: 5px solid #22c55e;
        border-radius: 12px;
    }
    
    .stError {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 5px solid #ef4444;
        border-radius: 12px;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
        border-left: 5px solid var(--color-primary-gold);
        border-radius: 12px;
    }
    
    /* RTL Support */
    .rtl {
        direction: rtl;
        text-align: right;
    }
    
    /* Responsive */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.5rem;
        }
        .header-container {
            padding: 2rem 1.5rem;
        }
        .stat-number {
            font-size: 2.5rem;
        }
    }
</style>
""", unsafe_allow_html=True)

def _trim_session_memory(max_messages: int = 80, max_message_chars: int = 1000):
    """Keep only the last N chat messages and truncate long texts to save memory."""
    if "chat_memory" in st.session_state and isinstance(st.session_state.chat_memory, list):
        st.session_state.chat_memory = st.session_state.chat_memory[-max_messages:]
        for m in st.session_state.chat_memory:
            if isinstance(m.get("content"), str) and len(m["content"]) > max_message_chars:
                m["content"] = m["content"][: max_message_chars - 3] + "..."
            if isinstance(m.get("dataframe"), list):
                m["dataframe"] = m["dataframe"][:50]

    st.session_state.pop("last_result_df", None)
    st.session_state.pop("openai_client", None)


# -----------------------------
# Main Application
# -----------------------------
def main():
    """Main application entry point"""
    
    # Initialize session state
    initialize_session_state()
    
    # Initialize core managers
    db_manager = DatabaseManager()
    llm_manager = LLMManager()
    chat_graph = ChatGraph(db_manager, llm_manager)
    
    # Initialize UI components
    sidebar = SidebarInterface(db_manager)
    chat_ui = ChatInterface(chat_graph, llm_manager)
    
    # Render sidebar
    sidebar.render()
    
    # Render GOLDEN header
    lang = st.session_state.language
    is_rtl = lang in ['العربية', 'اردو']
    
    # Badge text
    if 'عرب' in lang or lang == 'العربية' or lang == 'Arabic':
        badge_text = "✨ مدعوم بالذكاء الاصطناعي • فوري • متعدد اللغات"
    elif 'اردو' in lang or lang == 'Urdu':
        badge_text = "✨ AI سے چلنے والا • حقیقی وقت • کثیر لسانی"
    else:
        badge_text = "✨ AI-Powered • Real-Time • Multilingual"
    
    st.markdown(f"""
    <div class="header-container{' rtl' if is_rtl else ''}">
        <h1 class="main-title">
            🕋 <span class="title-highlight">{t('main_title', lang)}</span>
        </h1>
        <p class="subtitle">{t('subtitle', lang)}</p>
        <div class="header-badge">
            {badge_text}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render chat interface
    chat_ui.render()

if __name__ == "__main__":
    main()

