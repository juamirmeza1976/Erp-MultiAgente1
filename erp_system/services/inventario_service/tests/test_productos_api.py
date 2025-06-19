from fastapi.testclient import TestClient
from sqlalchemy.orm import Session # For type hinting if using db_session directly
import uuid # For generating test UUIDs

# Schemas are not explicitly used here for validation but could be imported for more detailed checks
# from ..schemas import ProductoCreate, Producto

# Note: 'client' and 'db_session' fixtures are provided by conftest.py

def test_create_producto(client: TestClient):
    response = client.post(
        "/productos/",
        json={"nombre": "Test Producto 1", "descripcion": "Desc Test 1", "precio_costo": 10.0, "precio_venta": 20.0, "stock_actual": 100, "categoria": "Test Categoria"},
    )
    assert response.status_code == 201, response.text
    data = response.json()
    assert data["nombre"] == "Test Producto 1"
    assert "id" in data
    assert uuid.UUID(data["id"]) # Check if 'id' is a valid UUID

def test_read_productos_empty(client: TestClient):
    # Test reading products when database is empty (due to transaction rollbacks)
    response = client.get("/productos/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 0

def test_read_productos_with_data(client: TestClient):
    # Create a product first
    product_data = {"nombre": "Test Producto List", "precio_costo": 5.0, "precio_venta": 10.0, "stock_actual": 50}
    create_response = client.post("/productos/", json=product_data)
    assert create_response.status_code == 201, create_response.text

    response = client.get("/productos/")
    assert response.status_code == 200, response.text
    data = response.json()
    assert isinstance(data, list)
    assert len(data) == 1
    assert data[0]["nombre"] == product_data["nombre"]

def test_read_single_producto(client: TestClient):
    product_data = {"nombre": "Test Producto Single", "precio_costo": 15.0, "precio_venta": 25.0, "stock_actual": 10}
    create_response = client.post("/productos/", json=product_data)
    assert create_response.status_code == 201, create_response.text
    producto_id = create_response.json()["id"]

    response = client.get(f"/productos/{producto_id}")
    assert response.status_code == 200, response.text
    data = response.json()
    assert data["nombre"] == product_data["nombre"]
    assert data["id"] == producto_id

def test_read_single_producto_not_found(client: TestClient):
    non_existent_id = str(uuid.uuid4())
    response = client.get(f"/productos/{non_existent_id}")
    assert response.status_code == 404, response.text

def test_update_producto(client: TestClient):
    product_data = {"nombre": "Producto Original", "precio_costo": 20.0, "precio_venta": 30.0, "stock_actual": 20}
    create_response = client.post("/productos/", json=product_data)
    assert create_response.status_code == 201, create_response.text
    producto_id = create_response.json()["id"]

    update_payload = {"nombre": "Producto Actualizado", "descripcion": "Actualizado", "precio_costo": 22.0, "precio_venta": 32.0, "stock_actual": 25, "categoria": "Actualizada"}
    update_response = client.put(f"/productos/{producto_id}", json=update_payload)
    assert update_response.status_code == 200, update_response.text
    data = update_response.json()
    assert data["nombre"] == "Producto Actualizado"
    assert data["precio_costo"] == 22.0
    assert data["id"] == producto_id

def test_update_producto_not_found(client: TestClient):
    non_existent_id = str(uuid.uuid4())
    response = client.put(
        f"/productos/{non_existent_id}",
        json={"nombre": "Intento Fallido", "precio_costo": 1.0, "precio_venta": 2.0},
    )
    assert response.status_code == 404, response.text

def test_delete_producto(client: TestClient):
    product_data = {"nombre": "Producto a Eliminar", "precio_costo": 5.0, "precio_venta": 8.0, "stock_actual": 5}
    create_response = client.post("/productos/", json=product_data)
    assert create_response.status_code == 201, create_response.text
    producto_id = create_response.json()["id"]

    delete_response = client.delete(f"/productos/{producto_id}")
    assert delete_response.status_code == 200, delete_response.text # Endpoint returns deleted item

    # Verify that the product no longer exists
    get_response = client.get(f"/productos/{producto_id}")
    assert get_response.status_code == 404, get_response.text

def test_delete_producto_not_found(client: TestClient):
    non_existent_id = str(uuid.uuid4())
    response = client.delete(f"/productos/{non_existent_id}")
    assert response.status_code == 404, response.text
