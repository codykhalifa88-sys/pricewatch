from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from backend.auth.jwt_handler import get_current_user
from backend.config import FREE_TIER_ITEM_LIMIT
from backend.db.models import PriceHistory, TrackedItem, User
from backend.db.session import get_db
from backend.items.models import PriceHistoryPoint, TrackedItemCreate, TrackedItemOut, TrackedItemUpdate
from scrapers.registry import supported_stores

router = APIRouter(prefix="/items", tags=["items"])


@router.get("/supported-stores", response_model=list[str])
def list_supported_stores() -> list[str]:
    return supported_stores()


@router.get("", response_model=list[TrackedItemOut])
def list_items(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[TrackedItem]:
    return (
        db.query(TrackedItem)
        .filter(TrackedItem.user_id == current_user.id, TrackedItem.is_active.is_(True))
        .order_by(TrackedItem.created_at.desc())
        .all()
    )


@router.post("", response_model=TrackedItemOut, status_code=status.HTTP_201_CREATED)
def create_item(
    payload: TrackedItemCreate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrackedItem:
    if payload.store not in supported_stores():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail=f"Unsupported store {payload.store!r}. Supported: {supported_stores()}",
        )

    # Tier limit enforced server-side — the frontend also hides the "add
    # item" button at the limit, but that's UX polish, not the actual gate.
    if current_user.subscription_tier == "free":
        active_count = (
            db.query(TrackedItem)
            .filter(TrackedItem.user_id == current_user.id, TrackedItem.is_active.is_(True))
            .count()
        )
        if active_count >= FREE_TIER_ITEM_LIMIT:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Free tier is limited to {FREE_TIER_ITEM_LIMIT} tracked items. Upgrade to Pro for unlimited tracking.",
            )

    item = TrackedItem(
        user_id=current_user.id,
        product_url=payload.product_url,
        store=payload.store,
        target_price=payload.target_price,
    )
    db.add(item)
    db.commit()
    db.refresh(item)
    return item


@router.get("/{item_id}", response_model=TrackedItemOut)
def get_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrackedItem:
    item = _get_owned_item(db, item_id, current_user.id)
    return item


@router.patch("/{item_id}", response_model=TrackedItemOut)
def update_item(
    item_id: int,
    payload: TrackedItemUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> TrackedItem:
    item = _get_owned_item(db, item_id, current_user.id)
    if payload.target_price is not None:
        item.target_price = payload.target_price
    if payload.is_active is not None:
        item.is_active = payload.is_active
    db.commit()
    db.refresh(item)
    return item


@router.delete("/{item_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_item(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> None:
    item = _get_owned_item(db, item_id, current_user.id)
    item.is_active = False
    db.commit()


@router.get("/{item_id}/history", response_model=list[PriceHistoryPoint])
def item_price_history(
    item_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> list[PriceHistory]:
    _get_owned_item(db, item_id, current_user.id)  # ownership check
    return (
        db.query(PriceHistory)
        .filter(PriceHistory.tracked_item_id == item_id)
        .order_by(PriceHistory.checked_at.asc())
        .all()
    )


def _get_owned_item(db: Session, item_id: int, user_id: int) -> TrackedItem:
    item = db.get(TrackedItem, item_id)
    if item is None or item.user_id != user_id:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Item not found")
    return item
