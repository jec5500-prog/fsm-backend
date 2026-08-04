import secrets
from datetime import datetime, timezone

from sqlalchemy import Column, DateTime, Float, ForeignKey, Integer, String
from sqlalchemy.orm import relationship

from app.core.database import Base


def generate_share_token() -> str:
    """공유 링크에 사용할 추측하기 어려운 토큰을 생성한다."""
    return secrets.token_urlsafe(16)


class Course(Base):
    """사용자가 저장한 쇼핑 코스"""

    __tablename__ = "courses"

    id = Column(Integer, primary_key=True, index=True)

    user_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    title = Column(String(100), nullable=False)
    area = Column(String(50), nullable=False)

    start_latitude = Column(Float, nullable=False)
    start_longitude = Column(Float, nullable=False)

    total_distance_meters = Column(Integer, nullable=False)
    total_walk_minutes = Column(Integer, nullable=False)
    estimated_total_minutes = Column(Integer, nullable=False)

    share_token = Column(
        String(64),
        nullable=False,
        unique=True,
        index=True,
        default=generate_share_token,
    )

    created_at = Column(
        DateTime(timezone=True),
        nullable=False,
        default=lambda: datetime.now(timezone.utc),
    )

    user = relationship("User", back_populates="courses")
    stops = relationship(
        "CourseStop",
        back_populates="course",
        cascade="all, delete-orphan",
        order_by="CourseStop.visit_order",
    )


class CourseStop(Base):
    """저장된 코스 안의 방문 매장과 순서"""

    __tablename__ = "course_stops"

    id = Column(Integer, primary_key=True, index=True)

    course_id = Column(
        Integer,
        ForeignKey("courses.id", ondelete="CASCADE"),
        nullable=False,
    )
    store_id = Column(Integer, ForeignKey("stores.id"), nullable=False)

    visit_order = Column(Integer, nullable=False)
    distance_from_previous_meters = Column(Integer, nullable=False)
    estimated_walk_minutes = Column(Integer, nullable=False)

    course = relationship("Course", back_populates="stops")
    store = relationship("Store")