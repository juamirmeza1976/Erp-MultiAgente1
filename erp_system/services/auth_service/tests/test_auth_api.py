from fastapi.testclient import TestClient
from jose import jwt
from sqlalchemy.orm import Session # Import Session for type hinting
# Import app_settings from the auth_service.database module to access test JWT settings
# This works because conftest.py modifies this shared settings object during test setup.
from auth_service.database import settings as test_settings # Access the potentially modified settings
# from auth_service.schemas import User # If needed for response validation beyond dict checks
# Import models via the alias established in conftest.py if direct model interaction is needed
# No, conftest uses 'from auth_service import models as auth_models'.
# For tests, directly importing from auth_service.models is clearer.
from auth_service.models import User as UserModel # Alias to avoid conflict if schemas.User is imported
import uuid # Import uuid module

USER_USERNAME = "testuser"
USER_EMAIL = "test@example.com"
USER_PASSWORD = "testpassword"
USER_FULL_NAME = "Test User Full Name"

def test_health_check(client: TestClient):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok", "message": "Auth Service is healthy"}

def test_register_user_success(client: TestClient):
    response = client.post(
        "/auth/register",
        json={"username": USER_USERNAME, "email": USER_EMAIL, "password": USER_PASSWORD, "full_name": USER_FULL_NAME},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["email"] == USER_EMAIL
    assert data["username"] == USER_USERNAME
    assert data["full_name"] == USER_FULL_NAME
    assert "id" in data
    assert data["is_active"] == True # Default from User model
    assert "hashed_password" not in data

def test_register_user_duplicate_email(client: TestClient):
    # First registration
    client.post("/auth/register", json={"username": "anotheruser", "email": USER_EMAIL, "password": "anotherpassword", "full_name": "Another User"})
    # Attempt to register with the same email
    response = client.post("/auth/register", json={"username": USER_USERNAME, "email": USER_EMAIL, "password": USER_PASSWORD, "full_name": USER_FULL_NAME})
    assert response.status_code == 400, response.text
    assert "Email already registered" in response.json()["detail"]

def test_register_user_duplicate_username(client: TestClient):
    # First registration
    client.post("/auth/register", json={"username": USER_USERNAME, "email": "another@example.com", "password": "anotherpassword", "full_name": "Another User"})
    # Attempt to register with the same username
    response = client.post("/auth/register", json={"username": USER_USERNAME, "email": USER_EMAIL, "password": USER_PASSWORD, "full_name": USER_FULL_NAME})
    assert response.status_code == 400, response.text
    assert "Username already taken" in response.json()["detail"]

def test_login_success(client: TestClient):
    # Register user first
    client.post("/auth/register", json={"username": USER_USERNAME, "email": USER_EMAIL, "password": USER_PASSWORD, "full_name": USER_FULL_NAME})

    login_response = client.post(
        "/auth/login",
        data={"username": USER_USERNAME, "password": USER_PASSWORD}, # OAuth2PasswordRequestForm uses form data
    )
    assert login_response.status_code == 200, login_response.text
    token_data = login_response.json()
    assert "access_token" in token_data
    assert token_data["token_type"] == "bearer"

    # Decode the token to verify the 'sub' (username)
    # Use the test_settings which conftest should have modified for the test session
    decoded_token = jwt.decode(token_data["access_token"], test_settings.SECRET_KEY, algorithms=[test_settings.ALGORITHM])
    assert decoded_token["sub"] == USER_USERNAME

def test_login_wrong_password(client: TestClient):
    client.post("/auth/register", json={"username": USER_USERNAME, "email": USER_EMAIL, "password": USER_PASSWORD, "full_name": USER_FULL_NAME})
    response = client.post("/auth/login", data={"username": USER_USERNAME, "password": "wrongpassword"})
    assert response.status_code == 401, response.text
    assert "Incorrect username or password" in response.json()["detail"]

def test_login_user_not_found(client: TestClient):
    response = client.post("/auth/login", data={"username": "nonexistentuser", "password": "anypassword"})
    assert response.status_code == 401, response.text
    assert "Incorrect username or password" in response.json()["detail"]

def test_read_users_me_success(client: TestClient):
    # Register and login to get a token
    client.post("/auth/register", json={"username": USER_USERNAME, "email": USER_EMAIL, "password": USER_PASSWORD, "full_name": USER_FULL_NAME})
    login_response = client.post("/auth/login", data={"username": USER_USERNAME, "password": USER_PASSWORD})
    token = login_response.json()["access_token"]

    me_response = client.get("/users/me", headers={"Authorization": f"Bearer {token}"})
    assert me_response.status_code == 200, me_response.text
    data = me_response.json()
    assert data["username"] == USER_USERNAME
    assert data["email"] == USER_EMAIL
    assert data["full_name"] == USER_FULL_NAME
    assert data["is_active"] == True

def test_read_users_me_no_token(client: TestClient):
    response = client.get("/users/me")
    assert response.status_code == 401, response.text
    # Default FastAPI message for missing OAuth2 token might vary slightly, check actual if needed
    assert "Not authenticated" in response.json()["detail"]

def test_read_users_me_invalid_token(client: TestClient):
    response = client.get("/users/me", headers={"Authorization": "Bearer invalidtoken"})
    assert response.status_code == 401, response.text
    assert "Could not validate credentials" in response.json()["detail"]

def test_login_inactive_user(client: TestClient, db_session: Session): # db_session fixture from conftest
    # from models import User # Direct model import for DB manipulation - changed to UserModel
    # 1. Registrar usuario
    reg_response = client.post(
        "/auth/register",
        json={"username": "inactiveuser", "email": "inactive@example.com", "password": "password", "full_name": "Inactive User"},
    )
    assert reg_response.status_code == 201
    user_id_str = reg_response.json()["id"]
    user_id_uuid = uuid.UUID(user_id_str) # Convert string to UUID object

    # 2. Marcar usuario como inactivo en la BD
    # This requires the db_session fixture to be correctly set up for direct DB access within tests,
    # which it is in the current conftest.py (though not used by client automatically).
    # We need to make sure the session from db_session is the one used for this operation.
    db_user = db_session.query(UserModel).filter(UserModel.id == user_id_uuid).first()
    assert db_user is not None
    db_user.is_active = False
    db_session.commit()
    db_session.refresh(db_user) # Ensure change is reflected if session is used again

    # 3. Intentar login
    login_response = client.post(
        "/auth/login",
        data={"username": "inactiveuser", "password": "password"},
    )
    # 4. Verificar error 400 "Inactive user"
    assert login_response.status_code == 400, login_response.text
    assert "Inactive user" in login_response.json()["detail"]
