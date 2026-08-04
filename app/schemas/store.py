from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class StoreCreate(BaseModel):
    """사용자가 직접 매장을 등록할 때 보내는 데이터"""

    name: str = Field(max_length=100)
    store_type: str = Field(max_length=50)
    latitude: float
    longitude: float

    styles: str | None = None
    description: str | None = None
    address: str | None = None
    area: str | None = None
    price_range: str | None = None
    business_hours: str | None = None
    phone: str | None = None
    website: str | None = None
    has_parking: bool = False


class StoreCollectRequest(BaseModel):
    """카카오 장소 API로 매장을 자동 수집할 때 보내는 조건"""

    area: str = Field(min_length=1, max_length=50)
    keywords: list[str] = Field(min_length=1)
    max_results_per_keyword: int = Field(default=15, ge=1, le=45)


class StoreResponse(BaseModel):
    """서버가 반환하는 매장 데이터"""

    model_config = ConfigDict(from_attributes=True)

    id: int
    name: str
    store_type: str
    latitude: float
    longitude: float

    styles: str | None
    description: str | None
    address: str | None
    area: str | None
    price_range: str | None
    business_hours: str | None
    phone: str | None
    website: str | None
    has_parking: bool

    source_type: str
    source_name: str | None
    source_url: str | None
    external_id: str | None
    is_verified: bool
    last_verified_at: datetime | None

    created_at: datetime
    updated_at: datetime
    owner_id: int | None


class StoreCollectionResponse(BaseModel):
    """자동 수집 작업 결과"""

    created_count: int
    updated_count: int
    skipped_count: int