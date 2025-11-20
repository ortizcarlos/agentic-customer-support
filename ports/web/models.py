# models.py

"""
Request and Response models for the FastAPI adapter
"""

from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime


class UserMessage(BaseModel):
    """User message request"""
    customer_name: str = Field(..., description="Your name")
    content: str = Field(..., description="Your message")


class AssistantResponse(BaseModel):
    """Assistant response"""
    message: str = Field(..., description="Response from the assistant")
    conversation_id: str = Field(..., description="Conversation ID")
    timestamp: datetime = Field(default_factory=datetime.now, description="Response timestamp")
    success: bool = Field(True, description="Whether the request was successful")
