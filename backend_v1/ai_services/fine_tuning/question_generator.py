import hashlib
import json
import os
from dataclasses import dataclass
from typing import List, Dict, Set
from datetime import datetime

@dataclass
class Question:
    topic: str
    question: str
    country: str
    question_id: str = ""

class QuestionGenerator:
    def __init__(self):
        # self.countries = ["USA", "Australia", "Austria", "Canada", "China", "France", 
        #                  "Germany", "Italy", "Japan", "New Zealand", "Philippines", 
        #                  "Singapore", "UK"]
        self.countries = ["Canada"]
        self.topics = ["visa", "immigration", "insurance", "safety"]
        self.generated_ids = set()
        
        # 간소화된 템플릿
        self.templates = {
            "visa": [
                "What types of visas are available for {country}?",
                "How do I apply for a visa to {country}?", 
                "What documents are required for a {country} visa?",
                "How much does a {country} visa cost?",
                "What is the processing time for a {country} visa?",
                "Can I extend my {country} visa?",
                "What if my {country} visa is rejected?",
                "Can I work on a tourist visa in {country}?",
                "Do I need travel insurance for a {country} visa?",
                "What are the age requirements for a {country} working holiday visa?"
            ],
            "immigration": [
                "How can I immigrate to {country}?",
                "What are the requirements for {country} permanent residence?",
                "How long does {country} immigration process take?",
                "How much does it cost to immigrate to {country}?",
                "Can I sponsor my family to {country}?",
                "What are the benefits of {country} citizenship?",
                "Is there a citizenship test in {country}?",
                "Does {country} allow dual citizenship?",
                "What documents are required for {country} immigration?",
                "Can I lose my {country} permanent residence?"
            ],
            "insurance": [
                "Is health insurance mandatory in {country}?",
                "How much does health insurance cost in {country}?", 
                "What does health insurance cover in {country}?",
                "How do I get health insurance in {country}?",
                "What travel insurance is recommended for {country}?",
                "How do international students get insurance in {country}?",
                "How do I make an insurance claim in {country}?",
                "Are pre-existing conditions covered in {country}?",
                "Is car insurance mandatory in {country}?",
                "What if I need medical care without insurance in {country}?"
            ],
            "safety": [
                "How safe is {country} for tourists?",
                "What is the crime rate in {country}?",
                "Are there areas to avoid in {country}?",
                "What natural disasters occur in {country}?",
                "How safe are the roads in {country}?",
                "What's the emergency number in {country}?",
                "What vaccinations do I need for {country}?",
                "Is the tap water safe to drink in {country}?",
                "What precautions should I take in {country}?",
                "What should I do if robbed in {country}?"
            ]
        }

    def _generate_id(self, text: str) -> str:
        return hashlib.md5(text.encode()).hexdigest()[:10]

    def generate_questions(self, questions_per_topic: int = 1000) -> List[Question]:
        """각 나라별 토픽별로 지정된 개수만큼 질문 생성"""
        all_questions = []
        
        print(f"Starting question generation for {len(self.countries)} countries, {len(self.topics)} topics")
        print(f"Target: {questions_per_topic} questions per topic")
        
        for country in self.countries:
            print(f"\nGenerating questions for {country}...")
            for topic in self.topics:
                print(f"  Processing {topic}...", end=" ")
                questions = []
                base_templates = self.templates[topic]
                
                # 1. 기본 템플릿 사용
                for template in base_templates:
                    question_text = template.format(country=country)
                    question_id = self._generate_id(question_text)
                    
                    if question_id not in self.generated_ids:
                        questions.append(Question(
                            topic=topic,
                            question=question_text,
                            country=country,
                            question_id=question_id
                        ))
                        self.generated_ids.add(question_id)
                
                # 2. 추가 패턴들로 다양한 질문 생성
                additional_templates = [
                    # 일반적인 정보 요청
                    "What are the main requirements for {topic} in {country}?",
                    "How long does the {topic} process take in {country}?",
                    "What documents do I need for {topic} in {country}?",
                    "How much does {topic} cost in {country}?",
                    "Where can I apply for {topic} in {country}?",
                    "What are the steps for {topic} in {country}?",
                    "Is {topic} mandatory in {country}?",
                    "What happens if I don't have {topic} in {country}?",
                    "Can I get {topic} online in {country}?",
                    "What are the benefits of {topic} in {country}?",
                    
                    # 문제 해결 및 상황별
                    "What if my {topic} application is rejected in {country}?",
                    "How do I renew my {topic} in {country}?",
                    "Can I transfer my {topic} to another person in {country}?",
                    "What are the penalties for {topic} violations in {country}?",
                    "How do I check my {topic} status in {country}?",
                    "What if I lose my {topic} documents in {country}?",
                    "Can I appeal a {topic} decision in {country}?",
                    "What if my {topic} expires in {country}?",
                    "How do I update my {topic} information in {country}?",
                    "What are the common {topic} mistakes in {country}?",
                    
                    # 비교 및 대안
                    "What are the different types of {topic} in {country}?",
                    "How does {topic} compare to other countries from {country}?",
                    "What are the alternatives to {topic} in {country}?",
                    "Is {topic} the same for all nationalities in {country}?",
                    "What are the age requirements for {topic} in {country}?",
                    "Can families apply together for {topic} in {country}?",
                    "What are the language requirements for {topic} in {country}?",
                    "How does income affect {topic} in {country}?",
                    "What are the medical requirements for {topic} in {country}?",
                    "Can students get special {topic} rates in {country}?",
                    
                    # 시간성 및 계획
                    "When is the best time to apply for {topic} in {country}?",
                    "How far in advance should I apply for {topic} in {country}?",
                    "What is the {topic} processing time during peak season in {country}?",
                    "Can I expedite my {topic} application in {country}?",
                    "What are the {topic} office hours in {country}?",
                    "Is there a deadline for {topic} applications in {country}?",
                    "How often do {topic} requirements change in {country}?",
                    "What happens if I apply late for {topic} in {country}?",
                    "Can I get emergency {topic} in {country}?",
                    "What are the seasonal considerations for {topic} in {country}?",
                    
                    # 기술적 세부사항
                    "What forms do I need to fill out for {topic} in {country}?",
                    "How do I submit my {topic} application in {country}?",
                    "What payment methods are accepted for {topic} in {country}?",
                    "Can I track my {topic} application status in {country}?",
                    "What are the photo requirements for {topic} in {country}?",
                    "How do I schedule an appointment for {topic} in {country}?",
                    "What are the interview requirements for {topic} in {country}?",
                    "Can I submit additional documents for {topic} in {country}?",
                    "How do I withdraw my {topic} application in {country}?",
                    "What are the biometric requirements for {topic} in {country}?"
                ]
                
                # 3. 추가 템플릿으로 다양한 질문 생성
                for i, template in enumerate(additional_templates):
                    if len(questions) >= questions_per_topic:
                        break
                        
                    question_text = template.format(topic=topic, country=country)
                    question_id = self._generate_id(question_text)
                    
                    if question_id not in self.generated_ids:
                        questions.append(Question(
                            topic=topic,
                            question=question_text,
                            country=country,
                            question_id=question_id
                        ))
                        self.generated_ids.add(question_id)
                
                # 4. 여전히 부족하면 변형으로 채우기
                counter = 1
                base_questions = [q.question for q in questions[:20]]  # 처음 20개를 바탕으로 변형
                
                # 기본 변형 패턴들
                variation_patterns = [
                    "Tell me more about {question}",
                    "Can you provide details on {question}", 
                    "I need information about {question}",
                    "Help me understand {question}",
                    "What should I know regarding {question}",
                    "Could you clarify {question}",
                    "I'm curious about {question}",
                    "Please explain {question}",
                    "What exactly is {question}",
                    "Give me guidance on {question}"
                ]
                
                while len(questions) < questions_per_topic and counter <= 50:  # 최대 50번 반복
                    for base_q in base_questions:
                        if len(questions) >= questions_per_topic:
                            break
                            
                        for pattern in variation_patterns:
                            if len(questions) >= questions_per_topic:
                                break
                                
                            # 기본 질문에서 국가 제거하여 변형
                            clean_base = base_q.replace(f" in {country}", "").replace(f" for {country}", "").replace(f" to {country}", "")
                            clean_base = clean_base.rstrip("?")
                            
                            new_question = pattern.format(question=clean_base.lower()) + f" in {country}?"
                            question_id = self._generate_id(new_question + str(counter))  # 카운터로 유니크 ID 보장
                            
                            if question_id not in self.generated_ids:
                                questions.append(Question(
                                    topic=topic,
                                    question=new_question,
                                    country=country,
                                    question_id=question_id
                                ))
                                self.generated_ids.add(question_id)
                    
                    counter += 1
                
                final_count = min(len(questions), questions_per_topic)
                all_questions.extend(questions[:questions_per_topic])
                print(f"✓ {final_count} questions generated")
                
        print(f"\n🎉 Total questions generated: {len(all_questions)}")
        return all_questions

    def save_questions(self, questions: List[Question], filename: str):
        """질문들을 JSON 파일로 저장"""
        # 디렉토리가 없으면 생성
        os.makedirs(os.path.dirname(filename), exist_ok=True)
        
        data = {
            "metadata": {
                "total_questions": len(questions),
                "countries": self.countries,
                "topics": list(self.topics),
                "generated_date": datetime.now().isoformat()
            },
            "questions": [
                {
                    "id": q.question_id,
                    "topic": q.topic,
                    "question": q.question,
                    "country": q.country
                } for q in questions
            ]
        }
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        
        print(f"💾 Saved {len(questions)} questions to {filename}")
