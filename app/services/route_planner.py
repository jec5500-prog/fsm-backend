import math

from app.models import Store


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
    현재 위치에서 가장 가까운 매장을 순서대로 고르는
    초기 버전의 동선 추천 알고리즘.
    """

    remaining_stores = list(stores)
    selected_stops: list[dict] = []

    current_latitude = start_latitude
    current_longitude = start_longitude

    total_distance = 0
    total_walk_minutes = 0

    while remaining_stores and len(selected_stops) < max_stores:
        nearest_store = min(
            remaining_stores,
            key=lambda store: haversine_distance_meters(
                current_latitude,
                current_longitude,
                store.latitude,
                store.longitude,
            ),
        )

        distance = haversine_distance_meters(
            current_latitude,
            current_longitude,
            nearest_store.latitude,
            nearest_store.longitude,
        )
        walk_minutes = max(
            1,
            math.ceil(distance / WALKING_SPEED_METERS_PER_MINUTE),
        )

        estimated_total_if_added = (
            total_walk_minutes
            + walk_minutes
            + (len(selected_stops) + 1)
            * ESTIMATED_SHOPPING_MINUTES_PER_STORE
        )

        if estimated_total_if_added > available_minutes:
            break

        selected_stops.append(
            {
                "store": nearest_store,
                "distance_from_previous_meters": round(distance),
                "estimated_walk_minutes": walk_minutes,
            }
        )

        total_distance += round(distance)
        total_walk_minutes += walk_minutes

        current_latitude = nearest_store.latitude
        current_longitude = nearest_store.longitude
        remaining_stores.remove(nearest_store)

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