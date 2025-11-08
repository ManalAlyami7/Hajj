"""
Memory Management Module
Handles conversation memory for voice assistant
"""
import logging
from datetime import datetime
import streamlit as st

logger = logging.getLogger(__name__)


class ConversationMemory:
    """Manages conversation memory for voice assistant"""
    
    def __init__(self, max_turns=10):
        """
        Initialize memory
        max_turns: Maximum number of conversation turns to remember (user+assistant = 1 turn)
        """
        self.max_turns = max_turns
        if 'voice_memory' not in st.session_state:
            st.session_state.voice_memory = {
                'messages': [],  # List of {role, content, timestamp}
                'user_context': {},  # Persistent user context (agencies mentioned, locations, etc.)
                'session_start': datetime.now().isoformat()
            }
    
    def add_message(self, role: str, content: str):
        """Add a message to memory"""
        message = {
            'role': role,  # 'user' or 'assistant'
            'content': content,
            'timestamp': datetime.now().isoformat()
        }
        st.session_state.voice_memory['messages'].append(message)
        
        # Trim to max_turns (keep most recent)
        # Each turn = user message + assistant message = 2 messages
        max_messages = self.max_turns * 2
        if len(st.session_state.voice_memory['messages']) > max_messages:
            st.session_state.voice_memory['messages'] = \
                st.session_state.voice_memory['messages'][-max_messages:]
        
        logger.info(f"Added {role} message to memory. Total messages: {len(st.session_state.voice_memory['messages'])}")
    
    def get_conversation_history(self, limit=None):
        """
        Get conversation history
        limit: Number of recent turns to retrieve (None = all)
        """
        messages = st.session_state.voice_memory['messages']
        if limit:
            messages = messages[-(limit * 2):]  # limit turns * 2 messages per turn
        return messages
    
    def get_formatted_history(self, limit=5):
        """Get formatted history string for LLM context"""
        messages = self.get_conversation_history(limit)
        if not messages:
            return "No previous conversation."
        
        formatted = []
        for msg in messages:
            role_label = "User" if msg['role'] == 'user' else "Assistant"
            formatted.append(f"{role_label}: {msg['content']}")
        
        return "\n".join(formatted)
    
    def update_context(self, key: str, value: any):
        """Update persistent user context"""
        st.session_state.voice_memory['user_context'][key] = value
        logger.info(f"Updated context: {key} = {value}")
    
    def get_context(self, key: str, default=None):
        """Get value from persistent context"""
        return st.session_state.voice_memory['user_context'].get(key, default)
    
    def extract_entities(self, text: str):
        """
        Extract and store important entities from user input
        (agencies mentioned, locations, etc.)
        """
        import re
        
        # Extract agency names (simple pattern - improve as needed)
        agencies = re.findall(r'(?:agency|company|office)\s+([A-Z][A-Za-z\s]+)', text, re.IGNORECASE)
        if agencies:
            self.update_context('last_agency_mentioned', agencies[0].strip())
        
        # Extract locations (simple pattern)
        locations = re.findall(r'(?:in|at|from)\s+([A-Z][a-z]+(?:\s+[A-Z][a-z]+)?)', text)
        if locations:
            self.update_context('last_location_mentioned', locations[0].strip())
    
    def clear_memory(self):
        """Clear all memory (useful for new session)"""
        st.session_state.voice_memory = {
            'messages': [],
            'user_context': {},
            'session_start': datetime.now().isoformat()
        }
        logger.info("Memory cleared")
    
    def get_memory_summary(self):
        """Get a summary of current memory state"""
        return {
            'total_messages': len(st.session_state.voice_memory['messages']),
            'session_duration': self._get_session_duration(),
            'context': st.session_state.voice_memory['user_context']
        }
    
    def _get_session_duration(self):
        """Calculate session duration"""
        start = datetime.fromisoformat(st.session_state.voice_memory['session_start'])
        duration = datetime.now() - start
        minutes = int(duration.total_seconds() / 60)
        return f"{minutes} min"