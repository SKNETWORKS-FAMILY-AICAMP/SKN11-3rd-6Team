from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from datetime import datetime

# 문서 스키마
class DocumentBase(BaseModel):
    title: str
    content: Optional[str] = None
    url: Optional[str] = None
    country: Optional[str] = None
    topic: Optional[str] = None
    source: Optional[str] = None

class DocumentResponse(DocumentBase):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 대화 스키마
class ConversationCreate(BaseModel):
    session_id: str
    country_id: str
    topic_id: str

class ConversationResponse(ConversationCreate):
    id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 메시지 스키마
class MessageCreate(BaseModel):
    role: str
    content: str
    references: Optional[List[Dict[str, Any]]] = None

class MessageResponse(MessageCreate):
    id: int
    conversation_id: int
    created_at: datetime
    
    class Config:
        from_attributes = True

# 채팅 요청/응답
class ChatRequest(BaseModel):
    message: str
    conversation_id: Optional[int] = None
    session_id: str
    country: Optional[str] = None
    topic: Optional[str] = None
    model_id: Optional[str] = None
    stream: bool = False

class ChatResponse(BaseModel):
    message: MessageResponse
    conversation_id: int