# TP3 - API de Tareas Persistente con SQLite

## 📋 Descripción

API REST desarrollada con FastAPI que permite gestionar tareas de forma persistente utilizando SQLite como base de datos.

## 🚀 Instalación y Ejecución

### 1. Instalar dependencias

```bash
pip install fastapi uvicorn pydantic
```

### 2. Iniciar el servidor

```bash
uvicorn main:app --reload
```

El servidor estará disponible en: `http://127.0.0.1:8000`

### 3. Acceder a la documentación interactiva

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

## 📊 Estructura de la Base de Datos

La tabla `tareas` tiene la siguiente estructura:

| Campo           | Tipo    | Descripción                    |
|-----------------|---------|--------------------------------|
| id              | INTEGER | Clave primaria autoincremental |
| descripcion     | TEXT    | Descripción de la tarea        |
| estado          | TEXT    | Estado: pendiente/en_progreso/completada |
| prioridad       | TEXT    | Prioridad: baja/media/alta     |
| fecha_creacion  | TEXT    | Fecha y hora de creación       |

## 🔌 Endpoints Disponibles

### 1. Listar todas las tareas
**GET** `/tareas`

**Query Parameters opcionales:**
- `estado`: filtrar por estado (pendiente, en_progreso, completada)
- `texto`: buscar en la descripción
- `prioridad`: filtrar por prioridad (baja, media, alta)
- `orden`: ordenar por fecha (asc o desc)

**Ejemplos:**
```bash
# Obtener todas las tareas
curl http://127.0.0.1:8000/tareas

# Filtrar por estado
curl http://127.0.0.1:8000/tareas?estado=pendiente

# Buscar por texto
curl http://127.0.0.1:8000/tareas?texto=estudiar

# Filtrar por prioridad
curl http://127.0.0.1:8000/tareas?prioridad=alta

# Ordenar de forma descendente
curl http://127.0.0.1:8000/tareas?orden=desc

# Combinar filtros
curl http://127.0.0.1:8000/tareas?estado=pendiente&prioridad=alta&orden=desc
```

### 2. Crear una nueva tarea
**POST** `/tareas`

**Body (JSON):**
```json
{
  "descripcion": "Estudiar para el examen",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Ejemplo curl:**
```bash
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Estudiar FastAPI", "estado": "pendiente", "prioridad": "alta"}'
```

### 3. Actualizar una tarea
**PUT** `/tareas/{id}`

**Body (JSON):** (todos los campos son opcionales)
```json
{
  "descripcion": "Nueva descripción",
  "estado": "completada",
  "prioridad": "media"
}
```

**Ejemplo curl:**
```bash
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'
```

### 4. Eliminar una tarea
**DELETE** `/tareas/{id}`

**Ejemplo curl:**
```bash
curl -X DELETE http://127.0.0.1:8000/tareas/1
```

### 5. Obtener resumen de tareas
**GET** `/tareas/resumen`

Devuelve la cantidad de tareas agrupadas por estado.

**Ejemplo curl:**
```bash
curl http://127.0.0.1:8000/tareas/resumen
```

**Respuesta:**
```json
{
  "pendiente": 3,
  "en_progreso": 2,
  "completada": 5,
  "total": 10
}
```

## 🧪 Ejecutar Tests

### Instalar dependencias de testing:
```bash
pip install pytest requests httpx
```

### Ejecutar todos los tests:
```bash
pytest test_TP3.py -v
```

### Ejecutar un test específico:
```bash
pytest test_TP3.py::test_00_crear_tarea_exitosamente -v
```

## ✅ Validaciones Implementadas

- ✅ La descripción no puede estar vacía
- ✅ Solo se aceptan estados: pendiente, en_progreso, completada
- ✅ Solo se aceptan prioridades: baja, media, alta
- ✅ Se guarda automáticamente la fecha de creación
- ✅ Errores 404 cuando se intenta modificar/eliminar tareas inexistentes
- ✅ Persistencia real: los datos no se pierden al reiniciar el servidor

## 📁 Estructura del Proyecto

```
TP3/
├── main.py          # Código principal de la API
├── tareas.db        # Base de datos SQLite (se crea automáticamente)
├── README.md        # Este archivo
└── test_TP3.py      # Tests (proporcionado por el profesor)
```

## 🎯 Características Implementadas

### Requisitos Básicos
- ✅ Conexión a SQLite
- ✅ Tabla con estructura requerida
- ✅ CRUD completo (Create, Read, Update, Delete)
- ✅ Persistencia de datos
- ✅ Validación de campos

### Mejoras Obligatorias
- ✅ Endpoint de resumen por estado
- ✅ Campo "prioridad" con filtro
- ✅ Ordenamiento por fecha de creación
- ✅ Uso de Pydantic Models para validación

### Extras
- ✅ Documentación automática con Swagger
- ✅ Manejo de errores con códigos HTTP apropiados
- ✅ Consultas SQL dinámicas para filtros
- ✅ Código limpio y comentado
