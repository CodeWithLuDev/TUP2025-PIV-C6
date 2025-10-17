from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
import sqlite3
from datetime import datetime
from typing import Optional

app = FastAPI(title="API de Tareas Persistente")

class Tarea(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str = Field(..., pattern="^(pendiente|en_progreso|completada)$")
    prioridad: str = Field(..., pattern="^(baja|media|alta)$")

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = Field(None, pattern="^(pendiente|en_progreso|completada)$")
    prioridad: Optional[str] = Field(None, pattern="^(baja|media|alta)$")

def get_db_connection():
    conn = sqlite3.connect("tareas.db")
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_db_connection()
    conn.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            fecha_creacion TEXT
        )
    """)
    conn.commit()
    conn.close()

init_db()

@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query(None)
):
    conn = get_db_connection()
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
    if orden and orden.lower() in ["asc", "desc"]:
        query += f" ORDER BY fecha_creacion {orden.upper()}"

    tareas = conn.execute(query, params).fetchall()
    conn.close()
    return [dict(t) for t in tareas]


@app.post("/tareas", status_code=201)
def crear_tarea(tarea: Tarea):
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    conn = get_db_connection()
    conn.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion) VALUES (?, ?, ?, ?)",
        (tarea.descripcion, tarea.estado, tarea.prioridad, fecha_actual)
    )
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea creada exitosamente"}


@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    conn = get_db_connection()
    existente = conn.execute("SELECT * FROM tareas WHERE id = ?", (id,)).fetchone()
    if not existente:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    nueva_desc = tarea.descripcion or existente["descripcion"]
    nuevo_estado = tarea.estado or existente["estado"]
    nueva_prioridad = tarea.prioridad or existente["prioridad"]

    conn.execute(
        "UPDATE tareas SET descripcion=?, estado=?, prioridad=? WHERE id=?",
        (nueva_desc, nuevo_estado, nueva_prioridad, id)
    )
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea actualizada exitosamente"}


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = get_db_connection()
    tarea = conn.execute("SELECT * FROM tareas WHERE id = ?", (id,)).fetchone()
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    conn.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea eliminada correctamente"}


@app.get("/tareas/resumen")
def resumen_tareas():
    conn = get_db_connection()
    resumen = conn.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        GROUP BY estado
    """).fetchall()
    conn.close()
    return {fila["estado"]: fila["cantidad"] for fila in resumen}
