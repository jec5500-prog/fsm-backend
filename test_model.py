import os
import google.generativeai as genai
from dotenv import load_dotenv

# .env 파일에서 API 키 불러오기
load_dotenv()
api_key = os.getenv("GEMINI_API_KEY")

if not api_key:
    print("API 키를 찾을 수 없습니다. .env 파일을 확인해주세요.")
else:
    genai.configure(api_key=api_key)
    print("=== 사용 가능한 제미나이 모델 리스트 ===")
    
    # generateContent(텍스트 생성) 기능을 지원하는 모델만 출력
    for m in genai.list_models():
        if 'generateContent' in m.supported_generation_methods:
            print(m.name)