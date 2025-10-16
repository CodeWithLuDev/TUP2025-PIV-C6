# main.py
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field
from typing import Optional, List, Dict, Any
import sqlite3
import os
from datetime import datetime, timezone

# Nombre del archivo de la DB — los tests importan DB_NAME
DB_NAME = "tareas.db"

app = FastAPI(title="API de Tareas Persistentes - TP3 (Rearte)")

# -----------------------
# Inicialización / migración
# -----------------------
def init_db() -> None:
    """
    Crea la base de datos y la tabla 'tareas' si no existen.
    """
    create_sql = """
    CREATE TABLE IF NOT EXISTS tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        estado TEXT NOT NULL,
        fecha_creacion TEXT,
        prioridad TEXT
    );
    """
    conn = sqlite3.connect(DB_NAME)
    cur = conn.cursor()
    cur.execute(create_sql)
    conn.commit()
    conn.close()

# Inicializar al importar (los tests llaman init_db() también desde la fixture)
init_db()

# -----------------------
# Utilidades DB
# -----------------------
def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {k: row[k] for k in row.keys()}

# -----------------------
# Constantes de validación
# -----------------------
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}
PRIORIDADES_VALIDAS = {"baja", "media", "alta"}

# -----------------------
# Modelos Pydantic
# -----------------------
class TareaCreate(BaseModel):
    descripcion: str = Field(..., description="Descripción de la tarea")
    estado: Optional[str] = Field(None, description="Estado de la tarea")
    prioridad: Optional[str] = Field(None, description="Prioridad de la tarea")

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    prioridad: Optional[str] = None

# -----------------------
# Endpoints
# -----------------------
@app.get("/", tags=["meta"])
def raiz():
    """Información básica de la API"""
    return {
        "nombre": "API de Tareas Persistentes - TP3 (Rearte Franco)",
        "endpoints": [
            "/tareas [GET, POST]",
            "/tareas/{id} [PUT, DELETE]",
            "/tareas/resumen [GET]",
            "/tareas/completar_todas [PUT]",
        ],
    }

@app.post("/tareas", status_code=201, tags=["tareas"])
def crear_tarea(payload: TareaCreate):
    """
    Crear una nueva tarea.
    - descripcion: requerido (Pydantic valida ausencia -> 422)
    - descripcion no puede ser vacía o solo espacios -> 422
    - estado default: 'pendiente' si no se pasa
    - prioridad: opcional, si se pasa debe ser válida
    """
    # Validar descripcion (no solo espacios)
    descripcion = (payload.descripcion or "")
    if not descripcion.strip():
        raise HTTPException(status_code=422, detail={"error": "descripcion no puede estar vacía o solo espacios"})

    # Estado (default a 'pendiente' si no viene)
    estado = payload.estado if payload.estado is not None else "pendiente"
    if estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=422, detail={"error": f"estado inválido. Debe ser uno de: {', '.join(sorted(ESTADOS_VALIDOS))}"})

    # Prioridad (si viene, validar)
    prioridad = payload.prioridad
    if prioridad is not None and prioridad not in PRIORIDADES_VALIDAS:
        raise HTTPException(status_code=422, detail={"error": f"prioridad inválida. Debe ser uno de: {', '.join(sorted(PRIORIDADES_VALIDAS))}"})

    fecha = datetime.now(timezone.utc).isoformat()
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad) VALUES (?, ?, ?, ?)",
        (descripcion.strip(), estado, fecha, prioridad)
    )
    conn.commit()
    tarea_id = cur.lastrowid
    cur.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    row = cur.fetchone()
    conn.close()
    return JSONResponse(status_code=201, content=row_to_dict(row))

@app.get("/tareas", tags=["tareas"])
def obtener_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query(None),  # "asc" o "desc"
):
    """
    Obtener tareas con filtros combinados y orden por fecha_creacion.
    Los filtros se aplican solo si son provistos.
    """
    sql = "SELECT * FROM tareas"
    condiciones: List[str] = []
    params: List[Any] = []

    if estado:
        condiciones.append("estado = ?")
        params.append(estado)
    if prioridad:
        condiciones.append("prioridad = ?")
        params.append(prioridad)
    if texto:
        condiciones.append("LOWER(descripcion) LIKE ?")
        params.append(f"%{texto.lower()}%")

    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)

    # Orden por fecha_creacion si se pide, defecto ASC si orden es None
    if orden and orden.lower() == "desc":
        sql += " ORDER BY fecha_creacion DESC"
    else:
        sql += " ORDER BY fecha_creacion ASC"

    conn = get_connection()
    cur = conn.cursor()
    cur.execute(sql, tuple(params))
    rows = cur.fetchall()
    conn.close()
    tareas = [row_to_dict(r) for r in rows]
    return tareas

@app.put("/tareas/{tarea_id}", tags=["tareas"])
def actualizar_tarea(tarea_id: int, payload: TareaUpdate):
    """
    Actualiza una tarea existente.
    - Si no existe: 404 con detail={"error": "..."}
    - Valida campos enviados (descripcion no vacía, estado/prioridad válidos)
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})

    updates: List[str] = []
    params: List[Any] = []

    if payload.descripcion is not None:
        if not payload.descripcion.strip():
            conn.close()
            raise HTTPException(status_code=422, detail={"error": "descripcion no puede estar vacía o solo espacios"})
        updates.append("descripcion = ?")
        params.append(payload.descripcion.strip())

    if payload.estado is not None:
        if payload.estado not in ESTADOS_VALIDOS:
            conn.close()
            raise HTTPException(status_code=422, detail={"error": f"estado inválido. Debe ser uno de: {', '.join(sorted(ESTADOS_VALIDOS))}"})
        updates.append("estado = ?")
        params.append(payload.estado)

    if payload.prioridad is not None:
        if payload.prioridad not in PRIORIDADES_VALIDAS:
            conn.close()
            raise HTTPException(status_code=422, detail={"error": f"prioridad inválida. Debe ser uno de: {', '.join(sorted(PRIORIDADES_VALIDAS))}"})
        updates.append("prioridad = ?")
        params.append(payload.prioridad)

    if updates:
        sql = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        params.append(tarea_id)
        cur.execute(sql, tuple(params))
        conn.commit()

    cur.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    updated = cur.fetchone()
    conn.close()
    return row_to_dict(updated)

@app.delete("/tareas/{tarea_id}", tags=["tareas"])
def eliminar_tarea(tarea_id: int):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    row = cur.fetchone()
    if row is None:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    cur.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea eliminada"}

@app.get("/tareas/resumen", tags=["tareas"])
def resumen_tareas():
    """
    Devuelve resumen con total_tareas, por_estado y por_prioridad.
    Las claves son los valores existentes en la DB (no se fuerzan all keys).
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT COUNT(*) as total FROM tareas")
    total_row = cur.fetchone()
    total = total_row["total"] if total_row is not None else 0

    cur.execute("SELECT estado, COUNT(*) as cnt FROM tareas GROUP BY estado")
    por_estado_rows = cur.fetchall()
    por_estado = {r["estado"]: r["cnt"] for r in por_estado_rows}

    cur.execute("SELECT prioridad, COUNT(*) as cnt FROM tareas GROUP BY prioridad")
    por_pri_rows = cur.fetchall()
    por_prioridad: Dict[str, int] = {}
    for r in por_pri_rows:
        key = r["prioridad"] if r["prioridad"] is not None else "sin_prioridad"
        por_prioridad[key] = r["cnt"]

    conn.close()
    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad,
    }

@app.put("/tareas/completar_todas", tags=["tareas"])
def completar_todas():
    """
    Marca todas las tareas como 'completada'. No espera body.
    Devuelve mensaje y no provoca validación 422.
    """
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("UPDATE tareas SET estado = 'completada' WHERE estado != 'completada'")
    conn.commit()
    conn.close()
    return {"mensaje": "Todas las tareas marcadas como completadas"}
