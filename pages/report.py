"""
Hajj Complaint Reporting Bot - Main Application
Enhanced UX with intelligent exit handling for all scenarios
Updated to match Supabase schema with status field
"""

import streamlit as st
from datetime import datetime
import pytz
import time
from typing import Dict, Optional, Tuple
import logging

# Supabase imports
from supabase import create_client, Client

# Import core modules (adjust paths as needed)
from core.report_llm import RLLMManager

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
    """
    Initialize and return Supabase client with proper error handling
    Uses st.cache_resource for singleton pattern
    """
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
        st.error("⚠️ Database connection failed. Please contact support.")
        st.stop()
    return client


# =============================================================================
# CSS STYLING
# =============================================================================

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Poppins:wght@300;400;500;600;700;800&family=Cairo:wght@400;600;700;800&display=swap');

/* ===== Secure Reporting Theme Variables (Trust, Safety, Elegance) ===== */
:root {
    --color-primary-authority: #1e3a8a; /* Deep Blue - Trust and Authority */
    --color-secondary-security: #708090; /* Slate Gray - Security and Modernity */
    --color-background-light: #ffffff;
    --color-background-mid: #f5f7fa;
    --color-text-dark: #1a1f2e;
    --color-text-mid: #4b5563;
    --color-border-subtle: #e5e7eb;
}

/* ===== Global Styles ===== */
* {
    font-family: 'Poppins', 'Cairo', sans-serif;
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1);
}

/* ===== Main Background - Elegant and Clean ===== */
.main {
    background-color: var(--color-background-mid);
    background-attachment: fixed;
}

.block-container {
    padding-top: 2.5rem;
    padding-bottom: 2.5rem;
    max-width: 1400px;
}

/* ===== Elegant Header - Trustworthy and Modern ===== */
.header-container {
    background: linear-gradient(135deg, var(--color-background-light) 0%, var(--color-background-mid) 100%);
    backdrop-filter: blur(15px);
    border-radius: 20px;
    padding: 2.5rem 2rem;
    margin-bottom: 2.5rem;
    box-shadow: 0 8px 30px rgba(0, 0, 0, 0.05);
    text-align: center;
    border: 1px solid var(--color-secondary-security);
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
    height: 4px;
    background: linear-gradient(90deg, var(--color-primary-authority) 0%, #a5b4fc 50%, var(--color-primary-authority) 100%);
    animation: shimmer 3s infinite;
}

@keyframes shimmer {
    0%, 100% { opacity: 1; }
    50% { opacity: 0.8; }
}

.main-title {
    font-size: 3.2rem;
    font-weight: 900;
    color: var(--color-text-dark);
    margin: 0;
    letter-spacing: -1px;
    text-shadow: 1px 1px 3px rgba(0, 0, 0, 0.05);
}

.title-highlight {
    background: linear-gradient(135deg, var(--color-primary-authority) 0%, #3b82f6 100%);
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    background-clip: text;
}

.subtitle {
    color: var(--color-text-mid);
    font-size: 1.1rem;
    margin-top: 0.5rem;
    font-weight: 400;
    line-height: 1.6;
}

.header-badge {
    background-color: var(--color-secondary-security); 
    color: white;
    padding: 0.3rem 1.15rem;
    border-radius: 50px;
    font-size: 0.8rem;
    font-weight: 600;
    margin-top: 1rem;
    box-shadow: 0 4px 10px rgba(112, 128, 144, 0.3);
}

/* ===== Progress Indicator - Clean and Clear ===== */
.progress-container {
    background: var(--color-background-light);
    border-radius: 12px;
    padding: 1rem 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
    border: 1px solid var(--color-border-subtle);
}

.progress-bar {
    width: 100%;
    height: 6px;
    background: var(--color-border-subtle);
    border-radius: 10px;
    overflow: hidden;
    margin-bottom: 0.5rem;
}

.progress-fill {
    height: 100%;
    background: linear-gradient(90deg, var(--color-primary-authority) 0%, #3b82f6 100%);
    border-radius: 10px;
    transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1);
}

.progress-text {
    display: flex;
    justify-content: space-between;
    color: var(--color-text-mid);
    font-size: 0.85rem;
    font-weight: 500;
}

/* ===== Elegant Modal - Safe and Controlled ===== */
.modal-content {
    background: var(--color-background-light);
    border-radius: 16px;
    padding: 2.5rem;
    max-width: 450px;
    box-shadow: 0 15px 40px rgba(0, 0, 0, 0.3);
    animation: slideInScale 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    text-align: center;
    border: 2px solid var(--color-primary-authority);
}

.modal-icon {
    font-size: 3rem;
    margin-bottom: 0.75rem;
    color: var(--color-primary-authority);
}

.modal-title {
    font-size: 1.6rem;
    font-weight: 700;
    color: var(--color-text-dark);
    margin-bottom: 0.75rem;
}

.modal-text {
    color: var(--color-text-mid);
    font-size: 1rem;
    font-weight: 400;
    line-height: 1.5;
    margin-bottom: 1.5rem;
}

/* ===== Refined Chat Messages ===== */
.stChatMessage {
    background: var(--color-background-light) !important;
    backdrop-filter: blur(8px);
    border-radius: 16px !important;
    padding: 1.5rem !important;
    margin: 1rem 0 !important;
    box-shadow: 0 2px 15px rgba(0, 0, 0, 0.05) !important;
    border: 1px solid var(--color-border-subtle);
    transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
    animation: slideInUp 0.4s ease-out;
}

.stChatMessage:hover {
    transform: translateY(-1px);
    box-shadow: 0 5px 20px rgba(0, 0, 0, 0.08) !important;
    border-color: var(--color-primary-authority);
}

.stChatMessage[data-testid*="user"] {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%) !important;
    border-left: 4px solid var(--color-primary-authority);
}

.stChatMessage[data-testid*="assistant"] {
    background: linear-gradient(135deg, #f9fafb 0%, #eff6ff 100%) !important;
    border-left: 4px solid var(--color-secondary-security);
}

.bot-message {
    background: linear-gradient(135deg, #f0f8ff 0%, #e0f2fe 100%) !important;
    border: 2px solid var(--color-primary-authority) !important;
    border-left: 6px solid var(--color-primary-authority) !important;
    color: var(--color-text-dark) !important;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    font-weight: 500;
}

.bot-message * {
    color: var(--color-text-dark) !important;
}

.typing-dot {
    background: var(--color-primary-authority);
}

/* ===== Elegant Sidebar ===== */
[data-testid="stSidebar"] {
    background: var(--color-background-light);
    border-right: 1px solid var(--color-border-subtle);
    box-shadow: 2px 0 10px rgba(0, 0, 0, 0.05);
}

[data-testid="stSidebar"] *,
[data-testid="stSidebar"] p,
[data-testid="stSidebar"] span,
[data-testid="stSidebar"] div,
[data-testid="stSidebar"] label {
    color: var(--color-text-dark) !important;
}

[data-testid="stSidebar"] h1,
[data-testid="stSidebar"] h2,
[data-testid="stSidebar"] h3 {
    color: var(--color-primary-authority) !important;
    font-weight: 700;
}

[data-testid="stSidebar"] .stButton > button {
    background: linear-gradient(135deg, var(--color-primary-authority) 0%, #3b82f6 100%) !important;
    color: white !important;
    border: none !important;
    border-radius: 10px !important;
    padding: 0.8rem 1.25rem !important;
    font-weight: 600 !important;
    font-size: 0.95rem !important;
    box-shadow: 0 4px 10px rgba(30, 58, 138, 0.3);
}

[data-testid="stSidebar"] .stButton > button:hover {
    background: linear-gradient(135deg, #3b82f6 0%, var(--color-primary-authority) 100%) !important;
    transform: translateY(-2px);
    box-shadow: 0 6px 15px rgba(30, 58, 138, 0.5);
}

/* ===== Enhanced Chat Input ===== */
.stChatInput > div {
    border-radius: 16px;
    border: 1px solid var(--color-border-subtle);
    background: white;
    box-shadow: 0 2px 10px rgba(0, 0, 0, 0.05);
}

.stChatInput > div:focus-within {
    border-color: var(--color-primary-authority);
    box-shadow: 0 0 0 3px rgba(30, 58, 138, 0.1);
    transform: none; 
}

/* ===== Success/Error Messages - Muted and Clear ===== */
.stSuccess {
    background: linear-gradient(135deg, #d1fae5 0%, #a7f3d0 100%);
    border-left: 4px solid #059669; 
}

.stError {
    background: linear-gradient(135deg, #fee2e2 0%, #fecaca 100%);
    border-left: 4px solid #b91c1c; 
}

/* ===== Custom Scrollbar - Blue Accent ===== */
::-webkit-scrollbar-thumb {
    background: linear-gradient(180deg, var(--color-primary-authority) 0%, #3b82f6 100%);
}

::-webkit-scrollbar-thumb:hover {
    background: linear-gradient(180deg, #3b82f6 0%, var(--color-primary-authority) 100%);
}

@keyframes slideInUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}
</style>
""", unsafe_allow_html=True)


# =============================================================================
# DATABASE OPERATIONS
# =============================================================================

def check_agency_in_sqlite(agency_name: str, db_manager) -> Tuple[bool, Dict]:
    """
    Check if agency exists in SQLite agencies table
    Checks both Arabic and English names
    
    Args:
        agency_name: Name of the agency to check
        db_manager: DatabaseManager instance from main app
    
    Returns:
        tuple: (exists: bool, agency_info: dict)
    """
    try:
        # Normalize agency name for fuzzy matching
        normalized_name = agency_name.strip().lower()
        
        # Try exact match in both English and Arabic columns
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
        
        # Try fuzzy match (contains) in both columns
        fuzzy_query = """
        SELECT hajj_company_en, hajj_company_ar, city, country, 
               email, contact_Info, rating_reviews, is_authorized,
               google_maps_link, formatted_address
        FROM agencies 
        WHERE LOWER(hajj_company_en) LIKE ? OR LOWER(hajj_company_ar) LIKE ?
        LIMIT 1
        """
        
        result = db_manager.execute_query(fuzzy_query, (f"%{normalized_name}%", f"%{normalized_name}%"))
        
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
) -> bool:
    """
    Check if agency+city combination already exists in Supabase complaints table
    
    Args:
        agency_name: Name of the agency
        city: City location
        supabase_client: Initialized Supabase client
    
    Returns:
        bool: True if already exists, False otherwise
    """
    try:
        # Check if this exact agency+city combo exists in complaints
        response = supabase_client.table('complaints').select('id').ilike(
            'agency_name', agency_name
        ).ilike('city', city).limit(1).execute()
        
        exists = response.data and len(response.data) > 0
        
        if exists:
            logger.info(f"Agency '{agency_name}' in '{city}' already exists in Supabase complaints")
        
        return exists
        
    except Exception as e:
        logger.error(f"Error checking Supabase for agency: {e}")
        return False  # On error, allow insertion (safer)


def submit_complaint_to_db(
    data: Dict, 
    contact: str, 
    supabase_client: Client,
    db_manager = None
) -> Tuple[bool, str]:
    """
    Submit complaint to database with proper error handling and duplicate prevention
    
    Checks:
    1. If agency exists in SQLite -> use official name
    2. If agency+city combo exists in Supabase complaints -> reject duplicate
    3. If all checks pass -> insert to Supabase
    
    Args:
        data: Dictionary containing agency_name, city, complaint_text
        contact: User contact info (email/phone) or empty string
        supabase_client: Initialized Supabase client
        db_manager: DatabaseManager instance for SQLite operations
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        agency_name = data["agency_name"]
        city = data["city"]
        agency_found_in_sqlite = False
        
        # Step 1: Check if agency exists in SQLite
        if db_manager:
            exists, agency_info = check_agency_in_sqlite(agency_name, db_manager)
            
            if exists:
                agency_found_in_sqlite = True
                logger.info(f"Agency found in SQLite: {agency_info.get('name_en', agency_name)}")
                
                # Use the official English name from database
                agency_name_official = agency_info.get('name_en') or agency_info.get('name_ar') or agency_name
                
                # Check authorization status
                is_authorized = agency_info.get('is_authorized', 'No')
                if is_authorized == 'Yes':
                    logger.warning(f"Report filed against AUTHORIZED agency: {agency_name_official}")
                
                # Use database city if available
                if agency_info.get('city'):
                    city = agency_info['city']
                
                # Override agency name with official name
                agency_name = agency_name_official
                
                logger.info(f"Using official name: {agency_name}, City: {city}")
            else:
                logger.info(f"Agency NOT found in SQLite: {agency_name}")
        
        # Step 2: Check if this agency+city already exists in Supabase complaints
        already_exists = check_agency_exists_in_supabase(agency_name, city, supabase_client)
        
        if already_exists:
            logger.warning(f"Duplicate prevented: '{agency_name}' in '{city}' already in complaints")
            return False, "This agency in this city has already been reported. Duplicate entry prevented."
        
        # Step 3: Prepare insert data for Supabase complaints table
        insert_data = {
            "agency_name": agency_name,
            "city": city,
            "complaint_text": data["complaint_text"],
            "user_contact": contact if contact else None,
            "submission_date": datetime.now(pytz.utc).strftime('%Y-%m-%d %H:%M:%S'),
            "status": "pending"
        }

        # Step 4: Insert into Supabase complaints table
        response = supabase_client.table('complaints').insert(insert_data).execute()
        
        # Check if insertion was successful
        if response.data and len(response.data) > 0:
            report_id = response.data[0].get('id', 'N/A')
            contact_status = "with secure contact" if contact else "anonymously"
            
            # Build success message
            if agency_found_in_sqlite:
                return True, f"Report #{report_id} filed {contact_status} (Agency verified in database)"
            else:
                return True, f"Report #{report_id} filed {contact_status} (New agency - under review)"
        else:
            logger.error("Supabase insert returned no data")
            return False, "Database insert failed - no data returned"
            
    except Exception as e:
        logger.error(f"Database submission error: {e}")
        return False, f"Database error: {str(e)}"


def save_draft_to_session(data: Dict, step: int):
    """Save partial report as draft in session state"""
    st.session_state.draft_report = {
        "data": data.copy(),
        "step": step,
        "timestamp": datetime.now(pytz.utc).isoformat()
    }
    logger.info(f"Draft saved at step {step}")


def load_draft_from_session() -> Optional[Dict]:
    """Load draft report from session state"""
    return st.session_state.get("draft_report", None)


def clear_draft():
    """Clear saved draft"""
    if "draft_report" in st.session_state:
        del st.session_state.draft_report
        logger.info("Draft cleared")


# =============================================================================
# UI COMPONENTS
# =============================================================================

def show_progress_bar(step: int, total_steps: int = 4):
    """Display elegant progress indicator"""
    progress = (step / total_steps) * 100
    st.markdown(f"""
    <div class="progress-container">
        <div class="progress-bar">
            <div class="progress-fill" style="width: {progress}%"></div>
        </div>
        <div class="progress-text">
            <span>Step {step} of {total_steps}</span>
            <span>{int(progress)}% Complete</span>
        </div>
    </div>
    """, unsafe_allow_html=True)


def show_typing_indicator() -> str:
    """Return typing indicator HTML"""
    return """
    <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    </div>
    """


def get_exit_context() -> Dict[str, any]:
    """
    Analyze current state to determine exit context
    Returns context information for intelligent exit handling
    """
    step = st.session_state.get("report_step", 0)
    data = st.session_state.get("complaint_data", {})
    
    # Not started yet
    if step == 0 or step == 1 and len(st.session_state.get("report_messages", [])) <= 2:
        return {
            "status": "not_started",
            "message": "You haven't started the report yet.",
            "show_save": False,
            "urgency": "low"
        }
    
    # Just started (only agency name)
    elif step == 1 or (step == 2 and "agency_name" in data and "city" not in data):
        return {
            "status": "just_started",
            "message": "You've only entered basic information.",
            "show_save": True,
            "urgency": "low",
            "progress_pct": 25
        }
    
    # Partially complete (has agency and city)
    elif step == 2 or (step == 3 and "city" in data and "complaint_text" not in data):
        return {
            "status": "partial",
            "message": "You're halfway through. Your agency and location are saved.",
            "show_save": True,
            "urgency": "medium",
            "progress_pct": 50
        }
    
    # Almost complete (has complaint details)
    elif step == 3 or (step == 4 and "complaint_text" in data):
        return {
            "status": "almost_complete",
            "message": "You're almost done! Only contact info remains.",
            "show_save": True,
            "urgency": "high",
            "progress_pct": 75
        }
    
    # Fallback
    else:
        return {
            "status": "unknown",
            "message": "You have unsaved progress.",
            "show_save": True,
            "urgency": "medium"
        }


def render_exit_modal():
    """Render intelligent exit confirmation modal as a true popup overlay"""
    
    context = get_exit_context()
    status = context["status"]
    
    # Inject modal CSS for true popup overlay
    st.markdown("""
    <style>
    .modal-overlay-backdrop {
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background: rgba(0, 0, 0, 0.75);
        z-index: 999998;
        backdrop-filter: blur(4px);
        animation: fadeIn 0.3s ease-out;
    }
    
    .modal-popup {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        z-index: 999999;
        background: white;
        border-radius: 20px;
        padding: 2.5rem;
        max-width: 550px;
        width: 90%;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
        animation: slideInScale 0.4s cubic-bezier(0.34, 1.56, 0.64, 1);
    }
    
    @keyframes fadeIn {
        from { opacity: 0; }
        to { opacity: 1; }
    }
    
    @keyframes slideInScale {
        from {
            opacity: 0;
            transform: translate(-50%, -48%) scale(0.9);
        }
        to {
            opacity: 1;
            transform: translate(-50%, -50%) scale(1);
        }
    }
    
    .modal-popup-icon {
        font-size: 4rem;
        text-align: center;
        margin-bottom: 1rem;
        animation: pulse 2s infinite;
    }
    
    .modal-popup-title {
        font-size: 1.8rem;
        font-weight: 800;
        color: #1a1f2e;
        text-align: center;
        margin-bottom: 1rem;
    }
    
    .modal-popup-text {
        color: #4b5563;
        font-size: 1.05rem;
        line-height: 1.6;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    .modal-progress-box {
        background: #f3f4f6;
        padding: 1rem;
        border-radius: 12px;
        margin: 1rem 0;
    }
    
    .modal-progress-bar-container {
        background: #e5e7eb;
        height: 10px;
        border-radius: 5px;
        margin-top: 0.5rem;
        overflow: hidden;
    }
    
    .modal-progress-bar-fill {
        height: 100%;
        border-radius: 5px;
        transition: width 0.6s ease;
    }
    </style>
    """, unsafe_allow_html=True)
    
    # Render backdrop
    st.markdown('<div class="modal-overlay-backdrop"></div>', unsafe_allow_html=True)
    
    # Scenario 1: Not started or just viewed welcome
    if status == "not_started":
        st.markdown("""
        <div class="modal-popup">
            <div class="modal-popup-icon">👋</div>
            <div class="modal-popup-title">Return to Main Chat?</div>
            <div class="modal-popup-text">
                You haven't started filing a report yet. You can return anytime to file a complaint.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><br><br><br><br><br>", unsafe_allow_html=True)
        col1, col2 = st.columns([1, 1])
        with col1:
            if st.button("✅ Yes, Return to Chat", use_container_width=True, key="modal_yes"):
                st.session_state.app_mode = "chat"
                st.session_state.report_messages = []
                st.session_state.report_step = 0
                st.session_state.complaint_data = {}
                st.session_state.show_exit_modal = False
                clear_draft()
                st.rerun()
        with col2:
            if st.button("📝 Stay & File Report", use_container_width=True, type="primary", key="modal_no"):
                st.session_state.show_exit_modal = False
                st.rerun()
    
    # Scenario 2: Just started (minimal progress)
    elif status == "just_started":
        st.markdown(f"""
        <div class="modal-popup">
            <div class="modal-popup-icon">⚠️</div>
            <div class="modal-popup-title">Exit Reporting?</div>
            <div class="modal-popup-text">
                {context['message']}
            </div>
            <div class="modal-progress-box">
                <strong>Progress: {context['progress_pct']}%</strong>
                <div class="modal-progress-bar-container">
                    <div class="modal-progress-bar-fill" style="width: {context['progress_pct']}%; background: #3b82f6;"></div>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("💾 Save Draft", use_container_width=True, key="modal_save"):
                save_draft_to_session(st.session_state.complaint_data, st.session_state.report_step)
                st.session_state.app_mode = "chat"
                st.session_state.report_messages = []
                st.session_state.report_step = 0
                st.session_state.complaint_data = {}
                st.session_state.show_exit_modal = False
                st.success("✅ Draft saved! You can resume later.")
                time.sleep(1.5)
                st.rerun()
        with col2:
            if st.button("🗑️ Discard & Exit", use_container_width=True, type="secondary", key="modal_discard"):
                st.session_state.app_mode = "chat"
                st.session_state.report_messages = []
                st.session_state.report_step = 0
                st.session_state.complaint_data = {}
                st.session_state.show_exit_modal = False
                clear_draft()
                st.rerun()
        with col3:
            if st.button("↩️ Continue", use_container_width=True, type="primary", key="modal_no"):
                st.session_state.show_exit_modal = False
                st.rerun()
    
    # Scenario 3: Partial or almost complete (significant progress)
    elif status in ["partial", "almost_complete"]:
        urgency_emoji = "🚨" if status == "almost_complete" else "⚠️"
        urgency_color = "#dc2626" if status == "almost_complete" else "#f59e0b"
        
        st.markdown(f"""
        <div class="modal-popup" style="border: 3px solid {urgency_color};">
            <div class="modal-popup-icon">{urgency_emoji}</div>
            <div class="modal-popup-title">You Have Significant Progress!</div>
            <div class="modal-popup-text">
                {context['message']}
            </div>
            <div class="modal-progress-box">
                <strong>Progress: {context['progress_pct']}%</strong>
                <div class="modal-progress-bar-container">
                    <div class="modal-progress-bar-fill" style="width: {context['progress_pct']}%; background: {urgency_color};"></div>
                </div>
            </div>
            <div class="modal-popup-text" style="color: {urgency_color}; font-weight: 700; margin-top: 1rem;">
                ⏰ Your report is important! Consider saving a draft to continue later.
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br><br><br><br><br><br><br><br><br><br>", unsafe_allow_html=True)
        col1, col2, col3 = st.columns([1, 1, 1])
        with col1:
            if st.button("💾 Save Draft & Exit", use_container_width=True, type="primary", key="modal_save"):
                save_draft_to_session(st.session_state.complaint_data, st.session_state.report_step)
                st.session_state.app_mode = "chat"
                st.session_state.report_messages = []
                st.session_state.report_step = 0
                st.session_state.complaint_data = {}
                st.session_state.show_exit_modal = False
                st.success("✅ Draft saved! Resume anytime from the main menu.")
                time.sleep(1.5)
                st.rerun()
        with col2:
            if st.button("🗑️ Discard Progress", use_container_width=True, type="secondary", key="modal_discard"):
                if st.session_state.get("confirm_discard_modal", False):
                    st.session_state.app_mode = "chat"
                    st.session_state.report_messages = []
                    st.session_state.report_step = 0
                    st.session_state.complaint_data = {}
                    st.session_state.show_exit_modal = False
                    st.session_state.confirm_discard_modal = False
                    clear_draft()
                    st.info("Progress discarded.")
                    time.sleep(1)
                    st.rerun()
                else:
                    st.session_state.confirm_discard_modal = True
                    st.rerun()
        with col3:
            if st.button("✍️ Continue Filing", use_container_width=True, type="primary", key="modal_no"):
                st.session_state.show_exit_modal = False
                st.rerun()
        
        # Show confirmation for discard
        if st.session_state.get("confirm_discard_modal", False):
            st.warning("⚠️ Are you sure? Click 'Discard Progress' again to confirm.")


def render_draft_resume_prompt():
    """Show prompt to resume from saved draft"""
    draft = load_draft_from_session()
    if not draft:
        return
    
    step = draft.get("step", 0)
    timestamp = draft.get("timestamp", "")
    data = draft.get("data", {})
    
    # Calculate how much progress was saved
    progress_items = []
    if "agency_name" in data:
        progress_items.append(f"**Agency:** {data['agency_name']}")
    if "city" in data:
        progress_items.append(f"**City:** {data['city']}")
    if "complaint_text" in data:
        preview = data['complaint_text'][:80] + "..." if len(data['complaint_text']) > 80 else data['complaint_text']
        progress_items.append(f"**Details:** {preview}")
    
    progress_text = "<br>".join(progress_items)
    
    st.markdown(f"""
    <div style="background: linear-gradient(135deg, #fef3c7 0%, #fde68a 100%); 
                border-left: 4px solid #f59e0b; 
                border-radius: 12px; 
                padding: 1.5rem; 
                margin-bottom: 1.5rem;
                box-shadow: 0 4px 12px rgba(245, 158, 11, 0.2);">
        <div style="display: flex; align-items: center; margin-bottom: 0.75rem;">
            <span style="font-size: 2rem; margin-right: 0.5rem;">💾</span>
            <h3 style="margin: 0; color: #92400e;">Draft Report Found!</h3>
        </div>
        <p style="color: #78350f; margin-bottom: 1rem;">
            You have a saved draft from your previous session. Would you like to continue where you left off?
        </p>
        <div style="background: white; padding: 1rem; border-radius: 8px; margin-bottom: 1rem;">
            {progress_text}
        </div>
        <p style="color: #92400e; font-size: 0.9rem; margin: 0;">
            📅 <em>Saved at step {step} of 4</em>
        </p>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("✅ Resume Draft", use_container_width=True, type="primary", key="resume_draft"):
            # Restore the draft
            st.session_state.complaint_data = data.copy()
            st.session_state.report_step = step
            
            # Reconstruct messages based on saved data
            st.session_state.report_messages = [
                {"role": "assistant", "content": "🛡️ <strong>Welcome back!</strong> Resuming your saved draft..."}
            ]
            
            if "agency_name" in data:
                st.session_state.report_messages.append({
                    "role": "assistant", 
                    "content": f"✅ <strong>Agency:</strong> {data['agency_name']}"
                })
            if "city" in data:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": f"✅ <strong>City:</strong> {data['city']}"
                })
            if "complaint_text" in data:
                preview = data['complaint_text'][:150] + "..." if len(data['complaint_text']) > 150 else data['complaint_text']
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": f"✅ <strong>Details:</strong> {preview}"
                })
            
            # Add next step prompt
            if step == 1:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": "<strong>Step 1 of 4:</strong> What is the <strong>full name</strong> of the agency you want to report?"
                })
            elif step == 2:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": "<strong>Step 2 of 4:</strong> Which <strong>city</strong> is this agency located in?"
                })
            elif step == 3:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": "<strong>Step 3 of 4:</strong> Please describe the incident in detail."
                })
            elif step == 4:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": "<strong>Step 4 of 4 (Optional):</strong> Provide contact info or type 'skip'."
                })
            
            clear_draft()
            st.success("✅ Draft restored!")
            time.sleep(1)
            st.rerun()
    
    with col2:
        if st.button("🗑️ Start Fresh", use_container_width=True, type="secondary", key="discard_draft"):
            clear_draft()
            st.info("Draft discarded. Starting new report...")
            time.sleep(1)
            st.rerun()


# =============================================================================
# MAIN REPORT BOT INTERFACE
# =============================================================================

def render_report_bot():
    """Render the enhanced secure report bot interface"""
    
    # Check for saved draft first (before initializing new session)
    draft = load_draft_from_session()
    if draft and st.session_state.get("report_step", 0) == 0:
        render_draft_resume_prompt()
        return  # Wait for user decision
    
    # Initialize session state for report flow
    if "report_messages" not in st.session_state:
        st.session_state.report_messages = []
        st.session_state.report_step = 0
        st.session_state.complaint_data = {}
    
    # Initialize LLM manager
    if "llm_manager" not in st.session_state:
        st.session_state.llm_manager = RLLMManager()

    # Get database clients
    supabase_client = get_supabase_client()
    
    # Get SQLite database manager from session state
    db_manager = st.session_state.get("db_manager", None)
    
    # Initial welcome messages (shown only at start)
    if st.session_state.report_step == 0:
        st.session_state.report_messages = [
            {
                "role": "assistant",
                "content": """🛡️ <strong>Welcome to the Confidential Reporting Office</strong>

Thank you for your courage. Your report is vital in protecting Hajj and Umrah integrity.

<strong>All information is encrypted and confidential.</strong>"""
            },
            {
                "role": "assistant",
                "content": """<strong>Step 1 of 4:</strong> What is the <strong>full name</strong> of the agency you want to report?"""
            }
        ]
        st.session_state.report_step = 1
    
    # Show progress bar
    if st.session_state.report_step > 0:
        show_progress_bar(st.session_state.report_step)
    
    # Display chat history
    for message in st.session_state.report_messages:
        with st.chat_message(message["role"]):
            if message["role"] == "assistant":
                st.markdown(
                    f'<div class="bot-message">{message["content"]}</div>', 
                    unsafe_allow_html=True
                )
            else:
                st.markdown(message["content"])
    
    # Chat input with validation flow
    if prompt := st.chat_input("Type your response here...", key="report_chat_input"):
        step = st.session_state.report_step
        
        # Add user message to chat
        st.session_state.report_messages.append({
            "role": "user", 
            "content": prompt
        })
        
        # Show typing indicator during validation
        with st.chat_message("assistant"):
            typing_placeholder = st.empty()
            typing_placeholder.markdown(show_typing_indicator(), unsafe_allow_html=True)
            time.sleep(0.3)
            
            # Validate input with LLM
            validation = st.session_state.llm_manager.validate_user_input_llm(step, prompt)
            typing_placeholder.empty()
        
        # Handle validation failure
        if not validation.get("is_valid", False):
            feedback = validation.get('feedback', 'Invalid input. Please try again.')
            st.session_state.report_messages.append({
                "role": "assistant",
                "content": f"⚠️ <strong>Validation Issue</strong><br><br>{feedback}"
            })
            st.rerun()
            return
        
        # Process valid input based on current step
        data = st.session_state.complaint_data
        
        if step == 1:  # Agency name
            data["agency_name"] = prompt
            st.session_state.report_messages.append({
                "role": "assistant",
                "content": f"""✅ <strong>Agency recorded:</strong> {prompt}

<strong>Step 2 of 4:</strong> Which <strong>city</strong> is this agency located in?"""
            })
            st.session_state.report_step = 2
            
        elif step == 2:  # City location
            data["city"] = prompt
            st.session_state.report_messages.append({
                "role": "assistant",
                "content": f"""✅ <strong>Location recorded:</strong> {prompt}

<strong>Step 3 of 4:</strong> Please describe the incident in detail:
- What happened?
- When? (approximate date)
- Any amounts or payments involved?
- Promises made that were broken?"""
            })
            st.session_state.report_step = 3
            
        elif step == 3:  # Complaint details
            data["complaint_text"] = prompt
            preview = prompt[:150] + "..." if len(prompt) > 150 else prompt
            st.session_state.report_messages.append({
                "role": "assistant",
                "content": f"""✅ <strong>Details recorded</strong>

<strong>Summary:</strong>
- Agency: {data['agency_name']}
- City: {data['city']}
- Details: {preview}

<strong>Step 4 of 4 (Optional):</strong> Provide contact info for follow-up, or type "<strong>skip</strong>" to remain anonymous."""
            })
            st.session_state.report_step = 4
            
        elif step == 4:  # Final submission
            contact = "" if prompt.lower() in ["skip", "anonymous"] else prompt
            
            # Submit with SQLite check and insert
            success, message = submit_complaint_to_db(
                data, 
                contact, 
                supabase_client,
                db_manager  # Pass SQLite DB manager
            )
            
            if success:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": f"""✅ <strong>Report Successfully Filed</strong>

{message}

<strong>Status:</strong> Pending Review

Your report is now with the relevant authorities. Redirecting to main chat..."""
                })
                st.success("✅ Report submitted successfully!")
                clear_draft()
                time.sleep(2)
                
                st.session_state.report_messages.clear()
                st.session_state.report_step = 0
                st.session_state.complaint_data.clear()
                st.session_state.app_mode = "chat"
            else:
                # Show error in modal instead
                st.error(f"❌ {message}")
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": f"""❌ <strong>Submission Failed</strong>

{message}

Please try again or modify your submission."""
                })
                # Don't clear step, allow user to try again
                st.rerun()
                return
        
        st.rerun()
    
    # Enhanced Sidebar with exit option and progress info
    with st.sidebar:
        st.markdown("---")
        st.markdown("### 🔒 Secure Reporting")
        st.markdown("All communications are encrypted and confidential")
        
        # Show current progress
        context = get_exit_context()
        if context["status"] != "not_started":
            progress_pct = context.get("progress_pct", 0)
            st.markdown(f"""
            <div style="background: #f3f4f6; padding: 0.75rem; border-radius: 8px; margin: 1rem 0;">
                <strong>Current Progress</strong>
                <div style="background: #e5e7eb; height: 6px; border-radius: 3px; margin-top: 0.5rem;">
                    <div style="background: #3b82f6; height: 100%; width: {progress_pct}%; border-radius: 3px;"></div>
                </div>
                <small style="color: #6b7280;">{progress_pct}% Complete</small>
            </div>
            """, unsafe_allow_html=True)
        
        st.markdown("---")
        
        if st.button("🚪 Exit Reporting Channel", use_container_width=True, type="secondary"):
            st.session_state.show_exit_modal = True
            st.rerun()
        
        # Quick save draft button for partial progress
        if context.get("show_save", False) and context["status"] not in ["not_started"]:
            if st.button("💾 Quick Save Draft", use_container_width=True, key="quick_save"):
                save_draft_to_session(st.session_state.complaint_data, st.session_state.report_step)
                st.success("✅ Draft saved!")
                time.sleep(1)


# =============================================================================
# MAIN APPLICATION ENTRY POINT
# =============================================================================

def main():
    """Main application controller"""
    
    # Initialize app mode
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "chat"
    if "show_exit_modal" not in st.session_state:
        st.session_state.show_exit_modal = False

    # Ensure Supabase is initialized
    get_supabase_client()
    
    # Render elegant header
    st.markdown("""
    <div class="header-container">
        <h1 class="main-title">
            🛡️ <span class="title-highlight">Confidential Reporting Office</span>
        </h1>
        <p class="subtitle">Secure and Encrypted Channel for Filing Agency Complaints</p>
        <div class="header-badge">
            🔒 Trustworthy • Secure • Official
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # Show exit modal if triggered
    if st.session_state.get("show_exit_modal", False):
        render_exit_modal()
    
    # Route to appropriate mode
    if st.session_state.app_mode == "report":
        render_report_bot()
    elif st.session_state.app_mode == "chat":
        st.switch_page("app.py")


if __name__ == "__main__":
    main()