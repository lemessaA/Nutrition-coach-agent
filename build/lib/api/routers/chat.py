from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import List, Optional

from database.connection import get_db
from database.models import ChatMessage, User, UserProfile
from schemas.chat import ChatRequest, ChatResponse, ChatMessageCreate, ChatMessageResponse
from graph.workflow import nutrition_coach_workflow

router = APIRouter()


@router.post("/chat", response_model=ChatResponse)
async def chat_with_ai(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """Chat with the Nutrition Coach AI"""
    try:
        # Get user context if user_id is provided
        user_context = {}
        if request.user_id:
            user = db.query(User).filter(User.id == request.user_id).first()
            if user and user.profile:
                profile = user.profile
                user_context = {
                    "user_profile": {
                        "age": profile.age,
                        "weight": profile.weight,
                        "height": profile.height,
                        "gender": profile.gender.value,
                        "activity_level": profile.activity_level.value,
                        "goal": profile.goal.value,
                        "target_calories": profile.target_calories,
                        "target_protein": profile.target_protein,
                        "target_carbs": profile.target_carbs,
                        "target_fat": profile.target_fat,
                        "dietary_restrictions": profile.dietary_restrictions,
                        "allergies": profile.allergies,
                        "preferences": profile.preferences
                    }
                }
        
        # Process message through workflow
        result = await nutrition_coach_workflow.process_message(
            message=request.message,
            user_id=request.user_id,
            session_id=request.session_id or "default",
            user_context=user_context
        )
        
        if not result["success"]:
            raise HTTPException(status_code=500, detail=result.get("error", "Chat processing failed"))
        
        # Save chat message to database if user_id is provided
        if request.user_id:
            chat_message = ChatMessage(
                user_id=request.user_id,
                message=request.message,
                response=result["response"],
                agent_type=result.get("agent_used", "unknown"),
                session_id=request.session_id or "default"
            )
            db.add(chat_message)
            db.commit()
        
        return ChatResponse(
            response=result["response"],
            agent_type=result.get("agent_used", "coaching_agent"),
            session_id=request.session_id or "default",
            suggestions=[]  # Can be enhanced based on context
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Chat error: {str(e)}")


@router.get("/chat/history/{user_id}", response_model=List[ChatMessageResponse])
async def get_chat_history(
    user_id: int,
    session_id: Optional[str] = None,
    limit: int = 50,
    db: Session = Depends(get_db)
):
    """Get chat history for a user"""
    try:
        query = db.query(ChatMessage).filter(ChatMessage.user_id == user_id)
        
        if session_id:
            query = query.filter(ChatMessage.session_id == session_id)
        
        messages = query.order_by(ChatMessage.created_at.desc()).limit(limit).all()
        
        return [
            ChatMessageResponse(
                id=msg.id,
                user_id=msg.user_id,
                message=msg.message,
                response=msg.response,
                agent_type=msg.agent_type,
                session_id=msg.session_id,
                created_at=msg.created_at
            )
            for msg in messages
        ]
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching chat history: {str(e)}")


@router.delete("/chat/history/{user_id}")
async def clear_chat_history(
    user_id: int,
    session_id: Optional[str] = None,
    db: Session = Depends(get_db)
):
    """Clear chat history for a user"""
    try:
        query = db.query(ChatMessage).filter(ChatMessage.user_id == user_id)
        
        if session_id:
            query = query.filter(ChatMessage.session_id == session_id)
        
        deleted_count = query.count()
        query.delete()
        db.commit()
        
        return {"message": f"Deleted {deleted_count} chat messages"}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error clearing chat history: {str(e)}")


@router.get("/chat/sessions/{user_id}")
async def get_chat_sessions(user_id: int, db: Session = Depends(get_db)):
    """Get all chat sessions for a user"""
    try:
        sessions = db.query(ChatMessage.session_id).filter(
            ChatMessage.user_id == user_id
        ).distinct().all()
        
        session_list = [session[0] for session in sessions]
        
        return {"sessions": session_list, "total_sessions": len(session_list)}
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error fetching sessions: {str(e)}")
