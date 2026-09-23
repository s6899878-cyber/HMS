from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

class ChatMessage(BaseModel):
    role: str
    content: str

class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None

class ChatResponse(BaseModel):
    message: ChatMessage
    conversation_id: int

class ConversationOut(BaseModel):
    id: int
    title: Optional[str]
    created_at: datetime
    messages: List[ChatMessage] = []

    class Config:
        from_attributes = True

class RecommendationOut(BaseModel):
    category: str
    title: str
    description: str
    icon: str
    action_text: Optional[str] = None
    
class TreatmentAnalysisRequest(BaseModel):
    condition: str
    treatment: str
    location: Optional[str] = None
    budget: Optional[str] = None

class TreatmentAnalysisResponse(BaseModel):
    treatment: str
    purpose: str
    general_procedure: str
    possible_benefits: List[str]
    common_risks: List[str]
    recovery: str
    questions_to_ask: List[str]
