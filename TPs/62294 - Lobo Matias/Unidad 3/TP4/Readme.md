TP4 - API de Gestión de Tareas y Proyectos
Sistema de gestión que permite organizar tareas dentro de proyectos, implementando relaciones 1:N entre tablas en SQLite.
Novedades del TP4

    Tabla Proyectos: Nueva entidad para agrupar tareas
    Relaciones 1:N: Un proyecto puede tener muchas tareas
    Claves foráneas: Con ON DELETE CASCADE
    Filtros avanzados: Múltiples criterios de búsqueda
    Estadísticas: Resúmenes por proyecto y generales
    Validación Pydantic: Modelos separados en models.py

Estructura de la Base de Datos
Tabla: proyectos
CampoTipoRestriccionesidINTEGERPRIMARY KEY, AUTOINCREMENTnombreTEXTNOT NULL, UNIQUEdescripcionTEXTNULLfecha_creacionTEXTNOT NULL
Tabla: tareas
CampoTipoRestriccionesidINTEGERPRIMARY KEY, AUTOINCREMENTdescripcionTEXTNOT NULLestadoTEXTNOT NULLprioridadTEXTNOT NULLproyecto_idINTEGERFOREIGN KEY → proyectos(id)fecha_creacionTEXTNOT NULL
Relación: Un proyecto → muchas tareas (1:N)
Integridad: Al eliminar un proyecto se eliminan sus tareas automáticamente (CASCADE)
Instalación
bashpip install fastapi uvicorn
Iniciar el servidor
bashuvicorn main:app --reload
O si no funciona:
bashpython -m uvicorn main:app --reload
Servidor disponible en: http://127.0.0.1:8000
Documentación: http://127.0.0.1:8000/docs
Endpoints - Proyectos
1. Listar proyectos
bashGET /proyectos
GET /proyectos?nombre=web  # Filtrar por nombre
2. Obtener proyecto específico
bashGET /proyectos/{id}
Incluye contador de tareas asociadas.
3. Crear proyecto
bashPOST /proyectos
Content-Type: application/json

{
  "nombre": "Proyecto Alpha",
  "descripcion": "Descripción opcional"
}
Ejemplo con curl:
bashcurl -X POST http://127.0.0.1:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Mi Proyecto", "descripcion": "Desarrollo web"}'
4. Actualizar proyecto
bashPUT /proyectos/{id}
Content-Type: application/json

{
  "nombre": "Proyecto Beta",
  "descripcion": "Nueva descripción"
}
5. Eliminar proyecto
bashDELETE /proyectos/{id}
⚠️ Elimina el proyecto y todas sus tareas (CASCADE)
Endpoints - Tareas
1. Listar todas las tareas
bashGET /tareas
GET /tareas?estado=pendiente
GET /tareas?prioridad=alta
GET /tareas?proyecto_id=1
GET /tareas?orden=desc
Filtros combinados:
bashGET /tareas?estado=completada&prioridad=alta&orden=desc
2. Listar tareas de un proyecto
bashGET /proyectos/{id}/tareas
GET /proyectos/{id}/tareas?estado=pendiente
GET /proyectos/{id}/tareas?prioridad=alta&orden=asc
3. Crear tarea en un proyecto
bashPOST /proyectos/{id}/tareas
Content-Type: application/json

{
  "descripcion": "Implementar login",
  "estado": "pendiente",
  "prioridad": "alta"
}
Ejemplo con curl:
bashcurl -X POST http://127.0.0.1:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Diseñar base de datos", "prioridad": "alta"}'
4. Actualizar tarea
bashPUT /tareas/{id}
Content-Type: application/json

{
  "descripcion": "Nueva descripción",
  "estado": "completada",
  "prioridad": "media",
  "proyecto_id": 2  # Mover a otro proyecto
}
5. Eliminar tarea
bashDELETE /tareas/{id}
Endpoints - Resumen y Estadísticas
1. Resumen de un proyecto
bashGET /proyectos/{id}/resumen
Respuesta:
json{
  "proyecto_id": 1,
  "proyecto_nombre": "Proyecto Alpha",
  "total_tareas": 15,
  "por_estado": {
    "pendiente": 5,
    "en_progreso": 7,
    "completada": 3
  },
  "por_prioridad": {
    "baja": 4,
    "media": 8,
    "alta": 3
  }
}
2. Resumen general
bashGET /resumen
Respuesta:
json{
  "total_proyectos": 3,
  "total_tareas": 42,
  "tareas_por_estado": {
    "pendiente": 15,
    "en_progreso": 20,
    "completada": 7
  },
  "proyecto_con_mas_tareas": {
    "id": 1,
    "nombre": "Proyecto Alpha",
    "cantidad_tareas": 15
  }
}
Ejemplos de Uso Completo
Escenario 1: Crear proyecto con tareas
bash# 1. Crear proyecto
curl -X POST http://127.0.0.1:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Desarrollo Web", "descripcion": "Sitio corporativo"}'

# Respuesta: {"id": 1, ...}

# 2. Agregar tareas al proyecto
curl -X POST http://127.0.0.1:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Diseñar mockups", "prioridad": "alta"}'

curl -X POST http://127.0.0.1:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Configurar servidor", "prioridad": "media"}'

# 3. Ver todas las tareas del proyecto
curl http://127.0.0.1:8000/proyectos/1/tareas

# 4. Ver resumen del proyecto
curl http://127.0.0.1:8000/proyectos/1/resumen
Escenario 2: Mover tarea entre proyectos
bash# 1. Crear dos proyectos
curl -X POST http://127.0.0.1:8000/proyectos \
  -d '{"nombre": "Proyecto A"}'

curl -X POST http://127.0.0.1:8000/proyectos \
  -d '{"nombre": "Proyecto B"}'

# 2. Crear tarea en Proyecto A (id=1)
curl -X POST http://127.0.0.1:8000/proyectos/1/tareas \
  -d '{"descripcion": "Tarea a mover"}'
# Respuesta: {"id": 1, "proyecto_id": 1, ...}

# 3. Mover tarea al Proyecto B (id=2)
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id": 2}'

# 4. Verificar que la tarea está en Proyecto B
curl http://127.0.0.1:8000/proyectos/2/tareas
Escenario 3: Filtros avanzados
bash# Buscar todas las tareas completadas de prioridad alta
curl "http://127.0.0.1:8000/tareas?estado=completada&prioridad=alta"

# Buscar tareas pendientes del proyecto 1, ordenadas por fecha
curl "http://127.0.0.1:8000/proyectos/1/tareas?estado=pendiente&orden=desc"

# Buscar proyectos que contengan "web" en el nombre
curl "http://127.0.0.1:8000/proyectos?nombre=web"
Validaciones Implementadas
Proyectos

✅ Nombre no puede estar vacío
✅ Nombre debe ser único
✅ Descripción es opcional

Tareas

✅ Descripción no puede estar vacía
✅ Estados válidos: pendiente, en_progreso, completada
✅ Prioridades válidas: baja, media, alta
✅ El proyecto_id debe existir

Códigos de Estado HTTP

200 OK: Operación exitosa
201 Created: Recurso creado exitosamente
400 Bad Request: Datos inválidos (ej: proyecto_id inexistente)
404 Not Found: Recurso no encontrado
409 Conflict: Conflicto (ej: nombre de proyecto duplicado)
422 Unprocessable Entity: Error de validación Pydantic

Integridad Referencial
ON DELETE CASCADE
Al eliminar un proyecto, todas sus tareas se eliminan automáticamente:
bash# Crear proyecto con tareas
curl -X POST http://127.0.0.1:8000/proyectos -d '{"nombre": "Test"}'
curl -X POST http://127.0.0.1:8000/proyectos/1/tareas -d '{"descripcion": "Tarea 1"}'
curl -X POST http://127.0.0.1:8000/proyectos/1/tareas -d '{"descripcion": "Tarea 2"}'

# Eliminar proyecto (elimina también las 2 tareas)
curl -X DELETE http://127.0.0.1:8000/proyectos/1
# Respuesta: {"mensaje": "Proyecto eliminado", "tareas_eliminadas": 2}
Validación de existencia
No se puede crear una tarea en un proyecto inexistente:
bashcurl -X POST http://127.0.0.1:8000/proyectos/999/tareas \
  -d '{"descripcion": "Tarea huérfana"}'
# Respuesta: 400 Bad Request - "El proyecto no existe"
Estructura del Proyecto
TP4/
├── main.py          # API principal con todos los endpoints
├── models.py        # Modelos Pydantic para validación
├── tareas.db        # Base de datos SQLite (se crea automáticamente)
├── README.md        # Este archivo
└── test_TP4.py      # Tests automatizados
Ejecutar Tests
bashpytest test_TP4.py -v
Para ver más detalles:
bashpytest test_TP4.py -v -s
Diferencias con el TP3
CaracterísticaTP3TP4Tablas1 (tareas)2 (proyectos + tareas)RelacionesSin relaciones1:N con FKOrganizaciónTareas sueltasTareas en proyectosCascade DeleteNo aplicaSí (ON DELETE CASCADE)FiltrosPor estado/prioridad+ por proyecto_idResumenSolo tareasPor proyecto y generalModelosEn main.pySeparados en models.py
Diagrama de Relaciones
┌─────────────────┐         ┌─────────────────┐
│   proyectos     │         │     tareas      │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │◄────────│ id (PK)         │
│ nombre (UNIQUE) │    1:N  │ descripcion     │
│ descripcion     │         │ estado          │
│ fecha_creacion  │         │ prioridad       │
└─────────────────┘         │ proyecto_id (FK)│
                            │ fecha_creacion  │
                            └─────────────────┘
Notas Adicionales

Las claves foráneas están habilitadas con PRAGMA foreign_keys = ON
Los IDs se generan automáticamente (AUTOINCREMENT)
Las fechas se almacenan en formato ISO 8601
El campo descripcion de proyectos puede ser NULL
Los filtros en query params pueden combinarse libremente


Autor: Matías Lobo - Legajo 62294
Fecha: Octubre 2025
Tecnologías: FastAPI, SQLite, Pydantic, Uvicorn