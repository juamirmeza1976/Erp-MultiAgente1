from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer, OAuth2PasswordRequestForm
from jose import JWTError # Already in core, but good for direct use if needed here
from sqlalchemy.orm import Session
from datetime import timedelta # For token expiration

from . import crud, models, schemas, core, database # database.get_db, database.settings

# oauth2_scheme defines that the token must be sent in the Authorization header
# as a Bearer token. tokenUrl points to the login endpoint.
oauth2_scheme = OAuth2PasswordBearer(tokenUrl="/auth/login")

# FastAPI app initialization (from previous setup)
app = FastAPI(
    title="Servicio de Autenticación",
    version="1.0.0",
    description="Servicio para gestionar usuarios y tokens de autenticación.",
    tags=[ # Define tags for Swagger UI organization
        {"name": "Autenticación", "description": "Operaciones de registro y login."},
        {"name": "Usuarios", "description": "Operaciones relacionadas con usuarios."},
        {"name": "Health", "description": "Chequeo de salud del servicio."}
    ]
)

async def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(database.get_db)) -> models.User:
    credentials_exception = HTTPException(
        status_code=status.HTTP_401_UNAUTHORIZED,
        detail="Could not validate credentials",
        headers={"WWW-Authenticate": "Bearer"},
    )

    token_data = core.decode_access_token(token) # Uses the function from core.py
    if token_data is None or token_data.username is None:
        raise credentials_exception

    username: str = token_data.username

    user = crud.get_user_by_username(db, username=username)
    if user is None:
        raise credentials_exception
    # No check for user.is_active here, will be done in get_current_active_user
    return user

async def get_current_active_user(current_user: models.User = Depends(get_current_user)) -> models.User:
    if not current_user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")
    return current_user

@app.post("/auth/register", response_model=schemas.User, status_code=status.HTTP_201_CREATED, tags=["Autenticación"], summary="Registrar un nuevo usuario")
def register_user(user: schemas.UserCreate, db: Session = Depends(database.get_db)):
    db_user_by_email = crud.get_user_by_email(db, email=user.email)
    if db_user_by_email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Email already registered")
    db_user_by_username = crud.get_user_by_username(db, username=user.username)
    if db_user_by_username:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Username already taken")
    return crud.create_user(db=db, user=user)

@app.post("/auth/login", response_model=schemas.Token, tags=["Autenticación"], summary="Iniciar sesión para obtener un token JWT")
async def login_for_access_token(form_data: OAuth2PasswordRequestForm = Depends(), db: Session = Depends(database.get_db)):
    user = crud.get_user_by_username(db, username=form_data.username)
    if not user or not core.verify_password(form_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    if not user.is_active:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Inactive user")

    access_token_expires = timedelta(minutes=core.settings.ACCESS_TOKEN_EXPIRE_MINUTES) # Use core.settings
    access_token = core.create_access_token(
        data={"sub": user.username}, expires_delta=access_token_expires
    )
    return {"access_token": access_token, "token_type": "bearer"}

@app.get("/users/me", response_model=schemas.User, tags=["Usuarios"], summary="Obtener información del usuario actualmente autenticado")
async def read_users_me(current_user: models.User = Depends(get_current_active_user)):
    return current_user

@app.get("/health", summary="Chequeo de salud del servicio", tags=["Health"])
def health_check():
    return {"status": "ok", "message": "Auth Service is healthy"}

# Note: The prompt mentioned `Base.metadata.create_all(bind=engine)` in main.py.
# This is generally not recommended if Alembic is used for managing schema.
# It was commented out in the previous subtask's main.py, and remains so.
