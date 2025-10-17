from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
import sqlite3

app = FastAPI(title="API de Gestión de Tareas Persistente")

DB_NAME = "tareas.db"


class Estado(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

class Prioridad(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: Estado
    fecha_creacion: str
    prioridad: Prioridad

class TareaCreate(BaseModel):
    descripcion: str
    estado: Optional[Estado] = Estado.pendiente
    prioridad: Optional[Prioridad] = Prioridad.media

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Estado] = None
    prioridad: Optional[Prioridad] = None


def init_db():
    """Crea la base de datos y la tabla si no existen"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL,
            prioridad TEXT NOT NULL
        )
    """)
    
    conn.commit()
    conn.close()


init_db()

def validar_estado(estado: str):
    estados_validos = {"pendiente", "en_progreso", "completada"}
    if estado not in estados_validos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "Estado inválido. Debe ser 'pendiente', 'en_progreso' o 'completada'"}
        )

def validar_prioridad(prioridad: str):
    prioridades_validas = {"baja", "media", "alta"}
    if prioridad not in prioridades_validas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "Prioridad inválida. Debe ser 'baja', 'media' o 'alta'"}
        )

@app.get("/")
def root():
    """Información de la API"""
    return {
        "nombre": "API de Gestión de Tareas Persistente",
        "version": "3.0",
        "endpoints": [
            "GET /tareas",
            "POST /tareas",
            "PUT /tareas/{id}",
            "DELETE /tareas/{id}",
            "GET /tareas/resumen",
            "PUT /tareas/completar_todas"
        ]
    }

@app.get("/tareas/resumen")
def get_resumen():
    """Obtiene un resumen de las tareas por estado y prioridad"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT estado, COUNT(*) FROM tareas GROUP BY estado
    """)
    por_estado = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    for estado, count in cursor.fetchall():
        por_estado[estado] = count
    
    cursor.execute("""
        SELECT prioridad, COUNT(*) FROM tareas GROUP BY prioridad
    """)
    por_prioridad = {
        "baja": 0,
        "media": 0,
        "alta": 0
    }
    for prioridad, count in cursor.fetchall():
        por_prioridad[prioridad] = count
    
    conn.close()
    
    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.put("/tareas/completar_todas", status_code=status.HTTP_200_OK)
def completar_todas():
    """Marca todas las tareas como completadas"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total = cursor.fetchone()[0]
    
    if total == 0:
        conn.close()
        return {"mensaje": "No hay tareas"}
    
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    conn.commit()
    conn.close()
    
    return {"mensaje": "Todas las tareas marcadas como completadas"}

@app.get("/tareas", response_model=List[Tarea])
def get_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query(None)
):
    """Obtiene todas las tareas con filtros opcionales"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "SELECT id, descripcion, estado, fecha_creacion, prioridad FROM tareas WHERE 1=1"
    params = []
    
   
    if estado:
        validar_estado(estado)
        query += " AND estado = ?"
        params.append(estado)
    
    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")
    
    if prioridad:
        validar_prioridad(prioridad)
        query += " AND prioridad = ?"
        params.append(prioridad)
    
   
    if orden:
        if orden.lower() == "desc":
            query += " ORDER BY fecha_creacion DESC"
        elif orden.lower() == "asc":
            query += " ORDER BY fecha_creacion ASC"
    
    cursor.execute(query, params)
    resultados = cursor.fetchall()
    conn.close()
    
   
    tareas = []
    for row in resultados:
        tareas.append({
            "id": row[0],
            "descripcion": row[1],
            "estado": row[2],
            "fecha_creacion": row[3],
            "prioridad": row[4]
        })
    
    return tareas

@app.post("/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED)
def create_tarea(tarea: TareaCreate):
    """Crea una nueva tarea"""
 
    if not tarea.descripcion.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "La descripción no puede estar vacía"}
        )
    
   
    validar_estado(tarea.estado)
    validar_prioridad(tarea.prioridad)
    
   
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
        VALUES (?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, fecha_creacion, tarea.prioridad))
    
    tarea_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": fecha_creacion,
        "prioridad": tarea.prioridad
    }

@app.put("/tareas/{id}", response_model=Tarea)
def update_tarea(id: int, tarea_update: TareaUpdate):
    """Actualiza una tarea existente"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
 
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    

    updates = []
    params = []
    
    if tarea_update.descripcion is not None:
        if not tarea_update.descripcion.strip():
            conn.close()
            raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
        updates.append("descripcion = ?")
        params.append(tarea_update.descripcion)
    
    if tarea_update.estado is not None:
        validar_estado(tarea_update.estado)
        updates.append("estado = ?")
        params.append(tarea_update.estado)
    
    if tarea_update.prioridad is not None:
        validar_prioridad(tarea_update.prioridad)
        updates.append("prioridad = ?")
        params.append(tarea_update.prioridad)
    
    if updates:
        params.append(id)
        query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
  
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()
    
    return {
        "id": tarea_actualizada[0],
        "descripcion": tarea_actualizada[1],
        "estado": tarea_actualizada[2],
        "fecha_creacion": tarea_actualizada[3],
        "prioridad": tarea_actualizada[4]
    }

@app.delete("/tareas/{id}")
def delete_tarea(id: int):
    """Elimina una tarea"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
 
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
 
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada"}