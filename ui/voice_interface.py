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
    def get_styles() -> str:
        """Return complete CSS for real-time voice interface"""
        return """
<style>
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

    .header-container {
        text-align: center;
        padding: 1rem 0;
        margin-bottom: 1rem;
    }

    .title {
        color: white;
        font-size: 2.5rem;
        font-weight: 800;
        margin-bottom: 0.3rem;
        text-shadow: 0 4px 20px rgba(0, 0, 0, 0.3);
        letter-spacing: 1px;
    }

    .subtitle {
        color: rgba(255, 255, 255, 0.9);
        font-size: 1.1rem;
        margin-bottom: 0.3rem;
        font-weight: 500;
    }

    .powered-by {
        color: rgba(255, 255, 255, 0.7);
        font-size: 0.85rem;
        margin-top: 0.3rem;
    }

    .avatar-section {
        display: flex;
        flex-direction: column;
        align-items: center;
        margin: 1rem auto;
        padding: 1.5rem;
        background: rgba(255, 255, 255, 0.05);
        border-radius: 2rem;
        backdrop-filter: blur(20px);
        box-shadow: 0 8px 32px rgba(0, 0, 0, 0.2);
        border: 1px solid rgba(255, 255, 255, 0.1);
    }

    .avatar-container {
        position: relative;
        margin-bottom: 1rem;
    }
    
    .avatar {
        width: 160px;
        height: 160px;
        background: linear-gradient(135deg, #ffffff 0%, #f0f0f0 100%);
        border-radius: 50%;
        display: flex;
        justify-content: center;
        align-items: center;
        font-size: 80px;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.4);
        animation: pulse 2s ease-in-out infinite;
        position: relative;
        z-index: 2;
        border: 5px solid rgba(255, 255, 255, 0.3);
    }
    
    .ring {
        position: absolute;
        border: 3px solid rgba(255, 255, 255, 0.2);
        border-radius: 50%;
        animation: ripple 2.5s ease-out infinite;
    }
    
    .ring-1 { width: 180px; height: 180px; animation-delay: 0s; }
    .ring-2 { width: 220px; height: 220px; animation-delay: 0.7s; }
    .ring-3 { width: 260px; height: 260px; animation-delay: 1.4s; }
    
    .avatar.active {
        animation: pulse-active 0.6s ease-in-out infinite;
        box-shadow: 0 25px 80px rgba(126, 34, 206, 0.6);
        border-color: rgba(255, 255, 255, 0.6);
    }
    
    @keyframes pulse {
        0%, 100% { transform: scale(1); }
        50% { transform: scale(1.03); }
    }
    
    @keyframes pulse-active {
        0%, 100% { transform: scale(1); box-shadow: 0 25px 80px rgba(126, 34, 206, 0.6); }
        50% { transform: scale(1.1); box-shadow: 0 30px 100px rgba(126, 34, 206, 0.9); }
    }
    
    @keyframes ripple {
        0% { transform: scale(0.95); opacity: 0.8; }
        100% { transform: scale(1.6); opacity: 0; }
    }

    .status-badge {
        display: inline-block;
        padding: 0.7rem 1.8rem;
        background: rgba(255, 255, 255, 0.15);
        border-radius: 2rem;
        color: white;
        font-weight: 600;
        font-size: 1rem;
        margin-bottom: 1rem;
        backdrop-filter: blur(10px);
        border: 1px solid rgba(255, 255, 255, 0.2);
        box-shadow: 0 4px 15px rgba(0, 0, 0, 0.2);
    }

    .status-badge.listening {
        background: linear-gradient(135deg, #ef4444 0%, #dc2626 100%);
        animation: glow 1.5s ease-in-out infinite;
    }

    @keyframes glow {
        0%, 100% { box-shadow: 0 0 20px rgba(239, 68, 68, 0.5); }
        50% { box-shadow: 0 0 40px rgba(239, 68, 68, 0.8); }
    }

    .toast-notification {
        position: fixed;
        top: 50%;
        left: 50%;
        transform: translate(-50%, -50%);
        background: rgba(255, 255, 255, 0.95);
        padding: 2rem;
        border-radius: 2rem;
        box-shadow: 0 20px 60px rgba(0, 0, 0, 0.3);
        z-index: 9999;
        max-width: 700px;
        width: 90%;
        animation: toastFadeIn 0.5s ease-out;
    }

    .toast-notification.fade-out {
        animation: toastFadeOut 0.5s ease-out forwards;
    }

    @keyframes toastFadeIn {
        from { opacity: 0; transform: translate(-50%, -60%); }
        to { opacity: 1; transform: translate(-50%, -50%); }
    }

    @keyframes toastFadeOut {
        from { opacity: 1; transform: translate(-50%, -50%); }
        to { opacity: 0; transform: translate(-50%, -60%); }
    }

    .toast-header {
        display: flex;
        align-items: center;
        margin-bottom: 1rem;
        padding-bottom: 1rem;
        border-bottom: 2px solid #e5e7eb;
    }

    .toast-icon {
        font-size: 2.5rem;
        margin-right: 1rem;
    }

    .toast-title {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1a1a1a;
    }

    .toast-metadata {
        display: flex;
        gap: 0.5rem;
        margin-top: 0.5rem;
        flex-wrap: wrap;
    }

    .toast-badge {
        display: inline-block;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.75rem;
        font-weight: 600;
    }

    .toast-badge.intent { background: #7e22ce; color: white; }
    .toast-badge.confidence { background: #10b981; color: white; }
    .toast-badge.tone { background: #3b82f6; color: white; }
    .toast-badge.urgency { background: #f59e0b; color: white; }
    .toast-badge.urgency.high { background: #ef4444; color: white; }

    .toast-content {
        color: #374151;
        line-height: 1.6;
        font-size: 1rem;
    }

    .toast-transcript {
        background: #f3f4f6;
        padding: 1rem;
        border-radius: 1rem;
        margin: 1rem 0;
        font-style: italic;
        color: #4b5563;
    }

    .toast-response {
        margin-top: 1rem;
        padding: 1rem;
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border-radius: 1rem;
    }

    .toast-key-points {
        background: #fef3c7;
        padding: 1rem;
        border-radius: 1rem;
        margin-top: 1rem;
        border-left: 4px solid #f59e0b;
    }

    .toast-key-points h4 {
        margin: 0 0 0.5rem 0;
        color: #92400e;
        font-size: 0.9rem;
    }

    .toast-key-points ul {
        margin: 0;
        padding-left: 1.5rem;
        color: #78350f;
    }

    .toast-actions {
        background: #dbeafe;
        padding: 1rem;
        border-radius: 1rem;
        margin-top: 1rem;
        border-left: 4px solid #3b82f6;
    }

    .toast-actions h4 {
        margin: 0 0 0.5rem 0;
        color: #1e40af;
        font-size: 0.9rem;
    }

    .toast-actions ul {
        margin: 0;
        padding-left: 1.5rem;
        color: #1e3a8a;
    }

    .stButton > button {
        background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
        color: white;
        border: none;
        padding: 0.8rem 2rem;
        border-radius: 3rem;
        font-size: 1rem;
        font-weight: 600;
        cursor: pointer;
        transition: all 0.3s ease;
        box-shadow: 0 6px 20px rgba(102, 126, 234, 0.4);
        border: 2px solid transparent;
    }

    .stButton > button:hover {
        transform: translateY(-3px);
        box-shadow: 0 10px 30px rgba(102, 126, 234, 0.6);
        border-color: rgba(255, 255, 255, 0.3);
    }

    ::-webkit-scrollbar { display: none; }

    @media (max-width: 768px) {
        .title { font-size: 2rem; }
        .subtitle { font-size: 0.95rem; }
        .avatar { width: 120px; height: 120px; font-size: 60px; }
        .toast-notification { width: 95%; padding: 1.5rem; }
    }
</style>
"""
