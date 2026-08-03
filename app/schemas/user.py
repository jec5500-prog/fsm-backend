from datetime import datetime

from pydantic import BaseModel, EmailStr


class UserCreate(BaseModel):
    """회원가입 시 클라이언트가 보내는 데이터"""
    email: EmailStr        # 이메일 형식인지 자동 검증!
    password: str          # 원본 비밀번호 (서버에서 해시 처리 예정)
    name: str        # ← 이 줄 추가!

class UserResponse(BaseModel):
    """서버가 돌려주는 데이터 (비밀번호 없음!)"""
    id: int
    email: EmailStr
    name: str        # ← 이 줄도 추가!
    created_at: datetime

    class Config:
        from_attributes = True   # SQLAlchemy 모델 → 스키마 자동 변환 허용

class UserLogin(BaseModel):
    """로그인 시 클라이언트가 보내는 데이터"""
    email: EmailStr
    password: str


class Token(BaseModel):
    """로그인 성공 시 서버가 돌려주는 토큰"""
    access_token: str      # JWT 토큰 문자열
    token_type: str        # "bearer" (토큰 사용 방식 표준 명칭)        