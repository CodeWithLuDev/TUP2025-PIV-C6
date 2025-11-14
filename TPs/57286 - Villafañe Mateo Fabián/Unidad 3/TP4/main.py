import sqlite3
from contextlib import asynccontextmanager
from datetime import datetime
from enum import Enum
from typing import Optional, List, Literal

from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator

# ========== LIFESPAN ==========
@asynccontextmanager
async def lifespan(app: FastAPI):
    """Maneja el ciclo de vida de la aplicación."""
    # Startup
    init_db()
    yield
    # Shutdown (si se necesita algo en el futuro)

app = FastAPI(title="API de Tareas y Proyectos", lifespan=lifespan)

# ========== ENUMS ==========
class Estado(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

class Prioridad(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"

class Orden(str, Enum):
    asc = "asc"
    desc = "desc"

# ========== MODELOS PYDANTIC ==========

# Modelos de Proyecto
class ProyectoCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío o contener solo espacios")
        return v.strip()

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1)
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    @classmethod
    def validar_nombre(cls, v):
        if v is not None and not v.strip():
            raise ValueError("El nombre no puede estar vacío o contener solo espacios")
        return v.strip() if v else None

class Proyecto(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str
    total_tareas: Optional[int] = 0

# Modelos de Tarea
class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    proyecto_id: Optional[int] = None  # Opcional para compatibilidad con TP3
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v.strip()

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and not v.strip():
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v.strip() if v else None

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    prioridad: str
    proyecto_id: int
    fecha_creacion: str

# ========== CONFIGURACIÓN DE BASE DE DATOS ==========
DB_PATH = "tareas.db"
DB_NAME = DB_PATH  # Alias para compatibilidad con tests

def get_connection():
    """Obtiene una conexión a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  # Habilitar claves foráneas
    return conn

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Crear tabla proyectos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        )
    """)
    
    # Crear tabla tareas con relación a proyectos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()
    print("✓ Base de datos inicializada correctamente")

# ========== RUTAS PRINCIPALES ==========

@app.get("/")
def bienvenida():
    """Ruta de bienvenida."""
    return {
        "nombre": "API de Tareas y Proyectos",
        "version": "3.0",
        "descripcion": "API con proyectos y tareas relacionadas",
        "endpoints": {
            "GET /proyectos": "Listar proyectos",
            "POST /proyectos": "Crear proyecto",
            "GET /proyectos/{id}": "Obtener proyecto",
            "PUT /proyectos/{id}": "Actualizar proyecto",
            "DELETE /proyectos/{id}": "Eliminar proyecto",
            "GET /proyectos/{id}/tareas": "Listar tareas de un proyecto",
            "POST /proyectos/{id}/tareas": "Crear tarea en proyecto",
            "GET /proyectos/{id}/resumen": "Resumen de proyecto",
            "GET /tareas": "Listar todas las tareas",
            "POST /tareas": "Crear tarea",
            "GET /tareas/{id}": "Obtener tarea",
            "PUT /tareas/{id}": "Actualizar tarea",
            "DELETE /tareas/{id}": "Eliminar tarea",
            "GET /tareas/resumen": "Resumen de tareas",
            "PUT /tareas/completar_todas": "Completar todas las tareas",
            "GET /resumen": "Resumen general"
        }
    }

# ========== ENDPOINTS DE PROYECTOS ==========

@app.get("/proyectos", response_model=List[Proyecto])
def listar_proyectos(nombre: Optional[str] = Query(None)):
    """
    Lista todos los proyectos.
    - nombre: filtra proyectos que contengan el texto en el nombre
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = """
        SELECT p.*, COUNT(t.id) as cantidad_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        WHERE 1=1
    """
    params = []
    
    if nombre:
        query += " AND p.nombre LIKE ?"
        params.append(f"%{nombre}%")
    
    query += " GROUP BY p.id ORDER BY p.fecha_creacion DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    proyectos = []
    for row in rows:
        proyectos.append({
            "id": row[0],
            "nombre": row[1],
            "descripcion": row[2],
            "fecha_creacion": row[3],
            "total_tareas": row[4]
        })
    
    return proyectos

@app.get("/proyectos/{id}", response_model=Proyecto)
def obtener_proyecto(id: int):
    """Obtiene un proyecto específico con el contador de tareas."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.*, COUNT(t.id) as cantidad_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        WHERE p.id = ?
        GROUP BY p.id
    """, (id,))
    
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail={"error": "El proyecto no existe"})
    
    return {
        "id": row[0],
        "nombre": row[1],
        "descripcion": row[2],
        "fecha_creacion": row[3],
        "total_tareas": row[4]
    }

@app.post("/proyectos", response_model=Proyecto, status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    """Crea un nuevo proyecto."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar si ya existe un proyecto con ese nombre
    cursor.execute("SELECT id FROM proyectos WHERE nombre = ?", (proyecto.nombre,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail={"error": "Ya existe un proyecto con ese nombre"})
    
    fecha_creacion = datetime.now().isoformat()
    
    try:
        cursor.execute("""
            INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
            VALUES (?, ?, ?)
        """, (proyecto.nombre, proyecto.descripcion, fecha_creacion))
        
        conn.commit()
        proyecto_id = cursor.lastrowid
        conn.close()
        
        return {
            "id": proyecto_id,
            "nombre": proyecto.nombre,
            "descripcion": proyecto.descripcion,
            "fecha_creacion": fecha_creacion,
            "total_tareas": 0
        }
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=409, detail={"error": "Ya existe un proyecto con ese nombre"})

@app.put("/proyectos/{id}", response_model=Proyecto)
def actualizar_proyecto(id: int, proyecto: ProyectoUpdate):
    """Modifica un proyecto existente."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto_actual = cursor.fetchone()
    
    if not proyecto_actual:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "El proyecto no existe"})
    
    # Si se cambia el nombre, verificar que no exista otro con ese nombre
    if proyecto.nombre and proyecto.nombre != proyecto_actual[1]:
        cursor.execute("SELECT id FROM proyectos WHERE nombre = ? AND id != ?", (proyecto.nombre, id))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=409, detail={"error": "Ya existe un proyecto con ese nombre"})
    
    nombre = proyecto.nombre if proyecto.nombre is not None else proyecto_actual[1]
    descripcion = proyecto.descripcion if proyecto.descripcion is not None else proyecto_actual[2]
    
    cursor.execute("""
        UPDATE proyectos SET nombre = ?, descripcion = ? WHERE id = ?
    """, (nombre, descripcion, id))
    
    # Obtener cantidad de tareas
    cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?", (id,))
    total_tareas = cursor.fetchone()[0]
    
    conn.commit()
    conn.close()
    
    return {
        "id": id,
        "nombre": nombre,
        "descripcion": descripcion,
        "fecha_creacion": proyecto_actual[3],
        "total_tareas": total_tareas
    }

@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    """Elimina un proyecto y todas sus tareas asociadas."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "El proyecto no existe"})
    
    # Contar tareas antes de eliminar
    cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?", (id,))
    tareas_eliminadas = cursor.fetchone()[0]
    
    # Eliminar proyecto (las tareas se eliminan automáticamente por ON DELETE CASCADE)
    cursor.execute("DELETE FROM proyectos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {
        "mensaje": "Proyecto y sus tareas eliminados correctamente",
        "tareas_eliminadas": tareas_eliminadas
    }

# ========== ENDPOINTS DE TAREAS DE UN PROYECTO ==========

@app.get("/proyectos/{id}/tareas", response_model=List[Tarea])
def listar_tareas_proyecto(
    id: int,
    estado: Optional[Estado] = Query(None),
    prioridad: Optional[Prioridad] = Query(None),
    orden: Optional[Orden] = Query(Orden.asc)
):
    """Lista todas las tareas de un proyecto específico."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "El proyecto no existe"})
    
    query = "SELECT * FROM tareas WHERE proyecto_id = ?"
    params = [id]
    
    if estado:
        query += " AND estado = ?"
        params.append(estado.value)
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad.value)
    
    orden_sql = "DESC" if orden == Orden.desc else "ASC"
    query += f" ORDER BY fecha_creacion {orden_sql}"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    tareas = []
    for row in rows:
        tareas.append({
            "id": row[0],
            "descripcion": row[1],
            "estado": row[2],
            "prioridad": row[3],
            "proyecto_id": row[4],
            "fecha_creacion": row[5]
        })
    
    return tareas

@app.post("/proyectos/{id}/tareas", response_model=Tarea, status_code=201)
def crear_tarea_en_proyecto(id: int, tarea: TareaCreate):
    """Crea una nueva tarea dentro de un proyecto."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail={"error": "El proyecto no existe"})
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, id, fecha_creacion))
    
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "prioridad": tarea.prioridad,
        "proyecto_id": id,
        "fecha_creacion": fecha_creacion
    }

# ========== ENDPOINTS DE TAREAS GENERALES ==========

@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea_general(tarea: TareaCreate):
    """
    Crea una nueva tarea. Si no se especifica proyecto_id, se crea un proyecto por defecto.
    Mantiene compatibilidad con TP3.
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    proyecto_id = tarea.proyecto_id
    
    # Si no se especifica proyecto, crear o usar proyecto por defecto
    if proyecto_id is None:
        cursor.execute("SELECT id FROM proyectos WHERE nombre = ?", ("Proyecto Por Defecto",))
        proyecto_defecto = cursor.fetchone()
        
        if not proyecto_defecto:
            # Crear proyecto por defecto
            fecha_creacion = datetime.now().isoformat()
            cursor.execute("""
                INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
                VALUES (?, ?, ?)
            """, ("Proyecto Por Defecto", "Tareas sin proyecto asignado", fecha_creacion))
            conn.commit()
            proyecto_id = cursor.lastrowid
        else:
            proyecto_id = proyecto_defecto[0]
    else:
        # Verificar que el proyecto existe
        cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail={"error": "El proyecto no existe"})
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, proyecto_id, fecha_creacion))
    
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "prioridad": tarea.prioridad,
        "proyecto_id": proyecto_id,
        "fecha_creacion": fecha_creacion
    }

@app.get("/tareas", response_model=List[Tarea])
def listar_tareas(
    estado: Optional[Estado] = Query(None),
    prioridad: Optional[Prioridad] = Query(None),
    proyecto_id: Optional[int] = Query(None),
    orden: Optional[Orden] = Query(Orden.asc)
):
    """
    Lista todas las tareas con filtros opcionales.
    - estado: filtra por estado
    - prioridad: filtra por prioridad
    - proyecto_id: filtra por proyecto
    - orden: ordena por fecha (asc o desc)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        query += " AND estado = ?"
        params.append(estado.value)
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad.value)
    
    if proyecto_id:
        query += " AND proyecto_id = ?"
        params.append(proyecto_id)
    
    orden_sql = "DESC" if orden == Orden.desc else "ASC"
    query += f" ORDER BY fecha_creacion {orden_sql}"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    tareas = []
    for row in rows:
        tareas.append({
            "id": row[0],
            "descripcion": row[1],
            "estado": row[2],
            "prioridad": row[3],
            "proyecto_id": row[4],
            "fecha_creacion": row[5]
        })
    
    return tareas

@app.get("/tareas/{id}", response_model=Tarea)
def obtener_tarea(id: int):
    """Obtiene una tarea específica por su ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    return {
        "id": row[0],
        "descripcion": row[1],
        "estado": row[2],
        "prioridad": row[3],
        "proyecto_id": row[4],
        "fecha_creacion": row[5]
    }

@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea: TareaUpdate):
    """Actualiza una tarea existente (puede cambiar de proyecto)."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actual = cursor.fetchone()
    
    if not tarea_actual:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    # Si se cambia el proyecto, verificar que existe
    proyecto_id = tarea.proyecto_id if tarea.proyecto_id is not None else tarea_actual[4]
    if tarea.proyecto_id is not None and tarea.proyecto_id != tarea_actual[4]:
        cursor.execute("SELECT id FROM proyectos WHERE id = ?", (tarea.proyecto_id,))
        if not cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail={"error": "El proyecto destino no existe"})
    
    descripcion = tarea.descripcion if tarea.descripcion is not None else tarea_actual[1]
    estado = tarea.estado if tarea.estado is not None else tarea_actual[2]
    prioridad = tarea.prioridad if tarea.prioridad is not None else tarea_actual[3]
    
    cursor.execute("""
        UPDATE tareas SET descripcion = ?, estado = ?, prioridad = ?, proyecto_id = ?
        WHERE id = ?
    """, (descripcion, estado, prioridad, proyecto_id, id))
    
    conn.commit()
    conn.close()
    
    return {
        "id": id,
        "descripcion": descripcion,
        "estado": estado,
        "prioridad": prioridad,
        "proyecto_id": proyecto_id,
        "fecha_creacion": tarea_actual[5]
    }

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """Elimina una tarea existente por su ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada correctamente"}

# ========== ENDPOINTS DE RESUMEN Y ESTADÍSTICAS ==========

@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    """Devuelve estadísticas del proyecto."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT nombre FROM proyectos WHERE id = ?", (id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "El proyecto no existe"})
    
    # Contar total de tareas
    cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?", (id,))
    total_tareas = cursor.fetchone()[0]
    
    # Contar por estado
    cursor.execute("""
        SELECT estado, COUNT(*) FROM tareas WHERE proyecto_id = ? GROUP BY estado
    """, (id,))
    estados = cursor.fetchall()
    
    # Contar por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) FROM tareas WHERE proyecto_id = ? GROUP BY prioridad
    """, (id,))
    prioridades = cursor.fetchall()
    
    conn.close()
    
    por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for estado, cantidad in estados:
        por_estado[estado] = cantidad
    
    por_prioridad = {"baja": 0, "media": 0, "alta": 0}
    for prioridad, cantidad in prioridades:
        por_prioridad[prioridad] = cantidad
    
    return {
        "proyecto_id": id,
        "proyecto_nombre": proyecto[0],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.get("/resumen")
def resumen_general():
    """Resumen general de toda la aplicación."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Total de proyectos
    cursor.execute("SELECT COUNT(*) FROM proyectos")
    total_proyectos = cursor.fetchone()[0]
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total_tareas = cursor.fetchone()[0]
    
    # Tareas por estado
    cursor.execute("SELECT estado, COUNT(*) FROM tareas GROUP BY estado")
    estados = cursor.fetchall()
    
    # Proyecto con más tareas
    cursor.execute("""
        SELECT p.id, p.nombre, COUNT(t.id) as cantidad
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        GROUP BY p.id
        ORDER BY cantidad DESC
        LIMIT 1
    """)
    proyecto_top = cursor.fetchone()
    
    conn.close()
    
    tareas_por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for estado, cantidad in estados:
        tareas_por_estado[estado] = cantidad
    
    proyecto_con_mas_tareas = None
    if proyecto_top:
        proyecto_con_mas_tareas = {
            "id": proyecto_top[0],
            "nombre": proyecto_top[1],
            "cantidad_tareas": proyecto_top[2]
        }
    
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas_tareas
    }