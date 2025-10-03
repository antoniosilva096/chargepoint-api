# ⚡ ChargePoint API

API para gestionar **ChargePoints** y sus **Connectors** con **borrado lógico (soft delete)**, construida con **Django 5** + **Django REST Framework**.
Incluye **versionado**, **paginación**, **filtros/búsqueda/ordenación**, **respuesta uniforme usando envelope** y **documentación OpenAPI (Swagger/ReDoc)**.

---

## 🧭 Tabla de contenidos
- [🏗️ Arquitectura y enfoque](#-arquitectura-y-enfoque)
- [🧰 Stack y herramientas](#-stack-y-herramientas)
- [✅ Requisitos](#-requisitos)
- [⚙️ Configuración](#-configuración)
- [🚀 Ejecución](#-ejecución)
- [🧩 Endpoints](#-endpoints)
- [📚 Documentación (OpenAPI)](#-documentación-openapi)
- [📦 Formato de respuesta (envelope)](#-formato-de-respuesta-envelope)
- [🧽 Borrado lógico (soft delete)](#-borrado-lógico-soft-delete)
- [🧪 Tests](#-tests)
- [🎲 Datos de demo (management command)](#-datos-de-demo-management-command)
- [🔐 Admin de Django](#-admin-de-django)
- [🧭 Versionado de API y crecimiento futuro](#-versionado-de-api-y-crecimiento)
- [🛡️ Notas de seguridad](#️-notas-de-seguridad)


---

## 🏗️ Arquitectura y enfoque

### Modelado
- **ChargePoint** con `status` ∈ {`ready`, `charging`, `waiting`, `error`}.
- **Connector** relacionado por FK con `ChargePoint`. Los conectores se exponen **anidados** y **read-only**.
- **SoftDeleteModel** base con `deleted_at` + manager que **oculta** elementos eliminados.
- **Índices explícitos y nombrados** para rendimiento y trazabilidad en migraciones.

### API
- **Versionada**: `/api/v1/...`
- **CRUD** de `ChargePoint`: `POST` / `GET list` / `GET detail` / `PUT` / `PATCH` / `DELETE (soft)`.
- **DX**: respuesta uniforme (envelope), handler global de excepciones, prefetch para evitar N+1, paginación, filtros/búsqueda/ordenación.

---

## 🧰 Stack y herramientas
- **Backend**: Django 5, Django REST Framework
- **DB**: PostgreSQL 16 (Docker)
- **Doc**: drf-spectacular (OpenAPI 3) + Swagger UI + ReDoc
- **Tests**: pytest, pytest-django, factory_boy, Faker
- **Calidad**: pre-commit, Black, Ruff, isort
- **Contenedores**: Docker Compose

---

## ✅ Requisitos
- **Opción A (recomendada):** Docker + Docker Compose
- **Opción B (local):** Python 3.12 y PostgreSQL 16

---

## ⚙️ Configuración
Crea un archivo .env, usa el ejemplo de abajo o adáptalo:



Variables relevantes en `.env`:
```dotenv
SECRET_KEY=3)s%))vppg8nn5x+&n5m*3j7@0mya9414uqxh38^5*da8&j7cy
ALLOWED_HOSTS=127.0.0.1,localhost,0.0.0.0
DEBUG=True
DB_NAME=chargepoint
DB_USER=chargepoint
DB_PASSWORD=chargepoint1234
DB_HOST=db
DB_PORT=5432
COMPOSE_PROJECT_NAME=chargepoint-api
```
Crea una Secret Key Segura:
```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

(Opcional) Activar hooks de calidad del código automáticos al hacer commit:
```bash
pre-commit install
```

---

## 🚀 Ejecución

### Con Docker (recomendado)

**Levantar servicios:**
```bash
docker compose up -d --build
```

**Aplicar migraciones:**
```bash
docker compose run --rm web python manage.py migrate
```

**Crear superusuario:**
```bash
docker compose run --rm web python manage.py createsuperuser
```

**App disponible en ->** http://localhost:8000/
#### Redirige a la documentación de Swagger para mejor experiencia de usuario

### Local (sin Docker)
```bash
python -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
export DJANGO_SETTINGS_MODULE=config.settings
python manage.py migrate
python manage.py runserver 0.0.0.0:8000
```

---

## 🧩 Endpoints

**Base:** `/api/v1/`

**Rutas con slash opcional** para mejor DX (`/chargepoint` o `/chargepoint/`)

### ChargePoint
- `POST   /chargepoint` — Crear
- `GET    /chargepoint` — Listar (paginado)
- `GET    /chargepoint/{id}` — Detalle
- `PUT    /chargepoint/{id}` — Actualizar completo
- `PATCH  /chargepoint/{id}` — Actualización parcial (p. ej. `status`)
- `DELETE /chargepoint/{id}` — **Soft delete** (marca `deleted_at`)

**Query params (list):**
- `status=ready|charging|waiting|error`
- `search=<nombre>`
- `ordering=name|created_at` (usar `-` para descendente)
- `page=<n>`

---

## 📚 Documentación (OpenAPI)

- **Swagger UI:** http://localhost:8000/api/docs/swagger/
- **ReDoc:** http://localhost:8000/api/docs/redoc/
- **Schema JSON:** http://localhost:8000/api/schema/

**Exportar schema a archivo:**
```bash
python manage.py spectacular --file schema.yaml
```

---

## 📦 Formato de respuesta (envelope)

**Éxito**
```json
{
  "code": 200,
  "message": "OK",
  "data": { "...": "..." },
  "errors": null
}
```

**Error (handler global)**
```json
{
  "code": 404,
  "message": "Not Found",
  "data": null,
  "errors": { "detail": "No encontrado" }
}
```

---

## 🧽 Borrado lógico (soft delete)

- `DELETE` marca `deleted_at` (no borra físicamente).
- El manager por defecto oculta elementos eliminados en listados y detalle.
- **Restore** disponible vía admin (acción personalizada) si es necesario.

---

## 🧪 Tests

### Unit tests
- Modelos: soft delete y managers
- Serializers: validación de `name`, conectores read-only
- Vistas (unit): `APIRequestFactory`
- Exception handler

### E2E (API)
- `APIClient` recorriendo CRUD real con envelope, paginación, filtros, `404/409` y soft delete.

### Comandos
```bash
# todos
pytest -q

# unit
pytest -q tests/unit

# e2e
pytest -q tests/api

# coverage
coverage run -m pytest && coverage report -m
```

---

## 🎲 Datos de demo (management command)

**Poblar/limpiar rápidamente:**
```bash
# Crear 20 chargepoints con conectores aleatorios
python manage.py chargepoints_demo --populate 20

# Crear 10 chargepoints con 2 conectores cada uno y seed
python manage.py chargepoints_demo --populate 10 --connectors 2 --seed 123

# Marcar 30% como soft-deleted
python manage.py chargepoints_demo --populate 20 --soft-delete-ratio 0.3

# Limpiar (hard delete) TODO
python manage.py chargepoints_demo --clean --force
```

**Después de poblar, se puede probar en Swagger:**
```
GET /api/v1/chargepoint?status=ready&search=CP&ordering=-created_at&page=1
```

---



## 🔐 Admin de Django

**Panel:** http://localhost:8000/admin/ (requiere superusuario).

- Listados con `created_at`, `deleted_at`, filtros por estado y eliminado/vivo.
- `Connector` inline solo lectura dentro de `ChargePoint`.

---

## 🧭 Versionado de API y crecimiento futuro

- La API está disponible en `/api/v1/`.
- Futuras versiones: añadir `/api/v2/` sin tocar `config/urls.py` (cada versión mantiene su propio `api/vX/urls.py`).
- Rutas con **slash opcional** para mejor DX (`/chargepoint` y `/chargepoint/`).
---

## 🛡️ Notas de seguridad
- `SECRET_KEY` y credenciales en `.env`.
- **CORS/CSRF**: no configurados para exposición pública (pendiente de ajustar en producción).
- **Permisos**: la prueba usa `AllowAny`; en producción se debe usar `IsAuthenticated`/scopes.
- **Índices explícitos y nombrados** para trazabilidad (evitar duplicados).
- **Hard delete** solo vía management/admin y con confirmación.
