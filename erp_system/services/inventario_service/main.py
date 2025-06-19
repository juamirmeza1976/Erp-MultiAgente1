from fastapi import FastAPI, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
import uuid

from . import crud, models, schemas, database

# models.Base.metadata.create_all(bind=database.engine) # Comentado si se usa Alembic

app = FastAPI(
    title="Servicio de Inventario",
    version="1.0.0",
    description="API para la gestión de inventario, incluyendo productos y stock.",
    openapi_tags=[ # Optional: Define tags for better Swagger UI organization
        {"name": "Productos", "description": "Operaciones con productos"},
        {"name": "Health", "description": "Chequeo de salud del servicio"}
    ]
)

# Dependencia para obtener la sesión de BD
# def get_db_session(): # Renombrado para evitar conflicto con database.get_db
#     db = database.SessionLocal()
#     try:
#         yield db
#     finally:
#         db.close()
# Using database.get_db directly now

@app.post("/productos/", response_model=schemas.Producto, status_code=status.HTTP_201_CREATED, summary="Crear un nuevo producto", tags=["Productos"])
def create_new_producto(producto: schemas.ProductoCreate, db: Session = Depends(database.get_db)):
    # Se podría añadir una verificación si el producto ya existe por nombre, por ejemplo:
    # existing_producto = db.query(models.Producto).filter(models.Producto.nombre == producto.nombre).first()
    # if existing_producto:
    #     raise HTTPException(status_code=status.HTTP_409_CONFLICT, detail="Ya existe un producto con este nombre")
    return crud.create_producto(db=db, producto=producto)

@app.get("/productos/", response_model=List[schemas.Producto], summary="Listar todos los productos", tags=["Productos"])
def read_all_productos(skip: int = 0, limit: int = 100, db: Session = Depends(database.get_db)):
    productos = crud.get_productos(db, skip=skip, limit=limit)
    return productos

@app.get("/productos/{producto_id}", response_model=schemas.Producto, summary="Obtener un producto por su ID", tags=["Productos"])
def read_single_producto(producto_id: uuid.UUID, db: Session = Depends(database.get_db)):
    db_producto = crud.get_producto(db, producto_id=producto_id)
    if db_producto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado")
    return db_producto

@app.put("/productos/{producto_id}", response_model=schemas.Producto, summary="Actualizar un producto existente", tags=["Productos"])
def update_existing_producto(producto_id: uuid.UUID, producto_update: schemas.ProductoCreate, db: Session = Depends(database.get_db)): # Changed 'producto' to 'producto_update' to match crud function
    db_producto = crud.update_producto(db, producto_id=producto_id, producto_update=producto_update)
    if db_producto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado para actualizar")
    return db_producto

@app.delete("/productos/{producto_id}", response_model=schemas.Producto, summary="Eliminar un producto", tags=["Productos"]) # O status_code 204 y sin response_model
def delete_single_producto(producto_id: uuid.UUID, db: Session = Depends(database.get_db)):
    db_producto = crud.delete_producto(db, producto_id=producto_id)
    if db_producto is None:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Producto no encontrado para eliminar")
    return db_producto # Devuelve el producto eliminado, o se puede cambiar a un mensaje o status 204

@app.get("/health", summary="Chequeo de salud del servicio", tags=["Health"])
def health_check():
    # Podríamos añadir un chequeo de conexión a BD aquí si es necesario
    # For example, try to execute a simple query:
    # try:
    #     db = database.SessionLocal()
    #     db.execute(text("SELECT 1"))
    #     db_status = "ok"
    # except Exception:
    #     db_status = "error"
    # finally:
    #     if 'db' in locals():
    #         db.close()
    return {"status": "ok", "database_url_loaded": database.settings.DATABASE_URL is not None}
