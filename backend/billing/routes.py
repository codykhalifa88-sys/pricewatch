import stripe
from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy.orm import Session

from backend.auth.jwt_handler import get_current_user
from backend.billing.models import CheckoutSessionOut, PortalSessionOut
from backend.config import (
    FRONTEND_URL,
    STRIPE_PRICE_ID_PRO,
    STRIPE_SECRET_KEY,
    STRIPE_WEBHOOK_SECRET,
)
from backend.db.models import User
from backend.db.session import get_db

stripe.api_key = STRIPE_SECRET_KEY

router = APIRouter(prefix="/billing", tags=["billing"])


@router.post("/create-checkout-session", response_model=CheckoutSessionOut)
def create_checkout_session(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db),
) -> CheckoutSessionOut:
    if current_user.subscription_tier == "pro":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Already on the Pro tier")

    try:
        if not current_user.stripe_customer_id:
            customer = stripe.Customer.create(email=current_user.email, metadata={"user_id": current_user.id})
            current_user.stripe_customer_id = customer.id
            db.commit()

        session = stripe.checkout.Session.create(
            customer=current_user.stripe_customer_id,
            mode="subscription",
            line_items=[{"price": STRIPE_PRICE_ID_PRO, "quantity": 1}],
            success_url=f"{FRONTEND_URL}/dashboard?upgraded=1",
            cancel_url=f"{FRONTEND_URL}/pricing",
            client_reference_id=str(current_user.id),
        )
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe error: {exc.user_message or str(exc)}",
        ) from exc

    return CheckoutSessionOut(checkout_url=session.url)


@router.post("/create-portal-session", response_model=PortalSessionOut)
def create_portal_session(current_user: User = Depends(get_current_user)) -> PortalSessionOut:
    if not current_user.stripe_customer_id:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No billing account yet — upgrade to Pro first")

    try:
        session = stripe.billing_portal.Session.create(
            customer=current_user.stripe_customer_id,
            return_url=f"{FRONTEND_URL}/dashboard",
        )
    except stripe.error.StripeError as exc:
        raise HTTPException(
            status_code=status.HTTP_502_BAD_GATEWAY,
            detail=f"Stripe error: {exc.user_message or str(exc)}",
        ) from exc

    return PortalSessionOut(portal_url=session.url)


@router.post("/webhook", status_code=status.HTTP_200_OK)
async def stripe_webhook(request: Request, db: Session = Depends(get_db)) -> dict:
    payload = await request.body()
    sig_header = request.headers.get("stripe-signature", "")

    try:
        event = stripe.Webhook.construct_event(payload, sig_header, STRIPE_WEBHOOK_SECRET)
    except (ValueError, stripe.error.SignatureVerificationError) as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Invalid webhook payload") from exc

    event_type = event["type"]
    data = event["data"]["object"]

    if event_type == "checkout.session.completed":
        user = _find_user(db, customer_id=data.get("customer"), client_reference_id=data.get("client_reference_id"))
        if user is not None:
            user.subscription_tier = "pro"
            user.stripe_customer_id = data.get("customer") or user.stripe_customer_id
            db.commit()

    elif event_type in ("customer.subscription.deleted", "customer.subscription.updated"):
        status_field = data.get("status")
        user = _find_user(db, customer_id=data.get("customer"))
        if user is not None:
            if event_type == "customer.subscription.deleted" or status_field in ("canceled", "unpaid", "incomplete_expired"):
                user.subscription_tier = "free"
            elif status_field == "active":
                user.subscription_tier = "pro"
            db.commit()

    return {"received": True}


def _find_user(db: Session, customer_id: str | None, client_reference_id: str | None = None) -> User | None:
    if customer_id:
        user = db.query(User).filter(User.stripe_customer_id == customer_id).first()
        if user is not None:
            return user
    if client_reference_id:
        return db.get(User, int(client_reference_id))
    return None
