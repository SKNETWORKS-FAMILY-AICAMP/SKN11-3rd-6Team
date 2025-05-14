import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import random
from datetime import datetime, timedelta
import uuid
import json
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from config import settings

from sqlalchemy.ext.declarative import declarative_base

from database import Document, Conversation, Message, COUNTRIES, TOPICS, SOURCES

# 샘플 데이터 생성을 위한 템플릿
VISA_TEMPLATES = {
    "United States": {
        "titles": [
            "미국 관광비자(B-2) 신청 가이드",
            "미국 학생비자(F-1) 준비 체크리스트",
            "미국 취업비자(H-1B) 신청 절차",
            "미국 비자 인터뷰 예상 질문과 답변",
            "ESTA 신청 방법 및 주의사항"
        ]
    },
    "Canada": {
        "titles": [
            "캐나다 관광비자(TRV) 신청 방법",
            "캐나다 학생비자 신청 절차",
            "캐나다 워킹홀리데이 프로그램 가이드",
            "eTA 신청 및 주의사항",
            "캐나다 영주권 Express Entry 시스템"
        ],
        "contents": [
            "캐나다 임시방문비자(TRV)는 온라인으로 신청 가능하며, 생체인식 정보 제공이 필요합니다.",
            "캐나다 학생비자 신청 시 입학허가서(LOA), 재정증명서, 학업계획서가 필요합니다.",
            "한국-캐나다 워킹홀리데이 프로그램은 연 4,000명 정원으로 운영되며, 만 18-30세 한국인이 지원 가능합니다.",
            "eTA는 항공편으로 캐나다 입국 시 필요한 전자여행허가로, 온라인으로 간편하게 신청할 수 있습니다.",
            "Express Entry는 연방 기술이민, 기술직종, 캐나다 경험 이민을 통합 관리하는 온라인 시스템입니다."
        ]
    },
    "Japan": {
        "titles": [
            "일본 단기체류 비자 면제 프로그램",
            "일본 취업비자 종류와 신청방법",
            "일본 유학비자 신청 가이드",
            "일본 워킹홀리데이 비자 안내",
            "일본 경영관리비자 취득 절차"
        ],
        "contents": [
            "한국 국민은 90일 이내 관광, 상용, 친지방문 목적으로 일본 방문 시 비자가 면제됩니다.",
            "일본 취업비자는 기술·인문지식·국제업무, 기능, 특정기능 등 여러 종류가 있으며 재류자격인정증명서가 필요합니다.",
            "일본 유학비자 신청 시 재류자격인정증명서, 입학허가서, 재정보증서류가 필요합니다.",
            "한일 워킹홀리데이 협정에 따라 만 18-30세 한국인은 최대 1년간 일본에서 체류하며 일할 수 있습니다.",
            "경영관리비자는 일본에서 사업을 시작하거나 경영에 참여하려는 외국인을 위한 비자입니다."
        ]
    }
}

INSURANCE_TEMPLATES = {
    "travel": {
        "titles": [
            "해외여행보험 가입 전 필수 체크사항",
            "여행자보험 보장내용 비교 가이드",
            "해외 의료비 청구 절차 안내",
            "여행보험 면책사항 주의점",
            "장기체류자를 위한 여행보험 선택법"
        ],
        "contents": [
            "해외여행보험 가입 시 의료비 보장한도, 휴대품 도난, 여행 취소/지연 보상 여부를 반드시 확인하세요.",
            "여행자보험은 질병/상해 치료비, 휴대품 손해, 배상책임, 항공기 지연 등을 보장합니다.",
            "해외에서 의료비 청구 시 진료기록, 영수증, 처방전을 반드시 보관하고 귀국 후 신청하세요.",
            "기존 질병, 위험한 스포츠, 음주 관련 사고는 보상에서 제외될 수 있으니 약관을 꼼꼼히 확인하세요.",
            "3개월 이상 장기체류 시에는 일반 여행보험보다 장기체류보험이나 현지 의료보험 가입을 고려하세요."
        ]
    },
    "health": {
        "titles": [
            "유학생 건강보험 가입 가이드",
            "해외 주재원 건강보험 선택 방법",
            "현지 의료보험 vs 한국 보험 비교",
            "긴급의료보험 가입 절차",
            "가족동반 시 건강보험 플랜"
        ],
        "contents": [
            "대부분의 국가에서 유학생은 의무적으로 건강보험에 가입해야 하며, 학교 단체보험이나 개인보험 중 선택할 수 있습니다.",
            "해외 주재원은 회사 제공 보험과 개인 추가 보험을 함께 가입하는 것이 일반적입니다.",
            "현지 의료보험은 해당 국가에서만 유효하지만, 한국 보험은 전 세계에서 사용 가능합니다.",
            "긴급의료보험은 갑작스러운 질병이나 사고에 대비한 단기 보험으로, 온라인으로 즉시 가입 가능합니다.",
            "가족동반 시에는 가족 전체를 커버하는 패밀리 플랜이 개별 가입보다 경제적입니다."
        ]
    }
}

IMMIGRATION_TEMPLATES = {
    "permanent": {
        "titles": [
            "투자이민 프로그램 비교 분석",
            "기술이민 점수제 시스템 이해하기",
            "가족초청 이민 절차와 요건",
            "난민 지위 신청 절차",
            "시민권 취득 요건과 절차"
        ],
        "contents": [
            "투자이민은 일정 금액 이상을 해당 국가에 투자하면 영주권을 받을 수 있는 프로그램입니다.",
            "기술이민은 나이, 학력, 경력, 언어능력 등을 점수화하여 일정 점수 이상이면 영주권을 신청할 수 있습니다.",
            "가족초청 이민은 영주권자나 시민권자가 직계가족을 초청하는 방식으로 진행됩니다.",
            "난민 지위는 본국에서 박해받을 우려가 있는 경우 신청할 수 있으며, 엄격한 심사를 거칩니다.",
            "시민권 취득을 위해서는 일정 기간 이상 거주, 언어시험 통과, 시민권 시험 합격이 필요합니다."
        ]
    },
    "temporary": {
        "titles": [
            "노동허가증 신청 절차",
            "학생비자에서 취업비자로 전환",
            "배우자 동반비자 신청 방법",
            "사업비자 취득 요건",
            "종교비자 신청 가이드"
        ],
        "contents": [
            "노동허가증은 고용주의 스폰서십이 필요하며, 직종에 따라 요구 조건이 다릅니다.",
            "졸업 후 일정 기간 내에 고용주를 찾아 취업비자로 전환 신청을 해야 합니다.",
            "주신청자의 배우자는 동반비자를 신청할 수 있으며, 일부 국가에서는 취업도 가능합니다.",
            "사업비자는 해당 국가에서 사업을 운영하려는 경우 필요하며, 사업계획서 제출이 필수입니다.",
            "종교비자는 종교 활동을 목적으로 하는 경우 발급되며, 종교단체의 초청장이 필요합니다."
        ]
    }
}

SAFETY_INFO_TEMPLATES = {
    "general": {
        "titles": [
            "해외 안전여행 기본 수칙",
            "긴급상황 시 대처방법",
            "현지 법규 및 문화 이해하기",
            "여행경보 단계별 주의사항",
            "해외 안전정보 확인 방법"
        ],
        "contents": [
            "여권과 비자는 복사본을 따로 보관하고, 현금은 분산해서 소지하며, 고가품은 자제하세요.",
            "긴급상황 시 현지 한국 영사관 연락처를 미리 저장하고, 영사콜센터 번호를 숙지하세요.",
            "현지의 법규와 문화를 사전에 조사하고 존중하며, 특히 복장 규정과 사진 촬영 제한을 확인하세요.",
            "여행경보는 1단계(여행유의)부터 4단계(여행금지)까지 있으며, 단계별로 주의사항이 다릅니다.",
            "외교부 해외안전여행 앱과 웹사이트에서 실시간 안전정보를 확인할 수 있습니다."
        ]
    },
    "health": {
        "titles": [
            "해외 여행 전 예방접종 안내",
            "지역별 풍토병 예방법",
            "의료 응급상황 대처 가이드",
            "여행자 건강 체크리스트",
            "귀국 후 건강관리 방법"
        ],
        "contents": [
            "여행 지역에 따라 필수 또는 권장 예방접종이 다르므로 출국 4-6주 전에 확인하고 접종하세요.",
            "말라리아, 뎅기열 등 모기 매개 질병 예방을 위해 방충제를 사용하고 긴 옷을 착용하세요.",
            "응급상황 시 현지 응급전화번호와 가까운 병원 위치를 미리 파악해두세요.",
            "상비약, 개인 처방약, 의료기록 영문 번역본을 준비하고 여행자보험에 가입하세요.",
            "귀국 후 2주 이내에 발열, 설사 등의 증상이 나타나면 즉시 의료기관을 방문하세요."
        ]
    }
}

def create_sample_data(session):
    """샘플 데이터 생성"""
    
    # 1. Document 데이터 생성
    documents = []
    
    # 비자 관련 문서
    for country in ["United States", "Canada", "Japan"]:
        country_data = VISA_TEMPLATES.get(country, {})
        for i, title in enumerate(country_data.get("titles", [])):
            doc = Document(
                title=title,
                url=f"https://example.com/{country.lower().replace(' ', '-')}/visa/{i+1}",
                country=country,
                topic="visa",
                source=random.choice(["Embassy", "Immigration Department"]),
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
            )
            documents.append(doc)
            session.add(doc)
    
    # 보험 관련 문서
    for insurance_type, data in INSURANCE_TEMPLATES.items():
        for i, title in enumerate(data.get("titles", [])):
            # 무작위로 국가 할당
            country = random.choice([c["name_en"] for c in COUNTRIES[:10]])
            doc = Document(
                title=title,
                url=f"https://example.com/insurance/{insurance_type}/{i+1}",
                country=country,
                topic="insurance",
                source="Insurance Agency",
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
            )
            documents.append(doc)
            session.add(doc)
    
    # 이민 관련 문서
    for imm_type, data in IMMIGRATION_TEMPLATES.items():
        for i, title in enumerate(data.get("titles", [])):
            country = random.choice([c["name_en"] for c in COUNTRIES[:10]])
            doc = Document(
                title=title,
                url=f"https://example.com/immigration/{imm_type}/{i+1}",
                country=country,
                topic="immigration",
                source="Immigration Department",
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
            )
            documents.append(doc)
            session.add(doc)
    
    # 안전정보 관련 문서
    for safety_type, data in SAFETY_INFO_TEMPLATES.items():
        for i, title in enumerate(data.get("titles", [])):
            country = random.choice([c["name_en"] for c in COUNTRIES[:10]])
            doc = Document(
                title=title,
                url=f"https://example.com/safety/{safety_type}/{i+1}",
                country=country,
                topic="safety_info",
                source="Government",
                created_at=datetime.utcnow() - timedelta(days=random.randint(1, 365))
            )
            documents.append(doc)
            session.add(doc)
    
    session.commit()
    print(f"Created {len(documents)} documents")
    
    # 2. Conversation 및 Message 데이터 생성
    conversations = []
    
    # 샘플 대화 시나리오
    sample_conversations = [
        {
            "country": "United States",
            "topic": "visa",
            "messages": [
                {"role": "user", "content": "미국 관광비자 신청하려고 하는데 어떤 서류가 필요한가요?"},
                {"role": "assistant", "content": "미국 관광비자(B-2) 신청을 위해서는 다음 서류들이 필요합니다:\n\n1. DS-160 온라인 신청서\n2. 유효한 여권\n3. 비자 수수료 납부 영수증\n4. 사진 (미국 비자 규격)\n5. 재정증명서\n6. 재직증명서 또는 사업자등록증\n\n추가로 인터뷰 예약이 필요합니다.", "references": [0, 3]},
                {"role": "user", "content": "인터뷰에서는 보통 어떤 질문들을 하나요?"},
                {"role": "assistant", "content": "미국 비자 인터뷰에서 자주 묻는 질문들:\n\n1. 방문 목적이 무엇인가요?\n2. 얼마나 체류할 예정인가요?\n3. 어디에 머물 예정인가요?\n4. 여행 경비는 누가 부담하나요?\n5. 한국에 가족이 있나요?\n6. 현재 직업은 무엇인가요?\n\n정직하고 일관성 있게 답변하는 것이 중요합니다.", "references": [3]}
            ]
        },
        {
            "country": "Canada",
            "topic": "immigration",
            "messages": [
                {"role": "user", "content": "캐나다 Express Entry 시스템에 대해 알려주세요"},
                {"role": "assistant", "content": "캐나다 Express Entry는 연방 기술이민 프로그램을 통합 관리하는 온라인 시스템입니다.\n\n주요 특징:\n- Federal Skilled Worker Program\n- Federal Skilled Trades Program\n- Canadian Experience Class\n\nCRS(Comprehensive Ranking System) 점수에 따라 선발되며, 나이, 학력, 경력, 언어능력 등이 평가됩니다.", "references": [4]},
                {"role": "user", "content": "필요한 언어 점수는 어느 정도인가요?"},
                {"role": "assistant", "content": "Express Entry를 위한 최소 언어 요구사항:\n\n영어 (IELTS 기준):\n- CLB 7 이상 (각 영역 6.0 이상)\n\n프랑스어 (TEF 기준):\n- NCLC 7 이상\n\n높은 언어 점수는 CRS 점수를 크게 향상시킬 수 있습니다.", "references": []}
            ]
        },
        {
            "country": "Japan",
            "topic": "visa",
            "messages": [
                {"role": "user", "content": "일본 워킹홀리데이 비자 신청 조건이 어떻게 되나요?"},
                {"role": "assistant", "content": "일본 워킹홀리데이 비자 신청 조건:\n\n1. 만 18-30세 한국 국민\n2. 부양가족 동반 불가\n3. 왕복 항공료와 초기 정착금 보유\n4. 건강한 신체\n5. 범죄 기록 없음\n\n연간 10,000명 정원으로 운영되며, 최대 1년간 체류 가능합니다.", "references": [8]},
                {"role": "user", "content": "신청은 어디서 하나요?"},
                {"role": "assistant", "content": "일본 워킹홀리데이 비자는 주한일본영사관에서 신청할 수 있습니다.\n\n신청 장소:\n- 서울: 주한일본대사관 영사부\n- 부산: 주부산일본총영사관\n- 제주: 주제주일본총영사관\n\n온라인 예약 후 방문하여 신청서를 제출하세요.", "references": []}
            ]
        },
        {
            "country": None,
            "topic": "insurance",
            "messages": [
                {"role": "user", "content": "해외여행보험은 언제 가입하는 게 좋을까요?"},
                {"role": "assistant", "content": "해외여행보험은 출발 전에 가입하는 것이 좋습니다.\n\n권장 가입 시기:\n- 출발 1-2주 전\n- 항공권 구매 직후\n\n조기 가입의 장점:\n- 여행 취소/변경 보장\n- 충분한 상품 비교 시간\n- 서류 준비 여유\n\n출국 당일 공항에서도 가입 가능하지만, 보장 내용이 제한적일 수 있습니다.", "references": [10, 14]},
                {"role": "user", "content": "어떤 보장들을 꼭 확인해야 하나요?"},
                {"role": "assistant", "content": "해외여행보험 필수 확인 사항:\n\n1. 의료비 보장한도\n   - 최소 1억원 이상 권장\n\n2. 휴대품 도난/손실\n   - 보상 한도 및 자기부담금\n\n3. 여행 취소/지연\n   - 보상 조건 확인\n\n4. 배상책임\n   - 타인에게 손해 발생 시\n\n5. 긴급의료후송\n   - 의료 상황 시 한국 송환\n\n면책사항도 반드시 확인하세요.", "references": [10, 13]}
            ]
        },
        {
            "country": None,
            "topic": "safety_info",
            "messages": [
                {"role": "user", "content": "해외여행 시 안전을 위한 기본 수칙은 뭐가 있나요?"},
                {"role": "assistant", "content": "해외여행 안전 기본 수칙:\n\n1. 여권/비자 복사본 별도 보관\n2. 현금 분산 소지\n3. 고가품 착용 자제\n4. 영사관 연락처 저장\n5. 여행자보험 가입\n6. 현지 법규/문화 사전 조사\n7. 야간 외출 자제\n8. 택시는 공식 택시 이용\n\n외교부 해외안전여행 앱도 설치하세요.", "references": [30, 34]},
                {"role": "user", "content": "응급상황이 발생하면 어떻게 해야 하나요?"},
                {"role": "assistant", "content": "해외 응급상황 대처법:\n\n1. 즉시 현지 응급번호로 연락\n   - 미국/캐나다: 911\n   - 유럽: 112\n   - 일본: 119\n\n2. 한국 영사관 연락\n   - 영사콜센터: +82-2-3210-0404\n\n3. 보험사 연락\n   - 24시간 핫라인 이용\n\n4. 가족에게 상황 전달\n\n평소에 응급 연락처를 정리해두세요.", "references": [31]}
            ]
        }
    ]
    
    # 대화 데이터 생성
    for i, conv_data in enumerate(sample_conversations):
        conversation = Conversation(
            session_id=str(uuid.uuid4()),
            country=conv_data.get("country"),
            topic=conv_data.get("topic"),
            created_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
        )
        session.add(conversation)
        session.commit()
        
        # 메시지 생성
        for j, msg_data in enumerate(conv_data["messages"]):
            references = None
            if "references" in msg_data and msg_data["references"]:
                # 참조 문서 정보를 JSON으로 저장
                ref_docs = []
                for ref_idx in msg_data["references"]:
                    if ref_idx < len(documents):
                        ref_docs.append({
                            "id": documents[ref_idx].id,
                            "title": documents[ref_idx].title,
                            "url": documents[ref_idx].url
                        })
                references = json.dumps(ref_docs, ensure_ascii=False)
            
            message = Message(
                conversation_id=conversation.id,
                role=msg_data["role"],
                content=msg_data["content"],
                references=references,
                created_at=conversation.created_at + timedelta(minutes=j*2)
            )
            session.add(message)
        
        conversations.append(conversation)
    
    session.commit()
    print(f"Created {len(conversations)} conversations with messages")
    
    return documents, conversations

def main():
    """메인 실행 함수"""
    # 데이터베이스 연결 설정
    engine = create_engine(settings.DATABASE_URL)
    SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    session = SessionLocal()
    
    try:
        # 기존 데이터 삭제 (선택적)
        session.query(Message).delete()
        session.query(Conversation).delete()
        session.query(Document).delete()
        session.commit()
        
        # 샘플 데이터 생성
        documents, conversations = create_sample_data(session)
        
        # 생성된 데이터 확인
        print(f"\n총 {session.query(Document).count()}개의 문서 생성됨")
        print(f"총 {session.query(Conversation).count()}개의 대화 생성됨")
        print(f"총 {session.query(Message).count()}개의 메시지 생성됨")
        
        # 샘플 데이터 조회
        print("\n=== 샘플 문서 ===")
        sample_docs = session.query(Document).limit(5).all()
        for doc in sample_docs:
            print(f"[{doc.country}][{doc.topic}] {doc.title}")
        
        print("\n=== 샘플 대화 ===")
        sample_convs = session.query(Conversation).limit(3).all()
        for conv in sample_convs:
            print(f"\n대화 ID: {conv.id}")
            print(f"국가: {conv.country}, 주제: {conv.topic}")
            for msg in conv.messages[:2]:
                print(f"  {msg.role}: {msg.content[:50]}...")
                if msg.references:
                    refs = json.loads(msg.references)
                    print(f"    참조: {[ref['title'][:30] + '...' for ref in refs]}")
    
    except Exception as e:
        print(f"Error: {e}")
        session.rollback()
    finally:
        session.close()

if __name__ == "__main__":
    main()