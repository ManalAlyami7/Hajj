"""
Sidebar Component Module
Handles sidebar rendering with language selection, accessibility, and navigation
"""
import time
import streamlit as st
from utils.translations import t


def render_sidebar(memory, language_code: str):
    """
    Render the complete sidebar with all controls
    
    Args:
        memory: ConversationMemory instance
        language_code: Current language code
    """
    
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

        # -----------------------------
        # Language Selection
        # -----------------------------
        _render_language_section(language_code)
        
        st.markdown("<hr style='margin-top:1rem; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

        # -----------------------------
        # Accessibility Options
        # -----------------------------
        _render_accessibility_section(language_code)
        
        st.markdown("<hr style='margin-top:1rem; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

        # -----------------------------
        # Memory Status Section
        # -----------------------------
        _render_memory_section(memory, language_code)
        
        st.markdown("<hr style='margin-top:1rem; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

        # -----------------------------
        # Sample Questions
        # -----------------------------
        _render_sample_questions(language_code)
        
        st.markdown("<hr style='margin-top:1rem; border-color:rgba(255,255,255,0.1);'>", unsafe_allow_html=True)

        # -----------------------------
        # Navigation
        # -----------------------------
        _render_navigation(language_code)


def _render_language_section(language_code: str):
    """Render language selection section"""
    st.markdown(f"### {t('language_title', language_code)}")
    st.caption(t('feat_multilingual_desc', language_code))
    
    language_options = {
        'English': 'en',
        'العربية': 'ar',
        'اردو': 'ur'
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
        st.toast(f"{t('language_title', language_code)}: {selected_language}", icon="🌐")
        st.rerun()


def _render_accessibility_section(language_code: str):
    """Render accessibility controls section"""
    # Accessibility title mapping
    accessibility_key = {
        'en': '♿ Accessibility',
        'ar': '♿ إمكانية الوصول',
        'ur': '♿ رسائی'
    }
    st.markdown(f"### {accessibility_key.get(language_code, accessibility_key['en'])}")
    
    # Use translation for caption
    accessibility_help = {
        'en': 'Adjust font size or contrast for better visibility and comfort.',
        'ar': 'اضبط حجم الخط أو التباين لرؤية وراحة أفضل.',
        'ur': 'بہتر مرئیت اور آرام کے لیے فونٹ سائز یا کنٹراسٹ کو ایڈجسٹ کریں۔'
    }
    st.caption(accessibility_help.get(language_code, accessibility_help['en']))

    # Font Size - Simple labels
    font_size_labels = {
        'en': ['Normal', 'Large', 'Extra Large'],
        'ar': ['عادي', 'كبير', 'كبير جداً'],
        'ur': ['عام', 'بڑا', 'بہت بڑا']
    }
    
    font_values = ['normal', 'large', 'extra-large']
    current_labels = font_size_labels.get(language_code, font_size_labels['en'])
    
    # Find current index
    current_index = font_values.index(st.session_state.font_size)
    
    font_size_title = {
        'en': 'Font Size',
        'ar': 'حجم الخط',
        'ur': 'فونٹ کا سائز'
    }
    
    selected_font = st.selectbox(
        font_size_title.get(language_code, 'Font Size'),
        options=current_labels,
        index=current_index
    )

    # Map back to value
    selected_index = current_labels.index(selected_font)
    if font_values[selected_index] != st.session_state.font_size:
        st.session_state.font_size = font_values[selected_index]
        st.toast(f"{font_size_title.get(language_code, 'Font Size')}: {selected_font}", icon="🔠")
        st.rerun()

    # High Contrast Mode
    st.markdown("")
    
    high_contrast_labels = {
        'en': 'Enable High Contrast Mode',
        'ar': 'تفعيل وضع التباين العالي',
        'ur': 'ہائی کنٹراسٹ موڈ فعال کریں'
    }
    
    high_contrast_help = {
        'en': 'Improves text and button visibility for users with low vision.',
        'ar': 'يحسن وضوح النص والأزرار للمستخدمين ذوي الرؤية المنخفضة.',
        'ur': 'کم بینائی والے صارفین کے لیے متن اور بٹن کی مرئیت کو بہتر بناتا ہے۔'
    }
    
    high_contrast = st.checkbox(
        high_contrast_labels.get(language_code, high_contrast_labels['en']),
        value=st.session_state.high_contrast,
        help=high_contrast_help.get(language_code, high_contrast_help['en'])
    )

    if high_contrast != st.session_state.high_contrast:
        st.session_state.high_contrast = high_contrast
        contrast_status = {
            'en': 'High contrast mode updated',
            'ar': 'تم تحديث وضع التباين العالي',
            'ur': 'ہائی کنٹراسٹ موڈ اپ ڈیٹ ہو گیا'
        }
        st.toast(contrast_status.get(language_code, contrast_status['en']), icon="🌓")
        st.rerun()


def _render_memory_section(memory, language_code: str):
    """Render memory status section"""
    memory_title = {
        'en': '🧠 Memory Status',
        'ar': '🧠 حالة الذاكرة',
        'ur': '🧠 میموری کی حیثیت'
    }
    st.markdown(f"### {memory_title.get(language_code, memory_title['en'])}")
    
    memory_caption = {
        'en': "Review your current session's progress.",
        'ar': 'راجع تقدم جلستك الحالية.',
        'ur': 'اپنے موجودہ سیشن کا جائزہ لیں۔'
    }
    st.caption(memory_caption.get(language_code, memory_caption['en']))
    
    memory_summary = memory.get_memory_summary()
    
    messages_label = t('voice_memory_messages', language_code)
    duration_label = t('voice_session_duration', language_code)
    
    st.markdown(f"""
    <div style="background: rgba(96, 165, 250, 0.1); padding: 1rem; border-radius: 0.75rem; 
                border-left: 4px solid #60a5fa; margin-top: 0.5rem;">
        <div style="display: flex; justify-content: space-between; margin-bottom: 0.5rem;">
            <span style="color: #64748b; font-size: 0.85rem; text-transform: capitalize;">{messages_label}</span>
            <strong style="color: #1e293b;">{memory_summary['total_messages']}</strong>
        </div>
        <div style="display: flex; justify-content: space-between;">
            <span style="color: #64748b; font-size: 0.85rem; text-transform: capitalize;">{duration_label}</span>
            <strong style="color: #1e293b;">{memory_summary['session_duration']}</strong>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("")
    
    clear_label = t('voice_clear_memory', language_code)
    
    if st.button(f"🗑️ {clear_label}", use_container_width=True, type="secondary"):
        memory.clear_memory()
        st.session_state.current_transcript = ""
        st.session_state.current_response = ""
        st.session_state.current_metadata = {}
        st.session_state.last_audio_hash = None
        st.session_state.pending_audio = None
        st.session_state.pending_audio_bytes = None
        
        success_msg = {
            'en': 'Memory cleared successfully!',
            'ar': 'تم مسح الذاكرة بنجاح!',
            'ur': 'میموری کامیابی سے صاف ہو گئی!'
        }
        st.success(success_msg.get(language_code, success_msg['en']))
        time.sleep(1)
        st.rerun()


def _render_sample_questions(language_code: str):
    """Render sample questions section"""
    sample_title = t('examples_title', language_code)
    st.markdown(f"### {sample_title}")
    
    sample_caption = {
        'en': 'Try one of these to get started quickly:',
        'ar': 'جرب أحد هذه للبدء بسرعة:',
        'ur': 'جلدی شروع کرنے کے لیے ان میں سے ایک کو آزمائیں:'
    }
    st.caption(sample_caption.get(language_code, sample_caption['en']))

    sample_questions = {
        'en': [
            "What are the Hajj requirements?",
            "Find affordable packages",
            "When should I book?",
            "Tell me about Mina"
        ],
        'ar': [
            "ما هي متطلبات الحج؟",
            "ابحث عن باقات ميسورة",
            "متى يجب أن أحجز؟",
            "أخبرني عن منى"
        ],
        'ur': [
            "حج کے تقاضے کیا ہیں؟",
            "سستے پیکجز تلاش کریں",
            "مجھے کب بک کرنا چاہیے؟",
            "منیٰ کے بارے میں بتائیں"
        ]
    }

    current_samples = sample_questions.get(language_code, sample_questions['en'])

    for question in current_samples:
        st.markdown(f"""
        <div style="background: rgba(255, 255, 255, 0.05); padding: 0.6rem 0.9rem; 
                    border-radius: 0.6rem; margin-bottom: 0.6rem; font-size: 0.9rem;
                    border: 1px solid rgba(255, 255, 255, 0.08); color: #cbd5e1; 
                    transition: all 0.3s ease;">
            💬 {question}
        </div>
        """, unsafe_allow_html=True)


def _render_navigation(language_code: str):
    """Render navigation section"""
    nav_title = {
        'en': '🏠 Navigation',
        'ar': '🏠 التنقل',
        'ur': '🏠 نیویگیشن'
    }
    st.markdown(f"### {nav_title.get(language_code, nav_title['en'])}")
    
    nav_caption = {
        'en': 'Return to the main chat interface.',
        'ar': 'العودة إلى واجهة الدردشة الرئيسية.',
        'ur': 'مین چیٹ انٹرفیس پر واپس جائیں۔'
    }
    st.caption(nav_caption.get(language_code, nav_caption['en']))

    back_label = t('voice_return_button', language_code)
    
    if st.button(f"← {back_label}" if language_code == 'en' else f"→ {back_label}", 
                 use_container_width=True, type="primary"):
        st.switch_page("./app.py")