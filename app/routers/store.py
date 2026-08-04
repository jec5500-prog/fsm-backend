from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Store, User
from app.schemas import (
    StoreCollectRequest,
    StoreCollectionResponse,
    StoreCreate,
    StoreResponse,
)
from app.services.kakao_local import (
    KakaoLocalAPIError,
    kakao_local_service,
)

router = APIRouter(prefix="/stores", tags=["stores"])


@router.post("/", response_model=StoreResponse, status_code=status.HTTP_201_CREATED)
def create_store(
    store_in: StoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """사용자가 직접 매장을 등록한다."""

    store = Store(
        **store_in.model_dump(),
        owner_id=current_user.id,
        source_type="user",
        source_name="user",
    )
    db.add(store)
    db.commit()
    db.refresh(store)

    return store


@router.post("/collect", response_model=StoreCollectionResponse)
def collect_stores(
    request: StoreCollectRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """
    카카오 장소 API에서 매장을 자동 수집한다.

    현재는 로그인한 사용자만 실행할 수 있다.
    추후 관리자 권한을 추가하면 관리자 전용 API로 변경한다.
    """

    created_count = 0
    updated_count = 0
    skipped_count = 0

    try:
        for keyword in request.keywords:
            search_query = f"{request.area} {keyword}"
            places = kakao_local_service.search_places(
                query=search_query,
                max_results=request.max_results_per_keyword,
            )

            for place in places:
                external_id = place.get("id")
                name = place.get("place_name")

                if not external_id or not name:
                    skipped_count += 1
                    continue

                try:
                    latitude = float(place["y"])
                    longitude = float(place["x"])
                except (KeyError, TypeError, ValueError):
                    skipped_count += 1
                    continue

                address = (
                    place.get("road_address_name")
                    or place.get("address_name")
                    or None
                )
                store_type = place.get("category_group_name") or "쇼핑"
                phone = place.get("phone") or None
                source_url = place.get("place_url") or None

                store = (
                    db.query(Store)
                    .filter(Store.external_id == external_id)
                    .first()
                )

                if store:
                    # 동일한 카카오 장소 ID면 새 매장을 만들지 않고 정보 갱신
                    store.name = name
                    store.store_type = store_type
                    store.address = address
                    store.area = request.area
                    store.latitude = latitude
                    store.longitude = longitude
                    store.phone = phone or store.phone
                    store.source_url = source_url or store.source_url
                    store.source_type = "kakao"
                    store.source_name = "Kakao Local API"
                    store.last_verified_at = datetime.now(timezone.utc)

                    existing_styles = set(
                        filter(None, (store.styles or "").split(","))
                    )
                    existing_styles.add(keyword)
                    store.styles = ",".join(sorted(existing_styles))

                    updated_count += 1

                else:
                    store = Store(
                        name=name,
                        store_type=store_type,
                        styles=keyword,
                        address=address,
                        area=request.area,
                        latitude=latitude,
                        longitude=longitude,
                        phone=phone,
                        source_type="kakao",
                        source_name="Kakao Local API",
                        source_url=source_url,
                        external_id=external_id,
                        is_verified=False,
                        last_verified_at=datetime.now(timezone.utc),
                        owner_id=None,
                    )
                    db.add(store)
                    created_count += 1

        db.commit()

    except KakaoLocalAPIError as error:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=str(error),
        ) from error

    return StoreCollectionResponse(
        created_count=created_count,
        updated_count=updated_count,
        skipped_count=skipped_count,
    )


@router.get("/search", response_model=list[StoreResponse])
def search_stores(
    area: str | None = None,
    style: str | None = None,
    store_type: str | None = None,
    price_range: str | None = None,
    limit: int = Query(default=50, ge=1, le=100),
    db: Session = Depends(get_db),
):
    """지역·스타일·업종·가격대를 기준으로 매장을 검색한다."""

    query = db.query(Store)

    if area:
        query = query.filter(Store.area.contains(area))

    if style:
        query = query.filter(Store.styles.ilike(f"%{style}%"))

    if store_type:
        query = query.filter(Store.store_type.contains(store_type))

    if price_range:
        query = query.filter(Store.price_range == price_range)

    return query.limit(limit).all()


@router.get("/", response_model=list[StoreResponse])
def get_stores(
    db: Session = Depends(get_db),
):
    """전체 매장 목록을 조회한다."""

    return db.query(Store).all()