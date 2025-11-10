"""
Professional Sidebar Interface Module
Enhanced with formal design, statistics, and navigation
Fixed color scheme with proper contrast
Complete version with Urdu language support and all translations working
"""

import streamlit as st
from utils.translations import t
from utils.state import save_chat_memory, clear_chat_memory
from datetime import datetime
import pytz


class SidebarInterface:
    """Manages professional sidebar display and interactions"""
    
    def __init__(self, db_manager):
        """Initialize with database manager"""
        self.db = db_manager
    
    def render(self):
        """Render complete professional sidebar"""
        with st.sidebar:
            self._inject_sidebar_styles()
            self._render_header()
            st.markdown("---")
            
            self._render_navigation_buttons()
            st.markdown("---")
            
            self._render_language_selector()
            st.markdown("---")
            
            self._render_stats()
            st.markdown("---")
            
            self._render_examples()
            st.markdown("---")
            
            self._render_clear_button()
            st.markdown("---")
            
            self._render_features()
            st.markdown("---")
            
            self._render_footer()
    
    def _inject_sidebar_styles(self):
        """Inject professional sidebar CSS with fixed colors"""
        st.markdown("""
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
        
        [data-testid="stSidebar"] button[kind="secondary"] {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            border: 2px solid #dc2626;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
        }
        
        [data-testid="stSidebar"] button[kind="secondary"]:hover {
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
            border-color: #b91c1c;
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
        """, unsafe_allow_html=True)
    
    def _render_header(self):
        """Render professional sidebar header"""
        lang = st.session_state.language
        st.markdown(f"""
        <div class="sidebar-header">
            <span class="sidebar-icon">🕋</span>
            <h2 class="sidebar-title">{t('assistant_title', lang).replace('🕋 ', '')}</h2>
            <p class="sidebar-subtitle">{t('assistant_subtitle', lang)}</p>
        </div>
        """, unsafe_allow_html=True)
    
    def _render_navigation_buttons(self):
        """Render professional navigation buttons"""
        lang = st.session_state.language
        
        # إضافة النص المترجم للعنوان
        mode_title = t('mode_title', lang)
        st.markdown(f"<h3>{mode_title}</h3>", unsafe_allow_html=True)
        
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
    
    def _render_language_selector(self):
        """Render professional language toggle"""
        lang = st.session_state.language
        
        # إضافة النص المترجم للعنوان
        language_title = t('language_title', lang)
        st.markdown(f"<h3>{language_title}</h3>", unsafe_allow_html=True)
        
        # إضافة الأردية للخيارات
        language_choice = st.radio(
            "",
            ["English 🇬🇧", "العربية 🇸🇦", "اردو 🇵🇰"],
            index=0 if lang == "English" else (1 if lang == "العربية" else 2),
            horizontal=True,
            label_visibility="collapsed",
            key="chatbot_lang_selector"
        )
        
        # تحديد اللغة الجديدة
        if "اردو" in language_choice:
            new_language = "اردو"
        elif "العربية" in language_choice:
            new_language = "العربية"
        else:
            new_language = "English"
        
        if new_language != st.session_state.language:
            st.session_state.language = new_language
            
            if len(st.session_state.chat_memory) <= 1:
                st.session_state.chat_memory = [{
                    "role": "assistant",
                    "content": t("welcome_msg", new_language),
                    "timestamp": self._get_current_time()
                }]
                save_chat_memory()
            
            st.rerun()
    
    def _render_stats(self):
        """Render professional database statistics"""
        lang = st.session_state.language
        
        # إضافة النص المترجم للعنوان
        stats_title = t('stats_title', lang)
        st.markdown(f"<h3>{stats_title}</h3>", unsafe_allow_html=True)
        
        stats = self.db.get_stats()
        
        stat_items = [
            ("total", "total_agencies", "🏢"),
            ("authorized", "authorized", "✅"),
            ("countries", "countries", "🌍"),
            ("cities", "cities", "🏙️")
        ]
        
        for key, label_key, icon in stat_items:
            st.markdown(f"""
            <div class="stat-card">
                <div style="font-size: 2.5rem;">{icon}</div>
                <div class="stat-number">{stats.get(key, 0):,}</div>
                <div class="stat-label">{t(label_key, lang)}</div>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_examples(self):
        """Render professional example questions"""
        lang = st.session_state.language
        
        # إضافة النص المترجم للعنوان
        examples_title = t('examples_title', lang)
        st.markdown(f"<h3>{examples_title}</h3>", unsafe_allow_html=True)
        
        example_questions = [
            ("ex_all_auth", "ex_all_auth_q"),
            ("ex_saudi", "ex_saudi_q"),
            ("ex_by_country", "ex_by_country_q"),
            ("ex_emails", "ex_emails_q"),
        ]
        
        for i, (display_key, question_key) in enumerate(example_questions):
            if st.button(
                f"📝 {t(display_key, lang)}",
                key=f"example_{i}",
                use_container_width=True
            ):
                question_text = t(question_key, lang)
                st.session_state.chat_memory.append({
                    "role": "user",
                    "content": question_text,
                    "timestamp": self._get_current_time()
                })
                
                st.session_state.pending_example = True
                #save_chat_memory()
                st.rerun()
    
    def _render_clear_button(self):
        """Render professional clear chat button"""
        lang = st.session_state.language
        
        if st.button(
            f"🗑️ {t('clear_chat', lang)}",
            use_container_width=True,
            type="secondary"
        ):
            st.session_state.chat_memory = [{
                "role": "assistant",
                "content": t("welcome_msg", lang),
                "timestamp": self._get_current_time()
            }]
            st.session_state.last_result_df = None
            st.session_state.pending_example = False
            clear_chat_memory()
            st.rerun()
    
    def _render_features(self):
        """Render professional features section"""
        lang = st.session_state.get("language", "English")
        
        # إضافة النص المترجم للعنوان
        features_title = t('features_title', lang)
        st.markdown(f"<h3>{features_title}</h3>", unsafe_allow_html=True)

        features = [
            ("feat_ai", "feat_ai_desc", "🤖"),
            ("feat_multilingual", "feat_multilingual_desc", "🌐"),
            ("feat_viz", "feat_viz_desc", "📈"),
            ("feat_secure", "feat_secure_desc", "🔐")
        ]

        for icon_key, desc_key, emoji in features:
            st.markdown(f"""
            <div class="feature-item">
                <div class="feature-icon">{emoji}</div>
                <div class="feature-content">
                    <div class="feature-title">{t(icon_key, lang)}</div>
                    <div class="feature-desc">{t(desc_key, lang)}</div>
                </div>
            </div>
            """, unsafe_allow_html=True)
    
    def _render_footer(self):
        """Render professional footer"""
        lang = st.session_state.get("language", "English")
        year = datetime.now().year
        
        st.markdown(f"""
        <div class="sidebar-footer">
            <p>© {year} {t('assistant_title', lang).replace('🕋 ', '')}</p>
            <p style="margin-top: 0.5rem;">
                {t('footer_powered', lang)} <strong>{t('footer_chat', lang)}</strong>
            </p>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def _get_current_time() -> float:
        """Get current timestamp"""
        riyadh_tz = pytz.timezone('Asia/Riyadh')
        return datetime.now(riyadh_tz).timestamp()