"""
Hajj Chatbot - Enhanced UX with Modern Interactions
Professional Islamic theme with improved user experience
"""

import streamlit as st
from datetime import datetime
import pytz
import sqlite3
import time
import json
# New Imports
from supabase import create_client, Client
import os
# Import core modules
from core.database import DatabaseManager
from core.report_llm import RLLMManager
from core.llm import LLMManager
from core.graph import ChatGraph
from ui.chat import ChatInterface
from ui.sidebar import SidebarInterface
from utils.translations import t, TRANSLATIONS
from utils.validators import validate_user_input
from utils.state import initialize_session_state, save_chat_memory, load_chat_memory
from openai import OpenAI


# -----------------------------
# Database Setup for Complaints
# -----------------------------
# -----------------------------
# Supabase Setup
# -----------------------------
# Replace with your actual Supabase URL and Key
SUPABASE_URL = st.secrets.get('supabase_url')
SUPABASE_KEY = st.secrets.get("supabase_key")


def get_supabase_client() -> Client:
    """Initializes and returns the Supabase client."""
    try:
        if not SUPABASE_URL or not SUPABASE_KEY:
            raise ValueError("Supabase URL and Key must be set.")
        
        # Use st.cache_resource to ensure the client is created only once
        @st.cache_resource
        def init_client():
            return create_client(SUPABASE_URL, SUPABASE_KEY)
        
        return init_client()
    except Exception as e:
        st.error(f"Failed to initialize Supabase client: {e}")
        st.stop()

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
    border: 1px solid var(--color-secondary-security); /* Subtle border */
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
    /* Deep Blue shimmer for authority */
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
    /* Deep Blue highlight */
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
    /* Subtle Gray/Silver badge for security */
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
    /* Deep Blue progress fill */
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
    border: 2px solid var(--color-primary-authority); /* Deep Blue accent */
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

/* User Message */
.stChatMessage[data-testid*="user"] {
    background: linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%) !important;
    border-left: 4px solid var(--color-primary-authority); /* Deep Blue */
}

/* Assistant Message - Subtle Gray/Blue for official replies */
.stChatMessage[data-testid*="assistant"] {
    background: linear-gradient(135deg, #f9fafb 0%, #eff6ff 100%) !important;
    border-left: 4px solid var(--color-secondary-security); /* Slate Gray */
}

/* Bot Message - Safe, Trustworthy Report Box - The "Inner Room" */
.bot-message {
    /* Subtle light blue background for the inner room */
    background: linear-gradient(135deg, #f0f8ff 0%, #e0f2fe 100%) !important;
    border: 2px solid var(--color-primary-authority) !important;
    border-left: 6px solid var(--color-primary-authority) !important; /* Strong authority line */ 
    color: var(--color-text-dark) !important;
    padding: 1.5rem;
    border-radius: 12px;
    box-shadow: 0 4px 10px rgba(0, 0, 0, 0.05);
    font-weight: 500;
}

.bot-message * {
    color: var(--color-text-dark) !important;
}

/* ===== Typing Indicator ===== */
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
    /* Blue button for action and trust */
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

/* Minor animation tweaks for elegance */
@keyframes slideInUp {
    from { opacity: 0; transform: translateY(10px); }
    to { opacity: 1; transform: translateY(0); }
}

</style>
""", unsafe_allow_html=True)

# -----------------------------
# Enhanced Report Bot Functions 
# -----------------------------
def show_progress_bar(step, total_steps=4):
    """Display progress indicator"""
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

def show_typing_indicator():
    """Display typing indicator"""
    return """
    <div class="typing-indicator">
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
        <div class="typing-dot"></div>
    </div>
    """
# -----------------------------
# Enhanced Report Bot Functions 
# -----------------------------

# ... (show_progress_bar and show_typing_indicator remain the same) ...

def render_report_bot():
    """Render the enhanced report bot chat interface"""
    
    # Initialize report messages if not exists
    if "report_messages" not in st.session_state:
        st.session_state.report_messages = []
        st.session_state.report_step = 0
        st.session_state.complaint_data = {}
    
    # Initialize LLMManager
    if "llm_manager" not in st.session_state:
        st.session_state.llm_manager = RLLMManager()

    # --- FIX 1: Get the Supabase client instance here ---
    supabase_client = get_supabase_client()
    # ---------------------------------------------------
    
    # Welcome message - Split into two messages
    if st.session_state.report_step == 0:
        st.session_state.report_messages = [
            {
                "role": "assistant",
                "content": """🛡️ **Welcome to the Confidential Reporting Office**

Thank you for your courage. Your report is a vital step in protecting the integrity of Hajj and Umrah. This is a secure, private channel.

**Your report is strictly confidential and will be reviewed by relevant authorities.**"""
            },
            {
                "role": "assistant",
                "content": """To begin, please tell me: **What is the full name of the agency you want to report?**"""
            }
        ]
        st.session_state.report_step = 1
    
    # Show progress bar
    if st.session_state.report_step > 0:
        show_progress_bar(st.session_state.report_step)
    
    # Display chat messages with enhanced styling
    for idx, message in enumerate(st.session_state.report_messages):
        with st.chat_message(message["role"]):
            # The 'bot-message' class now reflects the elegant, safe theme
            if message["role"] == "assistant":
                st.markdown(f'<div class="bot-message">{message["content"]}</div>', unsafe_allow_html=True)
            else:
                st.markdown(message["content"])
    
    # Chat input with enhanced UX
    if prompt := st.chat_input("Enter the agency name or your response here...", key="report_chat_input"):
        step = st.session_state.report_step

        # Add user message immediately
        st.session_state.report_messages.append({"role": "user", "content": prompt})

        # Show typing indicator for LLM validation
        with st.chat_message("assistant"):
            # Use st.empty to show the indicator and replace it with the actual response later
            typing_placeholder = st.empty()
            typing_placeholder.markdown(show_typing_indicator(), unsafe_allow_html=True)
            
            # Brief pause for better UX while the LLM runs
            time.sleep(0.5) 
                
            # Validate user input via LLM
            llm_response = st.session_state.llm_manager.validate_user_input_llm(step, prompt)
            
            # Clear typing indicator (it will be replaced by the response)
            typing_placeholder.empty()

        # If validation fails, append the error and rerun
        if not llm_response.get("is_valid", False):
            feedback = llm_response.get('feedback', 'Invalid input. Please try again.')
            st.session_state.report_messages.append({
                "role": "assistant", 
                "content": f"⚠️ **Validation Error**\n\n{feedback}."
            })
            st.rerun()

        # If validation succeeds, process the step
        else:
            data = st.session_state.complaint_data

            if step == 1: # Agency name
                data["agency_name"] = prompt
                response = f"""✅ **Agency name recorded.**

**Agency:** **{prompt}**

---

Next: **Which city is this agency located in?** (e.g., London, Jakarta, Cairo)

*Providing the city assists authorities in locating and investigating the entity.*"""
                st.session_state.report_messages.append({"role": "assistant", "content": response})
                st.session_state.report_step = 2
            
            elif step == 2: # City
                data["city"] = prompt
                response = f"""✅ **Location recorded.**

📍 **Report Details So Far:**
- **Agency:** {data['agency_name']}  
- **City:** {prompt}

---

**Crucial Step:** Please describe the suspicious activity in detail. The more comprehensive your description, the more effective the investigation will be.

- **What happened?** (False advertising, canceled trip, overcharging)
- **When did it occur?** (Approximate dates)
- **Any amounts or payments involved?**
- **Promises made that were broken?**"""
                st.session_state.report_messages.append({"role": "assistant", "content": response})
                st.session_state.report_step = 3
            
            elif step == 3: # Complaint details
                data["complaint_text"] = prompt
                preview = prompt[:150] + "..." if len(prompt) > 150 else prompt
                response = f"""✅ **Complaint details recorded.**

📋 **Report Summary:**
- **Agency:** {data['agency_name']}
- **City:** {data['city']}
- **Details:** *{preview}*

---

**Final Optional Step (Secure Follow-up):**

Would you like to provide a secure contact method (email or phone) so authorities can follow up for clarification, if necessary?

- Type your **contact info** (email/phone) to provide it
- Type "**skip**" to submit anonymously

*Your anonymity is guaranteed if you choose to skip this step.*"""
                st.session_state.report_messages.append({"role": "assistant", "content": response})
                st.session_state.report_step = 4
            
            elif step == 4: # Contact info and Submission
                
                contact = "" if prompt.lower() == "skip" else prompt
                
                try:
                    # Prepare data for insertion (FIX 2: Using 'submission_date' as key)
                    insert_data = {
                        "agency_name": data["agency_name"],
                        "city": data["city"],
                        "complaint_text": data["complaint_text"],
                        "user_contact": contact if contact else None,
                        # Use a standard UTC timestamp for database
                        "submission_date": datetime.now(pytz.utc).isoformat()
                    }

                    # Perform the Supabase insertion
                    response_data = supabase_client.table('complaints').insert(insert_data).execute()
                    
                    if response_data.data:
                        report_id = response_data.data[0]['id']
                    else:
                        report_id = "N/A (Check DB)" 

                    contact_status = "with contact info" if contact else "anonymously"
                    response = f"""✅ **Report Successfully Filed!**

Your report has been securely logged for investigation.

**Reference ID:** **#{report_id}** (Submitted {contact_status})

You are now being safely redirected to the main chat assistant."""
                    st.success("✅ Report submitted successfully!")
                    
                    # Reset and exit
                    st.session_state.report_messages.clear()
                    st.session_state.report_step = 0
                    st.session_state.complaint_data.clear()
                    st.session_state.app_mode = "chat"
                
                except Exception as e:
                    response = f"❌ **Error Submitting Report:** A database error occurred: {str(e)}"
                    st.error("❌ Database Error! Please check Supabase credentials/connection.")
                
                st.session_state.report_messages.append({"role": "assistant", "content": response})
                # No need to rerun if we are changing app_mode, but rerun to show final message/state change
            
            st.rerun() # Rerun to apply state change immediately
    
    # Enhanced Exit button in sidebar
    with st.sidebar:
        st.markdown("---")
        # Updated Title for elegance and security
        st.markdown("### 🔒 Secure Reporting Channel")
        st.markdown("All communication is encrypted and confidential.")
        st.markdown("---")
        
        if st.button("🚪 Exit Reporting Channel", use_container_width=True, type="secondary"):
            st.session_state.show_exit_modal = True
            st.rerun()

def render_exit_modal():
    """Render enhanced exit confirmation modal"""
    st.markdown("""
    <div class="modal-overlay">
        <div class="modal-content">
            <div class="modal-icon">⚠️</div>
            <div class="modal-title">Exit Secure Reporting?</div>
            <div class="modal-text">
                Your current progress will be deleted and you'll return to the main chat.
                Are you sure you want to leave this safe reporting process?
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    with col1:
        if st.button("✅ Yes, Exit", use_container_width=True, type="secondary", key="modal_yes"):
            st.session_state.app_mode = "chat"
            st.session_state.report_messages = []
            st.session_state.report_step = 0
            st.session_state.complaint_data = {}
            st.session_state.show_exit_modal = False
            st.info("Returning to main chat...")
            time.sleep(1)
            st.rerun()
    with col2:
        if st.button("❌ No, Stay", use_container_width=True, key="modal_no"):
            st.session_state.show_exit_modal = False
            st.rerun()

# -----------------------------
# Main Application
# -----------------------------
def main():
    initialize_session_state()
    
    if "app_mode" not in st.session_state:
        st.session_state.app_mode = "chat"
    if "show_exit_modal" not in st.session_state:
        st.session_state.show_exit_modal = False

    get_supabase_client()

    
    
    lang = st.session_state.language
    is_rtl = lang in ['العربية', 'اردو']
    
    # Updated text for Trustworthy, Safe, Elegant, Modern Reporting theme
    header_title = "Confidential Reporting Office"
    subtitle_text = "Secure and Encrypted Channel for Filing Agency Complaints"
    badge_text = "🔒 Trustworthy • Secure • Official"
    
    st.markdown(f"""
    <div class="header-container{' rtl' if is_rtl else ''}" style="background: linear-gradient(135deg, #fdfdfd 0%, #f0f4f8 100%); border-color: var(--color-primary-authority);">
        <h1 class="main-title" style="color: var(--color-text-dark);">
            🛡️ <span class="title-highlight" style="background: linear-gradient(135deg, var(--color-primary-authority) 0%, #3b82f6 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent;">{header_title}</span>
        </h1>
        <p class="subtitle" style="color: var(--color-text-mid);">{subtitle_text}</p>
        <div class="header-badge" style="background: linear-gradient(135deg, var(--color-primary-authority) 0%, #3b82f6 100%);">
            {badge_text}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    if st.session_state.get("show_exit_modal", False):
        render_exit_modal()
    
    if st.session_state.app_mode == "report":
        render_report_bot()
    elif st.session_state.app_mode == "chat":
       st.switch_page("app.py")


if __name__ == "__main__":
    main()