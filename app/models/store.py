from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Integer, String

from app.core.database import Base


class Store(Base):
    """가맹점 정보 테이블"""

    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)              # 가맹점 이름
    address = Column(String(255), nullable=False)           # 주소
    phone = Column(String(20), nullable=True)               # 전화번호 (선택)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )