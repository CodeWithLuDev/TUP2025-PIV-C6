# TP3 - API de Tareas Persistente con SQLite

## Descripción

API REST desarrollada con FastAPI que permite gestionar tareas con persistencia en base de datos SQLite. Las tareas se mantienen almacenadas incluso después de reiniciar el servidor.

## Requisitos

- Python 3.7+
- FastAPI
- Uvicorn
- Pydantic

## Instalación

1. Instalar las dependencias necesarias:

```bash
pip install fastapi uvicorn
```

## Iniciar el servidor

```bash
uvicorn main:app --reload
```

El servidor estará disponible en: `http://localhost:8000`

La documentación interactiva (Swagger) estará en: `http://localhost:8000/docs`

## Estructura de la Base de Datos

**Tabla: tareas**

| Campo           | Tipo    | Descripción                              |
|-----------------|---------|------------------------------------------|
| id              | INTEGER | Clave primaria auto incremental          |
| descripcion     | TEXT    | Descripción de la tarea (no nulo)        |
| estado          | TEXT    | Estado: pendiente, en_progreso, completada |
| fecha_creacion  | TEXT    | Fecha y hora de creación (ISO format)    |
| prioridad       | TEXT    | Prioridad: baja, media, alta             |

## Endpoints Disponibles

### 1. GET /tareas

Obtiene todas las tareas. Acepta filtros opcionales.

**Parámetros de consulta (query params):**
- `estado`: Filtrar por estado (pendiente, en_progreso, completada)
- `texto`: Buscar tareas que contengan este texto en la descripción
- `prioridad`: Filtrar por prioridad (baja, media, alta)
- `orden`: Ordenar por fecha (asc, desc)

**Ejemplos:**

```bash
# Obtener todas las tareas
curl http://localhost:8000/tareas

# Filtrar por estado
curl http://localhost:8000/tareas?estado=pendiente

# Buscar por texto
curl http://localhost:8000/tareas?texto=comprar

# Filtrar por prioridad
curl http://localhost:8000/tareas?prioridad=alta

# Ordenar por fecha descendente
curl http://localhost:8000/tareas?orden=desc

# Combinar filtros
curl http://localhost:8000/tareas?estado=pendiente&prioridad=alta&orden=desc
```

### 2. GET /tareas/resumen

Obtiene un resumen con la cantidad de tareas por cada estado.

**Ejemplo:**

```bash
curl http://localhost:8000/tareas/resumen
```

**Respuesta:**
```json
{
  "pendiente": 5,
  "en_progreso": 2,
  "completada": 10
}
```

### 3. POST /tareas

Crea una nueva tarea.

**Body (JSON):**
```json
{
  "descripcion": "Comprar leche",
  "estado": "pendiente",
  "prioridad": "media"
}
```

**Ejemplo:**

```bash
curl -X POST http://localhost:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Comprar leche", "estado": "pendiente", "prioridad": "alta"}'
```

**Respuesta:**
```json
{
  "id": 1,
  "descripcion": "Comprar leche",
  "estado": "pendiente",
  "fecha_creacion": "2025-10-17T14:30:00.123456",
  "prioridad": "alta"
}
```

### 4. PUT /tareas/{id}

Actualiza una tarea existente. Solo se actualizan los campos proporcionados.

**Body (JSON):**
```json
{
  "estado": "completada"
}
```

**Ejemplo:**

```bash
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'
```

**Respuesta:**
```json
{
  "id": 1,
  "descripcion": "Comprar leche",
  "estado": "completada",
  "fecha_creacion": "2025-10-17T14:30:00.123456",
  "prioridad": "alta"
}
```

### 5. DELETE /tareas/{id}

Elimina una tarea existente.

**Ejemplo:**

```bash
curl -X DELETE http://localhost:8000/tareas/1
```

**Respuesta:** Código 204 (No Content)

## Validaciones

La API valida automáticamente:

- **Estado**: Solo acepta `pendiente`, `en_progreso` o `completada`
- **Prioridad**: Solo acepta `baja`, `media` o `alta`
- **Descripción**: No puede estar vacía (mínimo 1 carácter)
- **IDs inexistentes**: Devuelve error 404 si la tarea no existe

## Persistencia

Los datos se almacenan en el archivo `tareas.db` que se crea automáticamente al iniciar el servidor por primera vez. Este archivo contiene toda la información y persiste entre reinicios del servidor.

## Pruebas

Para ejecutar los tests (si están disponibles):

```bash
pytest test_TP3.py -v
```

## Características Implementadas

✅ CRUD completo con persistencia en SQLite  
✅ Filtros por estado, texto y prioridad  
✅ Ordenamiento por fecha de creación  
✅ Endpoint de resumen estadístico  
✅ Campo de prioridad (baja, media, alta)  
✅ Validación con Pydantic Models  
✅ Manejo de errores (404, 400)  
✅ Documentación automática con Swagger  
✅ Inicialización automática de la base de datos

## Autor

TP3 - Programación de Aplicaciones - 2025