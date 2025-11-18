"""
Hajj Complaint Reporting Bot - Main Application
Enhanced UX with Golden Theme matching main app
UNIFIED GOLDEN SIDEBAR matching Chat & Voicebot pages
Multi-language support: English, Arabic, Urdu
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
# CSS STYLING - UNIFIED GOLDEN THEME WITH MATCHING SIDEBAR
# =============================================================================

def get_css_styles(lang: str) -> str:
    """Generate CSS with RTL support and UNIFIED GOLDEN THEME"""
    is_rtl = lang in ["العربية", "اردو"]
    text_align = "right" if is_rtl else "left"
    direction = "rtl" if is_rtl else "ltr"
    
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

/* ===== UNIFIED GOLDEN SIDEBAR - MATCHING CHAT & VOICEBOT ===== */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #1a1f2e 0%, #0f1419 100%) !important;
    border-{text_align}: 3px solid var(--color-primary-gold) !important;
    box-shadow: 2px 0 20px var(--color-gold-glow) !important;
    direction: {direction};
    text-align: {text_align};
}}

/* Sidebar Text Colors */
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

/* Sidebar Icon Container */
.sidebar-icon-container {{
    text-align: center;
    padding: 2rem 1rem 1.5rem;
    margin-bottom: 1.5rem;
    background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(184, 148, 31, 0.05) 100%);
    border-radius: 16px;
    border: 1px solid rgba(212, 175, 55, 0.3);
}}

.sidebar-icon {{
    font-size: 4em;
    margin-bottom: 0.5rem;
    filter: drop-shadow(0 4px 12px var(--color-gold-glow));
    animation: iconPulse 3s ease-in-out infinite;
}}

@keyframes iconPulse {{
    0%, 100% {{ transform: scale(1); opacity: 1; }}
    50% {{ transform: scale(1.05); opacity: 0.9; }}
}}

.sidebar-title {{
    color: var(--color-primary-gold) !important;
    font-size: 1.8rem !important;
    font-weight: 800 !important;
    margin: 0.5rem 0 !important;
    text-shadow: 0 2px 8px var(--color-gold-glow) !important;
}}

.sidebar-subtitle {{
    color: rgba(248, 250, 252, 0.8) !important;
    font-size: 0.9rem !important;
    font-weight: 400 !important;
    margin-bottom: 1rem !important;
}}

/* Sidebar Info Cards */
.sidebar-info-card {{
    background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(184, 148, 31, 0.1) 100%);
    border: 1px solid rgba(212, 175, 55, 0.3);
    border-radius: 12px;
    padding: 1rem;
    margin: 1rem 0;
    text-align: {text_align};
}}

.sidebar-info-card h4 {{
    color: var(--color-primary-gold) !important;
    font-size: 1rem !important;
    font-weight: 700 !important;
    margin-bottom: 0.5rem !important;
}}

.sidebar-info-card p {{
    color: rgba(248, 250, 252, 0.9) !important;
    font-size: 0.85rem !important;
    line-height: 1.5 !important;
    margin: 0 !important;
}}

/* Sidebar Divider */
.sidebar-divider {{
    height: 2px;
    background: linear-gradient(90deg, transparent 0%, var(--color-primary-gold) 50%, transparent 100%);
    margin: 1.5rem 0;
    opacity: 0.3;
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
    width: 100% !important;
}}

[data-testid="stSidebar"] .stButton > button:hover,
[data-testid="stSidebar"] button:hover {{
    background: linear-gradient(135deg, var(--color-light-gold) 0%, var(--color-primary-gold) 100%) !important;
    transform: translateY(-3px) !important;
    box-shadow: 0 6px 20px rgba(212, 175, 55, 0.5) !important;
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
# DATABASE OPERATIONS
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
        
        # Check for duplicates
        already_exists = check_agency_exists_in_supabase(agency_name, city, supabase_client)
        
        if already_exists[0]:
            return False, "Duplicate complaint detected"
        
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
            return True, f"Report #{report_id} filed successfully"
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


def render_unified_sidebar(lang: str):
    """Render unified golden sidebar matching Chat & Voicebot pages"""
    
    # Sidebar titles
    sidebar_titles = {
        "English": {
            "title": "Complaint Report",
            "subtitle": "Secure & Anonymous",
            "info_title": "🔐 Your Privacy",
            "info_text": "All reports are encrypted and stored securely. Your identity remains protected.",
            "secure_title": "✅ Secure Process",
            "secure_text": "End-to-end encrypted reporting system for your safety.",
            "exit": "← Exit Reporting"
        },
        "العربية": {
            "title": "تقرير الشكوى",
            "subtitle": "آمن ومجهول",
            "info_title": "🔐 خصوصيتك",
            "info_text": "جميع التقارير مشفرة ومحفوظة بشكل آمن. هويتك محمية تماماً.",
            "secure_title": "✅ عملية آمنة",
            "secure_text": "نظام إبلاغ مشفر من طرف إلى طرف لسلامتك.",
            "exit": "← الخروج من الإبلاغ"
        },
        "اردو": {
            "title": "شکایت کی رپورٹ",
            "subtitle": "محفوظ اور گمنام",
            "info_title": "🔐 آپ کی رازداری",
            "info_text": "تمام رپورٹس خفیہ اور محفوظ طریقے سے محفوظ ہیں۔ آپ کی شناخت محفوظ رہتی ہے۔",
            "secure_title": "✅ محفوظ عمل",
            "secure_text": "آپ کی حفاظت کے لیے اینڈ ٹو اینڈ خفیہ رپورٹنگ سسٹم۔",
            "exit": "← رپورٹنگ سے باہر نکلیں"
        }
    }
    
    texts = sidebar_titles.get(lang, sidebar_titles["العربية"])
    
    with st.sidebar:
        # Icon and Title
        st.markdown(f"""
        <div class="sidebar-icon-container">
            <div class="sidebar-icon">{get_openmoji_html('🛡️', '4em', 'openmoji-pulse')}</div>
            <h2 class="sidebar-title">{texts['title']}</h2>
            <p class="sidebar-subtitle">{texts['subtitle']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Privacy Info
        st.markdown(f"""
        <div class="sidebar-info-card">
            <h4>{texts['info_title']}</h4>
            <p>{texts['info_text']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Divider
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        # Secure Process Info
        st.markdown(f"""
        <div class="sidebar-info-card">
            <h4>{texts['secure_title']}</h4>
            <p>{texts['secure_text']}</p>
        </div>
        """, unsafe_allow_html=True)
        
        # Divider
        st.markdown('<div class="sidebar-divider"></div>', unsafe_allow_html=True)
        
        # Exit Button
        if st.button(texts['exit'], use_container_width=True, type="secondary", key="exit_btn"):
            st.session_state.report_messages.clear()
            st.session_state.report_step = 0
            st.session_state.complaint_data.clear()
            clear_draft()
            st.switch_page("app.py")
