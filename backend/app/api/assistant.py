from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.core.database import get_db
from app.api.deps import get_current_user
from app.models.user import User
from app.models.ai_conversation import Conversation, Message
from app.schemas.ai import ChatRequest, ChatResponse, ConversationOut, ChatMessage
from app.services.ai_service import get_ai_response, format_conversation_history, SYSTEM_PROMPT

router = APIRouter()

@router.post("/chat", response_model=ChatResponse)
def chat_with_assistant(
    req: ChatRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    if req.conversation_id:
        conversation = db.query(Conversation).filter(
            Conversation.id == req.conversation_id, 
            Conversation.user_id == current_user.id
        ).first()
        if not conversation:
            raise HTTPException(status_code=404, detail="Conversation not found")
    else:
        # Create new conversation
        conversation = Conversation(user_id=current_user.id, title=req.message[:30] + "...")
        db.add(conversation)
        db.commit()
        db.refresh(conversation)

    # Save user message
    user_msg = Message(conversation_id=conversation.id, role="user", content=req.message)
    db.add(user_msg)
    
    # Get history (limit to last 10 messages for cost control)
    history = db.query(Message).filter(Message.conversation_id == conversation.id).order_by(Message.created_at.asc()).limit(10).all()
    formatted_history = format_conversation_history(history)
    
    # Exclude the message we just added from history context passed to AI to avoid duplication,
    # or just pass the whole history and an empty string. We'll pass history[:-1] and req.message
    ai_context = formatted_history[:-1] if formatted_history else []
    
    ai_reply_text = get_ai_response(SYSTEM_PROMPT, req.message, ai_context, db, current_user.id)
    
    # Save AI message
    ai_msg = Message(conversation_id=conversation.id, role="assistant", content=ai_reply_text)
    db.add(ai_msg)
    db.commit()
    
    return {
        "message": {"role": "assistant", "content": ai_reply_text},
        "conversation_id": conversation.id
    }

@router.get("/conversations", response_model=list[ConversationOut])
def get_conversations(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    return db.query(Conversation).filter(Conversation.user_id == current_user.id).order_by(Conversation.created_at.desc()).all()
