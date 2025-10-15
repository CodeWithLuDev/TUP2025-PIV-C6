# TP3 - API de Tareas Persistente con SQLite

# Descripción
Esta es una API construida con FastAPI que gestiona tareas de forma persistente usando una base de datos SQLite (`tareas.db`). Las tareas incluyen descripción, estado ("pendiente", "en_progreso", "completada"), prioridad ("baja", "media", "alta") y fecha de creación.

##Requisitos
- Python 3.8+
- Instalar dependencias: `pip install fastapi uvicorn pydantic sqlite3` (sqlite3 viene por defecto en Python).

# Cómo iniciar el servidor
Ejecuta el siguiente comando en la carpeta del proyecto: uvicorn main:app --reload

El servidor estará disponible en `http://127.0.0.1:8000`. Accede a la documentación interactiva en `http://127.0.0.1:8000/docs`.

## Endpoints disponibles

# GET /tareas
Devuelve todas las tareas. Filtros opcionales:
- ?estado=pendiente (filtra por estado)
- ?texto=algo (busca en descripción)
- ?prioridad=alta (filtra por prioridad)
- ?orden=desc (ordena por fecha_creacion: asc o desc)

Ejemplo de request: `curl http://127.0.0.1:8000/tareas?estado=pendiente`

# POST /tareas
Crea una nueva tarea. Body JSON requerido: {
"descripcion": "Hacer la compra",
"estado": "pendiente",
"prioridad": "media"
}

Ejemplo: `curl -X POST -H "Content-Type: application/json" -d '{"descripcion":"Hacer la compra","estado":"pendiente","prioridad":"media"}' http://127.0.0.1:8000/tareas`

# PUT /tareas/{id}
Actualiza una tarea existente. Body JSON con campos opcionales.
Ejemplo: `curl -X PUT -H "Content-Type: application/json" -d '{"estado":"completada"}' http://127.0.0.1:8000/tareas/1`

# DELETE /tareas/{id}
Elimina una tarea.
Ejemplo: `curl -X DELETE http://127.0.0.1:8000/tareas/1`

# GET /tareas/resumen
Devuelve un resumen de conteo de tareas por estado.
Ejemplo: `curl http://127.0.0.1:8000/tareas/resumen`

# Verificación de persistencia
- Crea tareas con POST.
- Detén el servidor (Ctrl+C).
- Reinicia y verifica con GET /tareas que las tareas persisten.