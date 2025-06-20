from datetime import datetime, timedelta, timezone
from typing import Optional

from jose import JWTError, jwt
from passlib.context import CryptContext

from .database import settings # Import settings for SECRET_KEY, ALGORITHM, etc.
from . import schemas # To use schemas.TokenData

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# JWT Settings will be read directly from settings object in functions
# SECRET_KEY = settings.SECRET_KEY # No longer module-level copy
# ALGORITHM = settings.ALGORITHM # No longer module-level copy
# ACCESS_TOKEN_EXPIRE_MINUTES = settings.ACCESS_TOKEN_EXPIRE_MINUTES # No longer module-level copy

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def create_access_token(data: dict, expires_delta: Optional[timedelta] = None) -> str:
    """
    Creates a new JWT access token.
    The 'data' dictionary is typically {'sub': username}.
    """
    to_encode = data.copy()
    if expires_delta:
        expire = datetime.now(timezone.utc) + expires_delta
    else:
        expire = datetime.now(timezone.utc) + timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES) # Use live settings

    to_encode.update({"exp": expire})
    # Ensure 'sub' is present, as it's standard for JWT subject (username)
    if "sub" not in to_encode:
        # This case should ideally be handled by the caller ensuring 'sub' is in data.
        # For now, if 'username' is in data but 'sub' isn't, use 'username' as 'sub'.
        if "username" in to_encode: # Compatibility with TokenData(username=...)
            to_encode["sub"] = to_encode.pop("username")

    encoded_jwt = jwt.encode(to_encode, settings.SECRET_KEY, algorithm=settings.ALGORITHM) # Use live settings
    return encoded_jwt

def decode_access_token(token: str) -> schemas.TokenData | None:
    """
    Decodes a JWT access token.
    Returns TokenData if valid, None otherwise.
    """
    try:
        payload = jwt.decode(token, settings.SECRET_KEY, algorithms=[settings.ALGORITHM]) # Use live settings
        username: Optional[str] = payload.get("sub") # 'sub' is the standard field for subject (username)

        if username is None:
            # Token might be valid but missing the 'sub' claim, or 'sub' is not a string.
            # Depending on strictness, could raise an error or return None.
            return None
        return schemas.TokenData(username=username)
    except JWTError: # Catches various errors: expired, invalid signature, etc.
        return None


# The authenticate_user function is more of a conceptual helper.
# Actual authentication logic will combine get_user_by_username (from crud)
# and verify_password (from core) in the login endpoint.
#
# from sqlalchemy.orm import Session
# from . import crud
# def authenticate_user(db: Session, username: str, password: str) -> models.User | None:
#     user = crud.get_user_by_username(db, username=username)
#     if not user:
#         return None
#     if not verify_password(password, user.hashed_password):
#         return None
#     return user
