from sqlalchemy import create_engine, Column, Integer, String, DateTime, Text, ForeignKey
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, relationship
from datetime import datetime

from config import settings

engine = create_engine(settings.DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

class Document(Base):
    """문서 정보 및 벡터 메타데이터"""
    __tablename__ = "documents"
    
    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(500), nullable=False)
    url = Column(String(500))
    
    country = Column(String(100), index=True)  # Australia, Canada, France
    topic = Column(String(100), index=True)    # visa, insurance, immigration
    source = Column(String(200))               # 출처 정보
    
    created_at = Column(DateTime, default=datetime.utcnow)

class Conversation(Base):
    """대화 세션"""
    __tablename__ = "conversations"
    
    id = Column(Integer, primary_key=True, index=True)
    session_id = Column(String(100), index=True)
    
    # 선택적 필터
    country = Column(String(100))
    topic = Column(String(100))
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan")

class Message(Base):
    """채팅 메시지"""
    __tablename__ = "messages"
    
    id = Column(Integer, primary_key=True, index=True)
    conversation_id = Column(Integer, ForeignKey("conversations.id"))
    role = Column(String(20))  # user, assistant
    content = Column(Text)
    
    # RAG 참조 (JSON 형태로 저장)
    references = Column(Text)  # JSON string
    
    created_at = Column(DateTime, default=datetime.utcnow)
    
    conversation = relationship("Conversation", back_populates="messages")

class FAQ(Base):
    """FAQ"""
    __tablename__ = "faqs"
    
    id = Column(Integer, primary_key=True, index=True)
    question = Column(Text, nullable=False)  # 질문 내용
    country = Column(String(100), index=True)  # 국가 (영문명)
    topic = Column(String(100), index=True)    # 토픽 (visa, insurance 등)
    created_at = Column(DateTime, default=datetime.utcnow)

# 자주 사용하는 값들은 코드에서 관리
COUNTRIES = [
    {"emoji": "🇺🇸", "name_kr": "미국", "name_en": "America"},
    {"emoji": "🇨🇳", "name_kr": "중국", "name_en": "China"},
    {"emoji": "🇯🇵", "name_kr": "일본", "name_en": "Japan"},
    {"emoji": "🇨🇦", "name_kr": "캐나다", "name_en": "Canada"},
    {"emoji": "🇦🇺", "name_kr": "호주", "name_en": "Australia"},
    {"emoji": "🇩🇪", "name_kr": "독일", "name_en": "Germany"},
    {"emoji": "🇻🇳", "name_kr": "베트남", "name_en": "Vietnam"},
    {"emoji": "🇵🇭", "name_kr": "필리핀", "name_en": "Philippines"},
    {"emoji": "🇮🇩", "name_kr": "인도네시아", "name_en": "Indonesia"},
    {"emoji": "🇹🇭", "name_kr": "태국", "name_en": "Thailand"},
    {"emoji": "🇬🇧", "name_kr": "영국", "name_en": "United Kingdom"},
    {"emoji": "🇸🇬", "name_kr": "싱가포르", "name_en": "Singapore"},
    {"emoji": "🇲🇾", "name_kr": "말레이시아", "name_en": "Malaysia"},
    {"emoji": "🇪🇸", "name_kr": "스페인", "name_en": "Spain"},
    {"emoji": "🇳🇿", "name_kr": "뉴질랜드", "name_en": "New Zealand"},
    {"emoji": "🇷🇺", "name_kr": "러시아", "name_en": "Russia"},
    {"emoji": "🇫🇷", "name_kr": "프랑스", "name_en": "France"},
    {"emoji": "🇮🇹", "name_kr": "이탈리아", "name_en": "Italy"},
    {"emoji": "🇦🇹", "name_kr": "오스트리아", "name_en": "Austria"},
    {"emoji": "🇭🇰", "name_kr": "홍콩", "name_en": "Hong Kong"}
]

TOPICS = ["visa", "insurance", "immigration_safety", "immigration_regulations"]
SOURCES = ["Government", "Embassy", "Immigration Department"]