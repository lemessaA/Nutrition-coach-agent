from pydantic import BaseModel
from typing import Optional
from datetime import datetime
"""
Chat related Pydantic schemas
"""

class ChatMessageCreate(BaseModel):
    message: str # User message
    session_id: str # Session ID


class ChatMessageResponse(BaseModel):
    id: int # Database ID
    user_id: int # User ID
    message: str # User message
    response: str # Agent response
    agent_type: str # Agent type
    session_id: str # Session ID
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str # User message
    session_id: Optional[str] = None # Session ID
    user_id: Optional[int] = None # User ID


class ChatResponse(BaseModel):
    response: str # Agent response
    agent_type: str # Agent type
    session_id: str # Session ID
    suggestions: Optional[list] = None # Suggested follow-up questions
