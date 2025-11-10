"""
Professional Voicebot Sidebar Component Module
Enhanced design matching Chatbot sidebar with improved consistency
Fixed color scheme with proper contrast and modern professional look
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
        st.markdown("---")

        # Navigation
        _render_navigation_buttons(language_code)
        st.markdown("---")

        # Language Selection
        _render_language_section(language_code)
        st.markdown("---")

        # Memory Status (Statistics)
        _render_memory_section(memory, language_code)
        st.markdown("---")

        # Sample Questions
        _render_sample_questions(language_code)
        st.markdown("---")

        # Clear Memory Button
        _render_clear_button(memory, language_code)
        st.markdown("---")

        # Accessibility
        _render_accessibility_section(language_code)
        st.markdown("---")
        
        # Features Section
        _render_features_section(language_code)
        st.markdown("---")
        
        # Footer
        _render_footer(language_code)


# -----------------------------
# PROFESSIONAL STYLING
# -----------------------------
def _inject_professional_styles(is_rtl: bool):
    """Inject enhanced professional CSS matching chatbot sidebar"""
    st.markdown(f"""
    <style>
    /* ===== Sidebar Base Styling ===== */
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

    /* ===== Text Colors ===== */
    [data-testid="stSidebar"] .stMarkdown {{
        text-align: {'right' if is_rtl else 'left'};
        color: #f8fafc !important;
    }}

    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown span,
    [data-testid="stSidebar"] .stMarkdown div {{
        color: #f8fafc !important;
    }}

    [data-testid="stSidebar"] h2,
    [data-testid="stSidebar"] h3 {{
        color: #d4af37 !important;
        font-weight: 800;
        text-align: center;
        letter-spacing: -0.025em;
        margin-bottom: 1rem;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
    }}

    [data-testid="stSidebar"] p {{
        color: #cbd5e1 !important;
        line-height: 1.7;
        font-weight: 500;
    }}

    /* ===== Dividers ===== */
    [data-testid="stSidebar"] hr {{
        border-color: rgba(212, 175, 55, 0.3) !important;
        border-width: 2px !important;
        margin: 1.5rem 0;
    }}

    /* ===== Radio Buttons (Language Selector) ===== */
    [data-testid="stSidebar"] .stRadio > div {{
        background: rgba(212, 175, 55, 0.1);
        padding: 1rem;
        border-radius: 14px;
        border: 2px solid rgba(212, 175, 55, 0.3);
        direction: ltr;
    }}

    [data-testid="stSidebar"] .stRadio label {{
        color: #f8fafc !important;
        font-weight: 700 !important;
        font-size: 1rem !important;
    }}

    [data-testid="stSidebar"] .stRadio label span {{
        color: #f8fafc !important;
    }}

    /* ===== Checkbox Styling ===== */
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

    /* ===== Selectbox Styling ===== */
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

    /* ===== Primary Buttons (Gold Theme) ===== */
    [data-testid="stSidebar"] .stButton > button {{
        width: 100%;
        padding: 1rem 1.5rem;
        border-radius: 14px;
        font-weight: 700;
        font-size: 1rem;
        border: 2px solid #d4af37 !important;
        background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%) !important;
        color: #1a1f2e !important;
        transition: all 0.3s ease;
        letter-spacing: 0.025em;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
    }}

    [data-testid="stSidebar"] .stButton > button:hover {{
        background: linear-gradient(135deg, #f4e5b5 0%, #d4af37 100%) !important;
        border-color: #f4e5b5 !important;
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(212, 175, 55, 0.5);
    }}

    /* ===== Secondary Buttons (Alert/Clear) ===== */
    [data-testid="stSidebar"] button[kind="secondary"] {{
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        color: white !important;
        border: 2px solid #dc2626 !important;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
        box-shadow: 0 4px 12px rgba(239, 68, 68, 0.3);
    }}

    [data-testid="stSidebar"] button[kind="secondary"]:hover {{
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
        border-color: #b91c1c !important;
        transform: translateY(-3px);
        box-shadow: 0 6px 16px rgba(239, 68, 68, 0.5);
    }}

    /* ===== Statistics Cards ===== */
    .stat-card {{
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.08) 100%);
        padding: 1.5rem;
        border-radius: 16px;
        margin-bottom: 1.2rem;
        border: 2px solid rgba(212, 175, 55, 0.4);
        text-align: center;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
    }}

    .stat-card:hover {{
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.25) 0%, rgba(212, 175, 55, 0.15) 100%);
        border-color: rgba(212, 175, 55, 0.7);
        transform: translateY(-4px);
        box-shadow: 0 8px 20px rgba(212, 175, 55, 0.4);
    }}

    .stat-number {{
        font-size: 2.5rem;
        font-weight: 900;
        color: #d4af37;
        line-height: 1;
        margin: 0.75rem 0;
        text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
    }}

    .stat-label {{
        font-size: 0.95rem;
        color: #f8fafc;
        font-weight: 700;
        text-transform: uppercase;
        letter-spacing: 0.075em;
    }}

    /* ===== Feature Items ===== */
    .feature-item {{
        display: flex;
        align-items: flex-start;
        margin-bottom: 1.2rem;
        padding: 1.2rem;
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(212, 175, 55, 0.05) 100%);
        border-radius: 12px;
        border-left: {'none' if is_rtl else '4px solid #d4af37'};
        border-right: {'4px solid #d4af37' if is_rtl else 'none'};
        transition: all 0.3s ease;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        direction: {'rtl' if is_rtl else 'ltr'};
    }}

    .feature-item:hover {{
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(212, 175, 55, 0.1) 100%);
        transform: translateX({'8px' if is_rtl else '-8px'});
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
    }}

    .feature-icon {{
        font-size: 2rem;
        margin-right: {'0' if is_rtl else '1.2rem'};
        margin-left: {'1.2rem' if is_rtl else '0'};
        flex-shrink: 0;
    }}

    .feature-content {{
        flex: 1;
        text-align: {'right' if is_rtl else 'left'};
    }}

    .feature-title {{
        color: #d4af37;
        font-weight: 800;
        font-size: 1.1rem;
        margin-bottom: 0.3rem;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    }}

    .feature-desc {{
        color: #cbd5e1;
        font-size: 0.9rem;
        line-height: 1.6;
        font-weight: 500;
    }}

    /* ===== Header Styling ===== */
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

    /* ===== Footer Styling ===== */
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
        margin: 0.5rem 0;
    }}

    /* ===== Collapsed Control ===== */
    [data-testid="collapsedControl"] {{
        left: {'0.5rem !important' if is_rtl else 'auto !important'};
        right: {'auto !important' if is_rtl else '0.5rem !important'};
    }}

    /* ===== Main Content Adjustment ===== */
    .main .block-container {{
        margin-right: {'21rem !important' if is_rtl else '1rem !important'};
        margin-left: {'1rem !important' if is_rtl else '1rem !important'};
    }}

    [data-testid="stSidebar"][aria-expanded="false"] ~ .main .block-container {{
        margin-right: {'1rem !important' if is_rtl else 'auto'};
    }}
    </style>
    """, unsafe_allow_html=True)


# -----------------------------
# HELPER FUNCTIONS
# -----------------------------
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
        <h2 class="sidebar-title">{t('voice_main_title', language_code).replace('🕋 ', '').replace('🎙️ ', '')}</h2>
        <p class="sidebar-subtitle">{t('assistant_subtitle', language_code)}</p>
    </div>
    """, unsafe_allow_html=True)


# -----------------------------
# NAVIGATION SECTION
# -----------------------------
def _render_navigation_buttons(lang):
    """Render professional navigation buttons"""
    st.markdown(f"<h3>🎯 {t('mode_title', lang)}</h3>", unsafe_allow_html=True)
    
    col1, col2 = st.columns(2)
    
    with col1:
        if st.button(f"💬 {t('mode_chatbot', lang)}", key="nav_chatbot", use_container_width=True):
            try:
                st.switch_page("app.py")
            except Exception:
                st.rerun()
    
    with col2:
        if st.button(f"🎙️ {t('mode_voicebot', lang)}", key="nav_voicebot", use_container_width=True):
            try:
                st.switch_page("pages/voicebot.py")
            except Exception:
                st.info(t('voicebot_unavailable', lang))


# -----------------------------
# LANGUAGE SELECTION
# -----------------------------
def _render_language_section(language_code: str):
    """Render professional language selector matching chatbot style"""
    st.markdown(f"<h3>🌐 {t('language_title', language_code)}</h3>", unsafe_allow_html=True)

    language_options = {
        "English 🇬🇧": 'English',
        "العربية 🇸🇦": 'العربية',
        "اردو 🇵🇰": 'اردو'
    }

    current_lang_code = language_code
    current_display = None
    for display, code in language_options.items():
        if code == current_lang_code:
            current_display = display
            break
    
    if current_display is None:
        current_display = "English 🇬🇧"
    
    selected_language = st.radio(
        "",
        list(language_options.keys()),
        index=list(language_options.keys()).index(current_display),
        horizontal=True,
        label_visibility="collapsed",
        key="voicebot_lang_selector"
    )

    new_language_code = language_options[selected_language]
    if new_language_code != language_code:
        st.session_state.language = new_language_code
        st.session_state.is_rtl = _is_rtl_language(new_language_code)
        st.rerun()


# -----------------------------
# MEMORY/STATISTICS SECTION
# -----------------------------
def _render_memory_section(memory, language_code: str):
    """Render professional memory/statistics matching chatbot style"""
    st.markdown(f"<h3>📊 {t('memory_status_title', language_code)}</h3>", unsafe_allow_html=True)

    try:
        memory_summary = memory.get_memory_summary()
        
        # Statistics Cards
        stats_data = [
            ("📝", "voice_memory_messages", memory_summary['total_messages']),
            ("⏱️", "voice_session_duration", memory_summary['session_duration'])
        ]
        
        for icon, label_key, value in stats_data:
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size: 2.5rem;">{icon}</div>
                <div class="stat-number">{value}</div>
                <div class="stat-label">{t(label_key, language_code)}</div>
            </div>
            """, unsafe_allow_html=True)
            
    except Exception as e:
        st.error(f"Error loading memory: {str(e)}")


# -----------------------------
# SAMPLE QUESTIONS SECTION
# -----------------------------
def _render_sample_questions(language_code: str):
    """Render professional sample questions as buttons"""
    st.markdown(f"<h3>💡 {t('examples_title', language_code)}</h3>", unsafe_allow_html=True)

    try:
        sample_questions = t('sample_questions', language_code)
        
        for i, question in enumerate(sample_questions):
            if st.button(
                f"📝 {question[:50]}..." if len(question) > 50 else f"📝 {question}",
                key=f"sample_q_{i}",
                use_container_width=True
            ):
                # Handle question selection (you can add your logic here)
                st.info(f"{t('selected_question', language_code)}: {question}")
                
    except Exception as e:
        st.error(f"Error loading sample questions: {str(e)}")


# -----------------------------
# CLEAR BUTTON SECTION
# -----------------------------
def _render_clear_button(memory, language_code: str):
    """Render professional clear memory button"""
    if st.button(
        f"🗑️ {t('voice_clear_memory', language_code)}", 
        use_container_width=True, 
        type="secondary",
        key="clear_memory_btn"
    ):
        _clear_memory_and_state(memory, language_code)


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
# ACCESSIBILITY SECTION
# -----------------------------
def _render_accessibility_section(language_code: str):
    """Render professional accessibility controls"""
    st.markdown(f"<h3>♿ {t('accessibility_title', language_code)}</h3>", unsafe_allow_html=True)

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
        index=current_index,
        key="font_selector"
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
        help=t('contrast_help', language_code),
        key="contrast_checkbox"
    )

    if high_contrast != st.session_state.high_contrast:
        st.session_state.high_contrast = high_contrast
        st.rerun()


# -----------------------------
# FEATURES SECTION
# -----------------------------
def _render_features_section(language_code: str):
    """Render professional features section"""
    st.markdown(f"<h3>✨ {t('features_title', language_code)}</h3>", unsafe_allow_html=True)

    features = [
        ("feat_voice_ai", "feat_voice_ai_desc", "🎤"),
        ("feat_multilingual", "feat_multilingual_desc", "🌐"),
        ("feat_realtime", "feat_realtime_desc", "⚡"),
        ("feat_secure", "feat_secure_desc", "🔐")
    ]

    for title_key, desc_key, emoji in features:
        st.markdown(f"""
        <div class="feature-item">
            <div class="feature-icon">{emoji}</div>
            <div class="feature-content">
                <div class="feature-title">{t(title_key, language_code)}</div>
                <div class="feature-desc">{t(desc_key, language_code)}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)


# -----------------------------
# FOOTER SECTION
# -----------------------------
def _render_footer(language_code: str):
    """Render professional footer"""
    from datetime import datetime
    year = datetime.now().year
    
    st.markdown(f"""
    <div class="sidebar-footer">
        <p>© {year} {t('footer_title_voice', language_code)}</p>
        <p style="margin-top: 0.5rem;">
            {t('footer_powered', language_code)} <strong>{t('footer_tech', language_code)}</strong>
        </p>
    </div>
    """, unsafe_allow_html=True)