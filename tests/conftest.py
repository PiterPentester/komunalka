import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from models import Base
from app import app
from fastapi.testclient import TestClient
import os


@pytest.fixture(name="db_session")
def fixture_db_session():
    # Use a file-based SQLite for tests to avoid connection sharing issues with :memory:
    db_file = "test_komunalka.db"
    engine = create_engine(
        f"sqlite:///{db_file}", connect_args={"check_same_thread": False}
    )
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
    Base.metadata.drop_all(bind=engine)  # Start clean
    Base.metadata.create_all(bind=engine)
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()
        # Clean up
        if os.path.exists(db_file):
            os.remove(db_file)


@pytest.fixture(name="client")
def fixture_client(db_session):
    # Override get_db dependency to use the test database
    from app import get_db

    def override_get_db():
        try:
            yield db_session
        finally:
            pass

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# Fake account mapping — isolates all tests from the real CSV file.
# These accounts/addresses do NOT exist in production data.
# ---------------------------------------------------------------------------

FAKE_ACCOUNT_MAPPING = {
    # Water
    "T-0001": [
        {
            "address": "вул. Тестова, буд. 1, кв. 1",
            "service": "Вода та стоки",
            "company": "Тест-Водоканал",
        },
    ],
    # Gas supply
    "T-0002": [
        {
            "address": "вул. Тестова, буд. 1, кв. 1",
            "service": "Газопостачання",
            "company": "Тест-Газ",
        },
    ],
    # Gas transport
    "T-0003": [
        {
            "address": "вул. Тестова, буд. 1, кв. 1",
            "service": "Транспортування газу",
            "company": "Тест-Газмережі",
        },
    ],
    # Electricity
    "T-0004": [
        {
            "address": "вул. Тестова, буд. 1, кв. 1",
            "service": "електропостачання",
            "company": "Тест-Енерго",
        },
    ],
    # Garbage
    "T-0005": [
        {
            "address": "вул. Тестова, буд. 2, кв. 3",
            "service": "вивіз ТПВ",
            "company": "Тест-Сервіс",
        },
    ],
    # Multi-service: heating + maintenance for the same account
    "T-0006": [
        {
            "address": "вул. Тестова, буд. 3, кв. 5",
            "service": "Опалення",
            "company": "Тест-ЖКО",
        },
        {
            "address": "вул. Тестова, буд. 3, кв. 5",
            "service": "Утримання будинку",
            "company": "Тест-ЖКО",
        },
    ],
    # Multi-service: same account, different addresses (gas vs water)
    "T-0007": [
        {
            "address": "вул. Адресна, буд. 10",
            "service": "Газопостачання",
            "company": "Тест-Газ",
        },
        {
            "address": "вул. Інша, буд. 20",
            "service": "Вода та стоки",
            "company": "Тест-Вода",
        },
    ],
}


@pytest.fixture(autouse=True)
def fake_account_mapping(monkeypatch):
    """Patch utils.ACCOUNT_MAPPING with fake data for every test.

    This ensures tests are fully isolated from the real CSV file and
    will not break if the CSV is updated.
    """
    import utils

    monkeypatch.setattr(utils, "ACCOUNT_MAPPING", FAKE_ACCOUNT_MAPPING)
    return FAKE_ACCOUNT_MAPPING
