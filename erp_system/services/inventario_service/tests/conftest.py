import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
# from sqlalchemy.pool import StaticPool # Not using SQLite for this setup
import os
import sys

# Ensure the application's root directory (inventario_service) is in PYTHONPATH
# so that 'from ..main import app' and other similar imports work correctly.
# The conftest.py is in .../inventario_service/tests/
# So, '..' should refer to .../inventario_service/
import sys # Added
import os  # Already there

# Add the 'services' directory (parent of 'inventario_service') to sys.path
# This allows 'inventario_service.main' etc. to be imported as a package.
# __file__ is .../inventario_service/tests/conftest.py
# os.path.dirname(__file__) is .../inventario_service/tests/
# parent_of_tests (inventario_service dir) is os.path.join(os.path.dirname(__file__), '..')
# parent_of_inventario_service (services dir) is os.path.join(os.path.dirname(__file__), '..', '..')
services_dir = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', '..'))
sys.path.insert(0, services_dir)

from sqlalchemy.pool import StaticPool # For SQLite in-memory

from inventario_service.main import app # FastAPI app instance
from inventario_service.database import Base, get_db # SQLAlchemy Base and original get_db dependency
from inventario_service import models as models_module # Renamed to avoid conflict, ensures models are loaded

# Use SQLite in-memory for tests for portability and to avoid external DB dependency for this environment
SQLALCHEMY_DATABASE_URL_TEST = "sqlite:///:memory:"

engine_test = create_engine(
    SQLALCHEMY_DATABASE_URL_TEST,
    connect_args={"check_same_thread": False}, # Necessary for SQLite
    poolclass=StaticPool, # Use StaticPool for SQLite in-memory
)
SessionTesting = sessionmaker(autocommit=False, autoflush=False, bind=engine_test)


@pytest.fixture(scope="function", autouse=True) # Changed scope to "function"
def setup_test_db():
    """
    Fixture to create all tables in the test database before each test runs,
    and drop them after all tests have completed for the session.
    """
    # Import all models here before calling Base.metadata.create_all
    # This ensures all tables are known to Base.
    # The import of 'inventario_service.models' as models_module earlier should be sufficient.

    Base.metadata.create_all(bind=engine_test)
    yield
    Base.metadata.drop_all(bind=engine_test)

# Override the get_db dependency for the FastAPI app
def override_get_db():
    """
    A dependency override for FastAPI's get_db.
    It provides a database session from the test database engine.
    This session is meant to be managed by the db_session fixture per test.
    """
    try:
        db = SessionTesting()
        yield db
    finally:
        db.close()

# Apply the dependency override to the app.
# This must happen before TestClient(app) is called, so module scope is fine.
app.dependency_overrides[get_db] = override_get_db

@pytest.fixture(scope="function")
def db_session():
    """
    Provides a clean database state for each test function using transactions.
    A connection is opened, a transaction started, and the session is bound to this transaction.
    After the test yields, the transaction is rolled back, and the connection closed.
    """
    connection = engine_test.connect()
    transaction = connection.begin()
    session = SessionTesting(bind=connection)

    yield session  # Test runs with this session

    session.close()
    transaction.rollback()
    connection.close()

@pytest.fixture(scope="module")
def client():
    """
    Provides a TestClient instance for making HTTP requests to the FastAPI app.
    This client uses the app with the overridden get_db dependency.
    Scope is 'module' as the client itself doesn't hold per-test state,
    and the database state is managed by db_session and setup_test_db.
    """
    with TestClient(app) as c:
        yield c
