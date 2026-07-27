"""FastAPI entrypoint. Auto-generated docs at /docs."""
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from backend.auth.routes import router as auth_router
from backend.billing.routes import router as billing_router
from backend.config import FRONTEND_URL
from backend.discount_codes.routes import router as discount_codes_router
from backend.items.routes import router as items_router
from backend.search.routes import router as search_router

app = FastAPI(
    title="PriceWatch API",
    description="Track prices, get notified when they drop, find discount codes.",
    version="0.1.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=[FRONTEND_URL, "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth_router)
app.include_router(billing_router)
app.include_router(items_router)
app.include_router(discount_codes_router)
app.include_router(search_router)


@app.get("/health")
def health() -> dict:
    return {"status": "ok"}
