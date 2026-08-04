import httpx

from app.core.config import settings


class KakaoLocalAPIError(Exception):
    """카카오 로컬 API 호출 실패 예외"""


class KakaoLocalService:
    """카카오 로컬 API를 이용한 장소 검색 서비스"""

    BASE_URL = "https://dapi.kakao.com/v2/local/search/keyword.json"

    def search_places(
        self,
        query: str,
        max_results: int = 15,
    ) -> list[dict]:
        """키워드로 장소를 검색해 원본 장소 목록을 반환한다."""

        headers = {
            "Authorization": f"KakaoAK {settings.KAKAO_REST_API_KEY}",
        }
        params = {
            "query": query,
            "size": max_results,
            "page": 1,
        }

        try:
            with httpx.Client(timeout=10.0) as client:
                response = client.get(
                    self.BASE_URL,
                    headers=headers,
                    params=params,
                )
                response.raise_for_status()

        except httpx.HTTPError as error:
            raise KakaoLocalAPIError(
                f"카카오 장소 검색 요청에 실패했습니다: {error}"
            ) from error

        data = response.json()
        return data.get("documents", [])


kakao_local_service = KakaoLocalService()