"""User 관련 API 라우터"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse

router = APIRouter(prefix="/users", tags=["users"])


@router.post("/", response_model=UserResponse)
def create_user(user: UserCreate, db: Session = Depends(get_db)):
    # 1. 이메일 중복 확인
    existing_user = db.query(User).filter(User.email == user.email).first()
    if existing_user:
        raise HTTPException(status_code=400, detail="이미 등록된 이메일입니다")

    # 2. 비밀번호를 해싱해서 User 객체 생성
    new_user = User(
        email=user.email,
        hashed_password=hash_password(user.password),  # 원본이 아닌 해시 저장!
        name=user.name,
    )

    # 3. DB에 저장
    db.add(new_user)
    db.commit()
    db.refresh(new_user)
    return new_user