"""
Voice Models Module
Pydantic models specific to voice assistant functionality
"""

from pydantic import BaseModel, Field
from typing import List, Literal, Optional


class TranscriptionResult(BaseModel):
    """
    Structured output for audio transcription
    NOTE: This is for internal use only. Whisper API returns a simple object with .text attribute.
    We normalize it in VoiceProcessor._normalize_transcription() before using this model.
    """
    text: str = Field(
        description="The transcribed text from audio"
    )
    language: Optional[str] = Field(
        default="en",
        description="Detected language (only available with verbose_json format)"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        default=1.0,
        description="Confidence score (Whisper doesn't provide this, so we default to 1.0)"
    )


class VoiceIntentClassification(BaseModel):
    """Structured output for voice intent detection with urgency"""
    intent: Literal["GREETING", "DATABASE", "GENERAL_HAJJ"] = Field(
        description="The classified intent of the user's message"
    )
    confidence: float = Field(
        ge=0.0, le=1.0,
        description="Confidence score of the classification"
    )
    reasoning: str = Field(
        description="Brief explanation of why this intent was chosen"
    )
    is_arabic: bool = Field(
        default=False,
        description="Whether the input is in Arabic"
    )
    urgency: Literal["low", "medium", "high"] = Field(
        default="low",
        description="Urgency level of the request"
    )


class VoiceResponse(BaseModel):
    """Structured output for voice response generation"""
    response: str = Field(
        description="The text response to be spoken"
    )
    tone: Literal["formal", "casual", "warm", "urgent"] = Field(
        description="Tone of the response"
    )
    key_points: List[str] = Field(
        default_factory=list,
        description="Key points mentioned in the response"
    )
    includes_warning: bool = Field(
        default=False,
        description="Whether response includes a security warning"
    )
    suggested_actions: List[str] = Field(
        default_factory=list,
        description="Suggested next actions for the user"
    )


class DatabaseVoiceResponse(BaseModel):
    """Structured output for database-related voice queries"""
    response: str = Field(
        description="The spoken response text"
    )
    verification_steps: List[str] = Field(
        description="Steps to verify agency authorization"
    )
    warning_message: str = Field(
        description="Warning about fake agencies"
    )
    official_sources: List[str] = Field(
        default_factory=list,
        description="Official sources for verification"
    )
    tone: Literal["formal", "urgent", "informative"] = Field(
        default="urgent",
        description="Tone of the response"
    )