import os
import math
import json
import logging
import google.generativeai as genai
from dotenv import load_dotenv

from app.models import Store

# 1. 로거(Logger) 설정: print() 대신 실무용 로그 사용
logger = logging.getLogger(__name__)
logger.setLevel(logging.INFO)

# 환경 변수에서 제미나이 API 키 불러오기
load_dotenv()
GEMINI_API_KEY = os.getenv("GEMINI_API_KEY")
if GEMINI_API_KEY:
    genai.configure(api_key=GEMINI_API_KEY)

# 제미나이 모델 설정 (무료로 빠르고 성능 좋은 3.6 Flash 모델 사용)
model = genai.GenerativeModel('gemini-3.6-flash')

EARTH_RADIUS_METERS = 6_371_000
WALKING_SPEED_METERS_PER_MINUTE = 80
ESTIMATED_SHOPPING_MINUTES_PER_STORE = 40


def haversine_distance_meters(
    latitude_1: float,
    longitude_1: float,
    latitude_2: float,
    longitude_2: float,
) -> float:
    """두 좌표 사이의 직선거리를 미터 단위로 계산한다."""
    latitude_delta = math.radians(latitude_2 - latitude_1)
    longitude_delta = math.radians(longitude_2 - longitude_1)
    latitude_1 = math.radians(latitude_1)
    latitude_2 = math.radians(latitude_2)
    value = (
        math.sin(latitude_delta / 2) ** 2
        + math.cos(latitude_1)
        * math.cos(latitude_2)
        * math.sin(longitude_delta / 2) ** 2
    )
    return EARTH_RADIUS_METERS * 2 * math.atan2(
        math.sqrt(value),
        math.sqrt(1 - value),
    )


def create_shopping_route(
    stores: list[Store],
    start_latitude: float,
    start_longitude: float,
    max_stores: int,
    available_minutes: int,
) -> tuple[list[dict], int, int, int]:
    """
    제미나이 AI를 활용하여 취향과 동선을 고려한 최적의 코스를 추천합니다.
    """
    if not stores:
        return [], 0, 0, 0

    # 1. 제미나이에게 전달할 매장 후보 리스트 텍스트 만들기
    store_info_list = ""
    for idx, store in enumerate(stores):
        style_info = f", 스타일: {store.styles}" if store.styles else ""
        store_info_list += f"[{idx}] 분류: {store.store_type}, 이름: {store.name}{style_info}, 주소: {store.address}\n"

    # 2. 제미나이에게 요청할 프롬프트(명령어)
    prompt = f"""
    당신은 센스 있는 트렌디한 패션/라이프스타일 가이드입니다. 
    아래 장소 후보들 중에서 동선이 효율적인 곳을 골라 최대 {max_stores}곳의 쇼핑 코스를 추천해주세요.
    
    [코스 구성 규칙]
    1. 메인 목적은 쇼핑(옷가게)입니다. 사용자의 취향에 맞는 옷가게를 우선적으로 2~3곳 배치하세요.
    2. 쇼핑 중간에 다리를 쉬며 대화할 수 있는 '카페'를 1곳 정도 자연스럽게 포함하세요.
    3. 코스의 마지막이나 식사하기 좋은 동선에 '식당(맛집)'을 1곳 포함해 주세요.
    4. 제공된 주소를 바탕으로 장소 간의 거리가 너무 멀지 않게, 논리적인 걷기 순서로 배치하세요.
    
    [장소 후보 리스트]
    {store_info_list}
    
    반드시 아래 JSON 형식으로만 답변을 반환하세요. 다른 설명이나 텍스트는 절대 포함하지 마세요.
    {{
        "selected_indices": [선택한 장소의 번호(숫자)들을 방문할 순서대로 배열에 담아주세요]
    }}
    """

    selected_indices = []

    # 3. 제미나이 API 호출 및 안전한 예외 처리
    try:
        response = model.generate_content(prompt)
        response_text = response.text.strip()
        
        # 마크다운 코드 블록(```json ... ```) 제거 로직 유지
        if response_text.startswith("```json"):
            response_text = response_text[7:-3].strip()
        elif response_text.startswith("```"):
            response_text = response_text[3:-3].strip()
            
        ai_result = json.loads(response_text)
        selected_indices = ai_result.get("selected_indices", [])
        
    except json.JSONDecodeError as e:
        logger.error(f"제미나이 JSON 파싱 오류: {e}")
        # 오류 발생 시 빈 리스트로 두어 아래 폴백 로직을 타게 함
    except Exception as e:
        logger.error(f"제미나이 API 호출 오류: {e}")

    selected_stops = []
    current_latitude = start_latitude
    current_longitude = start_longitude
    total_distance = 0
    total_walk_minutes = 0

    # 4. 폴백(Fallback) 처리: AI가 실패했을 경우 가장 가까운 거리 순으로 강제 할당
    if not selected_indices:
        logger.warning("AI 추천 코스 생성 실패. 거리 기반 폴백(Fallback) 로직으로 전환합니다.")
        remaining_stores = list(stores)
        
        # 기준점을 계속 업데이트하기 위한 임시 변수
        temp_lat, temp_lon = start_latitude, start_longitude 
        
        while remaining_stores and len(selected_indices) < max_stores:
            nearest_store = min(
                remaining_stores,
                key=lambda s: haversine_distance_meters(
                    temp_lat, temp_lon, s.latitude, s.longitude
                ),
            )
            selected_indices.append(stores.index(nearest_store))
            remaining_stores.remove(nearest_store)
            
            # 다음 계산을 위해 기준점을 방금 찾은 매장으로 업데이트 (버그 수정됨)
            temp_lat = nearest_store.latitude
            temp_lon = nearest_store.longitude

    # 5. 선택된 순서대로 거리 및 시간 계산
    for idx in selected_indices[:max_stores]:
        if idx >= len(stores):
            continue
            
        store = stores[idx]
        distance = haversine_distance_meters(
            current_latitude,
            current_longitude,
            store.latitude,
            store.longitude,
        )
        walk_minutes = max(
            1,
            math.ceil(distance / WALKING_SPEED_METERS_PER_MINUTE),
        )

        estimated_total_if_added = (
            total_walk_minutes
            + walk_minutes
            + (len(selected_stops) + 1) * ESTIMATED_SHOPPING_MINUTES_PER_STORE
        )

        if estimated_total_if_added > available_minutes:
            break

        selected_stops.append(
            {
                "store": store,
                "distance_from_previous_meters": round(distance),
                "estimated_walk_minutes": walk_minutes,
            }
        )

        total_distance += round(distance)
        total_walk_minutes += walk_minutes
        current_latitude = store.latitude
        current_longitude = store.longitude

    estimated_total_minutes = (
        total_walk_minutes
        + len(selected_stops) * ESTIMATED_SHOPPING_MINUTES_PER_STORE
    )

    return (
        selected_stops,
        total_distance,
        total_walk_minutes,
        estimated_total_minutes,
    )