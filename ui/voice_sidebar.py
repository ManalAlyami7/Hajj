"""
Sidebar Component Module
Handles sidebar rendering with language selection, accessibility, and navigation
"""
import time
import streamlit as st
from utils.translations import t


def render_sidebar(memory, language_code: str):
    """Render the complete sidebar with all controls"""
    with st.sidebar:
        # -----------------------------
        # Header Section
        # -----------------------------
        st.markdown(f"""
        <div style="text-align: center; padding: 1.5rem 0 2rem 0;">
            <div style="font-size: 3rem; margin-bottom: 0.75rem;">🕋</div>
            <h2 style="margin: 0; font-size: 1.7rem; font-weight: 700; 
                       background: linear-gradient(135deg, #60a5fa 0%, #a78bfa 100%);
                       -webkit-background-clip: text; -webkit-text-fill-color: transparent;">
                {t('assistant_title', language_code).replace('🕋 ', '')}
            </h2>
            <p style="color: #94a3b8; font-size: 0.9rem; margin-top: 0.25rem;">
                {t('assistant_subtitle', language_code)}
            </p>
        </div>
        """, unsafe_allow_html=True)

        st.markdown("<hr style='margin-top:-0.5rem; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

        # Language Selection
        _render_language_section(language_code)
        st.markdown("<hr style='margin-top:1rem; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

        # Accessibility
        _render_accessibility_section(language_code)
        st.markdown("<hr style='margin-top:1rem; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

        # Memory
        _render_memory_section(memory, language_code)
        st.markdown("<hr style='margin-top:1rem; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

        # Sample Questions
        _render_sample_questions(language_code)
        st.markdown("<hr style='margin-top:1rem; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

        # Navigation
        _render_navigation(language_code)


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

    current_lang_display = [k for k, v in language_options.items() if v == language_code][0]
    selected_language = st.selectbox(
        t('language_title', language_code),
        options=list(language_options.keys()),
        index=list(language_options.keys()).index(current_lang_display),
        label_visibility="collapsed"
    )

    if language_options[selected_language] != language_code:
        st.session_state.language = language_options[selected_language]
        st.toast(f"{t('language_switched', language_code, lang=selected_language)} 🌐")
        st.rerun()


# -----------------------------
# ACCESSIBILITY SECTION
# -----------------------------
def _render_accessibility_section(language_code: str):
    st.markdown(f"### {t('accessibility_title', language_code)}")
    st.caption(t('accessibility_desc', language_code))

    font_labels = [t('font_normal', language_code), t('font_large', language_code), t('font_extra_large', language_code)]
    font_values = ['normal', 'large', 'extra-large']
    current_index = font_values.index(st.session_state.font_size)

    selected_font = st.selectbox(
        t('font_size_label', language_code),
        options=font_labels,
        index=current_index
    )

    selected_index = font_labels.index(selected_font)
    if font_values[selected_index] != st.session_state.font_size:
        st.session_state.font_size = font_values[selected_index]
        st.toast(f"{t('font_size_updated', language_code, size=selected_font)} 🔠")
        st.rerun()

    st.markdown("")

    high_contrast = st.checkbox(
        t('contrast_label', language_code),
        value=st.session_state.high_contrast,
        help=t('contrast_help', language_code)
    )

    if high_contrast != st.session_state.high_contrast:
        st.session_state.high_contrast = high_contrast
        st.toast(t('contrast_updated', language_code), icon="🌓")
        st.rerun()


# -----------------------------
# MEMORY SECTION
# -----------------------------
def _render_memory_section(memory, language_code: str):
    st.markdown(f"### {t('memory_status_title', language_code)}")
    st.caption(t('memory_status_desc', language_code))

    memory_summary = memory.get_memory_summary()
    st.markdown(f"""
    <div style="background: rgba(96,165,250,0.1); padding: 1rem; border-radius: 0.75rem; 
                border-left: 4px solid #60a5fa; margin-top: 0.5rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="color: #64748b; font-size: 0.85rem;">{t('voice_memory_messages', language_code)}</span>
            <strong style="color: #1e293b;">{memory_summary['total_messages']}</strong>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="color: #64748b; font-size: 0.85rem;">{t('voice_session_duration', language_code)}</span>
            <strong style="color: #1e293b;">{memory_summary['session_duration']}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    if st.button(f"🗑️ {t('voice_clear_memory', language_code)}", use_container_width=True, type="secondary"):
        memory.clear_memory()
        for key in ['current_transcript', 'current_response', 'current_metadata',
                    'last_audio_hash', 'pending_audio', 'pending_audio_bytes']:
            st.session_state[key] = None if 'audio' in key else ""
        st.success(t('memory_cleared', language_code))
        time.sleep(1)
        st.rerun()


# -----------------------------
# SAMPLE QUESTIONS
# -----------------------------
def _render_sample_questions(language_code: str):
    st.markdown(f"### {t('examples_title', language_code)}")
    st.caption(t('examples_caption', language_code))

    for question in t('sample_questions', language_code):
        st.markdown(f"""
        <div style="background: rgba(255,255,255,0.05); padding: 0.6rem 0.9rem; 
                    border-radius: 0.6rem; margin-bottom: 0.6rem; font-size: 0.9rem;
                    border: 1px solid rgba(255,255,255,0.08); color: #cbd5e1; 
                    transition: all 0.3s ease;">
            💬 {question}
        </div>
        """, unsafe_allow_html=True)


# -----------------------------
# NAVIGATION SECTION
# -----------------------------
def _render_navigation(language_code: str):
    st.markdown(f"### {t('nav_title', language_code)}")
    st.caption(t('nav_caption', language_code))

    back_label = t('voice_return_button', language_code)
    arrow = "←" if language_code == "en" else "→"

    if st.button(f"{arrow} {back_label}", use_container_width=True, type="primary"):
        st.switch_page("./app.py")
