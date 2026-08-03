from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session

from app.core.database import get_db
from app.core.security import get_current_user   # ← 추가!
from app.models import Store, User                # ← User 추가!
from app.schemas import StoreCreate, StoreResponse

router = APIRouter(prefix="/stores", tags=["stores"])


@router.post("/", response_model=StoreResponse)
def create_store(
    store_in: StoreCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),  # ← 로그인 필수!
):
    """가게 등록 (로그인 필요)"""
    store = Store(
        **store_in.model_dump(),
        owner_id=current_user.id,   # ← 로그인한 사람이 주인!
    )
    db.add(store)
    db.commit()
    db.refresh(store)
    return store


@router.get("/", response_model=list[StoreResponse])
def get_stores(db: Session = Depends(get_db)):
    """가게 전체 목록 조회"""
    return db.query(Store).all()