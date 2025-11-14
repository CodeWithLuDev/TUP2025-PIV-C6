import sqlite3
import os
from datetime import datetime
from fastapi import FastAPI, HTTPException, status, Query
from pydantic import BaseModel, constr, Field
from enum import Enum
from typing import List, Optional

# --- Configuración de la Base de Datos ---

DB_NAME = "tareas.db"

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("""
    CREATE TABLE IF NOT EXISTS tareas (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        descripcion TEXT NOT NULL,
        estado TEXT NOT NULL,
        fecha_creacion TEXT NOT NULL,
        prioridad TEXT NOT NULL
    );
    """)
    
    conn.commit()
    conn.close()

# --- Modelos Pydantic (Validación de datos) ---

class EstadoEnum(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

class PrioridadEnum(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"

class TareaBase(BaseModel):
    descripcion: constr(strip_whitespace=True, min_length=1)
    estado: EstadoEnum = EstadoEnum.pendiente
    prioridad: PrioridadEnum = PrioridadEnum.media

class TareaCreate(TareaBase):
    pass

class TareaUpdate(TareaBase):
    pass

class Tarea(TareaBase):
    id: int
    fecha_creacion: str

    class Config:
        from_attributes = True

# --- Inicialización de FastAPI ---

app = FastAPI(
    title="TP3 - API de Tareas Persistente",
    description="Implementación de un CRUD de tareas con FastAPI y persistencia en SQLite.",
    version="1.0.0"
)

init_db()

# --- Funciones Auxiliares (Helpers) ---

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def get_tarea_by_id(tarea_id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea = cursor.fetchone()
    conn.close()
    
    if tarea is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Tarea con id {tarea_id} no encontrada"}
        )
    return dict(tarea)

# --- Endpoints de la API ---

@app.get("/", summary="Endpoint Raíz")
def get_root():
    return {
        "nombre": "API de Tareas - TP3 (FastAPI + SQLite)",
        "documentacion": "/docs",
        "estado_db": f"Base de datos '{DB_NAME}' inicializada."
    }

@app.post("/tareas", 
          response_model=Tarea, 
          status_code=status.HTTP_201_CREATED, 
          summary="Crear una nueva tarea")
def create_tarea(tarea: TareaCreate):
    fecha_actual = datetime.now().isoformat()
    conn = get_db_connection()
    cursor = conn.cursor()
    
    try:
        cursor.execute(
            """
            INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
            VALUES (?, ?, ?, ?)
            """,
            (tarea.descripcion, tarea.estado.value, tarea.prioridad.value, fecha_actual)
        )
        new_id = cursor.lastrowid
        conn.commit()
    except sqlite3.Error as e:
        conn.rollback()
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    finally:
        conn.close()
    
    return get_tarea_by_id(new_id)

@app.get("/tareas", 
         response_model=List[Tarea], 
         summary="Obtener todas las tareas (con filtros)")
def get_tareas(
    estado: Optional[EstadoEnum] = Query(None, description="Filtrar por estado"),
    texto: Optional[str] = Query(None, description="Filtrar por texto en la descripción", min_length=1),
    prioridad: Optional[PrioridadEnum] = Query(None, description="Filtrar por prioridad"),
    orden: Optional[str] = Query(None, description="Ordenar por fecha: 'asc' o 'desc'", pattern="^(asc|desc)$")
):
    query = "SELECT * FROM tareas"
    conditions = []
    params = []

    if estado:
        conditions.append("estado = ?")
        params.append(estado.value)
    if prioridad:
        conditions.append("prioridad = ?")
        params.append(prioridad.value)
    if texto:
        conditions.append("descripcion LIKE ?")
        params.append(f"%{texto}%")

    if conditions:
        query += " WHERE " + " AND ".join(conditions)

    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    elif orden == "asc":
        query += " ORDER BY fecha_creacion ASC"

    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(query, tuple(params))
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

@app.get("/tareas/resumen", summary="Resumen de tareas")
def get_resumen():
    conn = get_db_connection()
    cursor = conn.cursor()

    resumen = {
        "total_tareas": 0,
        "por_estado": {e.value: 0 for e in EstadoEnum},
        "por_prioridad": {p.value: 0 for p in PrioridadEnum}
    }

    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total_row = cursor.fetchone()
    if total_row:
        resumen["total_tareas"] = total_row["total"]

    cursor.execute("SELECT estado, COUNT(*) as count FROM tareas GROUP BY estado")
    for row in cursor.fetchall():
        if row["estado"] in resumen["por_estado"]:
            resumen["por_estado"][row["estado"]] = row["count"]

    cursor.execute("SELECT prioridad, COUNT(*) as count FROM tareas GROUP BY prioridad")
    for row in cursor.fetchall():
        if row["prioridad"] in resumen["por_prioridad"]:
            resumen["por_prioridad"][row["prioridad"]] = row["count"]

    conn.close()
    return resumen

@app.put("/tareas/completar_todas", summary="Marcar todas como completadas")
def complete_all_tareas():
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE tareas SET estado = ?", (EstadoEnum.completada.value,))
    count = cursor.rowcount
    conn.commit()
    conn.close()
    return {"mensaje": f"{count} tareas actualizadas a 'completada'"}

@app.put("/tareas/{tarea_id}", 
         response_model=Tarea, 
         summary="Actualizar una tarea")
def update_tarea(tarea_id: int, tarea: TareaUpdate):
    get_tarea_by_id(tarea_id) 
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        UPDATE tareas SET descripcion = ?, estado = ?, prioridad = ?
        WHERE id = ?
        """,
        (tarea.descripcion, tarea.estado.value, tarea.prioridad.value, tarea_id)
    )
    conn.commit()
    conn.close()
    
    return get_tarea_by_id(tarea_id)

@app.delete("/tareas/{tarea_id}", 
            summary="Eliminar una tarea")
def delete_tarea(tarea_id: int):
    get_tarea_by_id(tarea_id)
    
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada exitosamente"}

if __name__ == "__main__":
    import uvicorn
    print(f"Iniciando servidor en http://127.0.0.1:8000")
    print("Base de datos utilizada:", DB_NAME)
    uvicorn.run("main:app", host="127.0.0.1", port=8000, reload=True)