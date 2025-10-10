import pytest
from fastapi.testclient import TestClient
from main import app, tareas 

client = TestClient(app)

@pytest.fixture(autouse=True)
def limpiar_lista():
    tareas.clear()
    yield

def test_crear_tarea():
    response = client.post("/tareas", json={"descripcion": "Comprar leche", "estado": "pendiente"})
    assert response.status_code == 201
    data = response.json()
    assert data["descripcion"] == "Comprar leche"
    assert data["estado"] == "pendiente"
    assert "id" in data
    assert "fecha_creacion" in data

def test_crear_tarea_sin_descripcion():
    response = client.post("/tareas", json={"descripcion": "", "estado": "pendiente"})
    assert response.status_code == 422  # Validación de Pydantic

def test_listar_tareas():
    client.post("/tareas", json={"descripcion": "Tarea 1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "estado": "en_progreso"})
    response = client.get("/tareas")
    assert response.status_code == 200
    assert len(response.json()) == 2

def test_actualizar_tarea():
    res = client.post("/tareas", json={"descripcion": "Tarea a actualizar", "estado": "pendiente"})
    id_tarea = res.json()["id"]
    response = client.put(f"/tareas/{id_tarea}", json={"descripcion": "Actualizada", "estado": "completada"})
    assert response.status_code == 200
    data = response.json()
    assert data["descripcion"] == "Actualizada"
    assert data["estado"] == "completada"

def test_eliminar_tarea():
    res = client.post("/tareas", json={"descripcion": "Tarea a eliminar", "estado": "pendiente"})
    id_tarea = res.json()["id"]
    response = client.delete(f"/tareas/{id_tarea}")
    assert response.status_code == 204
    # Verificar que ya no exista
    response = client.get("/tareas")
    assert len(response.json()) == 0

def test_resumen_tareas():
    client.post("/tareas", json={"descripcion": "Tarea 1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "estado": "en_progreso"})
    client.post("/tareas", json={"descripcion": "Tarea 3", "estado": "completada"})
    response = client.get("/tareas/resumen")
    assert response.status_code == 200
    resumen = response.json()
    assert resumen["pendiente"] == 1
    assert resumen["en_progreso"] == 1
    assert resumen["completada"] == 1

def test_completar_todas():
    client.post("/tareas", json={"descripcion": "Tarea 1", "estado": "pendiente"})
    client.post("/tareas", json={"descripcion": "Tarea 2", "estado": "en_progreso"})
    response = client.put("/tareas/completar_todas", json={})
    assert response.status_code == 200
    assert response.json()["mensaje"] == "Todas las tareas fueron marcadas como completadas"
    todas = client.get("/tareas").json()
    assert all(t["estado"] == "completada" for t in todas)
