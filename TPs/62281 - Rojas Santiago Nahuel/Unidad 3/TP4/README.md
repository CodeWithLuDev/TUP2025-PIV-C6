# tp4 - relaciones entre tablas y filtros avanzados

api de gestion de proyectos y tareas con persistencia en sqlite, implementando relaciones 1:n y filtros avanzados.

---

## tabla de contenidos

1. [descripcion del proyecto](#descripcion-del-proyecto)
2. [estructura de la base de datos](#estructura-de-la-base-de-datos)
3. [instrucciones para iniciar el servidor](#instrucciones-para-iniciar-el-servidor)
4. [ejemplos de requests para cada endpoint](#ejemplos-de-requests-para-cada-endpoint)
5. [explicacion de relaciones entre tablas](#explicacion-de-relaciones-entre-tablas)
6. [manejo de errores](#manejo-de-errores)
7. [verificacion de integridad referencial](#verificacion-de-integridad-referencial)

---

## descripcion del proyecto

este proyecto implementa una api restful con fastapi que permite gestionar proyectos y sus tareas asociadas. utiliza sqlite como base de datos con relaciones entre tablas mediante claves foraneas, implementando un modelo de relacion 1:n (uno a muchos) donde un proyecto puede tener multiples tareas.

### funcionalidades principales

- crud completo de proyectos
- crud completo de tareas
- relacion 1:n entre proyectos y tareas
- filtros avanzados (estado, prioridad, proyecto, orden)
- endpoints de resumen y estadisticas
- validacion de datos con pydantic
- integridad referencial con on delete cascade

---

## estructura de la base de datos

### diagrama de relaciones

```
┌─────────────────────────────────────┐
│           proyectos                 │
├─────────────────────────────────────┤
│ id (pk, autoincrement)              │
│ nombre (text, not null, unique)     │
│ descripcion (text, nullable)        │
│ fecha_creacion (text, not null)     │
└───────────────┬─────────────────────┘
                │
                │ 1:n (uno a muchos)
                │ on delete cascade
                │
                ↓
┌─────────────────────────────────────┐
│              tareas                 │
├─────────────────────────────────────┤
│ id (pk, autoincrement)              │
│ descripcion (text, not null)        │
│ estado (text, not null)             │
│ prioridad (text, not null)          │
│ proyecto_id (fk, not null)          │
│ fecha_creacion (text, not null)     │
└─────────────────────────────────────┘
```

### tabla proyectos

| campo          | tipo    | restricciones              | descripcion                          |
|---------------|---------|----------------------------|--------------------------------------|
| id            | integer | primary key, autoincrement | identificador unico del proyecto     |
| nombre        | text    | not null, unique           | nombre del proyecto (debe ser unico) |
| descripcion   | text    | nullable                   | descripcion opcional del proyecto    |
| fecha_creacion| text    | not null                   | fecha y hora de creacion (iso format)|

### tabla tareas

| campo          | tipo    | restricciones                          | descripcion                          |
|---------------|---------|----------------------------------------|--------------------------------------|
| id            | integer | primary key, autoincrement             | identificador unico de la tarea      |
| descripcion   | text    | not null                               | descripcion de la tarea              |
| estado        | text    | not null                               | pendiente, en_progreso o completada  |
| prioridad     | text    | not null                               | baja, media o alta                   |
| proyecto_id   | integer | foreign key, not null                  | referencia al proyecto padre         |
| fecha_creacion| text    | not null                               | fecha y hora de creacion (iso format)|

**constraint de clave foranea:**
```sql
foreign key (proyecto_id) references proyectos(id) on delete cascade
```

---

## instrucciones para iniciar el servidor

### requisitos previos

- python 3.8 o superior
- pip (gestor de paquetes de python)

### paso 1: instalar dependencias

primero, instala todas las dependencias necesarias del proyecto:

```bash
pip install -r requirements.txt
```

esto instalara:
- fastapi (framework web)
- uvicorn (servidor asgi)
- pydantic (validacion de datos)
- pytest (testing)
- httpx (cliente http para tests)

### paso 2: inicializar base de datos (opcional)

si deseas crear la base de datos con datos de prueba, ejecuta:

```bash
python database.py
```

esto creara:
- 3 proyectos de ejemplo (proyecto alpha, beta, gamma)
- 10 tareas distribuidas entre los proyectos

**nota:** si no ejecutas este paso, la base de datos se creara automaticamente vacia al iniciar el servidor.

### paso 3: iniciar el servidor

inicia el servidor de desarrollo con recarga automatica:

```bash
uvicorn main:app --reload
```

el servidor estara disponible en: **http://127.0.0.1:8000**

opciones adicionales:
```bash
uvicorn main:app --reload --host 0.0.0.0 --port 8080
```

### paso 4: verificar que funciona

abre tu navegador en:
- api base: http://127.0.0.1:8000
- documentacion swagger: http://127.0.0.1:8000/docs
- documentacion redoc: http://127.0.0.1:8000/redoc

### paso 5: ejecutar tests (opcional)

para verificar que todo funciona correctamente:

```bash
pytest test_main.py -v
```

para ver cobertura de tests:
```bash
pytest test_main.py -v --cov
```

---

## ejemplos de requests para cada endpoint

### endpoints de proyectos

#### 1. listar todos los proyectos

**request:**
```bash
curl -X GET "http://127.0.0.1:8000/proyectos"
```

**response:**
```json
[
  {
    "id": 1,
    "nombre": "proyecto alpha",
    "descripcion": "primer proyecto de prueba",
    "fecha_creacion": "2025-10-23T10:30:00.123456"
  },
  {
    "id": 2,
    "nombre": "proyecto beta",
    "descripcion": "segundo proyecto de prueba",
    "fecha_creacion": "2025-10-23T11:00:00.123456"
  }
]
```

#### 2. listar proyectos con filtro por nombre

**request:**
```bash
curl -X GET "http://127.0.0.1:8000/proyectos?nombre=alpha"
```

**response:**
```json
[
  {
    "id": 1,
    "nombre": "proyecto alpha",
    "descripcion": "primer proyecto de prueba",
    "fecha_creacion": "2025-10-23T10:30:00.123456"
  }
]
```

#### 3. obtener un proyecto especifico

**request:**
```bash
curl -X GET "http://127.0.0.1:8000/proyectos/1"
```

**response:**
```json
{
  "id": 1,
  "nombre": "proyecto alpha",
  "descripcion": "primer proyecto de prueba",
  "fecha_creacion": "2025-10-23T10:30:00.123456",
  "total_tareas": 5
}
```

#### 4. crear un nuevo proyecto

**request:**
```bash
curl -X POST "http://127.0.0.1:8000/proyectos" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "proyecto delta",
    "descripcion": "cuarto proyecto de prueba"
  }'
```

**body json:**
```json
{
  "nombre": "proyecto delta",
  "descripcion": "cuarto proyecto de prueba"
}
```

**response:**
```json
{
  "id": 4,
  "nombre": "proyecto delta",
  "descripcion": "cuarto proyecto de prueba",
  "fecha_creacion": "2025-10-23T12:00:00.123456"
}
```

#### 5. modificar un proyecto

**request:**
```bash
curl -X PUT "http://127.0.0.1:8000/proyectos/1" \
  -H "Content-Type: application/json" \
  -d '{
    "nombre": "proyecto alpha modificado",
    "descripcion": "descripcion actualizada"
  }'
```

**body json:**
```json
{
  "nombre": "proyecto alpha modificado",
  "descripcion": "descripcion actualizada"
}
```

**response:**
```json
{
  "id": 1,
  "nombre": "proyecto alpha modificado",
  "descripcion": "descripcion actualizada",
  "fecha_creacion": "2025-10-23T10:30:00.123456"
}
```

#### 6. eliminar un proyecto

**request:**
```bash
curl -X DELETE "http://127.0.0.1:8000/proyectos/1"
```

**response:**
```json
{
  "mensaje": "proyecto eliminado exitosamente"
}
```

**nota importante:** al eliminar un proyecto, todas sus tareas asociadas se eliminan automaticamente debido a on delete cascade.

---

### endpoints de tareas

#### 7. listar todas las tareas

**request:**
```bash
curl -X GET "http://127.0.0.1:8000/tareas"
```

**response:**
```json
[
  {
    "id": 1,
    "descripcion": "implementar login",
    "estado": "pendiente",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-23T10:30:00.123456"
  },
  {
    "id": 2,
    "descripcion": "diseñar base de datos",
    "estado": "completada",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-23T10:35:00.123456"
  }
]
```

#### 8. listar tareas con filtro por estado

**request:**
```bash
curl -X GET "http://127.0.0.1:8000/tareas?estado=pendiente"
```

**response:**
```json
[
  {
    "id": 1,
    "descripcion": "implementar login",
    "estado": "pendiente",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-23T10:30:00.123456"
  }
]
```

#### 9. listar tareas con filtro por prioridad

**request:**
```bash
curl -X GET "http://127.0.0.1:8000/tareas?prioridad=alta"
```

**response:**
```json
[
  {
    "id": 1,
    "descripcion": "implementar login",
    "estado": "pendiente",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-23T10:30:00.123456"
  }
]
```

#### 10. listar tareas con filtro por proyecto

**request:**
```bash
curl -X GET "http://127.0.0.1:8000/tareas?proyecto_id=1"
```

**response:**
```json
[
  {
    "id": 1,
    "descripcion": "implementar login",
    "estado": "pendiente",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-23T10:30:00.123456"
  }
]
```

#### 11. listar tareas con multiples filtros

**request:**
```bash
curl -X GET "http://127.0.0.1:8000/tareas?estado=completada&prioridad=alta"
```

**response:**
```json
[
  {
    "id": 2,
    "descripcion": "diseñar base de datos",
    "estado": "completada",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-23T10:35:00.123456"
  }
]
```

#### 12. listar tareas con orden descendente

**request:**
```bash
curl -X GET "http://127.0.0.1:8000/tareas?orden=desc"
```

**response:**
```json
[
  {
    "id": 10,
    "descripcion": "refactorizar codigo",
    "estado": "pendiente",
    "prioridad": "media",
    "proyecto_id": 3,
    "fecha_creacion": "2025-10-23T11:50:00.123456"
  },
  {
    "id": 9,
    "descripcion": "optimizar queries",
    "estado": "pendiente",
    "prioridad": "baja",
    "proyecto_id": 3,
    "fecha_creacion": "2025-10-23T11:45:00.123456"
  }
]
```

#### 13. listar tareas de un proyecto especifico

**request:**
```bash
curl -X GET "http://127.0.0.1:8000/proyectos/1/tareas"
```

**response:**
```json
[
  {
    "id": 1,
    "descripcion": "implementar login",
    "estado": "pendiente",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-23T10:30:00.123456"
  },
  {
    "id": 2,
    "descripcion": "diseñar base de datos",
    "estado": "completada",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-23T10:35:00.123456"
  }
]
```

#### 14. listar tareas de un proyecto con filtros

**request:**
```bash
curl -X GET "http://127.0.0.1:8000/proyectos/1/tareas?estado=pendiente&prioridad=alta"
```

**response:**
```json
[
  {
    "id": 1,
    "descripcion": "implementar login",
    "estado": "pendiente",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-23T10:30:00.123456"
  }
]
```

#### 15. crear una tarea en un proyecto

**request:**
```bash
curl -X POST "http://127.0.0.1:8000/proyectos/1/tareas" \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "implementar autenticacion oauth",
    "estado": "pendiente",
    "prioridad": "alta"
  }'
```

**body json:**
```json
{
  "descripcion": "implementar autenticacion oauth",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**response:**
```json
{
  "id": 11,
  "descripcion": "implementar autenticacion oauth",
  "estado": "pendiente",
  "prioridad": "alta",
  "proyecto_id": 1,
  "fecha_creacion": "2025-10-23T13:00:00.123456"
}
```

#### 16. modificar una tarea

**request:**
```bash
curl -X PUT "http://127.0.0.1:8000/tareas/1" \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "implementar login con jwt",
    "estado": "en_progreso",
    "prioridad": "alta"
  }'
```

**body json:**
```json
{
  "descripcion": "implementar login con jwt",
  "estado": "en_progreso",
  "prioridad": "alta"
}
```

**response:**
```json
{
  "id": 1,
  "descripcion": "implementar login con jwt",
  "estado": "en_progreso",
  "prioridad": "alta",
  "proyecto_id": 1,
  "fecha_creacion": "2025-10-23T10:30:00.123456"
}
```

#### 17. mover una tarea a otro proyecto

**request:**
```bash
curl -X PUT "http://127.0.0.1:8000/tareas/1" \
  -H "Content-Type: application/json" \
  -d '{
    "proyecto_id": 2
  }'
```

**body json:**
```json
{
  "proyecto_id": 2
}
```

**response:**
```json
{
  "id": 1,
  "descripcion": "implementar login",
  "estado": "pendiente",
  "prioridad": "alta",
  "proyecto_id": 2,
  "fecha_creacion": "2025-10-23T10:30:00.123456"
}
```

#### 18. eliminar una tarea

**request:**
```bash
curl -X DELETE "http://127.0.0.1:8000/tareas/1"
```

**response:**
```json
{
  "mensaje": "tarea eliminada exitosamente"
}
```

---

### endpoints de resumen y estadisticas

#### 19. obtener resumen de un proyecto

**request:**
```bash
curl -X GET "http://127.0.0.1:8000/proyectos/1/resumen"
```

**response:**
```json
{
  "proyecto_id": 1,
  "proyecto_nombre": "proyecto alpha",
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
```

#### 20. obtener resumen general

**request:**
```bash
curl -X GET "http://127.0.0.1:8000/resumen"
```

**response:**
```json
{
  "total_proyectos": 3,
  "total_tareas": 42,
  "tareas_por_estado": {
    "pendiente": 15,
    "en_progreso": 20,
    "completada": 7
  },
  "proyecto_con_mas_tareas": {
    "id": 1,
    "nombre": "proyecto alpha",
    "cantidad_tareas": 15
  }
}
```

---

## explicacion de relaciones entre tablas

### concepto de relacion 1:n (uno a muchos)

la base de datos implementa una relacion **uno a muchos** entre las tablas `proyectos` y `tareas`:

```
1 proyecto → muchas tareas
1 tarea    → 1 proyecto
```

### implementacion tecnica

#### 1. clave foranea (foreign key)

la tabla `tareas` contiene una columna `proyecto_id` que es una **clave foranea** que referencia a la columna `id` de la tabla `proyectos`:

```sql
foreign key (proyecto_id) references proyectos(id)
```

esto significa que:
- cada tarea **debe** estar asociada a un proyecto existente
- no se puede crear una tarea con un `proyecto_id` que no existe en la tabla proyectos
- sqlite valida automaticamente esta restriccion

#### 2. on delete cascade

la clave foranea incluye la clausula `on delete cascade`:

```sql
foreign key (proyecto_id) references proyectos(id) on delete cascade
```

**que hace esto:**
- cuando se elimina un proyecto de la tabla `proyectos`
- automaticamente se eliminan **todas las tareas** asociadas a ese proyecto
- no es necesario eliminar manualmente las tareas primero
- mantiene la integridad referencial de la base de datos

**ejemplo practico:**

```
estado inicial:
  proyecto id=1 "proyecto alpha"
    ├── tarea id=1 "implementar login"
    ├── tarea id=2 "diseñar bd"
    └── tarea id=3 "crear api"

ejecutar: delete from proyectos where id = 1

estado final:
  (proyecto eliminado)
  (tarea id=1 eliminada automaticamente)
  (tarea id=2 eliminada automaticamente)
  (tarea id=3 eliminada automaticamente)
```

#### 3. validacion de integridad

**al crear una tarea:**
```python
cursor.execute("select id from proyectos where id = ?", (proyecto_id,))
if not cursor.fetchone():
    raise httpexception(status_code=400, detail="el proyecto especificado no existe")
```

antes de crear una tarea, el sistema verifica que el `proyecto_id` exista en la tabla proyectos. si no existe, devuelve un error 400.

**al mover una tarea a otro proyecto:**
```python
if tarea.proyecto_id:
    cursor.execute("select id from proyectos where id = ?", (tarea.proyecto_id,))
    if not cursor.fetchone():
        raise httpexception(status_code=400, detail="el proyecto especificado no existe")
```

### ventajas de esta implementacion

1. **integridad de datos:** garantiza que no existan tareas huerfanas (sin proyecto)
2. **eliminacion en cascada:** simplifica la eliminacion de proyectos
3. **consultas eficientes:** permite hacer joins entre tablas
4. **validacion automatica:** sqlite valida las restricciones

### consultas con join (ejemplo interno)

aunque la api devuelve datos por separado, internamente se pueden hacer consultas que combinen ambas tablas:

```sql
select 
  p.nombre as proyecto_nombre,
  t.descripcion as tarea_descripcion,
  t.estado,
  t.prioridad
from proyectos p
inner join tareas t on p.id = t.proyecto_id
where p.id = 1;
```

esto se usa en el endpoint `/proyectos/{id}/resumen` para calcular estadisticas.

---

## manejo de errores

la api implementa respuestas de error apropiadas para diferentes situaciones:

### errores 404 (not found)

**cuando ocurre:**
- se intenta obtener un proyecto que no existe
- se intenta obtener una tarea que no existe
- se intenta listar tareas de un proyecto inexistente

**ejemplo:**
```json
{
  "detail": "proyecto no encontrado"
}
```

### errores 400 (bad request)

**cuando ocurre:**
- el nombre del proyecto esta vacio
- la descripcion de la tarea esta vacia
- se intenta crear una tarea con un proyecto_id inexistente

**ejemplo:**
```json
{
  "detail": "el nombre del proyecto no puede estar vacio"
}
```

### errores 409 (conflict)

**cuando ocurre:**
- se intenta crear un proyecto con un nombre que ya existe

**ejemplo:**
```json
{
  "detail": "ya existe un proyecto con ese nombre"
}
```

### errores 422 (validation error)

**cuando ocurre:**
- los datos enviados no cumplen con el schema pydantic
- estado o prioridad invalidos

**ejemplo:**
```json
{
  "detail": [
    {
      "loc": ["body", "estado"],
      "msg": "value is not a valid enumeration member; permitted: 'pendiente', 'en_progreso', 'completada'",
      "type": "type_error.enum"
    }
  ]
}
```

---

## verificacion de integridad referencial

### escenarios de prueba

#### 1. crear proyecto y agregar tareas

```bash
# paso 1: crear proyecto
curl -X POST "http://127.0.0.1:8000/proyectos" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "proyecto test"}'

# respuesta: {"id": 1, ...}

# paso 2: agregar tareas
curl -X POST "http://127.0.0.1:8000/proyectos/1/tareas" \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "tarea 1", "estado": "pendiente", "prioridad": "alta"}'

curl -X POST "http://127.0.0.1:8000/proyectos/1/tareas" \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "tarea 2", "estado": "pendiente", "prioridad": "media"}'

# verificar tareas creadas
curl -X GET "http://127.0.0.1:8000/proyectos/1/tareas"
```

#### 2. intentar crear tarea con proyecto inexistente

```bash
# esto debe fallar con error 400
curl -X POST "http://127.0.0.1:8000/proyectos/9999/tareas" \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "tarea imposible", "estado": "pendiente", "prioridad": "alta"}'

# respuesta esperada:
# {"detail": "el proyecto especificado no existe"}
```

#### 3. eliminar proyecto y verificar cascade

```bash
# paso 1: crear proyecto con tareas
curl -X POST "http://127.0.0.1:8000/proyectos" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "proyecto temporal"}'

# respuesta: {"id": 1, ...}

curl -X POST "http://127.0.0.1:8000/proyectos/1/tareas" \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "tarea temporal", "estado": "pendiente", "prioridad": "alta"}'

# paso 2: verificar que tiene tareas
curl -X GET "http://127.0.0.1:8000/proyectos/1/tareas"
# respuesta: [{"id": 1, "descripcion": "tarea temporal", ...}]

# paso 3: eliminar proyecto
curl -X DELETE "http://127.0.0.1:8000/proyectos/1"
# respuesta: {"mensaje": "proyecto eliminado exitosamente"}

# paso 4: verificar que las tareas tambien se eliminaron
curl -X GET "http://127.0.0.1:8000/tareas"
# respuesta: []
```

#### 4. mover tarea a otro proyecto

```bash
# paso 1: crear dos proyectos
curl -X POST "http://127.0.0.1:8000/proyectos" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "proyecto origen"}'
# respuesta: {"id": 1, ...}

curl -X POST "http://127.0.0.1:8000/proyectos" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "proyecto destino"}'
# respuesta: {"id": 2, ...}

# paso 2: crear tarea en proyecto 1
curl -X POST "http://127.0.0.1:8000/proyectos/1/tareas" \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "tarea movil", "estado": "pendiente", "prioridad": "alta"}'
# respuesta: {"id": 1, "proyecto_id": 1, ...}

# paso 3: mover tarea al proyecto 2
curl -X PUT "http://127.0.0.1:8000/tareas/1" \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id": 2}'
# respuesta: {"id": 1, "proyecto_id": 2, ...}

# paso 4: verificar que ahora esta en proyecto 2
curl -X GET "http://127.0.0.1:8000/proyectos/2/tareas"
# respuesta: [{"id": 1, "descripcion": "tarea movil", "proyecto_id": 2, ...}]
```

---

## estructura de archivos del proyecto

```
tp4/
│
├── main.py              # archivo principal con la api fastapi
│                        # contiene todos los endpoints y logica de negocio
│
├── models.py            # modelos pydantic para validacion
│                        # define schemas de entrada y salida
│
├── database.py          # funciones auxiliares de base de datos
│                        # inicializacion y datos de prueba
│
├── test_main.py         # suite de tests con pytest
│                        # tests de todos los endpoints
│
├── requirements.txt     # dependencias del proyecto
│                        # fastapi, uvicorn, pydantic, pytest, httpx
│
├── .gitignore          # archivos a ignorar en git
│                        # __pycache__, *.db, venv/, etc.
│
├── tareas.db           # base de datos sqlite (se crea automaticamente)
│                        # contiene tablas proyectos y tareas
│
└── readme.md           # este archivo con documentacion completa
```

---

## comandos utiles

### desarrollo

```bash
# instalar dependencias
pip install -r requirements.txt

# crear base de datos con datos de prueba
python database.py

# iniciar servidor
uvicorn main:app --reload

# iniciar en otro puerto
uvicorn main:app --reload --port 8080

# ejecutar tests
pytest test_main.py -v

# tests con cobertura
pytest test_main.py -v --cov

# limpiar base de datos
rm tareas.db
python database.py
```

### produccion

```bash
# instalar dependencias
pip install -r requirements.txt

# iniciar servidor sin reload
uvicorn main:app --host 0.0.0.0 --port 8000

# con workers
uvicorn main:app --host 0.0.0.0 --port 8000 --workers 4
```

---

## tecnologias utilizadas

- **fastapi** 0.104.1 - framework web moderno y rapido
- **uvicorn** 0.24.0 - servidor asgi
- **pydantic** 2.5.0 - validacion de datos
- **sqlite3** - base de datos embebida
- **pytest** 7.4.3 - framework de testing
- **httpx** 0.25.1 - cliente http para tests

---

## autor y fecha de entrega

**trabajo practico n°4**  
**fecha limite:** 24 de octubre de 2025 a las 21:00hs  
**materia:** programacion de aplicaciones web

---

## licencia

este proyecto es parte de un trabajo practico educativo.