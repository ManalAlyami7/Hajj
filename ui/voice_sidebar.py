"""
Professional Voicebot Sidebar Component Module
Refactored for improved maintainability and organization
"""

import time
import streamlit as st
from datetime import datetime
from typing import Dict, List, Optional

from utils.translations import t


# ============================================================================
# CONSTANTS
# ============================================================================
LANGUAGE_CONFIG = {
    "English": {'code': 'English', 'rtl': False},
    "العربية": {'code': 'العربية', 'rtl': True},
    "اردو": {'code': 'اردو', 'rtl': True}
}

FONT_SIZE_CONFIG = {
    'normal': 0,
    'large': 1,
    'extra-large': 2
}


# ============================================================================
# PUBLIC INTERFACE
# ============================================================================
def render_sidebar(memory, language_code: str) -> None:
    """Render the complete professional sidebar with all controls"""
    with st.sidebar:
        renderer = VoicebotSidebarRenderer(memory, language_code)
        renderer.render()


# ============================================================================
# VOICEBOT SIDEBAR RENDERER CLASS
# ============================================================================
class VoicebotSidebarRenderer:
    """Handles rendering of voicebot sidebar components"""
    
    def __init__(self, memory, language_code: str):
        self.memory = memory
        self.language_code = language_code
        self.is_rtl = self._is_rtl_language(language_code)
    
    # ------------------------------------------------------------------------
    # MAIN RENDER METHOD
    # ------------------------------------------------------------------------
    def render(self) -> None:
        """Render all sidebar sections"""
        self._inject_professional_styles()
        self._render_all_sections()
    
    def _render_all_sections(self) -> None:
        """Render all sidebar sections with dividers"""
        sections = [
            self._render_header,
            self._render_navigation_buttons,
            self._render_language_section,
            self._render_accessibility_section,
            self._render_sample_questions,
            self._render_memory_section,
            self._render_footer
        ]
        
        for i, section in enumerate(sections):
            section()
            if i < len(sections) - 1:
                self._render_divider()
    
    # ------------------------------------------------------------------------
    # STYLING
    # ------------------------------------------------------------------------
    def _inject_professional_styles(self) -> None:
        """Inject enhanced professional CSS for voicebot sidebar"""
        st.markdown(self._get_professional_css(), unsafe_allow_html=True)
    
    def _get_professional_css(self) -> str:
        """Return professional CSS as string"""
        return f"""
    <style>
    /* ===== Sidebar Base Styling ===== */
    [data-testid="stSidebar"] {{
        left: {'auto !important' if self.is_rtl else '0 !important'};
        right: {'0 !important' if self.is_rtl else 'auto !important'};
        background: linear-gradient(180deg, #0f1419 0%, #1a1f2e 100%) !important;
        border-right: {'none' if self.is_rtl else '2px solid #d4af37'} !important;
        border-left: {'2px solid #d4af37' if self.is_rtl else 'none'} !important;
    }}

    [data-testid="stSidebar"] > div:first-child {{
        {'transform: translateX(0) !important;' if self.is_rtl else ''}
    }}

    [data-testid="stSidebar"] .block-container {{
        direction: {'rtl' if self.is_rtl else 'ltr'};
        padding: 2rem 1.5rem;
    }}

    /* ===== Text Colors ===== */
    [data-testid="stSidebar"] .stMarkdown {{
        text-align: {'right' if self.is_rtl else 'left'};
        color: #f8fafc !important;
    }}

    [data-testid="stSidebar"] .stMarkdown p,
    [data-testid="stSidebar"] .stMarkdown span,
    [data-testid="stSidebar"] .stMarkdown div {{
        color: #f8fafc !important;
    }}

    /* ===== Headers ===== */
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

    /* ===== Captions ===== */
    [data-testid="stSidebar"] .stCaption {{
        color: #94a3b8 !important;
        font-size: 0.9rem;
        line-height: 1.6;
        font-weight: 500;
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

    /* ===== Button Styling ===== */
    [data-testid="stSidebar"] .stButton > button {{
        width: 100%;
        padding: 0.9rem 1.25rem;
        border-radius: 10px;
        font-weight: 600;
        font-size: 0.95rem;
        border: 2px solid #d4af37 !important;
        background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%) !important;
        color: #1a1f2e !important;
        transition: all 0.3s ease;
        letter-spacing: 0.015em;
        box-shadow: 0 3px 10px rgba(212, 175, 55, 0.3);
    }}

    [data-testid="stSidebar"] .stButton > button:hover {{
        background: linear-gradient(135deg, #f4e5b5 0%, #d4af37 100%) !important;
        border-color: #f4e5b5 !important;
        transform: translateY(-2px);
        box-shadow: 0 5px 14px rgba(212, 175, 55, 0.4);
    }}

    /* ===== Primary Button ===== */
    [data-testid="stSidebar"] button[kind="primary"] {{
        background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%) !important;
        color: white !important;
        border: 2px solid #b8941f !important;
    }}

    [data-testid="stSidebar"] button[kind="primary"]:hover {{
        background: linear-gradient(135deg, #f4e5b5 0%, #d4af37 100%) !important;
        box-shadow: 0 5px 16px rgba(212, 175, 55, 0.5);
    }}

    /* ===== Secondary Buttons ===== */
    [data-testid="stSidebar"] button[kind="secondary"] {{
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
        color: white !important;
        border: 2px solid #dc2626 !important;
    }}

    [data-testid="stSidebar"] button[kind="secondary"]:hover {{
        background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
        border-color: #b91c1c !important;
    }}

    /* ===== Collapsed Control Button ===== */
    [data-testid="collapsedControl"] {{
        left: {'0.5rem !important' if self.is_rtl else 'auto !important'};
        right: {'auto !important' if self.is_rtl else '0.5rem !important'};
        background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%) !important;
        color: white !important;
        border-radius: 0.5rem !important;
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3) !important;
    }}

    [data-testid="collapsedControl"]:hover {{
        background: linear-gradient(135deg, #e6c345 0%, #c9a527 100%) !important;
        transform: scale(1.05) !important;
    }}

    /* ===== Memory Panel ===== */
    .memory-panel {{
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.08) 0%, rgba(212, 175, 55, 0.04) 100%);
        padding: 1.5rem;
        border-radius: 16px;
        border-right: {'4px solid #d4af37' if self.is_rtl else 'none'};
        border-left: {'none' if self.is_rtl else '4px solid #d4af37'};
        margin-top: 0.75rem;
        transition: all 0.3s ease;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
    }}

    .memory-panel:hover {{
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.12) 0%, rgba(212, 175, 55, 0.08) 100%);
        box-shadow: 0 6px 16px rgba(212, 175, 55, 0.2);
        transform: translateY(-2px);
    }}

    .memory-panel-row {{
        display: flex;
        justify-content: space-between;
        margin-bottom: 0.75rem;
        direction: {'rtl' if self.is_rtl else 'ltr'};
        align-items: center;
    }}

    .memory-panel-row:last-child {{
        margin-bottom: 0;
    }}

    .memory-label {{
        color: #64748b;
        font-size: 0.95rem;
        font-weight: 700;
    }}

    .memory-value {{
        color: #d4af37;
        font-weight: 900;
        font-size: 1.2rem;
        text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
    }}

    /* ===== Sample Questions ===== */
    .sample-question {{
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.08) 0%, rgba(212, 175, 55, 0.04) 100%);
        padding: 1rem 1.25rem;
        border-radius: 14px;
        margin-bottom: 0.85rem;
        font-size: 0.95rem;
        border: 2px solid rgba(212, 175, 55, 0.25);
        color: #1f2937;
        transition: all 0.3s ease;
        text-align: {'right' if self.is_rtl else 'left'};
        direction: {'rtl' if self.is_rtl else 'ltr'};
        font-weight: 600;
        line-height: 1.6;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.06);
    }}

    .sample-question:hover {{
        background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.08) 100%);
        border-color: rgba(212, 175, 55, 0.5);
        transform: translateX({'-8px' if self.is_rtl else '8px'});
        box-shadow: 0 4px 12px rgba(212, 175, 55, 0.2);
    }}

    /* ===== Divider Styling ===== */
    [data-testid="stSidebar"] hr {{
        border-color: rgba(212, 175, 55, 0.3) !important;
        border-width: 2px !important;
        margin: 1.5rem 0;
    }}

    /* ===== Main content adjustment ===== */
    .main .block-container {{
        margin-right: {'21rem !important' if self.is_rtl else '1rem !important'};
        margin-left: {'1rem !important' if self.is_rtl else '1rem !important'};
    }}

    [data-testid="stSidebar"][aria-expanded="false"] ~ .main .block-container {{
        margin-right: {'1rem !important' if self.is_rtl else 'auto'};
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
        filter: drop-shadow(0 4px 8px rgba(212, 175, 55, 0.3));
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
        text-shadow: 0 2px 8px rgba(212, 175, 55, 0.3);
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
    }}

    /* ===== Scrollbar Styling ===== */
    [data-testid="stSidebar"] ::-webkit-scrollbar {{
        width: 8px;
    }}

    [data-testid="stSidebar"] ::-webkit-scrollbar-track {{
        background: #1a1f2e;
        border-radius: 4px;
    }}

    [data-testid="stSidebar"] ::-webkit-scrollbar-thumb {{
        background: linear-gradient(180deg, #d4af37 0%, #b8941f 100%);
        border-radius: 4px;
    }}

    [data-testid="stSidebar"] ::-webkit-scrollbar-thumb:hover {{
        background: linear-gradient(180deg, #e6c345 0%, #c9a527 100%);
    }}
    </style>
    """
    
    # ------------------------------------------------------------------------
    # SECTION RENDERERS
    # ------------------------------------------------------------------------
    def _render_header(self) -> None:
        """Render professional header"""
        header_html = f"""
        <div class="sidebar-header">
            <span class="sidebar-icon">🎙️</span>
            <h2 class="sidebar-title">{t('voice_main_title', self.language_code).replace('🕋 ', '')}</h2>
            <p class="sidebar-subtitle">{t('assistant_subtitle', self.language_code)}</p>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)
    
    def _render_navigation_buttons(self) -> None:
        """Render professional navigation buttons"""
        st.markdown(f"### {t('mode_title', self.language_code)}")
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(
                f"💬 {t('mode_chatbot', self.language_code)}", 
                key="nav_chatbot", 
                use_container_width=True, 
                type="primary"
            ):
                self._navigate_to_page("app.py")
        
        with col2:
            if st.button(
                f"🎙️ {t('mode_voicebot', self.language_code)}", 
                key="nav_voicebot", 
                use_container_width=True, 
                type="primary"
            ):
                st.info("Current page")
    
    def _render_language_section(self) -> None:
        """Render professional language selector"""
        st.markdown(f"### {t('language_title', self.language_code)}")
        st.caption(t('feat_multilingual_desc', self.language_code))

        current_lang_display = self._get_current_language_display()
        
        selected_language = st.selectbox(
            t('language_title', self.language_code),
            options=list(LANGUAGE_CONFIG.keys()),
            index=list(LANGUAGE_CONFIG.keys()).index(current_lang_display),
            label_visibility="collapsed",
            key="voicebot_lang_selector"
        )

        new_language_code = LANGUAGE_CONFIG[selected_language]['code']
        if new_language_code != self.language_code:
            self._handle_language_change(new_language_code)
    
    def _render_accessibility_section(self) -> None:
        """Render professional accessibility controls"""
        st.markdown(f"### {t('accessibility_title', self.language_code)}")
        st.caption(t('accessibility_desc', self.language_code))

        self._render_font_size_selector()
        st.markdown("")
        self._render_contrast_toggle()
    
    def _render_font_size_selector(self) -> None:
        """Render font size selector"""
        font_labels = [
            t('font_normal', self.language_code), 
            t('font_large', self.language_code), 
            t('font_extra_large', self.language_code)
        ]
        font_values = ['normal', 'large', 'extra-large']
        
        if 'font_size' not in st.session_state:
            st.session_state.font_size = 'normal'
        
        current_index = FONT_SIZE_CONFIG.get(st.session_state.font_size, 0)

        selected_font = st.selectbox(
            t('font_size_label', self.language_code),
            options=font_labels,
            index=current_index
        )

        selected_index = font_labels.index(selected_font)
        new_font_size = font_values[selected_index]
        
        if new_font_size != st.session_state.font_size:
            st.session_state.font_size = new_font_size
            st.rerun()
    
    def _render_contrast_toggle(self) -> None:
        """Render high contrast toggle"""
        if 'high_contrast' not in st.session_state:
            st.session_state.high_contrast = False

        high_contrast = st.checkbox(
            t('contrast_label', self.language_code),
            value=st.session_state.high_contrast,
            help=t('contrast_help', self.language_code)
        )

        if high_contrast != st.session_state.high_contrast:
            st.session_state.high_contrast = high_contrast
            st.rerun()
    
    def _render_sample_questions(self) -> None:
        """Render professional sample questions"""
        st.markdown(f"### {t('examples_title', self.language_code)}")
        st.caption(t('examples_caption', self.language_code))

        try:
            sample_questions = t('sample_questions', self.language_code)
            
            for i, question in enumerate(sample_questions):
                question_html = f"""
                <div class="sample-question">
                    <strong>{i+1}.</strong> {question}
                </div>
                """
                st.markdown(question_html, unsafe_allow_html=True)
        except Exception as e:
            st.error(f"Error loading sample questions: {str(e)}")
    
    def _render_memory_section(self) -> None:
        """Render professional memory status"""
        st.markdown(f"### {t('memory_status_title', self.language_code)}")
        st.caption(t('memory_status_desc', self.language_code))

        try:
            memory_summary = self.memory.get_memory_summary()
            
            memory_html = f"""
            <div class="memory-panel">
                <div class="memory-panel-row">
                    <span class="memory-label">📝 {t('voice_memory_messages', self.language_code)}</span>
                    <strong class="memory-value">{memory_summary['total_messages']}</strong>
                </div>
                <div class="memory-panel-row">
                    <span class="memory-label">⏱️ {t('voice_session_duration', self.language_code)}</span>
                    <strong class="memory-value">{memory_summary['session_duration']}</strong>
                </div>
            </div>
            """
            st.markdown(memory_html, unsafe_allow_html=True)

            st.markdown("")
            
            if st.button(
                f"🗑️ {t('voice_clear_memory', self.language_code)}", 
                use_container_width=True, 
                type="secondary"
            ):
                self._clear_memory()
                
        except Exception as e:
            st.error(f"Error loading memory: {str(e)}")
    
    def _render_footer(self) -> None:
        """Render professional footer"""
        year = datetime.now().year
        
        footer_html = f"""
        <div class="sidebar-footer">
            <p>© {year} {t('footer_title_voice', self.language_code)}</p>
            <p style="margin-top: 0.5rem;">
                {t('footer_powered', self.language_code)} <strong>{t('footer_tech', self.language_code)}</strong>
            </p>
        </div>
        """
        st.markdown(footer_html, unsafe_allow_html=True)
    
    # ------------------------------------------------------------------------
    # HELPER METHODS
    # ------------------------------------------------------------------------
    @staticmethod
    def _render_divider() -> None:
        """Render a professional divider line"""
        divider_html = "<hr style='margin-top:1.5rem; border-color:rgba(212, 175, 55, 0.3); border-width: 2px;'>"
        st.markdown(divider_html, unsafe_allow_html=True)
    
    def _get_current_language_display(self) -> str:
        """Get the display name for the current language code"""
        for display_name, config in LANGUAGE_CONFIG.items():
            if config['code'] == self.language_code:
                return display_name
        return "English"
    
    @staticmethod
    def _is_rtl_language(language_code: str) -> bool:
        """Check if the given language code is RTL"""
        for config in LANGUAGE_CONFIG.values():
            if config['code'] == language_code:
                return config['rtl']
        return False
    
    @staticmethod
    def _navigate_to_page(page_path: str) -> None:
        """Navigate to a page"""
        try:
            st.switch_page(page_path)
        except Exception:
            st.rerun()
    
    def _handle_language_change(self, new_language_code: str) -> None:
        """Handle language change"""
        st.session_state.language = new_language_code
        st.session_state.is_rtl = self._is_rtl_language(new_language_code)
        st.rerun()
    
    def _clear_memory(self) -> None:
        """Clear memory with professional feedback"""
        try:
            self.memory.clear_memory()
            
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
            
            st.success(t('memory_cleared', self.language_code))
            time.sleep(1)
            st.rerun()
        except Exception as e:
            st.error(f"Error clearing memory: {str(e)}")