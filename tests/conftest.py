"""In-memory SQLite session for fast, dependency-free unit tests of the
alert/price-check logic. Postgres-only features (discount_scraper's
ON CONFLICT upsert) aren't exercised by these tests."""
import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from backend.db.models import Base


@pytest.fixture()
def db_session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    session = Session()
    try:
        yield session
    finally:
        session.close()
