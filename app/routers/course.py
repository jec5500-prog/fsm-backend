from app.services.course_service import save_generated_course
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy import or_
from sqlalchemy.orm import Session, joinedload
from app.services.course_service import save_generated_course

from app.core.database import get_db
from app.core.security import get_current_user
from app.models import Course, CourseStop, Store, User
from app.schemas.course import (
    CourseRecommendRequest,
    CourseRecommendResponse,
    CourseSaveRequest,
    CourseSavedResponse,
    CourseListResponse,
    CourseStopResponse,
    SharedCourseResponse,
)
from app.services.route_planner import create_shopping_route
from app.services.kakao_local import kakao_local_service

router = APIRouter(prefix="/courses", tags=["courses"])


def get_candidate_stores(
    request: CourseRecommendRequest,
    db: Session,
) -> list[Store]:
    """카카오 API를 활용하여 지역 내 매장, 카페, 식당 후보를 조회한다."""
    
    area = request.area
    candidate_stores = []
    
    # 1. 수집할 키워드 세팅 (쇼핑뿐만 아니라 카페, 식당까지 포함)
    keywords = [f"{area} 옷가게", f"{area} 카페", f"{area} 맛집"]
    
    # DB에 당장 저장하지 않고 제미나이에게 전달하기 위한 메모리용 임시 ID
    temp_id = 1 
    
    # 2. 키워드별로 카카오 API 호출하여 데이터 수집
    for keyword in keywords:
        try:
            # 키워드당 10개씩 후보를 가져옵니다. (필요시 개수 조절 가능)
            places = kakao_local_service.search_places(query=keyword, max_results=10)
            
            for place in places:
                # 분류 설정
                store_type = "카페" if "카페" in keyword else "식당" if "맛집" in keyword else "옷가게"
                
                # 3. 카카오 API 응답 데이터를 Store 모델 형태로 임시 객체화
                store = Store(
                    # id=temp_id,  <-- 임시 ID는 에러의 원인이 되므로 과감히 삭제!
                    external_id=place.get("id"), # <-- 카카오 장소 고유 ID 추가!
                    name=place.get("place_name", "이름 없음"),
                    store_type=store_type,
                    address=place.get("road_address_name") or place.get("address_name", ""),
                    latitude=float(place.get("y", 0.0)),
                    longitude=float(place.get("x", 0.0)),
                    styles=", ".join(request.styles) if store_type == "옷가게" and request.styles else None,
                    area=area,
                    source_type="kakao"
                )
                candidate_stores.append(store)
                temp_id += 1
                
        except Exception as e:
            print(f"[{keyword}] 카카오 API 검색 중 오류 발생: {e}")
            continue

    return candidate_stores


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

    # 1. AI 코스 추천 받기
    (
        selected_stops,
        total_distance,
        total_walk_minutes,
        estimated_total_minutes,
    ) = build_recommendation(request, db)

    # 2. ✨ 서비스 레이어를 호출하여 DB 저장 로직 위임 (라우터가 훨씬 깔끔해짐!)
    course = save_generated_course(
        db=db,
        user_id=current_user.id,
        title=request.title or f"{request.area} 쇼핑 코스",
        area=request.area,
        start_latitude=request.start_latitude,
        start_longitude=request.start_longitude,
        selected_stops=selected_stops,
        total_distance_meters=total_distance,
        total_walk_minutes=total_walk_minutes,
        estimated_total_minutes=estimated_total_minutes,
    )

    # 3. 프론트엔드로 보낼 응답 포맷 구성
    stops = [
        make_stop_response(
            order=index,
            store=item["store"],
            distance_from_previous_meters=item.get("distance_from_previous_meters", 0),
            estimated_walk_minutes=item.get("estimated_walk_minutes", 0),
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
        message="코스가 성공적으로 저장되었습니다. 공유 링크를 사용할 수 있습니다.",
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

from fastapi import HTTPException

@router.get("/{course_id}", response_model=CourseSavedResponse)
def get_course(
    course_id: int, 
    db: Session = Depends(get_db)
):
    """저장된 특정 코스의 상세 정보를 불러옵니다."""
    
    # 1. DB에서 코스 기본 정보 조회
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="해당 코스를 찾을 수 없습니다.")

    # 2. 코스에 속한 장소(CourseStop)들을 방문 순서대로 조회
    stops_data = (
        db.query(CourseStop)
        .filter(CourseStop.course_id == course_id)
        .order_by(CourseStop.visit_order)
        .all()
    )

    # 3. 프론트엔드로 보낼 응답 데이터(stops) 조립
    stops_response = []
    for stop in stops_data:
        # 각 순서에 연결된 실제 매장(Store) 정보 조회
        store = db.query(Store).filter(Store.id == stop.store_id).first()
        
        if store:
            stops_response.append(
                make_stop_response(
                    order=stop.visit_order,
                    store=store,
                    distance_from_previous_meters=stop.distance_from_previous_meters,
                    estimated_walk_minutes=stop.estimated_walk_minutes,
                )
            )

    # 4. 최종 JSON 응답 반환
    return CourseSavedResponse(
        id=course.id,
        title=course.title,
        share_token=course.share_token,
        share_path=f"/courses/shared/{course.share_token}" if course.share_token else "",
        area=course.area,
        stops=stops_response,
        total_distance_meters=course.total_distance_meters,
        total_walk_minutes=course.total_walk_minutes,
        estimated_total_minutes=course.estimated_total_minutes,
        message="코스를 성공적으로 불러왔습니다."
    )

@router.get("", response_model=list[CourseListResponse])
def get_my_courses(
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """현재 로그인한 사용자가 저장한 모든 코스의 요약 목록을 최신순으로 불러옵니다."""
    
    # 현재 로그인한 유저(current_user.id)의 코스만 필터링하고, 최신순(내림차순)으로 정렬
    courses = (
        db.query(Course)
        .filter(Course.user_id == current_user.id)
        .order_by(Course.id.desc())
        .all()
    )
    
    return courses

@router.get("/shared/{share_token}", response_model=CourseSavedResponse)
def get_shared_course(
    share_token: str,
    db: Session = Depends(get_db)
):
    """로그인 없이 공유 토큰(share_token)을 통해 특정 코스의 상세 정보를 조회합니다."""
    
    # 1. share_token을 이용해 DB에서 코스 찾기
    course = db.query(Course).filter(Course.share_token == share_token).first()
    if not course:
        raise HTTPException(status_code=404, detail="유효하지 않거나 만료된 공유 링크입니다.")

    # 2. 해당 코스에 속한 장소(CourseStop)들 순서대로 조회
    stops_data = (
        db.query(CourseStop)
        .filter(CourseStop.course_id == course.id)
        .order_by(CourseStop.visit_order)
        .all()
    )

    # 3. 프론트엔드로 보낼 응답 데이터(stops) 조립
    stops_response = []
    for stop in stops_data:
        store = db.query(Store).filter(Store.id == stop.store_id).first()
        if store:
            stops_response.append(
                make_stop_response(
                    order=stop.visit_order,
                    store=store,
                    distance_from_previous_meters=stop.distance_from_previous_meters,
                    estimated_walk_minutes=stop.estimated_walk_minutes,
                )
            )

    # 4. 최종 JSON 응답 반환 (인증 불필요)
    return CourseSavedResponse(
        id=course.id,
        title=course.title,
        share_token=course.share_token,
        share_path=f"/courses/shared/{course.share_token}",
        area=course.area,
        stops=stops_response,
        total_distance_meters=course.total_distance_meters,
        total_walk_minutes=course.total_walk_minutes,
        estimated_total_minutes=course.estimated_total_minutes,
        message="공유된 코스를 성공적으로 불러왔습니다."
    )

@router.delete("/{course_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_course(
    course_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user)
):
    """로그인한 사용자가 자신이 생성한 특정 코스를 삭제합니다."""
    
    # 1. 삭제할 코스가 실제로 존재하는지, 그리고 현재 로그인한 사람의 코스가 맞는지 확인
    course = db.query(Course).filter(Course.id == course_id).first()
    if not course:
        raise HTTPException(status_code=404, detail="해당 코스를 찾을 수 없습니다.")
    
    if course.user_id != current_user.id:
        raise HTTPException(status_code=403, detail="본인이 작성한 코스만 삭제할 수 있습니다.")

    # 2. 코스에 연결된 장소들(CourseStop) 먼저 삭제 (외래 키 제약조건 에러 방지)
    db.query(CourseStop).filter(CourseStop.course_id == course_id).delete()

    # 3. 코스 본문 삭제
    db.delete(course)
    db.commit()

    return None