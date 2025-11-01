
# TP4 - API de Proyectos y Tareas

Esta API permite gestionar proyectos y tareas con persistencia en una base de datos SQLite (`tareas.db`). Implementa operaciones CRUD completas, filtros avanzados, resúmenes estadísticos y validaciones robustas utilizando FastAPI y Pydantic. La base de datos incluye una relación uno a muchos entre proyectos y tareas, con integridad referencial asegurada mediante claves foráneas.

## Instrucciones para Iniciar el Servidor

### Requisitos
- Python 3.8 o superior
- Dependencias necesarias:
  ```bash
  pip install fastapi uvicorn pydantic
  ```
  Nota: SQLite está incluido en la biblioteca estándar de Python.

### Estructura del Proyecto
```
TP4/
├── main.py          # Código principal de la API
├── models.py        # Modelos Pydantic para validación
├── database.py      # Funciones de acceso a la base de datos
├── tareas.db        # Base de datos SQLite (se genera al iniciar la API)
├── test_TP4.py      # Tests automatizados
└── README.md        # Este archivo
```

### Iniciar el Servidor
1. Asegúrate de estar en el directorio `TP4`.
2. Ejecuta el siguiente comando:
   ```bash
   uvicorn main:app --reload
   ```
3. La API estará disponible en `http://127.0.0.1:8000`. Accede a la documentación interactiva en:
   - `http://127.0.0.1:8000/docs` (Swagger UI)
   - `http://127.0.0.1:8000/redoc` (ReDoc)

### Ejecutar Tests
Para verificar que la API cumple con los requisitos, ejecuta:
```bash
pytest test_TP4.py -v
```

### Generar `tareas.db` con Datos de Prueba
La base de datos `tareas.db` se crea automáticamente al iniciar la API gracias a la función `init_db()`. Para poblarla con datos de prueba, ejecuta:
```bash
python -c "
import sqlite3
from datetime import datetime
conn = sqlite3.connect('tareas.db')
cur = conn.cursor()
cur.execute('INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)', 
            ('Proyecto Demo', 'Proyecto de prueba', datetime.now().isoformat()))
cur.execute('INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)', 
            ('Tarea de prueba', 'pendiente', 'alta', 1, datetime.now().isoformat()))
cur.execute('INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)', 
            ('Otra tarea', 'completada', 'media', 1, datetime.now().isoformat()))
conn.commit()
conn.close()
"
```

## Estructura de Tablas

### Tabla `proyectos`
| Columna         | Tipo   | Restricciones                     |
|-----------------|--------|-----------------------------------|
| `id`            | INTEGER| PRIMARY KEY, AUTOINCREMENT        |
| `nombre`        | TEXT   | NOT NULL, UNIQUE                  |
| `descripcion`   | TEXT   | NULL                              |
| `fecha_creacion`| TEXT   | NOT NULL (formato ISO 8601)       |

### Tabla `tareas`
| Columna         | Tipo   | Restricciones                     |
|-----------------|--------|-----------------------------------|
| `id`            | INTEGER| PRIMARY KEY, AUTOINCREMENT        |
| `descripcion`   | TEXT   | NOT NULL                          |
| `estado`        | TEXT   | NOT NULL (pendiente, en_progreso, completada) |
| `prioridad`     | TEXT   | NULL (baja, media, alta)          |
| `proyecto_id`   | INTEGER| NOT NULL, FOREIGN KEY (proyectos.id) ON DELETE CASCADE |
| `fecha_creacion`| TEXT   | NOT NULL (formato ISO 8601)       |

## Relaciones entre Tablas
- **Relación Uno a Muchos**: Un proyecto puede tener múltiples tareas asociadas, pero cada tarea pertenece a un único proyecto. Esto se implementa mediante la columna `proyecto_id` en la tabla `tareas`, que es una clave foránea que referencia `proyectos.id`.
- **Integridad Referencial**: La restricción `FOREIGN KEY (proyecto_id) REFERENCES proyectos(id)` asegura que no se puedan crear tareas para proyectos inexistentes. Además, `ON DELETE CASCADE` elimina automáticamente todas las tareas asociadas a un proyecto cuando este se elimina, manteniendo la consistencia de los datos.
- **Movilidad de Tareas**: Una tarea puede cambiar de proyecto actualizando su campo `proyecto_id`, siempre que el nuevo proyecto exista en la tabla `proyectos`.

## Ejemplos de Requests

A continuación, se presentan ejemplos de requests para cada endpoint, incluyendo el comando `curl` y el cuerpo JSON correspondiente.

### 1. Crear un Proyecto (`POST /proyectos`)
**JSON**:
```json
{
  "nombre": "Proyecto Alpha",
  "descripcion": "Proyecto de prueba"
}
```
**Curl**:
```bash
curl -X POST "http://127.0.0.1:8000/proyectos" \
-H "Content-Type: application/json" \
-d '{"nombre": "Proyecto Alpha", "descripcion": "Proyecto de prueba"}'
```
**Respuesta**:
```json
{
  "id": 1,
  "nombre": "Proyecto Alpha",
  "descripcion": "Proyecto de prueba",
  "fecha_creacion": "2025-10-30T11:07:00.123456+00:00"
}
```

### 2. Listar Proyectos (`GET /proyectos`)
**Parámetros Opcionales**:
- `nombre`: Filtra proyectos cuyo nombre contenga el texto (insensible a mayúsculas).
**Curl** (con filtro):
```bash
curl "http://127.0.0.1:8000/proyectos?nombre=alpha"
```
**Respuesta**:
```json
[
  {
    "id": 1,
    "nombre": "Proyecto Alpha",
    "descripcion": "Proyecto de prueba",
    "fecha_creacion": "2025-10-30T11:07:00.123456+00:00"
  }
]
```

### 3. Obtener Proyecto Específico (`GET /proyectos/{id}`)
**Curl**:
```bash
curl "http://127.0.0.1:8000/proyectos/1"
```
**Respuesta**:
```json
{
  "id": 1,
  "nombre": "Proyecto Alpha",
  "descripcion": "Proyecto de prueba",
  "fecha_creacion": "2025-10-30T11:07:00.123456+00:00",
  "total_tareas": 2
}
```

### 4. Actualizar Proyecto (`PUT /proyectos/{id}`)
**JSON**:
```json
{
  "nombre": "Proyecto Alpha Modificado",
  "descripcion": "Descripción actualizada"
}
```
**Curl**:
```bash
curl -X PUT "http://127.0.0.1:8000/proyectos/1" \
-H "Content-Type: application/json" \
-d '{"nombre": "Proyecto Alpha Modificado", "descripcion": "Descripción actualizada"}'
```
**Respuesta**:
```json
{
  "id": 1,
  "nombre": "Proyecto Alpha Modificado",
  "descripcion": "Descripción actualizada",
  "fecha_creacion": "2025-10-30T11:07:00.123456+00:00",
  "total_tareas": 2
}
```

### 5. Eliminar Proyecto (`DELETE /proyectos/{id}`)
**Curl**:
```bash
curl -X DELETE "http://127.0.0.1:8000/proyectos/1"
```
**Respuesta**:
```json
{
  "mensaje": "Proyecto eliminado",
  "tareas_eliminadas": 2
}
```

### 6. Crear Tarea en Proyecto (`POST /proyectos/{id}/tareas`)
**JSON**:
```json
{
  "descripcion": "Tarea importante",
  "estado": "pendiente",
  "prioridad": "alta"
}
```
**Curl**:
```bash
curl -X POST "http://127.0.0.1:8000/proyectos/1/tareas" \
-H "Content-Type: application/json" \
-d '{"descripcion": "Tarea importante", "estado": "pendiente", "prioridad": "alta"}'
```
**Respuesta**:
```json
{
  "id": 1,
  "descripcion": "Tarea importante",
  "estado": "pendiente",
  "prioridad": "alta",
  "proyecto_id": 1,
  "fecha_creacion": "2025-10-30T11:08:00.123456+00:00"
}
```

### 7. Listar Tareas de un Proyecto (`GET /proyectos/{id}/tareas`)
**Parámetros Opcionales**:
- `estado`: Filtra por estado (`pendiente`, `en_progreso`, `completada`).
- `prioridad`: Filtra por prioridad (`baja`, `media`, `alta`).
- `texto`: Busca en la descripción.
- `orden`: Ordena por fecha de creación (`asc` o `desc`).
**Curl** (con filtros):
```bash
curl "http://127.0.0.1:8000/proyectos/1/tareas?estado=pendiente&prioridad=alta&texto=importante&orden=desc"
```
**Respuesta**:
```json
[
  {
    "id": 1,
    "descripcion": "Tarea importante",
    "estado": "pendiente",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-30T11:08:00.123456+00:00"
  }
]
```

### 8. Listar Todas las Tareas (`GET /tareas`)
**Parámetros Opcionales**:
- `proyecto_id`: Filtra por ID de proyecto.
- `estado`, `prioridad`, `texto`, `orden`: Igual que en `/proyectos/{id}/tareas`.
**Curl** (con filtros):
```bash
curl "http://127.0.0.1:8000/tareas?proyecto_id=1&estado=pendiente&prioridad=alta"
```
**Respuesta**:
```json
[
  {
    "id": 1,
    "descripcion": "Tarea importante",
    "estado": "pendiente",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-30T11:08:00.123456+00:00"
  }
]
```

### 9. Actualizar Tarea (`PUT /tareas/{id}`)
**JSON**:
```json
{
  "descripcion": "Tarea actualizada",
  "estado": "completada",
  "prioridad": "media",
  "proyecto_id": 2
}
```
**Curl**:
```bash
curl -X PUT "http://127.0.0.1:8000/tareas/1" \
-H "Content-Type: application/json" \
-d '{"descripcion": "Tarea actualizada", "estado": "completada", "prioridad": "media", "proyecto_id": 2}'
```
**Respuesta**:
```json
{
  "id": 1,
  "descripcion": "Tarea actualizada",
  "estado": "completada",
  "prioridad": "media",
  "proyecto_id": 2,
  "fecha_creacion": "2025-10-30T11:08:00.123456+00:00"
}
```

### 10. Eliminar Tarea (`DELETE /tareas/{id}`)
**Curl**:
```bash
curl -X DELETE "http://127.0.0.1:8000/tareas/1"
```
**Respuesta**:
```json
{
  "mensaje": "Tarea eliminada"
}
```

### 11. Resumen de Proyecto (`GET /proyectos/{id}/resumen`)
**Curl**:
```bash
curl "http://127.0.0.1:8000/proyectos/1/resumen"
```
**Respuesta**:
```json
{
  "proyecto_id": 1,
  "proyecto_nombre": "Proyecto Alpha",
  "total_tareas": 2,
  "por_estado": {
    "pendiente": 1,
    "en_progreso": 0,
    "completada": 1
  },
  "por_prioridad": {
    "alta": 1,
    "media": 1,
    "baja": 0
  }
}
```

### 12. Resumen General (`GET /resumen`)
**Curl**:
```bash
curl "http://127.0.0.1:8000/resumen"
```
**Respuesta**:
```json
{
  "total_proyectos": 2,
  "total_tareas": 5,
  "tareas_por_estado": {
    "pendiente": 3,
    "en_progreso": 1,
    "completada": 1
  },
  "proyecto_con_mas_tareas": {
    "id": 1,
    "nombre": "Proyecto Alpha",
    "cantidad_tareas": 3
  }
}
```

## Manejo de Errores
- **404**: Proyecto o tarea no encontrada. Ejemplo: `{"detail": {"error": "Proyecto no encontrado"}}`
- **400**: Datos inválidos (ej. `proyecto_id` inexistente). Ejemplo: `{"detail": {"error": "Proyecto no encontrado"}}`
- **409**: Conflicto por nombre de proyecto duplicado. Ejemplo: `{"detail": {"error": "Nombre de proyecto duplicado"}}`
- **422**: Validación fallida (ej. descripción vacía, estado o prioridad inválida). Ejemplo: `{"detail": {"error": "Estado inválido"}}`

## Notas
- La API utiliza Pydantic para validar todos los datos de entrada, asegurando que los campos cumplan con las restricciones especificadas.
- Los filtros combinados permiten búsquedas precisas, y el ordenamiento por fecha de creación es configurable (`asc` o `desc`).
- La documentación interactiva en `/docs` facilita probar los endpoints directamente desde el navegador.
- Los tests en `test_TP4.py` verifican todos los requisitos, incluyendo integridad referencial, validaciones y comportamiento de los endpoints..
