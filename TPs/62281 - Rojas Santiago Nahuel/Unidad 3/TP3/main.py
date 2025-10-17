from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
import sqlite3
from datetime import datetime

app = FastAPI(title="api de tareas persistente", version="3.0")

class tareacreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str = Field(..., pattern="^(pendiente|en_progreso|completada)$")
    prioridad: str = Field(default="media", pattern="^(baja|media|alta)$")

class tareaupdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[str] = Field(None, pattern="^(pendiente|en_progreso|completada)$")
    prioridad: Optional[str] = Field(None, pattern="^(baja|media|alta)$")

def init_db():
    conn = sqlite3.connect('tareas.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media'
        )
    ''')
    conn.commit()
    conn.close()

@app.on_event("startup")
def startup_event():
    init_db()

def row_to_dict(row):
    return {
        "id": row[0],
        "descripcion": row[1],
        "estado": row[2],
        "fecha_creacion": row[3],
        "prioridad": row[4]
    }

@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = Query(None, pattern="^(pendiente|en_progreso|completada)$"),
    texto: Optional[str] = None,
    prioridad: Optional[str] = Query(None, pattern="^(baja|media|alta)$"),
    orden: Optional[str] = Query(None, pattern="^(asc|desc)$")
):
    conn = sqlite3.connect('tareas.db')
    cursor = conn.cursor()
    
    query = "SELECT id, descripcion, estado, fecha_creacion, prioridad FROM tareas WHERE 1=1"
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
        if orden == "asc":
            query += " ORDER BY fecha_creacion ASC"
        else:
            query += " ORDER BY fecha_creacion DESC"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    tareas = [row_to_dict(row) for row in rows]
    return tareas

@app.get("/tareas/resumen")
def obtener_resumen():
    conn = sqlite3.connect('tareas.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        GROUP BY estado
    ''')
    
    rows = cursor.fetchall()
    conn.close()
    
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for row in rows:
        resumen[row[0]] = row[1]
    
    return resumen

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: tareacreate):
    conn = sqlite3.connect('tareas.db')
    cursor = conn.cursor()
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute('''
        INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
        VALUES (?, ?, ?, ?)
    ''', (tarea.descripcion, tarea.estado, fecha_creacion, tarea.prioridad))
    
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": fecha_creacion,
        "prioridad": tarea.prioridad
    }

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: tareaupdate):
    conn = sqlite3.connect('tareas.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(status_code=404, detail="tarea no encontrada")
    
    campos_actualizar = []
    valores = []
    
    if tarea.descripcion is not None:
        campos_actualizar.append("descripcion = ?")
        valores.append(tarea.descripcion)
    
    if tarea.estado is not None:
        campos_actualizar.append("estado = ?")
        valores.append(tarea.estado)
    
    if tarea.prioridad is not None:
        campos_actualizar.append("prioridad = ?")
        valores.append(tarea.prioridad)
    
    if not campos_actualizar:
        conn.close()
        raise HTTPException(status_code=400, detail="no se proporcionaron campos para actualizar")
    
    valores.append(id)
    query = f"UPDATE tareas SET {', '.join(campos_actualizar)} WHERE id = ?"
    
    cursor.execute(query, valores)
    conn.commit()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()
    
    return row_to_dict(tarea_actualizada)

@app.delete("/tareas/{id}", status_code=204)
def eliminar_tarea(id: int):
    conn = sqlite3.connect('tareas.db')
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(status_code=404, detail="tarea no encontrada")
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return None

@app.get("/")
def root():
    return {
        "mensaje": "api de tareas persistente - tp3",
        "version": "3.0"
    }