"""
LangGraph Chat Flow Module
Implements the conversation flow using LangGraph state machine
"""

from typing import TypedDict, Optional, List, Dict
from langgraph.graph import StateGraph, START, END
import logging

logger = logging.getLogger(__name__)


# -----------------------------
# State Definition
# -----------------------------
class GraphState(TypedDict):
    """State schema for chat graph"""
    # Required fields
    user_input: str
    language: str
    
    # Optional fields
    intent: Optional[str]
    intent_confidence: Optional[float]
    intent_reasoning: Optional[str]
    is_vague: Optional[bool]
    sql_query: Optional[str]
    sql_params: Optional[Dict]
    sql_query_type: Optional[str]
    sql_filters: Optional[List[str]]
    sql_explanation: Optional[str]
    sql_error: Optional[str]
    result_rows: Optional[List[Dict]]
    columns: Optional[List[str]]
    row_count: Optional[int]
    summary: Optional[str]
    key_insights: Optional[List[str]]
    authorized_count: Optional[int]
    top_locations: Optional[List[str]]
    greeting_text: Optional[str]
    general_answer: Optional[str]
    needs_info: Optional[str]  # Add this field


# -----------------------------
# Chat Graph
# -----------------------------
class ChatGraph:
    """Manages the conversational flow using LangGraph"""
    
    def __init__(self, db_manager, llm_manager):
        """Initialize with database and LLM managers"""
        self.db = db_manager
        self.llm = llm_manager
        self.graph = self._build_graph()
    
    def _build_graph(self):
        """Build and compile the LangGraph state machine"""
        builder = StateGraph(GraphState)
        
        # Add nodes
        builder.add_node("detect_intent", self._node_detect_intent)
        builder.add_node("respond_greeting", self._node_respond_greeting)
        builder.add_node("respond_general", self._node_respond_general)
        builder.add_node("needs_info", self._node_ask_for_more_info)  # Placeholder for future implementation
        builder.add_node("generate_sql", self._node_generate_sql)
        builder.add_node("execute_sql", self._node_execute_sql)
        builder.add_node("summarize_results", self._node_summarize_results)
        
        # Start with intent detection
        builder.add_edge(START, "detect_intent")
        
        # Conditional routing based on intent
        builder.add_conditional_edges(
            "detect_intent",
            self._route_by_intent,
            {
                "GREETING": "respond_greeting",
                "GENERAL_HAJJ": "respond_general",
                "DATABASE": "generate_sql",
                "NEEDS_INFO": "needs_info"  # Placeholder for future node
            }
        )
        
        # Database flow
        builder.add_edge("generate_sql", "execute_sql")
        builder.add_edge("execute_sql", "summarize_results")
        builder.add_edge("summarize_results", END)
        
        # Other branches terminate
        builder.add_edge("respond_greeting", END)
        builder.add_edge("respond_general", END)
        builder.add_edge("needs_info", END)
        
        return builder.compile()
    
    # -----------------------------
    # Routing Logic
    # -----------------------------
    @staticmethod
    def _route_by_intent(state: GraphState) -> str:
        """Route to next node based on detected intent"""
        return state.get("intent", "GENERAL_HAJJ")
    
    # -----------------------------
    # Node Implementations
    # -----------------------------
    def _node_detect_intent(self, state: GraphState) -> dict:
        """Detect user intent with structured output"""
        user_input = state["user_input"]
        language = state["language"]
        
        intent_result = self.llm.detect_intent(user_input, language)
        
        return {
            "intent": intent_result["intent"],
            "intent_confidence": intent_result["confidence"],
            "intent_reasoning": intent_result["reasoning"],
            "is_vague": self._is_vague_input(user_input)
        }
    
    def _node_respond_greeting(self, state: GraphState) -> dict:
        """Generate greeting response"""
        greeting = self.llm.generate_greeting(
            state["user_input"],
            state["language"]
        )
        return {"greeting_text": greeting}
    def _node_ask_for_more_info(self, state: GraphState) -> dict:
        """Handle cases where more information is needed"""
        response = self.llm.ask_for_more_info(
            state["user_input"],
            state["language"]
        )
        
        # Ensure we return all expected fields
        return {
            "needs_info": response.get("needs_info"),
            "suggestions": response.get("suggestions", []),
            "missing_info": response.get("missing_info", []),
            "sample_query": response.get("sample_query"),
            "summary": None,
            "result_rows": []
        }
    def _node_respond_general(self, state: GraphState) -> dict:
        """Generate general Hajj answer"""
        answer = self.llm.generate_general_answer(
            state["user_input"],
            state["language"]
        )
        return {"general_answer": answer}
    
    def _node_generate_sql(self, state: GraphState) -> dict:
        """Generate SQL query from user input with structured output"""
        user_input = state["user_input"]
        language = state["language"]
        
        # Try LLM-generated SQL first
        sql_result = self.llm.generate_sql(user_input, language)
        
        if sql_result:
            return {
                "sql_query": sql_result["sql_query"],
                "sql_query_type": sql_result["query_type"],
                "sql_filters": sql_result["filters"],
                "sql_explanation": sql_result["explanation"],
                "sql_params": None
            }
        
        # Fallback to heuristic queries
        sql_query, params = self.db.get_heuristic_query(user_input)
        
        if sql_query:
            return {
                "sql_query": sql_query,
                "sql_query_type": "heuristic",
                "sql_filters": ["heuristic pattern match"],
                "sql_explanation": "Generated using pattern matching",
                "sql_params": params
            }
        
        return {
            "sql_query": None,
            "sql_query_type": "no_sql",
            "sql_filters": [],
            "sql_explanation": "Could not generate safe SQL query",
            "sql_params": None
        }
    
    def _node_execute_sql(self, state: GraphState) -> dict:
        """Execute SQL query"""
        sql_query = state.get("sql_query")
        params = state.get("sql_params")
        
        if not sql_query:
            return {
                "sql_error": "No SQL query generated",
                "result_rows": [],
                "row_count": 0
            }
        
        df, error = self.db.execute_query(sql_query, params)
        
        if error:
            return {
                "sql_error": error,
                "result_rows": [],
                "row_count": 0
            }
        
        if df is not None:
            return {
                "result_rows": df.to_dict(orient="records"),
                "columns": list(df.columns),
                "row_count": len(df)
            }
        
        return {
            "result_rows": [],
            "row_count": 0
        }
    
    def _node_summarize_results(self, state: GraphState) -> dict:
        """Generate summary of query results with structured output"""
        row_count = state.get("row_count", 0)
        rows = state.get("result_rows", [])
        
        summary_result = self.llm.generate_summary(
            state["user_input"],
            state["language"],
            row_count,
            rows
        )
        
        return {
            "summary": summary_result["summary"],
            "key_insights": summary_result["key_insights"],
            "authorized_count": summary_result["authorized_count"],
            "top_locations": summary_result["top_locations"]
        }
    
    # -----------------------------
    # Helper Methods
    # -----------------------------
    @staticmethod
    def _is_vague_input(user_input: str) -> bool:
        """Check if input is too vague for SQL generation"""
        keywords = ["agency", "company", "office", "وكالة", "شركة"]
        stripped = user_input.lower().strip()
        
        if len(stripped.split()) < 3 and any(k in stripped for k in keywords):
            return True
        return False
    
    def process(self, user_input: str, language: str) -> GraphState:
        """
        Process user input through the graph
        
        Args:
            user_input: User's question
            language: Current language (English or العربية)
        
        Returns:
            Final state after processing
        """
        initial_state: GraphState = {
            "user_input": user_input,
            "language": language,
            "intent": None,
            "intent_confidence": None,
            "intent_reasoning": None,
            "is_vague": None,
            "sql_query": None,
            "sql_params": None,
            "sql_query_type": None,
            "sql_filters": None,
            "sql_explanation": None,
            "sql_error": None,
            "result_rows": None,
            "columns": None,
            "row_count": None,
            "summary": None,
            "key_insights": None,
            "authorized_count": None,
            "top_locations": None,
            "greeting_text": None,
            "general_answer": None
        }
        
        try:
            final_state = self.graph.invoke(initial_state)
            return final_state
        except Exception as e:
            logger.error(f"Graph processing failed: {e}")
            return {
                **initial_state,
                "general_answer": f"Error processing request: {str(e)}"
            }
