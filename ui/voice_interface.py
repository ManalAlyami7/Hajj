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
    


    @staticmethod
    def get_styles() -> str:
        """Return complete CSS for real-time voice interface"""
        return """
<style>
/* ===== Base Layout ===== */
.stApp {
  background: linear-gradient(135deg, #0f172a 0%, #1e293b 50%, #334155 100%);
  background-attachment: fixed;
  overflow: hidden !important;
  height: 100vh;
}
#MainMenu, footer, header {visibility: hidden;}
.main .block-container {
  padding: 0.75rem 1rem;
  max-width: 1400px;
  height: 100vh;
  display: flex;
  flex-direction: column;
}

/* ===== Header ===== */
.voice-header{text-align:center;padding:0.75rem 0;margin-bottom:0.5rem;}
.voice-title{
  font-size:2.2rem;font-weight:800;letter-spacing:2px;
  background:linear-gradient(135deg,#60a5fa 0%,#a78bfa 100%);
  -webkit-background-clip:text;-webkit-text-fill-color:transparent;
  margin-bottom:0.25rem;
}
.voice-subtitle{color:rgba(255,255,255,0.85);font-size:0.95rem;}

/* ===== Grid Layout ===== */
.voice-container{
  display:grid;grid-template-columns:1fr 1fr;gap:1.5rem;
  flex:1;min-height:0;padding:0 1rem;
}

/* ===== Avatar Section ===== */
.voice-left{
  display:flex;flex-direction:column;align-items:center;justify-content:center;
  background:rgba(255,255,255,0.03);
  border-radius:2rem;padding:1.5rem;
  backdrop-filter:blur(20px);
  border:1px solid rgba(255,255,255,0.08);
  box-shadow:0 8px 32px rgba(0,0,0,0.25);
  overflow:hidden;
}
.voice-avatar{
  width:180px;height:180px;border-radius:50%;
  display:flex;align-items:center;justify-content:center;font-size:90px;
  background:linear-gradient(135deg,#60a5fa 0%,#a78bfa 100%);
  box-shadow:0 20px 60px rgba(96,165,250,0.35);
  border:6px solid rgba(255,255,255,0.15);
  animation:float 3s ease-in-out infinite;
}
.voice-avatar.listening{
  animation:pulse-listening 0.8s infinite;
  box-shadow:0 0 80px rgba(96,165,250,0.8);
}
.voice-avatar.speaking{
  animation:pulse-speaking 0.6s infinite;
  box-shadow:0 0 80px rgba(167,139,250,0.8);
}

/* ===== Avatar Animations ===== */
.voice-ring{position:absolute;border:3px solid rgba(96,165,250,0.3);
  border-radius:50%;top:50%;left:50%;transform:translate(-50%,-50%);
  animation:expand 3s ease-out infinite;
}
.voice-ring-1{width:200px;height:200px;animation-delay:0s;}
.voice-ring-2{width:240px;height:240px;animation-delay:1s;}
.voice-ring-3{width:280px;height:280px;animation-delay:2s;}
@keyframes float{0%,100%{transform:translateY(0);}50%{transform:translateY(-15px);}}
@keyframes pulse-listening{0%,100%{transform:scale(1);}50%{transform:scale(1.1);}}
@keyframes pulse-speaking{0%,100%{transform:scale(1);}50%{transform:scale(1.15);}}
@keyframes expand{0%{transform:translate(-50%,-50%) scale(0.8);opacity:0.8;}
                  100%{transform:translate(-50%,-50%) scale(1.5);opacity:0;}}

.record-label{
  margin-top:1rem;color:white;font-weight:600;
  text-transform:uppercase;letter-spacing:1.5px;
}

/* ===== Right Panel ===== */
.voice-right{
  display:flex;flex-direction:column;gap:1rem;
  height:100%;min-height:0;overflow:hidden;
}
.transcript-container,.response-container{
  background:rgba(255,255,255,0.04);border-radius:1.5rem;padding:1.25rem;
  backdrop-filter:blur(18px);border:1px solid rgba(255,255,255,0.08);
  box-shadow:0 8px 32px rgba(0,0,0,0.22);
  flex:1;min-height:0;display:flex;flex-direction:column;overflow:hidden;
}

/* ===== Panels ===== */
.panel-header{display:flex;align-items:center;gap:0.75rem;margin-bottom:0.75rem;
  padding-bottom:0.75rem;border-bottom:2px solid rgba(255,255,255,0.08);}
.panel-icon{font-size:1.75rem;}
.panel-title{font-size:1.2rem;font-weight:700;color:white;margin:0;}
.panel-badge{
  margin-left:auto;padding:0.3rem 0.8rem;border-radius:1rem;
  font-weight:600;font-size:0.75rem;background:rgba(96,165,250,0.16);
  color:#60a5fa;border:1px solid rgba(96,165,250,0.2);
}
.panel-badge.active{
  background:rgba(34,197,94,0.16);color:#22c55e;
  border-color:rgba(34,197,94,0.25);animation:badge-pulse 1s infinite;
}
@keyframes badge-pulse{0%,100%{opacity:1;}50%{opacity:0.6;}}

/* ===== Text Panels ===== */
.transcript-text,.response-content{
  color:rgba(255,255,255,0.92);font-size:1.1rem;line-height:1.6;
  flex:1;overflow-y:auto;padding-right:0.5rem;
}
.transcript-text.empty,.response-content.empty{
  color:rgba(255,255,255,0.45);font-style:italic;overflow:hidden;
}

/* ===== Metadata Cards ===== */
.metadata-card{
  background:rgba(255,255,255,0.03);border-radius:1rem;padding:0.9rem;
  margin-top:0.75rem;border-left:4px solid #60a5fa;
}
.metadata-title{
  font-size:0.85rem;font-weight:600;color:#60a5fa;
  margin-bottom:0.5rem;text-transform:uppercase;letter-spacing:1px;
}
.metadata-list{list-style:none;margin:0;padding:0;}
.metadata-list li{
  padding:0.25rem 0;color:rgba(255,255,255,0.85);
}
.metadata-list li:before{
  content:"→ ";color:#60a5fa;font-weight:bold;margin-right:0.5rem;
}

/* ===== Floating Status ===== */
.status-indicator{
  position:fixed;top:15px;right:15px;padding:0.6rem 1.25rem;
  background:rgba(0,0,0,0.75);border-radius:2rem;color:white;
  font-weight:600;font-size:0.85rem;backdrop-filter:blur(10px);
  border:1px solid rgba(255,255,255,0.12);z-index:1000;
  display:flex;align-items:center;gap:0.5rem;
}
.status-dot{width:10px;height:10px;border-radius:50%;background:#22c55e;animation:dot-pulse 1.5s infinite;}
.status-dot.listening{background:#ef4444;}
.status-dot.speaking{background:#a78bfa;}
@keyframes dot-pulse{0%,100%{opacity:1;}50%{opacity:0.4;}}

/* ===== Responsive ===== */
@media (max-width:1024px){
  .voice-container{grid-template-columns:1fr;gap:1rem;}
  .voice-avatar{width:140px;height:140px;font-size:70px;}
}
</style>
"""
