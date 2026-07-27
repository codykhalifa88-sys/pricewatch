from pydantic import BaseModel
from datetime import date, datetime

from fastapi import APIRouter, Depends, Query
from sqlalchemy.orm import Session

from backend.db.models import DiscountCode
from backend.db.session import get_db

router = APIRouter(prefix="/discount-codes", tags=["discount-codes"])


class DiscountCodeOut(BaseModel):
    id: int
    store: str
    code: str
    description: str | None
    discount_percent: float | None
    expires_at: date | None
    is_verified: bool
    scraped_at: datetime

    class Config:
        from_attributes = True


@router.get("", response_model=list[DiscountCodeOut])
def list_discount_codes(
    store: str | None = Query(default=None),
    search: str | None = Query(default=None),
    db: Session = Depends(get_db),
) -> list[DiscountCode]:
    query = db.query(DiscountCode)
    if store:
        query = query.filter(DiscountCode.store.ilike(f"%{store}%"))
    if search:
        query = query.filter(DiscountCode.description.ilike(f"%{search}%"))
    return query.order_by(DiscountCode.scraped_at.desc()).limit(200).all()


@router.get("/stores", response_model=list[str])
def list_stores_with_codes(db: Session = Depends(get_db)) -> list[str]:
    rows = db.query(DiscountCode.store).distinct().all()
    return sorted({r[0] for r in rows})
