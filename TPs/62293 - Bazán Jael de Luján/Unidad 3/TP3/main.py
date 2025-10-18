from fastapi import FastAPI, Path, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import sqlite3
import os

app = FastAPI(title="Mini API de Tareas Persistente - TP3")

DB_NAME = "tareas.db" 
ALLOWED_ESTADOS = {"pendiente", "en_progreso", "completada"}
ALLOWED_PRIORIDADES = {"baja", "media", "alta"}

def init_db():
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

def row_to_dict(row):
    if not row:
        return None
    return {
        "id": row[0],
        "descripcion": row[1],
        "estado": row[2],
        "fecha_creacion": row[3],
        "prioridad": row[4],
    }

init_db()

class TareaCreate(BaseModel):
    descripcion: str
    estado: Optional[str] = Field("pendiente", pattern=r'^(pendiente|en_progreso|completada)$')
    prioridad: Optional[str] = Field("media", pattern=r'^(baja|media|alta)$')

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = Field(None, pattern=r'^(pendiente|en_progreso|completada)$')
    prioridad: Optional[str] = Field(None, pattern=r'^(baja|media|alta)$')
    
class TareaDB(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: str
    prioridad: str

@app.get("/")
def endpoint_raiz():
    return {
        "nombre": "API de Tareas Persistente (SQLite)",
        "version": "1.0",
        "endpoints": {
            "/tareas": "GET, POST",
            "/tareas/{id}": "PUT, DELETE",
            "/tareas/resumen": "GET",
            "/tareas/completar_todas": "PUT"
        }
    }

@app.get("/tareas/resumen")
def resumen_tareas():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("SELECT estado, COUNT(*) FROM tareas GROUP BY estado")
    resumen_estado = {estado: count for estado, count in cursor.fetchall()}
    cursor.execute("SELECT prioridad, COUNT(*) FROM tareas GROUP BY prioridad")
    resumen_prioridad = {prioridad: count for prioridad, count in cursor.fetchall()}
    conn.close()
    por_estado = {e: resumen_estado.get(e, 0) for e in ALLOWED_ESTADOS}
    por_prioridad = {p: resumen_prioridad.get(p, 0) for p in ALLOWED_PRIORIDADES}
    total_tareas = sum(por_estado.values())
    return {
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad,
    }

@app.put("/tareas/completar_todas", status_code=status.HTTP_200_OK)
def completar_todas():
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
    return {"mensaje": "Todas las tareas completadas"}

@app.get("/tareas", response_model=List[TareaDB])
def obtener_tareas(
    estado: Optional[str] = Query(None), 
    texto: Optional[str] = Query(None), 
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query(None, description="Ordenamiento por fecha: 'asc' o 'desc'")
):
    base_query = "SELECT * FROM tareas"
    conditions = []
    params = []
    if estado:
        if estado not in ALLOWED_ESTADOS:
            raise HTTPException(status_code=422, detail="Estado inválido")
        conditions.append("estado = ?")
        params.append(estado)
    if prioridad:
        if prioridad not in ALLOWED_PRIORIDADES:
            raise HTTPException(status_code=422, detail="Prioridad inválida")
        conditions.append("prioridad = ?")
        params.append(prioridad)
    if texto:
        conditions.append("descripcion LIKE ?")
        params.append(f"%{texto.strip()}%")
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
    order_clause = ""
    if orden:
        orden_lower = orden.lower()
        if orden_lower == "desc":
            order_clause = " ORDER BY fecha_creacion DESC"
        elif orden_lower == "asc":
            order_clause = " ORDER BY fecha_creacion ASC"
        else:
            raise HTTPException(status_code=422, detail="Parámetro 'orden' inválido. Use 'asc' o 'desc'.")
    final_query = base_query + order_clause
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(final_query, params)
    tareas = cursor.fetchall()
    conn.close()
    return [row_to_dict(t) for t in tareas]

@app.post("/tareas", status_code=201, response_model=TareaDB)
def crear_tarea(payload: TareaCreate):
    descripcion = payload.descripcion.strip()
    if not descripcion:
        raise HTTPException(status_code=422, detail="La descripción no puede estar vacía")
    estado = payload.estado
    prioridad = payload.prioridad
    fecha_creacion = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
            VALUES (?, ?, ?, ?)
            """,
            (descripcion, estado, fecha_creacion, prioridad)
        )
        tarea_id = cursor.lastrowid
        conn.commit()
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        tarea = cursor.fetchone()
    finally:
        conn.close()
    return row_to_dict(tarea)

@app.put("/tareas/{tarea_id}", response_model=TareaDB)
def actualizar_tarea(tarea_id: int = Path(...), payload: TareaUpdate = None):
    update_data = payload.model_dump(exclude_unset=True) if payload else {}
    if not update_data:
        raise HTTPException(status_code=400, detail="No se recibieron datos para actualizar")
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    sets = []
    values = []
    if "descripcion" in update_data:
        desc = update_data["descripcion"].strip()
        if not desc:
            raise HTTPException(status_code=422, detail="La descripción no puede estar vacía")
        sets.append("descripcion = ?")
        values.append(desc)
    if "estado" in update_data:
        sets.append("estado = ?")
        values.append(update_data["estado"])
    if "prioridad" in update_data:
        sets.append("prioridad = ?")
        values.append(update_data["prioridad"])
    values.append(tarea_id)
    query = f"UPDATE tareas SET {', '.join(sets)} WHERE id = ?"
    cursor.execute(query, values)
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="error: La tarea no existe")
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    updated_tarea = cursor.fetchone()
    conn.close()
    return row_to_dict(updated_tarea)

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int = Path(...)):
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="error: La tarea no existe")
    conn.close()
    return {"mensaje": "Tarea eliminada"}


