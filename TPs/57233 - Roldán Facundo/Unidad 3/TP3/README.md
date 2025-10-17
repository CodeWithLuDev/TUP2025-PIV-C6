# TP3 - API de Tareas con Persistencia SQLite

## Descripción

API REST desarrollada con FastAPI que permite gestionar tareas de forma persistente usando SQLite como base de datos.

## Características

✅ Persistencia de datos con SQLite
✅ CRUD completo de tareas
✅ Filtros por estado, texto y prioridad
✅ Ordenamiento por fecha de creación
✅ Campo de prioridad (baja, media, alta)
✅ Resumen de tareas por estado
✅ Validación con Pydantic Models

## Requisitos

- Python 3.7+
- FastAPI
- Uvicorn
- SQLite3 (incluido en Python)

## Instalación

```bash
pip install fastapi uvicorn
```

## Ejecución

```bash
uvicorn main:app --reload
```

El servidor se iniciará en `http://127.0.0.1:8000`

## Documentación Interactiva

Una vez iniciado el servidor, accede a:
- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`

## Endpoints

### 1. Listar Tareas
**GET** `/tareas`

**Query Parameters:**
- `estado` (opcional): Filtra por estado (`pendiente`, `en_progreso`, `completada`)
- `texto` (opcional): Busca en la descripción
- `prioridad` (opcional): Filtra por prioridad (`baja`, `media`, `alta`)
- `orden` (opcional): Ordena por fecha (`asc` o `desc`)

**Ejemplos:**
```bash
curl http://127.0.0.1:8000/tareas
curl http://127.0.0.1:8000/tareas?estado=pendiente
curl http://127.0.0.1:8000/tareas?texto=TP3
curl http://127.0.0.1:8000/tareas?prioridad=alta
curl http://127.0.0.1:8000/tareas?orden=asc
```

### 2. Crear Tarea
**POST** `/tareas`

**Body (JSON):**
```json
{
  "descripcion": "Completar el TP3",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Ejemplo:**
```bash
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Estudiar FastAPI", "estado": "pendiente", "prioridad": "media"}'
```

### 3. Actualizar Tarea
**PUT** `/tareas/{id}`

**Body (JSON):**
```json
{
  "descripcion": "Nueva descripción",
  "estado": "en_progreso",
  "prioridad": "baja"
}
```

**Ejemplo:**
```bash
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'
```

### 4. Eliminar Tarea
**DELETE** `/tareas/{id}`

**Ejemplo:**
```bash
curl -X DELETE http://127.0.0.1:8000/tareas/1
```

### 5. Resumen de Tareas
**GET** `/tareas/resumen`

Devuelve la cantidad de tareas por cada estado.

**Ejemplo:**
```bash
curl http://127.0.0.1:8000/tareas/resumen
```

**Respuesta:**
```json
{
  "pendiente": 5,
  "en_progreso": 2,
  "completada": 3
}
```

### 6. Completar Todas las Tareas
**PUT** `/tareas/completar_todas`

Marca todas las tareas como completadas.

**Ejemplo:**
```bash
curl -X PUT http://127.0.0.1:8000/tareas/completar_todas
```

## Validaciones

### Estados válidos:
- `pendiente`
- `en_progreso`
- `completada`

### Prioridades válidas:
- `baja`
- `media`
- `alta`

### Reglas:
- La descripción no puede estar vacía
- Los campos `estado` y `prioridad` deben ser válidos
- La fecha de creación se genera automáticamente

## Estructura de la Base de Datos

**Tabla: tareas**

| Campo           | Tipo    | Descripción                        |
|-----------------|---------|-------------------------------------|
| id              | INTEGER | Clave primaria (autoincremental)   |
| descripcion     | TEXT    | Descripción de la tarea (not null) |
| estado          | TEXT    | Estado actual (not null)           |
| prioridad       | TEXT    | Nivel de prioridad (not null)      |
| fecha_creacion  | TEXT    | Timestamp ISO 8601 (not null)      |

## Persistencia

Los datos se almacenan en el archivo `tareas.db` que se crea automáticamente al iniciar la aplicación. Este archivo persiste entre reinicios del servidor.

## Testing

Para ejecutar los tests del TP3:

```bash
# Instalar pytest
pip install pytest httpx

# Ejecutar todos los tests
pytest test_TP3.py -v

# Ejecutar un test específico
pytest test_TP3.py::test_00_crear_tarea_exitosamente -v
```

## Archivos del Proyecto

```
TP3/
├── main.py         # Código principal de la API
├── tareas.db       # Base de datos SQLite (generado automáticamente)
├── README.md       # Este archivo
└── test_TP3.py     # Tests (proporcionado por la cátedra)
```

## Mejoras Implementadas

1. ✅ **Endpoint de resumen**: Cuenta tareas por estado
2. ✅ **Campo prioridad**: Con validación y filtro
3. ✅ **Ordenamiento**: Por fecha de creación (asc/desc)
4. ✅ **Pydantic Models**: Para validación de datos

## Ejemplos de Uso Completo

```bash
# 1. Crear varias tareas
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Tarea urgente", "prioridad": "alta"}'

curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Tarea normal", "prioridad": "media"}'

# 2. Ver resumen
curl http://127.0.0.1:8000/tareas/resumen

# 3. Filtrar por prioridad alta
curl http://127.0.0.1:8000/tareas?prioridad=alta

# 4. Actualizar estado
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "en_progreso"}'

# 5. Ver todas ordenadas por fecha (más antiguas primero)
curl http://127.0.0.1:8000/tareas?orden=asc
```

## Notas

- La base de datos se crea automáticamente al iniciar la aplicación
- Los datos persisten entre reinicios del servidor
- Todos los endpoints devuelven JSON
- Los códigos de estado HTTP son apropiados para cada operación

## Autor

[Roldán Facundo Exequiel]
