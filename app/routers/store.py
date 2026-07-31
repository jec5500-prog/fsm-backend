from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.models import Store
from app.schemas import StoreCreate, StoreResponse

router = APIRouter(prefix="/stores", tags=["stores"])


@router.post("/", response_model=StoreResponse)
def create_store(store_in: StoreCreate, db: Session = Depends(get_db)):
    """가게 등록"""
    store = Store(**store_in.model_dump())   # 스키마 → 모델 변환
    db.add(store)                             # 저장 준비
    db.commit()                               # 실제 저장!
    db.refresh(store)                         # DB가 만든 id를 다시 읽어옴
    return store


@router.get("/", response_model=list[StoreResponse])
def get_stores(db: Session = Depends(get_db)):
    """가게 전체 목록 조회"""
    return db.query(Store).all()