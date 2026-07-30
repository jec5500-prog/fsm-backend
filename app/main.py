from fastapi import FastAPI

from app.core.config import settings
from app.core.database import Base, engine

# 모델을 import 해야 Base가 테이블 존재를 인식함 (중요!)
import app.models

# DB에 테이블 생성 (이미 있으면 건너뜀)
Base.metadata.create_all(bind=engine)

# FastAPI 앱 인스턴스 생성 (프로젝트의 심장!)
app = FastAPI(
    title=settings.app_name,  # config.py의 app_name
    version="0.1.0",
)


@app.get("/")
def health_check():
    """서버가 살아있는지 확인하는 기본 엔드포인트"""
    return {"status": "ok", "message": "FSM Backend is running"}