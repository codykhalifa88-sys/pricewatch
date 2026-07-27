# PriceWatch

Track prices on supported stores, get alerted when they drop below your
target, and browse a directory of discount codes. Built as a portfolio
demo — Stripe billing runs in test mode, no real charges.

## Stack

- **Backend**: FastAPI + SQLAlchemy (Postgres), JWT auth, Stripe billing
- **Frontend**: Next.js (pages router) + Tailwind
- **Workers**: APScheduler-based background process for price checks, alerts, and discount-code scraping
- **Infra**: Postgres + Redis, orchestrated via `docker-compose.yml`

## Features

- Email/password auth (JWT)
- Track items across supported stores ([`scrapers/registry.py`](scrapers/registry.py) lists them), with price history and target-price alerts
- Free tier: 3 items, daily checks. Pro tier (Stripe subscription, £5/mo): unlimited items, hourly checks
- Discount code directory, scraped periodically
- Cross-store price comparison search

## Running locally

```bash
cp .env.example .env   # fill in a JWT secret; Stripe keys are optional (billing degrades gracefully without them)
docker compose up --build
```

- API: http://localhost:8000 (docs at `/docs`)
- Frontend: http://localhost:3000

Or run each piece directly:

```bash
# Backend
pip install -r requirements.txt
uvicorn backend.main:app --reload

# Frontend
cd frontend && npm install && npm run dev

# Background worker (price checks, alerts, discount scraping)
python -m workers.scheduler
```

## Tests

```bash
pytest
```

Stripe calls are monkeypatched in tests — no network calls or real API keys required.
