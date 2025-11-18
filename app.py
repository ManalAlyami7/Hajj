"""
Hajj Complaint Reporting Bot - Main Application
Enhanced UX with Golden Theme matching main app
Multi-language support: English, Arabic, Urdu
COMPLETE GOLDEN THEME FILE
"""

import streamlit as st
from datetime import datetime
import pytz
import time
from typing import Dict, Optional, Tuple
import logging

# Supabase imports
from supabase import create_client, Client

# Import core modules
from core.report_llm import RLLMManager
from utils.translations import t, LANGUAGE_MAP

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# CONSTANTS
# =============================================================================
COMPLAINT_STATUS = {
    "pending": "Pending Review",
    "under_investigation": "Under Investigation",
    "resolved": "Resolved",
    "closed": "Closed"
}


# =============================================================================
# SUPABASE CONFIGURATION
# =============================================================================

def get_supabase_client() -> Optional[Client]:
    """Initialize and return Supabase client with proper error handling"""
    @st.cache_resource
    def init_client() -> Optional[Client]:
        try:
            url = st.secrets.get('supabase_url')
            key = st.secrets.get("supabase_key")
            
            if not url or not key:
                logger.error("Supabase credentials missing in secrets")
                return None
                
            return create_client(url, key)
            
        except Exception as e:
            logger.error(f"Failed to initialize Supabase: {e}")
            return None
    
    client = init_client()
    if client is None:
        lang = st.session_state.get("language", "العربية")
        st.error(t("db_connection_error", lang))
        st.stop()
    return client


# =============================================================================
# CSS STYLING - COMPLETE GOLDEN THEME
# =============================================================================

def get_css_styles(lang: str) -> str:
    """Generate CSS with RTL support and GOLDEN THEME"""
    is_rtl = lang in ["العربية", "اردو"]
    text_align = "right" if is_rtl else "left"
    direction = "rtl" if is_rtl else "ltr"
    
    # Font selection
    if lang == "العربية":
        font_family = "'Cairo', 'Poppins', sans-serif"
    elif lang == "اردو":
        font_family = "'Noto Nastaliq Urdu', 'Cairo', 'Poppins', sans-serif"
    else:
        font_family = "'Poppins', sans-serif"
    
    return f"""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Cairo:wght@400;600;700;800&family=Noto+Nastaliq+Urdu:wght@400;600;700&display=swap');

/* ===== GOLDEN THEME VARIABLES ===== */
:root {{
    --color-primary-gold: #d4af37;
    --color-secondary-gold: #b8941f;
    --color-dark-gold: #9d7a1a;
    --color-light-gold: #e6c345;
    --color-gold-glow: rgba(212, 175, 55, 0.3);
    --color-bg-light: #f8fafc;
    --color-bg-mid: #e2e8f0;
    --color-text-dark: #1f2937;
    --color-text-mid: #64748b;
    --color-border: #e2e8f0;
}}

/* ===== Global Styles ===== */
* {{
    font-family: {font_family};
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}}

.main {{
    direction: {direction};
    text-align: {text_align};
    background: linear-gradient(135deg, var(--color-bg-light) 0%, var(--color-bg-mid) 100%);
    background-attachment: fixed;
}}

.block-container {{
    padding-top: 2.5rem;
    padding-bottom: 2.5rem;
    max-width: 1400px;
}}

/* ===== GOLDEN Header ===== */
.header-container {{
    background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
    backdrop-filter: blur(15px);
    border-radius: 20px;
    padding: 2.5rem 2rem;
    margin-bottom: 2.5rem;
    box-shadow: 0 8px 30px rgba(212, 175, 55, 0.15);
    text-align: center;
    border: 2px solid var(--color-primary-gold);
    animation: fadeInDown 0.6s ease-out;
    position: relative;
    overflow: hidden;
    direction: {direction};
}}

.header-container::before {{
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 4px;
    background: linear-gradient(90deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 50%, var(--color-primary-gold) 100%);
    animation: shimmer 3s infinite;
}}

@keyframes shimmer {{
    0%, 100% {{ opacity: 1; }}
    50% {{ opacity: 0.7; }}
}}

@keyframes fadeInDown {{
    from {{ opacity: 0; transform: translateY(-30px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

.main-title {{
    font-size: 3.2rem;
    font-weight: 900;
    color: var(--color-text-dark);
    margin: 0;
    letter-spacing: -1px;
}}

.title-highlight {{
    background: linear-gradient(135deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
    filter: drop-shadow(0 2px 4px var(--color-gold-glow));
}}

.subtitle {{
    color: var(--color-text-mid);
    font-size: 1.1rem;
    margin-top: 0.5rem;
    font-weight: 400;
    line-height: 1.6;
}}

.header-badge {{
    background: linear-gradient(135deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 100%);
    color: white;
    padding: 0.3rem 1.15rem;
    border-radius: 50px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 1rem;
    box-shadow: 0 4px 15px var(--color-gold-glow);
    display: inline-block;
}}

/* ===== Progress Bar - GOLDEN ===== */
.progress-container {{
    background: white;
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    border: 1px solid var(--color-border);
    direction: {direction};
}}

.progress-bar {{
    width: 100%;
    height: 6px;
    background: var(--color-border);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 0.5rem;
}}

.progress-fill {{
    height: 100%;
    background: linear-gradient(90deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 100%);
    border-radius: 10px;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
    box-shadow: 0 2px 8px var(--color-gold-glow);
}}

.progress-text {{
    display: flex;
    justify-content: space-between;
    color: var(--color-text-mid);
    font-size: 0.85rem;
    font-weight: 500;
    direction: {direction};
}}

/* ===== Modal - GOLDEN ===== */
.modal-icon {{
    font-size: 3rem;
    margin-bottom: 0.75rem;
    color: var(--color-primary-gold);
    filter: drop-shadow(0 2px 8px var(--color-gold-glow));
}}

.modal-title {{
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--color-text-dark);
    margin-bottom: 0.75rem;
}}

.modal-text {{
    color: var(--color-text-mid);
    font-size: 1rem;
    font-weight: 400;
    line-height: 1.5;
    margin-bottom: 1.5rem;
}}

/* ===== Chat Messages - GOLDEN ===== */
.stChatMessage {{
    background: white !important;
    backdrop-filter: blur(8px);
    border-radius: 16px !important;
    padding: 1.5rem !important;
    margin: 1rem 0 !important;
    box-shadow: 0 2px 15px rgba(0, 0, 0, 0.05) !important;
    border: 1px solid var(--color-border);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    animation: slideInUp 0.4s ease-out;
    direction: {direction};
    text-align: {text_align};
}}

.stChatMessage:hover {{
    transform: translateY(-1px);
    box-shadow: 0 5px 20px rgba(212, 175, 55, 0.15) !important;
    border-color: var(--color-primary-gold);
}}

.stChatMessage[data-testid*="user"] {{
    background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%) !important;
    border-{text_align}: 4px solid var(--color-primary-gold);
}}

.stChatMessage[data-testid*="assistant"] {{
    background: linear-gradient(135deg, #f9fafb 0%, #f8fafc 100%) !important;
    border-{text_align}: 4px solid var(--color-secondary-gold);
}}

.bot-message {{
    background: linear-gradient(135deg, #fffbeb 0%, #fef3c7 100%) !important;
    border: 2px solid var(--color-primary-gold) !important;
    border-{text_align}: 6px solid var(--color-primary-gold) !important;
    color: var(--color-text-dark) !important;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 4px 15px rgba(212, 175, 55, 0.15);
    font-weight: 500;
    direction: {direction};
    text-align: {text_align};
}}

.bot-message * {{
    color: var(--color-text-dark) !important;
}}

@keyframes slideInUp {{
    from {{ opacity: 0; transform: translateY(10px); }}
    to {{ opacity: 1; transform: translateY(0); }}
}}

/* ===== SIDEBAR - GOLDEN DARK ===== */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #1a1f2e 0%, #0f1419 100%) !important;
    border-{text_align}: 3px solid var(--color-primary-gold) !important;
    box-shadow: 2px 0 20px var(--color-gold-glow) !important;
    direction: {direction};
    text-align: {text_align};
}}

[data-testid="stSidebar"],
[data-testid="stSidebar"] *,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label {{
    color: #f8fafc !important;
}}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {{
    color: var(--color-primary-gold) !important;
    font-weight: 800 !important;
    text-shadow: 0 2px 8px var(--color-gold-glow) !important;
}}

/* Sidebar Buttons - GOLDEN */
[data-testid="stSidebar"] .stButton > button,
[data-testid="stSidebar"] button {{
    background: linear-gradient(135deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 100%) !important;
    color: white !important;
    border: 2px solid var(--color-primary-gold) !important;
    border-radius: 14px !important;
    padding: 1rem 1.5rem !important;
    font-weight: 700 !important;
    transition: all 0.3s ease !important;
    box-shadow: 0 4px 15px var(--color-gold-glow) !important;
}}

[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] button:hover {{
    background: linear-gradient(135deg, var(--color-light-gold) 0%, var(--color-primary-gold) 100%) !important;
    transform: translateY(-3px) !important;
    box-shadow: 0 6px 20px rgba(212, 175, 55, 0.5) !important;
}}

/* Progress indicator in sidebar - GOLDEN */
[data-testid="stSidebar"] .progress-indicator {{
    background: rgba(212, 175, 55, 0.15) !important;
    padding: 0.75rem;
    border-radius: 8px;
    margin: 1rem 0;
    border: 2px solid rgba(212, 175, 55, 0.3);
}}

/* Collapsed Sidebar Button - GOLDEN */
[data-testid="collapsedControl"] {{
    background: linear-gradient(135deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 100%) !important;
    color: white !important;
    border-radius: 0.5rem !important;
    box-shadow: 0 4px 12px var(--color-gold-glow) !important;
}}

[data-testid="collapsedControl"]:hover {{
    background: linear-gradient(135deg, var(--color-secondary-gold) 0%, var(--color-dark-gold) 100%) !important;
    transform: scale(1.05) !important;
    box-shadow: 0 6px 16px rgba(212, 175, 55, 0.5) !important;
}}

/* ===== ALL BUTTONS - GOLDEN ===== */
button[kind="primary"],
.stButton > button[kind="primary"],
div[data-testid="stButton"] > button[kind="primary"] {{
    background: linear-gradient(135deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 100%) !important;
    border: none !important;
    box-shadow: 0 4px 15px var(--color-gold-glow) !important;
    color: white !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    padding: 0.75rem 1.5rem !important;
    transition: all 0.3s ease !important;
}}

button[kind="primary"]:hover,
.stButton > button[kind="primary"]:hover {{
    transform: translateY(-2px) !important;
    box-shadow: 0 6px 20px rgba(212, 175, 55, 0.5) !important;
    background: linear-gradient(135deg, var(--color-light-gold) 0%, var(--color-primary-gold) 100%) !important;
}}

button[kind="secondary"],
.stButton > button[kind="secondary"] {{
    background: white !important;
    border: 2px solid var(--color-primary-gold) !important;
    color: var(--color-secondary-gold) !important;
    font-weight: 600 !important;
    border-radius: 12px !important;
    transition: all 0.3s ease !important;
}}

button[kind="secondary"]:hover {{
    background: linear-gradient(135deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 100%) !important;
    color: white !important;
    transform: translateY(-2px) !important;
    box-shadow: 0 4px 15px var(--color-gold-glow) !important;
}}

/* Chat Input - GOLDEN */
.stChatInput > div {{
    border-radius: 24px;
    border: 2px solid var(--color-primary-gold);
    background: white;
    box-shadow: 0 4px 20px rgba(212, 175, 55, 0.15);
}}

.stChatInput > div:focus-within {{
    border-color: var(--color-secondary-gold);
    box-shadow: 0 0 0 4px var(--color-gold-glow);
}}

/* Draft notification - GOLDEN */
.draft-notification {{
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border-left: 4px solid var(--color-primary-gold);
    border-radius: 12px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 4px 12px var(--color-gold-glow);
}}

.draft-notification h3 {{
    color: var(--color-secondary-gold);
    margin-bottom: 1rem;
}}

/* Scrollbar - GOLDEN */
::-webkit-scrollbar {{
    width: 10px;
}}

::-webkit-scrollbar-track {{
    background: #f1f5f9;
    border-radius: 10px;
}}

::-webkit-scrollbar-thumb {{
    background: linear-gradient(180deg, var(--color-primary-gold) 0%, var(--color-secondary-gold) 100%);
    border-radius: 10px;
}}

::-webkit-scrollbar-thumb:hover {{
    background: linear-gradient(180deg, var(--color-light-gold) 0%, var(--color-primary-gold) 100%);
}}

/* Success/Error Messages */
.stSuccess {{
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    border-left: 5px solid #22c55e;
    border-radius: 12px;
}}

.stError {{
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
    border-left: 5px solid #ef4444;
    border-radius: 12px;
}}

.stInfo {{
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border-left: 5px solid var(--color-primary-gold);
    border-radius: 12px;
}}

.stWarning {{
    background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%);
    border-left: 5px solid #f59e0b;
    border-radius: 12px;
}}
</style>
"""


# =============================================================================
# TRANSLATION ADDITIONS
# =============================================================================

REPORT_TRANSLATIONS = {
    "English": {
        "report_page_title": "Hajj Complaint Reporting",
        "report_main_title": "Confidential Reporting Office",
        "report_subtitle": "Secure and Encrypted Channel for Filing Agency Complaints",
        "report_badge": "🔒 Trustworthy • Secure • Official",
        "report_welcome": "🛡️ <strong>Welcome to the Confidential Reporting Office</strong><br><br>Thank you for your courage. Your report is vital in protecting Hajj and Umrah integrity.<br><br><strong>All information is encrypted and confidential.</strong>",
        "secure_reporting": "🔒 Secure Reporting",
        "all_encrypted": "All communications are encrypted and confidential",
        "current_progress": "Current Progress",
        "progress_complete": "{pct}% Complete",
        "exit_reporting": "🚪 Exit Reporting Channel",
        "quick_save": "💾 Quick Save Draft",
        "draft_saved": "✅ Draft saved!",
        "chat_input_placeholder": "Type your response here...",
        "report_submitted": "✅ Report submitted successfully!",
    },
    "العربية": {
        "report_page_title": "الإبلاغ عن شكوى الحج",
        "report_main_title": "مكتب الإبلاغ السري",
        "report_subtitle": "قناة آمنة ومشفرة لتقديم شكاوى الوكالات",
        "report_badge": "🔒 موثوق • آمن • رسمي",
        "report_welcome": "🛡️ <strong>مرحباً بك في مكتب الإبلاغ السري</strong><br><br>شكراً لشجاعتك. تقريرك حيوي في حماية سلامة الحج والعمرة.<br><br><strong>جميع المعلومات مشفرة وسرية.</strong>",
        "secure_reporting": "🔒 إبلاغ آمن",
        "all_encrypted": "جميع الاتصالات مشفرة وسرية",
        "current_progress": "التقدم الحالي",
        "progress_complete": "{pct}٪ مكتمل",
        "exit_reporting": "🚪 الخروج من قناة الإبلاغ",
        "quick_save": "💾 حفظ سريع للمسودة",
        "draft_saved": "✅ تم حفظ المسودة!",
        "chat_input_placeholder": "اكتب إجابتك هنا...",
        "report_submitted": "✅ تم تقديم التقرير بنجاح!",
    },
}


# =============================================================================
# DATABASE OPERATIONS (Keep existing functions)
# =============================================================================

def check_agency_in_sqlite(agency_name: str, db_manager) -> Tuple[bool, Dict]:
    """Check if agency exists in SQLite agencies table"""
    try:
        normalized_name = agency_name.strip().lower()
        
        query = """
        SELECT hajj_company_en, hajj_company_ar, city, country, 
               email, contact_Info, rating_reviews, is_authorized,
               google_maps_link, formatted_address
        FROM agencies 
        WHERE LOWER(hajj_company_en) = ? OR LOWER(hajj_company_ar) = ?
        """
        
        result = db_manager.execute_query(query, (normalized_name, normalized_name))
        
        if result and len(result) > 0:
            agency = result[0]
            return True, {
                "name_en": agency[0],
                "name_ar": agency[1],
                "city": agency[2],
                "country": agency[3],
                "email": agency[4],
                "contact_info": agency[5],
                "rating": agency[6],
                "is_authorized": agency[7],
                "maps_link": agency[8],
                "address": agency[9]
            }
        
        return False, {}
        
    except Exception as e:
        logger.error(f"Error checking agency in SQLite: {e}")
        return False, {}


def check_agency_exists_in_supabase(
    agency_name: str, 
    city: str, 
    supabase_client: Client
) -> Tuple[bool, Optional[Dict]]:  
    """Check if agency+city combination already exists in Supabase"""
    try:
        response = supabase_client.table('complaints').select('*').ilike(
            'agency_name', agency_name
        ).ilike('city', city).limit(1).execute()
        
        exists = response.data and len(response.data) > 0
        
        if exists:
            complaint_info = response.data[0]  
            logger.info(f"Agency '{agency_name}' in '{city}' already exists")
            return True, complaint_info 
        
        return False, None  
        
    except Exception as e:
        logger.error(f"Error checking Supabase: {e}")
        return False, None


def submit_complaint_to_db(
    data: Dict, 
    contact: str, 
    supabase_client: Client,
    db_manager = None,
    lang: str = "العربية"
) -> Tuple[bool, str]:
    """Submit complaint to database"""
    try:
        agency_name = data["agency_name"]
        city = data["city"]
        
        insert_data = {
            "agency_name": agency_name,
            "city": city,
            "complaint_text": data["complaint_text"],
            "user_contact": contact if contact else None,
            "submission_date": datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S'),
            "status": "pending"
        }

        response = supabase_client.table('complaints').insert(insert_data).execute()
        
        if response.data and len(response.data) > 0:
            report_id = response.data[0].get('id', 'N/A')
            
            success_msg = {
                "English": f"Report #{report_id} filed successfully",
                "العربية": f"تم تقديم التقرير #{report_id} بنجاح",
                "اردو": f"رپورٹ #{report_id} کامیابی سے درج کی گئی"
            }
            return True, success_msg.get(lang, success_msg["العربية"])
        else:
            return False, "Database error"
            
    except Exception as e:
        logger.error(f"Database error: {e}")
        return False, str(e)


def save_draft_to_session(data: Dict, step: int):
    """Save draft"""
    st.session_state.draft_report = {
        "data": data.copy(),
        "step": step,
        "timestamp": datetime.now(pytz.utc).isoformat()
    }


def load_draft_from_session() -> Optional[Dict]:
    """Load draft"""
    return st.session_state.get("draft_report", None)


def clear_draft():
    """Clear draft"""
    if "draft_report" in st.session_state:
        del st.session_state.draft_report


# =============================================================================
# UI COMPONENTS
# =============================================================================

def show_progress_bar(step: int, total_steps: int = 4, lang: str = "العربية"):
    """Display progress indicator"""
    progress = (step / total_steps) * 100
    
    step_text = {
        "English": f"Step {step} of {total_steps}",
        "العربية": f"الخطوة {step} من {total_steps}",
        "اردو": f"مرحلہ {step} از {total_steps}"
    }
    
    complete_text = t("progress_complete", lang, pct=int(progress))
    
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress}%"></div>
        </div>
        <div class="progress-text">
            <span>{step_text.get(lang, step_text['العربية'])}</span>
            <span>{complete_text}</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


# =============================================================================
# MAIN REPORT BOT INTERFACE
# =============================================================================

def render_report_bot():
    """Render report bot interface"""
    
    lang = st.session_state.get("language", "العربية")
    
    # Initialize session
    if "report_messages" not in st.session_state:
        st.session_state.report_messages = []
        st.session_state.report_step = 0
        st.session_state.complaint_data = {}
    
    # Initialize LLM
    if "llm_manager" not in st.session_state:
        st.session_state.llm_manager = RLLMManager()

    # Get clients
    supabase_client = get_supabase_client()
    db_manager = st.session_state.get("db_manager", None)
    
    # Show progress
    if st.session_state.report_step > 0:
        show_progress_bar(st.session_state.report_step, lang=lang)
    
    # Display chat
    for message in st.session_state.report_messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(
                    f'<div class="bot-message">{message["content"]}</div>', 
                    unsafe_allow_html=True
                )
            else:
                st.markdown(message["content"])
    
    # Chat input
    if prompt := st.chat_input(t("chat_input_placeholder", lang), key="report_chat_input"):
        st.session_state.report_messages.append({
            "role": "user", 
            "content": prompt
        })
        st.rerun()
    
    # Sidebar
    with st.sidebar:
        st.markdown("---")
        st.markdown(f"### {t('secure_reporting', lang)}")
        st.markdown(t("all_encrypted", lang))
        
        st.markdown("---")
        
        # Exit button - يرجع للشات
        if st.button(t("exit_reporting", lang), use_container_width=True, type="secondary", key="exit_btn"):
            # Clear report session
            st.session_state.report_messages = []
            st.session_state.report_step = 0
            st.session_state.complaint_data = {}
            clear_draft()
            # Return to main chat
            st.switch_page("app.py")
        
        # Quick save button
        if st.button(t("quick_save", lang), use_container_width=True, key="quick_save"):
            save_draft_to_session(st.session_state.complaint_data, st.session_state.report_step)
            st.success(t("draft_saved", lang))
            time.sleep(1)


# =============================================================================
# MAIN APPLICATION ENTRY POINT
# =============================================================================

def main():
    """Main application controller"""
    
    # Initialize app mode
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "report"
    
    # Get language
    lang = st.session_state.get("language", "العربية")
    
    # Set page config
    st.set_page_config(
        page_title=t("report_page_title", lang),
        page_icon="🛡️",
        layout="wide"
    )

    # Inject GOLDEN CSS
    st.markdown(get_css_styles(lang), unsafe_allow_html=True)
    
    # Ensure Supabase
    get_supabase_client()
    
    # Render GOLDEN header
    is_rtl = lang in ["العربية", "اردو"]
    
    st.markdown(f"""
    <div class="header-container" style="direction: {'rtl' if is_rtl else 'ltr'};">
        <h1 class="main-title">
            🛡️ <span class="title-highlight">{t("report_main_title", lang)}</span>
        </h1>
        <p class="subtitle">{t("report_subtitle", lang)}</p>
        <div class="header-badge">
            {t("report_badge", lang)}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Render bot
    render_report_bot()


if __name__ == "__main__":
    main()
