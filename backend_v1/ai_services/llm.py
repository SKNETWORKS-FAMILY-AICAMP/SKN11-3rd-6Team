import logging
from typing import Dict, Any, Optional, List, Union, AsyncGenerator
import openai
from openai import AsyncOpenAI
import google.generativeai as genai
import os
import json
from langchain_openai import ChatOpenAI

from config import settings

logger = logging.getLogger(__name__)

class LLM:
    """번역 기능이 추가된 LLM 모듈"""
    
    def __init__(self, model_name: Optional[str] = None):
        self.model_name = self._get_best_model(model_name)
        
        # OpenAI 초기화
        if settings.OPENAI_API_KEY:
            self.openai_client = AsyncOpenAI(api_key=settings.OPENAI_API_KEY)
        
        # Gemini 초기화
        if settings.GOOGLE_API_KEY:
            genai.configure(api_key=settings.GOOGLE_API_KEY)
        
        # 번역기 초기화
        self.translator = ChatOpenAI(model="gpt-3.5-turbo", temperature=0, openai_api_key=settings.OPENAI_API_KEY)
    
    def _get_best_model(self, requested_model: Optional[str]) -> str:
        """파인튜닝된 모델이 있으면 사용"""
        if requested_model:
            return requested_model
        
        # 파인튜닝된 모델 정보 로드
        model_info_path = "./data/finetuned_models.json"
        if os.path.exists(model_info_path):
            try:
                with open(model_info_path, "r") as f:
                    model_info = json.load(f)
                    if model_info.get("model_id"):
                        logger.info(f"Using finetuned model: {model_info['model_id']}")
                        return model_info["model_id"]
            except Exception as e:
                logger.error(f"Error loading model info: {e}")
        
        # 기본 모델 사용
        return settings.DEFAULT_LLM_MODEL
    
    async def generate_with_translation(
        self,
        query: str,
        context: str,
        references: List[Dict[str, Any]],
        translate_to_korean: bool = True,
        history: Optional[List[Dict[str, str]]] = None
    ) -> str:
        """응답 생성 후 한국어로 번역"""
        
        # 영어로 응답 생성
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
            response = await self.openai_client.chat.completions.create(
                model=self.model_name,
                messages=messages,
                temperature=0,  # 노트북과 동일하게 일관된 응답
                max_tokens=1000
            )
            answer = response.choices[0].message.content
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
        else:
            # 파인튜닝된 모델 (OpenAI 파인튜닝 모델)
            try:
                logger.info(f"Using fine-tuned model: {self.model_name}")
                response = await self.openai_client.chat.completions.create(
                    model=self.model_name,
                    messages=messages,
                    temperature=0.2,
                    max_tokens=1000
                )
                answer = response.choices[0].message.content
                logger.info("Fine-tuned model response generated successfully")
            except Exception as e:
                logger.error(f"Error using fine-tuned model: {e}")
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