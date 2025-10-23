from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional
import sqlite3
from datetime import datetime

app = FastAPI()

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: str = Field(..., pattern="^(pendiente|en_progreso|completada)$")
    prioridad: str = Field(default="media", pattern="^(baja|media|alta)$")

class TareaUpdate(BaseModel):
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
def startup():
    init_db()


def get_db():
    conn = sqlite3.connect('tareas.db')
    conn.row_factory = sqlite3.Row
    return conn


@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = Query(None, pattern="^(pendiente|en_progreso|completada)$"),
    texto: Optional[str] = None,
    prioridad: Optional[str] = Query(None, pattern="^(baja|media|alta)$"),
    orden: Optional[str] = Query(None, pattern="^(asc|desc)$")
):
    conn = get_db()
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
        if orden == "asc":
            query += " ORDER BY fecha_creacion ASC"
        else:
            query += " ORDER BY fecha_creacion DESC"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [dict(tarea) for tarea in tareas]


@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
    conn = get_db()
    cursor = conn.cursor()
    
    fecha_creacion = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad) VALUES (?, ?, ?, ?)",
        (tarea.descripcion, tarea.estado, fecha_creacion, tarea.prioridad)
    )
    conn.commit()
    
    tarea_id = cursor.lastrowid
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    nueva_tarea = cursor.fetchone()
    conn.close()
    
    return dict(nueva_tarea)


@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    conn = get_db()
    cursor = conn.cursor()
    
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    updates = []
    params = []
    
    if tarea.descripcion is not None:
        updates.append("descripcion = ?")
        params.append(tarea.descripcion)
    
    if tarea.estado is not None:
        updates.append("estado = ?")
        params.append(tarea.estado)
    
    if tarea.prioridad is not None:
        updates.append("prioridad = ?")
        params.append(tarea.prioridad)
    
    if updates:
        params.append(id)
        query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()
    
    return dict(tarea_actualizada)

@app.delete("/tareas/{id}", status_code=204)
def eliminar_tarea(id: int):
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return None

@app.get("/tareas/resumen")
def obtener_resumen():
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT 
            estado,
            COUNT(*) as cantidad
        FROM tareas
        GROUP BY estado
    ''')
    
    resultados = cursor.fetchall()
    conn.close()
    
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for row in resultados:
        resumen[row["estado"]] = row["cantidad"]
    
    return resumen

@app.get("/")
def saludar():
    return {"mensaje": "Bienvenido al servidor de tareas con persistencia"}