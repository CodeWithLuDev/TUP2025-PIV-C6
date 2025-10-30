# TP3 - API de Tareas Persistente con SQLite

## 📋 Descripción

API REST desarrollada con FastAPI que permite gestionar tareas de forma persistente utilizando SQLite como base de datos. Los datos se mantienen almacenados incluso después de reiniciar el servidor.

## 🚀 Características

- ✅ CRUD completo de tareas (Crear, Leer, Actualizar, Eliminar)
- ✅ Persistencia de datos con SQLite
- ✅ Filtros por estado, prioridad y texto
- ✅ Ordenamiento por fecha de creación (ascendente/descendente)
- ✅ Validación de datos con Pydantic
- ✅ Resumen estadístico de tareas por estado y prioridad
- ✅ Códigos de estado HTTP apropiados
- ✅ Sistema de prioridades (baja, media, alta)

## 📦 Requisitos

- Python 3.8 o superior
- FastAPI
- Uvicorn
- Pydantic

## 🔧 Instalación

1. **Asegurate de tener Python instalado**:

```bash
python --version
```

2. **Instalar las dependencias necesarias**:

```bash
pip install fastapi uvicorn pydantic
```

3. **Verificar la estructura del proyecto**:

```
TP3/
├── main.py          # Código principal de la API
├── test_TP3.py      # Tests del trabajo práctico
├── README.md        # Este archivo
└── tareas.db        # Base de datos (se crea automáticamente al iniciar)
```

## ▶️ Iniciar el Servidor

Para iniciar el servidor de desarrollo, ejecutá el siguiente comando en la terminal:

```bash
uvicorn main:app --reload
```

**Salida esperada**:
```
INFO:     Will watch for changes in these directories: ['C:\\Users\\...']
INFO:     Uvicorn running on http://127.0.0.1:8000 (Press CTRL+C to quit)
INFO:     Started reloader process [12345] using WatchFiles
INFO:     Started server process [12346]
INFO:     Waiting for application startup.
INFO:     Application startup complete.
```

El servidor estará disponible en: **http://127.0.0.1:8000**

### Opciones adicionales al iniciar:

```bash
# Cambiar el puerto (por ejemplo, al 8080)
uvicorn main:app --reload --port 8080

# Permitir acceso desde otras computadoras en la red
uvicorn main:app --reload --host 0.0.0.0

# Sin modo reload (para producción)
uvicorn main:app
```

## 📚 Documentación Interactiva

Una vez iniciado el servidor, podés acceder a la documentación automática generada por FastAPI:

- **Swagger UI** (recomendado): http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

Desde Swagger UI podés probar todos los endpoints directamente desde el navegador.

## 🌐 Endpoints Disponibles

### 1. Información de la API

**`GET /`**

Devuelve información general sobre la API y sus endpoints disponibles.

**Ejemplo con navegador**:
```
http://127.0.0.1:8000/
```

**Ejemplo con curl**:
```bash
curl http://127.0.0.1:8000/
```

**Respuesta**:
```json
{
  "nombre": "API de Tareas Persistente",
  "version": "3.0",
  "descripcion": "API para gestionar tareas con persistencia en SQLite",
  "endpoints": [
    "GET /tareas - Listar todas las tareas",
    "POST /tareas - Crear una nueva tarea",
    "PUT /tareas/{id} - Actualizar una tarea",
    "DELETE /tareas/{id} - Eliminar una tarea",
    "GET /tareas/resumen - Obtener resumen de tareas",
    "PUT /tareas/completar_todas - Completar todas las tareas"
  ]
}
```

---

### 2. Listar Tareas

**`GET /tareas`**

Obtiene todas las tareas almacenadas. Admite múltiples filtros opcionales que se pueden combinar.

**Query Parameters (todos opcionales)**:
- `estado`: Filtra por estado (`pendiente`, `en_progreso`, `completada`)
- `prioridad`: Filtra por prioridad (`baja`, `media`, `alta`)
- `texto`: Busca tareas que contengan ese texto en la descripción (case-insensitive)
- `orden`: Ordena por fecha de creación (`asc` = más antiguas primero, `desc` = más recientes primero)

**Ejemplos**:

```bash
# Obtener TODAS las tareas
curl http://127.0.0.1:8000/tareas

# Filtrar por estado "pendiente"
curl http://127.0.0.1:8000/tareas?estado=pendiente

# Filtrar por prioridad "alta"
curl http://127.0.0.1:8000/tareas?prioridad=alta

# Buscar tareas que contengan "comprar" en la descripción
curl http://127.0.0.1:8000/tareas?texto=comprar

# Ordenar por fecha descendente (más recientes primero)
curl http://127.0.0.1:8000/tareas?orden=desc

# Ordenar por fecha ascendente (más antiguas primero)
curl http://127.0.0.1:8000/tareas?orden=asc

# COMBINAR FILTROS: estado pendiente + prioridad alta + ordenar desc
curl "http://127.0.0.1:8000/tareas?estado=pendiente&prioridad=alta&orden=desc"
```

**Ejemplo de respuesta**:
```json
[
  {
    "id": 1,
    "descripcion": "Comprar leche y pan",
    "estado": "pendiente",
    "prioridad": "media",
    "fecha_creacion": "2025-10-16T14:30:25.123456"
  },
  {
    "id": 2,
    "descripcion": "Estudiar para el examen de Python",
    "estado": "en_progreso",
    "prioridad": "alta",
    "fecha_creacion": "2025-10-16T15:45:10.789012"
  }
]
```

---

### 3. Crear Tarea

**`POST /tareas`**

Crea una nueva tarea en la base de datos.

**Body (JSON)**:
```json
{
  "descripcion": "Texto de la tarea",
  "estado": "pendiente",
  "prioridad": "media"
}
```

**Campos**:
- `descripcion` **(obligatorio)**: Descripción de la tarea. No puede estar vacía ni contener solo espacios.
- `estado` *(opcional)*: Estado inicial. Valores: `pendiente`, `en_progreso`, `completada`. **Por defecto**: `pendiente`
- `prioridad` *(opcional)*: Nivel de prioridad. Valores: `baja`, `media`, `alta`. **Por defecto**: `media`

**Ejemplos**:

```bash
# Crear tarea básica (usa valores por defecto)
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Hacer las compras"}'

# Crear tarea con todos los campos
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Completar TP3 de programación",
    "estado": "en_progreso",
    "prioridad": "alta"
  }'

# Crear tarea urgente
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Entregar trabajo antes de las 21hs",
    "prioridad": "alta"
  }'
```

**Ejemplo con Python**:
```python
import requests

nueva_tarea = {
    "descripcion": "Ir al gimnasio",
    "estado": "pendiente",
    "prioridad": "media"
}

response = requests.post(
    "http://127.0.0.1:8000/tareas",
    json=nueva_tarea
)

print(response.status_code)  # 201
print(response.json())
```

**Respuesta exitosa (201 Created)**:
```json
{
  "id": 3,
  "descripcion": "Completar TP3 de programación",
  "estado": "en_progreso",
  "prioridad": "alta",
  "fecha_creacion": "2025-10-16T16:20:30.456789"
}
```

**Errores comunes (422 Unprocessable Entity)**:
```json
// Descripción vacía
{"detail": [...]}

// Estado inválido
{"detail": [...]}

// Prioridad inválida
{"detail": [...]}
```

---

### 4. Actualizar Tarea

**`PUT /tareas/{id}`**

Actualiza una tarea existente. Podés actualizar uno, dos o todos los campos.

**Parámetros de ruta**:
- `id`: ID de la tarea a actualizar

**Body (JSON)** - Todos los campos son opcionales:
```json
{
  "descripcion": "Nueva descripción",
  "estado": "completada",
  "prioridad": "baja"
}
```

**Ejemplos**:

```bash
# Actualizar SOLO el estado
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'

# Actualizar SOLO la descripción
curl -X PUT http://127.0.0.1:8000/tareas/2 \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Nueva descripción actualizada"}'

# Actualizar SOLO la prioridad
curl -X PUT http://127.0.0.1:8000/tareas/3 \
  -H "Content-Type: application/json" \
  -d '{"prioridad": "alta"}'

# Actualizar MÚLTIPLES campos
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Tarea actualizada",
    "estado": "en_progreso",
    "prioridad": "alta"
  }'
```

**Respuesta exitosa (200 OK)**:
```json
{
  "id": 1,
  "descripcion": "Tarea actualizada",
  "estado": "en_progreso",
  "prioridad": "alta",
  "fecha_creacion": "2025-10-16T14:30:25.123456"
}
```

**Error si la tarea no existe (404 Not Found)**:
```json
{
  "detail": {
    "error": "La tarea no existe"
  }
}
```

---

### 5. Eliminar Tarea

**`DELETE /tareas/{id}`**

Elimina permanentemente una tarea de la base de datos.

**Parámetros de ruta**:
- `id`: ID de la tarea a eliminar

**Ejemplos**:

```bash
# Eliminar la tarea con ID 1
curl -X DELETE http://127.0.0.1:8000/tareas/1

# Eliminar la tarea con ID 5
curl -X DELETE http://127.0.0.1:8000/tareas/5
```

**Respuesta exitosa (200 OK)**:
```json
{
  "mensaje": "Tarea eliminada correctamente"
}
```

**Error si la tarea no existe (404 Not Found)**:
```json
{
  "detail": {
    "error": "La tarea no existe"
  }
}
```

---

### 6. Resumen de Tareas

**`GET /tareas/resumen`**

Devuelve estadísticas completas sobre las tareas: total general, contadores por estado y contadores por prioridad.

**Ejemplo**:

```bash
curl http://127.0.0.1:8000/tareas/resumen
```

**Respuesta**:
```json
{
  "total_tareas": 8,
  "por_estado": {
    "pendiente": 3,
    "en_progreso": 2,
    "completada": 3
  },
  "por_prioridad": {
    "baja": 2,
    "media": 4,
    "alta": 2
  }
}
```

Este endpoint es útil para dashboards o mostrar estadísticas generales.

---

### 7. Completar Todas las Tareas

**`PUT /tareas/completar_todas`**

Marca automáticamente todas las tareas existentes como completadas.

**Ejemplo**:

```bash
curl -X PUT http://127.0.0.1:8000/tareas/completar_todas
```

**Respuesta si hay tareas**:
```json
{
  "mensaje": "Todas las tareas han sido marcadas como completadas"
}
```

**Respuesta si NO hay tareas**:
```json
{
  "mensaje": "No hay tareas para completar"
}
```

---

## 🧪 Ejecutar Tests

Para verificar que la API funciona correctamente:

```bash
# Instalar dependencias de testing (si no las tenés)
pip install pytest httpx

# Ejecutar TODOS los tests
pytest test_TP3.py -v

# Ejecutar un test específico
pytest test_TP3.py::test_crear_tarea -v

# Ver más detalles en caso de errores
pytest test_TP3.py -v --tb=short
```

**Salida esperada**:
```
============================= test session starts =============================
test_TP3.py::test_base_datos_se_crea PASSED                             [  3%]
test_TP3.py::test_tabla_tareas_existe PASSED                            [  7%]
...
test_TP3.py::test_endpoint_raiz PASSED                                  [100%]
============================= 27 passed in 2.45s ==============================
```

## 📊 Valores Válidos

### Estados de Tareas
| Estado | Descripción |
|--------|-------------|
| `pendiente` | Tarea pendiente de comenzar (valor por defecto) |
| `en_progreso` | Tarea que se está realizando actualmente |
| `completada` | Tarea finalizada |

### Prioridades
| Prioridad | Descripción |
|-----------|-------------|
| `baja` | Prioridad baja, no urgente |
| `media` | Prioridad media (valor por defecto) |
| `alta` | Prioridad alta, urgente |

## ⚠️ Validaciones y Restricciones

La API implementa las siguientes validaciones automáticas:

✅ **Descripción**:
- No puede estar vacía
- No puede contener solo espacios en blanco
- Debe tener al menos 1 carácter visible

✅ **Estado**:
- Solo acepta: `pendiente`, `en_progreso`, `completada`
- Cualquier otro valor devuelve error 422

✅ **Prioridad**:
- Solo acepta: `baja`, `media`, `alta`
- Cualquier otro valor devuelve error 422

✅ **Operaciones**:
- No se puede actualizar una tarea inexistente (404)
- No se puede eliminar una tarea inexistente (404)

## 🗄️ Base de Datos

### Información General
- **Motor**: SQLite
- **Archivo**: `tareas.db` (se crea automáticamente en el directorio del proyecto)
- **Persistencia**: Los datos se mantienen después de reiniciar el servidor

### Estructura de la Tabla `tareas`

| Columna | Tipo | Restricciones |
|---------|------|---------------|
| `id` | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| `descripcion` | TEXT | NOT NULL |
| `estado` | TEXT | NOT NULL |
| `prioridad` | TEXT | NOT NULL, DEFAULT 'media' |
| `fecha_creacion` | TEXT | NOT NULL |

### Verificar la Base de Datos Directamente

Podés inspeccionar la base de datos usando el cliente de SQLite:

```bash
# Abrir la base de datos
sqlite3 tareas.db

# Ver todas las tareas
SELECT * FROM tareas;

# Salir
.exit
```

## 💡 Ejemplos de Uso Completos

### Ejemplo 1: Flujo Completo de Trabajo

```bash
# 1. Ver información de la API
curl http://127.0.0.1:8000/

# 2. Crear varias tareas
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Comprar ingredientes", "prioridad": "alta"}'

curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Estudiar FastAPI", "prioridad": "media"}'

curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{"descripcion": "Hacer ejercicio", "prioridad": "baja"}'

# 3. Ver todas las tareas
curl http://127.0.0.1:8000/tareas

# 4. Filtrar tareas de prioridad alta
curl http://127.0.0.1:8000/tareas?prioridad=alta

# 5. Actualizar la primera tarea a "en_progreso"
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "en_progreso"}'

# 6. Ver el resumen
curl http://127.0.0.1:8000/tareas/resumen

# 7. Marcar la tarea como completada
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{"estado": "completada"}'

# 8. Eliminar una tarea
curl -X DELETE http://127.0.0.1:8000/tareas/3

# 9. Ver tareas ordenadas por fecha (más recientes primero)
curl http://127.0.0.1:8000/tareas?orden=desc
```

### Ejemplo 2: Script Python Completo

```python
import requests
import time

BASE_URL = "http://127.0.0.1:8000"

# 1. Crear varias tareas
print("=== CREANDO TAREAS ===")
tareas = [
    {"descripcion": "Estudiar para el examen", "prioridad": "alta"},
    {"descripcion": "Hacer las compras", "prioridad": "media"},
    {"descripcion": "Leer un libro", "prioridad": "baja"},
    {"descripcion": "Ir al gimnasio", "prioridad": "media"}
]

for tarea in tareas:
    response = requests.post(f"{BASE_URL}/tareas", json=tarea)
    print(f"✓ Creada: {response.json()['descripcion']}")
    time.sleep(0.1)  # Pequeña pausa para que las fechas sean diferentes

# 2. Obtener todas las tareas
print("\n=== TODAS LAS TAREAS ===")
response = requests.get(f"{BASE_URL}/tareas")
for tarea in response.json():
    print(f"ID: {tarea['id']} - {tarea['descripcion']} [{tarea['prioridad']}]")

# 3. Filtrar por prioridad alta
print("\n=== TAREAS DE ALTA PRIORIDAD ===")
response = requests.get(f"{BASE_URL}/tareas?prioridad=alta")
for tarea in response.json():
    print(f"- {tarea['descripcion']}")

# 4. Actualizar una tarea
print("\n=== ACTUALIZANDO TAREA ===")
response = requests.put(
    f"{BASE_URL}/tareas/1",
    json={"estado": "en_progreso"}
)
print(f"✓ Actualizada: {response.json()['descripcion']} -> {response.json()['estado']}")

# 5. Ver resumen
print("\n=== RESUMEN ===")
response = requests.get(f"{BASE_URL}/tareas/resumen")
resumen = response.json()
print(f"Total de tareas: {resumen['total_tareas']}")
print(f"Por estado: {resumen['por_estado']}")
print(f"Por prioridad: {resumen['por_prioridad']}")

# 6. Buscar tareas con texto específico
print("\n=== BUSCANDO 'libro' ===")
response = requests.get(f"{BASE_URL}/tareas?texto=libro")
for tarea in response.json():
    print(f"- {tarea['descripcion']}")

# 7. Completar todas las tareas
print("\n=== COMPLETANDO TODAS LAS TAREAS ===")
response = requests.put(f"{BASE_URL}/tareas/completar_todas")
print(f"✓ {response.json()['mensaje']}")

# 8. Verificar que todas estén completadas
response = requests.get(f"{BASE_URL}/tareas")
completadas = all(t['estado'] == 'completada' for t in response.json())
print(f"¿Todas completadas? {completadas}")
```

## 🐛 Solución de Problemas

### El servidor no inicia

**Problema**: Error al ejecutar `uvicorn main:app --reload`

**Soluciones**:
- Verificá que estés en el directorio correcto (donde está `main.py`)
- Comprobá que tengas instalado FastAPI y Uvicorn: `pip install fastapi uvicorn`
- Verificá que el puerto 8000 no esté en uso. Cambiá el puerto: `uvicorn main:app --reload --port 8080`

### Error 422 al crear tarea

**Problema**: La tarea no se crea y devuelve error 422

**Causas comunes**:
- La descripción está vacía o tiene solo espacios
- El estado no es uno de los tres válidos (`pendiente`, `en_progreso`, `completada`)
- La prioridad no es una de las tres válidas (`baja`, `media`, `alta`)
- El JSON está mal formateado

### Error 404 al actualizar/eliminar

**Problema**: Dice que la tarea no existe

**Solución**:
- Verificá que el ID sea correcto con `GET /tareas`
- Recordá que los IDs se incrementan automáticamente y no se reutilizan después de eliminar

### Los tests fallan

**Problema**: pytest muestra errores

**Soluciones**:
- Instalá las dependencias: `pip install pytest httpx`
- Asegurate de que el servidor NO esté corriendo cuando ejecutás los tests
- Verificá que `main.py` y `test_TP3.py` estén en el mismo directorio
- Si persiste, eliminá `tareas.db` y volvé a correr los tests

### La base de datos no se crea

**Problema**: No aparece el archivo `tareas.db`

**Solución**:
- Se crea automáticamente al iniciar el servidor por primera vez
- Verificá los permisos de escritura en el directorio
- Mirá en el mismo directorio donde está `main.py`

## 👨‍💻 Información del Trabajo

**Alumna**: Emilse Ibarra Aragón  
**Materia**: Programación  
**Institución**: UTN  
**Trabajo**: TP N°3 - API de Tareas Persistente  
**Fecha de Entrega**: 17 de Octubre de 2025 - 21:00hs

---

## 📝 Notas Adicionales

- La fecha de creación se registra automáticamente en formato ISO 8601
- Los IDs son autoincrementales y únicos
- La base de datos persiste entre reinicios del servidor
- Todos los filtros pueden combinarse para búsquedas más específicas
- El ordenamiento no afecta los filtros, se aplica después de filtrar

---

**¿Dudas o problemas?** Revisá la documentación interactiva en http://127.0.0.1:8000/docs