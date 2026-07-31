from datetime import datetime, timezone

from sqlalchemy import Boolean, Column, DateTime, Float, Integer, String

from app.core.database import Base


class Store(Base):
    """가맹점 정보 테이블"""

    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), nullable=False)          # 가게 이름
    store_type = Column(String(50), nullable=False)     # 업종 (한식, 카페 등)
    latitude = Column(Float, nullable=False)            # 위도
    longitude = Column(Float, nullable=False)           # 경도
    price_range = Column(String(50), nullable=True)     # 가격대
    business_hours = Column(String(100), nullable=True) # 영업시간
    phone = Column(String(20), nullable=True)           # 전화번호
    website = Column(String(255), nullable=True)        # 웹사이트
    has_parking = Column(Boolean, default=False)        # 주차 가능 여부
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc)
    )