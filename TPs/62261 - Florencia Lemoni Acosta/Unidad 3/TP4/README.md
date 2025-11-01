# TP4 - API de Proyectos y Tareas con Relaciones

## 📋 Descripción

API RESTful desarrollada con FastAPI y SQLite que implementa un sistema de gestión de proyectos y tareas con relaciones 1:N (uno a muchos). Cada proyecto puede contener múltiples tareas, con integridad referencial garantizada mediante claves foráneas.

## 🗄️ Estructura de la Base de Datos

### Diagrama de Relaciones

```
proyectos (1) ──────< (N) tareas
    │                      │
    ├─ id (PK)            ├─ id (PK)
    ├─ nombre (UNIQUE)    ├─ descripcion
    ├─ descripcion        ├─ estado
    └─ fecha_creacion     ├─ prioridad
                          ├─ proyecto_id (FK) → proyectos.id
                          └─ fecha_creacion
```

### Tabla: `proyectos`

| Campo           | Tipo    | Restricciones              |
|----------------|---------|----------------------------|
| id             | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| nombre         | TEXT    | NOT NULL, UNIQUE           |
| descripcion    | TEXT    | NULL                       |
| fecha_creacion | TEXT    | NOT NULL                   |

### Tabla: `tareas`

| Campo           | Tipo    | Restricciones                              |
|----------------|---------|---------------------------------------------|
| id             | INTEGER | PRIMARY KEY, AUTOINCREMENT                  |
| descripcion    | TEXT    | NOT NULL                                    |
| estado         | TEXT    | NOT NULL                                    |
| prioridad      | TEXT    | NOT NULL, DEFAULT 'media'                   |
| proyecto_id    | INTEGER | NOT NULL, FK → proyectos.id, ON DELETE CASCADE |
| fecha_creacion | TEXT    | NOT NULL                                    |

**Nota importante:** La relación `ON DELETE CASCADE` significa que al eliminar un proyecto, todas sus tareas asociadas se eliminan automáticamente.

## 🚀 Instalación y Ejecución

### Requisitos

```bash
pip install fastapi uvicorn pydantic
```

### Iniciar el Servidor

```bash
uvicorn main:app --reload
```

La API estará disponible en: `http://127.0.0.1:8000`

Documentación interactiva: `http://127.0.0.1:8000/docs`

## 📁 Estructura de Archivos

```
TP4/
├── main.py          # Endpoints de la API
├── models.py        # Modelos Pydantic para validación
├── database.py      # Funciones de acceso a datos
├── tareas.db        # Base de datos SQLite (se crea automáticamente)
└── README.md        # Este archivo
```

## 🔌 Endpoints Disponibles

### **Proyectos**

#### `GET /proyectos` - Listar todos los proyectos
Filtra proyectos opcionalmente por nombre (búsqueda parcial).

**Query Params:**
- `nombre` (opcional): Texto para buscar en el nombre

**Ejemplo:**
```bash
curl "http://127.0.0.1:8000/proyectos"
curl "http://127.0.0.1:8000/proyectos?nombre=Alpha"
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "nombre": "Proyecto Alpha",
    "descripcion": "Desarrollo de aplicación web",
    "fecha_creacion": "2025-10-24T15:30:00"
  }
]
```

---

#### `GET /proyectos/{id}` - Obtener un proyecto específico
Devuelve el proyecto con contador de tareas asociadas.

**Ejemplo:**
```bash
curl "http://127.0.0.1:8000/proyectos/1"
```

**Respuesta:**
```json
{
  "id": 1,
  "nombre": "Proyecto Alpha",
  "descripcion": "Desarrollo de aplicación web",
  "fecha_creacion": "2025-10-24T15:30:00",
  "cantidad_tareas": 5
}
```

---

#### `POST /proyectos` - Crear un nuevo proyecto
Crea un proyecto validando que el nombre sea único.

**Body:**
```json
{
  "nombre": "Proyecto Beta",
  "descripcion": "Sistema de gestión"
}
```

**Ejemplo:**
```bash
curl -X POST "http://127.0.0.1:8000/proyectos" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Proyecto Beta", "descripcion": "Sistema de gestión"}'
```

**Respuesta:**
```json
{
  "id": 2,
  "nombre": "Proyecto Beta",
  "descripcion": "Sistema de gestión",
  "fecha_creacion": "2025-10-24T16:00:00"
}
```

**Errores posibles:**
- `400`: Nombre vacío
- `409`: Nombre duplicado

---

#### `PUT /proyectos/{id}` - Actualizar un proyecto

**Body:**
```json
{
  "nombre": "Proyecto Beta v2",
  "descripcion": "Sistema de gestión actualizado"
}
```

**Ejemplo:**
```bash
curl -X PUT "http://127.0.0.1:8000/proyectos/2" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Proyecto Beta v2"}'
```

**Errores posibles:**
- `404`: Proyecto no encontrado
- `400`: Datos inválidos
- `409`: Nombre duplicado

---

#### `DELETE /proyectos/{id}` - Eliminar un proyecto
Elimina el proyecto y TODAS sus tareas asociadas (CASCADE).

**Ejemplo:**
```bash
curl -X DELETE "http://127.0.0.1:8000/proyectos/2"
```

**Respuesta:**
```json
{
  "mensaje": "Proyecto eliminado correctamente",
  "proyecto_id": 2,
  "tareas_eliminadas": 5
}
```

---

### **Tareas de Proyectos**

#### `GET /proyectos/{id}/tareas` - Listar tareas de un proyecto

**Query Params:**
- `estado` (opcional): `pendiente`, `en_progreso`, `completada`
- `prioridad` (opcional): `baja`, `media`, `alta`
- `orden` (opcional): `asc` o `desc` (por fecha)

**Ejemplo:**
```bash
curl "http://127.0.0.1:8000/proyectos/1/tareas"
curl "http://127.0.0.1:8000/proyectos/1/tareas?estado=pendiente&prioridad=alta"
```

**Respuesta:**
```json
[
  {
    "id": 1,
    "descripcion": "Implementar login",
    "estado": "pendiente",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-24T15:35:00"
  }
]
```

---

#### `POST /proyectos/{id}/tareas` - Crear tarea en un proyecto

**Body:**
```json
{
  "descripcion": "Implementar sistema de login",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Ejemplo:**
```bash
curl -X POST "http://127.0.0.1:8000/proyectos/1/tareas" \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Implementar login", "estado": "pendiente", "prioridad": "alta"}'
```

**Errores posibles:**
- `400`: Proyecto no existe o datos inválidos

---

### **Tareas Generales**

#### `GET /tareas` - Listar todas las tareas
Devuelve tareas de todos los proyectos con filtros opcionales.

**Query Params:**
- `estado` (opcional)
- `prioridad` (opcional)
- `proyecto_id` (opcional)
- `orden` (opcional): `asc` o `desc`

**Ejemplo:**
```bash
curl "http://127.0.0.1:8000/tareas?estado=completada&prioridad=alta"
```

---

#### `PUT /tareas/{id}` - Actualizar una tarea
Puede cambiar cualquier campo, incluyendo mover la tarea a otro proyecto.

**Body:**
```json
{
  "descripcion": "Nueva descripción",
  "estado": "en_progreso",
  "prioridad": "media",
  "proyecto_id": 2
}
```

**Ejemplo:**
```bash
curl -X PUT "http://127.0.0.1:8000/tareas/1" \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'
```

**Errores posibles:**
- `404`: Tarea no encontrada
- `400`: Proyecto destino no existe

---

#### `DELETE /tareas/{id}` - Eliminar una tarea

**Ejemplo:**
```bash
curl -X DELETE "http://127.0.0.1:8000/tareas/1"
```

---

### **Resumen y Estadísticas**

#### `GET /proyectos/{id}/resumen` - Estadísticas de un proyecto

**Ejemplo:**
```bash
curl "http://127.0.0.1:8000/proyectos/1/resumen"
```

**Respuesta:**
```json
{
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
```

---

#### `GET /resumen` - Resumen general de la aplicación

**Ejemplo:**
```bash
curl "http://127.0.0.1:8000/resumen"
```

**Respuesta:**
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
    "nombre": "Proyecto Alpha",
    "cantidad_tareas": 15
  }
}
```

## 🔍 Explicación de las Relaciones entre Tablas

### Relación 1:N (Uno a Muchos)

Cada **proyecto** puede tener **múltiples tareas**, pero cada **tarea** pertenece a **un solo proyecto**.

### Clave Foránea (Foreign Key)

La columna `proyecto_id` en la tabla `tareas` es una clave foránea que referencia a `proyectos.id`. Esto garantiza:

1. **Integridad referencial**: No se puede crear una tarea con un `proyecto_id` inexistente
2. **Eliminación en cascada**: Al eliminar un proyecto, se eliminan automáticamente todas sus tareas

### Implementación en SQLite

```sql
FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
```

### Ejemplos Prácticos

**Escenario 1: Crear proyecto y tareas**
```bash
# 1. Crear proyecto
curl -X POST "http://127.0.0.1:8000/proyectos" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "Mi Proyecto"}'

# Respuesta: {"id": 1, ...}

# 2. Crear tareas en ese proyecto
curl -X POST "http://127.0.0.1:8000/proyectos/1/tareas" \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Tarea 1", "estado": "pendiente", "prioridad": "alta"}'
```

**Escenario 2: Mover tarea entre proyectos**
```bash
# Cambiar tarea del proyecto 1 al proyecto 2
curl -X PUT "http://127.0.0.1:8000/tareas/5" \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id": 2}'
```

**Escenario 3: Eliminar proyecto con CASCADE**
```bash
# Eliminar proyecto (elimina automáticamente sus 10 tareas)
curl -X DELETE "http://127.0.0.1:8000/proyectos/1"

# Respuesta: {"mensaje": "...", "tareas_eliminadas": 10}
```

## 🛡️ Validaciones Implementadas

### Proyectos
- ✅ Nombre no puede estar vacío
- ✅ Nombre debe ser único
- ✅ Fecha de creación se genera automáticamente
- ✅ Descripción es opcional

### Tareas
- ✅ Descripción no puede estar vacía
- ✅ Estado debe ser: `pendiente`, `en_progreso` o `completada`
- ✅ Prioridad debe ser: `baja`, `media` o `alta`
- ✅ El `proyecto_id` debe existir en la tabla proyectos
- ✅ Fecha de creación se genera automáticamente

### Códigos de Error HTTP
- `200`: Operación exitosa
- `201`: Recurso creado exitosamente
- `400`: Datos de entrada inválidos
- `404`: Recurso no encontrado
- `409`: Conflicto (ej: nombre duplicado)
- `500`: Error interno del servidor

## 🧪 Pruebas Funcionales

### Verificación de Integridad Referencial

```bash
# 1. Crear un proyecto
curl -X POST "http://127.0.0.1:8000/proyectos" \
  -d '{"nombre": "Test"}' -H "Content-Type: application/json"

# 2. Intentar crear tarea con proyecto_id=999 (no existe)
curl -X POST "http://127.0.0.1:8000/proyectos/999/tareas" \
  -d '{"descripcion": "Tarea", "estado": "pendiente", "prioridad": "media"}' \
  -H "Content-Type: application/json"
# ❌ Error 400: "El proyecto con ID 999 no existe"

# 3. Crear tareas en proyecto 1
curl -X POST "http://127.0.0.1:8000/proyectos/1/tareas" \
  -d '{"descripcion": "Tarea A", "estado": "pendiente", "prioridad": "alta"}' \
  -H "Content-Type: application/json"

# 4. Eliminar proyecto 1
curl -X DELETE "http://127.0.0.1:8000/proyectos/1"

# 5. Verificar que las tareas también fueron eliminadas
curl "http://127.0.0.1:8000/tareas?proyecto_id=1"
# Respuesta: []
```

## 📊 Casos de Uso Completos

### Flujo de Trabajo Típico

```bash
# 1. Crear un nuevo proyecto
curl -X POST "http://127.0.0.1:8000/proyectos" \
  -H "Content-Type: application/json" \
  -d '{"nombre": "E-Commerce", "descripcion": "Tienda online"}'

# 2. Crear múltiples tareas
curl -X POST "http://127.0.0.1:8000/proyectos/1/tareas" \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Diseñar base de datos", "estado": "completada", "prioridad": "alta"}'

curl -X POST "http://127.0.0.1:8000/proyectos/1/tareas" \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Implementar carrito", "estado": "en_progreso", "prioridad": "alta"}'

curl -X POST "http://127.0.0.1:8000/proyectos/1/tareas" \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Configurar pasarela de pago", "estado": "pendiente", "prioridad": "media"}'

# 3. Ver tareas pendientes de alta prioridad
curl "http://127.0.0.1:8000/proyectos/1/tareas?estado=pendiente&prioridad=alta"

# 4. Ver resumen del proyecto
curl "http://127.0.0.1:8000/proyectos/1/resumen"

# 5. Marcar tarea como completada
curl -X PUT "http://127.0.0.1:8000/tareas/2" \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'

# 6. Ver resumen general
curl "http://127.0.0.1:8000/resumen"
```

## 👤 Autor

**Trabajo Práctico N°4** - Programación II  
Fecha de entrega: 24 de octubre de 2025, 21:00hs

## 📝 Notas Adicionales

- La base de datos `tareas.db` se crea automáticamente al iniciar el servidor
- Para reiniciar la base de datos, simplemente elimina el archivo `tareas.db`
- Todas las fechas se almacenan en formato ISO 8601
- La documentación interactiva de Swagger está disponible en `/docs`
- La documentación alternativa de ReDoc está en `/redoc`