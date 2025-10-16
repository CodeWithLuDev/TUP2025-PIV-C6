from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, validator
from typing import Optional, List
import sqlite3
from datetime import datetime

app = FastAPI()

def init_db():
    conn = sqlite3.connect('tareas.db')
    cursor = conn.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            fecha_creacion TEXT
        )
    ''')
    conn.commit()
    conn.close()

init_db()

class TaskBase(BaseModel):
    descripcion: str
    estado: str
    prioridad: str

    @validator('estado')
    def validate_estado(cls, v):
        if v not in ["pendiente", "en_progreso", "completada"]:
            raise ValueError('Estado debe ser "pendiente", "en_progreso" o "completada"')
        return v

    @validator('prioridad')
    def validate_prioridad(cls, v):
        if v not in ["baja", "media", "alta"]:
            raise ValueError('Prioridad debe ser "baja", "media" o "alta"')
        return v

class TaskCreate(TaskBase):
    pass

class TaskUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    prioridad: Optional[str] = None

    @validator('estado', always=True)
    def validate_estado_optional(cls, v):
        if v is not None and v not in ["pendiente", "en_progreso", "completada"]:
            raise ValueError('Estado debe ser "pendiente", "en_progreso" o "completada"')
        return v

    @validator('prioridad', always=True)
    def validate_prioridad_optional(cls, v):
        if v is not None and v not in ["baja", "media", "alta"]:
            raise ValueError('Prioridad debe ser "baja", "media" o "alta"')
        return v

class Task(TaskBase):
    id: int
    fecha_creacion: str

    class Config:
        orm_mode = True

def dict_factory(cursor, row):
    d = {}
    for idx, col in enumerate(cursor.description):
        d[col[0]] = row[idx]
    return d

@app.get("/tareas", response_model=List[Task])
def get_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query("asc", enum=["asc", "desc"])
):
    conn = sqlite3.connect('tareas.db')
    conn.row_factory = dict_factory
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

    order_direction = "ASC" if orden == "asc" else "DESC"
    query += f" ORDER BY fecha_creacion {order_direction}"

    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    return tareas

@app.post("/tareas", response_model=Task)
def create_tarea(task: TaskCreate):
    if not task.descripcion.strip():
        raise HTTPException(status_code=400, detail="La descripción no puede estar vacía")

    fecha_actual = datetime.now().isoformat()

    conn = sqlite3.connect('tareas.db')
    cursor = conn.cursor()
    cursor.execute('''
        INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
        VALUES (?, ?, ?, ?)
    ''', (task.descripcion, task.estado, task.prioridad, fecha_actual))
    conn.commit()
    new_id = cursor.lastrowid
    conn.close()

    return {"id": new_id, "descripcion": task.descripcion, "estado": task.estado, "prioridad": task.prioridad, "fecha_creacion": fecha_actual}

@app.put("/tareas/{id}", response_model=Task)
def update_tarea(id: int, task: TaskUpdate):
    conn = sqlite3.connect('tareas.db')
    conn.row_factory = dict_factory
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    existing_task = cursor.fetchone()
    if not existing_task:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    updates = []
    params = []
    if task.descripcion is not None:
        updates.append("descripcion = ?")
        params.append(task.descripcion)
    if task.estado is not None:
        updates.append("estado = ?")
        params.append(task.estado)
    if task.prioridad is not None:
        updates.append("prioridad = ?")
        params.append(task.prioridad)

    if not updates:
        conn.close()
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")

    query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
    params.append(id)
    cursor.execute(query, params)
    conn.commit()

    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    updated_task = cursor.fetchone()
    conn.close()
    return updated_task

@app.delete("/tareas/{id}")
def delete_tarea(id: int):
    conn = sqlite3.connect('tareas.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")

    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"detail": "Tarea eliminada"}

@app.get("/tareas/resumen")
def get_resumen():
    conn = sqlite3.connect('tareas.db')
    cursor = conn.cursor()

    cursor.execute('''
        SELECT estado, COUNT(*) as count
        FROM tareas
        GROUP BY estado
    ''')
    rows = cursor.fetchall()
    conn.close()

    resumen = {row[0]: row[1] for row in rows}
    for estado in ["pendiente", "en_progreso", "completada"]:
        if estado not in resumen:
            resumen[estado] = 0
    return resumen