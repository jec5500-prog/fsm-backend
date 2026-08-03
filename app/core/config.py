from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """앱 전체 설정을 관리하는 클래스"""
    app_name: str = "FSM Backend"
    database_url: str = "sqlite:///./fsm.db"
    debug: bool = True

    # JWT 설정 추가
    SECRET_KEY: str = "임시-기본값-실제로는-env에서-읽음"
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    class Config:
        env_file = ".env"


settings = Settings()