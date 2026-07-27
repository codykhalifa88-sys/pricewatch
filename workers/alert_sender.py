"""
After a price check, compares current_price to target_price. If the item
has dropped to or below target and no alert was sent for it in the last 24
hours (checked against alerts_sent), sends a notification.

Free tier: email only (if SendGrid is configured) + Telegram (if the user
linked a chat). Pro tier: same, plus would add SMS via Twilio — not wired
up by default since it's a paid API with no free tier, see README.

Both channels degrade gracefully to a log line if not configured, the same
placeholder pattern used in the other two projects' Slack webhook hooks —
so the alert logic can be fully tested without real credentials.
"""
from __future__ import annotations

from datetime import datetime, timedelta, timezone

import requests
from sqlalchemy import func
from sqlalchemy.orm import Session

from backend.config import ALERT_FROM_EMAIL, SENDGRID_API_KEY, TELEGRAM_BOT_TOKEN
from backend.db.models import AlertSent, TrackedItem
from workers.logging_setup import get_logger

logger = get_logger("alert_sender")

ALERT_COOLDOWN_HOURS = 24


def should_alert(item: TrackedItem, db: Session, now: datetime | None = None) -> bool:
    now = now or datetime.now(timezone.utc)
    if item.current_price is None or item.current_price > item.target_price:
        return False

    last_alert = (
        db.query(func.max(AlertSent.sent_at))
        .filter(AlertSent.tracked_item_id == item.id)
        .scalar()
    )
    if last_alert is None:
        return True
    if last_alert.tzinfo is None:
        last_alert = last_alert.replace(tzinfo=timezone.utc)
    return now - last_alert >= timedelta(hours=ALERT_COOLDOWN_HOURS)


def send_alert(item: TrackedItem, db: Session) -> list[str]:
    """Sends the alert on every configured channel, logs each success to
    alerts_sent, and returns the list of channels actually used."""
    channels_sent: list[str] = []

    subject = f"Price drop: {item.product_name or item.product_url}"
    body = (
        f"{item.product_name or 'Your tracked item'} is now £{item.current_price:.2f}, "
        f"at or below your target of £{item.target_price:.2f}.\n{item.product_url}"
    )

    if _send_email(item.user.email, subject, body):
        channels_sent.append("email")

    if item.user.telegram_chat_id and _send_telegram(item.user.telegram_chat_id, f"{subject}\n\n{body}"):
        channels_sent.append("telegram")

    for channel in channels_sent:
        db.add(AlertSent(tracked_item_id=item.id, channel=channel))
    if channels_sent:
        db.commit()
        logger.info("Alert sent for item %d via %s", item.id, ", ".join(channels_sent))
    else:
        logger.warning("Item %d qualifies for an alert but no channel is configured", item.id)

    return channels_sent


def _send_email(to_email: str, subject: str, body: str) -> bool:
    if not SENDGRID_API_KEY:
        logger.info("SENDGRID_API_KEY not set — would email %s: %s", to_email, subject)
        return False

    from sendgrid import SendGridAPIClient
    from sendgrid.helpers.mail import Mail

    message = Mail(from_email=ALERT_FROM_EMAIL, to_emails=to_email, subject=subject, plain_text_content=body)
    try:
        SendGridAPIClient(SENDGRID_API_KEY).send(message)
        return True
    except Exception:
        logger.exception("Failed to send email alert to %s", to_email)
        return False


def _send_telegram(chat_id: str, text: str) -> bool:
    if not TELEGRAM_BOT_TOKEN:
        logger.info("TELEGRAM_BOT_TOKEN not set — would message chat %s: %s", chat_id, text[:80])
        return False

    url = f"https://api.telegram.org/bot{TELEGRAM_BOT_TOKEN}/sendMessage"
    try:
        resp = requests.post(url, json={"chat_id": chat_id, "text": text}, timeout=10)
        resp.raise_for_status()
        return True
    except requests.RequestException:
        logger.exception("Failed to send Telegram alert to chat %s", chat_id)
        return False


def run_alert_checks(db: Session, now: datetime | None = None) -> int:
    now = now or datetime.now(timezone.utc)
    items = db.query(TrackedItem).filter(TrackedItem.is_active.is_(True)).all()

    sent_count = 0
    for item in items:
        if should_alert(item, db, now):
            if send_alert(item, db):
                sent_count += 1

    logger.info("Alert check run complete: %d alerts sent", sent_count)
    return sent_count
