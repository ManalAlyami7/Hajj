"""
Professional Chat Interface Module
Enhanced with formal design, improved UX, and consistent branding
Fixed color scheme with proper contrast and visibility
Simple clipboard copy with fallback
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
import time
from core.voice_processor import VoiceProcessor

class ChatInterface:
    """Manages professional chat interface and message display"""

    def __init__(self, chat_graph, llm_manager):
        self.graph = chat_graph
        self.llm = llm_manager
        self.proc = VoiceProcessor()
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

/* Icon Buttons (Rounded Squares) */
div[data-testid="column"], .stButton {
    padding: 0 !important;
    margin: 0 !important;
}

div[data-testid="stHorizontalBlock"] {
    gap: 3px !important;
}

.stButton > button:has(img) {
    background: linear-gradient(135deg, var(--primary-gold), var(--primary-gold-dark)) !important;
    border: none !important;
    border-radius: 12px !important;
    padding: 3px !important;
    margin: 0 0px !important;
    box-shadow: var(--shadow-sm) !important;
    width: 42px !important;
    height: 42px !important;
    display: inline-flex !important;
    align-items: center !important;
    justify-content: center !important;
    transition: all 0.25s ease !important;
}

.stButton > button:has(img):hover {
    transform: translateY(-2px) scale(1.05);
    box-shadow: var(--shadow-md) !important;
    background: linear-gradient(135deg, var(--primary-gold-dark), #9d7a1a) !important;
}

.stButton > button:has(img):active {
    transform: scale(0.97);
}

.stButton > button:focus {
    outline: none !important;
    box-shadow: 0 0 0 3px rgba(212, 175, 55, 0.3) !important;
}

.stChatMessage div[data-testid="column"] > div > div > button {
    padding: 0 !important;
    border-radius: 10px !important;
    border: 2px solid var(--primary-gold) !important;
    background: linear-gradient(135deg, var(--primary-gold) 0%, var(--primary-gold-dark) 100%) !important;
    box-shadow: var(--shadow-sm) !important;
    transition: all 0.3s ease !important;
    width: 40px !important;
    height: 40px !important;
    display: flex !important;
    align-items: center !important;
    justify-content: center !important;
    margin: 0 3px !important;
}

.stChatMessage div[data-testid="column"] > div > div > button:hover {
    transform: translateY(-2px) !important;
    background: linear-gradient(135deg, var(--primary-gold-dark), #9d7a1a) !important;
    box-shadow: var(--shadow-md) !important;
}

.stChatMessage div[data-testid="column"] > div > div > button:disabled {
    opacity: 0.6 !important;
    cursor: not-allowed !important;
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

/* Loading Spinner */
.stSpinner > div {
    border-color: var(--primary-gold) !important;
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
    # Chat History Display
    # -------------------
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

        # Icons
        play_icon = "https://img.icons8.com/?size=100&id=8VE4cuU0UjpB&format=png&color=000000"
        replay_icon = "https://img.icons8.com/?size=100&id=59872&format=png&color=000000"
        stop_icon = "https://img.icons8.com/?size=100&id=61012&format=png&color=000000"
        copy_icon = "https://img.icons8.com/?size=100&id=86206&format=png&color=000000"

        # Tooltips
        play_tip = "تشغيل الصوت" if lang == "العربية" else "Play audio"
        replay_tip = "إعادة التشغيل" if lang == "العربية" else "Replay audio"
        stop_tip = "إيقاف الصوت" if lang == "العربية" else "Stop audio"
        copy_tip = "نسخ النص" if lang == "العربية" else "Copy text"

        # Check if audio has finished playing
        if is_playing:
            start_time = st.session_state.get(f"audio_start_time_{idx}")
            duration = st.session_state.get(f"audio_duration_{idx}")
            
            if start_time and duration:
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    # Audio finished, reset state
                    st.session_state.audio_playing[idx] = False
                    st.session_state.pop(f"audio_start_time_{idx}", None)
                    st.session_state.pop(f"audio_duration_{idx}", None)
                    st.session_state.pop(f"audio_trigger_{idx}", None)
                    is_playing = False

        # Create columns based on playing state
        if is_playing:
            cols = st.columns([3, 0.4, 0.4, 0.4, 0.4], gap="small")
        else:
            cols = st.columns([3, 0.4, 0.4], gap="small")

        # Timestamp
        with cols[0]:
            if msg.get("timestamp"):
                st.markdown(
                    f"<div class='message-timestamp' style='padding-top: 5px;'>🕐 {self._safe_format_time(msg)}</div>",
                    unsafe_allow_html=True,
                )

        # Play button
        with cols[1]:
            if not is_playing:
                if st.button(f"![Play]({play_icon})", key=f"{button_key_prefix}_play", help=play_tip):
                    st.session_state.audio_playing[idx] = True
                    st.session_state[f"audio_trigger_{idx}"] = True
                    st.rerun()
            else:
                st.button(f"![Play]({play_icon})", key=f"{button_key_prefix}_play_active", disabled=True)

        # Stop and Replay buttons - only when playing
        if is_playing:
            with cols[2]:
                if st.button(f"![Stop]({stop_icon})", key=f"{button_key_prefix}_stop", help=stop_tip):
                    st.session_state.audio_playing[idx] = False
                    st.session_state.pop(f"audio_start_time_{idx}", None)
                    st.session_state.pop(f"audio_duration_{idx}", None)
                    st.session_state.pop(f"audio_trigger_{idx}", None)
                    st.rerun()

            with cols[3]:
                if st.button(f"![Replay]({replay_icon})", key=f"{button_key_prefix}_replay", help=replay_tip):
                    st.session_state[f"audio_trigger_{idx}"] = True
                    st.session_state[f"audio_start_time_{idx}"] = time.time()
                    st.rerun()

        # Copy button
        copy_col_index = 4 if is_playing else 2
        with cols[copy_col_index]:
            if st.button(f"![Copy]({copy_icon})", key=f"{button_key_prefix}_copy", help=copy_tip):
                self._copy_to_clipboard(text, idx)

        # Play audio if triggered
        if is_playing and st.session_state.get(f"audio_trigger_{idx}", False):
            self._play_message_audio_inline(text, idx)
            st.session_state[f"audio_trigger_{idx}"] = False

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
                else:
                    if msg.get("timestamp"):
                        st.markdown(
                            f"<div class='message-timestamp' style='padding-top: 5px;'>🕐 {self._safe_format_time(msg)}</div>",
                            unsafe_allow_html=True,
                        )

    def _play_message_audio_inline(self, text: str, idx: int):
            """Play message audio using hidden HTML5 audio element"""
            lang = st.session_state.get("language", "English")

            try:
                # Remove HTML tags
                clean_text = re.sub(r'<[^>]+>', '', text)
                
                # Remove URLs (comprehensive pattern for http/https URLs with any characters)
                clean_text = re.sub(r'https?://\S+', '', clean_text)
                
                # Remove www URLs without protocol
                clean_text = re.sub(r'www\.\S+', '', clean_text)
                
                # Remove markdown bold
                clean_text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', clean_text)
                
                # Clean up extra whitespace
                clean_text = re.sub(r'\s+', ' ', clean_text).strip()

                if not clean_text:
                    st.warning("لا يوجد نص لقراءته" if lang == "العربية" else "No text to read")
                    st.session_state.audio_playing[idx] = False
                    st.session_state.pop(f"audio_trigger_{idx}", None)
                    return

                tts_lang = "ar" if lang == "العربية" else "en"
                audio_data = self.proc.text_to_speech(clean_text, tts_lang)

                if audio_data:
                    audio_bytes = audio_data.getvalue() if hasattr(audio_data, "getvalue") else audio_data
                    
                    from io import BytesIO
                    from mutagen.mp3 import MP3
                    
                    if isinstance(audio_bytes, bytes):
                        audio_file = BytesIO(audio_bytes)
                    else:
                        audio_file = audio_bytes
                    
                    try:
                        audio = MP3(audio_file)
                        duration = audio.info.length
                    except Exception:
                        duration = 3.0
                    
                    # Store playback info
                    st.session_state[f"audio_start_time_{idx}"] = time.time()
                    st.session_state[f"audio_duration_{idx}"] = duration
                    
                    # Convert to base64 and play with hidden audio element
                    audio_base64 = base64.b64encode(audio_bytes).decode()
                    
                    components.html(
                        f"""
                        <audio autoplay style="display:none;" id="audio_{idx}_{int(time.time()*1000)}">
                            <source src="data:audio/mp3;base64,{audio_base64}" type="audio/mp3">
                        </audio>
                        <script>
                            var audio = document.querySelector('audio[id^="audio_{idx}_"]');
                            if (audio) {{
                                audio.play().catch(function(e) {{
                                    console.error('Audio play failed:', e);
                                }});
                            }}
                        </script>
                        """,
                        height=0,
                    )
                    
                else:
                    st.error("❌ فشل في توليد الصوت" if lang == "العربية" else "❌ Failed to generate audio")
                    st.session_state.audio_playing[idx] = False
                    st.session_state.pop(f"audio_trigger_{idx}", None)

            except Exception as e:
                st.error(
                    f"❌ خطأ في تشغيل الصوت: {str(e)}"
                    if lang == "العربية"
                    else f"❌ Audio error: {str(e)}"
                )
                st.session_state.audio_playing[idx] = False
                st.session_state.pop(f"audio_trigger_{idx}", None)
                st.session_state.pop(f"audio_start_time_{idx}", None)
                st.session_state.pop(f"audio_duration_{idx}", None)

    def _copy_to_clipboard(self, text: str, idx: int):
        """Copy text to clipboard using pyperclip"""
        lang = st.session_state.get("language", "English")
        clean_text = self._clean_text_for_copy(text)
        
        try:
            # Use pyperclip for reliable clipboard access
            import pyperclip
            pyperclip.copy(clean_text)
            
            success_msg = "✅ تم نسخ النص بنجاح" if lang == "العربية" else "✅ Text copied successfully"
            st.toast(success_msg, icon="✅")
        except ImportError:
            # Fallback: Show text in a text area for manual copy
            st.text_area(
                "انسخ النص من هنا:" if lang == "العربية" else "Copy text from here:",
                clean_text,
                height=150,
                key=f"copy_fallback_{idx}_{int(time.time() * 1000)}"
            )
        except Exception as e:
            st.error(f"❌ خطأ في النسخ: {str(e)}" if lang == "العربية" else f"❌ Copy error: {str(e)}")

    def _clean_text_for_copy(self, text: str) -> str:
        """Clean text for copying"""
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\*\*([^\*]+)\*\*', r'\1', clean)
        clean = re.sub(r'\*([^\*]+)\*', r'\1', clean)
        clean = re.sub(r'^#+\s+', '', clean, flags=re.MULTILINE)
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
        msg_idx = len(st.session_state.chat_memory)
        msg = {"role": "assistant", "content": info_request, "timestamp": self._get_current_time()}
        self._render_timestamp_and_actions(msg, info_request, msg_idx)
        self._add_message("assistant", info_request)

    def _respond(self, content: str):
        st.markdown(content)
        msg_idx = len(st.session_state.chat_memory)
        msg = {"role": "assistant", "content": content, "timestamp": self._get_current_time()}
        self._render_timestamp_and_actions(msg, content, msg_idx)
        self._add_message("assistant", content)

    def _handle_database_results(self, state: dict):
        summary = state.get("summary", "")
        if summary:
            st.markdown(summary)
            msg_idx = len(st.session_state.chat_memory)
            msg = {"role": "assistant", "content": summary, "timestamp": self._get_current_time()}
            self._render_timestamp_and_actions(msg, summary, msg_idx)
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
