from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Course, CourseStop, Store, User
from app.schemas.course import (
    CourseRecommendRequest,
    CourseRecommendResponse,
    CourseSaveRequest,
    CourseSavedResponse,
    CourseStopResponse,
    SharedCourseResponse,
)
from app.services.route_planner import create_shopping_route

router = APIRouter(prefix="/courses", tags=["courses"])


def get_candidate_stores(
    request: CourseRecommendRequest,
    db: Session,
) -> list[Store]:
    """추천 조건에 맞는 매장 후보를 조회한다."""

    query = db.query(Store).filter(Store.area.contains(request.area))

    if request.styles:
        style_filters = [
            Store.styles.ilike(f"%{style}%")
            for style in request.styles
        ]
        query = query.filter(or_(*style_filters))

    return query.limit(100).all()


def build_recommendation(
    request: CourseRecommendRequest,
    db: Session,
) -> tuple[list[dict], int, int, int]:
    """매장 후보를 조회하고 동선을 계산한다."""

    candidate_stores = get_candidate_stores(request, db)

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

    return (
        selected_stops,
        total_distance,
        total_walk_minutes,
        estimated_total_minutes,
    )


def make_stop_response(
    order: int,
    store: Store,
    distance_from_previous_meters: int,
    estimated_walk_minutes: int,
) -> CourseStopResponse:
    """매장 정보를 코스 경유지 응답 형식으로 바꾼다."""

    return CourseStopResponse(
        order=order,
        store_id=store.id,
        name=store.name,
        store_type=store.store_type,
        styles=store.styles,
        address=store.address,
        latitude=store.latitude,
        longitude=store.longitude,
        distance_from_previous_meters=distance_from_previous_meters,
        estimated_walk_minutes=estimated_walk_minutes,
    )


@router.post("/recommend", response_model=CourseRecommendResponse)
def recommend_course(
    request: CourseRecommendRequest,
    db: Session = Depends(get_db),
):
    """저장하지 않고 쇼핑 코스만 추천한다."""

    (
        selected_stops,
        total_distance,
        total_walk_minutes,
        estimated_total_minutes,
    ) = build_recommendation(request, db)

    stops = [
        make_stop_response(
            order=index,
            store=item["store"],
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


@router.post(
    "/save",
    response_model=CourseSavedResponse,
    status_code=status.HTTP_201_CREATED,
)
def save_course(
    request: CourseSaveRequest,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    """추천 조건으로 코스를 계산하고 로그인 사용자 계정에 저장한다."""

    (
        selected_stops,
        total_distance,
        total_walk_minutes,
        estimated_total_minutes,
    ) = build_recommendation(request, db)

    course = Course(
        user_id=current_user.id,
        title=request.title or f"{request.area} 쇼핑 코스",
        area=request.area,
        start_latitude=request.start_latitude,
        start_longitude=request.start_longitude,
        total_distance_meters=total_distance,
        total_walk_minutes=total_walk_minutes,
        estimated_total_minutes=estimated_total_minutes,
    )

    for index, item in enumerate(selected_stops, start=1):
        course.stops.append(
            CourseStop(
                store_id=item["store"].id,
                visit_order=index,
                distance_from_previous_meters=item[
                    "distance_from_previous_meters"
                ],
                estimated_walk_minutes=item["estimated_walk_minutes"],
            )
        )

    db.add(course)
    db.commit()
    db.refresh(course)

    stops = [
        make_stop_response(
            order=index,
            store=item["store"],
            distance_from_previous_meters=item[
                "distance_from_previous_meters"
            ],
            estimated_walk_minutes=item["estimated_walk_minutes"],
        )
        for index, item in enumerate(selected_stops, start=1)
    ]

    return CourseSavedResponse(
        id=course.id,
        title=course.title,
        share_token=course.share_token,
        share_path=f"/courses/shared/{course.share_token}",
        area=course.area,
        stops=stops,
        total_distance_meters=course.total_distance_meters,
        total_walk_minutes=course.total_walk_minutes,
        estimated_total_minutes=course.estimated_total_minutes,
        message="코스가 저장되었습니다. 공유 링크를 사용할 수 있습니다.",
    )


@router.get(
    "/shared/{share_token}",
    response_model=SharedCourseResponse,
)
def get_shared_course(
    share_token: str,
    db: Session = Depends(get_db),
):
    """공유 토큰으로 저장된 코스를 공개 조회한다."""

    course = (
        db.query(Course)
        .options(
            joinedload(Course.stops).joinedload(CourseStop.store)
        )
        .filter(Course.share_token == share_token)
        .first()
    )

    if not course:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="공유 코스를 찾지 못했습니다.",
        )

    stops = [
        make_stop_response(
            order=stop.visit_order,
            store=stop.store,
            distance_from_previous_meters=stop.distance_from_previous_meters,
            estimated_walk_minutes=stop.estimated_walk_minutes,
        )
        for stop in course.stops
    ]

    return SharedCourseResponse(
        id=course.id,
        title=course.title,
        area=course.area,
        stops=stops,
        total_distance_meters=course.total_distance_meters,
        total_walk_minutes=course.total_walk_minutes,
        estimated_total_minutes=course.estimated_total_minutes,
        message=f"{course.title} 공유 코스입니다.",
    )