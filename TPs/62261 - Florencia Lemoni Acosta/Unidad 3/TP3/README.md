# API de Tareas Persistente

API RESTful para gestión de tareas con persistencia en SQLite, construida con FastAPI.

## 📋 Descripción

Esta API permite crear, leer, actualizar y eliminar tareas, con funcionalidades adicionales como filtrado, búsqueda y resúmenes estadísticos. Todas las tareas se almacenan de forma persistente en una base de datos SQLite.

## 🚀 Características

- ✅ CRUD completo de tareas
- 🔍 Filtrado por estado, prioridad y texto
- 📊 Resumen estadístico de tareas
- 💾 Persistencia en SQLite
- 📝 Validación de datos con Pydantic
- 📚 Documentación automática con Swagger UI

## 🛠️ Tecnologías

- **FastAPI**: Framework web moderno y rápido
- **SQLite**: Base de datos embebida
- **Pydantic**: Validación de datos
- **Python 3.7+**

## 📦 Instalación

1. Clona el repositorio o copia el archivo `main.py`

2. Instala las dependencias:
```bash
pip install fastapi uvicorn
```

3. Ejecuta el servidor:
```bash
uvicorn main:app --reload
```

4. Accede a la documentación interactiva:
- Swagger UI: `http://localhost:8000/docs`
- ReDoc: `http://localhost:8000/redoc`

## 📖 Endpoints

### 🏠 Información general

```http
GET /
```
Retorna información básica de la API.

### 📝 Obtener todas las tareas

```http
GET /tareas
```

**Parámetros de consulta opcionales:**
- `estado`: Filtra por estado (`pendiente`, `en_progreso`, `completada`)
- `prioridad`: Filtra por prioridad (`baja`, `media`, `alta`)
- `texto`: Busca tareas que contengan el texto en la descripción
- `orden`: Ordena por fecha (`asc` o `desc`)

**Ejemplo:**
```bash
GET /tareas?estado=pendiente&prioridad=alta&orden=desc
```

### ➕ Crear una tarea

```http
POST /tareas
```

**Body (JSON):**
```json
{
  "descripcion": "Completar el informe mensual",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Campos:**
- `descripcion` (requerido): Texto descriptivo de la tarea
- `estado` (opcional): `pendiente`, `en_progreso` o `completada` (default: `pendiente`)
- `prioridad` (opcional): `baja`, `media` o `alta` (default: `media`)

### ✏️ Actualizar una tarea

```http
PUT /tareas/{id}
```

**Body (JSON):**
```json
{
  "descripcion": "Completar y revisar el informe mensual",
  "estado": "en_progreso",
  "prioridad": "alta"
}
```

Todos los campos son opcionales. Solo se actualizarán los campos enviados.

### 🗑️ Eliminar una tarea

```http
DELETE /tareas/{id}
```

### 📊 Obtener resumen

```http
GET /tareas/resumen
```

Retorna estadísticas de todas las tareas agrupadas por estado y prioridad.

**Respuesta:**
```json
{
  "total_tareas": 15,
  "por_estado": {
    "pendiente": 5,
    "en_progreso": 3,
    "completada": 7
  },
  "por_prioridad": {
    "baja": 4,
    "media": 6,
    "alta": 5
  },
  "pendiente": 5,
  "en_progreso": 3,
  "completada": 7
}
```

### ✔️ Completar todas las tareas

```http
PUT /tareas/completar_todas
```

Marca todas las tareas como completadas.

## 💡 Ejemplos de uso

### Usando cURL

**Crear una tarea:**
```bash
curl -X POST "http://localhost:8000/tareas" \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Revisar código",
    "estado": "pendiente",
    "prioridad": "alta"
  }'
```

**Obtener tareas pendientes:**
```bash
curl "http://localhost:8000/tareas?estado=pendiente"
```

**Actualizar una tarea:**
```bash
curl -X PUT "http://localhost:8000/tareas/1" \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "completada"
  }'
```

**Eliminar una tarea:**
```bash
curl -X DELETE "http://localhost:8000/tareas/1"
```

### Usando Python (requests)

```python
import requests

BASE_URL = "http://localhost:8000"

# Crear tarea
nueva_tarea = {
    "descripcion": "Preparar presentación",
    "prioridad": "alta"
}
response = requests.post(f"{BASE_URL}/tareas", json=nueva_tarea)
print(response.json())

# Obtener todas las tareas
response = requests.get(f"{BASE_URL}/tareas")
print(response.json())

# Obtener resumen
response = requests.get(f"{BASE_URL}/tareas/resumen")
print(response.json())
```

## 🗄️ Estructura de la Base de Datos

**Tabla: `tareas`**

| Campo | Tipo | Descripción |
|-------|------|-------------|
| `id` | INTEGER | Clave primaria autoincremental |
| `descripcion` | TEXT | Descripción de la tarea |
| `estado` | TEXT | Estado: pendiente, en_progreso, completada |
| `prioridad` | TEXT | Prioridad: baja, media, alta |
| `fecha_creacion` | TEXT | Fecha/hora de creación (ISO 8601) |

## ⚠️ Validaciones

- La descripción no puede estar vacía o contener solo espacios
- El estado debe ser: `pendiente`, `en_progreso` o `completada`
- La prioridad debe ser: `baja`, `media` o `alta`

## 🔧 Configuración

La base de datos SQLite se crea automáticamente al iniciar el servidor con el nombre `tareas.db` en el directorio actual. Puedes modificar el nombre editando la constante `DB_NAME` en el código.

