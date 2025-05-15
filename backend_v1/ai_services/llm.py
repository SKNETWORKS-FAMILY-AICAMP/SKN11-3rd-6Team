import logging
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
import openai
from openai import AsyncOpenAI
import google.generativeai as genai
import os
import json
from langchain_openai import ChatOpenAI
import torch
from transformers import T5ForConditionalGeneration, T5Tokenizer
from deep_translator import GoogleTranslator
import asyncio
import time

from config import settings

logger = logging.getLogger(__name__)

class LLM:
    """번역 기능이 추가된 LLM 모듈"""
    
    def __init__(self, model_name: Optional[str] = None):
        
        if model_name:
            self.model_name = model_name
        else:
            self.model_name = settings.DEFAULT_LLM_MODEL
        
        # OpenAI 초기화
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(
                api_key=settings.OPENAI_API_KEY,
                timeout=60.0,  # 60초 타임아웃
                max_retries=3  # 최대 3회 재시도
            )
        
        # Gemini 초기화
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # 번역기 초기화
        self.translator = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=settings.OPENAI_API_KEY)
        
        # Flan-T5 모델 및 토크나이저 초기화
        self.flan_t5_model = None
        self.flan_t5_tokenizer = None
        self.device = torch.device("cuda" if torch.cuda.is_available() else "cpu")
        
        # Flan-T5 모델인 경우 로드
        if self.model_name and "t5" in self.model_name.lower():
            self._load_flan_t5_model()
        
        self.ko_to_en = GoogleTranslator(source='ko', target='en')
    
    def _load_flan_t5_model(self):
        """파인튜닝된 Flan-T5 모델 로드"""
        try:
            # 파인튜닝된 모델 경로
            finetuned_model_path = "/Users/comet39/SKN_PJT/3rd_project_v2/backend2/data/models/finetuned-flan-t5-base/checkpoint-40"
            
            # 파인튜닝된 모델이 있으면 사용
            if os.path.exists(finetuned_model_path):
                logger.info(f"Loading finetuned Flan-T5 model from {finetuned_model_path}")
                self.flan_t5_model = T5ForConditionalGeneration.from_pretrained(finetuned_model_path)
                self.flan_t5_tokenizer = T5Tokenizer.from_pretrained("google/flan-t5-base")

            self.flan_t5_model.to(self.device)
            self.flan_t5_model.eval()  # 평가 모드로 설정
            logger.info(f"Flan-T5 model loaded successfully on {self.device}")
            
        except Exception as e:
            logger.error(f"Error loading Flan-T5 model: {e}")
            self.flan_t5_model = None
            self.flan_t5_tokenizer = None
    
    def _generate_with_flan_t5(self, prompt: str, max_length: int = 512) -> str:
        """파인튜닝된 Flan-T5 모델로 응답 생성"""
        if not self.flan_t5_model or not self.flan_t5_tokenizer:
            raise Exception("Flan-T5 model not loaded")
        
        # 입력 텍스트 토크나이징
        inputs = self.flan_t5_tokenizer(
            prompt, 
            max_length=512, 
            truncation=True, 
            padding=True,  # max_length 대신 True
            return_tensors="pt"
        ).to(self.device)
        
        # 응답 생성 - 개선된 파라미터
        with torch.no_grad():
            outputs = self.flan_t5_model.generate(
                inputs["input_ids"],
                max_length=max_length,
                min_length=30,  # 최소 길이 설정
                num_beams=5,    # 빔 수 증가
                temperature=0.8,  # 더 자연스러운 응답
                top_p=0.9,      # nucleus sampling
                top_k=50,       # top-k sampling
                do_sample=True,  # 샘플링 활성화
                early_stopping=True,
                no_repeat_ngram_size=3,  # 반복 방지
                pad_token_id=self.flan_t5_tokenizer.pad_token_id,
                eos_token_id=self.flan_t5_tokenizer.eos_token_id
            )
        
        # 디코딩
        response = self.flan_t5_tokenizer.decode(outputs[0], skip_special_tokens=True)
        return response
    
    async def generate_with_translation(
        self,
        query: str,
        context: str,
        references: List[Dict[str, Any]],
        translate_to_korean: bool = True,
        history: Optional[List[Dict[str, str]]] = None,
        system_prompt: Optional[str] = None
    ) -> str:
        """응답 생성 후 한국어로 번역"""
        
        # 영어로 응답 생성
        if not system_prompt:
            system_prompt = """You are Ready To Go, a friendly travel information assistant.
        You specialize in providing accurate information about visa requirements, insurance, and immigration procedures.
        
        IMPORTANT GUIDELINES:
        1. NEVER mention "based on the context" or "according to the provided context" or similar phrases
        2. Answer directly and naturally as if you know the information
        3. Be conversational and helpful
        4. If you have specific information about a topic, share it confidently
        5. If you don't have specific information, provide general helpful advice
        
        Remember: You are having a natural conversation with a traveler who needs help. Don't mention technical details about contexts or information sources."""
        
        # 이전 대화 기록이 있는 경우 컨텍스트에 포함
        messages = [{"role": "system", "content": system_prompt}]
        
        # history 추가 (이미 번역된 상태로 전달됨)
        if history and isinstance(history, list) and len(history) > 0:
            messages.extend(history)
        
        # 새로운 사용자 질문 추가
        if context and context.strip():
            user_prompt = f"""Query: {query}

Relevant Information:
{context}

Please provide a direct and natural answer to the query."""
        else:
            user_prompt = f"""Query: {query}

Please provide a helpful answer to this query."""
            
        messages.append({"role": "user", "content": user_prompt})

        # LLM 응답 생성
        if self.model_name.startswith("gpt-"):
            try:
                response = await self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0,  # 노트북과 동일하게 일관된 응답
                    max_tokens=1000
                )
                answer = response.choices[0].message.content
            except openai.RateLimitError as e:
                logger.warning(f"Rate limit reached: {e}")
                await asyncio.sleep(5)  # 5초 대기
                response = await self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0,
                    max_tokens=1000
                )
                answer = response.choices[0].message.content
            except openai.APIStatusError as e:
                logger.error(f"OpenAI API error: {e}")
                if e.status_code == 500:
                    # 500 오류의 경우 대체 모델 사용
                    logger.warning("Falling back to gpt-3.5-turbo due to 500 error")
                    response = await self.openai_client.chat.completions.create(
                        model="gpt-3.5-turbo",
                        messages=messages,
                        temperature=0,
                        max_tokens=1000
                    )
                    answer = response.choices[0].message.content
                else:
                    raise
        elif self.model_name.startswith("gemini-"):
            # Gemini 또는 다른 모델
            # history를 프롬프트에 추가
            history_text = ""
            if history and isinstance(history, list) and len(history) > 0:
                for h in history:
                    if h['role'] == 'user':
                        history_text += f"User: {h['content']}\n"
                    elif h['role'] == 'assistant':
                        history_text += f"Assistant: {h['content']}\n"
                history_text += "\n"
            full_prompt = f"{system_prompt}\n\n{history_text}User: {user_prompt}\nAssistant:"
            model = genai.GenerativeModel(self.model_name)
            response = model.generate_content(full_prompt)
            answer = response.text
        elif "t5" in self.model_name.lower():  # Flan-T5 모델
            # Flan-T5를 위한 프롬프트 형식
            # 파인튜닝된 모델은 한국어 질문에 직접 답변할 수 있도록 학습됨
        
            # 영어 질문
            if any(ord(char) >= 0xAC00 and ord(char) <= 0xD7A3 for char in query):
                query = self.ko_to_en.translate(query)
            t5_prompt = f"Answer the following question about travel:\n\nQuestion: {query}\n"
            if context:
                if any(ord(char) >= 0xAC00 and ord(char) <= 0xD7A3 for char in context):
                    translate_prompt = f"Translate the following text to English :\n\n{context}"
                    context = self.translator.invoke(translate_prompt).content
                t5_prompt += f"Context: {context}\n"
            t5_prompt += "Answer:"
            
            try:
                answer = self._generate_with_flan_t5(t5_prompt)
                logger.info("Flan-T5 response generated successfully")
                
                # 파인튜닝된 모델이 한국어로 학습되었다면 번역 스킵
                if translate_to_korean:
                    # 이미 한국어 응답이라면 번역 스킵
                    if any(ord(char) >= 0xAC00 and ord(char) <= 0xD7A3 for char in answer[:50]):
                        return answer
                        
            except Exception as e:
                logger.error(f"Error using Flan-T5 model: {e}")
                # 오류 발생 시 기본 GPT 모델로 폴백
                fallback_model = "gpt-3.5-turbo"
                logger.warning(f"Falling back to {fallback_model}")
                response = await self.openai_client.chat.completions.create(
                    model=fallback_model,
                    messages=messages,
                    temperature=0,
                    max_tokens=1000
                )
                answer = response.choices[0].message.content

        
        # 한국어로 번역
        if translate_to_korean:
            try:
                translate_prompt = f"Translate the following text to Korean. Make it sound natural and conversational, not like a translation. Keep the meaning intact:\n\n{answer}"
                
                # 번역할 내용이 이미 한국어인지 체크
                if any(ord(char) >= 0xAC00 and ord(char) <= 0xD7A3 for char in answer[:50]):
                    # 이미 한국어 포함되어 있으면 번역 스킵
                    return answer
                translated_answer = self.translator.invoke(translate_prompt)
                return translated_answer.content
            except Exception as e:
                logger.error(f"Translation error: {e}")
                return answer
        
        return answer
    
    async def generate(
        self,
        query: str,
        context: str = "",
        references: List[Dict[str, Any]] = None,
        stream: bool = False
    ) -> Union[str, AsyncGenerator[Dict[str, Any], None]]:
        """기존 generate 메서드 (수정)"""
        # 한국어 번역 기능 통합
        return await self.generate_with_translation(
            query=query,
            context=context,
            references=references or [],
            translate_to_korean=True
        )