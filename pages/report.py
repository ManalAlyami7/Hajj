"""
Hajj Complaint Reporting Bot - Main Application
Enhanced UX with intelligent exit handling for all scenarios
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
# DATABASE OPERATIONS
# =============================================================================

def submit_complaint_to_db(
    data: Dict, 
    contact: str, 
    supabase_client: Client
) -> Tuple[bool, str]:
    """
    Submit complaint to database with proper error handling
    
    Args:
        data: Dictionary containing agency_name, city, complaint_text
        contact: User contact info (email/phone) or empty string
        supabase_client: Initialized Supabase client
    
    Returns:
        tuple: (success: bool, message: str)
    """
    try:
        insert_data = {
            "agency_name": data["agency_name"],
            "city": data["city"],
            "complaint_text": data["complaint_text"],
            "user_contact": contact if contact else None,
            "submission_date": datetime.now(pytz.utc).isoformat()
        }

        response = supabase_client.table('complaints').insert(insert_data).execute()
        
        if response.data and len(response.data) > 0:
            report_id = response.data[0].get('id', 'N/A')
            contact_status = "with secure contact" if contact else "anonymously"
            return True, f"Report #{report_id} filed {contact_status}"
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
    """Render intelligent exit confirmation modal based on progress"""
    
    context = get_exit_context()
    status = context["status"]
    
    # Scenario 1: Not started or just viewed welcome
    if status == "not_started":
        st.markdown("""
        <div class="modal-overlay">
            <div class="modal-content">
                <div class="modal-icon">👋</div>
                <div class="modal-title">Return to Main Chat?</div>
                <div class="modal-text">
                    You haven't started filing a report yet. You can return anytime to file a complaint.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
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
        <div class="modal-overlay">
            <div class="modal-content">
                <div class="modal-icon">⚠️</div>
                <div class="modal-title">Exit Reporting?</div>
                <div class="modal-text">
                    {context['message']}
                    <br><br>
                    <strong>Progress: {context['progress_pct']}%</strong>
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
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
        <div class="modal-overlay">
            <div class="modal-content" style="border-color: {urgency_color};">
                <div class="modal-icon">{urgency_emoji}</div>
                <div class="modal-title">You Have Significant Progress!</div>
                <div class="modal-text">
                    {context['message']}
                    <br><br>
                    <div style="background: #f3f4f6; padding: 1rem; border-radius: 8px; margin-top: 0.5rem;">
                        <strong>Progress: {context['progress_pct']}%</strong>
                        <div style="background: #e5e7eb; height: 8px; border-radius: 4px; margin-top: 0.5rem;">
                            <div style="background: {urgency_color}; height: 100%; width: {context['progress_pct']}%; border-radius: 4px;"></div>
                        </div>
                    </div>
                    <br>
                    <strong style="color: {urgency_color};">⏰ Your report is important!</strong> Consider saving a draft to continue later.
                </div>
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        st.markdown("<br>", unsafe_allow_html=True)
        
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
                st.warning("⚠️ Are you sure? This will delete all your progress.")
                if st.button("⚠️ Yes, Discard Everything", key="confirm_discard", type="secondary"):
                    st.session_state.app_mode = "chat"
                    st.session_state.report_messages = []
                    st.session_state.report_step = 0
                    st.session_state.complaint_data = {}
                    st.session_state.show_exit_modal = False
                    clear_draft()
                    st.info("Progress discarded.")
                    time.sleep(1)
                    st.rerun()
        with col3:
            if st.button("✍️ Continue Filing", use_container_width=True, type="primary", key="modal_no"):
                st.session_state.show_exit_modal = False
                st.rerun()


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
                {"role": "assistant", "content": "🛡️ **Welcome back!** Resuming your saved draft..."}
            ]
            
            if "agency_name" in data:
                st.session_state.report_messages.append({
                    "role": "assistant", 
                    "content": f"✅ **Agency:** {data['agency_name']}"
                })
            if "city" in data:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": f"✅ **City:** {data['city']}"
                })
            if "complaint_text" in data:
                preview = data['complaint_text'][:150] + "..." if len(data['complaint_text']) > 150 else data['complaint_text']
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": f"✅ **Details:** {preview}"
                })
            
            # Add next step prompt
            if step == 1:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": "**Step 1 of 4:** What is the **full name** of the agency you want to report?"
                })
            elif step == 2:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": "**Step 2 of 4:** Which **city** is this agency located in?"
                })
            elif step == 3:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": "**Step 3 of 4:** Please describe the incident in detail."
                })
            elif step == 4:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": "**Step 4 of 4 (Optional):** Provide contact info or type 'skip'."
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

    # Get database client
    supabase_client = get_supabase_client()
    
    # Initial welcome messages (shown only at start)
    if st.session_state.report_step == 0:
        st.session_state.report_messages = [
            {
                "role": "assistant",
                "content": """🛡️ **Welcome to the Confidential Reporting Office**

Thank you for your courage. Your report is vital in protecting Hajj and Umrah integrity.

**All information is encrypted and confidential.**"""
            },
            {
                "role": "assistant",
                "content": """**Step 1 of 4:** What is the **full name** of the agency you want to report?"""
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
                "content": f"⚠️ **Validation Issue**\n\n{feedback}"
            })
            st.rerun()
            return
        
        # Process valid input based on current step
        data = st.session_state.complaint_data
        
        if step == 1:  # Agency name
            data["agency_name"] = prompt
            st.session_state.report_messages.append({
                "role": "assistant",
                "content": f"""✅ **Agency recorded:** {prompt}

**Step 2 of 4:** Which **city** is this agency located in?"""
            })
            st.session_state.report_step = 2
            
        elif step == 2:  # City location
            data["city"] = prompt
            st.session_state.report_messages.append({
                "role": "assistant",
                "content": f"""✅ **Location recorded:** {prompt}

**Step 3 of 4:** Please describe the incident in detail:
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
                "content": f"""✅ **Details recorded**

**Summary:**
- Agency: {data['agency_name']}
- City: {data['city']}
- Details: {preview}

**Step 4 of 4 (Optional):** Provide contact info for follow-up, or type "**skip**" to remain anonymous."""
            })
            st.session_state.report_step = 4
            
        elif step == 4:  # Final submission
            contact = "" if prompt.lower() in ["skip", "anonymous"] else prompt
            
            success, message = submit_complaint_to_db(data, contact, supabase_client)
            
            if success:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": f"""✅ **Report Successfully Filed**

{message}

Your report is now with the relevant authorities. Redirecting to main chat..."""
                })
                st.success("✅ Report submitted successfully!")
                clear_draft()  # Clear any saved drafts
                time.sleep(2)
                
                # Reset all report state
                st.session_state.report_messages.clear()
                st.session_state.report_step = 0
                st.session_state.complaint_data.clear()
                st.session_state.app_mode = "chat"
            else:
                st.session_state.report_messages.append({
                    "role": "assistant",
                    "content": f"""❌ **Submission Error**

{message}

Please try again or contact technical support if the issue persists."""
                })
                st.error("❌ Database error occurred")
        
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