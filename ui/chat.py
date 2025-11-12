"""
Professional Chat Interface Module
Refactored for improved maintainability and organization
"""

import streamlit as st
import re
import time
import base64
from datetime import datetime
from typing import Dict, Optional, Tuple
import pytz
import streamlit.components.v1 as components

from utils.translations import t
from utils.state import save_chat_memory
from utils.validators import validate_user_input
from core.voice_processor import VoiceProcessor


# ============================================================================
# CONSTANTS
# ============================================================================
RIYADH_TZ = pytz.timezone('Asia/Riyadh')

ICON_URLS = {
    'play': "https://img.icons8.com/?size=100&id=8VE4cuU0UjpB&format=png&color=000000",
    'replay': "https://img.icons8.com/?size=100&id=59872&format=png&color=000000",
    'stop': "https://img.icons8.com/?size=100&id=61012&format=png&color=000000",
    'copy': "https://img.icons8.com/?size=100&id=86206&format=png&color=000000"
}


# ============================================================================
# CHAT INTERFACE CLASS
# ============================================================================
class ChatInterface:
    """Manages professional chat interface and message display"""

    def __init__(self, chat_graph, llm_manager):
        self.graph = chat_graph
        self.llm = llm_manager
        self.proc = VoiceProcessor()
        self._initialize_session_state()

    # ------------------------------------------------------------------------
    # INITIALIZATION
    # ------------------------------------------------------------------------
    def _initialize_session_state(self) -> None:
        """Initialize all required session state variables"""
        defaults = {
            "chat_memory": [],
            "pending_example": False,
            "processing_example": False,
            "audio_playing": {}
        }
        
        for key, default_value in defaults.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
        
        # Add welcome message if chat is empty - باللغة العربية افتراضياً
        if not st.session_state.chat_memory:
            lang = st.session_state.get("language", "العربية")
            welcome_msg = t("welcome_msg", lang)
            self._add_message("assistant", welcome_msg)

    # ------------------------------------------------------------------------
    # PUBLIC INTERFACE
    # ------------------------------------------------------------------------
    def render(self) -> None:
        """Render complete professional chat interface"""
        self._inject_professional_styles()
        self._display_chat_history()
        self._handle_user_input()

    # ------------------------------------------------------------------------
    # STYLING
    # ------------------------------------------------------------------------
    def _inject_professional_styles(self) -> None:
        """Inject enhanced professional CSS styles"""
        st.markdown(self._get_professional_css(), unsafe_allow_html=True)

    @staticmethod
    def _get_professional_css() -> str:
        """Return professional CSS as string"""
        return """
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
        """

    # ------------------------------------------------------------------------
    # CHAT HISTORY DISPLAY
    # ------------------------------------------------------------------------
    def _display_chat_history(self) -> None:
        """Display all messages with professional styling"""
        for idx, msg in enumerate(st.session_state.chat_memory):
            self._render_single_message(msg, idx)

    def _render_single_message(self, msg: Dict, idx: int) -> None:
        """Render a single message with appropriate styling"""
        role = msg.get("role", "assistant")
        avatar = "🕋" if role == "assistant" else "👤"
        content = msg.get("content", "")

        with st.chat_message(role, avatar=avatar):
            st.markdown(content, unsafe_allow_html=True)
            
            if role == "assistant":
                self._render_timestamp_and_actions(msg, content, idx)
            else:
                self._render_timestamp_only(msg)

    def _render_timestamp_only(self, msg: Dict) -> None:
        """Render timestamp without action buttons"""
        if msg.get("timestamp"):
            timestamp_html = (
                f"<div class='message-timestamp' style='padding-top: 5px;'>"
                f"🕐 {self._safe_format_time(msg)}</div>"
            )
            st.markdown(timestamp_html, unsafe_allow_html=True)

    def _render_timestamp_and_actions(self, msg: Dict, text: str, idx: int) -> None:
        """Render timestamp with action buttons in a single row"""
        lang = st.session_state.get("language", "العربية")
        is_playing = self._check_and_update_audio_state(idx)
        
        # Create column layout
        cols = self._create_action_columns(is_playing)
        
        # Render timestamp
        self._render_timestamp_column(cols[0], msg)
        
        # Render action buttons
        self._render_action_buttons(cols, idx, text, lang, is_playing)
        
        # Play audio if triggered
        if is_playing and st.session_state.get(f"audio_trigger_{idx}", False):
            self._play_message_audio_inline(text, idx)
            st.session_state[f"audio_trigger_{idx}"] = False

    def _check_and_update_audio_state(self, idx: int) -> bool:
        """Check if audio is playing and update state if finished"""
        is_playing = st.session_state.audio_playing.get(idx, False)
        
        if is_playing:
            start_time = st.session_state.get(f"audio_start_time_{idx}")
            duration = st.session_state.get(f"audio_duration_{idx}")
            
            if start_time and duration:
                elapsed = time.time() - start_time
                if elapsed >= duration:
                    self._reset_audio_state(idx)
                    return False
        
        return is_playing

    def _create_action_columns(self, is_playing: bool):
        """Create column layout based on playback state"""
        if is_playing:
            return st.columns([3, 0.4, 0.4, 0.4, 0.4], gap="small")
        return st.columns([3, 0.4, 0.4], gap="small")

    def _render_timestamp_column(self, col, msg: Dict) -> None:
        """Render timestamp in the first column"""
        with col:
            if msg.get("timestamp"):
                timestamp_html = (
                    f"<div class='message-timestamp' style='padding-top: 5px;'>"
                    f"🕐 {self._safe_format_time(msg)}</div>"
                )
                st.markdown(timestamp_html, unsafe_allow_html=True)

    def _render_action_buttons(self, cols, idx: int, text: str, lang: str, is_playing: bool) -> None:
        """Render all action buttons"""
        button_key_prefix = f"msg_{idx}"
        
        # Play button
        self._render_play_button(cols[1], button_key_prefix, idx, lang, is_playing)
        
        # Stop and Replay buttons (only when playing)
        if is_playing:
            self._render_stop_button(cols[2], button_key_prefix, idx, lang)
            self._render_replay_button(cols[3], button_key_prefix, idx, lang)
        
        # Copy button
        copy_col_index = 4 if is_playing else 2
        self._render_copy_button(cols[copy_col_index], button_key_prefix, idx, text, lang)

    def _render_play_button(self, col, key_prefix: str, idx: int, lang: str, is_playing: bool) -> None:
        """Render play button"""
        play_tip = "تشغيل الصوت" if lang == "العربية" else "Play audio"
        
        with col:
            if not is_playing:
                if st.button(f"![Play]({ICON_URLS['play']})", key=f"{key_prefix}_play", help=play_tip):
                    st.session_state.audio_playing[idx] = True
                    st.session_state[f"audio_trigger_{idx}"] = True
                    st.rerun()
            else:
                st.button(f"![Play]({ICON_URLS['play']})", key=f"{key_prefix}_play_active", disabled=True)

    def _render_stop_button(self, col, key_prefix: str, idx: int, lang: str) -> None:
        """Render stop button"""
        stop_tip = "إيقاف الصوت" if lang == "العربية" else "Stop audio"
        
        with col:
            if st.button(f"![Stop]({ICON_URLS['stop']})", key=f"{key_prefix}_stop", help=stop_tip):
                self._reset_audio_state(idx)
                st.rerun()

    def _render_replay_button(self, col, key_prefix: str, idx: int, lang: str) -> None:
        """Render replay button"""
        replay_tip = "إعادة التشغيل" if lang == "العربية" else "Replay audio"
        
        with col:
            if st.button(f"![Replay]({ICON_URLS['replay']})", key=f"{key_prefix}_replay", help=replay_tip):
                st.session_state[f"audio_trigger_{idx}"] = True
                st.session_state[f"audio_start_time_{idx}"] = time.time()
                st.rerun()

    def _render_copy_button(self, col, key_prefix: str, idx: int, text: str, lang: str) -> None:
        """Render copy button"""
        copy_tip = "نسخ النص" if lang == "العربية" else "Copy text"
        
        with col:
            if st.button(f"![Copy]({ICON_URLS['copy']})", key=f"{key_prefix}_copy", help=copy_tip):
                self._copy_to_clipboard(text, idx)

    def _reset_audio_state(self, idx: int) -> None:
        """Reset all audio-related state for a message"""
        st.session_state.audio_playing[idx] = False
        st.session_state.pop(f"audio_start_time_{idx}", None)
        st.session_state.pop(f"audio_duration_{idx}", None)
        st.session_state.pop(f"audio_trigger_{idx}", None)

    # ------------------------------------------------------------------------
    # AUDIO PLAYBACK
    # ------------------------------------------------------------------------
    def _play_message_audio_inline(self, text: str, idx: int) -> None:
        """Play message audio using hidden HTML5 audio element"""
        lang = st.session_state.get("language", "العربية")

        try:
            clean_text = self._clean_text_for_audio(text)
            
            if not clean_text:
                self._show_no_text_warning(lang, idx)
                return

            audio_data = self._generate_audio(clean_text, lang)
            
            if audio_data:
                self._play_audio_with_duration(audio_data, idx)
            else:
                self._show_audio_error(lang, idx)

        except Exception as e:
            self._handle_audio_error(e, lang, idx)

    def _clean_text_for_audio(self, text: str) -> str:
        """Clean text for audio generation"""
        clean_text = re.sub(r'<[^>]+>', '', text)
        clean_text = re.sub(r'\*\*([^\*]+)\*\*', r'\1', clean_text).strip()
        return clean_text

    def _generate_audio(self, text: str, lang: str):
        """Generate audio from text"""
        tts_lang = "ar" if lang == "العربية" else "en"
        return self.proc.text_to_speech(text, tts_lang)

    def _play_audio_with_duration(self, audio_data, idx: int) -> None:
        """Play audio and store duration information"""
        audio_bytes = audio_data.getvalue() if hasattr(audio_data, "getvalue") else audio_data
        duration = self._get_audio_duration(audio_bytes)
        
        # Store playback info
        st.session_state[f"audio_start_time_{idx}"] = time.time()
        st.session_state[f"audio_duration_{idx}"] = duration
        
        # Play audio
        audio_base64 = base64.b64encode(audio_bytes).decode()
        self._render_audio_player(audio_base64, idx)

    def _get_audio_duration(self, audio_bytes) -> float:
        """Get audio duration using mutagen"""
        try:
            from io import BytesIO
            from mutagen.mp3 import MP3
            
            if isinstance(audio_bytes, bytes):
                audio_file = BytesIO(audio_bytes)
            else:
                audio_file = audio_bytes
            
            audio = MP3(audio_file)
            return audio.info.length
        except Exception:
            return 3.0

    def _render_audio_player(self, audio_base64: str, idx: int) -> None:
        """Render hidden HTML5 audio player"""
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

    def _show_no_text_warning(self, lang: str, idx: int) -> None:
        """Show warning when no text to read"""
        warning_msg = "لا يوجد نص لقراءته" if lang == "العربية" else "No text to read"
        st.warning(warning_msg)
        self._reset_audio_state(idx)

    def _show_audio_error(self, lang: str, idx: int) -> None:
        """Show error when audio generation fails"""
        error_msg = "❌ فشل في توليد الصوت" if lang == "العربية" else "❌ Failed to generate audio"
        st.error(error_msg)
        self._reset_audio_state(idx)

    def _handle_audio_error(self, error: Exception, lang: str, idx: int) -> None:
        """Handle audio playback errors"""
        error_msg = (
            f"❌ خطأ في تشغيل الصوت: {str(error)}"
            if lang == "العربية"
            else f"❌ Audio error: {str(error)}"
        )
        st.error(error_msg)
        self._reset_audio_state(idx)

    # ------------------------------------------------------------------------
    # CLIPBOARD OPERATIONS
    # ------------------------------------------------------------------------
    def _copy_to_clipboard(self, text: str, idx: int) -> None:
        """Copy text to clipboard using pyperclip"""
        lang = st.session_state.get("language", "العربية")
        clean_text = self._clean_text_for_copy(text)
        
        try:
            import pyperclip
            pyperclip.copy(clean_text)
            
            success_msg = "✅ تم نسخ النص بنجاح" if lang == "العربية" else "✅ Text copied successfully"
            st.toast(success_msg, icon="✅")
        except ImportError:
            self._show_copy_fallback(clean_text, idx, lang)
        except Exception as e:
            self._show_copy_error(e, lang)

    def _show_copy_fallback(self, text: str, idx: int, lang: str) -> None:
        """Show fallback text area for manual copy"""
        label = "انسخ النص من هنا:" if lang == "العربية" else "Copy text from here:"
        st.text_area(
            label,
            text,
            height=150,
            key=f"copy_fallback_{idx}_{int(time.time() * 1000)}"
        )

    def _show_copy_error(self, error: Exception, lang: str) -> None:
        """Show error message for copy operation"""
        error_msg = f"❌ خطأ في النسخ: {str(error)}" if lang == "العربية" else f"❌ Copy error: {str(error)}"
        st.error(error_msg)

    @staticmethod
    def _clean_text_for_copy(text: str) -> str:
        """Clean text for copying"""
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\*\*([^\*]+)\*\*', r'\1', clean)
        clean = re.sub(r'\*([^\*]+)\*', r'\1', clean)
        clean = re.sub(r'^#+\s+', '', clean, flags=re.MULTILINE)
        clean = re.sub(r'\n\s*\n', '\n\n', clean)
        return clean.strip()

    # ------------------------------------------------------------------------
    # USER INPUT HANDLING
    # ------------------------------------------------------------------------
    def _handle_user_input(self) -> None:
        """Handle user input from chat or examples"""
        lang = st.session_state.get("language", "العربية")
        user_input, should_process = self._get_user_input()
        
        if should_process and user_input:
            self._process_user_input(user_input, lang)

    def _get_user_input(self) -> Tuple[Optional[str], bool]:
        """Get user input and determine if it should be processed"""
        user_input = None
        should_process = False
        
        # Check for pending example
        if self._should_process_pending_example():
            st.session_state.processing_example = True
            user_input = st.session_state.chat_memory[-1].get("content")
            should_process = True
        
        # Check for new chat input
        chat_input = st.chat_input(t("input_placeholder", st.session_state.get("language", "العربية")))
        if chat_input:
            user_input = chat_input
            should_process = True
            self._add_message("user", user_input)
        
        return user_input, should_process

    def _should_process_pending_example(self) -> bool:
        """Check if there's a pending example to process"""
        return (
            st.session_state.get("pending_example") and 
            not st.session_state.get("processing_example") and
            st.session_state.chat_memory and
            st.session_state.chat_memory[-1].get("role") == "user"
        )

    def _process_user_input(self, user_input: str, lang: str) -> None:
        """Validate and process user input"""
        valid, err = validate_user_input(user_input)
        if not valid:
            st.error(f"❌ {err}")
            self._reset_processing_flags()
            return

        # Display user message if from chat input
        if not st.session_state.get("processing_example"):
            self._display_user_message(user_input)

        # Process with assistant
        self._process_with_assistant(user_input, lang)

    def _display_user_message(self, user_input: str) -> None:
        """Display user message in chat"""
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
            timestamp_html = (
                f"<div class='message-timestamp'>"
                f"🕐 {self._format_time(self._get_current_time())}</div>"
            )
            st.markdown(timestamp_html, unsafe_allow_html=True)

    def _process_with_assistant(self, user_input: str, lang: str) -> None:
        """Process input with assistant and handle response"""
        with st.chat_message("assistant", avatar="🕋"):
            with st.spinner(t("thinking", lang)):
                try:
                    final_state = self.graph.process(user_input, lang)
                    self._handle_response(final_state)
                    self._reset_processing_flags()
                except Exception as e:
                    self._handle_processing_error(e)

    def _handle_processing_error(self, error: Exception) -> None:
        """Handle errors during processing"""
        error_msg = f"Error: {str(error)}"
        st.error(error_msg)
        self._add_message("assistant", error_msg)
        self._reset_processing_flags()

    def _reset_processing_flags(self) -> None:
        """Reset example processing flags"""
        st.session_state.pending_example = False
        st.session_state.processing_example = False

    # ------------------------------------------------------------------------
    # RESPONSE HANDLING
    # ------------------------------------------------------------------------
    def _handle_response(self, state: Dict) -> None:
        """Handle different types of responses from the graph"""
        if state.get("greeting_text"):
            self._respond(state["greeting_text"])
        elif state.get("needs_info"):
            self._handle_needs_info(state["needs_info"])
        elif state.get("general_answer"):
            self._respond(state["general_answer"])
        elif state.get("summary") or state.get("result_rows"):
            self._handle_database_results(state)
        else:
            self._handle_error_response()

    def _handle_needs_info(self, info_request: str) -> None:
        """Handle information request from assistant"""
        st.markdown(info_request)
        msg_idx = len(st.session_state.chat_memory)
        msg = {
            "role": "assistant",
            "content": info_request,
            "timestamp": self._get_current_time()
        }
        self._render_timestamp_and_actions(msg, info_request, msg_idx)
        self._add_message("assistant", info_request)

    def _respond(self, content: str) -> None:
        """Display standard assistant response"""
        st.markdown(content)
        msg_idx = len(st.session_state.chat_memory)
        msg = {
            "role": "assistant",
            "content": content,
            "timestamp": self._get_current_time()
        }
        self._render_timestamp_and_actions(msg, content, msg_idx)
        self._add_message("assistant", content)

    def _handle_database_results(self, state: Dict) -> None:
        """Handle database query results"""
        summary = state.get("summary", "")
        if summary:
            st.markdown(summary)
            msg_idx = len(st.session_state.chat_memory)
            msg = {
                "role": "assistant",
                "content": summary,
                "timestamp": self._get_current_time()
            }
            self._render_timestamp_and_actions(msg, summary, msg_idx)
            self._add_message("assistant", summary)

    def _handle_error_response(self) -> None:
        """Handle error when no valid response"""
        lang = st.session_state.get("language", "العربية")
        err = t("general_error", lang)
        st.error(err)
        self._add_message("assistant", err)

    # ------------------------------------------------------------------------
    # CHAT MEMORY
    # ------------------------------------------------------------------------
    def _add_message(self, role: str, content: str, result_data: Optional[Dict] = None) -> None:
        """Add message to chat memory"""
        message = {
            "role": role,
            "content": content,
            "timestamp": self._get_current_time()
        }
        if result_data:
            message["result_data"] = result_data
        st.session_state.chat_memory.append(message)

    # ------------------------------------------------------------------------
    # TIME UTILITIES
    # ------------------------------------------------------------------------
    @staticmethod
    def _get_current_time() -> float:
        """Get current timestamp in Riyadh timezone"""
        return datetime.now(RIYADH_TZ).timestamp()

    @staticmethod
    def _format_time(timestamp: float) -> str:
        """Format timestamp to readable time string"""
        dt = datetime.fromtimestamp(timestamp, RIYADH_TZ)
        return dt.strftime("%I:%M %p")

    def _safe_format_time(self, msg: Dict) -> str:
        """Safely format time without errors"""
        try:
            timestamp = msg.get('timestamp')
            if not timestamp:
                return datetime.now().strftime("%I:%M %p")
            return self._format_time(timestamp)
        except Exception:
            return datetime.now().strftime("%I:%M %p")