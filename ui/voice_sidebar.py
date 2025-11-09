"""
Sidebar Component Module
Handles sidebar rendering with language selection, accessibility, and navigation
"""
import time
import streamlit as st
from utils.translations import t


# -----------------------------
# CONFIGURATION
# -----------------------------
LANGUAGE_CONFIG = {
    "English": {'code': 'English', 'rtl': False},
    "العربية": {'code': 'العربية', 'rtl': True},
    "اردو": {'code': 'اردو', 'rtl': True}
}


def render_sidebar(memory, language_code: str):
    """Render the complete sidebar with all controls"""
    with st.sidebar:
        # Apply RTL/LTR direction to sidebar
        is_rtl = _is_rtl_language(language_code)
        
        # Inject sidebar-specific RTL styling
        st.markdown(f"""
        <style>
/* Sidebar Position - Right side for RTL languages */
[data-testid="stSidebar"] {{
    /* Set left: auto and right: 0 to pin it to the right for RTL */
    left: {'auto !important' if is_rtl else '0 !important'}; 
    right: {'0 !important' if is_rtl else 'auto !important'};
}}

[data-testid="stSidebar"] > div:first-child {{
    {'transform: translateX(0) !important;' if is_rtl else ''}
}}

/* Sidebar RTL Support */
[data-testid="stSidebar"] .block-container {{
    direction: {'rtl' if is_rtl else 'ltr'};
}}

[data-testid="stSidebar"] .stMarkdown {{
    text-align: {'right' if is_rtl else 'left'};
}}

[data-testid="stSidebar"] h3 {{
    text-align: {'right' if is_rtl else 'left'};
}}

[data-testid="stSidebar"] p {{
    text-align: {'right' if is_rtl else 'left'};
}}

/* Sidebar Color Harmony with Main Page */
[data-testid="stSidebar"] {{
    background: linear-gradient(180deg, #1e293b 0%, #0f172a 100%);
    /* Adjust border: use border-left for RTL, border-right for LTR */
    border-right: {'none' if is_rtl else '1px solid rgba(251, 191, 36, 0.2)'} !important;
    border-left: {'1px solid rgba(251, 191, 36, 0.2)' if is_rtl else 'none'} !important;
}}

[data-testid="stSidebar"] .stMarkdown {{
    color: #e2e8f0;
}}

/* Sidebar Headers */
[data-testid="stSidebar"] h3 {{
    color: #fbbf24 !important;
    font-weight: 700;
    margin-bottom: 0.5rem;
}}

/* Sidebar Captions */
[data-testid="stSidebar"] .stCaption {{
    color: #94a3b8 !important;
}}

/* Sidebar Selectbox */
[data-testid="stSidebar"] .stSelectbox > div > div {{
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(251, 191, 36, 0.3);
    color: #e2e8f0;
}}

/* Sidebar Checkbox */
[data-testid="stSidebar"] .stCheckbox {{
    color: #e2e8f0;
}}

/* Sidebar Buttons */
[data-testid="stSidebar"] .stButton > button {{
    background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
    color: #1e293b;
    font-weight: 600;
    border: none;
    transition: all 0.3s ease;
}}

[data-testid="stSidebar"] .stButton > button:hover {{
    background: linear-gradient(135deg, #f59e0b 0%, #d97706 100%);
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(251, 191, 36, 0.4);
}}

[data-testid="stSidebar"] button[kind="secondary"] {{
    background: rgba(239, 68, 68, 0.1) !important;
    color: #ef4444 !important;
    border: 1px solid rgba(239, 68, 68, 0.3) !important;
}}

[data-testid="stSidebar"] button[kind="secondary"]:hover {{
    background: rgba(239, 68, 68, 0.2) !important;
    border-color: rgba(239, 68, 68, 0.5) !important;
}}

/* Collapsed Control Button - Position for RTL */
[data-testid="collapsedControl"] {{
    /* If RTL (sidebar on the right), move button to the left edge of the main content area */
    left: {'0.5rem !important' if is_rtl else 'auto !important'}; 
    right: {'auto !important' if is_rtl else '0.5rem !important'};
}}

/* Memory Panel Styling */
.memory-panel {{
    background: rgba(251, 191, 36, 0.1);
    padding: 1rem;
    border-radius: 0.75rem;
    /* Adjust border side */
    border-right: {'4px solid #fbbf24' if is_rtl else 'none'};
    border-left: {'none' if is_rtl else '4px solid #fbbf24'};
    margin-top: 0.5rem;
}}

.memory-panel-row {{
    display: flex;
    justify-content: space-between;
    margin-bottom: 0.5rem;
    direction: {'rtl' if is_rtl else 'ltr'};
}}

.memory-panel-row:last-child {{
    margin-bottom: 0;
}}

.memory-label {{
    color: #94a3b8;
    font-size: 0.85rem;
}}

.memory-value {{
    color: #fbbf24;
    font-weight: 600;
}}

/* Sample Questions Styling */
.sample-question {{
    background: rgba(251, 191, 36, 0.08);
    padding: 0.6rem 0.9rem;
    border-radius: 0.6rem;
    margin-bottom: 0.6rem;
    font-size: 0.9rem;
    border: 1px solid rgba(251, 191, 36, 0.15);
    color: #e2e8f0;
    transition: all 0.3s ease;
    text-align: {'right' if is_rtl else 'left'};
    direction: {'rtl' if is_rtl else 'ltr'};
}}

.sample-question:hover {{
    background: rgba(251, 191, 36, 0.15);
    border-color: rgba(251, 191, 36, 0.3);
    /* Flip translation direction for RTL */
    transform: translateX({'-5px' if is_rtl else '5px'});
}}

/* Divider Styling */
[data-testid="stSidebar"] hr {{
    border-color: rgba(251, 191, 36, 0.2) !important;
    margin: 1rem 0;
}}

/* Main content adjustment for RTL sidebar (creates margin on the right) */
.main .block-container {{
    /* The 21rem space is now on the right */
    margin-right: {'21rem !important' if is_rtl else '1rem !important'}; 
    margin-left: {'1rem !important' if is_rtl else '1rem !important'};
}}

/* Adjust main content when sidebar is collapsed in RTL (removes margin) */
[data-testid="stSidebar"][aria-expanded="false"] ~ .main .block-container {{
    margin-right: {'1rem !important' if is_rtl else 'auto'};
}}
</style>
        """, unsafe_allow_html=True)
        
        # -----------------------------
        # Header Section
        # -----------------------------
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem 0 2rem 0;">
            <div style="font-size: 3rem; margin-bottom: 0.75rem;">🕋</div>
            <h2 style="margin: 0; font-size: 1.7rem; font-weight: 700; 
                       background: linear-gradient(135deg, #fbbf24 0%, #f59e0b 100%);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                {t('assistant_title', language_code).replace('🕋 ', '')}
            </h2>
            <p style="color: #94a3b8; font-size: 0.9rem; margin-top: 0.25rem;">
                {t('assistant_subtitle', language_code)}
            </p>
        </div>
        """, unsafe_allow_html=True)

        _render_divider()

        # Language Selection
        _render_language_section(language_code)
        _render_divider()

        # Accessibility
        _render_accessibility_section(language_code)
        _render_divider()

        # Sample Questions
        _render_sample_questions(language_code)
        _render_divider()

        # Memory
        _render_memory_section(memory, language_code)
        _render_divider()
        
        # Navigation
        _render_navigation(language_code)


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def _render_divider():
    """Render a horizontal divider line"""
    st.markdown("<hr style='margin-top:1rem; border-color:rgba(251, 191, 36, 0.2);'>", 
                unsafe_allow_html=True)


def _get_current_language_display(language_code: str) -> str:
    """Get the display name for the current language code"""
    for display_name, config in LANGUAGE_CONFIG.items():
        if config['code'] == language_code:
            return display_name
    return "English"  # Default fallback


def _is_rtl_language(language_code: str) -> bool:
    """Check if the given language code is RTL"""
    for config in LANGUAGE_CONFIG.values():
        if config['code'] == language_code:
            return config['rtl']
    return False


# -----------------------------
# LANGUAGE SELECTION
# -----------------------------
def _render_language_section(language_code: str):
    st.markdown(f"### {t('language_title', language_code)}")
    st.caption(t('feat_multilingual_desc', language_code))

    language_options = {
        "English": 'English',
        "العربية": 'العربية',
        "اردو": 'اردو'
    }

    current_lang_display = _get_current_language_display(language_code)
    
    selected_language = st.selectbox(
        t('language_title', language_code),
        options=list(language_options.keys()),
        index=list(language_options.keys()).index(current_lang_display),
        label_visibility="collapsed"
    )

    new_language_code = language_options[selected_language]
    if new_language_code != language_code:
        st.session_state.language = new_language_code
        st.session_state.is_rtl = _is_rtl_language(new_language_code)
        st.rerun()


# -----------------------------
# ACCESSIBILITY SECTION
# -----------------------------
def _render_accessibility_section(language_code: str):
    st.markdown(f"### {t('accessibility_title', language_code)}")
    st.caption(t('accessibility_desc', language_code))

    font_labels = [
        t('font_normal', language_code), 
        t('font_large', language_code), 
        t('font_extra_large', language_code)
    ]
    font_values = ['normal', 'large', 'extra-large']
    
    # Ensure font_size exists in session state
    if 'font_size' not in st.session_state:
        st.session_state.font_size = 'normal'
    
    current_index = font_values.index(st.session_state.font_size)

    selected_font = st.selectbox(
        t('font_size_label', language_code),
        options=font_labels,
        index=current_index
    )

    selected_index = font_labels.index(selected_font)
    new_font_size = font_values[selected_index]
    
    if new_font_size != st.session_state.font_size:
        st.session_state.font_size = new_font_size
        st.rerun()

    st.markdown("")

    # Ensure high_contrast exists in session state
    if 'high_contrast' not in st.session_state:
        st.session_state.high_contrast = False

    high_contrast = st.checkbox(
        t('contrast_label', language_code),
        value=st.session_state.high_contrast,
        help=t('contrast_help', language_code)
    )

    if high_contrast != st.session_state.high_contrast:
        st.session_state.high_contrast = high_contrast
        st.rerun()


# -----------------------------
# MEMORY SECTION
# -----------------------------
def _render_memory_section(memory, language_code: str):
    is_rtl = _is_rtl_language(language_code)
    
    st.markdown(f"### {t('memory_status_title', language_code)}")
    st.caption(t('memory_status_desc', language_code))

    try:
        memory_summary = memory.get_memory_summary()
        
        st.markdown(f"""
        <div class="memory-panel">
            <div class="memory-panel-row">
                <span class="memory-label">{t('voice_memory_messages', language_code)}</span>
                <strong class="memory-value">{memory_summary['total_messages']}</strong>
            </div>
            <div class="memory-panel-row">
                <span class="memory-label">{t('voice_session_duration', language_code)}</span>
                <strong class="memory-value">{memory_summary['session_duration']}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        if st.button(f"🗑️ {t('voice_clear_memory', language_code)}", use_container_width=True, type="secondary"):
            _clear_memory_and_state(memory, language_code)
            
    except Exception as e:
        st.error(f"Error loading memory: {str(e)}")


def _clear_memory_and_state(memory, language_code: str):
    """Clear memory and reset related session state"""
    try:
        memory.clear_memory()
        
        # Keys to clear
        keys_to_clear = [
            'current_transcript', 
            'current_response', 
            'current_metadata',
            'last_audio_hash', 
            'pending_audio', 
            'pending_audio_bytes'
        ]
        
        for key in keys_to_clear:
            if key in st.session_state:
                st.session_state[key] = None if 'audio' in key else ""
        
        st.success(t('memory_cleared', language_code))
        time.sleep(1)
        st.rerun()
    except Exception as e:
        st.error(f"Error clearing memory: {str(e)}")


# -----------------------------
# SAMPLE QUESTIONS
# -----------------------------
def _render_sample_questions(language_code: str):
    st.markdown(f"### {t('examples_title', language_code)}")
    st.caption(t('examples_caption', language_code))

    try:
        sample_questions = t('sample_questions', language_code)
        
        for question in sample_questions:
            st.markdown(f"""
            <div class="sample-question">
                💬 {question}
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading sample questions: {str(e)}")


# -----------------------------
# NAVIGATION SECTION
# -----------------------------
def _render_navigation(language_code: str):
    st.markdown(f"### {t('nav_title', language_code)}")
    st.caption(t('nav_caption', language_code))

    back_label = t('voice_return_button', language_code)
    arrow = "→" if _is_rtl_language(language_code) else "←"

    if st.button(f"{arrow} {back_label}", use_container_width=True, type="primary"):
        try:
            st.switch_page("./app.py")
        except Exception as e:
            st.error(f"Navigation error: {str(e)}")