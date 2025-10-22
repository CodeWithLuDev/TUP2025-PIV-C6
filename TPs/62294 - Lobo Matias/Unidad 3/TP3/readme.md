TP3 - API de Gestión de Tareas con SQLite

API REST para gestionar tareas con persistencia en base de datos. Los datos ahora se guardan en tareas.db y no se pierden al reiniciar el servidor.

Instalación
Instalar las dependencias necesarias:
bashpip install fastapi uvicorn

Iniciar el servidor
bashuvicorn main:app --reload
O si no funciona el comando anterior:
bashpython -m uvicorn main:app --reload
El servidor arranca en: http://127.0.0.1:8000
Podés ver la documentación interactiva en: http://127.0.0.1:8000/docs

Endpoints principales
Ver todas las tareas
bashGET /tareas

Filtros disponibles:

?estado=pendiente - Filtrar por estado (pendiente, en_progreso, completada)
?prioridad=alta - Filtrar por prioridad (baja, media, alta)
?texto=comprar - Buscar en la descripción
?orden=desc - Ordenar por fecha (asc o desc)

Ejemplo:
bashcurl http://127.0.0.1:8000/tareas?estado=pendiente&prioridad=alta

Crear una tarea
bashPOST /tareas
Enviar JSON con la descripción (obligatorio), estado y prioridad (opcionales):
bashcurl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Estudiar para el parcial", "prioridad": "alta"}'

Actualizar una tarea
bashPUT /tareas/{id}

Ejemplo:
bashcurl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'

Eliminar una tarea
bashDELETE /tareas/{id}

Ver resumen
bashGET /tareas/resumen
Devuelve el total de tareas y cantidad por estado y prioridad.
Completar todas
bashPUT /tareas/completar_todas
Marca todas las tareas como completadas.
Validaciones

La descripción no puede estar vacía
Estados válidos: pendiente, en_progreso, completada
Prioridades válidas: baja, media, alta

Base de datos
El archivo tareas.db se crea automáticamente al iniciar el servidor. Contiene una tabla tareas con las columnas:

id (auto incremental)
descripcion
estado
fecha_creacion
prioridad

Ejecutar tests
bashpytest test_TP3.py -v

Diferencias con el TP2

Ahora usa SQLite en lugar de una lista en memoria
Los datos persisten al reiniciar el servidor
Se agregó el campo "prioridad" con filtro
Nuevo filtro de ordenamiento por fecha
Endpoint de resumen mejorado con estadísticas de prioridad


Autor: Matías Lobo - Legajo 62294
Tecnologías: FastAPI, SQLite, Pydantic, Uvicorn