import requests
import json
import urllib.parse

country_names = [
    "미국",
    "중국",
    "일본",
    "캐나다",
    "호주",
    "독일",
    "베트남",
    "필리핀",
    "인도네시아",
    "태국",
    "영국",
    "싱가포르",
    "말레이시아",
    "스페인",
    "뉴질랜드",
    "러시아",
    "프랑스",
    "이탈리아",
    "오스트리아",
    "홍콩"
]

for country_name in country_names:
    # 완전히 동일한 URL 사용 (curl에서 사용한 것과 동일)
    base_url = "http://apis.data.go.kr/1262000/CountrySafetyService6/getCountrySafetyList6"
    service_key = "R8KqK3WFsimh7fJrzqadqVDfMMOTp5TVf4soCDUGJAmOoi41fRZNTWC0JfrOjntRBiMIIhByHlKDjK%2BWPK9hIQ%3D%3D"

    # country_name을 URL 인코딩
    encoded_country = urllib.parse.quote(country_name)

    # 전체 URL 구성
    full_url = f"{base_url}?serviceKey={service_key}&numOfRows=5&pageNo=1&cond[country_nm%3A%3AEQ]={encoded_country}"
    
    try:
        # 직접 URL 호출 (파라미터 분리 없이)
        response = requests.get(full_url)
    
        # JSON 파싱
        if response.status_code == 200:
            data = json.loads(response.text)
        
        # 응답 구조 확인
        if 'response' in data and 'body' in data['response']:
            body = data['response']['body']
            
            # 에러 체크
            if 'items' not in body or not body['items']:
                print("\n데이터를 찾을 수 없습니다.")
            else:
                # 실제 데이터 파싱
                items = body['items']['item']
                print(f"\n찾은 항목 수: {len(items)}")
                
                for idx, item in enumerate(items):
                    title = item.get('title', 'N/A')
                    txt_origin_cn = item.get('txt_origin_cn', 'N/A')
                    country = item.get('country_nm', 'N/A')
                    
                    print(f"\n항목 {idx + 1}:")
                    print(f"국가: {country}")
                    print(f"제목: {title}")
                    if txt_origin_cn:
                        print(f"내용: {txt_origin_cn}")
                    else:
                        print("내용: 내용이 없습니다.")
        else:
            print("\nAPI 응답 구조가 예상과 다릅니다:")
            print(json.dumps(data, indent=2, ensure_ascii=False)[:500] + "...")
    except Exception as e:
        print(f"오류 발생: {e}")
        import traceback
        traceback.print_exc()