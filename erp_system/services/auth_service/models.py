from sqlalchemy import Column, String, Boolean, text, TIMESTAMP # Added TIMESTAMP and text for commented-out fields
from sqlalchemy.dialects.postgresql import UUID
import uuid
from .database import Base # Relative import

class User(Base):
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, index=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    full_name = Column(String, nullable=True)
    is_active = Column(Boolean, default=True)
    # Podríamos añadir una columna para superuser o roles más adelante
    # created_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"))
    # updated_at = Column(TIMESTAMP(timezone=True), nullable=False, server_default=text("now()"), onupdate=text("now()"))
