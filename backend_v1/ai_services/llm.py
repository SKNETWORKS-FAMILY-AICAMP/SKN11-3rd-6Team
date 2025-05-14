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
        system_prompt = """You are Ready To Go, a helpful travel information assistant.
        You specialize in providing accurate information about visa requirements, insurance, and immigration procedures.
        Provide clear and detailed answers based on the context provided."""
        
        user_prompt = f"""Query: {query}

        Context:
        {context}

        Please answer the query based on the provided context."""

        # history가 있으면 메시지 리스트에 자연스럽게 삽입
        messages = [{"role": "system", "content": system_prompt}]
        if history and isinstance(history, list) and len(history) > 0:
            # history는 [{"role": ..., "content": ...}, ...] 형식이어야 함
            messages.extend(history)
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
            # history를 프롬프트에 추가 (role: user/assistant 식으로 합침)
            history_text = ""
            if history and isinstance(history, list) and len(history) > 0:
                history_text = "\n".join([f"{h['role']}: {h['content']}" for h in history]) + "\n"
            full_prompt = f"{system_prompt}\n\n{history_text}{user_prompt}"
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
                translate_prompt = f"한국어로 출력해줘, Always respond in Korean, no matter the situation.:\n\n{answer}"
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