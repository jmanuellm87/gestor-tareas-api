# Contexto del curso — para retomar el trabajo en una sesión nueva de Claude Code

Este archivo contiene todo lo necesario para que una sesión de Claude Code sin contexto previo pueda continuar el trabajo exactamente donde se dejó. Léelo completo antes de hacer cualquier cambio.

---

## 1. Datos del curso

| Campo | Valor |
|---|---|
| Nombre | Curso de Devin AI para Softtek |
| Cliente | Softtek |
| Audiencia | Desarrolladores de distintos lenguajes y seniorities |
| Formato | Virtual |
| Plataforma | Cisco WebEx (credenciales en poder del formador, no incluir en este archivo) |
| Número de sesiones | 8 |
| Duración por sesión | 3 horas (incluyendo 20 min de descanso) |
| Horario | 15:30 – 18:30 |
| Idioma | Castellano (código en inglés, todo lo demás en castellano) |
| Cuenta Devin | versión gratuita de devin.ai, cada alumno con su propia cuenta |

---

## 2. Repositorio de práctica

**Nombre en GitHub:** `gestor-tareas-api`
**URL remota:** `https://github.com/jmojpar/gestor-tareas-api.git`
**Directorio local:** el nombre puede variar según el ordenador. Usar siempre la URL remota como referencia.
**Rama principal:** `main`

### Stack del proyecto

API REST de gestión de tareas en Python, construida exclusivamente como material de prácticas del curso. No es un proyecto de producción.

| Capa | Tecnología | Versión |
|---|---|---|
| Framework web | FastAPI | 0.136.1 |
| ORM | SQLAlchemy | 2.0.49 |
| Validación | Pydantic | 2.13.4 |
| Base de datos | SQLite (`tareas.db`) | — |
| Servidor | Uvicorn | 0.46.0 |
| Tests | pytest + httpx | 9.0.3 / 0.28.1 |
| Python | 3.14.5 | — |

### Estructura de archivos en `main`

```
gestor-tareas-api/
├── aplicacion/
│   ├── __init__.py
│   ├── principal.py        # FastAPI app, lifespan con create_all
│   ├── base_de_datos.py    # engine, SessionLocal, Base, get_db
│   ├── modelos.py          # Task (ORM) + TaskStatus (enum)
│   ├── esquemas.py         # TaskCreate, TaskUpdate, TaskResponse
│   └── rutas/
│       ├── __init__.py
│       └── tareas.py       # 5 endpoints REST (CRUD completo)
├── tests/
│   ├── __init__.py
│   └── test_tasks.py       # vacío en main; contenido en escenario-2
├── guias/
│   ├── contexto-curso.md   # este archivo
│   └── sesion-01-introduccion.md
├── .devin/
│   └── instructions.md     # instrucciones para Devin en castellano
├── .gitignore              # __pycache__, *.pyc, *.db, .claude/, venv/
├── requirements.txt        # dependencias con versiones fijas
└── README.md               # vacío intencionalmente — parte del escenario 4, no modificar
```

### Convenciones de código del proyecto

- **Código** (variables, funciones, clases, rutas URL): en **inglés**
- **Comentarios y documentación**: en **castellano**
- **Nombres de archivos y carpetas**: en **castellano** (`modelos.py`, `esquemas.py`, `rutas/`)
- Commits en formato `tipo: descripción breve` (feat, fix, refactor, docs, pruebas)
- PEP 8; máx. 100 caracteres por línea
- Importaciones: stdlib → third-party → proyecto, separadas por línea en blanco

---

## 3. Los 5 escenarios — ramas y PRs

Cada escenario es una rama ya pusheada a origin con un PR abierto contra `main`. Representan situaciones reales de código deficiente que los alumnos usan para practicar con Devin.

| PR | Rama | Commit message | Defecto introducido |
|---|---|---|---|
| #1 | `escenario-1-bug-logico` | `bug: validaciones de negocio ausentes en tareas` | (1) `create_task` no valida longitud mínima del título (< 3 chars). (2) `update_task` comprueba `payload.status == TaskStatus.done` en lugar de `task.status == TaskStatus.done`, permitiendo modificar tareas ya completadas. |
| #2 | `escenario-2-sin-tests` | `pruebas: tests incompletos, faltan casos de error` | `tests/test_tasks.py` con pytest cubre solo happy path (crear tarea, listar tareas). Faltan tests de 404, 422, y 400 por tarea completada. Los casos faltantes están comentados con `# TODO`. |
| #3 | `escenario-3-codigo-duplicado` | `refactor: lógica de búsqueda duplicada en múltiples endpoints` | El bloque de búsqueda por id + 404 (3 líneas + comentario) se repite literal en `get_task`, `update_task` y `delete_task`. Debería extraerse a una función `get_task_or_404`. |
| #4 | `escenario-4-sin-documentacion` | `docs: eliminada toda la documentación del proyecto` | Todos los comentarios eliminados de los 5 archivos Python. `README.md` vacío. El código funciona pero es opaco. |
| #5 | `escenario-5-endpoint-roto` | `feat: parámetros de filtrado y paginación con lógica incorrecta` | `list_tasks` acepta `?status=` y `?limit=` sin error pero: (1) filtra con `!=` en lugar de `==` (devuelve tareas con el estado contrario al solicitado); (2) `limit` se parsea pero nunca se aplica a la query. |

### Detalles de cada escenario para el formador

**Escenario 1 — código afectado (`escenario-1-bug-logico`):**
```python
# create_task: sin validación de longitud
def create_task(payload: TaskCreate, db: Session = Depends(get_db)):
    task = Task(**payload.model_dump())  # acepta título de 1 carácter

# update_task: comprueba payload en lugar de task
if payload.status == TaskStatus.done:   # bug: debería ser task.status
    raise HTTPException(status_code=400, ...)
```

**Escenario 3 — bloque duplicado (`escenario-3-codigo-duplicado`):**
```python
# Aparece idéntico en get_task, update_task y delete_task:
# Buscar tarea por id y devolver 404 si no existe
if task_id <= 0:
    raise HTTPException(status_code=400, detail="Invalid task id")
task = db.query(Task).filter(Task.id == task_id).first()
if task is None:
    raise HTTPException(status_code=404, detail="Task not found")
```

**Escenario 5 — bugs en list_tasks (`escenario-5-endpoint-roto`):**
```python
@router.get("/", response_model=List[TaskResponse])
def list_tasks(
    db: Session = Depends(get_db),
    status: Optional[TaskStatus] = Query(default=None),
    limit: int = Query(default=10, ge=1),
):
    query = db.query(Task)
    if status:
        query = query.filter(Task.status != status)  # bug: != en vez de ==
    return query.all()                               # bug: limit ignorado
```

---

## 4. Tabla de las 8 sesiones

Cada sesión dura 3 horas (15:30–18:30) e incluye 20 min de descanso. Los bloques B1–B10 son las unidades de contenido teórico del curso. El escenario de práctica indicado es orientativo — las actividades concretas y su número se definen al crear cada guía.

| Sesión | Bloques | Contenido principal | Escenario orientativo |
|---|---|---|---|
| 01 | B1 + B2 | B1: Qué es Devin, copilot vs agente autónomo, capacidades, limitaciones, casos reales (Gumroad, Goldman Sachs, Visma). B2: Arquitectura interna, ciclo plan→ejecuta→verifica, herramientas (terminal, editor, navegador) | PR #1 — los alumnos piden a Devin que identifique los bugs |
| 02 | B3 + B4 | B3: Sandbox simplificado — entorno de trabajo, permisos, configuración de acceso a repos. B4: Primeros pasos reales — conectar repo propio, definir tarea, ejecutar y revisar el output | PR #1 — Devin corrige los bugs identificados en sesión 1 |
| 03 | B5 | B5: Flujo de trabajo con PRs — cómo delegar code review parcial a Devin, cómo pedirle que proponga correcciones, cómo validar el output antes de aprobar | PR #3 — detección y refactor del código duplicado |
| 04 | B6 | B6: Testing con Devin — cómo pedirle que complete una suite incompleta, límites del testing autónomo, revisión humana de los tests generados | PR #2 — Devin completa los tests del escenario-2 |
| 05 | B7 | B7: Documentación y calidad de código — añadir comentarios, generar READMEs, detectar violaciones de estilo; qué documenta bien Devin y qué no | PR #4 — Devin restaura la documentación eliminada |
| 06 | B8 | B8: Debugging de endpoints y lógica compleja — diagnóstico de comportamientos incorrectos, estrategia de prompts para bugs de lógica vs bugs de sintaxis | PR #5 — Devin corrige los dos bugs de list_tasks |
| 07 | B9 | B9: Integración en flujo de equipo — branching, PRs automáticos, cómo comunicar restricciones del equipo a Devin | Por definir al crear la guía |
| 08 | B10 | B10: Gobernanza y producción — límites de autonomía en entornos empresariales, modelo de gobernanza, métricas para medir el impacto real | Por definir al crear la guía |

---

## 5. Estado actual de los materiales

### Completados

| Archivo | Estado | Notas |
|---|---|---|
| `guias/sesion-01-introduccion.md` | Completo y revisado | Última revisión: corrección de erratas y ajuste de horarios a 15:30 |
| `.devin/instructions.md` | Completo | Instrucciones en castellano para que Devin respete las convenciones del proyecto |
| `requirements.txt` | Completo | Versiones fijas de las 7 dependencias |
| `.gitignore` | Completo | `__pycache__/`, `*.pyc`, `*.db`, `.claude/`, `venv/` |
| `aplicacion/` (5 archivos) | Completo en `main` | API funcional con comentarios en castellano |
| 5 ramas de escenarios | Completo y pusheadas | PRs abiertos contra `main` en GitHub |
| `README.md` | Vacío intencionalmente | Forma parte del escenario 4. No añadir contenido. |

### Pendientes

| Archivo | Prioridad |
|---|---|
| `guias/sesion-02-sandbox-primeros-pasos.md` | Alta — siguiente a crear |
| `guias/sesion-03-flujo-prs.md` | Media |
| `guias/sesion-04-testing.md` | Media |
| `guias/sesion-05-documentacion.md` | Media |
| `guias/sesion-06-debugging.md` | Media |
| `guias/sesion-07-integracion-equipo.md` | Baja |
| `guias/sesion-08-gobernanza.md` | Baja |

---

## 6. Índice de la presentación de la sesión 1 — 13 diapositivas

La sesión 1 tiene una presentación de 13 diapositivas en Gamma:
**URL:** https://gamma.app/docs/Devin-AI-drzx5jgsctwn5hs

Solo la sesión 1 tiene presentación Gamma. Las sesiones siguientes no tienen PPT salvo que se indique expresamente al crear su guía.

| # | Título de diapositiva | Momento en la sesión |
|---|---|---|
| 1 | Devin AI — Sesión 01 · Introducción y Arquitectura | Apertura (15:30) |
| 2 | ¿Qué vamos a ver hoy? | Apertura |
| 3 | Copilot vs. Agente Autónomo | B1 — 15:40 |
| 4 | Capacidades reales de Devin | B1 |
| 5 | Limitaciones reales — no ignorarlas | B1 |
| 6 | Caso real: Gumroad | 16:15 |
| 7 | Casos reales: Goldman Sachs y Visma | 16:15 |
| 8 | Arquitectura interna: cómo planifica Devin | B2 — 16:20 |
| 9 | Las tres herramientas de Devin | B2 |
| 10 | La interfaz de Devin — orientación rápida | Antes de la demo — 16:45 |
| 11 | Demo en vivo | Demo — 16:45 |
| 12 | Actividad: tú con Devin | Actividad — 17:25 |
| 13 | ¿Qué aprendimos hoy? | Cierre — 18:25 |

---

## 7. Instrucciones para crear las guías de las sesiones restantes

### Principios generales del curso

**Este es un curso práctico de herramienta, no un curso académico.** La prioridad absoluta es la práctica. Cada sesión debe maximizar el tiempo que los alumnos pasan usando Devin, no escuchando teoría.

1. **Tono:** técnico y directo, sin relleno. No usar frases de transición vacías. Ir al grano.

2. **Notas del orador:** escritas en primera persona para leerse directamente. El formador debe poder leerlas en voz alta sin reinterpretar. Ejemplo correcto: *"Llevamos años usando herramientas de asistencia al código. GitHub Copilot, ChatGPT, Cursor."* Ejemplo incorrecto: *"Hablar sobre herramientas existentes y comparar con Devin."*

3. **Didascalias de pantalla:** entre asteriscos, en cursiva. Indican qué tiene que hacer el formador. Ejemplo: `*Cambiar a la pestaña del PR en GitHub.*`

4. **Timing:** cada sección lleva su cabecera con duración y hora de inicio. El timing exacto se define sesión a sesión al crear cada guía, no de antemano. El descanso es siempre a las 17:05 y dura 20 minutos.

5. **Actividades:** duran entre 10 y 20 minutos. Los alumnos son desarrolladores — no necesitan más tiempo para lanzar un prompt a Devin sobre un repo pequeño. Si una actividad se queda corta, la solución es añadir más actividades o más repos, no alargar artificialmente una sola.

6. **Prompts para Devin:** en bloques de código sin lenguaje especificado. Escribir el texto exacto que el formador debe escribir en la interfaz de Devin. Nunca parafrasear.

7. **Puesta en común:** preguntas concretas que generan respuestas concretas, no debates abiertos.

8. **No hay actividades por equipos planificadas.** Si se deciden, se indicará al crear la guía de esa sesión.

9. **No hay presentaciones de alumnos.** Es un curso de 3 horas por sesión — los alumnos no se llevan trabajo a casa ni presentan repos.

### Estructura de cada guía

La estructura varía por sesión según el contenido. No hay una plantilla rígida. Lo que sí debe tener siempre cada guía:

- Objetivos de aprendizaje (3-5 en infinitivo)
- Materiales necesarios antes de empezar
- Timing de la sesión (definido al crear la guía)
- Notas del orador para cada bloque teórico
- Demo en vivo con prompts exactos y paso a paso detallado
- Una o varias actividades técnicas de 10-20 minutos cada una
- Puesta en común con preguntas concretas
- Cierre con preview de la sesión siguiente

**Todas las sesiones con contenido teórico tienen presentación PPT en Gamma.** La sesión 1 ya está creada. Las demás se crean al desarrollar cada guía.

**El flujo de trabajo para cada sesión es siempre:** primero se crea el PPT en Gamma con el contenido teórico estructurado en slides, y después se escribe la guía del formador con las notas del orador alineadas slide por slide. Las notas deben indicar qué decir en cada slide concreta, cuánto tiempo, qué muestra en pantalla y qué hace a continuación. El PPT es el soporte visual para el alumno; el `.md` es el teleprompter del formador.

**El caso real intercalado es propio de la sesión 1.** No se incluye automáticamente en todas las sesiones.

### Contenido teórico por sesión

Las demos se mantienen como referencia. Las actividades concretas se definen al crear cada guía — puede haber una o varias, y pueden requerir repos adicionales si la actividad sobre `gestor-tareas-api` resulta demasiado simple.

**Sesión 2 — Sandbox y primeros pasos reales**
- B3: qué es un sandbox en Devin, permisos mínimos (lectura vs escritura), cómo limitar el alcance de una sesión.
- B4: flujo completo — conectar repo, escribir la primera tarea bien descrita, leer el plan de Devin, supervisar la ejecución, revisar el PR resultante.
- Demo: conectar `gestor-tareas-api` en modo escritura y pedirle a Devin que corrija el bug #1 del PR #1 (validación de longitud de título) con test incluido.

**Sesión 3 — Flujo de trabajo con PRs**
- B5: code review parcial con Devin, delegar detección de code smells, pedir propuestas de refactor, diferencia entre "encuentra problemas" y "corrígelo".
- Demo: PR #3. Pedirle a Devin que detecte el código duplicado y proponga la función `get_task_or_404`.

**Sesión 4 — Testing con Devin**
- B6: tipos de tests que Devin genera bien (happy path, 404, validaciones simples), tipos que falla (lógica compleja, integración con dependencias externas), cómo revisar tests generados.
- Demo: PR #2. Mostrar los TODO comentados y pedirle a Devin que los implemente.

**Sesión 5 — Documentación y calidad de código**
- B7: documentación que Devin genera bien (comentarios inline, docstrings, READMEs), documentación que requiere supervisión (decisiones de arquitectura, razonamientos de negocio).
- Demo: PR #4. Pedirle a Devin que restaure todos los comentarios siguiendo las convenciones del proyecto.

**Sesión 6 — Debugging de endpoints**
- B8: estrategia para diagnosticar comportamientos incorrectos (describir el síntoma, no la causa), diferencia entre bugs de lógica y bugs de sintaxis.
- Demo: PR #5. Mostrar el comportamiento incorrecto de `GET /tasks?status=done` y pedirle a Devin que diagnostique.

**Sesión 7 — Integración en flujo de equipo**
- B9: branching strategy con Devin, cómo comunicar restricciones del equipo (no tocar archivos de migración, no cambiar contratos de API públicos).
- Demo y actividades: por definir al crear la guía.

**Sesión 8 — Gobernanza y producción**
- B10: límites de autonomía recomendados en entornos empresariales, modelo de gobernanza, métricas para medir el impacto real.
- Demo y actividades: por definir al crear la guía.

---

## 8. Comandos útiles para el trabajo en este repo

```bash
# Clonar el repo
git clone https://github.com/jmojpar/gestor-tareas-api.git
cd gestor-tareas-api

# Crear y activar entorno virtual
python -m venv venv
venv\Scripts\activate        # Windows
source venv/bin/activate     # macOS/Linux

# Instalar dependencias
pip install -r requirements.txt

# Arrancar la API
uvicorn aplicacion.principal:app --reload

# Ejecutar tests
.\venv\Scripts\python.exe -m pytest tests/ -v   # Windows
python -m pytest tests/ -v                       # macOS/Linux

# Ver estado de ramas
git branch -a

# Ver diferencias de un escenario respecto a main
git diff main..escenario-1-bug-logico -- aplicacion/rutas/tareas.py

# Crear nueva guía y commitear
git add guias/sesion-XX-nombre.md
git commit -m "docs: guía completa del formador para la sesión XX"
git push origin main
```
