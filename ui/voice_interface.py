"""
Voice Interface Module
UI components for real-time voice assistant
"""

import streamlit as st
from typing import Dict


class VoiceInterface:
    """Manages real-time voice assistant UI components"""
    
    @staticmethod
    def render_status_indicator(status: str, is_recording: bool = False, is_speaking: bool = False):
        """
        Render floating status indicator
        
        Args:
            status: Current status text
            is_recording: Recording state
            is_speaking: Speaking state
        """
        dot_class = ""
        if is_recording:
            dot_class = "listening"
        elif is_speaking:
            dot_class = "speaking"
        
        st.markdown(f"""
        <div class="status-indicator">
            <div class="status-dot {dot_class}"></div>
            <span>{status}</span>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_live_transcript(transcript: str, is_active: bool = False):
        """
        Render live transcript panel
        
        Args:
            transcript: Current transcript text
            is_active: Whether currently recording/transcribing
        """
        badge_class = "active" if is_active else ""
        text_class = "empty" if not transcript else ""
        display_text = transcript if transcript else "Speak now..."
        badge_text = "● Listening" if is_active else "○ Ready"
        
        st.markdown(f"""
        <div class="transcript-container">
            <div class="panel-header">
                <div class="panel-icon">🎤</div>
                <h3 class="panel-title">Live Transcript</h3>
                <div class="panel-badge {badge_class}">{badge_text}</div>
            </div>
            <div class="transcript-text {text_class}">{display_text}</div>
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def render_live_response(
        response: str, 
        metadata: Dict = None, 
        is_speaking: bool = False
    ):
        """
        Render live response panel with metadata
        
        Args:
            response: Response text
            metadata: Response metadata (key_points, actions, etc.)
            is_speaking: Whether currently speaking
        """
        badge_class = "active" if is_speaking else ""
        text_class = "empty" if not response else ""
        display_text = response if response else "Response will appear here..."
        badge_text = "● Speaking" if is_speaking else "○ Ready"
        
        # Build metadata HTML
        metadata_html = VoiceInterface._build_metadata_html(metadata or {})
        
        st.markdown(f"""
        <div class="response-container">
            <div class="panel-header">
                <div class="panel-icon">🤖</div>
                <h3 class="panel-title">AI Response</h3>
                <div class="panel-badge {badge_class}">{badge_text}</div>
            </div>
            <div class="response-content {text_class}">{display_text}</div>
            {metadata_html}
        </div>
        """, unsafe_allow_html=True)
    
    @staticmethod
    def _build_metadata_html(metadata: Dict) -> str:
        """Build HTML for metadata cards"""
        html_parts = []
        
        # Key Points
        if metadata.get("key_points"):
            points_html = "".join([f"<li>{point}</li>" for point in metadata["key_points"]])
            html_parts.append(f"""
            <div class="metadata-card">
                <div class="metadata-title">💡 Key Points</div>
                <ul class="metadata-list">{points_html}</ul>
            </div>
            """)
        
        # Suggested Actions
        if metadata.get("suggested_actions"):
            actions_html = "".join([f"<li>{action}</li>" for action in metadata["suggested_actions"]])
            html_parts.append(f"""
            <div class="metadata-card" style="border-left-color: #a78bfa;">
                <div class="metadata-title" style="color: #a78bfa;">✅ Suggested Actions</div>
                <ul class="metadata-list">{actions_html}</ul>
            </div>
            """)
        
        # Verification Steps
        if metadata.get("verification_steps"):
            steps_html = "".join([f"<li>{step}</li>" for step in metadata["verification_steps"]])
            html_parts.append(f"""
            <div class="metadata-card" style="border-left-color: #ef4444;">
                <div class="metadata-title" style="color: #ef4444;">⚠️ Verification Steps</div>
                <ul class="metadata-list">{steps_html}</ul>
            </div>
            """)
        
        return "".join(html_parts)
    
    @staticmethod
    def render_avatar(is_recording: bool = False, is_speaking: bool = False):
        """
        Render animated avatar with state
        
        Args:
            is_recording: Recording state
            is_speaking: Speaking state
        """
        avatar_class = ""
        if is_recording:
            avatar_class = "listening"
        elif is_speaking:
            avatar_class = "speaking"
        
        label = "🔴 Recording..." if is_recording else "🎤 Press to Speak"
        
        st.markdown(f"""
        <div class="voice-left">
            <div class="voice-avatar-container">
                <div class="voice-ring voice-ring-1"></div>
                <div class="voice-ring voice-ring-2"></div>
                <div class="voice-ring voice-ring-3"></div>
                <div class="voice-avatar {avatar_class}">🕋</div>
            </div>
            
            <div class="record-button-container">
                <div class="record-label">{label}</div>
            </div>
        </div>
        """, unsafe_allow_html=True)

class RealTimeVoiceStyles:
    """CSS styles for real-time voice interface"""
    
    @staticmethod
    def get_base_styles() -> str:
        return """
        .stApp {
            background: linear-gradient(135deg, #1e3c72 0%, #2a5298 50%, #7e22ce 100%);
            background-attachment: fixed;
            overflow: hidden;
        }
        
        #MainMenu {visibility: hidden;}
        footer {visibility: hidden;}
        header {visibility: hidden;}
        
        .main .block-container {
            padding: 2rem 1rem;
            max-width: 1200px;
            height: 90vh;
            overflow: hidden;
            display: flex;
            flex-direction: column;
            justify-content: center;
        }
        """

    @staticmethod
    def get_avatar_styles() -> str:
        return """
        .voice-avatar-container {
            position: relative;
            margin-bottom: 1rem;
            display: flex;
            justify-content: center;
            align-items: center;
        }
        
        .voice-avatar {
            width: 120px;
            height: 120px;
            background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
            border-radius: 50%;
            display: flex;
            justify-content: center;
            align-items: center;
            font-size: 60px;
            position: relative;
            z-index: 2;
            border: 5px solid rgba(255, 255, 255, 0.3);
            transition: all 0.3s ease;
        }
        
        .voice-avatar.listening {
            border-color: #ef4444;
            box-shadow: 0 0 30px rgba(239, 68, 68, 0.5);
        }
        
        .voice-avatar.speaking {
            border-color: #3b82f6;
            box-shadow: 0 0 30px rgba(59, 130, 246, 0.5);
        }
        """

    @staticmethod
    def get_panel_styles() -> str:
        return """
        .transcript-container, .response-container {
            background: rgba(255, 255, 255, 0.1);
            backdrop-filter: blur(10px);
            border-radius: 1rem;
            padding: 1rem;
            margin-bottom: 1rem;
            border: 1px solid rgba(255, 255, 255, 0.1);
        }
        
        .panel-header {
            display: flex;
            align-items: center;
            margin-bottom: 0.5rem;
        }
        
        .panel-icon {
            font-size: 1.5rem;
            margin-right: 0.5rem;
        }
        
        .panel-title {
            color: white;
            margin: 0;
            flex-grow: 1;
        }
        
        .panel-badge {
            background: rgba(255, 255, 255, 0.2);
            padding: 0.25rem 0.75rem;
            border-radius: 1rem;
            font-size: 0.8rem;
            color: white;
        }
        
        .panel-badge.active {
            background: #ef4444;
        }
        """

    @staticmethod
    def get_styles() -> str:
        """Return complete CSS for real-time voice interface"""
        return f"""
        <style>
        {RealTimeVoiceStyles.get_base_styles()}
        {RealTimeVoiceStyles.get_avatar_styles()}
        {RealTimeVoiceStyles.get_panel_styles()}
        </style>
        """