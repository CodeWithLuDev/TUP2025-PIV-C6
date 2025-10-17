TP3 - API de Tareas Persistente con SQLite
Descripción
API REST desarrollada con FastAPI que permite gestionar tareas de forma persistente usando SQLite como base de datos. Este proyecto es una evolución del TP2, donde los datos ahora persisten en disco.
Requisitos

Python 3.7 o superior
FastAPI
Uvicorn

Instalación

Instalar las dependencias:

bashpip install fastapi uvicorn

Para ejecutar los tests:

bashpip install pytest httpx
Ejecución
Iniciar el servidor:
bashuvicorn main:app --reload
El servidor estará disponible en: http://localhost:8000
Documentación interactiva

Swagger UI: http://localhost:8000/docs
ReDoc: http://localhost:8000/redoc

Estructura de la Base de Datos
La aplicación crea automáticamente una base de datos SQLite (tareas.db) con la siguiente estructura:
sqlCREATE TABLE tareas (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    descripcion TEXT NOT NULL,
    estado TEXT NOT NULL,
    prioridad TEXT NOT NULL DEFAULT 'media',
    fecha_creacion TEXT NOT NULL
);
Endpoints
1. Información de la API
GET /
Retorna información general sobre la API y sus endpoints disponibles.
2. Listar todas las tareas
GET /tareas
Parámetros de consulta (Query Params):

estado (opcional): Filtrar por estado (pendiente, en_progreso, completada)
texto (opcional): Buscar tareas que contengan este texto en la descripción
prioridad (opcional): Filtrar por prioridad (baja, media, alta)
orden (opcional): Ordenar por fecha de creación (asc o desc, por defecto desc)

Ejemplos:
bash# Todas las tareas
GET /tareas

# Tareas pendientes
GET /tareas?estado=pendiente

# Tareas de alta prioridad
GET /tareas?prioridad=alta

# Buscar tareas con "estudiar"
GET /tareas?texto=estudiar

# Combinar filtros
GET /tareas?estado=pendiente&prioridad=alta&orden=asc
3. Crear una tarea
POST /tareas
Content-Type: application/json
Body:
json{
  "descripcion": "Completar el TP3",
  "estado": "pendiente",
  "prioridad": "alta"
}
Campos:

descripcion (requerido): Texto no vacío
estado (opcional): pendiente (default), en_progreso, completada
prioridad (opcional): baja, media (default), alta

Respuesta exitosa (201):
json{
  "id": 1,
  "descripcion": "Completar el TP3",
  "estado": "pendiente",
  "prioridad": "alta",
  "fecha_creacion": "2025-10-17T10:30:00.123456"
}
4. Obtener una tarea específica
GET /tareas/{id}
Ejemplo:
bashGET /tareas/1
5. Actualizar una tarea
PUT /tareas/{id}
Content-Type: application/json
Body (todos los campos son opcionales):
json{
  "descripcion": "Nueva descripción",
  "estado": "completada",
  "prioridad": "media"
}
Ejemplos:
bash# Solo cambiar el estado
PUT /tareas/1
{
  "estado": "completada"
}

# Cambiar descripción y prioridad
PUT /tareas/1
{
  "descripcion": "Tarea actualizada",
  "prioridad": "baja"
}
6. Eliminar una tarea
DELETE /tareas/{id}
Ejemplo:
bashDELETE /tareas/1
Respuesta:
json{
  "mensaje": "Tarea eliminada exitosamente",
  "tarea_eliminada": {
    "id": 1,
    "descripcion": "Completar el TP3",
    "estado": "completada",
    "prioridad": "alta",
    "fecha_creacion": "2025-10-17T10:30:00.123456"
  }
}
7. Obtener resumen de tareas
GET /tareas/resumen
Respuesta:
json{
  "total_tareas": 10,
  "por_estado": {
    "pendiente": 3,
    "en_progreso": 2,
    "completada": 5
  },
  "por_prioridad": {
    "baja": 2,
    "media": 4,
    "alta": 4
  }
}
8. Completar todas las tareas
PUT /tareas/completar_todas
Marca todas las tareas como completadas en una sola operación.
Respuesta:
json{
  "mensaje": "Se completaron 5 tareas",
  "total_tareas": 10
}
Ejemplos de uso con cURL
Crear una tarea
bashcurl -X POST http://localhost:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Estudiar FastAPI",
    "estado": "pendiente",
    "prioridad": "alta"
  }'
Listar todas las tareas
bashcurl http://localhost:8000/tareas
Filtrar tareas pendientes de alta prioridad
bashcurl "http://localhost:8000/tareas?estado=pendiente&prioridad=alta"
Actualizar una tarea
bashcurl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'
Eliminar una tarea
bashcurl -X DELETE http://localhost:8000/tareas/1
Ver resumen
bashcurl http://localhost:8000/tareas/resumen
Completar todas las tareas
bashcurl -X PUT http://localhost:8000/tareas/completar_todas
Verificar Persistencia
Para comprobar que los datos persisten:

Crear algunas tareas usando POST /tareas
Detener el servidor (Ctrl+C)
Reiniciar el servidor: uvicorn main:app --reload
Consultar las tareas: GET /tareas
✅ Las tareas seguirán ahí en la base de datos

Ejecutar Tests
Para ejecutar los tests del TP3:
bashpytest test_TP3.py -v
Deberías ver que pasan todos los 27 tests:
test_base_datos_se_crea PASSED
test_tabla_tareas_existe PASSED
test_crear_tarea PASSED
...
test_completar_todas_tareas PASSED
========================= 27 passed =========================
Códigos de Estado HTTP

200 OK: Operación exitosa
201 Created: Recurso creado correctamente
404 Not Found: Tarea no encontrada
422 Unprocessable Entity: Datos de entrada inválidos

Ejemplos de errores
Error 404 (tarea no existe):
json{
  "detail": {
    "error": "La tarea no existe"
  }
}
Error 422 (validación fallida):
json{
  "detail": [
    {
      "loc": ["body", "descripcion"],
      "msg": "La descripción no puede estar vacía",
      "type": "value_error"
    }
  ]
}
Validaciones

✅ La descripción no puede estar vacía ni contener solo espacios
✅ Solo se aceptan los estados: pendiente, en_progreso, completada
✅ Solo se aceptan las prioridades: baja, media, alta
✅ Todos los campos son validados con Pydantic

Notas Importantes

La base de datos tareas.db se crea automáticamente en el mismo directorio que main.py
Los filtros se pueden combinar para búsquedas más específicas
El ordenamiento por fecha permite ver las tareas más recientes primero (desc) o las más antiguas primero (asc)
La validación de datos se realiza automáticamente gracias a Pydantic

Archivos del Proyecto
TP3/
├── main.py          # Código principal de la API
├── test_TP3.py      # Tests automatizados
├── tareas.db        # Base de datos SQLite (se crea automáticamente)
└── README.md        # Este archivo