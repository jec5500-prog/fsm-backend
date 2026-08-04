from pydantic import BaseModel, Field


class CourseRecommendRequest(BaseModel):
    """쇼핑 코스 추천 요청"""

    start_latitude: float = Field(ge=-90, le=90)
    start_longitude: float = Field(ge=-180, le=180)

    area: str = Field(min_length=1, max_length=50)
    styles: list[str] = Field(default_factory=list)

    max_stores: int = Field(default=3, ge=1, le=10)
    available_minutes: int = Field(default=240, ge=30, le=720)


class CourseStopResponse(BaseModel):
    """추천 코스의 한 매장"""

    order: int
    store_id: int
    name: str
    store_type: str
    styles: str | None
    address: str | None
    latitude: float
    longitude: float

    distance_from_previous_meters: int
    estimated_walk_minutes: int


class CourseRecommendResponse(BaseModel):
    """추천된 쇼핑 코스"""

    area: str
    stops: list[CourseStopResponse]

    total_distance_meters: int
    total_walk_minutes: int
    estimated_total_minutes: int

    message: str

class CourseSaveRequest(CourseRecommendRequest):
    """추천 조건을 이용해 코스를 저장하는 요청"""

    title: str | None = Field(default=None, max_length=100)


class CourseSavedResponse(BaseModel):
    """저장 완료된 코스"""

    id: int
    title: str
    share_token: str
    share_path: str

    area: str
    stops: list[CourseStopResponse]

    total_distance_meters: int
    total_walk_minutes: int
    estimated_total_minutes: int
    message: str


class SharedCourseResponse(BaseModel):
    """공유 링크로 조회하는 공개 코스"""

    id: int
    title: str
    area: str
    stops: list[CourseStopResponse]

    total_distance_meters: int
    total_walk_minutes: int
    estimated_total_minutes: int
    message: str