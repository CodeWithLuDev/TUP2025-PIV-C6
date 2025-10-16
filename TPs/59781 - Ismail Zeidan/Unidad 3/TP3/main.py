from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum
import sqlite3
import os

app = FastAPI(title="API de Tareas Persistente")

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
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: Estado
    prioridad: Prioridad
    fecha_creacion: str

class CrearTarea(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Estado = Estado.pendiente
    prioridad: Prioridad = Prioridad.media
    
    def validate_descripcion(self):
        """Valida que la descripción no sea solo espacios en blanco."""
        if not self.descripcion:
            raise ValueError("La descripción no puede contener solo espacios en blanco")

class ActualizarTarea(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Estado] = None
    prioridad: Optional[Prioridad] = None

# ========== CONFIGURACIÓN DE BASE DE DATOS ==========
DB_PATH = "tareas.db"

def get_connection():
    """Obtiene una conexión a la base de datos."""
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
    return conn

def init_db():
    """Inicializa la base de datos y crea la tabla si no existe."""
    if os.path.exists(DB_PATH):
        return
    
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()
    print("✓ Base de datos inicializada correctamente")

def tarea_dict(row):
    """Convierte una fila de SQLite a un diccionario."""
    return {
        "id": row[0],
        "descripcion": row[1],
        "estado": row[2],
        "prioridad": row[3],
        "fecha_creacion": row[4]
    }

# ========== STARTUP ==========
@app.on_event("startup")
def startup_event():
    """Se ejecuta al iniciar la aplicación."""
    init_db()

# ========== RUTAS GET ==========

@app.get("/")
def bienvenida():
    """Ruta de bienvenida."""
    return {
        "titulo": "API de Tareas Persistente",
        "version": "2.0",
        "descripcion": "API con persistencia en SQLite",
        "endpoints": {
            "GET /tareas": "Obtener todas las tareas",
            "POST /tareas": "Crear nueva tarea",
            "PUT /tareas/{id}": "Actualizar tarea",
            "DELETE /tareas/{id}": "Eliminar tarea",
            "GET /tareas/resumen": "Resumen de tareas",
            "PUT /tareas/completar-todas": "Completar todas las tareas"
        }
    }

@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(
    estado: Optional[Estado] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[Prioridad] = Query(None),
    orden: Optional[Orden] = Query(Orden.asc)
):
    """
    Obtiene todas las tareas con filtros opcionales.
    - estado: filtra por estado (pendiente, en_progreso, completada)
    - texto: filtra tareas que contengan el texto en la descripción
    - prioridad: filtra por prioridad (baja, media, alta)
    - orden: ordena por fecha (asc o desc)
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    # Filtrar por estado
    if estado:
        query += " AND estado = ?"
        params.append(estado.value)
    
    # Filtrar por texto
    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")
    
    # Filtrar por prioridad
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad.value)
    
    # Ordenar por fecha
    orden_sql = "DESC" if orden == Orden.desc else "ASC"
    query += f" ORDER BY fecha_creacion {orden_sql}"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    tareas = [tarea_dict(row) for row in rows]
    return tareas

@app.put("/tareas/completar-todas")
def completar_todas1():
    """Marca todas las tareas como completadas."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total = cursor.fetchone()[0]
    
    if total == 0:
        conn.close()
        return {"mensaje": "No hay tareas para completar"}
    
    cursor.execute("UPDATE tareas SET estado = ? WHERE estado != ?", ("completada", "completada"))
    conn.commit()
    conn.close()
    
    return {"mensaje": f"Se completaron {total} tareas"}

@app.get("/tareas/resumen")
def obtener_resumen():
    """Retorna un resumen con el contador de tareas por estado y prioridad."""
    conn = get_connection()
    cursor = conn.cursor()
    
    # Contar por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad FROM tareas GROUP BY estado
    """)
    estados = cursor.fetchall()
    
    # Contar por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad FROM tareas GROUP BY prioridad
    """)
    prioridades = cursor.fetchall()
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total = cursor.fetchone()[0]
    
    conn.close()
    
    resumen_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    resumen_prioridad = {"baja": 0, "media": 0, "alta": 0}
    
    for estado, cantidad in estados:
        resumen_estado[estado] = cantidad
    
    for prioridad, cantidad in prioridades:
        resumen_prioridad[prioridad] = cantidad
    
    return {
        "por_estado": resumen_estado,
        "por_prioridad": resumen_prioridad,
        "total_tareas": total
    }

@app.get("/tareas/{id}", response_model=Tarea)
def obtener_tarea_por_id(id: int):
    """Obtiene una tarea específica por su ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    return tarea_dict(row)

# ========== RUTAS POST ==========

@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(nueva_tarea: CrearTarea):
    """
    Crea una nueva tarea.
    - descripcion: requerida y no puede estar vacía ni solo espacios
    - estado: por defecto "pendiente"
    - prioridad: por defecto "media"
    """
    # Validar que la descripción no sea solo espacios en blanco
    if not nueva_tarea.descripcion.strip():
        raise HTTPException(status_code=422, detail={"error": "La descripción no puede contener solo espacios en blanco"})
    
    conn = get_connection()
    cursor = conn.cursor()
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
        VALUES (?, ?, ?, ?)
    """, (nueva_tarea.descripcion, nueva_tarea.estado.value, nueva_tarea.prioridad.value, fecha_creacion))
    
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": nueva_tarea.descripcion,
        "estado": nueva_tarea.estado,
        "prioridad": nueva_tarea.prioridad,
        "fecha_creacion": fecha_creacion
    }

# ========== RUTAS PUT ==========

@app.get("/tareas/{id}", response_model=Tarea)
def obtener_tarea_por_id1(id: int):
    """Obtiene una tarea específica por su ID."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    row = cursor.fetchone()
    conn.close()
    
    if not row:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    return tarea_dict(row)

# ========== RUTAS PUT ==========

@app.put("/tareas/completar-todas")
def completar_todas():
    """Marca todas las tareas como completadas."""
    conn = get_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total = cursor.fetchone()[0]
    
    if total == 0:
        conn.close()
        return {"mensaje": "No hay tareas para completar"}
    
    cursor.execute("UPDATE tareas SET estado = ? WHERE estado != ?", ("completada", "completada"))
    conn.commit()
    conn.close()
    
    return {"mensaje": f"Se completaron {total} tareas"}

@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea_actualizada: ActualizarTarea):
    """
    Actualiza una tarea existente.
    - Solo se pueden actualizar descripcion, estado y/o prioridad
    - Si la tarea no existe, retorna 404
    """
    conn = get_connection()
    cursor = conn.cursor()
    
    # Verificar que la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    # Preparar datos a actualizar
    descripcion = tarea_actualizada.descripcion if tarea_actualizada.descripcion is not None else tarea[1]
    estado = tarea_actualizada.estado.value if tarea_actualizada.estado is not None else tarea[2]
    prioridad = tarea_actualizada.prioridad.value if tarea_actualizada.prioridad is not None else tarea[3]
    
    cursor.execute("""
        UPDATE tareas SET descripcion = ?, estado = ?, prioridad = ? WHERE id = ?
    """, (descripcion, estado, prioridad, id))
    
    conn.commit()
    conn.close()
    
    return {
        "id": id,
        "descripcion": descripcion,
        "estado": estado,
        "prioridad": prioridad,
        "fecha_creacion": tarea[4]
    }

# ========== RUTAS DELETE ==========

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """
    Elimina una tarea existente por su ID.
    - Si la tarea no existe, retorna 404
    """
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