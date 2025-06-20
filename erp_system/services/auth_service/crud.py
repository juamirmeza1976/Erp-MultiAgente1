from sqlalchemy.orm import Session
from . import models, schemas, core # core para el hashing
import uuid

def get_user(db: Session, user_id: uuid.UUID) -> models.User | None:
    return db.query(models.User).filter(models.User.id == user_id).first()

def get_user_by_email(db: Session, email: str) -> models.User | None:
    return db.query(models.User).filter(models.User.email == email).first()

def get_user_by_username(db: Session, username: str) -> models.User | None:
    return db.query(models.User).filter(models.User.username == username).first()

def create_user(db: Session, user: schemas.UserCreate) -> models.User:
    hashed_password = core.get_password_hash(user.password)
    db_user = models.User(
        username=user.username,
        email=user.email,
        hashed_password=hashed_password,
        full_name=user.full_name,
        is_active=True # Por defecto, o se puede añadir un flujo de activación
    )
    db.add(db_user)
    db.commit()
    db.refresh(db_user)
    return db_user

# Funciones para actualizar y eliminar usuarios podrían añadirse aquí si es necesario
# def update_user(...):
#     ...
# def delete_user(...):
#     ...

# La función authenticate_user no se define aquí,
# ya que la lógica de autenticación (verificar usuario y contraseña)
# se manejará más cerca de los endpoints o en core.py,
# utilizando las funciones CRUD get_user_by_username y core.verify_password.
