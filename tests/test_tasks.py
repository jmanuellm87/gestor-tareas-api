# Tests para los endpoints REST de tareas

import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

SQLALCHEMY_DATABASE_URL = "sqlite://"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL,
    connect_args={"check_same_thread": False},
    poolclass=StaticPool,
)
TestingSessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


@pytest.fixture()
def client():
    Base.metadata.create_all(bind=engine)

    def override_get_db():
        db = TestingSessionLocal()
        try:
            yield db
        finally:
            db.close()

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
    Base.metadata.drop_all(bind=engine)


def test_patch_done_task_returns_400(client):
    """Un PATCH sobre una tarea con estado done debe devolver 400."""
    response = client.post("/tasks/", json={"title": "Tarea de prueba", "status": "done"})
    assert response.status_code == 201
    task_id = response.json()["id"]

    response = client.patch(f"/tasks/{task_id}", json={"title": "Nuevo título"})
    assert response.status_code == 400
    assert response.json()["detail"] == "Cannot update a task that is already done"
