from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel
from typing import Optional, Literal, List, Dict, Any
from datetime import datetime
import sqlite3
from contextlib import contextmanager
import os

# -------------------------------------------------------------------
# CONFIG
# -------------------------------------------------------------------
DB_FILE = "tareas.db"
VALID_STATES = ["pendiente", "en_progreso", "completada"]
VALID_PRIORITIES = ["baja", "media", "alta"]

# -------------------------------------------------------------------
# APP
# -------------------------------------------------------------------
app = FastAPI(title="TP3 - API Tareas con SQLite")

# -------------------------------------------------------------------
# MODELOS
# -------------------------------------------------------------------
class TareaCreate(BaseModel):
    descripcion: str
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = "pendiente"
    prioridad: Optional[Literal["baja", "media", "alta"]] = "media"

class TareaOut(BaseModel):
    id: int
    descripcion: str
    estado: str
    prioridad: str
    fecha_creacion: str

# -------------------------------------------------------------------
# DB CONNECTION
# -------------------------------------------------------------------
@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

# -------------------------------------------------------------------
# INIT DB
# -------------------------------------------------------------------
def init_db():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                prioridad TEXT NOT NULL,
                fecha_creacion TEXT NOT NULL
            )
        """)

init_db()

# -------------------------------------------------------------------
# FUNCIONES AUXILIARES
# -------------------------------------------------------------------
def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "descripcion": row["descripcion"],
        "estado": row["estado"],
        "prioridad": row["prioridad"],
        "fecha_creacion": row["fecha_creacion"]
    }

# -------------------------------------------------------------------
# ENDPOINTS
# -------------------------------------------------------------------

@app.get("/", summary="Raíz")
def root():
    return {"mensaje": "API de Tareas con SQLite (TP3)"}


# ---------------------------------------------------------------
# POST /tareas -> crear una tarea nueva
# ---------------------------------------------------------------
@app.post("/tareas", response_model=TareaOut, status_code=status.HTTP_201_CREATED)
def crear_tarea(tarea: TareaCreate):
    descripcion = tarea.descripcion.strip()

    if not descripcion:
        raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
    if tarea.estado not in VALID_STATES:
        raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
    if tarea.prioridad not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail={"error": "Prioridad inválida"})

    fecha = datetime.now().isoformat(timespec="seconds")

    with get_db_connection() as conn:
        cur = conn.execute("""
            INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
            VALUES (?, ?, ?, ?)
        """, (descripcion, tarea.estado, tarea.prioridad, fecha))
        new_id = cur.lastrowid
        cur = conn.execute("SELECT * FROM tareas WHERE id = ?", (new_id,))
        nueva = cur.fetchone()
        return row_to_dict(nueva)


# ---------------------------------------------------------------
# GET /tareas -> listar con filtros, validaciones y ordenamiento
# ---------------------------------------------------------------
@app.get("/tareas", response_model=List[TareaOut])
def listar_tareas(
    estado: Optional[str] = Query(default=None),
    descripcion: Optional[str] = Query(default=None, description="Busca en la descripción"),
    prioridad: Optional[str] = Query(default=None),
    orden: Optional[str] = Query(default="asc", regex="^(asc|desc)$")
):
    # Validaciones de valores permitidos
    if estado and estado not in VALID_STATES:
        raise HTTPException(status_code=400, detail={"error": f"Estado '{estado}' no permitido"})
    if prioridad and prioridad not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail={"error": f"Prioridad '{prioridad}' no permitida"})

    sql = "SELECT * FROM tareas"
    params: List[Any] = []
    where_clauses: List[str] = []

    if estado:
        where_clauses.append("estado = ?")
        params.append(estado)
    if descripcion:
        where_clauses.append("LOWER(descripcion) LIKE ?")
        params.append(f"%{descripcion.lower()}%")
    if prioridad:
        where_clauses.append("prioridad = ?")
        params.append(prioridad)

    if where_clauses:
        sql += " WHERE " + " AND ".join(where_clauses)

    sql += " ORDER BY fecha_creacion " + ("ASC" if orden == "asc" else "DESC")

    with get_db_connection() as conn:
        cur = conn.execute(sql, params)
        rows = cur.fetchall()

    # Validaciones según filtros
    if estado and not rows:
        raise HTTPException(status_code=404, detail={"error": f"No hay tareas registradas con el estado '{estado}'."})
    if descripcion and not rows:
        raise HTTPException(status_code=404, detail={"error": f"No hay tareas cuya descripción contenga '{descripcion}'."})
    if prioridad and not rows:
        raise HTTPException(status_code=404, detail={"error": f"No hay tareas con prioridad '{prioridad}'."})
    if not estado and not descripcion and not prioridad and not rows:
        raise HTTPException(status_code=404, detail={"error": "No hay tareas registradas en el sistema."})

    return [row_to_dict(r) for r in rows]


# ---------------------------------------------------------------
# GET /tareas/resumen -> cantidad de tareas por estado
# ---------------------------------------------------------------
@app.get("/tareas/resumen")
def resumen_tareas():
    with get_db_connection() as conn:
        cur = conn.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM tareas
            GROUP BY estado
        """)
        data = cur.fetchall()

        if not data:
            raise HTTPException(status_code=404, detail={"error": "No hay tareas registradas para generar el resumen."})

        resumen = {row["estado"]: row["cantidad"] for row in data}
        return {"resumen": resumen}


# ---------------------------------------------------------------
# PUT /tareas/{id} -> modificar tarea
# ---------------------------------------------------------------
@app.put("/tareas/{tarea_id}", response_model=TareaOut)
def modificar_tarea(tarea_id: int, t: TareaCreate):
    descripcion = (t.descripcion or "").strip()
    if not descripcion:
        raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
    if t.estado not in VALID_STATES:
        raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
    if t.prioridad not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail={"error": "Prioridad inválida"})

    with get_db_connection() as conn:
        cur = conn.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail={"error": f"Tarea con ID {tarea_id} no encontrada."})

        conn.execute("""
            UPDATE tareas
            SET descripcion = ?, estado = ?, prioridad = ?
            WHERE id = ?
        """, (descripcion, t.estado, t.prioridad, tarea_id))

        cur = conn.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        actualizada = cur.fetchone()
        return row_to_dict(actualizada)


# ---------------------------------------------------------------
# DELETE /tareas/{id} -> eliminar tarea
# ---------------------------------------------------------------
@app.delete("/tareas/{tarea_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tarea(tarea_id: int):
    with get_db_connection() as conn:
        cur = conn.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail={"error": f"Tarea con ID {tarea_id} no encontrada."})
        conn.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
        conn.commit()
    return
