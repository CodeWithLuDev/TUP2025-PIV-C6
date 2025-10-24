# TP3 - API de Tareas Persistente con SQLite

## Descripción
API REST con FastAPI que gestiona tareas con persistencia en SQLite.

## Instalación

```bash
pip install fastapi uvicorn
```

## Iniciar el servidor

```bash
uvicorn main:app --reload
```

Servidor disponible en: `http://127.0.0.1:8000`

Documentación interactiva: `http://127.0.0.1:8000/docs`

## Endpoints

| Método | Ruta | Descripción |
|--------|------|-------------|
| GET | `/tareas` | Obtiene todas las tareas |
| POST | `/tareas` | Crea una nueva tarea |
| PUT | `/tareas/{id}` | Actualiza una tarea |
| DELETE | `/tareas/{id}` | Elimina una tarea |
| GET | `/tareas/resumen` | Resumen por estado |
| PUT | `/tareas/completar_todas` | Completa todas las tareas |

## Ejemplos de uso

### Crear tarea
```bash
curl -X POST "http://127.0.0.1:8000/tareas" \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Completar TP3", "estado": "pendiente", "prioridad": "alta"}'
```

### Obtener tareas con filtros
```bash
# Todas las tareas
GET /tareas

# Filtrar por estado
GET /tareas?estado=pendiente

# Filtrar por prioridad
GET /tareas?prioridad=alta

# Buscar por texto
GET /tareas?texto=TP3

# Ordenar por fecha
GET /tareas?orden=desc
```

### Actualizar tarea
```bash
curl -X PUT "http://127.0.0.1:8000/tareas/1" \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'
```

## Verificar persistencia

1. Crear algunas tareas
2. Detener el servidor (Ctrl+C)
3. Reiniciar el servidor
4. Verificar que las tareas siguen en la base de datos `tareas.db`

## Estados válidos
- `pendiente`
- `en_progreso`
- `completada`

## Prioridades válidas
- `baja`
- `media`
- `alta`