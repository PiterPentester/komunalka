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
