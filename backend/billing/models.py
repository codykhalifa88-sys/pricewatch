"""Pydantic request/response schemas for billing (ORM models live in
backend/db/models.py)."""
from pydantic import BaseModel


class CheckoutSessionOut(BaseModel):
    checkout_url: str


class PortalSessionOut(BaseModel):
    portal_url: str
