"""QA Pair Generation Strategies for RAG Fine-tuning"""

import random
import os
import sys
from typing import List, Dict, Optional, Any
from langchain.schema import Document

# Add parent directory to path for imports
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))
from ai_services.rag import RAG

class QAGenerator:
    """QA 쌍 생성기"""
    
    def __init__(self, vectordb=None):
        self.vectordb = vectordb
        self.rag = RAG()
        
    def extract_key_phrases(self, text: str) -> List[str]:
        """텍스트에서 핵심 구문 추출"""
        sentences = text.split('. ')
        key_phrases = []
        
        for sentence in sentences[:3]:
            words = sentence.split()
            if len(words) > 3:
                for i in range(len(words) - 2):
                    phrase = ' '.join(words[i:i+3])
                    key_phrases.append(phrase)
        
        return key_phrases if key_phrases else [text[:50]]
    
    def generate_qa(self, doc_content: str, qa_type: str) -> Optional[Dict[str, str]]:
        """다양한 타입의 QA 생성"""
        if qa_type == "factoid":
            return self._generate_factoid_qa(doc_content)
        elif qa_type == "explanation":
            return self._generate_explanation_qa(doc_content)
        elif qa_type == "summary":
            return self._generate_summary_qa(doc_content)
        else:
            return None
    
    def _generate_factoid_qa(self, doc_content: str) -> Optional[Dict[str, str]]:
        """사실 기반 질문-답변 생성"""
        key_phrases = self.extract_key_phrases(doc_content)
        if not key_phrases:
            return None
        
        phrase = random.choice(key_phrases)
        question = f"What is {phrase}?"
        
        # RAG 기반 응답 생성 사용
        context, references = self.rag.search_with_translation(question)
        answer = context[:300]
        
        return {
            "question": question,
            "answer": answer,
            "context": doc_content[:200]
        }
    
    def _generate_explanation_qa(self, doc_content: str) -> Optional[Dict[str, str]]:
        """설명 기반 질문-답변 생성"""
        key_phrases = self.extract_key_phrases(doc_content)
        if not key_phrases:
            return None
        
        phrase = random.choice(key_phrases)
        question = f"Can you explain how {phrase} works?"
        
        # RAG 기반 응답 생성 사용
        context, references = self.rag.search_with_translation(question)
        
        return {
            "question": question,
            "answer": context[:500],
            "context": doc_content[:200]
        }
    
    def _generate_summary_qa(self, doc_content: str) -> Optional[Dict[str, str]]:
        """요약 기반 질문-답변 생성"""
        question = "Can you summarize the main points of this information?"
        
        # RAG 기반 응답 생성 시도
        context, references = self.rag.search_with_translation(question)
        summary = context[:300]
        
        return {
            "question": question,
            "answer": summary,
            "context": doc_content[:200]
        }