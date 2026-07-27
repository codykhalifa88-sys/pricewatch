from datetime import datetime, timedelta, timezone

from backend.db.models import AlertSent, TrackedItem, User
from workers.alert_sender import should_alert


_email_counter = 0


def _make_user_and_item(db_session, current_price, target_price):
    global _email_counter
    _email_counter += 1
    user = User(email=f"test{_email_counter}@example.com", password_hash="x")
    db_session.add(user)
    db_session.commit()

    item = TrackedItem(
        user_id=user.id,
        product_url="https://example.com/p",
        store="books_to_scrape",
        target_price=target_price,
        current_price=current_price,
    )
    db_session.add(item)
    db_session.commit()
    return item


def test_no_alert_when_price_above_target(db_session):
    item = _make_user_and_item(db_session, current_price=50.0, target_price=40.0)
    assert should_alert(item, db_session) is False


def test_alert_when_price_at_or_below_target(db_session):
    item = _make_user_and_item(db_session, current_price=40.0, target_price=40.0)
    assert should_alert(item, db_session) is True

    item2 = _make_user_and_item(db_session, current_price=35.0, target_price=40.0)
    assert should_alert(item2, db_session) is True


def test_no_alert_within_cooldown_window(db_session):
    item = _make_user_and_item(db_session, current_price=30.0, target_price=40.0)
    db_session.add(AlertSent(tracked_item_id=item.id, channel="email", sent_at=datetime.now(timezone.utc)))
    db_session.commit()

    assert should_alert(item, db_session) is False


def test_alert_again_after_cooldown_expires(db_session):
    item = _make_user_and_item(db_session, current_price=30.0, target_price=40.0)
    old_alert_time = datetime.now(timezone.utc) - timedelta(hours=25)
    db_session.add(AlertSent(tracked_item_id=item.id, channel="email", sent_at=old_alert_time))
    db_session.commit()

    assert should_alert(item, db_session) is True


def test_no_alert_when_current_price_unknown(db_session):
    item = _make_user_and_item(db_session, current_price=None, target_price=40.0)
    assert should_alert(item, db_session) is False
