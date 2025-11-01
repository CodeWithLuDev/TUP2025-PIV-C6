from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
import sqlite3
from contextlib import asynccontextmanager

# Constantes
DB_NAME = "test.db"
VALID_ESTADOS = {"pendiente", "en_progreso", "completada"}
VALID_PRIORIDADES = {"baja", "media", "alta"}


# ============== MODELOS PYDANTIC V2 ==============

class ProyectoCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v):
        if not v or v.strip() == "":
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()


class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def nombre_no_vacio(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError('El nombre no puede estar vacío')
        return v.strip() if v else None


class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str = "pendiente"
    prioridad: str = "media"
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_no_vacia(cls, v):
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()
    
    @field_validator('estado')
    @classmethod
    def estado_valido(cls, v):
        if v not in VALID_ESTADOS:
            raise ValueError(f'Estado inválido. Debe ser: {", ".join(VALID_ESTADOS)}')
        return v
    
    @field_validator('prioridad')
    @classmethod
    def prioridad_valida(cls, v):
        if v not in VALID_PRIORIDADES:
            raise ValueError(f'Prioridad inválida. Debe ser: {", ".join(VALID_PRIORIDADES)}')
        return v


# ============== INICIALIZACIÓN DE BASE DE DATOS ==============

def init_db():
    """Inicializa la base de datos con las tablas necesarias"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Habilitar foreign keys
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Crear tabla proyectos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        )
    """)
    
    # Crear tabla tareas con clave foránea
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL DEFAULT 'pendiente',
            prioridad TEXT NOT NULL DEFAULT 'media',
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()


# Lifespan event handler (FastAPI moderno)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Startup
    init_db()
    yield
    # Shutdown (si necesitas limpiar algo)


# Inicializar app con lifespan
app = FastAPI(lifespan=lifespan)


# Helper para conexión
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    # Habilitar foreign keys en cada conexión
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ============== ENDPOINTS DE PROYECTOS ==============

@app.post("/proyectos")
async def crear_proyecto(request: Request):
    """Crear un nuevo proyecto"""
    try:
        payload = await request.json()
        proyecto = ProyectoCreate(**payload)
    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=422)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar nombre duplicado
    cursor.execute("SELECT id FROM proyectos WHERE nombre = ?", (proyecto.nombre,))
    if cursor.fetchone():
        conn.close()
        return JSONResponse({"detail": "Ya existe un proyecto con ese nombre"}, status_code=409)
    
    # Insertar proyecto
    fecha_creacion = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
        VALUES (?, ?, ?)
    """, (proyecto.nombre, proyecto.descripcion, fecha_creacion))
    
    conn.commit()
    proyecto_id = cursor.lastrowid
    
    # Obtener proyecto creado
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    nuevo_proyecto = dict(cursor.fetchone())
    conn.close()
    
    return JSONResponse(nuevo_proyecto, status_code=201)


@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = None):
    """Listar todos los proyectos con filtro opcional por nombre"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM proyectos WHERE 1=1"
    params = []
    
    if nombre:
        query += " AND nombre LIKE ?"
        params.append(f"%{nombre}%")
    
    cursor.execute(query, params)
    proyectos = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return JSONResponse(proyectos, status_code=200)


@app.get("/proyectos/{proyecto_id}/resumen")
def resumen_proyecto(proyecto_id: int):
    """Obtener resumen estadístico de un proyecto"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        return JSONResponse({"detail": "Proyecto no encontrado"}, status_code=404)
    
    proyecto_dict = dict(proyecto)
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    total_tareas = cursor.fetchone()["total"]
    
    # Tareas por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        WHERE proyecto_id = ?
        GROUP BY estado
    """, (proyecto_id,))
    
    por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for row in cursor.fetchall():
        por_estado[row["estado"]] = row["cantidad"]
    
    # Tareas por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad
        FROM tareas
        WHERE proyecto_id = ?
        GROUP BY prioridad
    """, (proyecto_id,))
    
    por_prioridad = {"baja": 0, "media": 0, "alta": 0}
    for row in cursor.fetchall():
        por_prioridad[row["prioridad"]] = row["cantidad"]
    
    conn.close()
    
    return JSONResponse({
        "proyecto_id": proyecto_id,
        "proyecto_nombre": proyecto_dict["nombre"],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }, status_code=200)


@app.get("/proyectos/{proyecto_id}")
def obtener_proyecto(proyecto_id: int):
    """Obtener proyecto específico con contador de tareas"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Obtener proyecto
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        return JSONResponse({"detail": "Proyecto no encontrado"}, status_code=404)
    
    proyecto_dict = dict(proyecto)
    
    # Contar tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    total_tareas = cursor.fetchone()["total"]
    
    proyecto_dict["total_tareas"] = total_tareas
    conn.close()
    
    return JSONResponse(proyecto_dict, status_code=200)


@app.put("/proyectos/{proyecto_id}")
async def actualizar_proyecto(proyecto_id: int, request: Request):
    """Actualizar un proyecto existente"""
    try:
        payload = await request.json()
        proyecto_update = ProyectoUpdate(**payload)
    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=422)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        return JSONResponse({"detail": "Proyecto no encontrado"}, status_code=404)
    
    # Construir actualización
    updates = []
    params = []
    
    if proyecto_update.nombre is not None:
        # Verificar duplicado
        cursor.execute("SELECT id FROM proyectos WHERE nombre = ? AND id != ?", 
                      (proyecto_update.nombre, proyecto_id))
        if cursor.fetchone():
            conn.close()
            return JSONResponse({"detail": "Ya existe un proyecto con ese nombre"}, status_code=409)
        updates.append("nombre = ?")
        params.append(proyecto_update.nombre)
    
    if proyecto_update.descripcion is not None:
        updates.append("descripcion = ?")
        params.append(proyecto_update.descripcion)
    
    if updates:
        params.append(proyecto_id)
        query = f"UPDATE proyectos SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    # Obtener proyecto actualizado
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto_actualizado = dict(cursor.fetchone())
    conn.close()
    
    return JSONResponse(proyecto_actualizado, status_code=200)


@app.delete("/proyectos/{proyecto_id}")
def eliminar_proyecto(proyecto_id: int):
    """Eliminar proyecto y sus tareas (CASCADE)"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        return JSONResponse({"detail": "Proyecto no encontrado"}, status_code=404)
    
    # Contar tareas antes de eliminar
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    tareas_eliminadas = cursor.fetchone()["total"]
    
    # Eliminar proyecto (CASCADE eliminará las tareas)
    cursor.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
    conn.commit()
    conn.close()
    
    return JSONResponse({
        "mensaje": "Proyecto eliminado",
        "tareas_eliminadas": tareas_eliminadas
    }, status_code=200)


# ============== ENDPOINTS DE TAREAS ==============

@app.post("/proyectos/{proyecto_id}/tareas")
async def crear_tarea(proyecto_id: int, request: Request):
    """Crear tarea dentro de un proyecto"""
    try:
        payload = await request.json()
        tarea = TareaCreate(**payload)
    except Exception as e:
        return JSONResponse({"detail": str(e)}, status_code=422)
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        return JSONResponse({"detail": "El proyecto no existe"}, status_code=400)
    
    # Insertar tarea
    fecha_creacion = datetime.now().isoformat()
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, proyecto_id, fecha_creacion))
    
    conn.commit()
    tarea_id = cursor.lastrowid
    
    # Obtener tarea creada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    nueva_tarea = dict(cursor.fetchone())
    conn.close()
    
    return JSONResponse(nueva_tarea, status_code=201)


@app.get("/proyectos/{proyecto_id}/tareas")
def listar_tareas_proyecto(proyecto_id: int):
    """Listar tareas de un proyecto específico"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        return JSONResponse({"detail": "Proyecto no encontrado"}, status_code=404)
    
    # Obtener tareas
    cursor.execute("SELECT * FROM tareas WHERE proyecto_id = ? ORDER BY fecha_creacion DESC", (proyecto_id,))
    tareas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return JSONResponse(tareas, status_code=200)


@app.get("/tareas")
def listar_todas_tareas(
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    proyecto_id: Optional[int] = None,
    orden: Optional[str] = None
):
    """Listar todas las tareas con filtros opcionales"""
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if proyecto_id:
        query += " AND proyecto_id = ?"
        params.append(proyecto_id)
    
    # Ordenamiento
    if orden and orden.lower() in ["asc", "desc"]:
        query += f" ORDER BY fecha_creacion {orden.upper()}"
    else:
        query += " ORDER BY fecha_creacion DESC"
    
    cursor.execute(query, params)
    tareas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    
    return JSONResponse(tareas, status_code=200)


@app.put("/tareas/{tarea_id}")
async def actualizar_tarea(tarea_id: int, request: Request):
    """Actualizar una tarea existente"""
    # Leer payload sin validación estricta de Pydantic primero
    payload = await request.json()
    
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        conn.close()
        return JSONResponse({"detail": "Tarea no encontrada"}, status_code=404)
    
    # Si se cambia proyecto_id, verificar que existe
    if "proyecto_id" in payload:
        cursor.execute("SELECT id FROM proyectos WHERE id = ?", (payload["proyecto_id"],))
        if not cursor.fetchone():
            conn.close()
            return JSONResponse({"detail": "El proyecto destino no existe"}, status_code=400)
    
    # Construir actualización manualmente
    updates = []
    params = []
    
    if "descripcion" in payload:
        descripcion = payload["descripcion"].strip() if payload["descripcion"] else ""
        if not descripcion:
            conn.close()
            return JSONResponse({"detail": "La descripción no puede estar vacía"}, status_code=422)
        updates.append("descripcion = ?")
        params.append(descripcion)
    
    if "estado" in payload:
        if payload["estado"] not in VALID_ESTADOS:
            conn.close()
            return JSONResponse({"detail": "Estado inválido"}, status_code=422)
        updates.append("estado = ?")
        params.append(payload["estado"])
    
    if "prioridad" in payload:
        if payload["prioridad"] not in VALID_PRIORIDADES:
            conn.close()
            return JSONResponse({"detail": "Prioridad inválida"}, status_code=422)
        updates.append("prioridad = ?")
        params.append(payload["prioridad"])
    
    if "proyecto_id" in payload:
        updates.append("proyecto_id = ?")
        params.append(payload["proyecto_id"])
    
    if updates:
        params.append(tarea_id)
        query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    # Obtener tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea_actualizada = dict(cursor.fetchone())
    conn.close()
    
    return JSONResponse(tarea_actualizada, status_code=200)


@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    """Eliminar una tarea específica"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        conn.close()
        return JSONResponse({"detail": "Tarea no encontrada"}, status_code=404)
    
    # Eliminar tarea
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    
    return JSONResponse({"mensaje": "Tarea eliminada"}, status_code=200)


# ============== ENDPOINTS DE RESUMEN Y ESTADÍSTICAS ==============

@app.get("/resumen")
def resumen_general():
    """Obtener resumen general de toda la aplicación"""
    conn = get_db()
    cursor = conn.cursor()
    
    # Total de proyectos
    cursor.execute("SELECT COUNT(*) as total FROM proyectos")
    total_proyectos = cursor.fetchone()["total"]
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total_tareas = cursor.fetchone()["total"]
    
    # Tareas por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        GROUP BY estado
    """)
    
    tareas_por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for row in cursor.fetchall():
        tareas_por_estado[row["estado"]] = row["cantidad"]
    
    # Proyecto con más tareas
    cursor.execute("""
        SELECT proyecto_id, COUNT(*) as cantidad_tareas
        FROM tareas
        GROUP BY proyecto_id
        ORDER BY cantidad_tareas DESC
        LIMIT 1
    """)
    
    proyecto_max = cursor.fetchone()
    
    proyecto_con_mas_tareas = None
    if proyecto_max:
        proyecto_con_mas_tareas = {
            "id": proyecto_max["proyecto_id"],
            "cantidad_tareas": proyecto_max["cantidad_tareas"]
        }
    
    conn.close()
    
    resumen = {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado
    }
    
    if proyecto_con_mas_tareas:
        resumen["proyecto_con_mas_tareas"] = proyecto_con_mas_tareas
    
    return JSONResponse(resumen, status_code=200)