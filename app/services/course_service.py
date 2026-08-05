from sqlalchemy.orm import Session
from app.models.course import Course, CourseStop
from app.models.store import Store

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
    (선택된 매장 정보가 DB에 없다면 추가하고, 있다면 기존 매장을 연결합니다.)
    """

    # 1. 메인 Course 객체 생성 및 ID 발급
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
    db.flush()  # DB에 전송하여 새로운 Course의 ID를 받아옵니다.

    # 2. 방문 순서대로 Store 검증 및 CourseStop 객체 생성
    for order, stop_data in enumerate(selected_stops, start=1):
        memory_store = stop_data["store"]  # 라우터에서 임시로 만든 Store 객체
        
        # 카카오 장소 ID(external_id) 기준으로 DB에 이미 존재하는지 조회 (Upsert 로직)
        existing_store = None
        if memory_store.external_id:
            existing_store = db.query(Store).filter(Store.external_id == memory_store.external_id).first()

        if existing_store:
            # 이미 DB에 존재하면, 새로 만들지 않고 기존 매장을 사용
            final_store = existing_store
        else:
            # DB에 없는 새로운 장소면, DB에 추가하여 진짜 ID 발급
            final_store = memory_store
            db.add(final_store)
            db.flush()  # 새 매장의 진짜 ID(final_store.id) 발급 완료

        # 3. 코스와 장소를 연결하는 CourseStop 객체 생성
        course_stop = CourseStop(
            course_id=new_course.id,
            store_id=final_store.id,  # 이제 무조건 실제 DB의 ID가 안전하게 들어갑니다!
            visit_order=order,
            distance_from_previous_meters=stop_data.get("distance_from_previous_meters", 0),
            estimated_walk_minutes=stop_data.get("estimated_walk_minutes", 0),
        )
        db.add(course_stop)
        
        # 라우터에서 최종 응답을 만들 때 진짜 DB 객체를 사용하도록 데이터 교체
        stop_data["store"] = final_store
        stop_data["store_id"] = final_store.id

    # 4. 모든 데이터 최종 커밋 (트랜잭션 확정)
    db.commit()
    db.refresh(new_course)

    return new_course

def generate_ai_course(request_data):
    area = request_data.area
    store_count = request_data.store_count
    available_minutes = request_data.available_minutes
    user_prompt = request_data.prompt  # 사용자가 입력한 자연어 요구사항
    
   # AI에게 보낼 프롬프트: 기존 변수와 새로운 규칙을 하나로 통합!
    prompt_instruction = f"""
    사용자 입력 요구사항: {user_prompt}
    방문 매장 수: {store_count}곳
    이용 가능 시간: {available_minutes}분

    [중요 규칙]
    1. 입력 형태 이해: 사용자의 입력은 '완전한 문장형(자연어)'일 수도 있고, '#홍대 #빈티지'처럼 '키워드/해시태그 나열형'일 수도 있습니다. 
    2. 의도 파악: 어떤 형태이든 입력된 텍스트에서 사용자의 핵심 의도(지역, 분위기, 목적, 스타일 등)를 파악하여 그에 딱 맞는 코스를 추천해 주세요.
    3. 위 조건을 바탕으로 사용자의 의도에 맞는 최적의 쇼핑/데이트 코스를 추천해 주세요.
    """