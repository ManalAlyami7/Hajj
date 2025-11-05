"""
Chat Interface Module
Handles chat display, user interactions, and TTS
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
import streamlit.components.v1 as components  # << هذا السطر مهم

class ChatInterface:
    """Manages chat interface and message display"""

    def __init__(self, chat_graph, llm_manager):
        self.graph = chat_graph
        self.llm = llm_manager
        # Ensure chat memory exists
        if "chat_memory" not in st.session_state:
            st.session_state.chat_memory = []

    # -------------------
    # Public Render Method
    # -------------------
    def render(self):
        """Render chat interface"""
        self._display_chat_history()
        self._handle_user_input()
        #if self._show_quick_actions():
            #self._display_quick_actions()

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
        """Display quick action buttons at the start of chat (styled for all themes)"""
        lang = st.session_state.get("language", "English")
        st.markdown(
            f"<h3 style='margin-bottom:8px;color:rgba(255,255,255,0.9);'>{t('quick_actions', lang)}</h3>",
            unsafe_allow_html=True
        )

        theme_base = st.get_option("theme.base", "dark")
        try:
            theme_base = st.get_option("theme.base")
            if not theme_base:
                theme_base = "dark"
        except Exception:
            theme_base = "dark"

        st.markdown(f"""
        <style>
        .quick-actions-row {{ display:flex; gap:12px; margin:12px 0; flex-wrap:wrap; }}
        .quick-action {{ display:inline-block; width:100% !important; }}
        .quick-action .icon {{ margin-right:8px; font-size:1.05rem; vertical-align:middle; }}
        .quick-action .label {{ vertical-align:middle; }}
        .stButton>button {{
            width:100% !important;
            padding:12px 16px !important;
            border-radius:10px !important;
            font-weight:700 !important;
            cursor:pointer !important;
            border:none !important;
        }}
        {" .stButton>button { background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%); color:#fff; box-shadow:0 6px 18px rgba(124,58,237,0.18); }"
        if theme_base == "dark"
        else " .stButton>button { background: linear-gradient(90deg, #eef2ff 0%, #e9d5ff 100%); color:#111827; box-shadow:0 4px 10px rgba(17,24,39,0.06); }"}
        .stButton>button:hover {{ transform: translateY(-2px); }}
        </style>
        """, unsafe_allow_html=True)

        col1, col2 = st.columns(2)
        actions = [
            ("🔍", t("find_authorized", lang), "find_authorized", "user", t("show_authorized", lang)),
            ("📊", t("show_stats", lang), "show_stats", "user", t("hajj_statistics", lang)),
            ("🌍", t("find_by_country", lang), "find_by_country", "user", t("country_search", lang)),
            ("❓", t("general_help", lang), "general_help", "user", t("help_message", lang)),
        ]

        with col1:
            st.markdown("<div class='quick-actions-row'>", unsafe_allow_html=True)
            for icon, label, key, role, content in actions[:2]:
                st.markdown("<div class='quick-action'>", unsafe_allow_html=True)
                if st.button(f"{icon}  {label}", key=f"qa_{key}", use_container_width=True):
                    self._add_message(role, content)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        with col2:
            st.markdown("<div class='quick-actions-row'>", unsafe_allow_html=True)
            for icon, label, key, role, content in actions[2:]:
                st.markdown("<div class='quick-action'>", unsafe_allow_html=True)
                if st.button(f"{icon}  {label}", key=f"qa_{key}", use_container_width=True):
                    self._add_message(role, content)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

    # -------------------
    # Chat History Display
    # -------------------
    def _display_chat_history(self):
        """Display all messages in chat history"""
        for idx, msg in enumerate(st.session_state.chat_memory):
            role = msg.get("role", "assistant")
            avatar = "🕋" if role == "assistant" else "👤"
            
            with st.chat_message(role, avatar=avatar):
                st.markdown(msg.get("content", ""), unsafe_allow_html=True)
                if role == "assistant":
                    col1, col2 = st.columns([0.7, 0.3])
                    with col1:
                        if msg.get("timestamp"):
                            st.markdown(
                                f"<div style='color: #777; font-size:0.8rem; margin-top:4px'>🕐 {self._format_time(msg['timestamp'])}</div>",
                                unsafe_allow_html=True
                            )
                        # Show TTS for assistant messages
                        if role == "assistant":
                            self._create_voice_player(msg.get("content", "")[:4000], idx=str(idx))

    # -------------------
    # User Input Handling
    # -------------------
    def _handle_user_input(self):
        lang = st.session_state.get("language", "English")
        user_input = None
        if st.session_state.get("selected_question"):
            user_input = st.session_state["selected_question"]
            st.session_state.selected_question = ""
        else:
            user_input = st.chat_input(t("input_placeholder", lang))
        
        if not user_input:
            return
        
        valid, err = validate_user_input(user_input)
        if not valid:
            st.error(f"❌ {err}")
            return

        self._add_message("user", user_input)
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
            st.markdown(
                f"<div style='color: #777; font-size:0.8rem'>🕐 {self._format_time(self._get_current_time())}</div>",
                unsafe_allow_html=True
            )

        with st.chat_message("assistant", avatar="🕋"):
            with st.spinner(t("thinking", lang)):
                final_state = self.graph.process(user_input, lang)
            self._handle_response(final_state)

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
        lang = st.session_state.get("language", "English")
        st.markdown(info_request)
        self._create_voice_player(info_request)  # يظهر المشغل مباشرة
        self._add_message("assistant", info_request)

    def _respond(self, content: str):
        st.markdown(content)
        # اعرض مشغل الصوت مع الثلاثة أيقونات مباشرة
        self._create_voice_player(content)
        self._add_message("assistant", content)

    # -------------------
    # Database Results Display
    # -------------------
    def _handle_database_results(self, state: dict):
        summary = state.get("summary", "")
        if summary:
            st.markdown(summary)
            self._create_voice_player(summary) 
            self._add_message("assistant", summary)
        else:
            st.warning(summary)
            self._add_message("assistant", summary)

    def _display_results(self, result_data: dict):
        rows = result_data.get("rows", [])
        if not rows:
            st.info("No results found.")
            return
        st.markdown("### 🕋 Authorized Hajj Agencies")
        for row in rows:
            name_en = row.get("hajj_company_en", "") or "N/A"
            name_ar = row.get("hajj_company_ar", "") or ""
            address = row.get("formatted_address", "")
            city = row.get("city", "")
            country = row.get("country", "")
            email = row.get("email", "")
            phone = row.get("contact_Info", "")
            rating = row.get("rating_reviews", "")
            authorized = row.get("is_authorized", "")
            maps_link = row.get("google_maps_link", "")
            link_valid = row.get("link_valid", False)
            is_authorized = authorized in ["yes", "true", "1"]
            status_icon = "✅ Authorized" if authorized.lower() == "yes" else "❌ Not Authorized"
            bg_color = "rgba(16,185,129,0.1)" if authorized.lower() == "yes" else "rgba(239,68,68,0.1)"
            border_color = "#10b981" if authorized.lower() == "yes" else "#ef4444"

            if maps_link:
                if link_valid:
                    maps_display = f"""
                    <div style='margin-top:10px;display:flex;gap:10px;align-items:center;'>
                        <a href='{maps_link}' target='_blank'
                        style='padding:6px 12px;background-color:#2563eb;color:white;
                                text-decoration:none;border-radius:8px;font-size:0.9rem;'>
                        📍 Open Map
                        </a>
                        <button onclick="navigator.clipboard.writeText('{maps_link}');
                                        var msg=document.createElement('div');
                                        msg.innerText='✅ Link copied!';
                                        msg.style='position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
                                                background:#10b981;color:white;padding:8px 14px;border-radius:8px;
                                                z-index:9999;font-size:0.9rem;';
                                        document.body.appendChild(msg);
                                        setTimeout(()=>msg.remove(),2000);"
                                style='padding:6px 12px;background-color:#10b981;color:white;
                                    border:none;border-radius:8px;font-size:0.9rem;cursor:pointer;'>
                            🔗 Copy Link
                        </button>
                    </div>
                    """
                else:
                    maps_display = "<span style='color:#f87171;'>⚠️ Invalid Link</span>"
            else:
                maps_display = "N/A"


            st.markdown(f"""
            <div style='padding:14px;margin:10px 0;border-radius:10px;
                        background:{bg_color};border:1.5px solid {border_color};'>
                <strong>🏢 {name_en}</strong>  
                {f"<br><span style='color:#555;font-size:0.95rem;'>({name_ar})</span>" if name_ar else ""}<br><br>
                📍 <b>Address:</b> {address or "N/A"}  
                <br>🏙️ <b>City:</b> {city or "N/A"} | 🌍 <b>Country:</b> {country or "N/A"}  
                <br>☎️ <b>Phone:</b> {phone or "N/A"}  
                <br>📧 <b>Email:</b> {email or "N/A"}  
                <br>⭐ <b>Rating & Reviews:</b> {rating or "N/A"} 
                <br>🗺️ <b>Google Maps:</b> {maps_display} 
                <br><b>Status:</b> {status_icon}
            </div>
            """, unsafe_allow_html=True)
            save_chat_memory()

    # -------------------
    # TTS
    # -------------------
    # def _create_voice_player(self, text: str, autoplay: bool = False, idx: str = None):
    #     """Render audio player for TTS"""
    #     if idx is None:
    #         idx = str(uuid.uuid4())
    #     try:
    #         audio_io = self.llm.text_to_speech(text, st.session_state.get("language", "English"))
    #         if audio_io is None:
    #             raise RuntimeError("No audio returned")
    #         audio_bytes = audio_io.getvalue() if hasattr(audio_io, "getvalue") else bytes(audio_io)
    #         b64 = base64.b64encode(audio_bytes).decode("ascii")
    #         html = f"""
    #         <audio id="audio_{idx}" src="data:audio/mp3;base64,{b64}" {'autoplay' if autoplay else ''}></audio>
    #         <div style="margin:5px 0;">
    #             <button onclick="document.getElementById('audio_{idx}').play()">🔊 Play/Resume</button>
    #             <button onclick="var a=document.getElementById('audio_{idx}'); a.currentTime=0; a.play();">🔄 Replay</button>
    #             <button onclick="document.getElementById('audio_{idx}').pause()">⏹️ Stop</button>
    #         </div>
    #         """
    #         components.html(html, height=60)
    #     except Exception as e:
    #         st.error(f"❌ TTS failed: {str(e)}")
    def _create_voice_player(self, text: str, idx: str = None):
        """Render audio player with icon-only buttons for TTS"""
        import streamlit.components.v1 as components
        import base64
        import uuid

        if idx is None:
            idx = str(uuid.uuid4())

        try:
            audio_io = self.llm.text_to_speech(text, st.session_state.get("language", "English"))
            if audio_io is None:
                raise RuntimeError("No audio returned")
            audio_bytes = audio_io.getvalue() if hasattr(audio_io, "getvalue") else bytes(audio_io)
            b64 = base64.b64encode(audio_bytes).decode("ascii")

            html = f"""
            <audio id="audio_{idx}" src="data:audio/mp3;base64,{b64}"></audio>
            <div style="margin:5px 0; display:flex; gap:8px;">
                <button style="font-size:20px; padding:6px 10px; border-radius:8px; border:none; cursor:pointer;"
                    onclick="document.getElementById('audio_{idx}').play()">🔊</button>
                <button style="font-size:20px; padding:6px 10px; border-radius:8px; border:none; cursor:pointer;"
                    onclick="var a=document.getElementById('audio_{idx}'); a.currentTime=0; a.play();">🔄</button>
                <button style="font-size:20px; padding:6px 10px; border-radius:8px; border:none; cursor:pointer;"
                    onclick="document.getElementById('audio_{idx}').pause()">⏹️</button>
            </div>
            """

            components.html(html, height=50)                   
        except Exception as e:
            st.error(f"❌ TTS failed: {str(e)}")


    # -------------------
    # Chat Memory Helpers
    # -------------------
    def _add_message(self, role: str, content: str, result_data: dict = None):
        message = {"role": role, "content": content, "timestamp": self._get_current_time()}
        if result_data: message["result_data"] = result_data
        st.session_state.chat_memory.append(message)
        save_chat_memory()

    @staticmethod
    def _get_current_time() -> float:
        return datetime.now(pytz.timezone('Asia/Riyadh')).timestamp()

    @staticmethod
    def _format_time(timestamp: float) -> str:
        dt = datetime.fromtimestamp(timestamp, pytz.timezone('Asia/Riyadh'))
        return dt.strftime("%I:%M %p")
