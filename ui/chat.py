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

  

# ...existing code...
    def _display_quick_actions(self):
        """Display quick action buttons at the start of chat (styled for all themes)"""
        lang = st.session_state.get("language", "English")

        # Title
        st.markdown(
            f"<h3 style='margin-bottom:8px;color:rgba(255,255,255,0.9);'>{t('quick_actions', lang)}</h3>",
            unsafe_allow_html=True
        )

        # Detect Streamlit theme preference
# ...existing code...
        # Detect Streamlit theme preference (safe fallback)
        theme_base = st.get_option("theme.base", "dark")  # 'dark' or 'light' (fallback 'dark')
        try:
            theme_base = st.get_option("theme.base")
            if not theme_base:
                theme_base = "dark"
        except Exception:
            theme_base = "dark"
# ...existing code...
        # Inject CSS once: style the Streamlit button element (.stButton > button)
        st.markdown(f"""
        <style>
        .quick-actions-row {{ display:flex; gap:12px; margin:12px 0; flex-wrap:wrap; }}
        .quick-action {{ display:inline-block; width:100% !important; }}
        .quick-action .icon {{ margin-right:8px; font-size:1.05rem; vertical-align:middle; }}
        .quick-action .label {{ vertical-align:middle; }}

        /* Style the actual Streamlit button element */
        .stButton>button {{
            width:100% !important;
            padding:12px 16px !important;
            border-radius:10px !important;
            font-weight:700 !important;
            cursor:pointer !important;
            border:none !important;
        }}
        /* Theme-specific adjustments */
        {" .stButton>button { background: linear-gradient(90deg, #4f46e5 0%, #7c3aed 100%); color:#fff; box-shadow:0 6px 18px rgba(124,58,237,0.18); }"
        if theme_base == "dark"
        else " .stButton>button { background: linear-gradient(90deg, #eef2ff 0%, #e9d5ff 100%); color:#111827; box-shadow:0 4px 10px rgba(17,24,39,0.06); }"}
        .stButton>button:hover {{ transform: translateY(-2px); }}
        </style>
        """, unsafe_allow_html=True)

        # Layout columns
        col1, col2 = st.columns(2)

        actions = [
            ("🔍", t("find_authorized", lang), "find_authorized", "user", t("show_authorized", lang)),
            ("📊", t("show_stats", lang), "show_stats", "user", t("hajj_statistics", lang)),
            ("🌍", t("find_by_country", lang), "find_by_country", "user", t("country_search", lang)),
            ("❓", t("general_help", lang), "general_help", "user", t("help_message", lang)),
        ]

        # First column
        with col1:
            st.markdown("<div class='quick-actions-row'>", unsafe_allow_html=True)
            for icon, label, key, role, content in actions[:2]:
                st.markdown("<div class='quick-action'>", unsafe_allow_html=True)
                if st.button(f"{icon}  {label}", key=f"qa_{key}", use_container_width=True):
                    self._add_message(role, content)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

        # Second column
        with col2:
            st.markdown("<div class='quick-actions-row'>", unsafe_allow_html=True)
            for icon, label, key, role, content in actions[2:]:
                st.markdown("<div class='quick-action'>", unsafe_allow_html=True)
                if st.button(f"{icon}  {label}", key=f"qa_{key}", use_container_width=True):
                    self._add_message(role, content)
                st.markdown("</div>", unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)
    # ...existing code...


    # Chat History Display
    # -------------------
    def _display_chat_history(self):
        """Display all messages in chat memory"""
        for idx, msg in enumerate(st.session_state.chat_memory):
            role = msg.get("role", "assistant")
            avatar = "🕋" if role == "assistant" else "👤"
            with st.chat_message(role, avatar=avatar):
                st.markdown(msg.get("content", ""), unsafe_allow_html=True)
                if msg.get("timestamp"):
                    st.markdown(f"<div style='color: #777; font-size:0.8rem'>🕐 {self._format_time(msg['timestamp'])}</div>", unsafe_allow_html=True)
                if role == "assistant":
                    tts_btn_key = f"tts_btn_{idx}"
                    if st.button("🔊 Listen", key=tts_btn_key):
                        self._create_voice_player(msg.get("content", "")[:4000], autoplay=True)
                if msg.get("result_data"):
                    self._display_results(msg["result_data"])

    # -------------------
    # User Input Handling
    # -------------------
    def _handle_user_input(self):
        lang = st.session_state.get("language", "English")
        user_input = st.session_state.pop("selected_question", None) or st.chat_input(t("input_placeholder", lang))
        if not user_input:
            return
        valid, err = validate_user_input(user_input)
        if not valid:
            st.error(f"❌ {err}")
            return
        self._add_message("user", user_input)
        with st.chat_message("user", avatar="👤"):
            st.markdown(user_input)
            st.markdown(f"<div style='color: #777; font-size:0.8rem'>🕐 {self._format_time(self._get_current_time())}</div>", unsafe_allow_html=True)
        # Process through graph
        with st.chat_message("assistant", avatar="🕋"):
            with st.spinner(t("thinking", lang)):
                final_state = self.graph.process(user_input, lang)
            self._handle_response(final_state)

    # -------------------
    # Response Handling
    # -------------------
    def _handle_response(self, state: dict):
        """Route response based on type"""
        if state.get("greeting_text"):
            self._respond(state["greeting_text"])
        elif state.get("general_answer"):
            self._respond(state["general_answer"])
        elif state.get("summary") or state.get("result_rows"):
            self._handle_database_results(state)
        else:
            err = t("general_error", st.session_state.get("language", "English"))
            st.error(err)
            self._add_message("assistant", err)

    def _respond(self, content: str):
        """Display assistant response with TTS"""
        st.markdown(content)
        if st.button("🔊 Listen",):
          self._create_voice_player(content, autoplay=True)
        self._add_message("assistant", content)

    # -------------------
    # Database Results Display
    # -------------------
    def _handle_database_results(self, state: dict):
        """Display structured DB results"""
        summary = state.get("summary", "")
        rows = state.get("result_rows", [])
        key_insights = state.get("key_insights", [])
        authorized_count = state.get("authorized_count")
        top_locations = state.get("top_locations", [])
        sql_explanation = state.get("sql_explanation")


        if summary:
            st.markdown(summary)
       
        if summary and st.button("🔊 Listen to Summary"):

             self._create_voice_player(summary, autoplay=True)
        if rows:
            df = pd.DataFrame(rows)
            self._display_results_summary(df)
            st.session_state.last_result_df = df
            result_data = {
                "rows": df.head(100).to_dict(orient="records"),
                "columns": list(df.columns),
                "total_rows": len(df),
                "key_insights": key_insights,
                "authorized_count": authorized_count,
                "top_locations": top_locations
            }
            self._add_message("assistant", summary, result_data=result_data)
        else:
            st.warning(summary)
            self._add_message("assistant", summary)

    def _display_results_summary(self, df: pd.DataFrame):
        """Show metrics badges for results"""
        col1, col2 = st.columns(2)
        with col1:
            st.markdown(f"<div style='display:inline-block;padding:6px;background:#667eea;color:white;border-radius:8px;'>📊 {t('results_badge', st.session_state.language, count=len(df))}</div>", unsafe_allow_html=True)
        if "is_authorized" in df.columns:
            auth_count = len(df[df["is_authorized"] == "Yes"])
            with col2:
                st.markdown(f"<div style='display:inline-block;padding:6px;background:#38ef7d;color:white;border-radius:8px;'>🔒 {t('authorized_badge', st.session_state.language, count=auth_count)}</div>", unsafe_allow_html=True)



    def _display_results(self, result_data: dict):
        """Render stored results in chat history (simple text list, no tables/cards)"""
        rows = result_data.get("rows", [])
        key_insights = result_data.get("key_insights", [])
        authorized_count = result_data.get("authorized_count")
        top_locations = result_data.get("top_locations", [])
        summary = result_data.get("summary", "")

        if not rows:
            st.warning("No results found.")
            return

        # ✅ Display summary text and voice option
        if summary:
            st.info(summary)
            if st.button("🔊 Listen to Summary", key=f"summary_{uuid.uuid4()}"):
                self._create_voice_player(summary, autoplay=True)

        # ✅ Display key insights if any
        if key_insights:
            st.markdown("### 🔍 Key Insights")
            for i, insight in enumerate(key_insights, start=1):
                st.markdown(f"- {insight}")

        # ✅ Authorized count & locations
        if authorized_count is not None:
            st.markdown(f"**Authorized Agencies:** {authorized_count}")
        if top_locations:
            st.markdown(f"**Top Locations:** {', '.join(top_locations)}")

        # ✅ Display each agency as plain text (no table)
        st.markdown("### 🏢 Agencies Found")
        for i, row in enumerate(rows, start=1):
            name_en = row.get("hajj_company_en", "N/A")
            name_ar = row.get("hajj_company_ar", "")
            city = row.get("city", "N/A")
            country = row.get("country", "N/A")
            email = row.get("email", "N/A")
            contact = row.get("contact_Info", "N/A")
            rating = row.get("rating_reviews", "N/A")
            authorized = row.get("is_authorized", "N/A")

            st.markdown(f"""
    **{i}. {name_en}**  
    {name_ar}  
    📍 *{city}, {country}*  
    📧 {email}  
    📞 {contact}  
    ⭐ {rating}  
    🔒 Authorized: {authorized}  
    ---
    """)





    # -------------------
    # TTS
    # -------------------
    def _create_voice_player(self, text: str, autoplay: bool = False):
        """Render hidden audio player for TTS"""
        try:
            audio_io = self.llm.text_to_speech(text, st.session_state.get("language", "English"))
            if audio_io is None: raise RuntimeError("No audio returned")
            audio_bytes = audio_io.getvalue() if hasattr(audio_io, "getvalue") else bytes(audio_io)
            b64 = base64.b64encode(audio_bytes).decode("ascii")
            st.markdown(f'<div style="display:none"><audio {"autoplay" if autoplay else ""} src="data:audio/mp3;base64,{b64}"></audio></div>', unsafe_allow_html=True)
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
