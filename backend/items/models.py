"""Pydantic request/response schemas for tracked items (ORM models live in
backend/db/models.py)."""
from datetime import datetime

from pydantic import BaseModel, Field


class TrackedItemCreate(BaseModel):
    product_url: str
    store: str
    target_price: float = Field(gt=0)


class TrackedItemUpdate(BaseModel):
    target_price: float | None = Field(default=None, gt=0)
    is_active: bool | None = None


class TrackedItemOut(BaseModel):
    id: int
    product_url: str
    product_name: str | None
    store: str
    target_price: float
    current_price: float | None
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class PriceHistoryPoint(BaseModel):
    price: float
    checked_at: datetime

    class Config:
        from_attributes = True
