"""
Voice Graph Module
LangGraph workflow for voice assistant interactions
"""

from typing import TypedDict, Annotated, Literal, List
from langgraph.graph import StateGraph, END
import operator
import logging

logger = logging.getLogger(__name__)


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
        """
        Initialize graph builder
        
        Args:
            voice_processor: VoiceProcessor instance
        """
        self.processor = voice_processor
    
    # -----------------------------
    # Node Functions
    # -----------------------------
    
    def transcribe_audio_node(self, state: VoiceAssistantState) -> VoiceAssistantState:
        """Node: Transcribe audio to text"""
        try:
            result = self.processor.transcribe_audio(state["audio_bytes"])
            
            if "error" in result:
                state["error"] = result["error"]
            else:
                state["transcript"] = result["text"]
                state["user_input"] = result["text"]
                state["detected_language"] = result["language"]
                state["transcription_confidence"] = result["confidence"]
                
        except Exception as e:
            error_msg = f"Transcription node error: {str(e)}"
            logger.error(error_msg)
            state["error"] = error_msg
        
        return state
    
    def detect_intent_node(self, state: VoiceAssistantState) -> VoiceAssistantState:
        """Node: Detect user intent with urgency"""
        try:
            result = self.processor.detect_voice_intent(
                state["user_input"],
                state.get("detected_language", "en")
            )
            
            state["intent"] = result["intent"]
            state["intent_confidence"] = result["confidence"]
            state["intent_reasoning"] = result["reasoning"]
            state["is_arabic"] = result["is_arabic"]
            state["urgency"] = result["urgency"]
            
        except Exception as e:
            error_msg = f"Intent detection node error: {str(e)}"
            logger.error(error_msg)
            state["error"] = error_msg
            state["intent"] = "GENERAL_HAJJ"
        
        return state
    
    def handle_greeting_node(self, state: VoiceAssistantState) -> VoiceAssistantState:
        """Node: Handle greeting intent"""
        try:
            result = self.processor.generate_voice_greeting(
                state["user_input"],
                state.get("is_arabic", False)
            )
            
            state["response"] = result["response"]
            state["response_tone"] = result["tone"]
            state["key_points"] = result["key_points"]
            state["suggested_actions"] = result["suggested_actions"]
            state["includes_warning"] = result["includes_warning"]
            state["verification_steps"] = []
            state["official_sources"] = []
            
        except Exception as e:
            logger.error(f"Greeting node error: {e}")
            state["response"] = (
                "السلام عليكم! 🌙 كيف يمكنني مساعدتك؟"
                if state.get("is_arabic")
                else "Hello! 👋 How can I assist you today?"
            )
            state["response_tone"] = "warm"
            state["key_points"] = []
            state["suggested_actions"] = []
        
        return state
    
    def handle_database_node(self, state: VoiceAssistantState) -> VoiceAssistantState:
        """Node: Handle database/verification queries"""
        try:
            result = self.processor.generate_database_response(
                state["user_input"],
                state.get("is_arabic", False)
            )
            
            state["response"] = result["response"]
            state["response_tone"] = result["tone"]
            state["verification_steps"] = result["verification_steps"]
            state["official_sources"] = result["official_sources"]
            state["includes_warning"] = True
            state["key_points"] = result["verification_steps"][:3]
            state["suggested_actions"] = ["Verify authorization", "Check official sources"]
            
        except Exception as e:
            logger.error(f"Database node error: {e}")
            state["response"] = "⚠️ Always verify Hajj agency authorization before booking!"
            state["response_tone"] = "urgent"
            state["verification_steps"] = ["Check official database", "Verify office location"]
            state["official_sources"] = ["Ministry of Hajj"]
        
        return state
    
    def handle_general_hajj_node(self, state: VoiceAssistantState) -> VoiceAssistantState:
        """Node: Handle general Hajj questions"""
        try:
            result = self.processor.generate_general_response(
                state["user_input"],
                state.get("is_arabic", False),
                state.get("messages_history", [])
            )
            
            state["response"] = result["response"]
            state["response_tone"] = result["tone"]
            state["key_points"] = result["key_points"]
            state["suggested_actions"] = result["suggested_actions"]
            state["includes_warning"] = result["includes_warning"]
            state["verification_steps"] = []
            state["official_sources"] = []
            
        except Exception as e:
            logger.error(f"General Hajj node error: {e}")
            state["response"] = "I'm here to help with Hajj information. Please ask your question."
            state["response_tone"] = "warm"
            state["key_points"] = []
            state["suggested_actions"] = []
        
        return state
    
    def text_to_speech_node(self, state: VoiceAssistantState) -> VoiceAssistantState:
        """Node: Convert response to speech"""
        try:
            audio_bytes = self.processor.text_to_speech(
                state["response"],
                state.get("detected_language", "en")
            )
            
            if audio_bytes:
                state["response_audio"] = audio_bytes
            else:
                state["error"] = "TTS generation failed"
                
        except Exception as e:
            error_msg = f"TTS node error: {str(e)}"
            logger.error(error_msg)
            state["error"] = error_msg
        
        return state
    
    # -----------------------------
    # Router Function
    # -----------------------------
    
    @staticmethod
    def route_intent(state: VoiceAssistantState) -> Literal["greeting", "database", "general_hajj"]:
        """Route based on detected intent"""
        intent = state.get("intent", "GENERAL_HAJJ")
        
        if intent == "GREETING":
            return "greeting"
        elif intent == "DATABASE":
            return "database"
        else:
            return "general_hajj"
    
    # -----------------------------
    # Build Graph
    # -----------------------------
    
    def build(self):
        """Build and compile the voice assistant graph"""
        workflow = StateGraph(VoiceAssistantState)
        
        # Add nodes
        workflow.add_node("transcribe", self.transcribe_audio_node)
        workflow.add_node("detect_intent", self.detect_intent_node)
        workflow.add_node("greeting", self.handle_greeting_node)
        workflow.add_node("database", self.handle_database_node)
        workflow.add_node("general_hajj", self.handle_general_hajj_node)
        workflow.add_node("tts", self.text_to_speech_node)
        
        # Define edges
        workflow.set_entry_point("transcribe")
        workflow.add_edge("transcribe", "detect_intent")
        
        # Conditional routing based on intent
        workflow.add_conditional_edges(
            "detect_intent",
            self.route_intent,
            {
                "greeting": "greeting",
                "database": "database",
                "general_hajj": "general_hajj"
            }
        )
        
        # All paths lead to TTS then END
        workflow.add_edge("greeting", "tts")
        workflow.add_edge("database", "tts")
        workflow.add_edge("general_hajj", "tts")
        workflow.add_edge("tts", END)
        
        return workflow.compile()
