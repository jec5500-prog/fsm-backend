from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """회원가입 시 클라이언트가 보내는 데이터"""
    email: EmailStr        # 이메일 형식인지 자동 검증!
    password: str          # 원본 비밀번호 (서버에서 해시 처리 예정)


class UserResponse(BaseModel):
    """서버가 돌려주는 데이터 (비밀번호 없음!)"""
    id: int
    email: EmailStr
    created_at: datetime

    class Config:
        from_attributes = True   # SQLAlchemy 모델 → 스키마 자동 변환 허용