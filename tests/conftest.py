import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
from models import Base
from app import app
from fastapi.testclient import TestClient

# Create a single in-memory SQLite engine using StaticPool so all 
# connections and sessions share the exact same in-memory database.
engine = create_engine(
    "sqlite:///:memory:",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)


@pytest.fixture(scope="session", autouse=True)
def setup_database():
    """Create all tables once per test session in memory."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)
    engine.dispose()


@pytest.fixture(name="db_session")
def fixture_db_session():
    """Provide a transactional session that rolls back after each test."""
    connection = engine.connect()
    transaction = connection.begin()
    
    TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=connection)
    session = TestingSessionLocal()
    
    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


@pytest.fixture(name="client")
def fixture_client(db_session):
    """Override FastAPI dependency to use the test database session."""
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
# ---------------------------------------------------------------------------

FAKE_ACCOUNT_MAPPING = {
    "T-0001": [
        {
            "address": "вул. Тестова, буд. 1, кв. 1",
            "service": "Вода та стоки",
            "company": "Тест-Водоканал",
        },
    ],
    "T-0002": [
        {
            "address": "вул. Тестова, буд. 1, кв. 1",
            "service": "Газопостачання",
            "company": "Тест-Газ",
        },
    ],
    "T-0003": [
        {
            "address": "вул. Тестова, буд. 1, кв. 1",
            "service": "Транспортування газу",
            "company": "Тест-Газмережі",
        },
    ],
    "T-0004": [
        {
            "address": "вул. Тестова, буд. 1, кв. 1",
            "service": "електропостачання",
            "company": "Тест-Енерго",
        },
    ],
    "T-0005": [
        {
            "address": "вул. Тестова, буд. 2, кв. 3",
            "service": "вивіз ТПВ",
            "company": "Тест-Сервіс",
        },
    ],
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
    import utils
    monkeypatch.setattr(utils, "ACCOUNT_MAPPING", FAKE_ACCOUNT_MAPPING)
    return FAKE_ACCOUNT_MAPPING