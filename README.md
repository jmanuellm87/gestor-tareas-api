# API de Gestión de Tareas

API REST para gestionar tareas construida con **FastAPI** y **SQLAlchemy**. Permite crear, consultar, actualizar y eliminar tareas. Cada tarea cuenta con un identificador único, título, descripción opcional, estado (`pending`, `in_progress`, `done`) y fecha de creación automática.

---

## Requisitos previos

| Requisito | Versión mínima |
|---|---|
| Python | 3.12+ |

### Dependencias de producción

| Paquete | Versión |
|---|---|
| FastAPI | 0.136.1 |
| SQLAlchemy | 2.0.49 |
| Pydantic | 2.13.4 |
| Uvicorn | 0.46.0 |

### Dependencias de desarrollo y tests

| Paquete | Versión |
|---|---|
| pytest | 9.0.3 |
| httpx | 0.28.1 |
| anyio | 4.13.0 |

---

## Instalación

1. Clonar el repositorio:

   ```bash
   git clone https://github.com/jmanuellm87/gestor-tareas-api.git
   cd gestor-tareas-api
   ```

2. Crear y activar un entorno virtual:

   ```bash
   python -m venv venv
   source venv/bin/activate        # macOS / Linux
   # venv\Scripts\activate          # Windows
   ```

3. Instalar las dependencias:

   ```bash
   pip install -r requirements.txt
   ```

---

## Arrancar la aplicación

```bash
uvicorn aplicacion.principal:app --reload
```

La API quedará disponible en `http://127.0.0.1:8000`.
La documentación interactiva (Swagger UI) se encuentra en `http://127.0.0.1:8000/docs`.

---

## Endpoints

Todos los endpoints están bajo el prefijo `/tasks`.

### 1. Listar tareas

| | |
|---|---|
| **Método** | `GET` |
| **Ruta** | `/tasks/` |
| **Parámetros** | Ninguno |

**Ejemplo de request:**

```bash
curl http://127.0.0.1:8000/tasks/
```

**Ejemplo de response** (`200 OK`):

```json
[
  {
    "id": 1,
    "title": "Revisar documentación",
    "description": "Actualizar el README del proyecto",
    "status": "pending",
    "created_at": "2025-05-28T10:00:00"
  }
]
```

---

### 2. Obtener una tarea por id

| | |
|---|---|
| **Método** | `GET` |
| **Ruta** | `/tasks/{task_id}` |
| **Parámetros de ruta** | `task_id` (int) — Identificador de la tarea |

**Ejemplo de request:**

```bash
curl http://127.0.0.1:8000/tasks/1
```

**Ejemplo de response** (`200 OK`):

```json
{
  "id": 1,
  "title": "Revisar documentación",
  "description": "Actualizar el README del proyecto",
  "status": "pending",
  "created_at": "2025-05-28T10:00:00"
}
```

**Response de error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

### 3. Crear una tarea

| | |
|---|---|
| **Método** | `POST` |
| **Ruta** | `/tasks/` |
| **Cuerpo (JSON)** | `title` (str, obligatorio), `description` (str, opcional), `status` (str, opcional — por defecto `"pending"`) |

Valores válidos para `status`: `"pending"`, `"in_progress"`, `"done"`.

**Ejemplo de request:**

```bash
curl -X POST http://127.0.0.1:8000/tasks/ \
  -H "Content-Type: application/json" \
  -d '{"title": "Nueva tarea", "description": "Descripción de ejemplo", "status": "pending"}'
```

**Ejemplo de response** (`201 Created`):

```json
{
  "id": 2,
  "title": "Nueva tarea",
  "description": "Descripción de ejemplo",
  "status": "pending",
  "created_at": "2025-05-28T10:05:00"
}
```

---

### 4. Actualizar parcialmente una tarea

| | |
|---|---|
| **Método** | `PATCH` |
| **Ruta** | `/tasks/{task_id}` |
| **Parámetros de ruta** | `task_id` (int) — Identificador de la tarea |
| **Cuerpo (JSON)** | `title` (str, opcional), `description` (str, opcional), `status` (str, opcional) |

Solo se modifican los campos incluidos en el cuerpo de la petición.

**Ejemplo de request:**

```bash
curl -X PATCH http://127.0.0.1:8000/tasks/1 \
  -H "Content-Type: application/json" \
  -d '{"status": "done"}'
```

**Ejemplo de response** (`200 OK`):

```json
{
  "id": 1,
  "title": "Revisar documentación",
  "description": "Actualizar el README del proyecto",
  "status": "done",
  "created_at": "2025-05-28T10:00:00"
}
```

**Response de error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

### 5. Eliminar todas las tareas

| | |
|---|---|
| **Método** | `DELETE` |
| **Ruta** | `/tasks/` |
| **Parámetros** | Ninguno |

**Ejemplo de request:**

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/
```

**Response exitosa:** `204 No Content` (sin cuerpo).

---

### 6. Eliminar una tarea

| | |
|---|---|
| **Método** | `DELETE` |
| **Ruta** | `/tasks/{task_id}` |
| **Parámetros de ruta** | `task_id` (int) — Identificador de la tarea |

**Ejemplo de request:**

```bash
curl -X DELETE http://127.0.0.1:8000/tasks/1
```

**Response exitosa:** `204 No Content` (sin cuerpo).

**Response de error** (`404 Not Found`):

```json
{
  "detail": "Task not found"
}
```

---

## Ejecutar los tests

```bash
pytest tests/ -v
```

Los tests utilizan una base de datos SQLite en memoria con `StaticPool` para garantizar aislamiento entre casos. No afectan al archivo `tareas.db` de producción.

---

## Estructura del proyecto

```
gestor-tareas-api/
├── aplicacion/                # Paquete principal con toda la lógica de la aplicación
│   ├── __init__.py
│   ├── principal.py           # Punto de entrada: instancia de FastAPI y registro de routers
│   ├── base_de_datos.py       # Configuración del engine y sesión de SQLAlchemy
│   ├── modelos.py             # Modelos ORM (tabla tasks, enum TaskStatus)
│   ├── esquemas.py            # Esquemas Pydantic de entrada y respuesta
│   └── rutas/                 # Definición de los endpoints REST
│       ├── __init__.py
│       └── tareas.py          # Endpoints CRUD de tareas
├── tests/                     # Suite de tests automatizados
│   └── test_tasks.py          # Tests con pytest y SQLite en memoria
├── requirements.txt           # Dependencias del proyecto
├── AGENTS.md                  # Instrucciones y convenciones para Devin
├── .gitignore
└── README.md
```
