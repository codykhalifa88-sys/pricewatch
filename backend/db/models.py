"""SQLAlchemy ORM models, mirroring backend/db/schema.sql."""
from __future__ import annotations

from datetime import date, datetime

from sqlalchemy import (
    Boolean, CheckConstraint, Date, DateTime, ForeignKey, Numeric, String,
    UniqueConstraint, func,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass


class User(Base):
    __tablename__ = "users"

    id: Mapped[int] = mapped_column(primary_key=True)
    email: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    password_hash: Mapped[str] = mapped_column(String, nullable=False)
    subscription_tier: Mapped[str] = mapped_column(String, nullable=False, default="free")
    stripe_customer_id: Mapped[str | None] = mapped_column(String, nullable=True)
    telegram_chat_id: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    tracked_items: Mapped[list["TrackedItem"]] = relationship(back_populates="user", cascade="all, delete-orphan")


class TrackedItem(Base):
    __tablename__ = "tracked_items"

    id: Mapped[int] = mapped_column(primary_key=True)
    user_id: Mapped[int] = mapped_column(ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    product_url: Mapped[str] = mapped_column(String, nullable=False)
    product_name: Mapped[str | None] = mapped_column(String, nullable=True)
    store: Mapped[str] = mapped_column(String, nullable=False)
    target_price: Mapped[float] = mapped_column(Numeric, nullable=False)
    current_price: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    is_active: Mapped[bool] = mapped_column(Boolean, default=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    user: Mapped["User"] = relationship(back_populates="tracked_items")
    price_history: Mapped[list["PriceHistory"]] = relationship(back_populates="tracked_item", cascade="all, delete-orphan")


class PriceHistory(Base):
    __tablename__ = "price_history"

    id: Mapped[int] = mapped_column(primary_key=True)
    tracked_item_id: Mapped[int] = mapped_column(ForeignKey("tracked_items.id", ondelete="CASCADE"), nullable=False)
    price: Mapped[float] = mapped_column(Numeric, nullable=False)
    checked_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())

    tracked_item: Mapped["TrackedItem"] = relationship(back_populates="price_history")


class DiscountCode(Base):
    __tablename__ = "discount_codes"
    __table_args__ = (UniqueConstraint("store", "code"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    store: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)
    description: Mapped[str | None] = mapped_column(String, nullable=True)
    discount_percent: Mapped[float | None] = mapped_column(Numeric, nullable=True)
    expires_at: Mapped[date | None] = mapped_column(Date, nullable=True)
    scraped_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    is_verified: Mapped[bool] = mapped_column(Boolean, default=False)


class AlertSent(Base):
    __tablename__ = "alerts_sent"

    id: Mapped[int] = mapped_column(primary_key=True)
    tracked_item_id: Mapped[int] = mapped_column(ForeignKey("tracked_items.id", ondelete="CASCADE"), nullable=False)
    channel: Mapped[str] = mapped_column(String, nullable=False)
    sent_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class ScraperRun(Base):
    __tablename__ = "scraper_runs"
    __table_args__ = (CheckConstraint("status IN ('success', 'failure')"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    scraper_name: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False)
    items_checked: Mapped[int] = mapped_column(default=0)
    items_failed: Mapped[int] = mapped_column(default=0)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    run_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
