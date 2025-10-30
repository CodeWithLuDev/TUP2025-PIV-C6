from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum
import sqlite3
import os

app = FastAPI()

# Nombre de la base de datos
DB_NAME = "tareas.db"

# ============== ENUMS ==============

class EstadoTarea(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"

class PrioridadTarea(str, Enum):
    BAJA = "baja"
    MEDIA = "media"
    ALTA = "alta"

# ============== MODELOS PYDANTIC ==============

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1, pattern=r"^\S.*$")
    estado: Optional[EstadoTarea] = EstadoTarea.PENDIENTE
    prioridad: Optional[PrioridadTarea] = PrioridadTarea.MEDIA

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v):
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1, pattern=r"^\S.*$")
    estado: Optional[EstadoTarea] = None
    prioridad: Optional[PrioridadTarea] = None

    @field_validator("descripcion", mode="before")
    @classmethod
    def descripcion_no_vacia(cls, v):
        if v is not None and not v.strip():
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: EstadoTarea
    prioridad: PrioridadTarea
    fecha_creacion: str

class MensajeRespuesta(BaseModel):
    mensaje: str

# ============== FUNCIONES DE BASE DE DATOS ==============

def init_db():
    """Inicializa la base de datos y crea la tabla si no existe"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media',
            fecha_creacion TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Obtiene una conexión a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    return conn

# Inicializar la base de datos al iniciar la aplicación
init_db()

# ============== ENDPOINTS ==============

@app.get("/")
def raiz():
    """Endpoint raíz con información de la API"""
    return {
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

@app.get("/tareas", response_model=list[Tarea])
def obtener_tareas(
    estado: Optional[EstadoTarea] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[PrioridadTarea] = Query(None),
    orden: Optional[str] = Query(None)
):
    """
    Obtiene todas las tareas con filtros opcionales:
    - estado: filtra por estado
    - texto: busca en la descripción
    - prioridad: filtra por prioridad
    - orden: ordena por fecha (asc o desc)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Construir query SQL dinámicamente
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        query += " AND estado = ?"
        params.append(estado.value)
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad.value)
    
    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")
    
    # Ordenamiento
    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    elif orden == "asc":
        query += " ORDER BY fecha_creacion ASC"
    else:
        query += " ORDER BY id"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    # Convertir a diccionarios
    tareas = []
    for row in rows:
        tareas.append({
            "id": row["id"],
            "descripcion": row["descripcion"],
            "estado": row["estado"],
            "prioridad": row["prioridad"],
            "fecha_creacion": row["fecha_creacion"]
        })
    
    return tareas

@app.get("/tareas/resumen")
def obtener_resumen():
    """
    Obtiene un resumen con contadores por estado y prioridad
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Contar total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total = cursor.fetchone()["total"]
    
    # Contar por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad 
        FROM tareas 
        GROUP BY estado
    """)
    estados = cursor.fetchall()
    
    # Contar por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad 
        FROM tareas 
        GROUP BY prioridad
    """)
    prioridades = cursor.fetchall()
    
    conn.close()
    
    # Construir respuesta
    resumen_estados = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for row in estados:
        resumen_estados[row["estado"]] = row["cantidad"]
    
    resumen_prioridades = {
        "baja": 0,
        "media": 0,
        "alta": 0
    }
    
    for row in prioridades:
        resumen_prioridades[row["prioridad"]] = row["cantidad"]
    
    return {
        "total_tareas": total,
        "por_estado": resumen_estados,
        "por_prioridad": resumen_prioridades
    }

@app.put("/tareas/completar_todas")
def completar_todas():
    """Marca todas las tareas como completadas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si hay tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total = cursor.fetchone()["total"]
    
    if total == 0:
        conn.close()
        return {"mensaje": "No hay tareas para completar"}
    
    # Actualizar todas a completada
    cursor.execute("UPDATE tareas SET estado = ?", (EstadoTarea.COMPLETADA.value,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Todas las tareas han sido marcadas como completadas"}

@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(tarea: TareaCreate):
    """Crea una nueva tarea"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fecha_actual = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
        VALUES (?, ?, ?, ?)
    """, (
        tarea.descripcion,
        tarea.estado.value,
        tarea.prioridad.value,
        fecha_actual
    ))
    
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado.value,
        "prioridad": tarea.prioridad.value,
        "fecha_creacion": fecha_actual
    }

@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea_update: TareaUpdate):
    """Actualiza una tarea existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actual = cursor.fetchone()
    
    if not tarea_actual:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    # Actualizar campos proporcionados
    nueva_descripcion = tarea_update.descripcion if tarea_update.descripcion else tarea_actual["descripcion"]
    nuevo_estado = tarea_update.estado.value if tarea_update.estado else tarea_actual["estado"]
    nueva_prioridad = tarea_update.prioridad.value if tarea_update.prioridad else tarea_actual["prioridad"]
    
    cursor.execute("""
        UPDATE tareas 
        SET descripcion = ?, estado = ?, prioridad = ?
        WHERE id = ?
    """, (nueva_descripcion, nuevo_estado, nueva_prioridad, id))
    
    conn.commit()
    
    # Obtener tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()
    
    return {
        "id": tarea_actualizada["id"],
        "descripcion": tarea_actualizada["descripcion"],
        "estado": tarea_actualizada["estado"],
        "prioridad": tarea_actualizada["prioridad"],
        "fecha_creacion": tarea_actualizada["fecha_creacion"]
    }

@app.delete("/tareas/{id}", response_model=MensajeRespuesta)
def eliminar_tarea(id: int):
    """Elimina una tarea"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    # Eliminar
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return MensajeRespuesta(mensaje="Tarea eliminada correctamente")