import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool
import os
import sys

# Add the 'services' directory (parent of 'auth_service') to sys.path
# This allows 'auth_service.main' etc. to be imported as a package.
SERVICES_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
if SERVICES_DIR not in sys.path:
    sys.path.insert(0, SERVICES_DIR)

from auth_service.main import app  # FastAPI app instance
from auth_service.database import Base, get_db, settings as app_db_settings # Original settings
# Import models to ensure they are registered with Base.metadata
from auth_service import models as auth_models # Using alias to avoid potential conflicts if User is defined elsewhere

# Test database setup (SQLite in-memory)
SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///:memory:"
engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL_TEST,
    connect_args={"check_same_thread": False},  # Required for SQLite
    poolclass=StaticPool,  # Use StaticPool for in-memory SQLite
)
SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)

@pytest.fixture(scope="function", autouse=True)
def setup_test_db_and_settings():
    # Store original settings
    original_settings_values = app_db_settings.model_dump()

    # Apply test-specific settings
    # These values should ideally match or be sourced from pytest.ini for consistency
    # For now, explicitly setting them here as per the example.
    app_db_settings.SECRET_KEY = "test_secret_key_for_pytest"
    app_db_settings.ALGORITHM = "HS256"
    app_db_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 15
    # Note: app_db_settings.DATABASE_URL is not changed here as engine_test uses a hardcoded SQLite URL.
    # If tests needed to respect DATABASE_URL from pytest.ini for PostgreSQL, this would be different.

    # Create database tables for each test
    Base.metadata.create_all(bind=engine_test)
    yield  # Test runs here
    # Drop database tables after each test
    Base.metadata.drop_all(bind=engine_test)

    # Restore original settings
    # Re-initialize settings from the stored original values
    # This is a bit simplistic; if Settings uses complex initialization, this might need adjustment.
    # A cleaner way might be to mock settings or use a context manager if Settings supported it easily.
    # Ensure all relevant settings are restored.
    app_db_settings.SECRET_KEY = original_settings_values.get("SECRET_KEY", app_db_settings.SECRET_KEY)
    app_db_settings.ALGORITHM = original_settings_values.get("ALGORITHM", app_db_settings.ALGORITHM)
    app_db_settings.ACCESS_TOKEN_EXPIRE_MINUTES = original_settings_values.get("ACCESS_TOKEN_EXPIRE_MINUTES", app_db_settings.ACCESS_TOKEN_EXPIRE_MINUTES)
    app_db_settings.DATABASE_URL = original_settings_values.get("DATABASE_URL", app_db_settings.DATABASE_URL)
    # Re-apply model_config if it was part of original_settings_values and pydantic allows it
    # For simplicity, assuming direct attribute restoration is sufficient for these specific fields.


# Override get_db dependency for test sessions
def override_get_db():
    try:
        db = SessionTesting()
        yield db
    finally:
        db.close()

app.dependency_overrides[get_db] = override_get_db # Use the get_db from auth_service.database

@pytest.fixture(scope="function")
def db_session():
    """
    Provides a clean database state for each test function using transactions.
    A connection is opened, a transaction started, and the session is bound to this transaction.
    After the test yields, the transaction is rolled back, and the connection closed.
    This is for tests that need to interact with the DB directly, outside of API calls.
    """
    connection = engine_test.connect()
    transaction = connection.begin()
    session = SessionTesting(bind=connection)

    yield session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="module") # client can be module-scoped if app setup (like dependency_overrides) is module-wide
def client():
    with TestClient(app) as c:
        yield c
