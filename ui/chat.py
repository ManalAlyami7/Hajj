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
        if "chat_memory" not in st.session_state:
            st.session_state.chat_memory = []
        if "pending_example" not in st.session_state:
            st.session_state.pending_example = False
        if "processing_example" not in st.session_state:
            st.session_state.processing_example = False

    # -------------------
    # Public Render Method
    # -------------------
    def render(self):
        """Render chat interface"""
        self._display_chat_history()
        
        # Show quick actions only if conditions are met
        if self._show_quick_actions():
            self._display_quick_actions()
        
        self._handle_user_input()

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
        """Display quick action buttons with clean modern theme"""
        lang = st.session_state.get("language", "English")
        
        st.markdown(f"""
            <div style='background: white; 
                        padding: 1.2rem; border-radius: 16px; margin-bottom: 1rem;
                        border: 2px solid #e5e7eb; text-align: center;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);'>
                <h3 style='margin: 0; color: #1f2937; font-weight: 700;
                           letter-spacing: 0.3px;'>
                    {t('quick_actions', lang)}
                </h3>
            </div>
        """, unsafe_allow_html=True)

        st.markdown("""
        <style>
        .quick-actions-row { display:flex; gap:12px; margin:12px 0; flex-wrap:wrap; }
        .quick-action { display:inline-block; width:100% !important; }
        .stButton>button {
            width:100% !important;
            padding:14px 18px !important;
            border-radius:12px !important;
            font-weight:600 !important;
            cursor:pointer !important;
            border:2px solid #e5e7eb !important;
            background: white !important;
            color:#1f2937 !important;
            box-shadow:0 2px 8px rgba(0, 0, 0, 0.06) !important;
            transition: all 0.3s ease !important;
        }
        .stButton>button:hover { 
            transform: translateY(-2px); 
            box-shadow:0 6px 16px rgba(0, 0, 0, 0.12) !important;
            border-color: #d1d5db !important;
            background: #f9fafb !important;
        }
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
        """Display all messages in chat history with clean modern theme"""
        for idx, msg in enumerate(st.session_state.chat_memory):
            role = msg.get("role", "assistant")
            avatar = "🕋" if role == "assistant" else "👤"

            with st.chat_message(role, avatar=avatar):
                st.markdown(msg.get("content", ""), unsafe_allow_html=True)

                if msg.get("timestamp"):
                    time_color = "#6b7280"
                    st.markdown(
                        f"<div style='color: {time_color}; font-size:0.8rem; margin-top:4px; font-weight:500'>🕐 {self._format_time(msg['timestamp'])}</div>",
                        unsafe_allow_html=True
                    )

                # TTS buttons with clean modern colors
                if role == "assistant":
                    html = f"""
                    <div style="margin:8px 0; display:flex; gap:10px;">
                        <button style="font-size:20px; padding:8px 14px; border-radius:10px; 
                                       border:2px solid #e5e7eb; background:white; color:#1f2937;
                                       cursor:pointer; transition: all 0.3s ease;
                                       box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);"
                                onmouseover="this.style.background='#f9fafb'; this.style.boxShadow='0 4px 10px rgba(0, 0, 0, 0.1)'"
                                onmouseout="this.style.background='white'; this.style.boxShadow='0 2px 6px rgba(0, 0, 0, 0.06)'"
                                onclick="fetch('/generate_tts', {{
                                    method: 'POST',
                                    headers: {{'Content-Type':'application/json'}},
                                    body: JSON.stringify({{'text':'{msg.get('content','').replace("'", "\\'")}'}})
                                }}).then(resp => resp.json())
                                .then(data => {{
                                    const audio = new Audio('data:audio/mp3;base64,' + data.audio_b64);
                                    audio.id = 'audio_{idx}';
                                    audio.play();
                                    window.audio_{idx} = audio;
                                }});"
                        >🔊</button>
                        <button style="font-size:20px; padding:8px 14px; border-radius:10px; 
                                       border:2px solid #e5e7eb; background:#3b82f6; color:white;
                                       cursor:pointer; transition: all 0.3s ease; font-weight:600;
                                       box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);"
                                onmouseover="this.style.background='#2563eb'; this.style.boxShadow='0 4px 10px rgba(59, 130, 246, 0.4)'"
                                onmouseout="this.style.background='#3b82f6'; this.style.boxShadow='0 2px 6px rgba(59, 130, 246, 0.3)'"
                                onclick="if(window.audio_{idx}){{ window.audio_{idx}.currentTime=0; window.audio_{idx}.play(); }}">🔄</button>
                        <button style="font-size:20px; padding:8px 14px; border-radius:10px; 
                                       border:2px solid #e5e7eb; background:white; color:#ef4444;
                                       cursor:pointer; transition: all 0.3s ease; font-weight:600;
                                       box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);"
                                onmouseover="this.style.background='#fef2f2'; this.style.borderColor='#fca5a5'"
                                onmouseout="this.style.background='white'; this.style.borderColor='#e5e7eb'"
                                onclick="if(window.audio_{idx}){{ window.audio_{idx}.pause(); }}">⏹️</button>
                    </div>
                    """
                    components.html(html, height=60)

    # -------------------
    # User Input Handling
    # -------------------
    def _handle_user_input(self):
        lang = st.session_state.get("language", "English")
        user_input = None
        should_process = False
        
        # Check if there's a pending example from sidebar that hasn't been processed yet
        if st.session_state.get("pending_example") and not st.session_state.get("processing_example"):
            # Mark as processing
            st.session_state.processing_example = True
            
            # Get the last user message from chat memory
            if st.session_state.chat_memory and st.session_state.chat_memory[-1].get("role") == "user":
                user_input = st.session_state.chat_memory[-1].get("content")
                should_process = True
        
        # Always show the chat input (this is the fix!)
        chat_input = st.chat_input(t("input_placeholder", lang))
        if chat_input:
            user_input = chat_input
            should_process = True
            # Add new message from chat input
            self._add_message("user", user_input)
        
        # If we have input to process
        if should_process and user_input:
            # Validate input
            valid, err = validate_user_input(user_input)
            if not valid:
                st.error(f"❌ {err}")
                # Clear flags
                st.session_state.pending_example = False
                st.session_state.processing_example = False
                return

            # Display user message if it's from chat input
            if chat_input:
                with st.chat_message("user", avatar="👤"):
                    st.markdown(user_input)
                    st.markdown(
                        f"<div style='color: #6b7280; font-size:0.8rem; font-weight:500'>🕐 {self._format_time(self._get_current_time())}</div>",
                        unsafe_allow_html=True
                    )

            # Process the query and show response
            with st.chat_message("assistant", avatar="🕋"):
                with st.spinner(t("thinking", lang)):
                    try:
                        final_state = self.graph.process(user_input, lang)
                        self._handle_response(final_state)
                        
                        # Clear flags after successful processing
                        st.session_state.pending_example = False
                        st.session_state.processing_example = False
                        
                    except Exception as e:
                        error_msg = f"Error processing request: {str(e)}"
                        st.error(error_msg)
                        self._add_message("assistant", error_msg)
                        st.markdown(
                            f"<div style='color: #6b7280; font-size:0.8rem; margin-top:4px; font-weight:500'>🕐 {self._format_time(self._get_current_time())}</div>",
                            unsafe_allow_html=True
                        )
                        
                        # Clear flags on error too
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
        lang = st.session_state.get("language", "English")
        st.markdown(info_request)
        self._create_voice_player(info_request)  
        self._add_message("assistant", info_request)

    def _respond(self, content: str):
        st.markdown(content)
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
            
        st.markdown("""
            <div style='background: white; 
                        padding: 1.2rem; border-radius: 16px; margin: 1rem 0;
                        border: 2px solid #e5e7eb; text-align: center;
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);'>
                <h3 style='margin: 0; color: #1f2937; font-weight: 700;
                           letter-spacing: 0.3px;'>
                    🕋 Authorized Hajj Agencies
                </h3>
            </div>
        """, unsafe_allow_html=True)
        
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
            
            is_authorized = authorized.lower() == "yes"
            status_icon = "✅ Authorized" if is_authorized else "❌ Not Authorized"
            bg_color = "white"
            border_color = "#10b981" if is_authorized else "#ef4444"

            if maps_link and link_valid:
                maps_display = f"""
                <div style='margin-top:12px;display:flex;gap:10px;align-items:center;flex-wrap:wrap;'>
                    <a href='{maps_link}' target='_blank'
                       style='padding:8px 16px;background:#3b82f6;color:white;
                              text-decoration:none;border-radius:10px;font-size:0.9rem;
                              border:2px solid #e5e7eb;font-weight:600;
                              transition: all 0.3s ease;
                              box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);'>
                    📍 Open Map
                    </a>
                    <button onclick="navigator.clipboard.writeText('{maps_link}');
                                    var msg=document.createElement('div');
                                    msg.innerText='✅ Link copied!';
                                    msg.style='position:fixed;bottom:20px;left:50%;transform:translateX(-50%);
                                            background:#10b981;color:white;padding:10px 16px;border-radius:10px;
                                            border:2px solid white;z-index:9999;font-size:0.9rem;font-weight:600;
                                            box-shadow: 0 4px 12px rgba(16, 185, 129, 0.3);';
                                    document.body.appendChild(msg);
                                    setTimeout(()=>msg.remove(),2000);"
                            style='padding:8px 16px;background:white;color:#1f2937;
                                   border:2px solid #e5e7eb;border-radius:10px;font-size:0.9rem;
                                   cursor:pointer;font-weight:600;transition: all 0.3s ease;
                                   box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);'>
                        🔗 Copy Link
                    </button>
                </div>
                """
            else:
                maps_display = "<span style='color:#ef4444;font-weight:500;'>⚠️ Invalid Link</span>" if maps_link else "N/A"

            st.markdown(f"""
            <div style='padding:18px;margin:12px 0;border-radius:14px;
                        background:{bg_color};border:2px solid {border_color};
                        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
                        transition: transform 0.2s ease;'>
                <strong style='color:#1f2937;font-size:1.15rem;'>🏢 {name_en}</strong>  
                {f"<br><span style='color:#6b7280;font-size:0.95rem;font-weight:500;'>({name_ar})</span>" if name_ar else ""}<br><br>
                <div style='color:#4b5563;line-height:1.8;'>
                    📍 <b style='color:#1f2937;'>Address:</b> {address or "N/A"}  
                    <br>🏙️ <b style='color:#1f2937;'>City:</b> {city or "N/A"} | 🌍 <b style='color:#1f2937;'>Country:</b> {country or "N/A"}  
                    <br>☎️ <b style='color:#1f2937;'>Phone:</b> {phone or "N/A"}  
                    <br>📧 <b style='color:#1f2937;'>Email:</b> {email or "N/A"}  
                    <br>⭐ <b style='color:#1f2937;'>Rating & Reviews:</b> {rating or "N/A"} 
                    <br>🗺️ <b style='color:#1f2937;'>Google Maps:</b> {maps_display} 
                    <br><b style='color:#1f2937;'>Status:</b> <span style='font-weight:600;color:{border_color};'>{status_icon}</span>
                </div>
            </div>
            """, unsafe_allow_html=True)
        save_chat_memory()

    # -------------------
    # TTS
    # -------------------
    def _create_voice_player(self, text: str, idx: str = None):
        """Render audio player for TTS with clean modern theme"""
        import streamlit.components.v1 as components
        import uuid

        if idx is None:
            idx = str(uuid.uuid4())

        html = f"""
        <div style="margin:8px 0; display:flex; gap:10px;">
            <button style="font-size:20px; padding:8px 14px; border-radius:10px; 
                           border:2px solid #e5e7eb; background:white; color:#1f2937;
                           cursor:pointer; transition: all 0.3s ease;
                           box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);"
                    onmouseover="this.style.background='#f9fafb'; this.style.boxShadow='0 4px 10px rgba(0, 0, 0, 0.1)'"
                    onmouseout="this.style.background='white'; this.style.boxShadow='0 2px 6px rgba(0, 0, 0, 0.06)'"
                    onclick="
                        (async () => {{
                            const resp = await fetch('/generate_tts', {{
                                method: 'POST',
                                headers: {{'Content-Type':'application/json'}},
                                body: JSON.stringify({{'text':'{text.replace("'", "\\'")}'}})
                            }});
                            const data = await resp.json();
                            const audio = new Audio('data:audio/mp3;base64,' + data.audio_b64);
                            audio.id = 'audio_{idx}';
                            audio.play();
                            window.audio_{idx} = audio;
                        }})();
                    ">🔊</button>
            <button style="font-size:20px; padding:8px 14px; border-radius:10px; 
                           border:2px solid #e5e7eb; background:#3b82f6; color:white;
                           cursor:pointer; transition: all 0.3s ease; font-weight:600;
                           box-shadow: 0 2px 6px rgba(59, 130, 246, 0.3);"
                    onmouseover="this.style.background='#2563eb'; this.style.boxShadow='0 4px 10px rgba(59, 130, 246, 0.4)'"
                    onmouseout="this.style.background='#3b82f6'; this.style.boxShadow='0 2px 6px rgba(59, 130, 246, 0.3)'"
                    onclick="if(window.audio_{idx}){{ window.audio_{idx}.currentTime=0; window.audio_{idx}.play(); }}">🔄</button>
            <button style="font-size:20px; padding:8px 14px; border-radius:10px; 
                           border:2px solid #e5e7eb; background:white; color:#ef4444;
                           cursor:pointer; transition: all 0.3s ease; font-weight:600;
                           box-shadow: 0 2px 6px rgba(0, 0, 0, 0.06);"
                    onmouseover="this.style.background='#fef2f2'; this.style.borderColor='#fca5a5'"
                    onmouseout="this.style.background='white'; this.style.borderColor='#e5e7eb'"
                    onclick="if(window.audio_{idx}){{ window.audio_{idx}.pause(); }}">⏹️</button>
        </div>
        """
        components.html(html, height=60)

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