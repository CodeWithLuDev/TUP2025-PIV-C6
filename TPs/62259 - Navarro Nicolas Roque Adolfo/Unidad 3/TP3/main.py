from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
import sqlite3
from contextlib import contextmanager

app = FastAPI(title="API Para gestionar tareas")


DB_NAME = "tareas.db"

class Estado(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

class Prioridad(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: Estado
    fecha_creacion: str
    prioridad: Prioridad

class TareaCreate(BaseModel):
    descripcion: str
    estado: Optional[Estado] = Estado.pendiente
    prioridad: Optional[Prioridad] = Prioridad.media

class TareaUpdate(BaseModel): 
    descripcion: Optional[str] = None
    estado: Optional[Estado] = None
    prioridad: Optional[Prioridad] = None


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception as e:
        conn.rollback()
        raise e
    finally:
        conn.close()


def init_db():
    with get_db() as conn:
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


@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def root():
    return {
        "nombre": "API de Tareas Persistente",
        "version": "1.0",
        "descripcion": "API REST para gestionar tareas con SQLite",
        "endpoints": [
            "GET /tareas - Obtener todas las tareas",
            "POST /tareas - Crear una nueva tarea",
            "PUT /tareas/{id} - Actualizar una tarea",
            "DELETE /tareas/{id} - Eliminar una tarea",
            "GET /tareas/resumen - Obtener resumen de tareas",
            "PUT /tareas/completar_todas - Marcar todas como completadas"
        ]
    }

def validar_estado(estado: str):
    estados_validos = {"pendiente", "en_progreso", "completada"}
    if estado not in estados_validos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail={"error": "Estado inválido. Debe ser 'pendiente', 'en_progreso' o 'completada'"}
        )

def validar_prioridad(prioridad: str):
    prioridades_validas = {"baja", "media", "alta"}
    if prioridad not in prioridades_validas:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail={"error": "Prioridad inválida. Debe ser 'baja', 'media' o 'alta'"}
        )

@app.get("/tareas/resumen")
def get_resumen():
    with get_db() as conn:
        cursor = conn.cursor()
        

        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total = cursor.fetchone()["total"]
        

        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM tareas
            GROUP BY estado
        """)
        resultados_estado = cursor.fetchall()
        
        conteo_estado = {
            "pendiente": 0,
            "en_progreso": 0,
            "completada": 0
        }
        
        for row in resultados_estado:
            conteo_estado[row["estado"]] = row["cantidad"]
        

        cursor.execute("""
            SELECT prioridad, COUNT(*) as cantidad
            FROM tareas
            GROUP BY prioridad
        """)
        resultados_prioridad = cursor.fetchall()
        
        conteo_prioridad = {
            "baja": 0,
            "media": 0,
            "alta": 0
        }
        
        for row in resultados_prioridad:
            conteo_prioridad[row["prioridad"]] = row["cantidad"]
        
        return {
            "total_tareas": total,
            "por_estado": conteo_estado,
            "por_prioridad": conteo_prioridad
        }

@app.put("/tareas/completar_todas", status_code=status.HTTP_200_OK)
def completar_todas():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total = cursor.fetchone()["total"]
        
        if total == 0:
            return {"mensaje": "No hay tareas"}
        
        cursor.execute("UPDATE tareas SET estado = 'completada'")
        conn.commit()
        
        return {"mensaje": "Todas las tareas marcadas como completadas"}

@app.get("/tareas", response_model=List[Tarea])
def get_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query(None)
):
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = "SELECT * FROM tareas WHERE 1=1"
        params = []
        
        if estado:
            validar_estado(estado)
            query += " AND estado = ?"
            params.append(estado)
        
        if texto:
            query += " AND descripcion LIKE ?"
            params.append(f"%{texto}%")
        
        if prioridad:
            validar_prioridad(prioridad)
            query += " AND prioridad = ?"
            params.append(prioridad)
        
        if orden:
            if orden.lower() == "desc":
                query += " ORDER BY fecha_creacion DESC"
            elif orden.lower() == "asc":
                query += " ORDER BY fecha_creacion ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        tareas = []
        for row in rows:
            tareas.append(Tarea(
                id=row["id"],
                descripcion=row["descripcion"],
                estado=row["estado"],
                fecha_creacion=row["fecha_creacion"],
                prioridad=row["prioridad"]
            ))
        
        return tareas

@app.post("/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED)
def create_tarea(tarea: TareaCreate):
    if not tarea.descripcion.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail={"error": "La descripción no puede estar vacía"}
        )
    
    validar_estado(tarea.estado)
    validar_prioridad(tarea.prioridad)
    
    fecha_creacion = datetime.now().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
            VALUES (?, ?, ?, ?)
        """, (tarea.descripcion, tarea.estado, fecha_creacion, tarea.prioridad))
        conn.commit()
        
        tarea_id = cursor.lastrowid
        
        return Tarea(
            id=tarea_id,
            descripcion=tarea.descripcion,
            estado=tarea.estado,
            fecha_creacion=fecha_creacion,
            prioridad=tarea.prioridad
        )

@app.put("/tareas/{id}", response_model=Tarea)
def update_tarea(id: int, tarea_update: TareaUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        

        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea_row = cursor.fetchone()
        
        if not tarea_row:
            raise HTTPException(
                status_code=404, 
                detail={"error": "La tarea no existe"}
            )
        

        if tarea_update.descripcion is not None:
            if not tarea_update.descripcion.strip():
                raise HTTPException(
                    status_code=400, 
                    detail={"error": "La descripción no puede estar vacía"}
                )
        
        if tarea_update.estado is not None:
            validar_estado(tarea_update.estado)
        
        if tarea_update.prioridad is not None:
            validar_prioridad(tarea_update.prioridad)
        

        updates = []
        params = []
        
        if tarea_update.descripcion is not None:
            updates.append("descripcion = ?")
            params.append(tarea_update.descripcion)
        
        if tarea_update.estado is not None:
            updates.append("estado = ?")
            params.append(tarea_update.estado)
        
        if tarea_update.prioridad is not None:
            updates.append("prioridad = ?")
            params.append(tarea_update.prioridad)
        
        if updates:
            query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
            params.append(id)
            cursor.execute(query, params)
            conn.commit()
        

        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea_actualizada = cursor.fetchone()
        
        return Tarea(
            id=tarea_actualizada["id"],
            descripcion=tarea_actualizada["descripcion"],
            estado=tarea_actualizada["estado"],
            fecha_creacion=tarea_actualizada["fecha_creacion"],
            prioridad=tarea_actualizada["prioridad"]
        )

@app.delete("/tareas/{id}")
def delete_tarea(id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        

        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea = cursor.fetchone()
        
        if not tarea:
            raise HTTPException(
                status_code=404, 
                detail={"error": "La tarea no existe"}
            )
        
        cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
        conn.commit()
        
        return {"mensaje": "Tarea eliminad"}