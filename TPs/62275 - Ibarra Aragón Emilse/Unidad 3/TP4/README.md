# README.md - API de Gestión de Proyectos y Tareas

## Descripción del Proyecto

API REST desarrollada con FastAPI para gestionar proyectos y tareas. Utiliza SQLite como base de datos con relaciones entre tablas y eliminación en cascada.

## Estructura de Tablas

### Diagrama de Base de Datos

```
┌─────────────────────────────┐
│       PROYECTOS             │
├─────────────────────────────┤
│ id (PK)                     │
│ nombre (UNIQUE)             │
│ descripcion                 │
│ fecha_creacion              │
└─────────────────────────────┘
           │
           │ 1:N
           │
           ▼
┌─────────────────────────────┐
│        TAREAS               │
├─────────────────────────────┤
│ id (PK)                     │
│ descripcion                 │
│ estado                      │
│ prioridad                   │
│ proyecto_id (FK)            │
│ fecha_creacion              │
└─────────────────────────────┘
```

### Relaciones entre Tablas

- **Relación 1:N (Uno a Muchos)**: Un proyecto puede tener múltiples tareas, pero cada tarea pertenece a un solo proyecto.
- **Clave Foránea con CASCADE**: `tareas.proyecto_id` referencia a `proyectos.id` con `ON DELETE CASCADE`. Cuando se elimina un proyecto, todas sus tareas asociadas se eliminan automáticamente.
- **Integridad Referencial**: No se puede crear una tarea sin un proyecto válido, ni asignarla a un proyecto inexistente.

## Instalación y Configuración

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación de Dependencias

```bash
pip install fastapi uvicorn pydantic
```

### Iniciar el Servidor

```bash
uvicorn main:app --reload
```

El servidor estará disponible en: `http://localhost:8000`

### Documentación Interactiva

- **Swagger UI**: `http://localhost:8000/docs`
- **ReDoc**: `http://localhost:8000/redoc`

## Endpoints de la API

### 1. Raíz

#### GET /

Información general de la API.

```bash
curl http://localhost:8000/
```

**Respuesta:**
```json
{
  "nombre": "API de Gestión de Proyectos y Tareas",
  "version": "4.0",
  "descripcion": "API con relaciones entre tablas y filtros avanzados",
  "endpoints_proyectos": ["..."],
  "endpoints_tareas": ["..."]
}
```

---

### 2. CRUD de Proyectos

#### GET /proyectos

Lista todos los proyectos (con filtro opcional por nombre).

```bash
# Todos los proyectos
curl http://localhost:8000/proyectos

# Filtrar por nombre
curl "http://localhost:8000/proyectos?nombre=Web"
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "nombre": "Proyecto Web",
    "descripcion": "Desarrollo de aplicación web",
    "fecha_creacion": "2024-01-15T10:30:00"
  }
]
```

#### GET /proyectos/{id}

Obtiene un proyecto específico con contador de tareas.

```bash
curl http://localhost:8000/proyectos/1
```

**Respuesta:**
```json
{
  "id": 1,
  "nombre": "Proyecto Web",
  "descripcion": "Desarrollo de aplicación web",
  "fecha_creacion": "2024-01-15T10:30:00",
  "total_tareas": 5
}
```

#### POST /proyectos

Crea un nuevo proyecto.

```bash
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Proyecto Mobile",
    "descripcion": "Aplicación móvil nativa"
  }'
```

**Body (JSON):**
```json
{
  "nombre": "Proyecto Mobile",
  "descripcion": "Aplicación móvil nativa"
}
```

**Respuesta (201):**
```json
{
  "id": 2,
  "nombre": "Proyecto Mobile",
  "descripcion": "Aplicación móvil nativa",
  "fecha_creacion": "2024-01-16T14:20:00"
}
```

#### PUT /proyectos/{id}

Actualiza un proyecto existente.

```bash
curl -X PUT http://localhost:8000/proyectos/1 \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "Proyecto Web Actualizado",
    "descripcion": "Nueva descripción"
  }'
```

**Body (JSON):**
```json
{
  "nombre": "Proyecto Web Actualizado",
  "descripcion": "Nueva descripción"
}
```

#### DELETE /proyectos/{id}

Elimina un proyecto y todas sus tareas asociadas (CASCADE).

```bash
curl -X DELETE http://localhost:8000/proyectos/1
```

**Respuesta:**
```json
{
  "mensaje": "Proyecto 1 eliminado correctamente",
  "tareas_eliminadas": 5
}
```

---

### 3. Tareas de un Proyecto

#### GET /proyectos/{id}/tareas

Lista todas las tareas de un proyecto (con filtros opcionales).

```bash
# Todas las tareas del proyecto
curl http://localhost:8000/proyectos/1/tareas

# Filtrar por estado
curl "http://localhost:8000/proyectos/1/tareas?estado=pendiente"

# Filtrar por prioridad
curl "http://localhost:8000/proyectos/1/tareas?prioridad=alta"

# Ordenar por fecha
curl "http://localhost:8000/proyectos/1/tareas?orden=desc"

# Múltiples filtros
curl "http://localhost:8000/proyectos/1/tareas?estado=en_progreso&prioridad=alta&orden=asc"
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "descripcion": "Diseñar base de datos",
    "estado": "completada",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2024-01-15T11:00:00"
  }
]
```

#### POST /proyectos/{id}/tareas

Crea una nueva tarea en un proyecto.

```bash
curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Implementar autenticación",
    "estado": "pendiente",
    "prioridad": "alta"
  }'
```

**Body (JSON):**
```json
{
  "descripcion": "Implementar autenticación",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Estados válidos:** `pendiente`, `en_progreso`, `completada`  
**Prioridades válidas:** `baja`, `media`, `alta`

---

### 4. Gestión de Tareas

#### GET /tareas

Lista todas las tareas de todos los proyectos (con filtros).

```bash
# Todas las tareas
curl http://localhost:8000/tareas

# Filtros combinados
curl "http://localhost:8000/tareas?estado=pendiente&prioridad=alta&proyecto_id=1"
```

#### PUT /tareas/{id}

Actualiza una tarea (puede cambiar de proyecto).

```bash
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Tarea actualizada",
    "estado": "en_progreso",
    "prioridad": "media",
    "proyecto_id": 2
  }'
```

**Body (JSON):**
```json
{
  "descripcion": "Tarea actualizada",
  "estado": "en_progreso",
  "prioridad": "media",
  "proyecto_id": 2
}
```

#### DELETE /tareas/{id}

Elimina una tarea específica.

```bash
curl -X DELETE http://localhost:8000/tareas/1
```

---

### 5. Resúmenes y Estadísticas

#### GET /proyectos/{id}/resumen

Obtiene resumen estadístico de un proyecto.

```bash
curl http://localhost:8000/proyectos/1/resumen
```

**Respuesta:**
```json
{
  "proyecto_id": 1,
  "proyecto_nombre": "Proyecto Web",
  "total_tareas": 10,
  "por_estado": {
    "pendiente": 3,
    "en_progreso": 4,
    "completada": 3
  },
  "por_prioridad": {
    "baja": 2,
    "media": 5,
    "alta": 3
  }
}
```

#### GET /resumen

Obtiene resumen general de toda la aplicación.

```bash
curl http://localhost:8000/resumen
```

**Respuesta:**
```json
{
  "total_proyectos": 3,
  "total_tareas": 25,
  "tareas_por_estado": {
    "pendiente": 10,
    "en_progreso": 8,
    "completada": 7
  },
  "proyecto_con_mas_tareas": {
    "id": 1,
    "nombre": "Proyecto Web",
    "cantidad_tareas": 15
  }
}
```

---

## Manejo de Errores

### Códigos de Estado HTTP

- **200 OK**: Operación exitosa
- **201 Created**: Recurso creado exitosamente
- **404 Not Found**: Recurso no encontrado
- **409 Conflict**: Conflicto (ej: nombre duplicado)
- **400 Bad Request**: Datos inválidos
- **422 Unprocessable Entity**: Error de validación

### Ejemplos de Errores

**Proyecto no encontrado (404):**
```json
{
  "detail": {
    "error": "Proyecto con id 99 no encontrado"
  }
}
```

**Nombre duplicado (409):**
```json
{
  "detail": {
    "error": "Ya existe un proyecto con el nombre 'Proyecto Web'"
  }
}
```

**Validación fallida (422):**
```json
{
  "detail": [
    {
      "loc": ["body", "nombre"],
      "msg": "El nombre no puede estar vacío",
      "type": "value_error"
    }
  ]
}
```

---

## Características Avanzadas

### 1. Eliminación en Cascada

Cuando se elimina un proyecto, todas sus tareas se eliminan automáticamente gracias a la configuración `ON DELETE CASCADE` en la base de datos.

```sql
FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
```

### 2. Validaciones

- Nombres de proyectos únicos
- Campos obligatorios no vacíos
- Estados y prioridades con valores predefinidos
- Validación de existencia de proyectos al crear/actualizar tareas

### 3. Filtros y Ordenamiento

- Filtrar proyectos por nombre (búsqueda parcial)
- Filtrar tareas por estado, prioridad y proyecto
- Ordenar tareas por fecha de creación (ascendente/descendente)

### 4. Estadísticas

- Contador de tareas por proyecto
- Resumen por estado y prioridad
- Identificación del proyecto con más tareas

---

## Estructura de Archivos

```
├── main.py          # Endpoints de la API
├── database.py      # Funciones de acceso a datos
├── models.py        # Modelos Pydantic
├── tareas.db        # Base de datos SQLite (se crea automáticamente)
└── README.md        # Este archivo
```

---

## Ejemplos de Uso Completo

### Flujo de Trabajo Típico

```bash
# 1. Crear un proyecto
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre": "E-commerce", "descripcion": "Tienda online"}'

# 2. Crear tareas en el proyecto (asumiendo id=1)
curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Diseñar catálogo", "prioridad": "alta"}'

curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Integrar pasarela de pago", "prioridad": "alta"}'

# 3. Listar tareas del proyecto
curl http://localhost:8000/proyectos/1/tareas

# 4. Actualizar estado de una tarea
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "en_progreso"}'

# 5. Ver resumen del proyecto
curl http://localhost:8000/proyectos/1/resumen

# 6. Ver resumen general
curl http://localhost:8000/resumen
```

---

## Testing

Para ejecutar tests (si están implementados):

```bash
pytest
```

---

## Tecnologías Utilizadas

- **FastAPI**: Framework web moderno y rápido
- **Pydantic**: Validación de datos
- **SQLite**: Base de datos relacional
- **Uvicorn**: Servidor ASGI

---

## Autor

**Ibarra Aragón Emilse** - 62275

---

## Licencia

Proyecto académico - UTN FRRo - TUP 2025
