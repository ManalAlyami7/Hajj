"""
Professional Sidebar Interface Module
Enhanced with sleek top-corner report button
"""

import streamlit as st
from datetime import datetime
from typing import Dict, List, Tuple
import pytz

from utils.translations import t
from utils.state import save_chat_memory, clear_chat_memory


# ============================================================================
# CONSTANTS
# ============================================================================
RIYADH_TZ = pytz.timezone('Asia/Riyadh')

STAT_ICONS = {
    'total': '🏢',
    'authorized': '✅',
    'countries': '🌍',
    'cities': '🏙️'
}

FEATURE_ICONS = {
    'feat_ai': '🤖',
    'feat_multilingual': '🌐',
    'feat_viz': '📈',
    'feat_secure': '🔐'
}

LANGUAGE_OPTIONS = {
    "English 🇬🇧": "English",
    "العربية 🇸🇦": "العربية",
    "اردو 🇵🇰": "اردو"
}


# ============================================================================
# SIDEBAR INTERFACE CLASS
# ============================================================================
class SidebarInterface:
    """Manages professional sidebar display and interactions"""
    
    def __init__(self, db_manager):
        """Initialize with database manager"""
        self.db = db_manager
    
    # ------------------------------------------------------------------------
    # PUBLIC INTERFACE
    # ------------------------------------------------------------------------
    def render(self) -> None:
        """Render complete professional sidebar"""
        with st.sidebar:
            self._inject_sidebar_styles()
            self._render_report_button()  # Top corner button
            self._render_all_sections()
    
    def _render_all_sections(self) -> None:
        """Render all sidebar sections in order"""
        sections = [
            self._render_header,
            self._render_navigation_buttons,
            self._render_language_selector,
            self._render_stats,
            self._render_examples,
            self._render_clear_button,
            self._render_features,
            self._render_footer
        ]
        
        for i, section in enumerate(sections):
            section()
            if i < len(sections) - 1:
                self._render_divider()
    
    @staticmethod
    def _render_divider() -> None:
        """Render professional divider line"""
        st.markdown("---")
    
    # ------------------------------------------------------------------------
    # REPORT BUTTON (TOP CORNER)
    # ------------------------------------------------------------------------
    def _render_report_button(self) -> None:
        """Render sleek report button in top corner"""
        lang = st.session_state.language
        
        # Get appropriate text based on language
        report_text = {
            "English": "Report Agency",
            "العربية": "الإبلاغ",
            "اردو": "رپورٹ کریں"
        }.get(lang, "Report Agency")
        
        # Render compact report button with custom styling
        st.markdown("""
        <style>
        .report-corner-btn {
            position: fixed;
            top: 1rem;
            right: 1rem;
            z-index: 999999;
            padding: 0.6rem 1rem;
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            border: 2px solid #dc2626;
            border-radius: 20px;
            font-weight: 700;
            font-size: 0.85rem;
            cursor: pointer;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4);
            transition: all 0.3s ease;
            text-align: center;
            letter-spacing: 0.025em;
            display: flex;
            align-items: center;
            gap: 0.4rem;
        }
        
        .report-corner-btn:hover {
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
            border-color: #b91c1c;
            transform: translateY(-2px);
            box-shadow: 0 6px 16px rgba(239, 68, 68, 0.6);
        }
        
        .report-corner-btn::before {
            content: '🛡️';
            font-size: 1.1rem;
        }
        
        /* Mobile responsive */
        @media (max-width: 768px) {
            .report-corner-btn {
                top: 0.75rem;
                right: 0.75rem;
                padding: 0.5rem 0.8rem;
                font-size: 0.8rem;
            }
        }
        </style>
        """, unsafe_allow_html=True)
        
        # Use st.button with custom CSS
        if st.button(
            f"🛡️ {report_text}",
            key="report_corner_btn",
            help="File a confidential complaint about an agency",
            type="secondary"
        ):
            st.session_state.app_mode = "report"
            st.switch_page("pages/report.py")
    
    # ------------------------------------------------------------------------
    # STYLING
    # ------------------------------------------------------------------------
    def _inject_sidebar_styles(self) -> None:
        """Inject professional sidebar CSS"""
        st.markdown(self._get_sidebar_css(), unsafe_allow_html=True)
    
    @staticmethod
    def _get_sidebar_css() -> str:
        """Return sidebar CSS as string"""
        return """
        <style>
        /* Sidebar Base Styling */
        [data-testid="stSidebar"] {
            background: linear-gradient(180deg, #0f1419 0%, #1a1f2e 100%);
            border-right: 3px solid #d4af37;
        }
        
        [data-testid="stSidebar"] .block-container {
            padding: 2rem 1.5rem;
        }
        
        /* Sidebar Text Colors */
        [data-testid="stSidebar"] .stMarkdown {
            color: #f8fafc !important;
        }
        
        [data-testid="stSidebar"] .stMarkdown p,
        [data-testid="stSidebar"] .stMarkdown span,
        [data-testid="stSidebar"] .stMarkdown div {
            color: #f8fafc !important;
        }
        
        [data-testid="stSidebar"] h2,
        [data-testid="stSidebar"] h3 {
            color: #d4af37 !important;
            font-weight: 800;
            letter-spacing: -0.025em;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.3);
        }
        
        [data-testid="stSidebar"] p {
            color: #cbd5e1 !important;
            line-height: 1.7;
            font-weight: 500;
        }
        
        /* Sidebar Dividers */
        [data-testid="stSidebar"] hr {
            border-color: rgba(212, 175, 55, 0.3) !important;
            border-width: 2px !important;
            margin: 1.5rem 0;
        }
        
        /* Sidebar Buttons */
        [data-testid="stSidebar"] .stButton > button {
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
        }
        
        [data-testid="stSidebar"] .stButton > button:hover {
            background: linear-gradient(135deg, #f4e5b5 0%, #d4af37 100%);
            border-color: #f4e5b5;
            transform: translateY(-3px);
            box-shadow: 0 6px 16px rgba(212, 175, 55, 0.5);
        }
        
        [data-testid="stSidebar"] button[kind="primary"] {
            background: linear-gradient(135deg, #d4af37 0%, #b8941f 100%);
            color: white;
            border: 2px solid #b8941f;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
        }
        
        [data-testid="stSidebar"] button[kind="primary"]:hover {
            background: linear-gradient(135deg, #f4e5b5 0%, #d4af37 100%);
            box-shadow: 0 6px 20px rgba(212, 175, 55, 0.6);
        }
        
        /* Enhanced Report Button Styling (secondary type) */
        [data-testid="stSidebar"] button[kind="secondary"] {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%) !important;
            color: white !important;
            border: 2px solid #dc2626 !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3) !important;
            padding: 0.6rem 1rem !important;
            font-size: 0.85rem !important;
            border-radius: 20px !important;
            box-shadow: 0 4px 12px rgba(239, 68, 68, 0.4) !important;
            margin-bottom: 1rem !important;
        }
        
        [data-testid="stSidebar"] button[kind="secondary"]:hover {
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%) !important;
            border-color: #b91c1c !important;
            transform: translateY(-2px) !important;
            box-shadow: 0 6px 16px rgba(239, 68, 68, 0.6) !important;
        }
        
        /* Stat Cards */
        .stat-card {
            background: linear-gradient(135deg, rgba(212, 175, 55, 0.15) 0%, rgba(212, 175, 55, 0.08) 100%);
            padding: 1.5rem;
            border-radius: 16px;
            margin-bottom: 1.2rem;
            border: 2px solid rgba(212, 175, 55, 0.4);
            text-align: center;
            transition: all 0.3s ease;
            box-shadow: 0 4px 12px rgba(0, 0, 0, 0.3);
        }
        
        .stat-card:hover {
            background: linear-gradient(135deg, rgba(212, 175, 55, 0.25) 0%, rgba(212, 175, 55, 0.15) 100%);
            border-color: rgba(212, 175, 55, 0.7);
            transform: translateY(-4px);
            box-shadow: 0 8px 20px rgba(212, 175, 55, 0.4);
        }
        
        .stat-number {
            font-size: 2.5rem;
            font-weight: 900;
            color: #d4af37;
            line-height: 1;
            margin: 0.75rem 0;
            text-shadow: 0 2px 4px rgba(0, 0, 0, 0.4);
        }
        
        .stat-label {
            font-size: 0.95rem;
            color: #f8fafc;
            font-weight: 700;
            text-transform: uppercase;
            letter-spacing: 0.075em;
        }
        
        /* Radio Button Styling */
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
        
        [data-testid="stSidebar"] .stRadio label span {
            color: #f8fafc !important;
        }
        
        /* Feature Items */
        .feature-item {
            display: flex;
            align-items: flex-start;
            margin-bottom: 1.2rem;
            padding: 1.2rem;
            background: linear-gradient(135deg, rgba(212, 175, 55, 0.1) 0%, rgba(212, 175, 55, 0.05) 100%);
            border-radius: 12px;
            border-left: 4px solid #d4af37;
            transition: all 0.3s ease;
            box-shadow: 0 2px 8px rgba(0, 0, 0, 0.2);
        }
        
        .feature-item:hover {
            background: linear-gradient(135deg, rgba(212, 175, 55, 0.2) 0%, rgba(212, 175, 55, 0.1) 100%);
            transform: translateX(8px);
            box-shadow: 0 4px 12px rgba(212, 175, 55, 0.3);
        }
        
        .feature-icon {
            font-size: 2rem;
            margin-right: 1.2rem;
            flex-shrink: 0;
        }
        
        .feature-content {
            flex: 1;
        }
        
        .feature-title {
            color: #d4af37;
            font-weight: 800;
            font-size: 1.1rem;
            margin-bottom: 0.3rem;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
        }
        
        .feature-desc {
            color: #cbd5e1;
            font-size: 0.9rem;
            line-height: 1.6;
            font-weight: 500;
        }
        
        /* Header Styling */
        .sidebar-header {
            text-align: center;
            padding: 1.5rem 0 2rem 0;
        }
        
        .sidebar-icon {
            font-size: 4rem;
            margin-bottom: 1.2rem;
            display: block;
            animation: pulse 2s infinite;
            filter: drop-shadow(0 4px 8px rgba(212, 175, 55, 0.5));
        }
        
        @keyframes pulse {
            0%, 100% { transform: scale(1); }
            50% { transform: scale(1.08); }
        }
        
        .sidebar-title {
            margin: 0;
            font-size: 2rem;
            font-weight: 900;
            color: #d4af37;
            text-shadow: 0 2px 8px rgba(212, 175, 55, 0.6);
            letter-spacing: -0.025em;
        }
        
        .sidebar-subtitle {
            color: #cbd5e1;
            font-size: 1rem;
            margin-top: 0.75rem;
            line-height: 1.5;
            font-weight: 600;
        }
        
        /* Footer Styling */
        .sidebar-footer {
            text-align: center;
            padding-top: 1.5rem;
            border-top: 2px solid rgba(212, 175, 55, 0.3);
            color: #94a3b8;
            font-size: 0.9rem;
        }
        
        .sidebar-footer strong {
            color: #d4af37;
            font-weight: 800;
        }
        
        .sidebar-footer p {
            color: #94a3b8 !important;
            margin: 0.5rem 0;
        }
        </style>
        """
    
    # ------------------------------------------------------------------------
    # HEADER SECTION
    # ------------------------------------------------------------------------
    def _render_header(self) -> None:
        """Render professional sidebar header"""
        lang = st.session_state.language
        header_html = f"""
        <div class="sidebar-header">
            <img src="/static/talbiyah.png" class="sidebar-icon" width="60" height="60" style="object-fit: contain; margin-bottom: 1rem;">
            <h2 class="sidebar-title">{t('assistant_title', lang).replace('🕋 ', '')}</h2>
            <p class="sidebar-subtitle">{t('assistant_subtitle', lang)}</p>
        </div>
        """
        st.markdown(header_html, unsafe_allow_html=True)
    
    # ------------------------------------------------------------------------
    # NAVIGATION SECTION
    # ------------------------------------------------------------------------
    def _render_navigation_buttons(self) -> None:
        """Render professional navigation buttons"""
        lang = st.session_state.language
        
        st.markdown(f"<h3>{t('mode_title', lang)}</h3>", unsafe_allow_html=True)
        
        col1, col2 = st.columns(2)
        
        with col1:
            if st.button(
                f"💬 {t('mode_chatbot', lang)}", 
                key="nav_chatbot", 
                use_container_width=True
            ):
                self._navigate_to_page("app.py")
        
        with col2:
            if st.button(
                f"🎙️ {t('mode_voicebot', lang)}", 
                key="nav_voicebot", 
                use_container_width=True
            ):
                self._navigate_to_page("pages/voicebot.py", t('voicebot_unavailable', lang))
    
    @staticmethod
    def _navigate_to_page(page_path: str, fallback_message: str = None) -> None:
        """Navigate to a page with fallback"""
        try:
            st.switch_page(page_path)
        except Exception:
            if fallback_message:
                st.info(fallback_message)
            else:
                st.rerun()
    
    # ------------------------------------------------------------------------
    # LANGUAGE SECTION
    # ------------------------------------------------------------------------
    def _render_language_selector(self) -> None:
        """Render professional language toggle"""
        lang = st.session_state.language
        
        st.markdown(f"<h3>{t('language_title', lang)}</h3>", unsafe_allow_html=True)
        
        current_index = self._get_current_language_index(lang)
        
        language_choice = st.radio(
            "",
            list(LANGUAGE_OPTIONS.keys()),
            index=current_index,
            horizontal=True,
            label_visibility="collapsed",
            key="chatbot_lang_selector"
        )
        
        new_language = LANGUAGE_OPTIONS[language_choice]
        
        if new_language != lang:
            self._handle_language_change(new_language)
    
    @staticmethod
    def _get_current_language_index(current_lang: str) -> int:
        """Get index of current language in options"""
        language_list = list(LANGUAGE_OPTIONS.values())
        try:
            return language_list.index(current_lang)
        except ValueError:
            return 0
    
    def _handle_language_change(self, new_language: str) -> None:
        """Handle language change and update chat"""
        st.session_state.language = new_language
        
        if len(st.session_state.chat_memory) <= 1:
            st.session_state.chat_memory = [{
                "role": "assistant",
                "content": t("welcome_msg", new_language),
                "timestamp": self._get_current_time()
            }]
        
        st.rerun()
    
    # ------------------------------------------------------------------------
    # STATS SECTION
    # ------------------------------------------------------------------------
    def _render_stats(self) -> None:
        """Render professional database statistics"""
        lang = st.session_state.language
        
        st.markdown(f"<h3>{t('stats_title', lang)}</h3>", unsafe_allow_html=True)
        
        stats = self.db.get_stats()
        stat_items = self._get_stat_items()
        
        for key, label_key, icon in stat_items:
            self._render_stat_card(stats, key, label_key, icon, lang)
    
    @staticmethod
    def _get_stat_items() -> List[Tuple[str, str, str]]:
        """Get list of stat items to display"""
        return [
            ("total", "total_agencies", STAT_ICONS['total']),
            ("authorized", "authorized", STAT_ICONS['authorized']),
            ("countries", "countries", STAT_ICONS['countries']),
            ("cities", "cities", STAT_ICONS['cities'])
        ]
    
    @staticmethod
    def _render_stat_card(stats: Dict, key: str, label_key: str, icon: str, lang: str) -> None:
        """Render a single stat card"""
        stat_html = f"""
        <div class="stat-card">
            <div style="font-size: 2.5rem;">{icon}</div>
            <div class="stat-number">{stats.get(key, 0):,}</div>
            <div class="stat-label">{t(label_key, lang)}</div>
        </div>
        """
        st.markdown(stat_html, unsafe_allow_html=True)
    
    # ------------------------------------------------------------------------
    # EXAMPLES SECTION
    # ------------------------------------------------------------------------
    def _render_examples(self) -> None:
        """Render professional example questions"""
        lang = st.session_state.language
        
        st.markdown(f"<h3>{t('examples_title', lang)}</h3>", unsafe_allow_html=True)
        
        example_questions = self._get_example_questions()
        
        for i, (display_key, question_key) in enumerate(example_questions):
            if st.button(
                f"📝 {t(display_key, lang)}",
                key=f"example_{i}",
                use_container_width=True
            ):
                self._handle_example_click(question_key, lang)
    
    @staticmethod
    def _get_example_questions() -> List[Tuple[str, str]]:
        """Get list of example questions"""
        return [
            ("ex_all_auth", "ex_all_auth_q"),
            ("ex_saudi", "ex_saudi_q"),
            ("ex_by_country", "ex_by_country_q"),
            ("ex_emails", "ex_emails_q"),
        ]
    
    def _handle_example_click(self, question_key: str, lang: str) -> None:
        """Handle example question click"""
        question_text = t(question_key, lang)
        st.session_state.chat_memory.append({
            "role": "user",
            "content": question_text,
            "timestamp": self._get_current_time()
        })
        
        st.session_state.pending_example = True
        st.rerun()
    
    # ------------------------------------------------------------------------
    # CLEAR BUTTON SECTION
    # ------------------------------------------------------------------------
    def _render_clear_button(self) -> None:
        """Render professional clear chat button"""
        lang = st.session_state.language
        
        if st.button(
            f"🗑️ {t('clear_chat', lang)}",
            use_container_width=True,
            type="primary"
        ):
            self._clear_chat(lang)
    
    def _clear_chat(self, lang: str) -> None:
        """Clear chat history and reset state"""
        st.session_state.chat_memory = [{
            "role": "assistant",
            "content": t("welcome_msg", lang),
            "timestamp": self._get_current_time()
        }]
        st.session_state.last_result_df = None
        st.session_state.pending_example = False
        clear_chat_memory()
        st.rerun()
    
    # ------------------------------------------------------------------------
    # FEATURES SECTION
    # ------------------------------------------------------------------------
    def _render_features(self) -> None:
        """Render professional features section"""
        lang = st.session_state.get("language", "English")
        
        st.markdown(f"<h3>{t('features_title', lang)}</h3>", unsafe_allow_html=True)

        features = self._get_features()

        for title_key, desc_key, emoji in features:
            self._render_feature_item(title_key, desc_key, emoji, lang)
    
    @staticmethod
    def _get_features() -> List[Tuple[str, str, str]]:
        """Get list of features to display"""
        return [
            ("feat_ai", "feat_ai_desc", FEATURE_ICONS['feat_ai']),
            ("feat_multilingual", "feat_multilingual_desc", FEATURE_ICONS['feat_multilingual']),
            ("feat_viz", "feat_viz_desc", FEATURE_ICONS['feat_viz']),
            ("feat_secure", "feat_secure_desc", FEATURE_ICONS['feat_secure'])
        ]
    
    @staticmethod
    def _render_feature_item(title_key: str, desc_key: str, emoji: str, lang: str) -> None:
        """Render a single feature item"""
        feature_html = f"""
        <div class="feature-item">
            <div class="feature-icon">{emoji}</div>
            <div class="feature-content">
                <div class="feature-title">{t(title_key, lang)}</div>
                <div class="feature-desc">{t(desc_key, lang)}</div>
            </div>
        </div>
        """
        st.markdown(feature_html, unsafe_allow_html=True)
    
    # ------------------------------------------------------------------------
    # FOOTER SECTION
    # ------------------------------------------------------------------------
    def _render_footer(self) -> None:
        """Render professional footer with multilingual support and LinkedIn links"""
        lang = st.session_state.get("language", "English")
        year = datetime.now().year

        # النصوص حسب اللغة
        developed_by_text = {
            "English": "Developed by",
            "العربية": "تم التطوير بواسطة",
            "اردو": "کی طرف سے تیار شدہ"
        }.get(lang, "Developed by")

        footer_html = f"""
        <div class="sidebar-footer">
            <p>© {year} {t('assistant_title', lang).replace('🕋 ', '')}</p>
            <p style="margin-top: 0.8rem; font-weight: 600; color: #d4af37;">
                {developed_by_text}
            </p>
            <div style="margin-top: 0.5rem; display: flex; flex-direction: column; gap: 0.4rem;">
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <a href="https://linkedin.com/in/raghad-almanqour" target="_blank" 
                       style="display: flex; align-items: center; gap: 0.4rem; text-decoration: none; color: #cbd5e1; transition: color 0.3s;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="#0A66C2">
                            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                        </svg>
                        <span>Raghad Almangour</span>
                    </a>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <a href="https://www.linkedin.com/in/manal-alyami/" target="_blank" 
                       style="display: flex; align-items: center; gap: 0.4rem; text-decoration: none; color: #cbd5e1; transition: color 0.3s;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="#0A66C2">
                            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                        </svg>
                        <span>Manal Alyami</span>
                    </a>
                </div>
                <div style="display: flex; align-items: center; gap: 0.5rem;">
                    <a href="https://www.linkedin.com/in/nora-alhuwaidi-2a89841b3/" target="_blank" 
                       style="display: flex; align-items: center; gap: 0.4rem; text-decoration: none; color: #cbd5e1; transition: color 0.3s;">
                        <svg width="16" height="16" viewBox="0 0 24 24" fill="#0A66C2">
                            <path d="M20.447 20.452h-3.554v-5.569c0-1.328-.027-3.037-1.852-3.037-1.853 0-2.136 1.445-2.136 2.939v5.667H9.351V9h3.414v1.561h.046c.477-.9 1.637-1.85 3.37-1.85 3.601 0 4.267 2.37 4.267 5.455v6.286zM5.337 7.433c-1.144 0-2.063-.926-2.063-2.065 0-1.138.92-2.063 2.063-2.063 1.14 0 2.064.925 2.064 2.063 0 1.139-.925 2.065-2.064 2.065zm1.782 13.019H3.555V9h3.564v11.452zM22.225 0H1.771C.792 0 0 .774 0 1.729v20.542C0 23.227.792 24 1.771 24h20.451C23.2 24 24 23.227 24 22.271V1.729C24 .774 23.2 0 22.222 0h.003z"/>
                        </svg>
                        <span>Nora Alhuwaidi</span>
                    </a>
                </div>
            </div>
            <p style="margin-top: 0.8rem;">
                {t('footer_powered', lang)} <strong>{t('footer_chat', lang)}</strong>
            </p>
        </div>
        """
        st.markdown(footer_html, unsafe_allow_html=True)

    
    # ------------------------------------------------------------------------
    # TIME UTILITIES
    # ------------------------------------------------------------------------
    @staticmethod
    def _get_current_time() -> float:
        """Get current timestamp in Riyadh timezone"""
        return datetime.now(RIYADH_TZ).timestamp()
