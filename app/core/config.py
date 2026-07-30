from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    """앱 전체 설정을 관리하는 클래스"""
    app_name: str = "FSM Backend"
    database_url: str = "sqlite:///./fsm.db"
    debug: bool = True

    class Config:
        env_file = ".env"  # .env 파일이 있으면 거기서 값을 읽어옴


settings = Settings()