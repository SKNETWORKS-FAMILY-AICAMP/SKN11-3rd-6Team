import logging
from typing import List, Optional
from sqlalchemy.orm import Session

from database import Document
from schemas import DocumentResponse

logger = logging.getLogger(__name__)

class MetadataService:
    """메타데이터 관리 서비스"""
    
    def get_countries(self, db: Session) -> List[str]:
        """국가 목록 조회"""
        countries = db.query(Document.country).distinct().all()
        
        return [country[0] for country in countries if country[0]]
    
    def get_topics(self, db: Session) -> List[str]:
        """주제 목록 조회"""
        topics = db.query(Document.topic).distinct().all()
        return [topic[0] for topic in topics if topic[0]]

    
    def get_sources(self, db: Session) -> List[str]:
        """출처 목록 조회"""
        sources = db.query(Document.source).distinct().all()
        return [source[0] for source in sources if source[0]]
    
    def get_documents_by_filter(
        self,
        country_id: Optional[int],
        topic_id: Optional[int],
        source_id: Optional[int],
        limit: int = 20,
        offset: int = 0,
        db: Session = None
    ) -> List[DocumentResponse]:
        """필터링된 문서 목록 조회"""
        query = db.query(Document)
        
        if country_id:
            query = query.filter(Document.country_id == country_id)
        if topic_id:
            query = query.filter(Document.topic_id == topic_id)
        if source_id:
            query = query.filter(Document.source_id == source_id)
        
        documents = query.offset(offset).limit(limit).all()
        
        return [
            DocumentResponse(
                id=doc.id,
                title=doc.title,
                doc_type=doc.doc_type,
                url=doc.url,
                country_id=doc.country_id,
                topic_id=doc.topic_id,
                source_id=doc.source_id,
                created_at=doc.created_at,
                updated_at=doc.updated_at
            )
            for doc in documents
        ]
    
    def get_document_detail(self, document_id: int, db: Session) -> DocumentResponse:
        """문서 상세 조회"""
        document = db.query(Document).filter(Document.id == document_id).first()
        
        if not document:
            raise ValueError(f"Document {document_id} not found")
        
        return DocumentResponse(
            id=document.id,
            title=document.title,
            content=document.content,
            doc_type=document.doc_type,
            url=document.url,
            metadata=document.metadata,
            country_id=document.country_id,
            topic_id=document.topic_id,
            source_id=document.source_id,
            created_at=document.created_at,
            updated_at=document.updated_at
        )
