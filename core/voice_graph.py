"""
Voice Graph Module - FIXED
LangGraph workflow for voice assistant interactions
"""

from typing import Dict, Optional, TypedDict, Annotated, Literal, List
from langgraph.graph import StateGraph, END
import operator
import logging

logger = logging.getLogger(__name__)

from core.graph import ChatGraph
from core.voice_processor import VoiceProcessor
from core.llm import LLMManager
from core.database import DatabaseManager



# -----------------------------
# State Definition
# -----------------------------
class VoiceAssistantState(TypedDict):
    """Enhanced state for voice assistant workflow"""
    # Input
    audio_bytes: bytes

    # Transcription
    transcript: str
    detected_language: str
    transcription_confidence: float

    # Intent
    user_input: str
    intent: str
    intent_confidence: float
    intent_reasoning: str
    is_arabic: bool
    urgency: str

    # Response
    response: str
    response_tone: str
    key_points: List[str]
    suggested_actions: List[str]
    includes_warning: bool
    verification_steps: List[str]
    official_sources: List[str]
# --- Required fields ---

    user_input: str
    language: str

    # --- Intent understanding ---
    intent: Optional[str]
    intent_confidence: Optional[float]
    intent_reasoning: Optional[str]
    is_vague: Optional[bool]

    # --- SQL / Database-related fields ---
    sql_query: Optional[str]
    sql_params: Optional[Dict]
    sql_query_type: Optional[str]
    sql_filters: Optional[List[str]]
    sql_explanation: Optional[str]
    sql_error: Optional[str]
    result_rows: Optional[List[Dict]]
    columns: Optional[List[str]]
    row_count: Optional[int]

    # --- Generated content ---
    summary: Optional[str]
    greeting_text: Optional[str]
    general_answer: Optional[str]
    needs_ifo: Optional[str]
    suggestions: Optional[List[str]]
    missing_info: Optional[List[str]]
    sample_query: Optional[str]

    # --- Interaction / reasoning support ---
    
    # Audio output
    response_audio: bytes

    # Error handling
    error: str

    # Context
    messages_history: Annotated[list, operator.add]


# -----------------------------
# Voice Graph Builder
# -----------------------------
class VoiceGraphBuilder:
    """Builds LangGraph workflow for voice assistant"""

    def __init__(self, voice_processor):

        self.processor = voice_processor
        self.llm = LLMManager()
        self.db_manager = DatabaseManager()
        self.graph = ChatGraph(self.db_manager, self.llm)

    # -----------------------------
    # Node Functions
    # -----------------------------

    def transcribe_audio_node(self, state: VoiceAssistantState) -> VoiceAssistantState:
        """Node: Transcribe audio to text"""
        try:
            logger.info("Transcribing audio input")
            result = self.processor.transcribe_audio(state["audio_bytes"])

            if "error" in result:
                state["error"] = result["error"]
                state["user_input"] = ""
                state["transcript"] = ""
            else:
                state["transcript"] = result["text"]
                state["user_input"] = result["text"]
                state["detected_language"] = result["language"]
                state["transcription_confidence"] = result["confidence"]

        except Exception as e:
            error_msg = f"Transcription node error: {str(e)}"
            logger.error(error_msg)
            state["error"] = error_msg
            state["user_input"] = ""
            state["transcript"] = ""

        return state

    def detect_intent_node(self, state: VoiceAssistantState) -> VoiceAssistantState:
        """Node: Detect intent"""
        logger.info("Detecting intent from user input")
        state['user_input'] = state.get('transcript', '')
        state['language'] = state.get('detected_language', 'en')
        return self.graph._node_detect_intent(state)

    def handle_greeting_node(self, state: VoiceAssistantState) -> VoiceAssistantState:
        """Node: Greeting response"""
        logger.info("Handling greeting intent")
        state['user_input'] = state.get('transcript', '')
        state['language'] = state.get('detected_language', 'en')
        return self.graph._node_respond_greeting(state)

    def generate_sql_node(self, state: VoiceAssistantState) -> VoiceAssistantState:
        logger.info("Generating SQL query from user input")
        """Node: Generate SQL query"""
        state['user_input'] = state.get('transcript', '')
        state['language'] = state.get('detected_language', 'en')
        return self.graph._node_generate_sql(state)
    
    def generate_ask_for_info_node(self, state: VoiceAssistantState) -> VoiceAssistantState:
        """Node: Generate ask for more info"""
        logger.info("Generating ask for more info from user input")
        state['user_input'] = state.get('transcript', '')
        state['language'] = state.get('detected_language', 'en')
        return self.graph._node_ask_for_more_info(state)

    def execute_sql_node(self, state: VoiceAssistantState) -> VoiceAssistantState:
        """Node: Execute SQL query"""
        logger.info("Executing SQL query")
        state['sql_params'] = state.get('sql_params', {})
        state['sql_query'] = state.get('sql_query', '')
        return self.graph._node_execute_sql(state)

    def summary_node(self, state: VoiceAssistantState) -> VoiceAssistantState:
        """Node: Summarize SQL results"""
        logger.info("Summarizing SQL results")
        state['result_rows'] = state.get('result_rows', [])
        state['columns'] = state.get('columns', [])
        return self.graph._node_summarize_results(state)

    def handle_general_hajj_node(self, state: VoiceAssistantState) -> VoiceAssistantState:
        logger.info("Handling general Hajj questions")
        """Node: Handle general questions"""
        state['user_input'] = state.get('transcript', '')
        state['language'] = state.get('detected_language', 'en')
        return self.graph._node_respond_general(state)

    def text_to_speech_node(self, state: VoiceAssistantState) -> VoiceAssistantState:
        logger.info("Converting text response to audio")
        """Node: Convert response text to audio"""
        try:
            logger.info("needs_info", state.get('need_info', None))
            
            state['response'] = (
                state.get('needs_info') or
                state.get('greeting_text')
                or state.get('summary')
                or state.get('general_answer')
                or "I'm here! How can I assist you today?"
            )

            audio_bytes = self.processor.text_to_speech(
                state.get("response", ""),
                state.get("detected_language", "en")
            )
            if audio_bytes:
                state["response_audio"] = audio_bytes
            else:
                logger.warning("TTS generation returned no audio")

        except Exception as e:
            logger.error(f"TTS node error: {e}")

        return state

    # -----------------------------
    # Router Function
    # -----------------------------
    @staticmethod
    def route_intent(state: VoiceAssistantState) -> Literal["respond_greeting", "generate_sql", "respond_general", "NEEDS_INFO"]:
        """Route based on detected intent"""
        intent = state.get("intent", "GENERAL_HAJJ")

        if intent == "GREETING":
            return "respond_greeting"
        elif intent == "DATABASE":
            return "generate_sql"
        elif intent == "GENERAL_HAJJ":
            return "respond_general"
        else:
            return "needs_info"

    # -----------------------------
    # Build Graph
    # -----------------------------
    def build(self):
        """Build and compile the voice assistant graph"""
        workflow = StateGraph(VoiceAssistantState)

        # Add nodes
        workflow.add_node("transcribe", self.transcribe_audio_node)
        workflow.add_node("detect_intent", self.detect_intent_node)
        workflow.add_node("respond_greeting", self.handle_greeting_node)
        workflow.add_node("respond_general", self.handle_general_hajj_node)
        workflow.add_node("generate_sql", self.generate_sql_node)
        workflow.add_node("execute_sql", self.execute_sql_node)
        workflow.add_node("needs_info", self.generate_ask_for_info_node)
        workflow.add_node("summarize_results", self.summary_node)
        workflow.add_node("tts", self.text_to_speech_node)

        # Define edges
        workflow.set_entry_point("transcribe")
        workflow.add_edge("transcribe", "detect_intent")

        workflow.add_conditional_edges(
            "detect_intent",
            self.route_intent,
            {
                "respond_greeting": "respond_greeting",
                "generate_sql": "generate_sql",
                "respond_general": "respond_general",
                "needs_info": "needs_info"

            }
        )

        # Database chain
        workflow.add_edge("generate_sql", "execute_sql")
        workflow.add_edge("execute_sql", "summarize_results")
        workflow.add_edge("summarize_results", "tts")

        # Greeting and general go straight to TTS
        workflow.add_edge("needs_info", "tts")
        workflow.add_edge("respond_greeting", "tts")
        workflow.add_edge("respond_general", "tts")

        workflow.add_edge("tts", END)

        return workflow.compile()
