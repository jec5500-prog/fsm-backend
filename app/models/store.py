from datetime import datetime, timezone

from sqlalchemy import (
    Boolean,
    Column,
    DateTime,
    Float,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import relationship

from app.core.database import Base


class Store(Base):
    """쇼핑 매장 정보 테이블"""

    __tablename__ = "stores"

    id = Column(Integer, primary_key=True, index=True)

    # 기본 정보
    name = Column(String(100), nullable=False, index=True)
    store_type = Column(String(50), nullable=False)  # 편집숍, 의류, 빈티지숍 등
    styles = Column(String(255), nullable=True)  # 빈티지, 스트릿, 미니멀 등
    description = Column(Text, nullable=True)

    # 위치·동선 계산 정보
    address = Column(String(255), nullable=True)
    area = Column(String(50), nullable=True, index=True)  # 성수, 홍대, 강남 등
    latitude = Column(Float, nullable=False)
    longitude = Column(Float, nullable=False)

    # 매장 상세 정보
    price_range = Column(String(50), nullable=True)
    business_hours = Column(String(100), nullable=True)
    phone = Column(String(20), nullable=True)
    website = Column(String(255), nullable=True)
    has_parking = Column(Boolean, default=False)

    # 수집 출처·검증 정보
    source_type = Column(
        String(30),
        nullable=False,
        default="user",
    )  # user, kakao, public_data, crawled
    source_name = Column(String(50), nullable=True)
    source_url = Column(String(255), nullable=True)
    external_id = Column(
        String(100),
        nullable=True,
        unique=True,
        index=True,
    )  # 예: 카카오 장소 ID
    is_verified = Column(Boolean, nullable=False, default=False)
    last_verified_at = Column(DateTime(timezone=True), nullable=True)

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )
    updated_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
        onupdate=lambda: datetime.now(timezone.utc),
    )

    # 자동 수집 매장은 소유자가 없으므로 nullable=True
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    owner = relationship("User", back_populates="stores")