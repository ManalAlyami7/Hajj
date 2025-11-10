"""
Professional Chat Interface Module
Enhanced with formal design, improved UX, and consistent branding
Fixed color scheme with proper contrast and visibility
Fixed timestamp and buttons appearing on first render
"""

import streamlit as st
import pandas as pd
from datetime import datetime
import pytz
import base64
from utils.translations import t
from utils.state import save_chat_memory
from utils.validators import validate_user_input
import uuid
import streamlit.components.v1 as components
import re

class ChatInterface:
    """Manages professional chat interface and message display"""

    def __init__(self, chat_graph, llm_manager):
        self.graph = chat_graph
        self.llm = llm_manager
        if "chat_memory" not in st.session_state:
            st.session_state.chat_memory = []
        if "pending_example" not in st.session_state:
            st.session_state.pending_example = False
        if "processing_example" not in st.session_state:
            st.session_state.processing_example = False
        if "audio_playing" not in st.session_state:
            st.session_state.audio_playing = {}

    # -------------------
    # Public Render Method
    # -------------------
    def render(self):
        """Render professional chat interface"""
        self._inject_professional_styles()
        self._display_chat_history()
        
        # if self._show_quick_actions():
        #     self._display_quick_actions()
        
        self._handle_user_input()

    # -------------------
    # Professional Styling
    # -------------------
    def _inject_professional_styles(self):
        """Inject enhanced professional CSS styles with fixed colors"""
        st.markdown("""
        <style>
        /* Professional Color Palette */
        :root {
            --primary-gold: #d4af37;
            --primary-gold-light: #f4e5b5;
            --primary-gold-dark: #b8941f;
            --primary-dark: #1a1f2e;
            --secondary-dark: #0f1419;
            --accent-blue: #4a9eff;
            --success-green: #22c55e;
            --error-red: #ef4444;
            --warning-orange: #f97316;
            --text-dark: #1f2937;
            --text-light: #f8fafc;
            --text-muted: #64748b;
            --border-light: #e2e8f0;
            --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.08);
            --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.12);
            --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.16);
        }

        /* Main Background */
        .main {
            background: linear-gradient(135deg, #f8fafc 0%, #e2e8f0 100%);
        }

        /* Chat Container Styling */
        .stChatMessage {
            background: white;
            border-radius: 16px;
            padding: 1.5rem;
            margin-bottom: 1.5rem;
            border: 2px solid var(--border-light);
            box-shadow: var(--shadow-sm);
            transition: all 0.3s ease;
        }

        .stChatMessage:hover {
            box-shadow: var(--shadow-md);
            border-color: var(--primary-gold);
            transform: translateY(-2px);
        }

        /* User Message Styling */
        .stChatMessage[data-testid*="user"] {
            background: linear-gradient(135deg, #dbeafe 0%, #bfdbfe 100%);
            border-left: 5px solid var(--accent-blue);
        }

        /* Assistant Message Styling */
        .stChatMessage[data-testid*="assistant"] {
            background: linear-gradient(135deg, #fef9e7 0%, #fdf4d8 100%);
            border-left: 5px solid var(--primary-gold);
        }

        /* Chat Message Text */
        .stChatMessage p, .stChatMessage span, .stChatMessage div {
            color: var(--text-dark) !important;
            line-height: 1.7;
        }

        /* Chat Input Styling */
        .stChatInputContainer {
            border-top: 3px solid var(--primary-gold);
            background: white;
            padding: 1.5rem 0;
            box-shadow: 0 -4px 12px rgba(0, 0, 0, 0.05);
        }

        .stChatInput > div {
            border-radius: 24px;
            border: 2px solid var(--primary-gold);
            box-shadow: var(--shadow-sm);
            transition: all 0.3s ease;
            background: white;
        }

        .stChatInput > div:focus-within {
            border-color: var(--primary-gold-dark);
            box-shadow: 0 0 0 4px rgba(212, 175, 55, 0.15);
            transform: scale(1.01);
        }

        .stChatInput input {
            color: var(--text-dark) !important;
            font-size: 1rem !important;
        }

        .stChatInput input::placeholder {
            color: var(--text-muted) !important;
        }

        /* Quick Actions Styling */
        .quick-actions-container {
            background: linear-gradient(135deg, #ffffff 0%, #f8fafc 100%);
            padding: 2rem;
            border-radius: 20px;
            border: 3px solid var(--primary-gold);
            box-shadow: var(--shadow-md);
            margin: 2rem 0;
        }

        .quick-actions-header {
            text-align: center;
            margin-bottom: 1.5rem;
        }

        .quick-actions-header h3 {
            color: var(--primary-dark);
            font-size: 1.8rem;
            font-weight: 800;
            margin: 0 0 0.5rem 0;
            letter-spacing: -0.025em;
        }

        .quick-actions-header p {
            color: var(--text-muted);
            font-size: 1rem;
            margin: 0;
            font-weight: 500;
        }

        /* Professional Button Styling */
        .stButton > button {
            width: 100% !important;
            padding: 1.1rem 1.5rem !important;
            border-radius: 14px !important;
            font-weight: 700 !important;
            font-size: 1rem !important;
            cursor: pointer !important;
            border: 2px solid var(--primary-gold) !important;
            background: linear-gradient(135deg, var(--primary-gold) 0%, var(--primary-gold-dark) 100%) !important;
            color: white !important;
            box-shadow: var(--shadow-sm) !important;
            transition: all 0.3s cubic-bezier(0.4, 0, 0.2, 1) !important;
            letter-spacing: 0.025em !important;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.2);
        }

        .stButton > button:hover {
            transform: translateY(-3px);
            box-shadow: var(--shadow-lg) !important;
            background: linear-gradient(135deg, var(--primary-gold-dark) 0%, #9d7a1a 100%) !important;
            border-color: var(--primary-gold-dark) !important;
        }

        .stButton > button:active {
            transform: translateY(-1px);
        }

        /* Remove column gaps */
        div[data-testid="column"] {
            padding: 0 2px !important;
        }

        /* Small Action Buttons for Audio Controls */
        .stChatMessage div[data-testid="column"] > div > div > button {
            padding: 0.5rem 0.6rem !important;
            font-size: 1.1rem !important;
            border-radius: 8px !important;
            min-height: 38px !important;
            max-height: 38px !important;
            margin: 0 !important;
        }

        /* Timestamp Styling */
        .message-timestamp {
            color: var(--text-muted);
            font-size: 0.85rem;
            margin-top: 0.75rem;
            font-weight: 600;
            display: flex;
            align-items: center;
            gap: 6px;
        }

        /* Toast Notification */
        .toast-notification {
            position: fixed;
            bottom: 30px;
            left: 50%;
            transform: translateX(-50%);
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
            color: white;
            padding: 16px 28px;
            border-radius: 16px;
            border: 2px solid white;
            z-index: 9999;
            font-size: 1rem;
            font-weight: 700;
            box-shadow: var(--shadow-lg);
            animation: slideUp 0.3s ease, fadeOut 0.3s ease 2.7s;
        }

        @keyframes slideUp {
            from {
                bottom: -50px;
                opacity: 0;
            }
            to {
                bottom: 30px;
                opacity: 1;
            }
        }

        @keyframes fadeOut {
            to {
                opacity: 0;
                bottom: -50px;
            }
        }

        /* Results Card Styling */
        .results-card {
            padding: 2rem;
            margin: 1.5rem 0;
            border-radius: 16px;
            background: white;
            border: 2px solid var(--border-light);
            box-shadow: var(--shadow-md);
            transition: all 0.3s ease;
        }

        .results-card:hover {
            box-shadow: var(--shadow-lg);
            transform: translateY(-2px);
        }

        .results-card.authorized {
            border-left: 6px solid var(--success-green);
            background: linear-gradient(135deg, #f0fdf4 0%, #dcfce7 100%);
        }

        .results-card.unauthorized {
            border-left: 6px solid var(--error-red);
            background: linear-gradient(135deg, #fef2f2 0%, #fee2e2 100%);
        }

        .results-card-header {
            display: flex;
            justify-content: space-between;
            align-items: start;
            margin-bottom: 1.2rem;
        }

        .results-card-title {
            color: var(--text-dark);
            font-size: 1.25rem;
            font-weight: 800;
            line-height: 1.4;
        }

        .status-badge {
            padding: 8px 18px;
            border-radius: 24px;
            font-size: 0.9rem;
            font-weight: 700;
            white-space: nowrap;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }

        .status-badge.authorized {
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
            color: white;
            border: 2px solid #15803d;
        }

        .status-badge.unauthorized {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            border: 2px solid #b91c1c;
        }

        .results-card-content {
            color: var(--text-dark);
            line-height: 1.8;
            font-size: 1rem;
        }

        .results-card-content strong {
            color: var(--primary-dark);
            font-weight: 700;
        }

        /* Loading Spinner */
        .stSpinner > div {
            border-color: var(--primary-gold) !important;
        }

        /* Error/Success Messages */
        .stAlert {
            border-radius: 12px;
            border-width: 2px;
            font-weight: 600;
        }

        /* Scrollbar Styling */
        ::-webkit-scrollbar {
            width: 12px;
        }

        ::-webkit-scrollbar-track {
            background: #e2e8f0;
            border-radius: 6px;
        }

        ::-webkit-scrollbar-thumb {
            background: linear-gradient(180deg, var(--primary-gold) 0%, var(--primary-gold-dark) 100%);
            border-radius: 6px;
        }

        ::-webkit-scrollbar-thumb:hover {
            background: linear-gradient(180deg, var(--primary-gold-dark) 0%, #9d7a1a 100%);
        }
        </style>
        """, unsafe_allow_html=True)

    # -------------------
    # Quick Actions
    # -------------------
    def _show_quick_actions(self) -> bool:
        chat = st.session_state.chat_memory
        lang = st.session_state.get("language", "English")
        if len(chat) == 1:
            first = chat[0]
            return first.get("role") == "assistant" and first.get("content") == t("welcome_msg", lang)
        return False

    def _display_quick_actions(self):
        """Display professional quick action buttons"""
        lang = st.session_state.get("language", "English")
        
        st.markdown(f"""
            <div class='quick-actions-container'>
                <div class='quick-actions-header'>
                    <h3>✨ {t('quick_actions', lang)}</h3>
                    <p>Select a quick action to get started instantly</p>
                </div>
            </div>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        actions = [
            ("🔍", t("find_authorized", lang), "find_authorized", "user", t("show_authorized", lang)),
            ("📊", t("show_stats", lang), "show_stats", "user", t("hajj_statistics", lang)),
            ("🌍", t("find_by_country", lang), "find_by_country", "user", t("country_search", lang)),
            ("❓", t("general_help", lang), "general_help", "user", t("help_message", lang)),
        ]

        with col1:
            for icon, label, key, role, content in actions[:2]:
                if st.button(f"{icon}  {label}", key=f"qa_{key}", use_container_width=True):
                    self._add_message(role, content)
                    st.session_state.pending_example = True
                    st.session_state.processing_example = False
                    st.rerun()

        with col2:
            for icon, label, key, role, content in actions[2:]:
                if st.button(f"{icon}  {label}", key=f"qa_{key}", use_container_width=True):
                    self._add_message(role, content)
                    st.session_state.pending_example = True
                    st.session_state.processing_example = False
                    st.rerun()

    # -------------------
    # Chat History Display
    # -------------------
    def _display_chat_history(self):
        """Display all messages with professional styling"""
        for idx, msg in enumerate(st.session_state.chat_memory):
            role = msg.get("role", "assistant")
            avatar = "🕋" if role == "assistant" else "👤"
            content = msg.get("content", "")

            with st.chat_message(role, avatar=avatar):
                st.markdown(content, unsafe_allow_html=True)

                if role == "assistant":
                    self._render_timestamp_and_actions(msg, content, idx)
                    
    def _safe_format_time(self, msg):
        """تنسيق الوقت بشكل آمن بدون أخطاء"""
        try:
            timestamp = msg.get('timestamp')
            if not timestamp:
                return datetime.now().strftime("%I:%M %p")
            
            return self._format_time(timestamp)
        except Exception:
            return datetime.now().strftime("%I:%M %p")

    def _render_timestamp_and_actions(self, msg: dict, text: str, idx: int):
        """Render timestamp with action buttons in a single row"""
        lang = st.session_state.get("language", "English")
        button_key_prefix = f"msg_{idx}"
        is_playing = st.session_state.audio_playing.get(idx, False)
        
        # Icon URLs
        play_icon = "https://img.icons8.com/?size=100&id=8VE4cuU0UjpB&format=png&color=FFFFFF"
        replay_icon = "https://img.icons8.com/?size=100&id=59872&format=png&color=FFFFFF"
        stop_icon = "https://img.icons8.com/?size=100&id=61012&format=png&color=FFFFFF"
        copy_icon = "https://img.icons8.com/?size=100&id=86206&format=png&color=FFFFFF"
        
        # Tooltips
        play_tip = "تشغيل الصوت" if lang == "العربية" else "Play audio"
        replay_tip = "إعادة التشغيل" if lang == "العربية" else "Replay audio"
        stop_tip = "إيقاف الصوت" if lang == "العربية" else "Stop audio"
        copy_tip = "نسخ النص" if lang == "العربية" else "Copy text"
        
        # Create columns based on playing state with minimal gap
        if is_playing:
            cols = st.columns([3, 0.4, 0.4, 0.4, 0.4], gap="small")
        else:
            cols = st.columns([3, 0.4, 0.4], gap="small")
        
        # Timestamp in first column
        with cols[0]:
            if msg.get("timestamp"):
                st.markdown(
                    f"<div class='message-timestamp' style='padding-top: 5px;'>🕐 {self._safe_format_time(msg)}</div>",
                    unsafe_allow_html=True
                )
        
        # Play button in second column
        with cols[1]:
            if not is_playing:
                if st.button(f"![]({play_icon})", key=f"{button_key_prefix}_play", use_container_width=True, help=play_tip):
                    self._play_message_audio(text, idx)
            else:
                st.button(f"![]({play_icon})", key=f"{button_key_prefix}_play_active", disabled=True, use_container_width=True, help=play_tip)
        
        # Replay button (only when playing)
        if is_playing:
            with cols[2]:
                if st.button(f"![]({replay_icon})", key=f"{button_key_prefix}_replay", use_container_width=True, help=replay_tip):
                    st.session_state.audio_playing[idx] = False
                    st.rerun()
        
        # Stop button (only when playing)
        if is_playing:
            with cols[3]:
                if st.button(f"![]({stop_icon})", key=f"{button_key_prefix}_stop", use_container_width=True, help=stop_tip):
                    st.session_state.audio_playing[idx] = False
                    st.rerun()
        
        # Copy button in last column
        with (cols[4] if is_playing else cols[2]):
            if st.button(f"![]({copy_icon})", key=f"{button_key_prefix}_copy", use_container_width=True, help=copy_tip):
                self._copy_to_clipboard(text, idx)

    def _play_message_audio(self, text: str, idx: int):
        """Play message audio using LLM manager's text_to_speech function"""
        lang = st.session_state.get("language", "English")
        
        try:
            # Clean text for speech
            clean_for_speech = re.sub(r'<[^>]+>', '', text)
            clean_for_speech = re.sub(r'\*\*([^\*]+)\*\*', r'\1', clean_for_speech)
            clean_for_speech = clean_for_speech.strip()
            
            if not clean_for_speech:
                st.warning("لا يوجد نص لقراءته" if lang == "العربية" else "No text to read")
                return
            
            # Call the LLM manager's text_to_speech function
            # Pass the language parameter
            tts_lang = "ar" if lang == "العربية" else "en"
            audio_bytes = self.llm.text_to_speech(clean_for_speech, tts_lang)
            
            if audio_bytes:
                # Encode audio for HTML playback
                audio_b64 = base64.b64encode(audio_bytes).decode()
                
                audio_html = f"""
                <audio id="audio_{idx}" autoplay>
                    <source src="data:audio/mp3;base64,{audio_b64}" type="audio/mp3">
                </audio>
                <script>
                    var audio = document.getElementById('audio_{idx}');
                    audio.play();
                </script>
                """
                components.html(audio_html, height=0)
                
                # Set playing state
                st.session_state.audio_playing[idx] = True
                st.rerun()
            else:
                st.error("❌ فشل في توليد الصوت" if lang == "العربية" else "❌ Failed to generate audio")
                
        except Exception as e:
            st.error(f"❌ خطأ في تشغيل الصوت: {str(e)}" if lang == "العربية" else  f"❌ Audio error: {str(e)}")

    def _copy_to_clipboard(self, text: str, idx: int):
        """Copy text to clipboard with improved functionality"""
        lang = st.session_state.get("language", "English")
        
        # Clean text for copying
        clean_text = self._clean_text_for_copy(text)
        
        # Escape special characters for JavaScript
        escaped_text = clean_text.replace('\\', '\\\\').replace('`', '\\`').replace('$', '\\$').replace('"', '\\"').replace('\n', '\\n')
        
        # Create JavaScript to copy to clipboard
        copy_js = f"""
        <script>
            (function() {{
                const text = `{escaped_text}`;
                navigator.clipboard.writeText(text).then(function() {{
                    console.log('Copied successfully');
                }}, function(err) {{
                    console.error('Could not copy text: ', err);
                }});
            }})();
        </script>
        """
        
        components.html(copy_js, height=0)
        
        # Show success message
        if lang == "العربية":
            st.toast("✅ تم النسخ إلى الحافظة!", icon="📋")
        else:
            st.toast("✅ Copied to clipboard!", icon="📋")

    def _clean_text_for_copy(self, text: str) -> str:
        """Clean text for copying - remove HTML and markdown formatting"""
        # Remove HTML tags
        clean = re.sub(r'<[^>]+>', '', text)
        # Remove markdown bold
        clean = re.sub(r'\*\*([^\*]+)\*\*', r'\1', clean)
        # Remove markdown italic
        clean = re.sub(r'\*([^\*]+)\*', r'\1', clean)
        # Remove markdown headers
        clean = re.sub(r'^#+\s+', '', clean, flags=re.MULTILINE)
        # Clean up extra whitespace
        clean = re.sub(r'\n\s*\n', '\n\n', clean)
        
        return clean.strip()

    # -------------------
    # User Input Handling
    # -------------------
    def _handle_user_input(self):
        lang = st.session_state.get("language", "English")
        user_input = None
        should_process = False
        
        if st.session_state.get("pending_example") and not st.session_state.get("processing_example"):
            st.session_state.processing_example = True
            if st.session_state.chat_memory and st.session_state.chat_memory[-1].get("role") == "user":
                user_input = st.session_state.chat_memory[-1].get("content")
                should_process = True
        
        chat_input = st.chat_input(t("input_placeholder", lang))
        if chat_input:
            user_input = chat_input
            should_process = True
            self._add_message("user", user_input)
        
        if should_process and user_input:
            valid, err = validate_user_input(user_input)
            if not valid:
                st.error(f"❌ {err}")
                st.session_state.pending_example = False
                st.session_state.processing_example = False
                return

            if chat_input:
                with st.chat_message("user", avatar="👤"):
                    st.markdown(user_input)
                    st.markdown(
                        f"<div class='message-timestamp'>🕐 {self._format_time(self._get_current_time())}</div>",
                        unsafe_allow_html=True
                    )

            with st.chat_message("assistant", avatar="🕋"):
                with st.spinner(t("thinking", lang)):
                    try:
                        final_state = self.graph.process(user_input, lang)
                        self._handle_response(final_state)
                        st.session_state.pending_example = False
                        st.session_state.processing_example = False
                    except Exception as e:
                        error_msg = f"Error: {str(e)}"
                        st.error(error_msg)
                        self._add_message("assistant", error_msg)
                        st.session_state.pending_example = False
                        st.session_state.processing_example = False

    # -------------------
    # Response Handling
    # -------------------
    def _handle_response(self, state: dict):
        if state.get("greeting_text"):
            self._respond(state["greeting_text"])
        elif state.get("needs_info"):
            self._handle_needs_info(state["needs_info"])
        elif state.get("general_answer"):
            self._respond(state["general_answer"])
        elif state.get("summary") or state.get("result_rows"):
            self._handle_database_results(state)
        else:
            err = t("general_error", st.session_state.get("language", "English"))
            st.error(err)
            self._add_message("assistant", err)

    def _handle_needs_info(self, info_request: str):
        st.markdown(info_request)
        
        # Get the index for the new message
        msg_idx = len(st.session_state.chat_memory)
        
        # Create the message object
        msg = {"role": "assistant", "content": info_request, "timestamp": self._get_current_time()}
        
        # Render timestamp and actions immediately
        self._render_timestamp_and_actions(msg, info_request, msg_idx)
        
        # Add to memory after rendering
        self._add_message("assistant", info_request)

    def _respond(self, content: str):
        st.markdown(content)
        
        # Get the index for the new message
        msg_idx = len(st.session_state.chat_memory)
        
        # Create the message object
        msg = {"role": "assistant", "content": content, "timestamp": self._get_current_time()}
        
        # Render timestamp and actions immediately
        self._render_timestamp_and_actions(msg, content, msg_idx)
        
        # Add to memory after rendering
        self._add_message("assistant", content)

    def _handle_database_results(self, state: dict):
        summary = state.get("summary", "")
        if summary:
            st.markdown(summary)
            
            # Get the index for the new message
            msg_idx = len(st.session_state.chat_memory)
            
            # Create the message object
            msg = {"role": "assistant", "content": summary, "timestamp": self._get_current_time()}
            
            # Render timestamp and actions immediately
            self._render_timestamp_and_actions(msg, summary, msg_idx)
            
            # Add to memory after rendering
            self._add_message("assistant", summary)

    # -------------------
    # Chat Memory Helpers
    # -------------------
    def _add_message(self, role: str, content: str, result_data: dict = None):
        message = {"role": role, "content": content, "timestamp": self._get_current_time()}
        if result_data:
            message["result_data"] = result_data
        st.session_state.chat_memory.append(message)

    @staticmethod
    def _get_current_time() -> float:
        return datetime.now(pytz.timezone('Asia/Riyadh')).timestamp()

    @staticmethod
    def _format_time(timestamp: float) -> str:
        dt = datetime.fromtimestamp(timestamp, pytz.timezone('Asia/Riyadh'))
        return dt.strftime("%I:%M %p")