from pydantic import BaseModel


class StoreCreate(BaseModel):
    """가게 등록 시 클라이언트가 보내는 데이터"""
    name: str
    store_type: str
    latitude: float
    longitude: float
    price_range: str | None = None       # 선택 항목 (없어도 됨)
    business_hours: str | None = None
    phone: str | None = None
    website: str | None = None
    has_parking: bool = False             # 기본값 False


class StoreResponse(BaseModel):
    """서버가 돌려주는 데이터"""
    id: int
    name: str
    store_type: str
    latitude: float
    longitude: float
    price_range: str | None
    business_hours: str | None
    phone: str | None
    website: str | None
    has_parking: bool

    class Config:
        from_attributes = True