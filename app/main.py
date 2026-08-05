from pathlib import Path

from fastapi import FastAPI
from fastapi.responses import FileResponse
from fastapi.staticfiles import StaticFiles

from app.core.config import settings
from app.core.database import Base, engine
from app.routers.course import router as course_router
from app.routers.store import router as store_router
from app.routers.user import router as user_router

import app.models


BASE_DIR = Path(__file__).resolve().parent
STATIC_DIR = BASE_DIR / "static"

Base.metadata.create_all(bind=engine)

app = FastAPI(
    title=settings.app_name,
    version="0.2.0",
)

app.mount(
    "/static",
    StaticFiles(directory=STATIC_DIR),
    name="static",
)

app.include_router(store_router)
app.include_router(user_router)
app.include_router(course_router)


@app.get("/", include_in_schema=False)
def show_homepage():
    return FileResponse(STATIC_DIR / "index.html")


@app.get("/api/client-config", include_in_schema=False)
def get_client_config():
    return {
        "kakao_javascript_key": settings.KAKAO_JAVASCRIPT_KEY,
    }


@app.get("/health")
def health_check():
    return {
        "status": "ok",
        "message": "FSM Backend is running",
    }