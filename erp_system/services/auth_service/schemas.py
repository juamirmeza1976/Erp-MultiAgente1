from pydantic import BaseModel, EmailStr, Field
from typing import Optional, List # Added List for future roles
import uuid

class UserBase(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=50)
    full_name: Optional[str] = None

class UserCreate(UserBase):
    password: str = Field(..., min_length=6)

class User(UserBase):
    id: uuid.UUID
    is_active: bool = True
    # roles: List[str] = [] # Para futura implementación

    class Config:
        from_attributes = True # Pydantic V2

class Token(BaseModel):
    access_token: str
    token_type: str

class TokenData(BaseModel): # Para decodificar el contenido del token
    username: Optional[str] = None
    # Podríamos añadir 'scopes' o 'user_id' aquí si es necesario

class LoginRequest(BaseModel):
    username: str # O EmailStr si se prefiere login con email
    password: str
