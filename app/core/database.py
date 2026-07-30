from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, declarative_base

from app.core.config import settings

# DB 연결 엔진 생성 (SQLite는 아래 옵션 필요)
engine = create_engine(
    settings.database_url,
    connect_args={"check_same_thread": False},
)

# DB 작업 세션을 만들어주는 공장
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# 모든 모델(테이블)이 상속받을 기본 클래스
Base = declarative_base()


def get_db():
    """요청마다 DB 세션을 열고, 끝나면 자동으로 닫아주는 함수"""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()