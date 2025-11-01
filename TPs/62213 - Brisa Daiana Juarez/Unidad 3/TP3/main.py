from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from pydantic import BaseModel, constr, field_validator
from datetime import datetime
from typing import List, Optional, Dict, Union, Any
import sqlite3
import os

app = FastAPI()

# Configuración de la base de datos
DB_NAME = "tareas.db"

def init_db():
    """Inicializar la base de datos y crear la tabla si no existe"""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media'
        )
    """)
    
    conn.commit()
    conn.close()

# Inicializar la base de datos al iniciar la aplicación
init_db()

class TareaBase(BaseModel):
    descripcion: str
    estado: str = "pendiente"
    prioridad: str = "media"

    @field_validator("estado")
    def validar_estado(cls, v):
        if v not in ["pendiente", "en_progreso", "completada"]:
            raise ValueError("Estado no válido")
        return v

    @field_validator("prioridad")
    def validar_prioridad(cls, v):
        if v not in ["baja", "media", "alta"]:
            raise ValueError("Prioridad no válida")
        return v

    @field_validator("descripcion")
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v.strip()

class Tarea(TareaBase):
    id: int
    fecha_creacion: str

@app.put("/tareas/completar_todas")
async def completar_todas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total = cursor.fetchone()[0]
    
    if total == 0:
        conn.close()
        return {"mensaje": "No hay tareas para completar"}
    
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    conn.commit()
    conn.close()
    
    return {"mensaje": f"Se han completado {total} tareas"}

@app.get("/tareas")
async def obtener_tareas(
    estado: Optional[str] = None,
    texto: Optional[str] = None,
    prioridad: Optional[str] = None,
    orden: Optional[str] = None
):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if orden:
        if orden.lower() == "asc":
            query += " ORDER BY fecha_creacion ASC"
        elif orden.lower() == "desc":
            query += " ORDER BY fecha_creacion DESC"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [
        {
            "id": t[0],
            "descripcion": t[1],
            "estado": t[2],
            "fecha_creacion": t[3],
            "prioridad": t[4]
        }
        for t in tareas
    ]

@app.post("/tareas", status_code=201)
async def crear_tarea(tarea: TareaBase):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute(
        """
        INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
        VALUES (?, ?, ?, ?)
        """,
        (
            tarea.descripcion,
            tarea.estado,
            datetime.now().isoformat(),
            tarea.prioridad
        )
    )
    
    tarea_id = cursor.lastrowid
    conn.commit()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    nueva_tarea = cursor.fetchone()
    conn.close()
    
    return {
        "id": nueva_tarea[0],
        "descripcion": nueva_tarea[1],
        "estado": nueva_tarea[2],
        "fecha_creacion": nueva_tarea[3],
        "prioridad": nueva_tarea[4]
    }

@app.put("/tareas/{id}")
async def actualizar_tarea(id: int, tarea_update: Dict[str, Any]):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Verificar si la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail="error: La tarea no existe")
    
    # Construir la consulta de actualización
    updates = []
    params = []
    
    if "descripcion" in tarea_update:
        descripcion = str(tarea_update["descripcion"]).strip()
        if not descripcion:
            conn.close()
            raise HTTPException(status_code=422, detail="error: La descripción no puede estar vacía")
        updates.append("descripcion = ?")
        params.append(descripcion)
    
    if "estado" in tarea_update:
        estado = str(tarea_update["estado"])
        if estado not in ["pendiente", "en_progreso", "completada"]:
            conn.close()
            raise HTTPException(status_code=422, detail="error: Estado no válido")
        updates.append("estado = ?")
        params.append(estado)
    
    if "prioridad" in tarea_update:
        prioridad = str(tarea_update["prioridad"])
        if prioridad not in ["baja", "media", "alta"]:
            conn.close()
            raise HTTPException(status_code=422, detail="error: Prioridad no válida")
        updates.append("prioridad = ?")
        params.append(prioridad)
    
    if updates:
        query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        params.append(id)
        cursor.execute(query, params)
        conn.commit()
    
    # Obtener la tarea actualizada
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
async def eliminar_tarea(id: int):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="error: La tarea no existe")
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada exitosamente"}

@app.get("/tareas/resumen")
async def obtener_resumen():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Obtener total de tareas
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total_tareas = cursor.fetchone()[0]
    
    # Obtener conteo por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as conteo
        FROM tareas
        GROUP BY estado
    """)
    por_estado = {estado: conteo for estado, conteo in cursor.fetchall()}
    
    # Obtener conteo por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as conteo
        FROM tareas
        GROUP BY prioridad
    """)
    por_prioridad = {prioridad: conteo for prioridad, conteo in cursor.fetchall()}
    
    conn.close()
    
    return {
        "total_tareas": total_tareas,
        "por_estado": {
            "pendiente": por_estado.get("pendiente", 0),
            "en_progreso": por_estado.get("en_progreso", 0),
            "completada": por_estado.get("completada", 0)
        },
        "por_prioridad": {
            "baja": por_prioridad.get("baja", 0),
            "media": por_prioridad.get("media", 0),
            "alta": por_prioridad.get("alta", 0)
        }
    }

@app.get("/")
async def root():
    return {
        "nombre": "Mini API de Tareas con FastAPI y SQLite",
        "endpoints": {
            "GET /tareas": "Listar todas las tareas (filtros: estado, texto, prioridad, orden)",
            "POST /tareas": "Crear nueva tarea",
            "PUT /tareas/{id}": "Actualizar una tarea",
            "DELETE /tareas/{id}": "Eliminar una tarea",
            "GET /tareas/resumen": "Obtener resumen de tareas",
            "PUT /tareas/completar_todas": "Marcar todas las tareas como completadas"
        }
    }
