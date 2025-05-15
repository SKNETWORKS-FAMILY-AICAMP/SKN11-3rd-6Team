import json
import logging
import os
from sqlalchemy.orm import Session

from database import Conversation, Message
from schemas import ChatRequest, ChatResponse, MessageResponse
from ai_services.rag import RAG
from ai_services.llm import LLM

logger = logging.getLogger(__name__)

class ChatService:
    
    def __init__(self):
        self.rag = RAG()
        self.llm = LLM()

    async def create_conversation(self, session_id: str, country_id: str, topic_id: str, db: Session):
        """새 대화 세션 생성"""
        conversation = Conversation(
            session_id=session_id,
            country=country_id,  # country_id -> country
            topic=topic_id      # topic_id -> topic
        )
        db.add(conversation)
        db.commit()
        db.refresh(conversation)
        return conversation

    async def get_conversation_history(self, conversation_id: int, db: Session):
        """대화 기록 반환"""
        messages = db.query(Message).filter(
            Message.conversation_id == conversation_id
        ).order_by(Message.created_at).all()
        return [
            MessageResponse(
                id=m.id,
                conversation_id=m.conversation_id,
                role=m.role,
                content=m.content,
                references=json.loads(m.references) if m.references else [],
                created_at=m.created_at
            ) for m in messages
        ]

    def get_available_models(self):
        """사용 가능한 LLM 모델 목록 반환"""
        # 기본 모델 목록
        models = [
            {"id": "gpt-3.5-turbo", "name": "GPT-3.5 Turbo"},
            {"id": "gpt-4", "name": "GPT-4"},
            {"id": "flan-t5-base", "name": "Flan-T5 Base(Fine-Tuned)"}
        ]
        
        # self.llm.get_model_list()가 구현되어 있다면 사용
        if hasattr(self.llm, "get_model_list"):
            models = self.llm.get_model_list()
            
        return models

    def get_example_questions(self, country: str = None, topic: str = None):
        """FAQ 반환"""
        from database import FAQ, SessionLocal
        
        # DB 세션 생성
        db = SessionLocal()
        try:
            # DB에서 예시 질문 가져오기
            query = db.query(FAQ)
            
            # 필터 적용
            if country:
                query = query.filter(FAQ.country == country.lower())
            if topic:
                if topic=="safety":
                    topic="immigration_safety"
                query = query.filter(FAQ.topic == topic.lower())
                
            # 생성일 기준 정렬 및 가져오기
            questions = query.order_by(FAQ.created_at.desc()).limit(5).all()
            
            # 결과 가공
            if questions:
                return [q.question for q in questions]
                
        except Exception as e:
            logger.error(f"Error fetching example questions: {e}")
        finally:
            db.close()
    
    def get_document_sources(self, country: str = None, topic: str = None):
        """선택된 국가/토픽의 문서 출처 URL들 반환"""
        from database import Document, SessionLocal
        
        # DB 세션 생성
        db = SessionLocal()
        try:
            # 토픽 변환
            doc_topic = topic
            # DB에서 문서 가져오기
            query = db.query(Document)
            
            # 필터 적용
            if country:
                query = query.filter(Document.country == country.lower())
            if doc_topic:
                query = query.filter(Document.topic == doc_topic.lower())
                
            # URL이 있는 문서만 가져오기
            documents = query.filter(Document.url != None).all()
            
            # 중복 제거한 URL 리스트 반환
            urls = list(set([doc.url for doc in documents if doc.url]))
            return urls
                
        except Exception as e:
            logger.error(f"Error fetching document sources: {e}")
            return []
        finally:
            db.close()

    async def process_message(self, request: ChatRequest, db: Session) -> ChatResponse:
        """메시지 처리"""
        
        # 대화 가져오기 또는 생성
        if request.conversation_id:
            conversation = db.query(Conversation).filter(
                Conversation.id == request.conversation_id
            ).first()
        else:
            conversation = Conversation(
                session_id=request.session_id,
                country=request.country,
                topic=request.topic
            )
            db.add(conversation)
            db.commit()
            db.refresh(conversation)
        
        # 사용자 메시지 저장
        user_message = Message(
            conversation_id=conversation.id,
            role="user",
            content=request.message
        )
        db.add(user_message)
        db.commit()
        db.refresh(user_message)
        
        # 이전 메시지들 가져오기 (현재 메시지 제외)
        previous_messages = db.query(Message).filter(
            Message.conversation_id == conversation.id,
            Message.id != user_message.id
        ).order_by(Message.created_at.asc()).all()
        
        history = [
            {"role": m.role, "content": m.content}
            for m in previous_messages
        ]
        
        # 디버그: 히스토리 확인
        logger.info(f"Conversation {conversation.id} history: {len(history)} messages")
        
        country = request.country or conversation.country
        country = country.replace(" " , "").lower()
        
        topic = request.topic or conversation.topic
        if topic == "immigration":
            topic = "immigration_regulations_info"
        elif topic == "safety":
            topic = "immigration_safety_info"
        else :
            topic = topic + "_info"
        
        # RAG 검색 (번역 포함)
        context, references = self.rag.search_with_translation(
            query=request.message,
            country=country,
            doc_type=topic
        )
        
        # RAG 검색 결과 로그
        logger.info(f"RAG context length: {len(context) if context else 0}")
        logger.info(f"References found: {len(references) if references else 0}")
        
        # LLM 응답 생성 (번역 포함)
        # 사용자가 선택한 모델이 있는 경우 해당 모델 사용
        if request.model_id:
            # Flan-T5 모델인지 확인
            if "t5" in request.model_id.lower():
                llm = LLM(model_name=request.model_id)
                response_text = await llm.generate_with_translation(
                    query=request.message,
                    context=context,
                    references=references,
                    history=history,
                    translate_to_korean=True,
                    system_prompt="You are a kind AI assistant who answers questions related to immigration, insurance, national safety, and visa information for different countries. Provide accurate and helpful answers to your questions."
                )
            else:
                llm = LLM(model_name=request.model_id)
                response_text = await llm.generate_with_translation(
                    query=request.message,
                    context=context,
                    references=references,
                    history=history,
                    translate_to_korean=True
                )
        else:
            response_text = await self.llm.generate_with_translation(
                query=request.message,
                context=context,
                references=references,
                history=history,
                translate_to_korean=True
            )
        
        # 응답 길이 로그
        logger.info(f"Generated response length: {len(response_text) if response_text else 0}")
        
        # 응답 저장
        assistant_message = Message(
            conversation_id=conversation.id,
            role="assistant",
            content=response_text,
            references=json.dumps(references)
        )
        db.add(assistant_message)
        db.commit()
        db.refresh(assistant_message)
        
        return ChatResponse(
            message=MessageResponse(
                id=assistant_message.id,
                conversation_id=conversation.id,
                role=assistant_message.role,
                content=assistant_message.content,
                references=references,
                created_at=assistant_message.created_at
            ),
            conversation_id=conversation.id
        )
