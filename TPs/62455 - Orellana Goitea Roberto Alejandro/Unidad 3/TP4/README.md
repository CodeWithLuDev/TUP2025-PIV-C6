# Trabajo Práctico N°4 – Relaciones entre Tablas y Filtros Avanzados

## 📋 Descripción

API REST para gestión de **Proyectos** y **Tareas** con persistencia en SQLite. Implementa relaciones **1:N** (un proyecto tiene muchas tareas) con integridad referencial mediante claves foráneas.

## 🏗️ Estructura de la Base de Datos

### Diagrama de Relaciones

```
┌─────────────────┐         ┌─────────────────┐
│   Proyectos     │         │     Tareas      │
├─────────────────┤         ├─────────────────┤
│ id (PK)         │────┐    │ id (PK)         │
│ nombre (UNIQUE) │    │    │ descripcion     │
│ descripcion     │    │    │ estado          │
│ fecha_creacion  │    └───<│ proyecto_id(FK) │
└─────────────────┘         │ prioridad       │
                            │ fecha_creacion  │
                            └─────────────────┘
                            
    Relación: 1:N (uno a muchos)
    ON DELETE CASCADE
```

### Tabla `proyectos`

| Campo           | Tipo    | Restricciones                   |
| --------------- | ------- | ------------------------------- |
| id              | INTEGER | PRIMARY KEY, AUTOINCREMENT      |
| nombre          | TEXT    | NOT NULL, UNIQUE                |
| descripcion     | TEXT    | NULL                            |
| fecha_creacion  | TEXT    | NOT NULL                        |

### Tabla `tareas`

| Campo           | Tipo    | Restricciones                           |
| --------------- | ------- | --------------------------------------- |
| id              | INTEGER | PRIMARY KEY, AUTOINCREMENT              |
| descripcion     | TEXT    | NOT NULL                                |
| estado          | TEXT    | NOT NULL                                |
| prioridad       | TEXT    | NOT NULL, DEFAULT 'media'               |
| proyecto_id     | INTEGER | NOT NULL, FOREIGN KEY → proyectos(id)   |
| fecha_creacion  | TEXT    | NOT NULL                                |

**Nota**: La clave foránea está configurada con `ON DELETE CASCADE`, por lo que al eliminar un proyecto se eliminan automáticamente todas sus tareas asociadas.

## 📁 Estructura del Proyecto

```
TP4/
├── main.py         # API principal con todos los endpoints
├── models.py       # Modelos Pydantic para validación
├── database.py     # Funciones de acceso a base de datos
├── tareas.db       # Base de datos SQLite (se crea automáticamente)
└── README.md       # Este archivo
```

## 🚀 Instalación y Ejecución

### Requisitos Previos

- Python 3.8 o superior
- pip (gestor de paquetes de Python)

### Instalación de Dependencias

```bash
pip install fastapi uvicorn
```

### Iniciar el Servidor

```bash
# Opción 1: Usando uvicorn directamente
uvicorn main:app --reload

# Opción 2: Ejecutando main.py
python main.py
```

El servidor se iniciará en: **http://localhost:8000**

### Documentación Interactiva

Una vez iniciado el servidor, accede a:

- **Swagger UI**: http://localhost:8000/docs
- **ReDoc**: http://localhost:8000/redoc

## 🔗 Endpoints de la API

### 📊 Información General

#### `GET /`
Información básica de la API y lista de endpoints disponibles.

```bash
curl http://localhost:8000/
```

---

## 📂 Endpoints de Proyectos

### 1. Listar Proyectos

**`GET /proyectos`**

Lista todos los proyectos con filtro opcional por nombre.

**Query Parameters:**
- `nombre` (opcional): Buscar proyectos que contengan este texto

**Ejemplo:**

```bash
# Listar todos los proyectos
curl http://localhost:8000/proyectos

# Buscar proyectos por nombre
curl "http://localhost:8000/proyectos?nombre=Alpha"
```

**Respuesta:**

```json
[
  {
    "id": 1,
    "nombre": "Proyecto Alpha",
    "descripcion": "Primer proyecto de prueba",
    "fecha_creacion": "2025-10-17T10:30:00",
    "cantidad_tareas": 5
  }
]
```

---

### 2. Obtener Proyecto Específico

**`GET /proyectos/{id}`**

Obtiene un proyecto por su ID con el contador de tareas.

**Ejemplo:**

```bash
curl http://localhost:8000/proyectos/1
```

**Respuesta:**

```json
{
  "id": 1,
  "nombre": "Proyecto Alpha",
  "descripcion": "Primer proyecto de prueba",
  "fecha_creacion": "2025-10-17T10:30:00",
  "cantidad_tareas": 5
}
```

---

### 3. Crear Proyecto

**`POST /proyectos`**

Crea un nuevo proyecto.

**Body (JSON):**

```json
{
  "nombre": "Proyecto Beta",
  "descripcion": "Segundo proyecto"
}
```

**Ejemplo:**

```bash
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Proyecto Beta","descripcion":"Segundo proyecto"}'
```

**Validaciones:**
- ✅ El nombre no puede estar vacío
- ✅ El nombre debe ser único (no puede haber dos proyectos con el mismo nombre)
- ✅ La descripción es opcional

**Respuesta:**

```json
{
  "id": 2,
  "nombre": "Proyecto Beta",
  "descripcion": "Segundo proyecto",
  "fecha_creacion": "2025-10-17T11:00:00",
  "cantidad_tareas": 0
}
```

---

### 4. Actualizar Proyecto

**`PUT /proyectos/{id}`**

Actualiza un proyecto existente.

**Body (JSON):**

```json
{
  "nombre": "Proyecto Beta Actualizado",
  "descripcion": "Nueva descripción"
}
```

**Ejemplo:**

```bash
curl -X PUT http://localhost:8000/proyectos/2 \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Proyecto Beta Actualizado"}'
```

**Validaciones:**
- ✅ El proyecto debe existir
- ✅ El nombre debe ser único (si se cambia)
- ✅ Se pueden actualizar campos individualmente

---

### 5. Eliminar Proyecto

**`DELETE /proyectos/{id}`**

Elimina un proyecto y todas sus tareas asociadas (CASCADE).

**Ejemplo:**

```bash
curl -X DELETE http://localhost:8000/proyectos/2
```

**Respuesta:**

```json
{
  "mensaje": "Proyecto 'Proyecto Beta' eliminado exitosamente",
  "tareas_eliminadas": 3
}
```

---

## ✅ Endpoints de Tareas

### 6. Listar Tareas de un Proyecto

**`GET /proyectos/{id}/tareas`**

Lista todas las tareas de un proyecto específico.

**Query Parameters:**
- `estado` (opcional): `pendiente`, `en_progreso`, `completada`
- `prioridad` (opcional): `baja`, `media`, `alta`
- `orden` (opcional): `asc` o `desc`

**Ejemplo:**

```bash
# Todas las tareas del proyecto 1
curl http://localhost:8000/proyectos/1/tareas

# Tareas pendientes de alta prioridad
curl "http://localhost:8000/proyectos/1/tareas?estado=pendiente&prioridad=alta"
```

**Respuesta:**

```json
[
  {
    "id": 1,
    "descripcion": "Implementar login",
    "estado": "en_progreso",
    "prioridad": "alta",
    "proyecto_id": 1,
    "proyecto_nombre": "Proyecto Alpha",
    "fecha_creacion": "2025-10-17T10:35:00"
  }
]
```

---

### 7. Crear Tarea en un Proyecto

**`POST /proyectos/{id}/tareas`**

Crea una nueva tarea dentro de un proyecto.

**Body (JSON):**

```json
{
  "descripcion": "Implementar API REST",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Ejemplo:**

```bash
curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion":"Implementar API REST","prioridad":"alta"}'
```

**Validaciones:**
- ✅ El proyecto debe existir
- ✅ La descripción no puede estar vacía
- ✅ Estado por defecto: `pendiente`
- ✅ Prioridad por defecto: `media`

---

### 8. Listar Todas las Tareas

**`GET /tareas`**

Lista todas las tareas de todos los proyectos con filtros.

**Query Parameters:**
- `estado` (opcional): Filtrar por estado
- `prioridad` (opcional): Filtrar por prioridad
- `proyecto_id` (opcional): Filtrar por proyecto
- `orden` (opcional): `asc` o `desc`

**Ejemplo:**

```bash
# Todas las tareas
curl http://localhost:8000/tareas

# Tareas completadas de alta prioridad
curl "http://localhost:8000/tareas?estado=completada&prioridad=alta"

# Tareas del proyecto 1 ordenadas por fecha descendente
curl "http://localhost:8000/tareas?proyecto_id=1&orden=desc"
```

---

### 9. Actualizar Tarea

**`PUT /tareas/{id}`**

Actualiza una tarea existente. Permite cambiar de proyecto.

**Body (JSON):**

```json
{
  "descripcion": "Nueva descripción",
  "estado": "completada",
  "prioridad": "baja",
  "proyecto_id": 2
}
```

**Ejemplo:**

```bash
# Cambiar estado a completada
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado":"completada"}'

# Mover tarea al proyecto 2
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id":2}'
```

**Validaciones:**
- ✅ La tarea debe existir
- ✅ El nuevo proyecto_id debe existir (si se cambia)
- ✅ Se pueden actualizar campos individualmente

---

### 10. Eliminar Tarea

**`DELETE /tareas/{id}`**

Elimina una tarea específica.

**Ejemplo:**

```bash
curl -X DELETE http://localhost:8000/tareas/1
```

**Respuesta:**

```json
{
  "mensaje": "Tarea eliminada exitosamente"
}
```

---

## 📊 Endpoints de Resumen y Estadísticas

### 11. Resumen de un Proyecto

**`GET /proyectos/{id}/resumen`**

Devuelve estadísticas completas de un proyecto.

**Ejemplo:**

```bash
curl http://localhost:8000/proyectos/1/resumen
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

### 12. Resumen General

**`GET /resumen`**

Devuelve estadísticas de toda la aplicación.

**Ejemplo:**

```bash
curl http://localhost:8000/resumen
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

---

## 🔐 Validaciones y Manejo de Errores

### Códigos de Estado HTTP

| Código | Descripción                          | Ejemplo                                    |
| ------ | ------------------------------------ | ------------------------------------------ |
| 200    | OK                                   | Operación exitosa                          |
| 201    | Created                              | Recurso creado exitosamente                |
| 400    | Bad Request                          | Datos inválidos (nombre vacío, etc.)       |
| 404    | Not Found                            | Proyecto o tarea no encontrada             |
| 409    | Conflict                             | Nombre de proyecto duplicado               |
| 422    | Unprocessable Entity                 | Error de validación de Pydantic            |

### Ejemplos de Errores

**404 - Proyecto no encontrado:**

```json
{
  "detail": {
    "error": "El proyecto con ID 999 no existe"
  }
}
```

**409 - Nombre duplicado:**

```json
{
  "detail": {
    "error": "Ya existe un proyecto con el nombre 'Proyecto Alpha'"
  }
}
```

**400 - Datos inválidos:**

```json
{
  "detail": {
    "error": "El nombre del proyecto no puede estar vacío"
  }
}
```

---

## 🧪 Pruebas de Integridad Referencial

### Escenario 1: Crear Proyecto y Tareas

```bash
# 1. Crear proyecto
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Proyecto Test","descripcion":"Prueba de relaciones"}'

# 2. Crear tareas en el proyecto (ID = 1)
curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion":"Tarea 1","prioridad":"alta"}'

curl -X POST http://localhost:8000/proyectos/1/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion":"Tarea 2","prioridad":"media"}'
```

### Escenario 2: Intentar Crear Tarea en Proyecto Inexistente

```bash
# Debe fallar con 404
curl -X POST http://localhost:8000/proyectos/999/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion":"Tarea huérfana"}'
```

### Escenario 3: Eliminar Proyecto con Tareas (CASCADE)

```bash
# Las tareas se eliminan automáticamente
curl -X DELETE http://localhost:8000/proyectos/1
```

### Escenario 4: Mover Tarea a Otro Proyecto

```bash
# Crear segundo proyecto
curl -X POST http://localhost:8000/proyectos \
  -H "Content-Type: application/json" \
  -d '{"nombre":"Proyecto Destino"}'

# Mover tarea del proyecto 1 al proyecto 2
curl -X PUT http://localhost:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"proyecto_id":2}'
```

---

## 📝 Notas Técnicas

### Relaciones entre Tablas

- **Tipo de Relación**: 1:N (One-to-Many)
  - Un proyecto puede tener muchas tareas
  - Una tarea pertenece a un solo proyecto

- **Clave Foránea**: `tareas.proyecto_id` → `proyectos.id`

- **Integridad Referencial**: 
  - `ON DELETE CASCADE`: Al eliminar un proyecto se eliminan sus tareas
  - Activado con `PRAGMA foreign_keys = ON` en SQLite

### Consultas con JOIN

Las consultas de tareas utilizan `JOIN` para incluir el nombre del proyecto:

```sql
SELECT t.*, p.nombre as proyecto_nombre 
FROM tareas t 
JOIN proyectos p ON t.proyecto_id = p.id 
WHERE t.proyecto_id = ?
```

### Validación de Datos

- **Pydantic Models**: Validación automática de tipos y restricciones
- **Validación Manual**: Nombres duplicados, claves foráneas, campos vacíos
- **Enums**: Estados y prioridades definidos con `Enum` de Python

---

## 🛠️ Tecnologías Utilizadas

- **FastAPI**: Framework web moderno para APIs REST
- **Pydantic**: Validación de datos y serialización
- **SQLite**: Base de datos relacional embebida
- **Uvicorn**: Servidor ASGI de alto rendimiento
- **Python 3.8+**: Lenguaje de programación

---

## 👤 Autor

**Roberto Alejandro Orellana Goitea**  
Legajo: 62455  
Trabajo Práctico N°4 - Programación IV

---

## 📚 Referencias

- [Documentación de FastAPI](https://fastapi.tiangolo.com/)
- [Documentación de SQLite](https://www.sqlite.org/docs.html)
- [Documentación de Pydantic](https://docs.pydantic.dev/)
