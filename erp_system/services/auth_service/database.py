from sqlalchemy import create_engine
from sqlalchemy.ext.declarative import declarative_base # Corrected: This is still how Base is often created, or sqlalchemy.orm.declarative_base
from sqlalchemy.orm import sessionmaker
from pydantic_settings import BaseSettings, SettingsConfigDict

class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql://user:password@localhost/erp_auth" # BD específica para Auth
    # JWT settings
    SECRET_KEY: str = "a_very_secret_key_that_should_be_in_env" # CAMBIAR ESTO Y PONERLO EN .ENV
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30

    model_config = SettingsConfigDict(env_file=".env", extra='ignore')


settings = Settings()
SQLALCHEMY_DATABASE_URL = settings.DATABASE_URL

engine = create_engine(SQLALCHEMY_DATABASE_URL)
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Using sqlalchemy.orm.declarative_base for modern SQLAlchemy if preferred,
# but sqlalchemy.ext.declarative.declarative_base is common and works.
# For consistency with the prompt, keeping declarative_base from ext.
Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
