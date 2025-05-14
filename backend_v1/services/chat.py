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
            {"id": "gpt-4", "name": "GPT-4"}
        ]
        
        # self.llm.get_model_list()가 구현되어 있다면 사용
        if hasattr(self.llm, "get_model_list"):
            models = self.llm.get_model_list()
        
        # 파인튜닝된 모델 정보 추가
        try:
            finetuned_model_path = "./data/finetuned_models.json"
            if os.path.exists(finetuned_model_path):
                with open(finetuned_model_path, "r") as f:
                    finetuned_model = json.load(f)
                    if "model_id" in finetuned_model:
                        models.append({
                            "id": finetuned_model["model_id"],
                            "name": "Ready To Go 파인튜닝 모델"
                        })
                    logger.info(f"Added finetuned model: {finetuned_model.get('model_id')}")
        except Exception as e:
            logger.error(f"Error loading finetuned models: {e}")
            
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
        
        country = request.country or conversation.country
        topic = request.topic or conversation.topic
        
        # RAG 검색 (번역 포함)
        context, references = self.rag.search_with_translation(
            query=request.message,
            country=country.lower(),
            doc_type=topic+"_info"
        )
        
        # LLM 응답 생성 (번역 포함)
        # 사용자가 선택한 모델이 있는 경우 해당 모델 사용
        if request.model_id:
            # 기존 LLM 인스턴스 대신 새 인스턴스 생성 (선택한 모델로)
            llm = LLM(model_name=request.model_id)
            response_text = await llm.generate_with_translation(
                query=request.message,
                context=context,
                references=references,
                translate_to_korean=True
            )
            logger.info(f"Using user-selected model: {request.model_id}")
        else:
            # 기본 LLM 인스턴스 사용
            response_text = await self.llm.generate_with_translation(
                query=request.message,
                context=context,
                references=references,
                translate_to_korean=True
            )
        
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