# ADR-001: Elección de SQLite como base de datos

| Campo | Valor |
|---|---|
| **Estado** | Aceptado |
| **Fecha** | 2025-05-28 |
| **Autores** | Equipo de desarrollo |

---

## Contexto

La API de Gestión de Tareas necesita una base de datos relacional para persistir tareas con los campos `id`, `title`, `description`, `status` y `created_at`. El proyecto tiene las siguientes características:

- Es una API REST ligera construida con FastAPI y SQLAlchemy.
- Está pensada para entornos de desarrollo, pruebas de concepto y despliegues de baja concurrencia.
- El equipo busca minimizar la complejidad operativa: sin servidores de base de datos externos, sin configuración de red ni gestión de credenciales.
- El volumen de datos esperado es reducido (miles de registros, no millones).
- Se valora poder arrancar la aplicación con un solo comando (`uvicorn`) sin dependencias adicionales.

---

## Decisión

Se adopta **SQLite** como motor de base de datos, almacenando los datos en el archivo local `tareas.db`.

### Razones principales

1. **Cero configuración**: SQLite no requiere instalar ni administrar un servidor de base de datos. El archivo se crea automáticamente en el primer arranque.
2. **Incluido en la biblioteca estándar de Python**: El módulo `sqlite3` viene integrado en CPython, por lo que no se necesitan dependencias de sistema adicionales.
3. **Portabilidad**: La base de datos es un único archivo que se puede copiar, versionar o mover entre entornos sin herramientas especiales.
4. **Integración sencilla con SQLAlchemy**: Basta con definir la URL de conexión `sqlite:///./tareas.db` y añadir `check_same_thread=False` para el uso asíncrono con FastAPI.
5. **Tests rápidos y aislados**: SQLite permite crear bases de datos en memoria (`:memory:` con `StaticPool`), lo que hace que los tests sean instantáneos y no afecten a los datos de producción.
6. **Huella mínima**: No consume recursos de un proceso servidor independiente; ideal para el alcance actual del proyecto.

---

## Alternativas consideradas

### PostgreSQL

| Aspecto | Detalle |
|---|---|
| **Ventajas** | Soporte completo de SQL estándar y tipos avanzados (JSONB, arrays). Alta concurrencia con MVCC. Excelente ecosistema de extensiones (PostGIS, pg_trgm). Robusto para producción a gran escala. Replicación nativa y copias de seguridad incrementales. |
| **Inconvenientes** | Requiere instalar y mantener un servidor (`postgresql-server`) o un servicio gestionado (RDS, Cloud SQL). Añade configuración de red, credenciales y gestión de conexiones. Sobredimensionado para una API con bajo volumen de datos y baja concurrencia. Incrementa la complejidad del entorno de desarrollo y CI. |

### MySQL / MariaDB

| Aspecto | Detalle |
|---|---|
| **Ventajas** | Amplia adopción y comunidad grande. Buen rendimiento en lecturas con el motor InnoDB. Compatible con la mayoría de proveedores de hosting compartido. Herramientas maduras de administración (phpMyAdmin, MySQL Workbench). |
| **Inconvenientes** | También requiere un proceso servidor independiente. Cumplimiento parcial del estándar SQL en algunas áreas (modos estrictos, CTEs en versiones antiguas). Menor riqueza de tipos de datos comparado con PostgreSQL. Configuración inicial más compleja que SQLite y sin ventaja clara frente a PostgreSQL para nuevos proyectos. |

---

## Consecuencias

### Positivas

- **Arranque inmediato**: cualquier desarrollador puede clonar el repositorio y ejecutar la API sin instalar servicios externos.
- **Pipeline de CI simplificado**: no es necesario levantar contenedores de base de datos en los flujos de integración continua.
- **Menor superficie de errores operativos**: se eliminan problemas relacionados con conexiones de red, autenticación de base de datos y compatibilidad de versiones del servidor.

### Negativas y riesgos a largo plazo

- **Concurrencia limitada**: SQLite permite un solo escritor a la vez. Si el proyecto crece y recibe múltiples escrituras simultáneas, se producirán bloqueos (`database is locked`).
- **Sin acceso remoto nativo**: la base de datos vive en el sistema de archivos local; no es posible conectarse desde otra máquina sin herramientas intermedias.
- **Funcionalidades SQL reducidas**: SQLite no soporta algunas operaciones habituales en otros motores (ALTER COLUMN, tipos estrictos por defecto, procedimientos almacenados).
- **Migración futura obligatoria**: si la aplicación escala a producción con alta carga, será necesario migrar a PostgreSQL u otro motor cliente-servidor. Gracias a SQLAlchemy, el cambio de motor se reduce a modificar la URL de conexión y ajustar tipos de columna específicos, pero requerirá pruebas de regresión completas.

### Plan de mitigación

- Mantener toda la lógica de acceso a datos a través de SQLAlchemy ORM para que el cambio de motor sea transparente.
- Monitorizar el rendimiento si el número de usuarios concurrentes aumenta.
- Documentar el procedimiento de migración a PostgreSQL cuando el proyecto lo requiera.
