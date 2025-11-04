"""
Sidebar Interface Module
Handles sidebar display with stats, examples, and settings
"""

import streamlit as st
from utils.translations import t
from utils.state import save_chat_memory
from datetime import datetime
import pytz


class SidebarInterface:
    """Manages sidebar display and interactions"""
    
    def __init__(self, db_manager):
        """Initialize with database manager"""
        self.db = db_manager
    
    def render(self):
        """Render complete sidebar"""
        with st.sidebar:
            self._render_header()
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
    
    def _render_header(self):
        """Render sidebar header"""
        lang = st.session_state.language
        st.markdown(
            f"<h2 style='text-align: center; color: white; margin-bottom: 0;'>{t('assistant_title', lang)}</h2>",
            unsafe_allow_html=True
        )
        st.markdown(
            f"<p style='text-align: center; color: rgba(255,255,255,0.7); font-size: 0.9rem;'>{t('assistant_subtitle', lang)}</p>",
            unsafe_allow_html=True
        )
    
    def _render_language_selector(self):
        """Render language toggle"""
        lang = st.session_state.language
        st.markdown(f"<h3>{t('language_title', lang)}</h3>", unsafe_allow_html=True)
        
        language_choice = st.radio(
            "",
            ["English 🇬🇧", "العربية 🇸🇦"],
            index=0 if lang == "English" else 1,
            horizontal=True,
            label_visibility="collapsed",
            key="lang_radio"
        )
        
        # Handle language change
        new_language = "العربية" if "العربية" in language_choice else "English"
        if new_language != st.session_state.language:
            st.session_state.language = new_language
            
            # Reset chat with welcome message in new language
            if len(st.session_state.chat_memory) <= 1:
                st.session_state.chat_memory = [{
                    "role": "assistant",
                    "content": t("welcome_msg", new_language),
                    "timestamp": self._get_current_time()
                }]
                save_chat_memory()
            
            st.rerun()
    
    def _render_stats(self):
        """Render database statistics"""
        lang = st.session_state.language
        st.markdown(f"<h3>{t('stats_title', lang)}</h3>", unsafe_allow_html=True)
        
        stats = self.db.get_stats()
        
        stat_items = [
            ("total", "total_agencies", "🏢"),
            ("authorized", "authorized", "✅"),
            ("countries", "countries", "🌍"),
            ("cities", "cities", "🏙️")
        ]
        
        for key, label_key, icon in stat_items:
            html_card = f"""
            <div class="stat-card">
                <div style="font-size: 1.5rem; margin-bottom: 0.5rem;">{icon}</div>
                <div class="stat-number">{stats.get(key, 0):,}</div>
                <div class="stat-label">{t(label_key, lang)}</div>
            </div>
            """
            st.markdown(html_card, unsafe_allow_html=True)
    
    def _render_examples(self):
        """Render example questions"""
        lang = st.session_state.language
        st.markdown(f"<h3>{t('examples_title', lang)}</h3>", unsafe_allow_html=True)
        
        example_questions = [
            ("ex_all_auth", "ex_all_auth_q"),
            ("ex_saudi", "ex_saudi_q"),
            ("ex_by_country", "ex_by_country_q"),
            ("ex_emails", "ex_emails_q"),
        ]
        
        for i, (display_key, question_key) in enumerate(example_questions):
            if st.button(
                t(display_key, lang),
                key=f"example_{i}",
                use_container_width=True
            ):
                # Store the example in session state
                st.session_state.selected_question = t(question_key, lang)
                
                # Optionally trigger auto-submit
                st.session_state.submit_example = True
                
                st.rerun()

    def _render_clear_button(self):
        """Render clear chat button"""
        lang = st.session_state.language
        
        if st.button(
            t("clear_chat", lang),
            use_container_width=True,
            type="primary"
        ):
            st.session_state.chat_memory = [{
                "role": "assistant",
                "content": t("welcome_msg", lang),
                "timestamp": self._get_current_time()
            }]
            st.session_state.last_result_df = None
            save_chat_memory()
            st.rerun()
    

    # ...existing code...
   # ...existing code...
    def _render_features(self):
        """
        Render features section in Streamlit.
        `t` is the translation function: t(key, lang)
        """
        lang = st.session_state.get("language", "English")
        st.markdown(f"<h3>{t('features_title', lang)}</h3>", unsafe_allow_html=True)

        features = [
            ("feat_ai", "feat_ai_desc", "✨"),
            ("feat_multilingual", "feat_multilingual_desc", "🌍"),
            ("feat_viz", "feat_viz_desc", "📊"),
            ("feat_secure", "feat_secure_desc", "🔒")
        ]

        # Build HTML without leading indentation so Markdown doesn't treat it as a code block
        features_html = ""
        for icon_key, desc_key, emoji in features:
            features_html += (
                f'<div style="display:flex;align-items:flex-start;margin-bottom:10px;">'
                f'<div style="font-size:1.5rem;margin-right:10px;">{emoji}</div>'
                f'<div><strong>{t(icon_key, lang)}</strong><br/>'
                f'<span style="color:rgba(255,255,255,0.8);font-size:0.9rem;">{t(desc_key, lang)}</span>'
                f'</div></div>'
            )

        st.markdown(
            f'<div style="color: rgba(255,255,255,0.9); font-size: 0.9rem; line-height: 1.8;">{features_html}</div>',
            unsafe_allow_html=True
        )
# ...existing code...
# ...existing code...
    
    @staticmethod
    def _get_current_time() -> float:
        """Get current timestamp"""
        riyadh_tz = pytz.timezone('Asia/Riyadh')
        return datetime.now(riyadh_tz).timestamp()
