import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from aplicacion.base_de_datos import Base, get_db
from aplicacion.principal import app

SQLALCHEMY_DATABASE_URL = "sqlite:///./test_tareas.db"

engine = create_engine(
    SQLALCHEMY_DATABASE_URL, connect_args={"check_same_thread": False}
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
    Base.metadata.create_all(bind=engine)
    yield
    Base.metadata.drop_all(bind=engine)


client = TestClient(app)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------
def create_sample_task(**overrides):
    payload = {"title": "Tarea de prueba", **overrides}
    return client.post("/tasks/", json=payload)


# ===========================================================================
# GET /tasks/ - list
# ===========================================================================
class TestListTasks:
    def test_empty_list(self):
        resp = client.get("/tasks/")
        assert resp.status_code == 200
        assert resp.json() == []

    def test_multiple_tasks(self):
        create_sample_task(title="Tarea A")
        create_sample_task(title="Tarea B")
        resp = client.get("/tasks/")
        assert resp.status_code == 200
        assert len(resp.json()) == 2


# ===========================================================================
# GET /tasks/{task_id} - detail
# ===========================================================================
class TestGetTask:
    def test_not_found(self):
        resp = client.get("/tasks/9999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Tarea no encontrada"

    def test_not_found_zero_id(self):
        resp = client.get("/tasks/0")
        assert resp.status_code == 404

    def test_not_found_negative_id(self):
        resp = client.get("/tasks/-1")
        assert resp.status_code == 404

    def test_invalid_id_type(self):
        resp = client.get("/tasks/abc")
        assert resp.status_code == 422

    def test_existing_task(self):
        created = create_sample_task().json()
        resp = client.get(f"/tasks/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["id"] == created["id"]


# ===========================================================================
# POST /tasks/ - create
# ===========================================================================
class TestCreateTask:
    def test_missing_title(self):
        resp = client.post("/tasks/", json={})
        assert resp.status_code == 422

    def test_null_title(self):
        resp = client.post("/tasks/", json={"title": None})
        assert resp.status_code == 422

    def test_invalid_status(self):
        resp = client.post("/tasks/", json={"title": "X", "status": "invalid"})
        assert resp.status_code == 422

    def test_empty_body(self):
        resp = client.post("/tasks/")
        assert resp.status_code == 422

    def test_defaults(self):
        resp = create_sample_task()
        assert resp.status_code == 201
        body = resp.json()
        assert body["status"] == "pending"
        assert body["priority"] == "medium"
        assert body["description"] is None
        assert body["categoria"] is None
        assert "id" in body
        assert "created_at" in body

    def test_with_all_fields(self):
        resp = create_sample_task(
            title="Completa",
            description="Desc",
            categoria="Trabajo",
            status="in_progress",
            priority="high",
        )
        assert resp.status_code == 201
        body = resp.json()
        assert body["title"] == "Completa"
        assert body["description"] == "Desc"
        assert body["categoria"] == "Trabajo"
        assert body["status"] == "in_progress"
        assert body["priority"] == "high"

    def test_with_categoria(self):
        resp = create_sample_task(categoria="Personal")
        assert resp.status_code == 201
        body = resp.json()
        assert body["categoria"] == "Personal"

    def test_with_status_done(self):
        resp = create_sample_task(status="done")
        assert resp.status_code == 201
        assert resp.json()["status"] == "done"

    def test_extra_fields_ignored(self):
        resp = client.post(
            "/tasks/", json={"title": "Tarea", "unknown_field": "val"}
        )
        assert resp.status_code == 201
        assert "unknown_field" not in resp.json()


# ===========================================================================
# PATCH /tasks/{task_id} - update
# ===========================================================================
class TestUpdateTask:
    def test_not_found(self):
        resp = client.patch("/tasks/9999", json={"title": "Nueva"})
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Tarea no encontrada"

    def test_invalid_status(self):
        created = create_sample_task().json()
        resp = client.patch(
            f"/tasks/{created['id']}", json={"status": "bogus"}
        )
        assert resp.status_code == 422

    def test_empty_body_no_change(self):
        created = create_sample_task(title="Original").json()
        resp = client.patch(f"/tasks/{created['id']}", json={})
        assert resp.status_code == 200
        assert resp.json()["title"] == "Original"

    def test_partial_update_title(self):
        created = create_sample_task(title="Old").json()
        resp = client.patch(
            f"/tasks/{created['id']}", json={"title": "New"}
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "New"
        assert resp.json()["status"] == "pending"

    def test_partial_update_status(self):
        created = create_sample_task().json()
        resp = client.patch(
            f"/tasks/{created['id']}", json={"status": "done"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"

    def test_partial_update_description(self):
        created = create_sample_task().json()
        resp = client.patch(
            f"/tasks/{created['id']}", json={"description": "Added"}
        )
        assert resp.status_code == 200
        assert resp.json()["description"] == "Added"

    def test_update_all_fields(self):
        created = create_sample_task().json()
        resp = client.patch(
            f"/tasks/{created['id']}",
            json={
                "title": "Nuevo",
                "description": "Desc nueva",
                "status": "in_progress",
                "priority": "high",
            },
        )
        assert resp.status_code == 200
        body = resp.json()
        assert body["title"] == "Nuevo"
        assert body["description"] == "Desc nueva"
        assert body["status"] == "in_progress"
        assert body["priority"] == "high"

    def test_null_description_clears(self):
        created = create_sample_task(description="Has desc").json()
        resp = client.patch(
            f"/tasks/{created['id']}", json={"description": None}
        )
        assert resp.status_code == 200
        assert resp.json()["description"] is None


# ===========================================================================
# DELETE /tasks/{task_id} - delete
# ===========================================================================
class TestDeleteTask:
    def test_not_found(self):
        resp = client.delete("/tasks/9999")
        assert resp.status_code == 404
        assert resp.json()["detail"] == "Tarea no encontrada"

    def test_delete_existing(self):
        created = create_sample_task().json()
        resp = client.delete(f"/tasks/{created['id']}")
        assert resp.status_code == 204
        assert resp.content == b""

    def test_delete_twice(self):
        created = create_sample_task().json()
        client.delete(f"/tasks/{created['id']}")
        resp = client.delete(f"/tasks/{created['id']}")
        assert resp.status_code == 404

    def test_deleted_not_in_list(self):
        created = create_sample_task().json()
        client.delete(f"/tasks/{created['id']}")
        resp = client.get("/tasks/")
        assert resp.status_code == 200
        ids = [t["id"] for t in resp.json()]
        assert created["id"] not in ids


# ===========================================================================
# DELETE /tasks/ - delete all
# ===========================================================================
class TestDeleteAllTasks:
    def test_delete_all(self):
        create_sample_task(title="A")
        create_sample_task(title="B")
        create_sample_task(title="C")
        resp = client.delete("/tasks/")
        assert resp.status_code == 204
        assert resp.content == b""
        listing = client.get("/tasks/")
        assert listing.status_code == 200
        assert listing.json() == []

    def test_delete_all_empty_db(self):
        resp = client.delete("/tasks/")
        assert resp.status_code == 204
        assert resp.content == b""
        listing = client.get("/tasks/")
        assert listing.status_code == 200
        assert listing.json() == []


# ===========================================================================
# get_db dependency
# ===========================================================================
class TestGetDbDependency:
    def test_yields_and_closes(self):
        gen = get_db()
        db = next(gen)
        assert db is not None
        gen.close()


# ===========================================================================
# Priority field (prioridad)
# ===========================================================================
class TestPriority:
    def test_create_default_priority(self):
        resp = create_sample_task()
        assert resp.status_code == 201
        assert resp.json()["priority"] == "medium"

    def test_create_with_low_priority(self):
        resp = create_sample_task(priority="low")
        assert resp.status_code == 201
        assert resp.json()["priority"] == "low"

    def test_create_with_high_priority(self):
        resp = create_sample_task(priority="high")
        assert resp.status_code == 201
        assert resp.json()["priority"] == "high"

    def test_create_invalid_priority(self):
        resp = client.post(
            "/tasks/", json={"title": "X", "priority": "urgent"}
        )
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_patch_priority(self):
        created = create_sample_task().json()
        resp = client.patch(
            f"/tasks/{created['id']}", json={"priority": "high"}
        )
        assert resp.status_code == 200
        assert resp.json()["priority"] == "high"

    def test_patch_invalid_priority(self):
        created = create_sample_task().json()
        resp = client.patch(
            f"/tasks/{created['id']}", json={"priority": "urgent"}
        )
        assert resp.status_code == 422
        assert "detail" in resp.json()

    def test_priority_in_list(self):
        create_sample_task(priority="low")
        create_sample_task(priority="high")
        resp = client.get("/tasks/")
        assert resp.status_code == 200
        priorities = [t["priority"] for t in resp.json()]
        assert "low" in priorities
        assert "high" in priorities

    def test_priority_in_detail(self):
        created = create_sample_task(priority="low").json()
        resp = client.get(f"/tasks/{created['id']}")
        assert resp.status_code == 200
        assert resp.json()["priority"] == "low"


# ===========================================================================
# Schema validation (esquemas.py)
# ===========================================================================
class TestSchemas:
    def test_task_create_defaults(self):
        from aplicacion.esquemas import TaskCreate

        tc = TaskCreate(title="T")
        assert tc.status.value == "pending"
        assert tc.priority.value == "medium"
        assert tc.description is None
        assert tc.categoria is None

    def test_task_update_all_none(self):
        from aplicacion.esquemas import TaskUpdate

        tu = TaskUpdate()
        assert tu.title is None
        assert tu.description is None
        assert tu.categoria is None
        assert tu.status is None
        assert tu.priority is None

    def test_task_response_from_orm(self):
        from datetime import datetime, timezone

        from aplicacion.esquemas import TaskResponse

        now = datetime.now(timezone.utc)
        tr = TaskResponse(
            id=1,
            title="T",
            description=None,
            categoria="Trabajo",
            status="pending",
            priority="medium",
            created_at=now,
        )
        assert tr.id == 1
        assert tr.categoria == "Trabajo"
        assert tr.priority.value == "medium"


# ===========================================================================
# Model (modelos.py)
# ===========================================================================
class TestModels:
    def test_task_status_values(self):
        from aplicacion.modelos import TaskStatus

        assert TaskStatus.pending.value == "pending"
        assert TaskStatus.in_progress.value == "in_progress"
        assert TaskStatus.done.value == "done"
        assert len(TaskStatus) == 3

    def test_task_priority_values(self):
        from aplicacion.modelos import TaskPriority

        assert TaskPriority.low.value == "low"
        assert TaskPriority.medium.value == "medium"
        assert TaskPriority.high.value == "high"
        assert len(TaskPriority) == 3

    def test_task_table_name(self):
        from aplicacion.modelos import Task

        assert Task.__tablename__ == "tasks"


# ===========================================================================
# Regresión: validación de longitud mínima del título en POST /tasks/
# ===========================================================================
class TestCreateTaskTitleValidation:
    def test_title_empty_string(self):
        resp = client.post("/tasks/", json={"title": ""})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "El título debe tener al menos 3 caracteres"

    def test_title_one_char(self):
        resp = client.post("/tasks/", json={"title": "A"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "El título debe tener al menos 3 caracteres"

    def test_title_two_chars(self):
        resp = client.post("/tasks/", json={"title": "AB"})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "El título debe tener al menos 3 caracteres"

    def test_title_only_spaces(self):
        resp = client.post("/tasks/", json={"title": "   "})
        assert resp.status_code == 400
        assert resp.json()["detail"] == "El título debe tener al menos 3 caracteres"

    def test_title_three_chars_valid(self):
        resp = client.post("/tasks/", json={"title": "ABC"})
        assert resp.status_code == 201
        assert resp.json()["title"] == "ABC"


# ===========================================================================
# Regresión: no se puede modificar una tarea ya completada (PATCH /tasks/{id})
# ===========================================================================
class TestUpdateCompletedTask:
    def test_cannot_update_done_task_title(self):
        created = create_sample_task(status="done").json()
        resp = client.patch(
            f"/tasks/{created['id']}", json={"title": "Nuevo título"}
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "No se puede modificar una tarea ya completada"

    def test_cannot_update_done_task_status(self):
        created = create_sample_task(status="done").json()
        resp = client.patch(
            f"/tasks/{created['id']}", json={"status": "pending"}
        )
        assert resp.status_code == 400
        assert resp.json()["detail"] == "No se puede modificar una tarea ya completada"

    def test_can_update_pending_task(self):
        created = create_sample_task(status="pending").json()
        resp = client.patch(
            f"/tasks/{created['id']}", json={"title": "Actualizado"}
        )
        assert resp.status_code == 200
        assert resp.json()["title"] == "Actualizado"

    def test_can_transition_to_done(self):
        created = create_sample_task(status="in_progress").json()
        resp = client.patch(
            f"/tasks/{created['id']}", json={"status": "done"}
        )
        assert resp.status_code == 200
        assert resp.json()["status"] == "done"
