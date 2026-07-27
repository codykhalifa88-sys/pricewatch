"""Shared config for the API, workers, and scrapers."""
from __future__ import annotations

import os

from dotenv import load_dotenv

load_dotenv()

POSTGRES_HOST = os.getenv("POSTGRES_HOST", "localhost")
POSTGRES_PORT = os.getenv("POSTGRES_PORT", "5432")
POSTGRES_DB = os.getenv("POSTGRES_DB", "pricewatch")
POSTGRES_USER = os.getenv("POSTGRES_USER", "pricewatch_user")
POSTGRES_PASSWORD = os.getenv("POSTGRES_PASSWORD", "change_me")

DATABASE_URL = (
    f"postgresql+psycopg2://{POSTGRES_USER}:{POSTGRES_PASSWORD}"
    f"@{POSTGRES_HOST}:{POSTGRES_PORT}/{POSTGRES_DB}"
)

REDIS_HOST = os.getenv("REDIS_HOST", "localhost")
REDIS_PORT = int(os.getenv("REDIS_PORT", "6379"))

JWT_SECRET = os.getenv("JWT_SECRET", "dev-secret-change-in-production")
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 60 * 24 * 7  # 7 days

FREE_TIER_ITEM_LIMIT = 3
FREE_TIER_CHECK_INTERVAL_HOURS = 24
PRO_TIER_CHECK_INTERVAL_HOURS = 1

STRIPE_SECRET_KEY = os.getenv("STRIPE_SECRET_KEY", "")
STRIPE_WEBHOOK_SECRET = os.getenv("STRIPE_WEBHOOK_SECRET", "")
STRIPE_PRICE_ID_PRO = os.getenv("STRIPE_PRICE_ID_PRO", "")
FRONTEND_URL = os.getenv("FRONTEND_URL", "http://localhost:3000")

TELEGRAM_BOT_TOKEN = os.getenv("TELEGRAM_BOT_TOKEN", "")
SENDGRID_API_KEY = os.getenv("SENDGRID_API_KEY", "")
ALERT_FROM_EMAIL = os.getenv("ALERT_FROM_EMAIL", "alerts@pricewatch.example")

LOG_DIR = os.getenv("LOG_DIR", "logs")
