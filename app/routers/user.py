"""User 관련 API 라우터"""
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import hash_password, verify_password, create_access_token
from app.models.user import User
from app.schemas.user import UserCreate, UserResponse, UserLogin, Token

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

@router.post("/login", response_model=Token)
def login(user_data: UserLogin, db: Session = Depends(get_db)):
    # 1. 이메일로 유저 찾기
    user = db.query(User).filter(User.email == user_data.email).first()

    # 2. 유저가 없거나 비밀번호가 틀리면 → 401 에러
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(status_code=401, detail="이메일 또는 비밀번호가 올바르지 않습니다")

    # 3. 검증 통과 → JWT 토큰 발급
    access_token = create_access_token(data={"sub": user.email})
    return {"access_token": access_token, "token_type": "bearer"}