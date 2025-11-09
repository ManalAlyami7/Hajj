"""
Professional Voicebot Sidebar Component Module
Enhanced with formal design, RTL support, and accessibility
Fixed color scheme with proper contrast and visibility
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
    """Render the complete professional sidebar with all controls"""
    with st.sidebar:
        is_rtl = _is_rtl_language(language_code)
        
        # Inject professional sidebar styling
        _inject_professional_styles(is_rtl)
        
        # Header Section
        _render_header(language_code)
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

        # Memory Status
        _render_memory_section(memory, language_code)
        _render_divider()
        
        # Navigation
        _render_navigation(language_code)
        _render_divider()
        
        # Footer
        _render_footer(language_code)


# -----------------------------
# PROFESSIONAL STYLING
# -----------------------------
def _inject_professional_styles(is_rtl: bool):
    """Inject enhanced professional CSS for voicebot sidebar with fixed colors"""
    st.markdown(f"""
    <style>
    /* Sidebar Position and RTL Support */
    [data-testid="stSidebar"] {{
        left: {'auto !important' if is_rtl else '0 !important'};
        right: {'0 !important' if is_rtl else 'auto !important'};
        background: linear-gradient(180deg, #0f1419 0%, #1a1f2e 100%);
        border-right: {'none' if is_rtl else '3px solid #d4af37'} !important;
        border-left: {'3px solid #d4af37' if is_rtl else 'none'} !important;
    }}

    [data-testid="stSidebar"] > div:first-child {{
        {'transform: translateX(0) !important;' if is_rtl else ''}
    }}

    [data-testid="stSidebar"] .block-container {{
        direction: {'rtl' if is_rtl else 'ltr'};
        padding: 2rem 1.5rem;
    }}

    [data-testid="stSidebar"] .stMarkdown {{
        text-align: {'right' if is_rtl else 'left'};
        color: #f8fafc !important;
    }}

    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown span,
    [data-testid="stSidebar"] .stMarkdown div {{
        color: #f8fafc !important;
    }}

    /* Headers */
    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{
        color: #d4af37 !important;
        font-weight: 800;
        text-align: {'right' if is_rtl else 'left'};
        letter-spacing: -0.025em;
        margin-bottom: 1rem;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }}

    [data-testid="stSidebar"] p {{
        color: #cbd5e1 !important;
        line-height: 1.7;
        font-weight: 500;
    }}

    /* Captions */
    [data-testid="stSidebar"] .stCaption {{
        color: #94a3b8 !important;
        font-size: 0.9rem;
        line-height: 1.6;
        font-weight: 500;
    }}

    /* Selectbox Styling */
    [data-testid="stSidebar"] .stSelectbox > div > div {{
        background: rgba(212, 175, 55, 0.1);
        border: 2px solid rgba(212, 175, 55, 0.4);
        border-radius: 14px;
        color: #f8fafc;
        font-weight: 700;
        transition: all 0.3s ease;
    }}

    [data-testid="stSidebar"] .stSelectbox > div > div:hover {{
        border-color: rgba(212, 175, 55, 0.7);
        background: rgba(212, 175, 55, 0.15);
    }}

    [data-testid="stSidebar"] .stSelectbox label {{
        color: #f8fafc !important;
        font-weight: 700 !important;
    }}

    /* Checkbox Styling */
    [data-testid="stSidebar"] .stCheckbox {{
        color: #f8fafc;
    }}

    [data-testid="stSidebar"] .stCheckbox label {{
        color: #f8fafc !important;
        font-weight: 700 !important;
    }}

    [data-testid="stSidebar"] .stCheckbox label span {{
        color: #f8fafc !important;
    }}

    /* Button Styling */
    [data-testid="stSidebar"] .stButton > button {{
        width: 100%;
        padding: 1rem 1.5rem;
        border-radius: 14px;
        font-weight: 700;
        font-size: 1rem;
        border: 2px solid #d4af37;
        background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
        color: #1a1f2e;
        transition: all 0.3s ease;
        letter-spacing: 0.025em;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
    }}

    [data-testid="stSidebar"] .stButton > button:hover {{
        background: linear-gradient(135deg, #f4e5b5 0%, #d4af37 100%);
        border-color: #f4e5b5;
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(212, 175, 55, 0.5);
    }}

    [data-testid="stSidebar"] button[kind="primary"] {{
        background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
        color: white;
        border: 2px solid #b8941f;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    }}

    [data-testid="stSidebar"] button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #f4e5b5 0%, #d4af37 100%);
        box-shadow: 0 6px 20px rgba(212, 175, 55, 0.6);
    }}

    [data-testid="stSidebar"] button[kind="secondary"] {{
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        color: white !important;
        border: 2px solid #dc2626 !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    }}

    [data-testid="stSidebar"] button[kind="secondary"]:hover {{
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
        border-color: #b91c1c !important;
    }}

    /* Collapsed Control Button */
    [data-testid="collapsedControl"] {{
        left: {'0.5rem !important' if is_rtl else 'auto !important'};
        right: {'auto !important' if is_rtl else '0.5rem !important'};
    }}

    /* Memory Panel */
    .memory-panel {{
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.08) 100%);
        padding: 1.5rem;
        border-radius: 16px;
        border-right: {'4px solid #d4af37' if is_rtl else 'none'};
        border-left: {'none' if is_rtl else '4px solid #d4af37'};
        margin-top: 0.75rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }}

    .memory-panel:hover {{
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.25) 0%, rgba(212, 175, 55, 0.15) 100%);
        box-shadow: 0 6px 16px rgba(212, 175, 55, 0.4);
    }}

    .memory-panel-row {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.75rem;
        direction: {'rtl' if is_rtl else 'ltr'};
        align-items: center;
    }}

    .memory-panel-row:last-child {{
        margin-bottom: 0;
    }}

    .memory-label {{
        color: #cbd5e1;
        font-size: 0.95rem;
        font-weight: 700;
    }}

    .memory-value {{
        color: #d4af37;
        font-weight: 900;
        font-size: 1.2rem;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    }}

    /* Sample Questions */
    .sample-question {{
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.12) 0%, rgba(212, 175, 55, 0.06) 100%);
        padding: 1rem 1.25rem;
        border-radius: 14px;
        margin-bottom: 0.85rem;
        font-size: 0.95rem;
        border: 2px solid rgba(212, 175, 55, 0.3);
        color: #f8fafc;
        transition: all 0.3s ease;
        text-align: {'right' if is_rtl else 'left'};
        direction: {'rtl' if is_rtl else 'ltr'};
        font-weight: 600;
        line-height: 1.6;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
    }}

    .sample-question:hover {{
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.25) 0%, rgba(212, 175, 55, 0.15) 100%);
        border-color: rgba(212, 175, 55, 0.6);
        transform: translateX({'-8px' if is_rtl else '8px'});
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.4);
    }}

    /* Divider Styling */
    [data-testid="stSidebar"] hr {{
        border-color: rgba(212, 175, 55, 0.3) !important;
        border-width: 2px !important;
        margin: 1.5rem 0;
    }}

    /* Main content adjustment */
    .main .block-container {{
        margin-right: {'21rem !important' if is_rtl else '1rem !important'};
        margin-left: {'1rem !important' if is_rtl else '1rem !important'};
    }}

    [data-testid="stSidebar"][aria-expanded="false"] ~ .main .block-container {{
        margin-right: {'1rem !important' if is_rtl else 'auto'};
    }}

    /* Header Styling */
    .sidebar-header {{
        text-align: center;
        padding: 1.5rem 0 2rem 0;
    }}

    .sidebar-icon {{
        font-size: 4rem;
        display: block;
        margin-bottom: 1.2rem;
        animation: pulse 2s infinite;
        filter: drop-shadow(0 4px 8px rgba(212, 175, 55, 0.6));
    }}

    @keyframes pulse {{
        0%, 100% {{ transform: scale(1); }}
        50% {{ transform: scale(1.08); }}
    }}

    .sidebar-title {{
        margin: 0;
        font-size: 2rem;
        font-weight: 900;
        color: #d4af37;
        text-shadow: 0 2px 8px rgba(212, 175, 55, 0.6);
        letter-spacing: -0.025em;
    }}

    .sidebar-subtitle {{
        color: #cbd5e1;
        font-size: 1rem;
        margin-top: 0.75rem;
        line-height: 1.5;
        font-weight: 600;
    }}

    /* Footer Styling */
    .sidebar-footer {{
        text-align: center;
        padding-top: 1.5rem;
        border-top: 2px solid rgba(212, 175, 55, 0.3);
        color: #94a3b8;
        font-size: 0.9rem;
    }}

    .sidebar-footer strong {{
        color: #d4af37;
        font-weight: 800;
    }}

    .sidebar-footer p {{
        color: #94a3b8 !important;
    }}
    </style>
    """, unsafe_allow_html=True)


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
def _render_divider():
    """Render a professional divider line"""
    st.markdown("<hr style='margin-top:1.5rem; border-color:rgba(212, 175, 55, 0.3); border-width: 2px;'>", 
                unsafe_allow_html=True)


def _get_current_language_display(language_code: str) -> str:
    """Get the display name for the current language code"""
    for display_name, config in LANGUAGE_CONFIG.items():
        if config['code'] == language_code:
            return display_name
    return "English"


def _is_rtl_language(language_code: str) -> bool:
    """Check if the given language code is RTL"""
    for config in LANGUAGE_CONFIG.values():
        if config['code'] == language_code:
            return config['rtl']
    return False


# -----------------------------
# HEADER SECTION
# -----------------------------
def _render_header(language_code: str):
    """Render professional header"""
    st.markdown(f"""
    <div class="sidebar-header">
        <span class="sidebar-icon">🎙️</span>
        <h2 class="sidebar-title">{t('assistant_title', language_code).replace('🕋 ', '')}</h2>
        <p class="sidebar-subtitle">{t('voice_mode_desc', language_code)}</p>
    </div>
    """, unsafe_allow_html=True)


# -----------------------------
# LANGUAGE SELECTION
# -----------------------------
def _render_language_section(language_code: str):
    """Render professional language selector"""
    st.markdown(f"### 🌐 {t('language_title', language_code)}")
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
        label_visibility="collapsed",
        key="voicebot_lang_selector"
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
    """Render professional accessibility controls"""
    st.markdown(f"### ♿ {t('accessibility_title', language_code)}")
    st.caption(t('accessibility_desc', language_code))

    font_labels = [
        t('font_normal', language_code), 
        t('font_large', language_code), 
        t('font_extra_large', language_code)
    ]
    font_values = ['normal', 'large', 'extra-large']
    
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
# SAMPLE QUESTIONS
# -----------------------------
def _render_sample_questions(language_code: str):
    """Render professional sample questions"""
    st.markdown(f"### 💡 {t('examples_title', language_code)}")
    st.caption(t('examples_caption', language_code))

    try:
        sample_questions = t('sample_questions', language_code)
        
        for i, question in enumerate(sample_questions):
            st.markdown(f"""
            <div class="sample-question">
                <strong>{i+1}.</strong> {question}
            </div>
            """, unsafe_allow_html=True)
    except Exception as e:
        st.error(f"Error loading sample questions: {str(e)}")


# -----------------------------
# MEMORY SECTION
# -----------------------------
def _render_memory_section(memory, language_code: str):
    """Render professional memory status"""
    st.markdown(f"### 💾 {t('memory_status_title', language_code)}")
    st.caption(t('memory_status_desc', language_code))

    try:
        memory_summary = memory.get_memory_summary()
        
        st.markdown(f"""
        <div class="memory-panel">
            <div class="memory-panel-row">
                <span class="memory-label">📝 {t('voice_memory_messages', language_code)}</span>
                <strong class="memory-value">{memory_summary['total_messages']}</strong>
            </div>
            <div class="memory-panel-row">
                <span class="memory-label">⏱️ {t('voice_session_duration', language_code)}</span>
                <strong class="memory-value">{memory_summary['session_duration']}</strong>
            </div>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("")
        
        if st.button(f"🗑️ {t('voice_clear_memory', language_code)}", use_container_width=True, type="secondary"):
            _clear_memory_and_state(memory, language_code)
            
    except Exception as e:
        st.error(f"Error loading memory: {str(e)}")


def _clear_memory_and_state(memory, language_code: str):
    """Clear memory with professional feedback"""
    try:
        memory.clear_memory()
        
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
# NAVIGATION SECTION
# -----------------------------
def _render_navigation(language_code: str):
    """Render professional navigation"""
    st.markdown(f"### 🧭 {t('nav_title', language_code)}")
    st.caption(t('nav_caption', language_code))

    back_label = t('voice_return_button', language_code)
    arrow = "→" if _is_rtl_language(language_code) else "←"

    if st.button(f"{arrow} {back_label}", use_container_width=True, type="primary"):
        try:
            st.switch_page("./app.py")
        except Exception as e:
            st.error(f"Navigation error: {str(e)}")


# -----------------------------
# FOOTER SECTION
# -----------------------------
def _render_footer(language_code: str):
    """Render professional footer"""
    from datetime import datetime
    year = datetime.now().year
    
    st.markdown(f"""
    <div class="sidebar-footer">
        <p>© {year} Hajj Voice Assistant</p>
        <p style="margin-top: 0.5rem;">
            Powered by <strong>AI Speech Technology</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)