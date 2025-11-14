from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional, List
from datetime import datetime
import sqlite3



#BASE DE DATOS
DB_NAME = "tareas.db"

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def row_to_dict(row):
    return dict(row)

class EstadoEnum(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

class PrioridadEnum(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"

#MODELOS

class TareaBase(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: EstadoEnum = EstadoEnum.pendiente
    prioridad: PrioridadEnum = PrioridadEnum.media

class TareaCreate(TareaBase):
    pass

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[EstadoEnum] = None
    prioridad: Optional[PrioridadEnum] = None

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: EstadoEnum
    prioridad: PrioridadEnum
    fecha_creacion: str

#FASTAPI APP
app = FastAPI(title="TP3 - API de Tareas")

@app.on_event("startup")
def startup_event():
    init_db()

#ENDPOINTS

#GET /tareas 
@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(
    estado: Optional[EstadoEnum] = None,
    texto: Optional[str] = None,
    prioridad: Optional[PrioridadEnum] = None,
    orden: Optional[str] = Query(None, pattern="^(asc|desc)$")
):
    conn = get_connection()
    cur = conn.cursor()

    query = "SELECT * FROM tareas WHERE 1=1"
    params = []

    if estado:
        query += " AND estado = ?"
        params.append(estado.value)

    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")

    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad.value)

    if orden:
        query += f" ORDER BY fecha_creacion {orden.upper()}"
    else:
        query += " ORDER BY id ASC"

    cur.execute(query, params)
    filas = cur.fetchall()
    conn.close()

    return [row_to_dict(f) for f in filas]

#POST /tareas 
@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(data: TareaCreate):
    if not data.descripcion.strip():
        raise HTTPException(422, "La descripción no puede estar vacía")

    conn = get_connection()
    cur = conn.cursor()

    fecha = datetime.now().isoformat()

    cur.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
        VALUES (?, ?, ?, ?)
    """, (data.descripcion, data.estado.value, data.prioridad.value, fecha))

    conn.commit()

    nueva_id = cur.lastrowid
    cur.execute("SELECT * FROM tareas WHERE id = ?", (nueva_id,))
    fila = cur.fetchone()

    conn.close()
    return row_to_dict(fila)


#PUT /tareas/{id}
@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, data: TareaUpdate):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    existente = cur.fetchone()

    if not existente:
        raise HTTPException(404, "La tarea no existe")

    campos = []
    valores = []

    if data.descripcion is not None:
        if not data.descripcion.strip():
            raise HTTPException(422, "Descripción no válida")
        campos.append("descripcion = ?")
        valores.append(data.descripcion)

    if data.estado is not None:
        campos.append("estado = ?")
        valores.append(data.estado.value)

    if data.prioridad is not None:
        campos.append("prioridad = ?")
        valores.append(data.prioridad.value)

    if campos:
        valores.append(id)
        query = f"UPDATE tareas SET {', '.join(campos)} WHERE id = ?"
        cur.execute(query, valores)
        conn.commit()

    cur.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    actualizada = row_to_dict(cur.fetchone())

    conn.close()
    return actualizada


#DELETE /tareas/{id}
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    existe = cur.fetchone()

    if not existe:
        raise HTTPException(404, "La tarea no existe")

    cur.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return {"mensaje": "Tarea eliminada correctamente"}


#GET /tareas/resumen
@app.get("/tareas/resumen")
def resumen():
    conn = get_connection()
    cur = conn.cursor()

    cur.execute("SELECT COUNT(*) AS total FROM tareas")
    total = cur.fetchone()["total"]

    # por estado
    resumen_estado = {e.value: 0 for e in EstadoEnum}
    cur.execute("SELECT estado, COUNT(*) AS c FROM tareas GROUP BY estado")
    for r in cur.fetchall():
        resumen_estado[r["estado"]] = r["c"]

    # por prioridad
    resumen_prioridad = {p.value: 0 for p in PrioridadEnum}
    cur.execute("SELECT prioridad, COUNT(*) AS c FROM tareas GROUP BY prioridad")
    for r in cur.fetchall():
        resumen_prioridad[r["prioridad"]] = r["c"]

    conn.close()

    return {
        "total_tareas": total,
        "por_estado": resumen_estado,
        "por_prioridad": resumen_prioridad
    }
