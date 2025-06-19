from pydantic import BaseModel
from typing import Optional
import uuid

class ProductoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    precio_costo: float
    precio_venta: float
    stock_actual: int = 0
    categoria: Optional[str] = None

class ProductoCreate(ProductoBase):
    pass

class Producto(ProductoBase):
    id: uuid.UUID

    class Config:
        # orm_mode = True # Deprecated in Pydantic V2
        from_attributes = True # For Pydantic V2
