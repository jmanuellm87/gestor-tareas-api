# Tests para los endpoints REST de tareas

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

# Motor SQLite en memoria para aislar los tests de la BD de producción
engine = create_engine(
    "sqlite://",
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def override_get_db():
    db = TestingSessionLocal()
    try:
        yield db
    finally:
        db.close()


app.dependency_overrides[get_db] = override_get_db


@pytest.fixture(autouse=True)
def setup_db():
    """Crea las tablas antes de cada test y las elimina al terminar."""
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


@pytest.fixture()
def client():
    """Cliente HTTP de prueba para interactuar con la API."""
    return TestClient(app)


# ---- Tests para GET /tasks/status/{status} ----


def test_list_tasks_by_status_returns_matching_tasks(client):
    """Caso feliz: devuelve solo las tareas con el estado solicitado."""
    client.post("/tasks/", json={"title": "Tarea pendiente"})
    client.post("/tasks/", json={"title": "Tarea en progreso", "status": "in_progress"})
    client.post("/tasks/", json={"title": "Tarea completada", "status": "done"})

    response = client.get("/tasks/status/pending")
    assert response.status_code == 200
    data = response.json()
    assert len(data) == 1
    assert data[0]["title"] == "Tarea pendiente"
    assert data[0]["status"] == "pending"


def test_list_tasks_by_status_returns_empty_when_no_match(client):
    """Devuelve lista vacía cuando no existen tareas con ese estado."""
    client.post("/tasks/", json={"title": "Tarea pendiente"})

    response = client.get("/tasks/status/done")
    assert response.status_code == 200
    assert response.json() == []


def test_list_tasks_by_status_invalid_status(client):
    """Caso de error: devuelve 422 cuando el estado no es válido."""
    response = client.get("/tasks/status/invalid_status")
    assert response.status_code == 422
    body = response.json()
    assert "detail" in body
