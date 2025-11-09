"""
Professional Chat Interface Module
Enhanced with formal design, improved UX, and consistent branding
Fixed color scheme with proper contrast and visibility
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

    # -------------------
    # Public Render Method
    # -------------------
    def render(self):
        """Render professional chat interface"""
        self._inject_professional_styles()
        self._display_chat_history()
        
        if self._show_quick_actions():
            self._display_quick_actions()
        
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

        /* Action Buttons Container */
        .action-buttons-container {
            display: flex;
            gap: 12px;
            margin-top: 1.2rem;
            flex-wrap: wrap;
        }

        .action-btn {
            padding: 12px 20px;
            border-radius: 12px;
            border: 2px solid transparent;
            font-size: 0.95rem;
            font-weight: 700;
            cursor: pointer;
            transition: all 0.3s ease;
            box-shadow: var(--shadow-sm);
            display: inline-flex;
            align-items: center;
            gap: 8px;
            text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
        }

        .action-btn:hover {
            transform: translateY(-3px);
            box-shadow: var(--shadow-md);
        }

        .action-btn.primary {
            background: linear-gradient(135deg, #4a9eff 0%, #2563eb 100%);
            color: white;
            border-color: #2563eb;
        }

        .action-btn.primary:hover {
            background: linear-gradient(135deg, #2563eb 0%, #1d4ed8 100%);
        }

        .action-btn.success {
            background: linear-gradient(135deg, #22c55e 0%, #16a34a 100%);
            color: white;
            border-color: #16a34a;
        }

        .action-btn.success:hover {
            background: linear-gradient(135deg, #16a34a 0%, #15803d 100%);
        }

        .action-btn.danger {
            background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
            color: white;
            border-color: #dc2626;
        }

        .action-btn.danger:hover {
            background: linear-gradient(135deg, #dc2626 0%, #b91c1c 100%);
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
<<<<<<< HEAD
<<<<<<< HEAD
        """Display all messages in chat history with clean modern theme"""
        for idx, msg in enumerate(st.session_state.chat_memory):
            role = msg.get("role", "assistant")
            avatar = "🕋" if role == "assistant" else "👤"

            with st.chat_message(role, avatar=avatar):
                st.markdown(msg.get("content", ""), unsafe_allow_html=True)
=======
        """Display all messages in chat history with clean modern theme and copy button"""
=======
        """Display all messages with professional styling"""
>>>>>>> fb4da5c (Update chat and voice UI, and main app)
        for idx, msg in enumerate(st.session_state.chat_memory):
            role = msg.get("role", "assistant")
            avatar = "🕋" if role == "assistant" else "👤"
            content = msg.get("content", "")

            with st.chat_message(role, avatar=avatar):
                st.markdown(content, unsafe_allow_html=True)
>>>>>>> 6d085673f358d911d5b250454877f5c350067cb3

                if msg.get("timestamp"):
                    st.markdown(
                        f"<div class='message-timestamp'>🕐 {self._format_time(msg['timestamp'])}</div>",
                        unsafe_allow_html=True
                    )

<<<<<<< HEAD
<<<<<<< HEAD
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
=======
                # TTS and Copy buttons for assistant messages
=======
>>>>>>> fb4da5c (Update chat and voice UI, and main app)
                if role == "assistant":
                    self._render_action_buttons(content, idx)

    def _render_action_buttons(self, text: str, idx: int):
        """Render professional TTS and Copy buttons"""
        clean_text = self._clean_text_for_copy(text)
        
        html = f"""
        <div class="action-buttons-container">
            <button class="action-btn primary" onclick="playAudio_{idx}()">
                🔊 Play
            </button>
            
            <button class="action-btn primary" onclick="replayAudio_{idx}()">
                🔄 Replay
            </button>
            
            <button class="action-btn danger" onclick="stopAudio_{idx}()">
                ⏹️ Stop
            </button>
            
            <button class="action-btn success" onclick="copyText_{idx}()">
                📋 Copy
            </button>
        </div>
        
        <script>
            function playAudio_{idx}() {{
                fetch('/generate_tts', {{
                    method: 'POST',
                    headers: {{'Content-Type':'application/json'}},
                    body: JSON.stringify({{'text':'{text.replace("'", "\\'")}'}})
                }})
                .then(resp => resp.json())
                .then(data => {{
                    const audio = new Audio('data:audio/mp3;base64,' + data.audio_b64);
                    audio.id = 'audio_{idx}';
                    audio.play();
                    window.audio_{idx} = audio;
                }});
            }}
            
            function replayAudio_{idx}() {{
                if(window.audio_{idx}) {{
                    window.audio_{idx}.currentTime = 0;
                    window.audio_{idx}.play();
                }}
            }}
            
            function stopAudio_{idx}() {{
                if(window.audio_{idx}) {{
                    window.audio_{idx}.pause();
                }}
            }}
            
            function copyText_{idx}() {{
                const text = `{clean_text}`;
                navigator.clipboard.writeText(text).then(() => {{
                    showToast('✅ تم النسخ بنجاح! / Copied successfully!');
                }});
            }}
            
            function showToast(message) {{
                const toast = document.createElement('div');
                toast.className = 'toast-notification';
                toast.innerText = message;
                document.body.appendChild(toast);
                setTimeout(() => toast.remove(), 3000);
            }}
        </script>
        """
<<<<<<< HEAD
        components.html(html, height=70)
>>>>>>> 6d085673f358d911d5b250454877f5c350067cb3
=======
        components.html(html, height=80)

    def _clean_text_for_copy(self, text: str) -> str:
        """Clean text for clipboard copying"""
        clean = re.sub(r'<[^>]+>', '', text)
        clean = re.sub(r'\*\*([^\*]+)\*\*', r'\1', clean)
        clean = clean.replace("'", "\\'").replace('"', '\\"').replace('\n', '\\n')
        return clean
>>>>>>> fb4da5c (Update chat and voice UI, and main app)

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
<<<<<<< HEAD
        self._create_voice_player(info_request)  
=======
>>>>>>> 6d085673f358d911d5b250454877f5c350067cb3
        self._add_message("assistant", info_request)

    def _respond(self, content: str):
        st.markdown(content)
<<<<<<< HEAD
        self._create_voice_player(content)
=======
>>>>>>> 6d085673f358d911d5b250454877f5c350067cb3
        self._add_message("assistant", content)

    def _handle_database_results(self, state: dict):
        summary = state.get("summary", "")
        if summary:
            st.markdown(summary)
<<<<<<< HEAD
            self._create_voice_player(summary) 
=======
>>>>>>> 6d085673f358d911d5b250454877f5c350067cb3
            self._add_message("assistant", summary)
<<<<<<< HEAD
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
<<<<<<< HEAD

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
=======
>>>>>>> 6d085673f358d911d5b250454877f5c350067cb3
=======
>>>>>>> fb4da5c (Update chat and voice UI, and main app)

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