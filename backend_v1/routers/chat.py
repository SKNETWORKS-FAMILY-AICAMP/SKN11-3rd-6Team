from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from typing import List, Optional
import json

from database import get_db
from schemas import ChatRequest, ChatResponse, MessageResponse, ConversationCreate, ConversationResponse
from services.chat import ChatService

router = APIRouter()
chat_service = ChatService()

@router.post("/conversation", response_model=ConversationResponse)
async def create_conversation(
    request: ConversationCreate,
    db: Session = Depends(get_db)
):
    """새 대화 세션 시작"""
    try:
        conversation = await chat_service.create_conversation(
            session_id=request.session_id,
            country_id=request.country_id,
            topic_id=request.topic_id,
            db=db
        )
        
        return ConversationResponse(
            id=conversation.id,
            session_id=conversation.session_id,
            country_id=conversation.country,  # country_id <- country
            topic_id=conversation.topic,      # topic_id <- topic
            created_at=conversation.created_at
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/message", response_model=ChatResponse)
async def process_message(
    request: ChatRequest,
    db: Session = Depends(get_db)
):
    """사용자 메시지 처리"""
    try:
        response = await chat_service.process_message(request, db)
        
        # 스트리밍 응답
        if request.stream:
            async def generate():
                async for chunk in response:
                    yield f"data: {json.dumps(chunk)}\n\n"
                yield "data: [DONE]\n\n"
            
            return StreamingResponse(
                generate(),
                media_type="text/event-stream"
            )
        
        return response
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/history/{conversation_id}", response_model=List[MessageResponse])
async def get_conversation_history(
    conversation_id: int,
    db: Session = Depends(get_db)
):
    """대화 기록 조회"""
    try:
        messages = await chat_service.get_conversation_history(conversation_id, db)
        return messages
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/settings/models")
async def get_available_models():
    """사용 가능한 LLM 모델 목록"""
    return chat_service.get_available_models()

@router.get("/examples")
async def get_example_questions(
    country: Optional[str] = None,
    topic: Optional[str] = None
):
    """예시 질문 반환"""
    return {
        "examples": chat_service.get_example_questions(country, topic)
    }

@router.get("/sources")
async def get_document_sources(
    country: Optional[str] = None,
    topic: Optional[str] = None
):
    """선택된 국가/토픽의 문서 출처 URL 반환"""
    return {
        "sources": chat_service.get_document_sources(country, topic)
    }