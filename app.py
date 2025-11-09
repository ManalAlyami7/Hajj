"""
Hajj Chatbot - Main Application
Modern, elegant design with professional Islamic theme
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
# Modern Professional CSS
# -----------------------------
st.markdown("""
<style>
    @import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Cairo:wght@400;600;700;800&display=swap');
    
    /* ===== Global Styles ===== */
    * {
        font-family: 'Poppins', 'Cairo', sans-serif;
        transition: all 0.3s ease;
    }
    
    /* ===== Main Background - Clean White/Light ===== */
    .main {
        background: linear-gradient(135deg, #f8f9fa 0%, #e9ecef 100%);
        background-attachment: fixed;
    }
    
    .block-container {
        padding-top: 2.5rem;
        padding-bottom: 2.5rem;
        max-width: 1600px;
    }
    
    /* ===== Header Section ===== */
    .header-container {
        background: linear-gradient(135deg, #ffffff 0%, #f8f9fa 100%);
        backdrop-filter: blur(20px);
        border-radius: 24px;
        padding: 3rem 2.5rem;
        margin-bottom: 2.5rem;
        box-shadow: 0 10px 40px rgba(0, 0, 0, 0.08);
        text-align: center;
        border: 2px solid #d4af37;
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
        background: linear-gradient(90deg, #d4af37 0%, #f4e5b5 50%, #d4af37 100%);
    }
    
    .main-title {
        font-size: 3.5rem;
        font-weight: 900;
        color: #1a1f2e;
        margin: 0;
        letter-spacing: -0.5px;
        text-shadow: 2px 2px 4px rgba(0, 0, 0, 0.1);
    }
    
    .title-highlight {
        background: linear-gradient(135deg, #d4af37 0%, #f4e5b5 100%);
        -webkit-background-clip: text;
        -webkit-text-fill-color: transparent;
        background-clip: text;
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
        background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
        color: white;
        padding: 0.5rem 1.5rem;
        border-radius: 50px;
        font-size: 0.9rem;
        font-weight: 700;
        margin-top: 1rem;
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
    }
    
    /* ===== Chat Messages ===== */
    .stChatMessage {
        background: white !important;
        backdrop-filter: blur(10px);
        border-radius: 20px !important;
        padding: 2rem !important;
        margin: 1.5rem 0 !important;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.06) !important;
        border: 2px solid #f1f5f9;
        transition: all 0.3s ease !important;
    }
    
    .stChatMessage:hover {
        transform: translateY(-3px);
        box-shadow: 0 8px 30px rgba(0, 0, 0, 0.1) !important;
        border-color: #d4af37;
    }
    
    /* User Message */
    .stChatMessage[data-testid*="user"] {
        background: linear-gradient(135deg, #e0f2fe 0%, #bae6fd 100%) !important;
        border-left: 5px solid #0ea5e9;
    }
    
    /* Assistant Message */
    .stChatMessage[data-testid*="assistant"] {
        background: linear-gradient(135deg, #fef9e7 0%, #fef3c7 100%) !important;
        border-left: 5px solid #d4af37;
    }
    
    /* ===== Sidebar Styling ===== */
    [data-testid="stSidebar"] {
        background: linear-gradient(180deg, #1a1f2e 0%, #0f1419 100%);
        border-right: 3px solid #d4af37;
    }
    
    [data-testid="stSidebar"] .block-container {
        padding: 2rem 1.5rem;
    }
    
    /* All sidebar text white */
    [data-testid="stSidebar"] *,
    [data-testid="stSidebar"] p,
    [data-testid="stSidebar"] span,
    [data-testid="stSidebar"] div,
    [data-testid="stSidebar"] label {
        color: #f8fafc !important;
    }
    
    [data-testid="stSidebar"] h1,
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {
        color: #d4af37 !important;
        font-weight: 800;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }
    
    /* Hide default navigation */
    [data-testid="stSidebarNav"] {
        display: none !important;
    }
    
    /* Sidebar Buttons */
    [data-testid="stSidebar"] .stButton > button {
        background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%) !important;
        color: white !important;
        border: 2px solid #d4af37 !important;
        border-radius: 14px !important;
        padding: 1rem 1.5rem !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
        transition: all 0.3s ease !important;
        width: 100% !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        box-shadow: 0 4px 15px rgba(212, 175, 55, 0.3);
    }
    
    [data-testid="stSidebar"] .stButton > button:hover {
        background: linear-gradient(135deg, #f4e5b5 0%, #d4af37 100%) !important;
        transform: translateY(-3px);
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.5);
    }
    
    /* Stat Cards */
    .stat-card {
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.08) 100%);
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
        box-shadow: 0 10px 30px rgba(212, 175, 55, 0.4);
        border-color: rgba(212, 175, 55, 0.7);
    }
    
    .stat-number {
        font-size: 3rem;
        font-weight: 900;
        color: #d4af37;
        margin-bottom: 0.5rem;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
        line-height: 1;
    }
    
    .stat-label {
        color: #f8fafc;
        font-size: 1rem;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 1.5px;
    }
    
    /* Radio Buttons */
    [data-testid="stSidebar"] .stRadio > div {
        background: rgba(212, 175, 55, 0.1);
        padding: 1rem;
        border-radius: 14px;
        border: 2px solid rgba(212, 175, 55, 0.3);
    }
    
    [data-testid="stSidebar"] .stRadio label {
        color: #f8fafc !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }
    
    /* Dividers */
    [data-testid="stSidebar"] hr {
        border-color: rgba(212, 175, 55, 0.3) !important;
        border-width: 2px !important;
        margin: 2rem 0;
    }
    
    /* Chat Input */
    .stChatInput > div {
        border-radius: 24px;
        border: 2px solid #d4af37;
        background: white;
        box-shadow: 0 4px 20px rgba(0, 0, 0, 0.08);
    }
    
    .stChatInput > div:focus-within {
        border-color: #b8941f;
        box-shadow: 0 0 0 4px rgba(212, 175, 55, 0.15);
    }
    
    .stChatInput input {
        color: #1a1f2e !important;
        font-size: 1.05rem !important;
        font-weight: 500;
    }
    
    .stChatInput input::placeholder {
        color: #94a3b8 !important;
    }
    
    /* Scrollbar */
    ::-webkit-scrollbar {
        width: 10px;
        height: 10px;
    }
    
    ::-webkit-scrollbar-track {
        background: #f1f5f9;
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb {
        background: linear-gradient(180deg, #d4af37 0%, #b8941f 100%);
        border-radius: 10px;
    }
    
    ::-webkit-scrollbar-thumb:hover {
        background: linear-gradient(180deg, #f4e5b5 0%, #d4af37 100%);
    }
    
    /* RTL Support */
    .rtl {
        direction: rtl;
        text-align: right;
    }
    
    /* Animations */
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
    
    @keyframes fadeIn {
        from {
            opacity: 0;
        }
        to {
            opacity: 1;
        }
    }
    
    /* Loading Animation */
    .stSpinner > div {
        border-color: #d4af37 !important;
    }
    
    /* Success/Error Messages */
    .stSuccess {
        background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
        border-left: 5px solid #22c55e;
        border-radius: 12px;
        color: #065f46 !important;
    }
    
    .stError {
        background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
        border-left: 5px solid #ef4444;
        border-radius: 12px;
        color: #991b1b !important;
    }
    
    .stInfo {
        background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
        border-left: 5px solid #3b82f6;
        border-radius: 12px;
        color: #1e40af !important;
    }
    
    /* Quick Actions Grid */
    .quick-actions-grid {
        display: grid;
        grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
        gap: 1.5rem;
        margin: 2rem 0;
    }
    
    /* Feature Badge */
    .feature-badge {
        display: inline-flex;
        align-items: center;
        gap: 0.5rem;
        background: rgba(212, 175, 55, 0.1);
        border: 2px solid rgba(212, 175, 55, 0.3);
        border-radius: 50px;
        padding: 0.5rem 1rem;
        font-size: 0.9rem;
        font-weight: 600;
        color: #d4af37;
        margin: 0.25rem;
    }
    
    /* Responsive Design */
    @media (max-width: 768px) {
        .main-title {
            font-size: 2.5rem;
        }
        
        .header-container {
            padding: 2rem 1.5rem;
        }
        
        .stat-card {
            padding: 1.5rem;
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
# Initialize Application
# -----------------------------
def main():
    """Main application entry point"""
    
    # Initialize session state
    initialize_session_state()
    
    # Load existing chat memory
    try:
        load_chat_memory()
    except Exception:
        pass

    # Trim session memory
    _trim_session_memory()
    
    # Persist trimmed memory
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
    
    # Render modern header with translated badge
    lang = st.session_state.language
    is_rtl = lang in ['العربية', 'اردو']
    
    # Build the badge text with translations - check all possible language values
    if 'عرب' in lang or lang == 'العربية' or lang == 'Arabic':
        badge_text = f"✨ مدعوم بالذكاء الاصطناعي • فوري • متعدد اللغات"
    elif 'اردو' in lang or lang == 'Urdu':
        badge_text = f"✨ AI سے چلنے والا • حقیقی وقت • کثیر لسانی"
    else:  # English
        badge_text = f"✨ AI-Powered • Real-Time • Multilingual"
    
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