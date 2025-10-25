from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum
import sqlite3
from contextlib import contextmanager

app = FastAPI(title="API Para gestionar proyectos y tareas")

DB_NAME = "tareas.db"

class Estado(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

class Prioridad(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"


class Proyecto(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str
    total_tareas: Optional[int] = 0

class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None


class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: Estado
    fecha_creacion: str
    prioridad: Prioridad
    proyecto_id: int

class TareaCreate(BaseModel):
    descripcion: str
    estado: Optional[Estado] = Estado.pendiente
    prioridad: Optional[Prioridad] = Prioridad.media

class TareaUpdate(BaseModel): 
    descripcion: Optional[str] = None
    estado: Optional[Estado] = None
    prioridad: Optional[Prioridad] = None
    proyecto_id: Optional[int] = None


@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")  
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
            CREATE TABLE IF NOT EXISTS proyectos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT,
                fecha_creacion TEXT NOT NULL
            )
        """)
        

        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                fecha_creacion TEXT NOT NULL,
                prioridad TEXT NOT NULL DEFAULT 'media',
                proyecto_id INTEGER NOT NULL,
                FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
            )
        """)
        conn.commit()

@app.on_event("startup")
def startup_event():
    init_db()

@app.get("/")
def root():
    return {
        "nombre": "API de Proyectos y Tareas",
        "version": "2.0",
        "descripcion": "API REST para gestionar proyectos y tareas con relaciones",
        "endpoints": [
            "GET /proyectos - Listar proyectos",
            "POST /proyectos - Crear proyecto",
            "GET /proyectos/{id} - Obtener proyecto",
            "PUT /proyectos/{id} - Actualizar proyecto",
            "DELETE /proyectos/{id} - Eliminar proyecto",
            "GET /proyectos/{id}/tareas - Listar tareas del proyecto",
            "POST /proyectos/{id}/tareas - Crear tarea en proyecto",
            "GET /proyectos/{id}/resumen - Resumen del proyecto",
            "GET /tareas - Listar todas las tareas",
            "PUT /tareas/{id} - Actualizar tarea",
            "DELETE /tareas/{id} - Eliminar tarea",
            "GET /resumen - Resumen general"
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

def proyecto_existe(proyecto_id: int, conn):
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
    return cursor.fetchone() is not None



@app.get("/proyectos", response_model=List[Proyecto])
def get_proyectos(nombre: Optional[str] = Query(None)):
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = """
            SELECT p.*, COUNT(t.id) as total_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            WHERE 1=1
        """
        params = []
        
        if nombre:
            query += " AND p.nombre LIKE ?"
            params.append(f"%{nombre}%")
        
        query += " GROUP BY p.id"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        proyectos = []
        for row in rows:
            proyectos.append(Proyecto(
                id=row["id"],
                nombre=row["nombre"],
                descripcion=row["descripcion"],
                fecha_creacion=row["fecha_creacion"],
                total_tareas=row["total_tareas"]
            ))
        
        return proyectos

@app.get("/proyectos/{id}", response_model=Proyecto)
def get_proyecto(id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            SELECT p.*, COUNT(t.id) as total_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            WHERE p.id = ?
            GROUP BY p.id
        """, (id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=404,
                detail={"error": "El proyecto no existe"}
            )
        
        return Proyecto(
            id=row["id"],
            nombre=row["nombre"],
            descripcion=row["descripcion"],
            fecha_creacion=row["fecha_creacion"],
            total_tareas=row["total_tareas"]
        )

@app.post("/proyectos", response_model=Proyecto, status_code=status.HTTP_201_CREATED)
def create_proyecto(proyecto: ProyectoCreate):
    if not proyecto.nombre or not proyecto.nombre.strip():
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
            detail={"error": "El nombre del proyecto no puede estar vacío"}
        )
    
    fecha_creacion = datetime.now().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        

        cursor.execute("SELECT id FROM proyectos WHERE nombre = ?", (proyecto.nombre,))
        if cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": "Ya existe un proyecto con ese nombre"}
            )
        
        cursor.execute("""
            INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
            VALUES (?, ?, ?)
        """, (proyecto.nombre, proyecto.descripcion, fecha_creacion))
        conn.commit()
        
        proyecto_id = cursor.lastrowid
        
        return Proyecto(
            id=proyecto_id,
            nombre=proyecto.nombre,
            descripcion=proyecto.descripcion,
            fecha_creacion=fecha_creacion,
            total_tareas=0
        )

@app.put("/proyectos/{id}", response_model=Proyecto)
def update_proyecto(id: int, proyecto_update: ProyectoUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
        proyecto_row = cursor.fetchone()
        
        if not proyecto_row:
            raise HTTPException(
                status_code=404,
                detail={"error": "El proyecto no existe"}
            )
        
        if proyecto_update.nombre is not None:
            if not proyecto_update.nombre.strip():
                raise HTTPException(
                    status_code=400,
                    detail={"error": "El nombre del proyecto no puede estar vacío"}
                )
            

            cursor.execute("SELECT id FROM proyectos WHERE nombre = ? AND id != ?", 
                        (proyecto_update.nombre, id))
            if cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error": "Ya existe un proyecto con ese nombre"}
                )
        
        updates = []
        params = []
        
        if proyecto_update.nombre is not None:
            updates.append("nombre = ?")
            params.append(proyecto_update.nombre)
        
        if proyecto_update.descripcion is not None:
            updates.append("descripcion = ?")
            params.append(proyecto_update.descripcion)
        
        if updates:
            query = f"UPDATE proyectos SET {', '.join(updates)} WHERE id = ?"
            params.append(id)
            cursor.execute(query, params)
            conn.commit()
        
        cursor.execute("""
            SELECT p.*, COUNT(t.id) as total_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            WHERE p.id = ?
            GROUP BY p.id
        """, (id,))
        proyecto_actualizado = cursor.fetchone()
        
        return Proyecto(
            id=proyecto_actualizado["id"],
            nombre=proyecto_actualizado["nombre"],
            descripcion=proyecto_actualizado["descripcion"],
            fecha_creacion=proyecto_actualizado["fecha_creacion"],
            total_tareas=proyecto_actualizado["total_tareas"]
        )

@app.delete("/proyectos/{id}")
def delete_proyecto(id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
        proyecto = cursor.fetchone()
        
        if not proyecto:
            raise HTTPException(
                status_code=404,
                detail={"error": "El proyecto no existe"}
            )
        

        cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (id,))
        tareas_eliminadas = cursor.fetchone()["total"]
        
        cursor.execute("DELETE FROM proyectos WHERE id = ?", (id,))
        conn.commit()
        
        return {
            "mensaje": "Proyecto y sus tareas eliminados correctamente",
            "tareas_eliminadas": tareas_eliminadas
        }



@app.get("/proyectos/{id}/tareas", response_model=List[Tarea])
def get_tareas_proyecto(
    id: int,
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query(None)
):
    with get_db() as conn:
        cursor = conn.cursor()
        

        if not proyecto_existe(id, conn):
            raise HTTPException(
                status_code=404,
                detail={"error": "El proyecto no existe"}
            )
        
        query = "SELECT * FROM tareas WHERE proyecto_id = ?"
        params = [id]
        
        if estado:
            validar_estado(estado)
            query += " AND estado = ?"
            params.append(estado)
        
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
                prioridad=row["prioridad"],
                proyecto_id=row["proyecto_id"]
            ))
        
        return tareas

@app.post("/proyectos/{id}/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED)
def create_tarea_proyecto(id: int, tarea: TareaCreate):
    with get_db() as conn:

        if not proyecto_existe(id, conn):
            raise HTTPException(
                status_code=400,
                detail={"error": "El proyecto no existe"}
            )
        
        if not tarea.descripcion.strip():
            raise HTTPException(
                status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
                detail={"error": "La descripción no puede estar vacía"}
            )
        
        validar_estado(tarea.estado)
        validar_prioridad(tarea.prioridad)
        
        fecha_creacion = datetime.now().isoformat()
        
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad, proyecto_id)
            VALUES (?, ?, ?, ?, ?)
        """, (tarea.descripcion, tarea.estado, fecha_creacion, tarea.prioridad, id))
        conn.commit()
        
        tarea_id = cursor.lastrowid
        
        return Tarea(
            id=tarea_id,
            descripcion=tarea.descripcion,
            estado=tarea.estado,
            fecha_creacion=fecha_creacion,
            prioridad=tarea.prioridad,
            proyecto_id=id
        )

@app.get("/tareas", response_model=List[Tarea])
def get_tareas(
    estado: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    proyecto_id: Optional[int] = Query(None),
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
        
        if proyecto_id:
            query += " AND proyecto_id = ?"
            params.append(proyecto_id)
        
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
                prioridad=row["prioridad"],
                proyecto_id=row["proyecto_id"]
            ))
        
        return tareas

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
        
        if tarea_update.proyecto_id is not None:
            if not proyecto_existe(tarea_update.proyecto_id, conn):
                raise HTTPException(
                    status_code=400,
                    detail={"error": "El proyecto especificado no existe"}
                )
        
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
        
        if tarea_update.proyecto_id is not None:
            updates.append("proyecto_id = ?")
            params.append(tarea_update.proyecto_id)
        
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
            prioridad=tarea_actualizada["prioridad"],
            proyecto_id=tarea_actualizada["proyecto_id"]
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
        
        return {"mensaje": "Tarea eliminada correctamente"}



@app.get("/proyectos/{id}/resumen")
def get_resumen_proyecto(id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        

        cursor.execute("SELECT nombre FROM proyectos WHERE id = ?", (id,))
        proyecto = cursor.fetchone()
        
        if not proyecto:
            raise HTTPException(
                status_code=404,
                detail={"error": "El proyecto no existe"}
            )
        

        cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (id,))
        total = cursor.fetchone()["total"]
        

        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM tareas
            WHERE proyecto_id = ?
            GROUP BY estado
        """, (id,))
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
            WHERE proyecto_id = ?
            GROUP BY prioridad
        """, (id,))
        resultados_prioridad = cursor.fetchall()
        
        conteo_prioridad = {
            "baja": 0,
            "media": 0,
            "alta": 0
        }
        
        for row in resultados_prioridad:
            conteo_prioridad[row["prioridad"]] = row["cantidad"]
        
        return {
            "proyecto_id": id,
            "proyecto_nombre": proyecto["nombre"],
            "total_tareas": total,
            "por_estado": conteo_estado,
            "por_prioridad": conteo_prioridad
        }

@app.get("/resumen")
def get_resumen_general():
    with get_db() as conn:
        cursor = conn.cursor()
        

        cursor.execute("SELECT COUNT(*) as total FROM proyectos")
        total_proyectos = cursor.fetchone()["total"]
        

        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total_tareas = cursor.fetchone()["total"]
        

        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM tareas
            GROUP BY estado
        """)
        resultados_estado = cursor.fetchall()
        
        tareas_por_estado = {
            "pendiente": 0,
            "en_progreso": 0,
            "completada": 0
        }
        
        for row in resultados_estado:
            tareas_por_estado[row["estado"]] = row["cantidad"]
        

        cursor.execute("""
            SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            GROUP BY p.id
            ORDER BY cantidad_tareas DESC
            LIMIT 1
        """)
        proyecto_top = cursor.fetchone()
        
        proyecto_con_mas_tareas = None
        if proyecto_top:
            proyecto_con_mas_tareas = {
                "id": proyecto_top["id"],
                "nombre": proyecto_top["nombre"],
                "cantidad_tareas": proyecto_top["cantidad_tareas"]
            }
        
        return {
            "total_proyectos": total_proyectos,
            "total_tareas": total_tareas,
            "tareas_por_estado": tareas_por_estado,
            "proyecto_con_mas_tareas": proyecto_con_mas_tareas
        }