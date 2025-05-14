import re
import json
from typing import List, Dict
from dataclasses import dataclass
from datetime import datetime

@dataclass
class TopicQuestion:
    """Structure for topic-based questions"""
    topic: str
    question: str
    sub_topic: str = ""
    difficulty: str = "medium"  # easy, medium, hard
    
class EnglishQuestionGenerator:
    def __init__(self):
        self.countries = [
            "USA", "Australia", "Austria", "Canada", "China", "France", 
            "Germany", "Italy", "Japan", "New Zealand", "Philippines", 
            "Singapore", "UK"
        ]
        
        # 4 main topics
        self.topics = {
            "visa": "Visa",
            "immigration": "Immigration",
            "insurance": "Insurance",
            "safety": "Safety Information"
        }
        
        # Question templates for each topic
        self.topic_templates = {
            "visa": {
                "sub_topics": [
                    "types", "application process", "required documents", "fees", 
                    "processing time", "validity", "extension/renewal", "rejection reasons"
                ],
                "templates": [
                    # Basic information
                    "What types of visas are available for {country}?",
                    "What is a {visa_type} visa for {country}?",
                    "What are the visa requirements for {country}?",
                    
                    # Application process
                    "How do I apply for a {visa_type} visa to {country}?",
                    "Where can I apply for a {country} visa?",
                    "Can I apply for a {country} visa online?",
                    "What is the visa application process for {country}?",
                    
                    # Required documents
                    "What documents are required for a {country} {visa_type} visa?",
                    "Do I need proof of funds for a {country} visa?",
                    "Is a medical examination required for a {country} visa?",
                    "Do I need travel insurance for a {country} visa?",
                    
                    # Fees and timeline
                    "How much does a {country} {visa_type} visa cost?",
                    "What is the processing time for a {country} visa?",
                    "Is expedited processing available for {country} visas?",
                    "Are {country} visa fees refundable?",
                    
                    # Validity and stay
                    "How long is a {country} {visa_type} visa valid?",
                    "What is the maximum stay allowed on a {country} visa?",
                    "Can I enter {country} multiple times with my visa?",
                    "When should I apply for a {country} visa before travel?",
                    
                    # Extension and changes
                    "Can I extend my {country} visa?",
                    "Can I change my visa type while in {country}?",
                    "What happens if my {country} visa expires?",
                    "Can I work on a {visa_type} visa in {country}?",
                    
                    # Special situations
                    "What if my {country} visa is rejected?",
                    "Is an interview required for a {country} visa?",
                    "Can I apply for a {country} visa with a criminal record?",
                    "Do children need separate visas for {country}?",
                    
                    # Visa-specific questions
                    "What are the age requirements for a {country} working holiday visa?",
                    "Can I study on a tourist visa in {country}?",
                    "What is the minimum investment for a {country} investor visa?",
                    "Can I bring my family on a {country} work visa?"
                ]
            },
            
            "immigration": {
                "sub_topics": [
                    "permanent residence", "citizenship", "eligibility", "application process", 
                    "required documents", "costs", "processing time", "family sponsorship"
                ],
                "templates": [
                    # Basic information
                    "What are the immigration options for {country}?",
                    "What is permanent residence in {country}?",
                    "What's the difference between PR and citizenship in {country}?",
                    "How can I immigrate to {country}?",
                    
                    # Eligibility criteria
                    "What are the eligibility requirements for {country} immigration?",
                    "What are the requirements for skilled migration to {country}?",
                    "What is the minimum investment for {country} investor immigration?",
                    "Can I sponsor my family to immigrate to {country}?",
                    "What are the age limits for immigration to {country}?",
                    
                    # Application process
                    "What is the immigration application process for {country}?",
                    "How do I apply for permanent residence in {country}?",
                    "Do I need an immigration lawyer for {country}?",
                    "What is Express Entry for {country}?",
                    "How does the points system work for {country} immigration?",
                    
                    # Required documents
                    "What documents are required for {country} immigration?",
                    "Do I need to get my education credentials assessed for {country}?",
                    "What proof of funds is required for {country} immigration?",
                    "What medical examinations are required for {country} immigration?",
                    "Do I need police clearance for {country} immigration?",
                    
                    # Costs and timeline
                    "How much does it cost to immigrate to {country}?",
                    "How long does {country} immigration process take?",
                    "What are the government fees for {country} PR application?",
                    "Are there any hidden costs in {country} immigration?",
                    
                    # Permanent residence
                    "What are the benefits of {country} permanent residence?",
                    "How long is {country} PR valid?",
                    "What are the residency requirements for {country} PR?",
                    "Can I lose my {country} permanent residence?",
                    "Can I work anywhere in {country} with PR?",
                    
                    # Citizenship
                    "How do I apply for {country} citizenship?",
                    "What are the requirements for {country} citizenship?",
                    "Is there a citizenship test in {country}?",
                    "Does {country} allow dual citizenship?",
                    "How long do I need to wait for {country} citizenship after PR?",
                    
                    # Family matters
                    "Can I bring my spouse to {country}?",
                    "Can I sponsor my parents to {country}?",
                    "Are there age limits for dependent children in {country} immigration?",
                    "Can my family work in {country} on dependent visas?",
                    "What happens to my family's status if I lose my {country} PR?"
                ]
            },
            
            "insurance": {
                "sub_topics": [
                    "health insurance", "travel insurance", "student insurance", "car insurance",
                    "enrollment", "coverage", "premiums", "claims"
                ],
                "templates": [
                    # Basic information
                    "What types of insurance are available in {country}?",
                    "Is health insurance mandatory in {country}?",
                    "What's the difference between public and private insurance in {country}?",
                    "How does the healthcare system work in {country}?",
                    
                    # Health insurance
                    "How do I get health insurance in {country}?",
                    "How much does health insurance cost in {country}?",
                    "What does health insurance cover in {country}?",
                    "Is dental insurance separate in {country}?",
                    "Are prescriptions covered by insurance in {country}?",
                    "What is the waiting period for health insurance in {country}?",
                    
                    # Travel/visitor insurance
                    "What travel insurance is recommended for {country}?",
                    "Do I need insurance as a tourist in {country}?",
                    "What does travel insurance cover in {country}?",
                    "How much travel insurance do I need for {country}?",
                    
                    # Student insurance
                    "How do international students get insurance in {country}?",
                    "Is student health insurance mandatory in {country}?",
                    "How much does student insurance cost in {country}?",
                    "Can I use university health insurance in {country}?",
                    "What's the difference between university and private student insurance in {country}?",
                    
                    # Other insurance types
                    "Is car insurance mandatory in {country}?",
                    "Do I need home insurance in {country}?",
                    "What about life insurance in {country}?",
                    "Is liability insurance necessary in {country}?",
                    
                    # Premiums and payment
                    "How do I pay for insurance in {country}?",
                    "Can I get insurance premium refunds in {country}?",
                    "Are insurance premiums tax-deductible in {country}?",
                    "What factors affect insurance costs in {country}?",
                    
                    # Coverage issues
                    "Are pre-existing conditions covered in {country}?",
                    "What's excluded from insurance coverage in {country}?",
                    "Does insurance cover emergency room visits in {country}?",
                    "Is mental health covered by insurance in {country}?",
                    
                    # Claims process
                    "How do I make an insurance claim in {country}?",
                    "What documents are needed for insurance claims in {country}?",
                    "How long do insurance claims take in {country}?",
                    "Can I see any doctor with insurance in {country}?",
                    
                    # Special situations
                    "Is pregnancy covered by insurance in {country}?",
                    "What if I need medical care without insurance in {country}?",
                    "Can I use my home country insurance in {country}?",
                    "What about insurance for chronic conditions in {country}?"
                ]
            },
            
            "safety": {
                "sub_topics": [
                    "crime", "natural disasters", "traffic safety", "healthcare", 
                    "emergency contacts", "precautions", "regional safety", "health risks"
                ],
                "templates": [
                    # General safety
                    "How safe is {country} for tourists?",
                    "What is the crime rate in {country}?",
                    "Is {country} safe for solo travelers?",
                    "Is {country} safe for women travelers?",
                    "What are the safest cities in {country}?",
                    
                    # Crime-related
                    "What types of crime are common in {country}?",
                    "Are there areas to avoid in {country}?",
                    "Is pickpocketing common in {country}?",
                    "Is it safe to walk at night in {country}?",
                    "How safe is public transportation in {country}?",
                    
                    # Regional safety
                    "Are there dangerous areas in {country}?",
                    "Which regions should tourists avoid in {country}?",
                    "Is the capital city of {country} safe?",
                    "Are rural areas safe in {country}?",
                    "What about border areas in {country}?",
                    
                    # Natural disasters
                    "What natural disasters occur in {country}?",
                    "Is {country} prone to earthquakes?",
                    "When is typhoon/hurricane season in {country}?",
                    "Are there flood-prone areas in {country}?",
                    "What about volcanic activity in {country}?",
                    
                    # Traffic and road safety
                    "How safe are the roads in {country}?",
                    "What are the traffic laws in {country}?",
                    "Is it safe to drive in {country}?",
                    "What's the emergency number for accidents in {country}?",
                    "Do I need an international driving permit in {country}?",
                    
                    # Healthcare and medical
                    "What's the quality of healthcare in {country}?",
                    "How do I find hospitals in {country}?",
                    "Are medications easily available in {country}?",
                    "What vaccinations do I need for {country}?",
                    "Is the tap water safe to drink in {country}?",
                    
                    # Emergency contacts
                    "What's the emergency number in {country}?",
                    "How do I contact police in {country}?",
                    "Where is the nearest embassy/consulate in {country}?",
                    "Is there a tourist helpline in {country}?",
                    "How do I get emergency medical help in {country}?",
                    
                    # Precautions and tips
                    "What precautions should I take in {country}?",
                    "What are common scams in {country}?",
                    "Is food poisoning common in {country}?",
                    "What cultural sensitivities should I be aware of in {country}?",
                    "What items are illegal to bring into {country}?",
                    
                    # Current situations
                    "What are the COVID-19 restrictions in {country}?",
                    "Is there political instability in {country}?",
                    "Are there any travel warnings for {country}?",
                    "What's the terrorism risk in {country}?",
                    "Are protests common in {country}?"
                ]
            }
        }
        
        # Visa types for detailed questions
        self.visa_types = {
            "tourist": ["B-2", "visitor", "holiday"],
            "student": ["F-1", "M-1", "study"],
            "work": ["H-1B", "employment", "skilled worker"],
            "business": ["B-1", "investor", "entrepreneur"],
            "family": ["spouse", "dependent", "relative"],
            "working holiday": ["WHV", "youth mobility"],
            "transit": ["C", "airport transit"],
            "retirement": ["pensioner", "retiree"],
            "medical": ["treatment", "healthcare"],
            "diplomatic": ["official", "government"]
        }

    def generate_topic_questions(self, country: str, topic: str) -> List[TopicQuestion]:
        """Generate questions for a specific country and topic"""
        questions = []
        
        if topic not in self.topic_templates:
            return questions
        
        topic_info = self.topic_templates[topic]
        
        for template in topic_info["templates"]:
            # Generate basic questions
            if "{visa_type}" not in template:
                question = template.format(country=country)
                questions.append(TopicQuestion(
                    topic=topic,
                    question=question,
                    difficulty=self._determine_difficulty(template)
                ))
            else:
                # Generate visa type specific questions
                for visa_type, _ in self.visa_types.items():
                    question = template.format(
                        country=country, 
                        visa_type=visa_type
                    )
                    questions.append(TopicQuestion(
                        topic=topic,
                        question=question,
                        sub_topic=visa_type,
                        difficulty=self._determine_difficulty(template)
                    ))
        
        return questions

    def generate_comparative_questions(self, topic: str) -> List[TopicQuestion]:
        """Generate comparative questions between countries"""
        comparative_templates = {
            "visa": [
                "Which country has easier visa requirements: {country1} or {country2}?",
                "How do visa fees compare between {country1} and {country2}?",
                "Which country has faster visa processing: {country1} or {country2}?",
                "What's the difference in visa validity between {country1} and {country2}?"
            ],
            "immigration": [
                "Which country is better for immigration: {country1} or {country2}?",
                "How do PR requirements compare between {country1} and {country2}?",
                "Which country has lower immigration costs: {country1} or {country2}?",
                "How do citizenship timelines compare between {country1} and {country2}?"
            ],
            "insurance": [
                "How do healthcare systems compare between {country1} and {country2}?",
                "Which country has cheaper health insurance: {country1} or {country2}?",
                "What's the difference in coverage between {country1} and {country2}?",
                "Which country has better public healthcare: {country1} or {country2}?"
            ],
            "safety": [
                "Which country is safer: {country1} or {country2}?",
                "How do crime rates compare between {country1} and {country2}?",
                "Which country has better healthcare facilities: {country1} or {country2}?",
                "How do natural disaster risks compare between {country1} and {country2}?"
            ]
        }
        
        questions = []
        templates = comparative_templates.get(topic, [])
        
        # Generate country pairs
        for i in range(len(self.countries)):
            for j in range(i+1, min(i+3, len(self.countries))):  # Limit combinations
                for template in templates:
                    question = template.format(
                        country1=self.countries[i],
                        country2=self.countries[j]
                    )
                    questions.append(TopicQuestion(
                        topic=topic,
                        question=question,
                        difficulty="hard"
                    ))
        
        return questions

    def generate_situational_questions(self, country: str, topic: str) -> List[TopicQuestion]:
        """Generate situation-specific questions"""
        situational_templates = {
            "visa": {
                "emergencies": [
                    "What if my visa expires while I'm in {country}?",
                    "What if I lose my passport with the {country} visa?",
                    "Can I reapply immediately if my {country} visa is rejected?",
                    "What if I need to leave and re-enter {country} urgently?"
                ],
                "special_cases": [
                    "Can pregnant women apply for {country} visas?",
                    "Can I apply for a {country} visa with a criminal record?",
                    "What if my passport expires during the {country} visa validity?",
                    "Can I change employers on a {country} work visa?"
                ]
            },
            "immigration": {
                "family_situations": [
                    "What if my child is born in {country} during immigration?",
                    "Can I bring my elderly parents to {country}?",
                    "What happens to my {country} PR if I divorce?",
                    "Can my adult children immigrate with me to {country}?"
                ],
                "work_situations": [
                    "Can I start a business after immigrating to {country}?",
                    "Can PR holders work for the government in {country}?",
                    "What if I lose my job after getting {country} PR?",
                    "Can I work remotely for a foreign company with {country} PR?"
                ]
            },
            "insurance": {
                "medical_emergencies": [
                    "What if I need emergency treatment without insurance in {country}?",
                    "Are ambulance services covered by insurance in {country}?",
                    "What if I get sick before my {country} insurance starts?",
                    "Can I get emergency dental care in {country}?"
                ],
                "special_conditions": [
                    "Can I get insurance with pre-existing conditions in {country}?",
                    "Is maternity care covered by insurance in {country}?",
                    "What about mental health treatment in {country}?",
                    "Are alternative therapies covered in {country}?"
                ]
            },
            "safety": {
                "emergency_situations": [
                    "What should I do if robbed in {country}?",
                    "How do I handle a medical emergency in {country}?",
                    "What if there's a natural disaster while in {country}?",
                    "Who do I contact if arrested in {country}?"
                ],
                "daily_safety": [
                    "How can I avoid scams in {country}?",
                    "Is it safe to use ATMs in {country}?",
                    "What areas should I avoid at night in {country}?",
                    "How reliable are taxis in {country}?"
                ]
            }
        }
        
        questions = []
        if topic in situational_templates:
            for situation, templates in situational_templates[topic].items():
                for template in templates:
                    question = template.format(country=country)
                    questions.append(TopicQuestion(
                        topic=topic,
                        question=question,
                        sub_topic=situation,
                        difficulty="hard"
                    ))
        
        return questions

    def generate_faq_questions(self, country: str) -> List[TopicQuestion]:
        """Generate FAQ-style questions"""
        faq_templates = [
            "What are the top 5 things to know before visiting {country}?",
            "What are common mistakes tourists make in {country}?",
            "What's the cost of living in {country}?",
            "How easy is it to find English speakers in {country}?",
            "What's the best time to visit {country}?",
            "What cultural differences should I expect in {country}?",
            "How does {country} compare to neighboring countries?",
            "What are the must-know laws in {country}?",
            "How tourist-friendly is {country}?",
            "What should first-time visitors to {country} know?"
        ]
        
        questions = []
        for template in faq_templates:
            question = template.format(country=country)
            questions.append(TopicQuestion(
                topic="general",
                question=question,
                difficulty="easy"
            ))
        
        return questions

    def generate_specific_scenario_questions(self) -> List[TopicQuestion]:
        """Generate questions for specific user scenarios"""
        scenarios = {
            "students": [
                "Can I work part-time as a student in {country}?",
                "How do I extend my student visa in {country}?",
                "Can I bring my spouse on a student visa to {country}?",
                "What happens after I graduate in {country}?"
            ],
            "workers": [
                "Can I change jobs on a work visa in {country}?",
                "How do I convert from work visa to PR in {country}?",
                "Can my family work on dependent visas in {country}?",
                "What are my rights as a foreign worker in {country}?"
            ],
            "retirees": [
                "What are retirement visa options for {country}?",
                "Can I access healthcare as a retiree in {country}?",
                "What's the cost of retirement in {country}?",
                "Are pensions taxed in {country}?"
            ],
            "digital_nomads": [
                "Does {country} offer digital nomad visas?",
                "Can I work remotely on a tourist visa in {country}?",
                "What's the internet connectivity like in {country}?",
                "Are there co-working spaces in {country}?"
            ]
        }
        
        questions = []
        for scenario, templates in scenarios.items():
            for country in self.countries[:5]:  # Limit to avoid too many questions
                for template in templates:
                    question = template.format(country=country)
                    questions.append(TopicQuestion(
                        topic="general",
                        question=question,
                        sub_topic=scenario,
                        difficulty="medium"
                    ))
        
        return questions

    def _determine_difficulty(self, template: str) -> str:
        """Determine question difficulty"""
        easy_keywords = ["what", "which", "how much", "is", "are", "can i"]
        hard_keywords = ["compare", "difference", "vs", "pros and cons", "complex", "detailed"]
        
        template_lower = template.lower()
        
        if any(keyword in template_lower for keyword in hard_keywords):
            return "hard"
        elif any(keyword in template_lower for keyword in easy_keywords):
            return "easy"
        else:
            return "medium"

    def generate_all_questions(self) -> Dict[str, List[TopicQuestion]]:
        """Generate all questions organized by category"""
        all_questions = {
            "by_topic": {},
            "by_country": {},
            "by_difficulty": {"easy": [], "medium": [], "hard": []},
            "comparative": [],
            "faq": [],
            "scenarios": []
        }
        
        # Generate topic and country specific questions
        for topic in self.topics.keys():
            all_questions["by_topic"][topic] = []
            
            for country in self.countries:
                if country not in all_questions["by_country"]:
                    all_questions["by_country"][country] = []
                
                # Basic questions
                basic_questions = self.generate_topic_questions(country, topic)
                all_questions["by_topic"][topic].extend(basic_questions)
                all_questions["by_country"][country].extend(basic_questions)
                
                # Situational questions
                situational = self.generate_situational_questions(country, topic)
                all_questions["by_topic"][topic].extend(situational)
                all_questions["by_country"][country].extend(situational)
                
                # Categorize by difficulty
                for q in basic_questions + situational:
                    all_questions["by_difficulty"][q.difficulty].append(q)
            
            # Comparative questions
            comparative = self.generate_comparative_questions(topic)
            all_questions["comparative"].extend(comparative)
        
        # FAQ style questions
        for country in self.countries:
            faq = self.generate_faq_questions(country)
            all_questions["faq"].extend(faq)
        
        # Scenario-based questions
        scenario_questions = self.generate_specific_scenario_questions()
        all_questions["scenarios"].extend(scenario_questions)
        
        return all_questions

    def export_questions(self, filename: str = "english_questions.json") -> Dict:
        """Export generated questions to JSON file"""
        all_questions = self.generate_all_questions()
        
        # Convert to JSON-serializable format
        export_data = {
            "metadata": {
                "total_questions": sum(
                    len(questions) for questions in all_questions["by_topic"].values()
                ),
                "topics": list(self.topics.keys()),
                "countries": self.countries,
                "generated_date": datetime.now().isoformat(),
                "language": "English"
            },
            "questions": {}
        }
        
        # Convert TopicQuestion objects to dictionaries
        for category, data in all_questions.items():
            if isinstance(data, dict):
                export_data["questions"][category] = {}
                for key, questions in data.items():
                    export_data["questions"][category][key] = [
                        {
                            "topic": q.topic,
                            "question": q.question,
                            "sub_topic": q.sub_topic,
                            "difficulty": q.difficulty
                        } for q in questions
                    ]
            else:
                export_data["questions"][category] = [
                    {
                        "topic": q.topic,
                        "question": q.question,
                        "sub_topic": q.sub_topic,
                        "difficulty": q.difficulty
                    } for q in data
                ]
        
        # Save to file
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        print(f"Generated {export_data['metadata']['total_questions']} questions")
        print(f"Saved to: {filename}")
        
        # Print statistics
        self._print_statistics(all_questions)
        
        return export_data

    def _print_statistics(self, all_questions: Dict):
        """Print generation statistics"""
        print("\n=== Question Generation Statistics ===")
        
        # Topic statistics
        print("\nQuestions by topic:")
        for topic, questions in all_questions["by_topic"].items():
            print(f"  {self.topics[topic]}: {len(questions)} questions")
        
        # Difficulty statistics
        print("\nQuestions by difficulty:")
        for difficulty, questions in all_questions["by_difficulty"].items():
            print(f"  {difficulty}: {len(questions)} questions")
        
        # Country statistics (top 3)
        print("\nQuestions by country (top 3):")
        country_counts = {
            country: len(questions) 
            for country, questions in all_questions["by_country"].items()
        }
        sorted_countries = sorted(
            country_counts.items(), 
            key=lambda x: x[1], 
            reverse=True
        )[:3]
        for country, count in sorted_countries:
            print(f"  {country}: {count} questions")
        
        print(f"\nComparative questions: {len(all_questions['comparative'])}")
        print(f"FAQ questions: {len(all_questions['faq'])}")
        print(f"Scenario questions: {len(all_questions['scenarios'])}")

# Usage example
if __name__ == "__main__":
    # Initialize generator
    generator = EnglishQuestionGenerator()
    
    # Generate and export all questions
    generator.export_questions()
    
    # Generate questions for specific country and topic
    usa_visa_questions = generator.generate_topic_questions("USA", "visa")
    print(f"\nGenerated {len(usa_visa_questions)} USA visa questions")
    print("\nSample questions:")
    for q in usa_visa_questions[:5]:
        print(f"- {q.question} (Difficulty: {q.difficulty})")