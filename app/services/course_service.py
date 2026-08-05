from sqlalchemy.orm import Session
from app.models.course import Course, CourseStop

def save_generated_course(
    db: Session,
    user_id: int,
    title: str,
    area: str,
    start_latitude: float,
    start_longitude: float,
    selected_stops: list[dict],
    total_distance_meters: int,
    total_walk_minutes: int,
    estimated_total_minutes: int,
) -> Course:
    """
    AI가 생성한 추천 코스와 세부 방문 장소들을 DB에 저장합니다.
    """
    
    # 1. 메인 Course 객체 생성
    new_course = Course(
        user_id=user_id,
        title=title,
        area=area,
        start_latitude=start_latitude,
        start_longitude=start_longitude,
        total_distance_meters=total_distance_meters,
        total_walk_minutes=total_walk_minutes,
        estimated_total_minutes=estimated_total_minutes,
    )
    
    db.add(new_course)
    db.flush()  # DB에 전송하여 새로운 Course의 ID를 미리 받아옵니다 (commit 전).

    # 2. 방문 순서대로 CourseStop (상세 장소) 객체 생성 및 연결
    for order, stop_data in enumerate(selected_stops, start=1):
        store = stop_data["store"]
        
        course_stop = CourseStop(
            course_id=new_course.id,
            store_id=store.id,
            visit_order=order,
            distance_from_previous_meters=stop_data["distance_from_previous_meters"],
            estimated_walk_minutes=stop_data["estimated_walk_minutes"],
        )
        db.add(course_stop)

    # 3. 모든 데이터 최종 커밋 (트랜잭션 확정)
    db.commit()
    db.refresh(new_course) # DB에서 생성된 share_token, created_at 등을 반영

    return new_course