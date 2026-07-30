from fastapi import FastAPI

from app.core.config import settings

# FastAPI 앱 인스턴스 생성 (프로젝트의 심장!)
app = FastAPI(
    title=settings.app_name,  # config.py의 app_name과 일치
    version="0.1.0",
)


@app.get("/")
def health_check():
    """서버가 살아있는지 확인하는 기본 엔드포인트"""
    return {"status": "ok", "message": "FSM Backend is running"}