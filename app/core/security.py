"""비밀번호 암호화 관련 함수"""
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from jose import JWTError, jwt
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models.user import User
from app.core.config import settings

from datetime import datetime, timedelta, timezone
from passlib.context import CryptContext

oauth2_scheme = OAuth2PasswordBearer(tokenUrl="users/login")

# bcrypt 알고리즘을 사용하는 암호화 도구 생성
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """비밀번호를 해싱해서 반환 (복원 불가능)"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """입력한 비밀번호가 저장된 해시와 일치하는지 확인"""
    return pwd_context.verify(plain_password, hashed_password)



# ── JWT 설정 ──────────────────────────────
SECRET_KEY = "my-super-secret-key-change-this-later"  # 서명용 비밀키 (도장)
ALGORITHM = "HS256"                                    # 서명 알고리즘
ACCESS_TOKEN_EXPIRE_MINUTES = 30                       # 토큰 유효 시간


def create_access_token(data: dict) -> str:
    """유저 정보를 받아 JWT 토큰을 만들어 반환"""
    to_encode = data.copy()

    # 만료 시간 추가 (현재 시각 + 30분)
    expire = datetime.now(timezone.utc) + timedelta(minutes=ACCESS_TOKEN_EXPIRE_MINUTES)
    to_encode.update({"exp": expire})

    # 비밀키로 서명해서 토큰 생성
    return jwt.encode(to_encode, SECRET_KEY, algorithm=ALGORITHM)

def get_current_user(
    token: str = Depends(oauth2_scheme),
    db: Session = Depends(get_db)
) -> User:
    """토큰을 검증하고 현재 로그인한 유저를 반환"""

    # 인증 실패 시 보낼 에러를 미리 만들어둠
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="인증 정보를 확인할 수 없습니다",
        headers={"WWW-Authenticate": "Bearer"},
    )

    try:
        # 1) 토큰을 해독(decode)한다
        payload = jwt.decode(
            token,
            settings.SECRET_KEY,
            algorithms=[settings.ALGORITHM]
        )
        # 2) 토큰 안에서 이메일("sub")을 꺼낸다
        email: str = payload.get("sub")
        if email is None:
            raise credentials_exception
    except JWTError:
        # 토큰이 가짜거나 만료됐으면 에러
        raise credentials_exception

    # 3) 이메일로 DB에서 유저를 찾는다
    user = db.query(User).filter(User.email == email).first()
    if user is None:
        raise credentials_exception

    # 4) 찾은 유저를 돌려준다
    return user