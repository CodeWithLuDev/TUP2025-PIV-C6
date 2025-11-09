
# Trabajo Práctico N°4 – Relaciones entre Tablas y Filtros Avanzados

## Cómo inicializar mi API desde Git Bash

1. Posicionarse en la carpeta del TP4:  
   ```bash
   cd 'C:\Users\User\Desktop\TUP2025-PIV-C6\TPs\62198 - Villagra Martina Paula\Unidad 3\TP4'
   ```

2. Activar el entorno virtual:  
   ```bash
   source venv/Scripts/activate
   ```

3. Levantar el servidor:  
   ```bash
   uvicorn main:app --reload
   ```

4. Acceder a la URL base:  
   `http://127.0.0.1:8000`

---

## Base de Datos - Tareas

### Tabla `proyecto`
```sql
CREATE TABLE proyecto (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  nombre TEXT NOT NULL UNIQUE,
  descripcion TEXT,
  fecha_creacion TEXT NOT NULL
);
```

### Tabla `tarea`
```sql
CREATE TABLE tarea (
  id INTEGER PRIMARY KEY AUTOINCREMENT,
  descripcion TEXT NOT NULL,
  estado TEXT NOT NULL,
  prioridad TEXT NOT NULL,
  proyectoId INTEGER NOT NULL,
  fecha_creacion TEXT NOT NULL,
  FOREIGN KEY (proyectoId) REFERENCES proyecto(id)
);
```

---

## Endpoints / Rutas de la API

**URL base:** `http://127.0.0.1:8000`

---

###  **GET /**  
Raíz de la API.
```json
{
  "mensaje": "API de Tareas con SQLite (TP4)"
}
```

###  **GET /proyectos**  
Lista todos los proyectos.
```json
[
  {
    "id": 1,
    "nombre": "Proyecto API",
    "descripcion": "Desarrollo de API REST con FastAPI",
    "fecha_creacion": "2025-10-25T14:32:00"
  }
]
```

### **GET /proyectos/{id}**  
Obtiene un proyecto específico.
```json
{
  "id": 1,
  "nombre": "Proyecto API",
  "descripcion": "Desarrollo de API REST con FastAPI",
  "fecha_creacion": "2025-10-25T14:32:00",
  "total_tareas": 3
}
```

###  **POST /proyectos**  
Crea un nuevo proyecto.  
Ejemplo con **curl**:
```bash
curl -X POST "http://127.0.0.1:8000/proyectos" -H "Content-Type: application/json" -d '{
  "nombre": "Nuevo Proyecto",
  "descripcion": "Proyecto de ejemplo"
}'
```
**Respuesta:**
```json
{
  "id": 2,
  "nombre": "Nuevo Proyecto",
  "descripcion": "Proyecto de ejemplo",
  "fecha_creacion": "2025-10-26T15:00:00"
}
```

###  **PUT /proyectos/{id}**  
Modifica un proyecto existente.
```bash
curl -X PUT "http://127.0.0.1:8000/proyectos/1" -H "Content-Type: application/json" -d '{
  "nombre": "Proyecto API Actualizado",
  "descripcion": "API con FastAPI y SQLite"
}'
```
**Respuesta:**
```json
{
  "id": 1,
  "nombre": "Proyecto API Actualizado",
  "descripcion": "API con FastAPI y SQLite",
  "fecha_creacion": "2025-10-25T14:32:00"
}
```

###  **DELETE /proyectos/{id}**  
Elimina un proyecto y sus tareas asociadas.
```bash
curl -X DELETE "http://127.0.0.1:8000/proyectos/1"
```
**Respuesta:**
```json
{
  "mensaje": "Proyecto y tareas asociadas eliminadas correctamente."
}
```

###  **GET /proyectos/{id}/tareas**  
Lista todas las tareas de un proyecto.
```json
[
  {
    "id": 1,
    "descripcion": "Diseñar modelo de datos",
    "estado": "pendiente",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-25T15:00:00"
  }
]
```

### **GET /tareas**  
Lista todas las tareas de todos los proyectos.
```bash
curl -X GET "http://127.0.0.1:8000/tareas"
```
**Respuesta:**
```json
[
  {
    "id": 1,
    "descripcion": "Implementar endpoint POST",
    "estado": "pendiente",
    "prioridad": "alta",
    "proyecto_id": 1,
    "fecha_creacion": "2025-10-26T16:20:00"
  }
]
```

### **POST /proyectos/{id}/tareas**  
Crea una tarea dentro de un proyecto.
```bash
curl -X POST "http://127.0.0.1:8000/proyectos/1/tareas" -H "Content-Type: application/json" -d '{
  "descripcion": "Implementar endpoint POST",
  "estado": "pendiente",
  "prioridad": "alta"
}'
```
**Respuesta:**
```json
{
  "id": 4,
  "descripcion": "Implementar endpoint POST",
  "estado": "pendiente",
  "prioridad": "alta",
  "proyecto_id": 1,
  "fecha_creacion": "2025-10-27T10:30:00"
}
```

### **PUT /tareas/{id}**  
Modifica una tarea existente (puede cambiar de proyecto).
```bash
curl -X PUT "http://127.0.0.1:8000/tareas/4" -H "Content-Type: application/json" -d '{
  "descripcion": "Endpoint POST completado",
  "estado": "completada",
  "prioridad": "alta",
  "proyecto_id": 1
}'
```
**Respuesta:**
```json
{
  "mensaje": "Tarea actualizada correctamente."
}
```

### **DELETE /tareas/{id}**  
Elimina una tarea.
```bash
curl -X DELETE "http://127.0.0.1:8000/tareas/4"
```
**Respuesta:**
```json
{
  "mensaje": "Tarea eliminada correctamente."
}
```

---

## Filtros y Búsquedas Avanzadas

###  Buscar proyectos por nombre
**GET /proyectos?nombre=parcial**
```json
[
  {
    "id": 1,
    "nombre": "Proyecto Parcial",
    "descripcion": "Entrega del parcial FastAPI",
    "fecha_creacion": "2025-10-28T09:15:00"
  }
]
```

### Filtrar tareas por estado
**GET /tareas?estado=pendiente**
```json
[
  {
    "id": 3,
    "descripcion": "Diseñar interfaz",
    "estado": "pendiente",
    "prioridad": "media",
    "proyecto_id": 2,
    "fecha_creacion": "2025-10-27T12:00:00"
  }
]
```

### Filtrar por prioridad
**GET /tareas?prioridad=alta**

### Filtrar por proyecto
**GET /tareas?proyecto_id=1**

### Filtros combinados
**GET /tareas?estado=completada&prioridad=alta**

###  Ordenar por fecha
**GET /tareas?orden=asc**  
**GET /tareas?orden=desc**

---

## Resúmenes

### **GET /proyectos/{id}/resumen**
Devuelve estadísticas de un proyecto específico.
```json
{
  "proyecto_id": 1,
  "nombre": "Proyecto API",
  "total_tareas": 5,
  "tareas_pendientes": 2,
  "tareas_completadas": 3,
  "ultima_actualizacion": "2025-10-27T18:00:00"
}
```

### 🧾 **GET /resumen**
Resumen general de toda la aplicación.
```json
{
  "total_proyectos": 3,
  "total_tareas": 15,
  "pendientes": 7,
  "completadas": 8,
  "porcentaje_completado": "53%"
}
```
