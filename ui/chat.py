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
import streamlit.components.v1 as components

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
        
        # Handle pending example from sidebar
        if st.session_state.get("pending_example", True):
            st.session_state.pending_example = True
            self._process_pending_example()
        
        # Always show input (CRITICAL!)
        self._handle_user_input()

    # -------------------
    # Process Pending Example
    # -------------------
    def _process_pending_example(self):
        """Process example question clicked from sidebar"""
        # Get last message (should be user message)
        if st.session_state.chat_memory and st.session_state.chat_memory[-1]["role"] == "user":
            user_input = st.session_state.chat_memory[-1]["content"]
            lang = st.session_state.get("language", "English")
            
            with st.chat_message("assistant", avatar="🕋"):
                with st.spinner(t("thinking", lang)):
                    final_state = self.graph.process(user_input, lang)
                self._handle_response(final_state)
            
            # Force rerun to display properly
            st.rerun()

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
                    with col2:
                        tts_btn_key = f"tts_btn_{idx}"
                        if st.button("🔊", key=tts_btn_key, help="Listen to message"):
                            self._create_voice_player(msg.get("content", "")[:4000], idx=str(idx))
                else:
                    if msg.get("timestamp"):
                        st.markdown(
                            f"<div style='color: #777; font-size:0.8rem; margin-top:4px'>🕐 {self._format_time(msg['timestamp'])}</div>",
                            unsafe_allow_html=True
                        )

    # -------------------
    # User Input Handling
    # -------------------
    def _handle_user_input(self):
        """Handle user input from chat input box"""
        lang = st.session_state.get("language", "English")
        
        # CRITICAL: Always show chat input
        user_input = st.chat_input(t("input_placeholder", lang), key="main_chat_input")
        
        if not user_input:
            return
        
        # Validate input
        valid, err = validate_user_input(user_input)
        if not valid:
            st.error(f"❌ {err}")
            return

        # Add user message
        self._add_message("user", user_input)
        
        # Display user message
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
            st.markdown(
                f"<div style='color: #777; font-size:0.8rem'>🕐 {self._format_time(self._get_current_time())}</div>",
                unsafe_allow_html=True
            )

        # Process and display response
        with st.chat_message("assistant", avatar="🕋"):
            with st.spinner(t("thinking", lang)):
                final_state = self.graph.process(user_input, lang)
            self._handle_response(final_state)
        
        # Rerun to update display
        st.rerun()

    # -------------------
    # Response Handling
    # -------------------
    def _handle_response(self, state: dict):
        """Handle different types of responses"""
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
        """Handle information request"""
        lang = st.session_state.get("language", "English")
        st.markdown(info_request)
        if st.button("🔊 Listen", key=str(uuid.uuid4())):
            self._create_voice_player(info_request)
        self._add_message("assistant", info_request)

    def _respond(self, content: str):
        """Display and save response"""
        st.markdown(content)
        if st.button("🔊 Listen", key=str(uuid.uuid4())):
            self._create_voice_player(content)
        self._add_message("assistant", content)

    # -------------------
    # Database Results Display
    # -------------------
    def _handle_database_results(self, state: dict):
        """Display database query results"""
        summary = state.get("summary", "")
        if summary:
            st.markdown(summary)
            if st.button("🔊 Listen to Summary", key=str(uuid.uuid4())):
                self._create_voice_player(summary)
            self._add_message("assistant", summary)
        else:
            st.warning(summary)
            self._add_message("assistant", summary)

    def _display_results(self, result_data: dict):
        """Display results in formatted cards"""
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
            
            is_authorized = authorized.lower() in ["yes", "true", "1"]
            status_icon = "✅ Authorized" if is_authorized else "❌ Not Authorized"
            bg_color = "rgba(16,185,129,0.1)" if is_authorized else "rgba(239,68,68,0.1)"
            border_color = "#10b981" if is_authorized else "#ef4444"

            if maps_link and link_valid:
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
                                    msg.style='position:fixed;bottom:20px;left:50%;transform:translateX(-50%);background:#10b981;color:white;padding:8px 14px;border-radius:8px;z-index:9999;font-size:0.9rem;';
                                    document.body.appendChild(msg);
                                    setTimeout(()=>msg.remove(),2000);"
                            style='padding:6px 12px;background-color:#10b981;color:white;
                                border:none;border-radius:8px;font-size:0.9rem;cursor:pointer;'>
                        🔗 Copy Link
                    </button>
                </div>
                """
            elif maps_link and not link_valid:
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
    def _create_voice_player(self, text: str, idx: str = None):
        """Render audio player with icon-only buttons for TTS"""
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
        """Add message to chat memory"""
        message = {
            "role": role,
            "content": content,
            "timestamp": self._get_current_time()
        }
        if result_data:
            message["result_data"] = result_data
        st.session_state.chat_memory.append(message)
        save_chat_memory()

    @staticmethod
    def _get_current_time() -> float:
        """Get current timestamp"""
        return datetime.now(pytz.timezone('Asia/Riyadh')).timestamp()

    @staticmethod
    def _format_time(timestamp: float) -> str:
        """Format timestamp to readable time"""
        dt = datetime.fromtimestamp(timestamp, pytz.timezone('Asia/Riyadh'))
        return dt.strftime("%I:%M %p")