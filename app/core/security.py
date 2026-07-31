"""비밀번호 암호화 관련 함수"""
from passlib.context import CryptContext

# bcrypt 알고리즘을 사용하는 암호화 도구 생성
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def hash_password(password: str) -> str:
    """비밀번호를 해싱해서 반환 (복원 불가능)"""
    return pwd_context.hash(password)


def verify_password(plain_password: str, hashed_password: str) -> bool:
    """입력한 비밀번호가 저장된 해시와 일치하는지 확인"""
    return pwd_context.verify(plain_password, hashed_password)