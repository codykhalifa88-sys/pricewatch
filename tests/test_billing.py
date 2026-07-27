"""Billing route tests. Stripe itself is never called — every stripe.*
function used by backend/billing/routes.py is monkeypatched, matching the
project's existing style of stubbing external calls (see test_scrapers.py)."""
from contextlib import contextmanager

import pytest
import stripe
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from backend.auth.jwt_handler import get_current_user
from backend.db.models import Base, User
from backend.db.session import get_db
from backend.main import app


@pytest.fixture()
def db_session():
    # TestClient runs the app in a worker thread; a plain sqlite in-memory
    # engine hands each thread its own empty database, so this needs
    # StaticPool + check_same_thread=False to share one connection.
    engine = create_engine(
        "sqlite:///:memory:",
        connect_args={"check_same_thread": False},
        poolclass=StaticPool,
    )
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()


def _make_user(db_session, tier="free", stripe_customer_id=None):
    user = User(
        email=f"user{id(object())}@example.com",
        password_hash="x",
        subscription_tier=tier,
        stripe_customer_id=stripe_customer_id,
    )
    db_session.add(user)
    db_session.commit()
    return user


@contextmanager
def _client(db_session, user):
    app.dependency_overrides[get_db] = lambda: db_session
    app.dependency_overrides[get_current_user] = lambda: user
    try:
        yield TestClient(app)
    finally:
        app.dependency_overrides.clear()


def test_create_checkout_session_creates_customer_and_returns_url(db_session, monkeypatch):
    user = _make_user(db_session)

    monkeypatch.setattr(stripe.Customer, "create", lambda **kw: type("C", (), {"id": "cus_new123"})())
    monkeypatch.setattr(
        stripe.checkout.Session, "create", lambda **kw: type("S", (), {"url": "https://checkout.stripe.test/abc"})()
    )

    with _client(db_session, user) as client:
        resp = client.post("/billing/create-checkout-session")

    assert resp.status_code == 200
    assert resp.json() == {"checkout_url": "https://checkout.stripe.test/abc"}
    db_session.refresh(user)
    assert user.stripe_customer_id == "cus_new123"


def test_create_checkout_session_returns_502_on_stripe_error(db_session, monkeypatch):
    user = _make_user(db_session)

    def raise_auth_error(**kw):
        raise stripe.error.AuthenticationError("You did not provide an API key.")

    monkeypatch.setattr(stripe.Customer, "create", raise_auth_error)

    with _client(db_session, user) as client:
        resp = client.post("/billing/create-checkout-session")

    assert resp.status_code == 502
    db_session.refresh(user)
    assert user.stripe_customer_id is None


def test_create_checkout_session_reuses_existing_customer(db_session, monkeypatch):
    user = _make_user(db_session, stripe_customer_id="cus_existing")

    def fail_create(**kw):
        raise AssertionError("should not create a new customer when one already exists")

    monkeypatch.setattr(stripe.Customer, "create", fail_create)
    captured = {}

    def fake_session_create(**kw):
        captured.update(kw)
        return type("S", (), {"url": "https://checkout.stripe.test/xyz"})()

    monkeypatch.setattr(stripe.checkout.Session, "create", fake_session_create)

    with _client(db_session, user) as client:
        resp = client.post("/billing/create-checkout-session")

    assert resp.status_code == 200
    assert captured["customer"] == "cus_existing"


def test_create_checkout_session_rejects_existing_pro_user(db_session):
    user = _make_user(db_session, tier="pro", stripe_customer_id="cus_pro")

    with _client(db_session, user) as client:
        resp = client.post("/billing/create-checkout-session")

    assert resp.status_code == 400


def test_create_portal_session_requires_stripe_customer(db_session):
    user = _make_user(db_session)

    with _client(db_session, user) as client:
        resp = client.post("/billing/create-portal-session")

    assert resp.status_code == 400


def test_create_portal_session_returns_url(db_session, monkeypatch):
    user = _make_user(db_session, tier="pro", stripe_customer_id="cus_existing")

    monkeypatch.setattr(
        stripe.billing_portal.Session,
        "create",
        lambda **kw: type("S", (), {"url": "https://billing.stripe.test/portal"})(),
    )

    with _client(db_session, user) as client:
        resp = client.post("/billing/create-portal-session")

    assert resp.status_code == 200
    assert resp.json() == {"portal_url": "https://billing.stripe.test/portal"}


def _fake_event(event_type, data_object):
    return {"type": event_type, "data": {"object": data_object}}


def test_webhook_checkout_completed_upgrades_user(db_session, monkeypatch):
    user = _make_user(db_session)
    event = _fake_event(
        "checkout.session.completed",
        {"customer": "cus_new123", "client_reference_id": str(user.id)},
    )
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *a, **kw: event)

    with _client(db_session, user) as client:
        resp = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "sig"})

    assert resp.status_code == 200
    db_session.refresh(user)
    assert user.subscription_tier == "pro"
    assert user.stripe_customer_id == "cus_new123"


def test_webhook_subscription_deleted_downgrades_user(db_session, monkeypatch):
    user = _make_user(db_session, tier="pro", stripe_customer_id="cus_existing")
    event = _fake_event("customer.subscription.deleted", {"customer": "cus_existing", "status": "canceled"})
    monkeypatch.setattr(stripe.Webhook, "construct_event", lambda *a, **kw: event)

    with _client(db_session, user) as client:
        resp = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "sig"})

    assert resp.status_code == 200
    db_session.refresh(user)
    assert user.subscription_tier == "free"


def test_webhook_invalid_signature_returns_400(db_session, monkeypatch):
    user = _make_user(db_session)

    def raise_invalid(*a, **kw):
        raise stripe.error.SignatureVerificationError("bad signature", "sig")

    monkeypatch.setattr(stripe.Webhook, "construct_event", raise_invalid)

    with _client(db_session, user) as client:
        resp = client.post("/billing/webhook", content=b"{}", headers={"stripe-signature": "bad"})

    assert resp.status_code == 400
