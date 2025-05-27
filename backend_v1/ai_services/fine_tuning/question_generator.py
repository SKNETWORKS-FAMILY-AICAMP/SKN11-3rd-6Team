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
        # self.countries = ["America", "Australia", "Austria", "Canada", "China", "France", 
        #                  "Germany", "Italy", "Japan", "New Zealand", "Philippines", 
        #                  "Singapore", "UK"]
        self.countries = ["Australia", "UK", "Canada", "America", "Japan"]
        self.topics = ["visa"]
        # self.topics = ["visa", "immigration", "insurance", "safety"]
        self.generated_ids = set()
        self.question_counts = {}  # 질문별 등장 횟수 추적  
        self.max_duplicates = 3    # 최대 3번까지 허용
        
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
                "What are the entry requirements for {country}?",
                "Do I need a passport to enter {country}?",
                "What documents do I need to enter {country}?",
                "How long can I stay in {country} without a visa?",
                "What are the customs regulations when entering {country}?",
                "What items are prohibited when entering {country}?",
                "Do I need to declare money when entering {country}?",
                "What are the quarantine requirements for {country}?",
                "Can I bring food into {country}?",
                "What are the duty-free allowances for {country}?"
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
    
    def _can_add_question(self, question_text: str) -> bool:
        """질문을 추가할 수 있는지 확인 (최대 3번까지 허용)"""
        current_count = self.question_counts.get(question_text, 0)
        return current_count < self.max_duplicates
    
    def _add_question_if_possible(self, topic: str, question_text: str, country: str, questions: List[Question]) -> bool:
        """가능하면 질문을 추가하고 True 반환"""
        if self._can_add_question(question_text):
            question_id = self._generate_id(question_text + str(self.question_counts.get(question_text, 0)))
            self.question_counts[question_text] = self.question_counts.get(question_text, 0) + 1
            
            questions.append(Question(
                topic=topic, 
                question=question_text, 
                country=country, 
                question_id=question_id
            ))
            return True
        return False

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
                    self._add_question_if_possible(topic, question_text, country, questions)
                
                # 2. 추가 패턴들로 다양한 질문 생성
                additional_templates = [
                    # 일반적인 정보 요청 (토픽에 맞게 수정)
                    "What are the main requirements for {topic} in {country}?" if topic in ["visa", "insurance"] else "What are the main {topic} concerns in {country}?",
                    "How long does the {topic} process take in {country}?" if topic in ["visa", "insurance"] else "How can I stay safe regarding {topic} in {country}?",
                    "What documents do I need for {topic} in {country}?" if topic in ["visa", "immigration"] else "What should I know about {topic} in {country}?",
                    "How much does {topic} cost in {country}?" if topic in ["visa", "insurance"] else "What are the {topic} guidelines in {country}?",
                    "Where can I apply for {topic} in {country}?" if topic in ["visa", "insurance"] else "Where can I get {topic} information in {country}?",
                    "What are the steps for {topic} in {country}?" if topic in ["visa", "immigration"] else "What {topic} precautions should I take in {country}?",
                    "Is {topic} mandatory in {country}?" if topic == "insurance" else "What are the {topic} rules in {country}?",
                    "What happens if I don't have {topic} in {country}?" if topic == "insurance" else "What should I avoid regarding {topic} in {country}?",
                    "Can I get {topic} online in {country}?" if topic in ["visa", "insurance"] else "How do I prepare for {topic} issues in {country}?",
                    "What are the benefits of {topic} in {country}?" if topic == "insurance" else "What are the common {topic} mistakes in {country}?",
                    
                    # 추가 다양한 패턴들
                    "What do I need to know about {topic} in {country}?",
                    "How does {topic} work in {country}?",
                    "What are the {topic} options in {country}?",
                    "What should I expect with {topic} in {country}?",
                    "How can I get help with {topic} in {country}?",
                    "What are the latest {topic} updates in {country}?",
                    "How do I choose the right {topic} in {country}?",
                    "What are the {topic} restrictions in {country}?",
                    "How do I compare {topic} options in {country}?",
                    "What {topic} advice do you have for {country}?",
                    
                    # 상황별 질문
                    "What {topic} information do I need for first-time visitors to {country}?",
                    "How does {topic} differ for tourists vs residents in {country}?",
                    "What {topic} considerations are there for families in {country}?",
                    "How do students handle {topic} in {country}?",
                    "What {topic} options exist for business travelers to {country}?",
                    "How does {topic} work for elderly visitors to {country}?",
                    "What {topic} requirements apply to children in {country}?",
                    "How do I handle {topic} for emergency travel to {country}?",
                    "What {topic} rules apply during peak season in {country}?",
                    "How does {topic} change during holidays in {country}?",
                    
                    # 비교 및 선택
                    "How do I compare different {topic} providers in {country}?",
                    "What are the pros and cons of {topic} in {country}?",
                    "Which {topic} option is best for short stays in {country}?",
                    "What {topic} choice is recommended for long visits to {country}?",
                    "How does {topic} in {country} compare to other countries?",
                    "What makes {topic} in {country} unique?",
                    "Which {topic} features are most important in {country}?",
                    "How do I decide between {topic} alternatives in {country}?",
                    "What {topic} factors should I prioritize in {country}?",
                    "How do locals handle {topic} in {country}?",
                    
                    # 문제 해결
                    "What if I have problems with {topic} in {country}?",
                    "How do I resolve {topic} issues in {country}?",
                    "Who can help me with {topic} problems in {country}?",
                    "What are common {topic} challenges in {country}?",
                    "How do I avoid {topic} complications in {country}?",
                    "What backup plans exist for {topic} in {country}?",
                    "How do I get emergency {topic} assistance in {country}?",
                    "What should I do if {topic} goes wrong in {country}?",
                    "How do I recover from {topic} setbacks in {country}?",
                    "What {topic} mistakes should I avoid in {country}?",
                    
                    # 시간 관련
                    "When should I arrange {topic} for {country}?",
                    "How far ahead should I plan {topic} for {country}?",
                    "What's the best timing for {topic} in {country}?",
                    "How does {topic} timing affect costs in {country}?",
                    "When is {topic} processing fastest in {country}?",
                    "What {topic} deadlines should I know for {country}?",
                    "How do seasonal changes affect {topic} in {country}?",
                    "What {topic} schedules should I be aware of in {country}?",
                    "How do I time {topic} applications for {country}?",
                    "When do {topic} requirements change in {country}?",
                    
                    # 비용 관련
                    "How much should I budget for {topic} in {country}?",
                    "What are hidden {topic} costs in {country}?",
                    "How can I save money on {topic} in {country}?",
                    "What affects {topic} pricing in {country}?",
                    "Are there {topic} discounts available in {country}?",
                    "How do I pay for {topic} in {country}?",
                    "What {topic} fees should I expect in {country}?",
                    "How do {topic} costs vary by region in {country}?",
                    "What's the typical {topic} expense in {country}?",
                    "How do I get {topic} cost estimates for {country}?"
                ]
                
                # 3. 추가 템플릿으로 다양한 질문 생성
                for template in additional_templates:
                    if len(questions) >= questions_per_topic:
                        break
                    question_text = template.format(topic=topic, country=country)
                    self._add_question_if_possible(topic, question_text, country, questions)
                
                # 4. 더 많은 변형 패턴으로 900개 목표 달성
                if len(questions) < questions_per_topic:
                    # 기존 질문들을 바탕으로 더 다양한 변형 생성
                    base_questions = questions[:min(50, len(questions))]  # 더 많은 베이스 질문 사용
                    
                    # 확장된 변형 패턴들
                    variation_patterns = [
                        "Can you tell me about {question}",
                        "I need help with {question}", 
                        "Could you explain {question}",
                        "What should I know about {question}",
                        "Please provide information on {question}",
                        "Help me understand {question}",
                        "I'm curious about {question}",
                        "Could you clarify {question}",
                        "What exactly is {question}",
                        "Give me details about {question}",
                        "I want to learn about {question}",
                        "Can you guide me on {question}",
                        "What's important about {question}",
                        "Tell me more about {question}",
                        "I need guidance on {question}"
                    ]
                    
                    # 추가 질문 접두사
                    question_prefixes = [
                        "As a tourist, ",
                        "As a first-time visitor, ",
                        "For someone traveling alone, ",
                        "For a family trip, ",
                        "For business travel, ",
                        "For students, ",
                        "For elderly travelers, ",
                        "For budget travelers, ",
                        "For luxury travel, ",
                        "For emergency situations, ",
                        "For long-term stays, ",
                        "For short visits, ",
                        "During peak season, ",
                        "During off-season, ",
                        "For weekend trips, "
                    ]
                    
                    # 베이스 질문들로 다양한 변형 생성
                    for base_q in base_questions:
                        if len(questions) >= questions_per_topic:
                            break
                            
                        clean_base = base_q.question.replace(f" in {country}", "").replace(f" for {country}", "").replace(f" to {country}", "")
                        clean_base = clean_base.rstrip("?").lower()
                        
                        # 일반 변형 패턴
                        for pattern in variation_patterns:
                            if len(questions) >= questions_per_topic:
                                break
                            new_question = pattern.format(question=clean_base) + f" in {country}?"
                            self._add_question_if_possible(topic, new_question, country, questions)
                        
                        # 접두사 추가 변형
                        for prefix in question_prefixes:
                            if len(questions) >= questions_per_topic:
                                break
                            new_question = prefix + clean_base + f" in {country}?"
                            self._add_question_if_possible(topic, new_question, country, questions)
                    
                    # 여전히 부족하면 추가 조합 생성
                    if len(questions) < questions_per_topic:
                        # 토픽별 특수 키워드
                        topic_keywords = {
                            "visa": ["application", "requirements", "processing", "approval", "extension", "renewal"],
                            "immigration": ["entry", "customs", "border", "arrival", "departure", "transit"],
                            "insurance": ["coverage", "claims", "premium", "policy", "benefits", "provider"],
                            "safety": ["security", "precautions", "emergency", "risks", "protection", "awareness"]
                        }
                        
                        # 키워드 조합으로 추가 질문 생성
                        for keyword in topic_keywords.get(topic, []):
                            if len(questions) >= questions_per_topic:
                                break
                            
                            keyword_questions = [
                                f"What {keyword} information do I need for {country}?",
                                f"How does {keyword} work in {country}?",
                                f"What are the {keyword} procedures in {country}?",
                                f"Where can I get {keyword} help in {country}?",
                                f"What {keyword} tips do you have for {country}?",
                                f"How do I handle {keyword} issues in {country}?",
                                f"What are the {keyword} options in {country}?",
                                f"How much does {keyword} cost in {country}?",
                                f"When should I consider {keyword} for {country}?",
                                f"What {keyword} mistakes should I avoid in {country}?"
                            ]
                            
                            for kq in keyword_questions:
                                if len(questions) >= questions_per_topic:
                                    break
                                self._add_question_if_possible(topic, kq, country, questions)
                
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
