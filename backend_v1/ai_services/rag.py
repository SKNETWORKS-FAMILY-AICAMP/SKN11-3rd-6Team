import os
import re
import logging
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
import chromadb
from chromadb import PersistentClient
from chromadb.utils import embedding_functions
from langchain_community.vectorstores.chroma import Chroma as LangChroma
import tiktoken
from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_community.document_loaders import PyMuPDFLoader
from langchain_community.embeddings import OpenAIEmbeddings  # Updated import
from deep_translator import GoogleTranslator
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from config import settings  # Changed to absolute import

logger = logging.getLogger(__name__)

class RAG:

    def __init__(self):
        # ChromaDB 초기화
        self.client = PersistentClient(path=settings.VECTOR_DB_PATH)
        
        # OpenAI 임베딩 설정
        self.embedding_function = OpenAIEmbeddings(
            model="text-embedding-3-small",
            openai_api_key=settings.OPENAI_API_KEY,
            dimensions=384
        )
        
        # 텍스트 분할기
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=1000,
            chunk_overlap=200
        )
        
        # 전역 collection 사용
        try:
            self.collection = self.client.get_collection("global-documents")
        except:
            self.collection = self.client.create_collection("global-documents")
            
        self.vectorstore = LangChroma(
            collection_name="global-documents",
            embedding_function=self.embedding_function,
            client=self.client
        )
        
        self.tokenizer = tiktoken.get_encoding("cl100k_base")
        
        # 번역기 초기화
        self.ko_to_en = GoogleTranslator(source='ko', target='en')
        self.en_to_ko = GoogleTranslator(source='en', target='ko')
        
        # 문서 타입 패턴
        self.doc_type_pattern = r"(.*?)_(visa_info|insurance_info|immigration_regulations_info|immigration_safety_info)\.pdf"
    
    def process_pdf_directory(self, pdf_dir: str):
        """PDF 디렉토리 처리"""
        pdf_files = [f for f in os.listdir(pdf_dir) if f.endswith(".pdf")]
        
        for filename in pdf_files:
            match = re.match(self.doc_type_pattern, filename)
            if not match:
                continue
                
            country, doc_type = match.groups()
            pdf_path = os.path.join(pdf_dir, filename)
            
            logger.info(f"Processing {country.upper()} - {doc_type}")
            
            # PDF 로드 및 처리
            docs = PyMuPDFLoader(pdf_path).load()
            splits = self.text_splitter.split_documents(docs)
            texts = [doc.page_content for doc in splits]
            
            # 메타데이터
            metadatas = [
                {
                    "country": country,
                    "document_type": doc_type,
                    "tag": f"{country}_{doc_type}",
                    "language": "en",
                    "updated_at": datetime.now().isoformat()
                }
                for _ in splits
            ]
            
            # 배치 크기 제한 (ChromaDB 최대 배치 크기: 5461)
            MAX_BATCH_SIZE = 1000  # 안전한 배치 크기 설정
            
            # 배치 처리
            total_texts = len(texts)
            logger.info(f"Total chunks to process: {total_texts}")
            
            for i in range(0, total_texts, MAX_BATCH_SIZE):
                end_idx = min(i + MAX_BATCH_SIZE, total_texts)
                batch_texts = texts[i:end_idx]
                batch_metadatas = metadatas[i:end_idx]
                
                logger.info(f"Processing batch {i//MAX_BATCH_SIZE + 1}: chunks {i} to {end_idx-1}")
                
                # 벡터 스토어에 배치 추가
                self.vectorstore.add_texts(texts=batch_texts, metadatas=batch_metadatas)
                
            logger.info(f"Indexed {country}_{doc_type} in {(total_texts-1)//MAX_BATCH_SIZE + 1} batches")
    
    def search_with_translation(
        self,
        query: str,
        country: Optional[str] = None,
        doc_type: Optional[str] = None
    ) -> Tuple[str, List[Dict[str, Any]]]:
        """한국어 질문을 영어로 번역하여 검색"""
        
        # 태그 구성
        tag = f"{country}_{doc_type}" if country and doc_type else country
        
        # 한국어 질문을 영어로 번역
        translated_query = self.ko_to_en.translate(query)
        
        # 검색 실행 (MMR 사용)
        retriever = self.vectorstore.as_retriever(
            search_type="mmr",
            search_kwargs={"k": 5, "filter": {"tag": tag} if tag else {}}
        )
        
        # 문서 검색
        docs = retriever.get_relevant_documents(translated_query)
        
        if not docs:
            return "관련 문서를 찾지 못했습니다.", []
        
        # 컨텍스트와 참조 구성
        context_parts = []
        references = []
        
        for i, doc in enumerate(docs[:3]):  # 최대 3개 문서
            context_parts.append(doc.page_content)
            metadata = doc.metadata
            references.append({
                "title": metadata.get("document_type", "Unknown"),
                "country": metadata.get("country", "Unknown"),
                "tag": metadata.get("tag", ""),
                "updated_at": metadata.get("updated_at", "")
            })
        
        context = "\n\n---\n\n".join(context_parts)
        return context, references
    
    def add_document(self, text: str, metadata: Dict[str, Any]) -> bool:
        """단일 문서 추가 (기존 메서드 유지)"""
        try:
            # 텍스트 분할
            splits = self.text_splitter.split_text(text)
            texts = splits
            
            # 각 청크에 메타데이터 추가
            metadatas = []
            for i in range(len(splits)):
                chunk_metadata = {
                    **metadata,
                    "chunk_index": i,
                    "total_chunks": len(splits)
                }
                metadatas.append(chunk_metadata)
            
            # 배치 크기 제한 적용
            MAX_BATCH_SIZE = 1000
            total_texts = len(texts)
            
            for i in range(0, total_texts, MAX_BATCH_SIZE):
                end_idx = min(i + MAX_BATCH_SIZE, total_texts)
                batch_texts = texts[i:end_idx]
                batch_metadatas = metadatas[i:end_idx]
                
                # 벡터 스토어에 배치 추가
                self.vectorstore.add_texts(texts=batch_texts, metadatas=batch_metadatas)
                
            return True
            
        except Exception as e:
            logger.error(f"Error adding document: {e}")
            return False
        
if __name__ == "__main__":
    rag = RAG()
    query = "프랑스에서 비자 연장하려면?"
    context, references = rag.search_with_translation(query, country="france", doc_type="visa_info")
    print("Context:", context)
    print("References:", references)
    
