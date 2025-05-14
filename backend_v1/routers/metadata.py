from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from database import get_db
from services.metadata import MetadataService

router = APIRouter()
metadata_service = MetadataService()

@router.get("/countries", response_model=list[str])
async def get_countries(db: Session = Depends(get_db)):
    """지원 국가 목록"""
    return metadata_service.get_countries(db)

@router.get("/topics", response_model=list[str])
async def get_topics(db: Session = Depends(get_db)):
    """지원 주제 목록"""
    return metadata_service.get_topics(db)

@router.get("/sources", response_model=list[str])
async def get_sources(db: Session = Depends(get_db)):
    """문서 출처 목록"""
    return metadata_service.get_sources(db)