from sqlalchemy.orm import Session
# from sqlalchemy.dialects.postgresql import UUID # Not strictly needed here for comparisons if using Python uuid
from . import models, schemas
import uuid

def get_producto(db: Session, producto_id: uuid.UUID) -> models.Producto | None:
    return db.query(models.Producto).filter(models.Producto.id == producto_id).first()

def get_productos(db: Session, skip: int = 0, limit: int = 100) -> list[models.Producto]:
    return db.query(models.Producto).offset(skip).limit(limit).all()

def create_producto(db: Session, producto: schemas.ProductoCreate) -> models.Producto:
    db_producto = models.Producto(
        # id se genera automáticamente por defecto en el modelo SQLAlchemy (default=uuid.uuid4)
        nombre=producto.nombre,
        descripcion=producto.descripcion,
        precio_costo=producto.precio_costo,
        precio_venta=producto.precio_venta,
        stock_actual=producto.stock_actual,
        categoria=producto.categoria
    )
    db.add(db_producto)
    db.commit()
    db.refresh(db_producto)
    return db_producto

def update_producto(db: Session, producto_id: uuid.UUID, producto_update: schemas.ProductoCreate) -> models.Producto | None:
    db_producto = get_producto(db, producto_id)
    if db_producto:
        update_data = producto_update.model_dump(exclude_unset=True) # Pydantic v2
        for key, value in update_data.items():
            setattr(db_producto, key, value)
        db.commit()
        db.refresh(db_producto)
    return db_producto

def delete_producto(db: Session, producto_id: uuid.UUID) -> models.Producto | None:
    db_producto = get_producto(db, producto_id)
    if db_producto:
        db.delete(db_producto)
        db.commit()
    return db_producto
