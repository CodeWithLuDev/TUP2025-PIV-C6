# 📝 API de Tareas con FastAPI y SQLite

Una API REST completa para gestionar tareas con persistencia en SQLite, filtros avanzados y validación con Pydantic.

## 🚀 Características

- ✅ CRUD completo de tareas
- 💾 Persistencia en SQLite
- 🔍 Filtros por estado, prioridad y texto
- 📊 Endpoint de resumen estadístico
- ⚡ Validación automática con Pydantic
- 📚 Documentación interactiva automática (Swagger)

## 📋 Requisitos

- Python 3.7+
- pip (gestor de paquetes de Python)

## 🔧 Instalación

### 1. Crear entorno virtual

**Windows:**
```bash
python -m venv venv
venv\Scripts\activate
```

**Linux/Mac:**
```bash
python3 -m venv venv
source venv/bin/activate
```

### 2. Instalar dependencias

```bash
pip install fastapi uvicorn sqlite3 pydantic
```

O si tienes un archivo `requirements.txt`:
```bash
pip install -r requirements.txt
```

## ▶️ Iniciar el Servidor

### Opción 1: Ejecución directa
```bash
python main.py
```

### Opción 2: Con uvicorn (recomendado)
```bash
uvicorn main:app --reload
```

### Opción 3: Especificando host y puerto
```bash
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

El servidor estará disponible en: **http://127.0.0.1:8000**

## 📖 Documentación Interactiva

Una vez iniciado el servidor, accede a:

- **Swagger UI**: http://127.0.0.1:8000/docs
- **ReDoc**: http://127.0.0.1:8000/redoc

Desde ahí puedes probar todos los endpoints directamente.

## 🛣️ Endpoints Disponibles

### 1. Información de la API
```http
GET /
```

**Respuesta:**
```json
{
  "nombre": "API de Tareas",
  "version": "1.0.0",
  "endpoints": [...]
}
```

---

### 2. Crear Tarea
```http
POST /tareas
Content-Type: application/json
```

**Body:**
```json
{
  "descripcion": "Comprar pan",
  "estado": "pendiente",
  "prioridad": "alta"
}
```

**Campos:**
- `descripcion` (string, requerido): No puede estar vacía
- `estado` (string, opcional): `pendiente`, `en_progreso`, `completada` (default: `pendiente`)
- `prioridad` (string, opcional): `baja`, `media`, `alta` (default: `media`)

**Respuesta (201):**
```json
{
  "id": 1,
  "descripcion": "Comprar pan",
  "estado": "pendiente",
  "prioridad": "alta",
  "fecha_creacion": "2025-10-17T14:30:00.000000"
}
```

---

### 3. Listar Tareas (con filtros)
```http
GET /tareas
GET /tareas?estado=pendiente
GET /tareas?prioridad=alta
GET /tareas?texto=comprar
GET /tareas?estado=pendiente&prioridad=alta&orden=desc
```

**Query Parameters:**
- `estado`: Filtrar por estado (`pendiente`, `en_progreso`, `completada`)
- `prioridad`: Filtrar por prioridad (`baja`, `media`, `alta`)
- `texto`: Buscar en descripción (case-insensitive)
- `orden`: Ordenar por fecha (`asc` o `desc`, default: `asc`)

**Respuesta (200):**
```json
[
  {
    "id": 1,
    "descripcion": "Comprar pan",
    "estado": "pendiente",
    "prioridad": "alta",
    "fecha_creacion": "2025-10-17T14:30:00.000000"
  },
  {
    "id": 2,
    "descripcion": "Estudiar Python",
    "estado": "en_progreso",
    "prioridad": "media",
    "fecha_creacion": "2025-10-17T15:00:00.000000"
  }
]
```

---

### 4. Actualizar Tarea
```http
PUT /tareas/{id}
Content-Type: application/json
```

**Body (todos los campos opcionales):**
```json
{
  "descripcion": "Comprar pan integral",
  "estado": "completada",
  "prioridad": "baja"
}
```

**Respuesta (200):**
```json
{
  "id": 1,
  "descripcion": "Comprar pan integral",
  "estado": "completada",
  "prioridad": "baja",
  "fecha_creacion": "2025-10-17T14:30:00.000000"
}
```

**Errores:**
- `404`: Tarea no encontrada

---

### 5. Eliminar Tarea
```http
DELETE /tareas/{id}
```

**Respuesta (200):**
```json
{
  "mensaje": "Tarea 1 eliminada exitosamente"
}
```

**Errores:**
- `404`: Tarea no encontrada

---

### 6. Resumen de Tareas
```http
GET /tareas/resumen
```

**Respuesta (200):**
```json
{
  "total_tareas": 5,
  "por_estado": {
    "pendiente": 2,
    "en_progreso": 1,
    "completada": 2
  },
  "por_prioridad": {
    "alta": 2,
    "media": 2,
    "baja": 1
  }
}
```

---

### 7. Completar Todas las Tareas
```http
PUT /tareas/completar_todas
```

**Respuesta (200):**
```json
{
  "mensaje": "Se completaron 5 tareas"
}
```

---

## 💡 Ejemplos con cURL

### Crear una tarea
```bash
curl -X POST http://127.0.0.1:8000/tareas \
  -H "Content-Type: application/json" \
  -d '{
    "descripcion": "Estudiar FastAPI",
    "estado": "pendiente",
    "prioridad": "alta"
  }'
```

### Listar todas las tareas
```bash
curl http://127.0.0.1:8000/tareas
```

### Filtrar tareas pendientes de alta prioridad
```bash
curl "http://127.0.0.1:8000/tareas?estado=pendiente&prioridad=alta"
```

### Actualizar una tarea
```bash
curl -X PUT http://127.0.0.1:8000/tareas/1 \
  -H "Content-Type: application/json" \
  -d '{
    "estado": "completada"
  }'
```

### Eliminar una tarea
```bash
curl -X DELETE http://127.0.0.1:8000/tareas/1
```

### Obtener resumen
```bash
curl http://127.0.0.1:8000/tareas/resumen
```

---

## 🧪 Ejecutar Tests

```bash
# Instalar pytest si no lo tienes
pip install pytest httpx

# Ejecutar todos los tests
pytest test_TP3.py -v

# Ejecutar un test específico
pytest test_TP3.py::test_crear_tarea -v
```

---

## 📁 Estructura del Proyecto

```
proyecto/
├── venv/              # Entorno virtual (no subir a git)
├── main.py            # Código principal de la API
├── test_TP3.py        # Tests automatizados
├── tareas.db          # Base de datos SQLite (se crea automáticamente)
├── README.md          # Este archivo
└── requirements.txt   # Dependencias (opcional)
```

---

## 🗄️ Base de Datos

La aplicación usa SQLite con la siguiente estructura:

**Tabla: `tareas`**
| Campo | Tipo | Restricciones |
|-------|------|---------------|
| id | INTEGER | PRIMARY KEY, AUTOINCREMENT |
| descripcion | TEXT | NOT NULL |
| estado | TEXT | NOT NULL |
| fecha_creacion | TEXT | NOT NULL |
| prioridad | TEXT | NOT NULL, DEFAULT 'media' |

---

## ⚠️ Códigos de Estado HTTP

- `200 OK`: Operación exitosa
- `201 Created`: Recurso creado exitosamente
- `404 Not Found`: Recurso no encontrado
- `422 Unprocessable Entity`: Error de validación

---

## 🛡️ Validaciones

- La descripción no puede estar vacía ni contener solo espacios
- Estados válidos: `pendiente`, `en_progreso`, `completada`
- Prioridades válidas: `baja`, `media`, `alta`
- Todos los campos son validados automáticamente por Pydantic

---

## 🤝 Contribuir

1. Fork el proyecto
2. Crea una rama para tu feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit tus cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Abre un Pull Request

---

## 📝 Licencia

Este proyecto es de código abierto y está disponible bajo la Licencia MIT.

---

## 👨‍💻 Autor

Desarrollado como proyecto educativo para aprender FastAPI y SQLite.

---

## 📞 Soporte

Si tienes problemas:
1. Verifica que todas las dependencias estén instaladas
2. Asegúrate de que el puerto 8000 esté libre
3. Revisa los logs del servidor en la terminal
4. Consulta la documentación en `/docs`

---

**¡Disfruta desarrollando con FastAPI! 🚀**