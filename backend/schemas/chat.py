from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ChatMessageCreate(BaseModel):
    message: str
    session_id: str


class ChatMessageResponse(BaseModel):
    id: int
    user_id: int
    message: str
    response: str
    agent_type: str
    session_id: str
    created_at: datetime
    
    class Config:
        from_attributes = True


class ChatRequest(BaseModel):
    message: str
    session_id: Optional[str] = None
    user_id: Optional[int] = None


class ChatResponse(BaseModel):
    response: str
    agent_type: str
    session_id: str
    suggestions: Optional[list] = None
