# Mini API de Tareas con FastAPI y SQLite

Esta es una API REST que permite gestionar tareas con persistencia en SQLite.

## Requisitos

```bash
pip install fastapi uvicorn sqlite3
```

## Ejecución

Para iniciar el servidor:

```bash
uvicorn main:app --reload
```

El servidor estará disponible en `http://localhost:8000`

## Endpoints Disponibles

### Listar Tareas
```http
GET /tareas
```

Parámetros de consulta opcionales:
- `estado`: Filtrar por estado ("pendiente", "en_progreso", "completada")
- `texto`: Buscar en descripción
- `prioridad`: Filtrar por prioridad ("baja", "media", "alta")
- `orden`: Ordenar por fecha ("asc" o "desc")

### Crear Tarea
```http
POST /tareas
```

Body:
```json
{
    "descripcion": "Nueva tarea",
    "estado": "pendiente",
    "prioridad": "media"
}
```

### Actualizar Tarea
```http
PUT /tareas/{id}
```

Body (campos opcionales):
```json
{
    "descripcion": "Tarea actualizada",
    "estado": "completada",
    "prioridad": "alta"
}
```

### Eliminar Tarea
```http
DELETE /tareas/{id}
```

### Obtener Resumen
```http
GET /tareas/resumen
```

### Completar Todas las Tareas
```http
PUT /tareas/completar_todas
```

## Ejemplos de Uso

### Crear una tarea
```bash
curl -X POST "http://localhost:8000/tareas" -H "Content-Type: application/json" -d '{"descripcion": "Estudiar FastAPI", "prioridad": "alta"}'
```

### Listar tareas pendientes de alta prioridad
```bash
curl "http://localhost:8000/tareas?estado=pendiente&prioridad=alta"
```

### Actualizar una tarea
```bash
curl -X PUT "http://localhost:8000/tareas/1" -H "Content-Type: application/json" -d '{"estado": "completada"}'
```