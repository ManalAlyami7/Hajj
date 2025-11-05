"""
State Management Module
Handles session state initialization and persistence
"""

import streamlit as st
import json
import os
from datetime import datetime
import pytz
from typing import List, Dict


def initialize_session_state():
    """Initialize all session state variables"""
    
    # Language
    if "language" not in st.session_state:
        st.session_state.language = "English"
    
    # Chat memory
    if "chat_memory" not in st.session_state:
        st.session_state.chat_memory = load_chat_memory()
        
        # Add welcome message if empty
        if not st.session_state.chat_memory:
            from utils.translations import t
            st.session_state.chat_memory = [{
                "role": "assistant",
                "content": t("welcome_msg", st.session_state.language),
                "timestamp": get_current_time()
            }]
            save_chat_memory()
    
    # Last result dataframe
    if "last_result_df" not in st.session_state:
        st.session_state.last_result_df = None
    
    # Pending example flag - CRITICAL for sidebar examples
    if "pending_example" not in st.session_state:
        st.session_state.pending_example = False
    
    # Selected question from examples (legacy - kept for compatibility)
    if "selected_question" not in st.session_state:
        st.session_state.selected_question = None
    
    # Submit example flag (legacy - kept for compatibility)
    if "submit_example" not in st.session_state:
        st.session_state.submit_example = False
    
    # OpenAI client cache
    if "openai_client" not in st.session_state:
        st.session_state.openai_client = None


def load_chat_memory() -> List[Dict]:
    """
    Load chat history from file if it exists
    
    Returns:
        List of chat messages
    """
    chat_file = "chat_history.json"
    
    if not os.path.exists(chat_file):
        return []
    
    try:
        with open(chat_file, "r", encoding="utf-8") as f:
            data = json.load(f)
            
            # Validate structure
            if isinstance(data, list):
                # Remove any messages with non-serializable data
                cleaned_data = []
                for msg in data:
                    if isinstance(msg, dict) and "role" in msg and "content" in msg:
                        # Remove dataframe objects, keep result_data
                        if "dataframe" in msg:
                            del msg["dataframe"]
                        cleaned_data.append(msg)
                
                return cleaned_data
            
    except (json.JSONDecodeError, IOError) as e:
        print(f"Error loading chat history: {e}")
    
    return []


def save_chat_memory():
    """
    Save chat history to file
    Handles serialization of complex objects
    """
    chat_file = "chat_history.json"
    
    try:
        # Create a serializable copy of chat memory
        serializable_memory = []
        
        for msg in st.session_state.chat_memory:
            msg_copy = {
                "role": msg.get("role"),
                "content": msg.get("content"),
                "timestamp": msg.get("timestamp")
            }
            
            # Include result_data if present (already serializable)
            if "result_data" in msg:
                msg_copy["result_data"] = msg["result_data"]
            
            serializable_memory.append(msg_copy)
        
        with open(chat_file, "w", encoding="utf-8") as f:
            json.dump(serializable_memory, f, ensure_ascii=False, indent=2)
            
    except (IOError, TypeError) as e:
        print(f"Error saving chat history: {e}")


def clear_chat_memory():
    """Clear chat memory and reset to welcome message"""
    from utils.translations import t
    
    st.session_state.chat_memory = [{
        "role": "assistant",
        "content": t("welcome_msg", st.session_state.language),
        "timestamp": get_current_time()
    }]
    
    st.session_state.last_result_df = None
    st.session_state.pending_example = False  # Reset the flag
    save_chat_memory()


def get_current_time() -> float:
    """
    Get current timestamp in Riyadh timezone
    
    Returns:
        Timestamp as float
    """
    riyadh_tz = pytz.timezone('Asia/Riyadh')
    return datetime.now(riyadh_tz).timestamp()


def format_time(timestamp: float) -> str:
    """
    Format timestamp to readable time in Riyadh timezone
    
    Args:
        timestamp: Unix timestamp
    
    Returns:
        Formatted time string
    """
    riyadh_tz = pytz.timezone('Asia/Riyadh')
    dt = datetime.fromtimestamp(timestamp, riyadh_tz)
    return dt.strftime("%I:%M %p")


def get_session_info() -> Dict:
    """
    Get information about current session
    
    Returns:
        Dictionary with session info
    """
    return {
        "language": st.session_state.get("language", "English"),
        "message_count": len(st.session_state.get("chat_memory", [])),
        "has_results": st.session_state.get("last_result_df") is not None,
        "pending_example": st.session_state.get("pending_example", False)
    }