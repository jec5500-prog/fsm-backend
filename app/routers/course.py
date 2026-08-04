from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Store
from app.schemas.course import (
    CourseRecommendRequest,
    CourseRecommendResponse,
    CourseStopResponse,
)
from app.services.route_planner import create_shopping_route

router = APIRouter(prefix="/courses", tags=["courses"])


@router.post("/recommend", response_model=CourseRecommendResponse)
def recommend_course(
    request: CourseRecommendRequest,
    db: Session = Depends(get_db),
):
    """지역, 취향, 출발 위치와 시간에 맞는 쇼핑 코스를 추천한다."""

    query = db.query(Store).filter(Store.area.contains(request.area))

    if request.styles:
        style_filters = [
            Store.styles.ilike(f"%{style}%")
            for style in request.styles
        ]
        query = query.filter(or_(*style_filters))

    candidate_stores = query.limit(100).all()

    if not candidate_stores:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="조건에 맞는 매장을 찾지 못했습니다.",
        )

    (
        selected_stops,
        total_distance,
        total_walk_minutes,
        estimated_total_minutes,
    ) = create_shopping_route(
        stores=candidate_stores,
        start_latitude=request.start_latitude,
        start_longitude=request.start_longitude,
        max_stores=request.max_stores,
        available_minutes=request.available_minutes,
    )

    if not selected_stops:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="주어진 시간 안에 방문 가능한 매장을 찾지 못했습니다.",
        )

    stops = [
        CourseStopResponse(
            order=index,
            store_id=item["store"].id,
            name=item["store"].name,
            store_type=item["store"].store_type,
            styles=item["store"].styles,
            address=item["store"].address,
            latitude=item["store"].latitude,
            longitude=item["store"].longitude,
            distance_from_previous_meters=item[
                "distance_from_previous_meters"
            ],
            estimated_walk_minutes=item["estimated_walk_minutes"],
        )
        for index, item in enumerate(selected_stops, start=1)
    ]

    return CourseRecommendResponse(
        area=request.area,
        stops=stops,
        total_distance_meters=total_distance,
        total_walk_minutes=total_walk_minutes,
        estimated_total_minutes=estimated_total_minutes,
        message=(
            f"{request.area}에서 {len(stops)}곳을 방문하는 "
            f"쇼핑 코스를 추천합니다."
        ),
    )