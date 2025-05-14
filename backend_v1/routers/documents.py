from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import List, Optional

from database import get_db
from schemas import DocumentResponse
from services.metadata import MetadataService

router = APIRouter()
metadata_service = MetadataService()

@router.get("/{country_id}/{topic_id}", response_model=List[DocumentResponse])
async def get_documents_by_filter(
    country_id: int,
    topic_id: int,
    source_id: Optional[int] = None,
    limit: int = Query(20, le=100),
    offset: int = Query(0, ge=0),
    db: Session = Depends(get_db)
):
    """필터링된 문서 목록"""
    return metadata_service.get_documents_by_filter(
        country_id=country_id,
        topic_id=topic_id,
        source_id=source_id,
        limit=limit,
        offset=offset,
        db=db
    )

@router.get("/{document_id}", response_model=DocumentResponse)
async def get_document_detail(
    document_id: int,
    db: Session = Depends(get_db)
):
    """문서 상세 조회"""
    try:
        return metadata_service.get_document_detail(document_id, db)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

@router.get("/search", response_model=List[DocumentResponse])
async def search_documents(
    q: str = Query(..., description="검색어"),
    limit: int = Query(20, le=100),
    db: Session = Depends(get_db)
):
    """문서 검색"""
    return metadata_service.search_documents(
        query=q,
        limit=limit,
        db=db
    )