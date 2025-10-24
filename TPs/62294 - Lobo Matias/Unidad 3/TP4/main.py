from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, field_validator
from typing import List, Optional, Literal
from datetime import datetime
import sqlite3

app = FastAPI(title="API de Gestión de Tareas y Proyectos")

DB_NAME = "tareas.db"

class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    def nombre_no_vacio(cls, v):
        if not v or not v.strip():
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    
    @field_validator('nombre')
    def nombre_no_vacio(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('El nombre no puede estar vacío')
        return v.strip() if v else None

class Proyecto(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str
    total_tareas: int = 0

class TareaCreate(BaseModel):
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    @field_validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None
    
    @field_validator('descripcion')
    def descripcion_no_vacia(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('La descripción no puede estar vacía')
        return v.strip() if v else None

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    prioridad: str
    proyecto_id: int
    fecha_creacion: str

def init_db():
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("PRAGMA foreign_keys = ON")
    
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
            prioridad TEXT NOT NULL,
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

init_db()

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def proyecto_existe(proyecto_id: int) -> bool:
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe


@app.get("/")
def root():
    return {
        "nombre": "API de Gestión de Tareas y Proyectos",
        "version": "4.0",
        "descripcion": "API con relaciones entre proyectos y tareas"
    }

@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = Query(None)):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if nombre:
        cursor.execute("""
            SELECT p.id, p.nombre, p.descripcion, p.fecha_creacion,
                   COUNT(t.id) as total_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            WHERE p.nombre LIKE ?
            GROUP BY p.id
        """, (f"%{nombre}%",))
    else:
        cursor.execute("""
            SELECT p.id, p.nombre, p.descripcion, p.fecha_creacion,
                   COUNT(t.id) as total_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            GROUP BY p.id
        """)
    
    proyectos = []
    for row in cursor.fetchall():
        proyectos.append({
            "id": row[0],
            "nombre": row[1],
            "descripcion": row[2],
            "fecha_creacion": row[3],
            "total_tareas": row[4]
        })
    
    conn.close()
    return proyectos

@app.get("/proyectos/{id}")
def obtener_proyecto(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        SELECT p.id, p.nombre, p.descripcion, p.fecha_creacion,
               COUNT(t.id) as total_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        WHERE p.id = ?
        GROUP BY p.id
    """, (id,))
    
    proyecto = cursor.fetchone()
    conn.close()
    
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    return {
        "id": proyecto[0],
        "nombre": proyecto[1],
        "descripcion": proyecto[2],
        "fecha_creacion": proyecto[3],
        "total_tareas": proyecto[4]
    }

@app.post("/proyectos", status_code=status.HTTP_201_CREATED)
def crear_proyecto(proyecto: ProyectoCreate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM proyectos WHERE nombre = ?", (proyecto.nombre,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")
    
    fecha_creacion = datetime.now().isoformat()
    
    try:
        cursor.execute("""
            INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
            VALUES (?, ?, ?)
        """, (proyecto.nombre, proyecto.descripcion, fecha_creacion))
        
        proyecto_id = cursor.lastrowid
        conn.commit()
        conn.close()
        
        return {
            "id": proyecto_id,
            "nombre": proyecto.nombre,
            "descripcion": proyecto.descripcion,
            "fecha_creacion": fecha_creacion,
            "total_tareas": 0
        }
    except sqlite3.IntegrityError:
        conn.close()
        raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")

@app.put("/proyectos/{id}")
def actualizar_proyecto(id: int, proyecto: ProyectoUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    updates = []
    params = []
    
    if proyecto.nombre is not None:

        cursor.execute("SELECT id FROM proyectos WHERE nombre = ? AND id != ?", 
                      (proyecto.nombre, id))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=409, detail="Ya existe un proyecto con ese nombre")
        updates.append("nombre = ?")
        params.append(proyecto.nombre)
    
    if proyecto.descripcion is not None:
        updates.append("descripcion = ?")
        params.append(proyecto.descripcion)
    
    if updates:
        params.append(id)
        query = f"UPDATE proyectos SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    cursor.execute("""
        SELECT p.id, p.nombre, p.descripcion, p.fecha_creacion,
               COUNT(t.id) as total_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        WHERE p.id = ?
        GROUP BY p.id
    """, (id,))
    
    proyecto_actualizado = cursor.fetchone()
    conn.close()
    
    return {
        "id": proyecto_actualizado[0],
        "nombre": proyecto_actualizado[1],
        "descripcion": proyecto_actualizado[2],
        "fecha_creacion": proyecto_actualizado[3],
        "total_tareas": proyecto_actualizado[4]
    }

@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
 
    cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?", (id,))
    tareas_eliminadas = cursor.fetchone()[0]
    
    cursor.execute("DELETE FROM proyectos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {
        "mensaje": "Proyecto eliminado",
        "tareas_eliminadas": tareas_eliminadas
    }

@app.get("/tareas")
def listar_tareas(
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    proyecto_id: Optional[int] = Query(None),
    orden: Optional[str] = Query(None)
):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, descripcion, estado, prioridad, proyecto_id, fecha_creacion FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if proyecto_id:
        query += " AND proyecto_id = ?"
        params.append(proyecto_id)
    
    if orden:
        if orden.lower() == "asc":
            query += " ORDER BY fecha_creacion ASC"
        elif orden.lower() == "desc":
            query += " ORDER BY fecha_creacion DESC"
    
    cursor.execute(query, params)
    
    tareas = []
    for row in cursor.fetchall():
        tareas.append({
            "id": row[0],
            "descripcion": row[1],
            "estado": row[2],
            "prioridad": row[3],
            "proyecto_id": row[4],
            "fecha_creacion": row[5]
        })
    
    conn.close()
    return tareas

@app.get("/proyectos/{id}/tareas")
def listar_tareas_proyecto(
    id: int,
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query(None)
):
    if not proyecto_existe(id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT id, descripcion, estado, prioridad, proyecto_id, fecha_creacion FROM tareas WHERE proyecto_id = ?"
    params = [id]
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if orden:
        if orden.lower() == "asc":
            query += " ORDER BY fecha_creacion ASC"
        elif orden.lower() == "desc":
            query += " ORDER BY fecha_creacion DESC"
    
    cursor.execute(query, params)
    
    tareas = []
    for row in cursor.fetchall():
        tareas.append({
            "id": row[0],
            "descripcion": row[1],
            "estado": row[2],
            "prioridad": row[3],
            "proyecto_id": row[4],
            "fecha_creacion": row[5]
        })
    
    conn.close()
    return tareas

@app.post("/proyectos/{id}/tareas", status_code=status.HTTP_201_CREATED)
def crear_tarea(id: int, tarea: TareaCreate):
    if not proyecto_existe(id):
        raise HTTPException(status_code=400, detail="El proyecto no existe")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, id, fecha_creacion))
    
    tarea_id = cursor.lastrowid
    conn.commit()
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "prioridad": tarea.prioridad,
        "proyecto_id": id,
        "fecha_creacion": fecha_creacion
    }

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
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
    
    if tarea.proyecto_id is not None:
    
        if not proyecto_existe(tarea.proyecto_id):
            conn.close()
            raise HTTPException(status_code=400, detail="El proyecto destino no existe")
        updates.append("proyecto_id = ?")
        params.append(tarea.proyecto_id)
    
    if updates:
        params.append(id)
        query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()
    
    return {
        "id": tarea_actualizada[0],
        "descripcion": tarea_actualizada[1],
        "estado": tarea_actualizada[2],
        "prioridad": tarea_actualizada[3],
        "proyecto_id": tarea_actualizada[4],
        "fecha_creacion": tarea_actualizada[5]
    }

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada"}


@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    if not proyecto_existe(id):
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT nombre FROM proyectos WHERE id = ?", (id,))
    proyecto_nombre = cursor.fetchone()[0]

    cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id = ?", (id,))
    total_tareas = cursor.fetchone()[0]
    
    cursor.execute("""
        SELECT estado, COUNT(*) FROM tareas WHERE proyecto_id = ? GROUP BY estado
    """, (id,))
    por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for estado, count in cursor.fetchall():
        por_estado[estado] = count
    
    cursor.execute("""
        SELECT prioridad, COUNT(*) FROM tareas WHERE proyecto_id = ? GROUP BY prioridad
    """, (id,))
    por_prioridad = {"baja": 0, "media": 0, "alta": 0}
    for prioridad, count in cursor.fetchall():
        por_prioridad[prioridad] = count
    
    conn.close()
    
    return {
        "proyecto_id": id,
        "proyecto_nombre": proyecto_nombre,
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.get("/resumen")
def resumen_general():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) FROM proyectos")
    total_proyectos = cursor.fetchone()[0]
    
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total_tareas = cursor.fetchone()[0]
    
    cursor.execute("SELECT estado, COUNT(*) FROM tareas GROUP BY estado")
    tareas_por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for estado, count in cursor.fetchall():
        tareas_por_estado[estado] = count
    
    proyecto_con_mas_tareas = None
    if total_proyectos > 0:
        cursor.execute("""
            SELECT p.id, p.nombre, COUNT(t.id) as cantidad
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            GROUP BY p.id
            ORDER BY cantidad DESC
            LIMIT 1
        """)
        resultado = cursor.fetchone()
        if resultado:
            proyecto_con_mas_tareas = {
                "id": resultado[0],
                "nombre": resultado[1],
                "cantidad_tareas": resultado[2]
            }
    
    conn.close()
    
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas_tareas
    }