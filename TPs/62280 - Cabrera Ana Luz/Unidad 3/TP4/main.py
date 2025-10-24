from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime
import sqlite3

app = FastAPI(title="API de Tareas con Proyectos", version="4.0.0")

DB_NAME = "tareas.db"

class ProyectoCrear(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None
    
    @validator('nombre')
    def validar_nombre(cls, v):
        if not v or v.strip() == "":
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()

class ProyectoActualizar(BaseModel):
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    
    @validator('nombre')
    def validar_nombre(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError('El nombre no puede estar vacío')
        return v.strip() if v else v

class TareaCrear(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    @validator('descripcion')
    def validar_descripcion(cls, v):
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()

class TareaActualizar(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None
    
    @validator('descripcion')
    def validar_descripcion(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError('La descripción no puede estar vacía')
        return v.strip() if v else v

def init_db():
    conn = sqlite3.connect(DB_NAME)
    c = conn.cursor()
    c.execute("PRAGMA foreign_keys = ON")
    c.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        )
    """)
    c.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media',
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)
    conn.commit()
    conn.close()

def get_conn():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def dict_from_row(row):
    return {k: row[k] for k in row.keys()}

@app.on_event("startup")
def startup():
    init_db()

@app.post("/proyectos", status_code=201)
def crear_proyecto(proyecto: ProyectoCrear):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM proyectos WHERE nombre = ?", (proyecto.nombre,))
    if c.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail={"error": "Ya existe un proyecto con ese nombre"})
    fecha = datetime.now().isoformat()
    c.execute(
        "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
        (proyecto.nombre, proyecto.descripcion, fecha)
    )
    proyecto_id = c.lastrowid
    conn.commit()
    c.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    resultado = c.fetchone()
    conn.close()
    return dict_from_row(resultado)

@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = Query(None)):
    conn = get_conn()
    c = conn.cursor()
    if nombre:
        c.execute("SELECT * FROM proyectos WHERE nombre LIKE ?", (f"%{nombre}%",))
    else:
        c.execute("SELECT * FROM proyectos")
    proyectos = c.fetchall()
    conn.close()
    return [dict_from_row(p) for p in proyectos]

@app.get("/proyectos/{id}")
def obtener_proyecto(id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto = c.fetchone()
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Proyecto no encontrado"})
    c.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (id,))
    total = c.fetchone()["total"]
    conn.close()
    resultado = dict_from_row(proyecto)
    resultado["total_tareas"] = total
    return resultado

@app.put("/proyectos/{id}")
def actualizar_proyecto(id: int, proyecto: ProyectoActualizar):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Proyecto no encontrado"})
    cambios = []
    params = []
    if proyecto.nombre is not None:
        c.execute("SELECT id FROM proyectos WHERE nombre = ? AND id != ?", (proyecto.nombre, id))
        if c.fetchone():
            conn.close()
            raise HTTPException(status_code=409, detail={"error": "Ya existe un proyecto con ese nombre"})
        cambios.append("nombre = ?")
        params.append(proyecto.nombre)
    if proyecto.descripcion is not None:
        cambios.append("descripcion = ?")
        params.append(proyecto.descripcion)
    if cambios:
        params.append(id)
        c.execute(f"UPDATE proyectos SET {', '.join(cambios)} WHERE id = ?", params)
        conn.commit()
    c.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    resultado = c.fetchone()
    conn.close()
    return dict_from_row(resultado)

@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto = c.fetchone()
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Proyecto no encontrado"})
    c.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (id,))
    total_tareas = c.fetchone()["total"]
    c.execute("DELETE FROM proyectos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {
        "mensaje": "Proyecto eliminado exitosamente",
        "proyecto_eliminado": dict_from_row(proyecto),
        "tareas_eliminadas": total_tareas
    }

@app.post("/proyectos/{id}/tareas", status_code=201)
def crear_tarea_en_proyecto(id: int, tarea: TareaCrear):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=400, detail={"error": "El proyecto no existe"})
    fecha = datetime.now().isoformat()
    c.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
        (tarea.descripcion, tarea.estado, tarea.prioridad, id, fecha)
    )
    tarea_id = c.lastrowid
    conn.commit()
    c.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    resultado = c.fetchone()
    conn.close()
    return dict_from_row(resultado)

@app.get("/proyectos/{id}/tareas")
def listar_tareas_proyecto(
    id: int,
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Query(None),
    prioridad: Optional[Literal["baja", "media", "alta"]] = Query(None),
    orden: Optional[Literal["asc", "desc"]] = Query("desc")
):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT id FROM proyectos WHERE id = ?", (id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Proyecto no encontrado"})
    query = "SELECT * FROM tareas WHERE proyecto_id = ?"
    params = [id]
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    query += f" ORDER BY fecha_creacion {'ASC' if orden == 'asc' else 'DESC'}"
    c.execute(query, params)
    tareas = c.fetchall()
    conn.close()
    return [dict_from_row(t) for t in tareas]

@app.get("/tareas")
def listar_todas_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Query(None),
    prioridad: Optional[Literal["baja", "media", "alta"]] = Query(None),
    proyecto_id: Optional[int] = Query(None),
    orden: Optional[Literal["asc", "desc"]] = Query("desc")
):
    conn = get_conn()
    c = conn.cursor()
    query = "SELECT * FROM tareas WHERE 1=1"
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
    query += f" ORDER BY fecha_creacion {'ASC' if orden == 'asc' else 'DESC'}"
    c.execute(query, params)
    tareas = c.fetchall()
    conn.close()
    return [dict_from_row(t) for t in tareas]

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaActualizar):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    if not c.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    cambios = []
    params = []
    if tarea.descripcion is not None:
        cambios.append("descripcion = ?")
        params.append(tarea.descripcion)
    if tarea.estado is not None:
        cambios.append("estado = ?")
        params.append(tarea.estado)
    if tarea.prioridad is not None:
        cambios.append("prioridad = ?")
        params.append(tarea.prioridad)
    if tarea.proyecto_id is not None:
        c.execute("SELECT id FROM proyectos WHERE id = ?", (tarea.proyecto_id,))
        if not c.fetchone():
            conn.close()
            raise HTTPException(status_code=400, detail={"error": "El proyecto destino no existe"})
        cambios.append("proyecto_id = ?")
        params.append(tarea.proyecto_id)
    if cambios:
        params.append(id)
        c.execute(f"UPDATE tareas SET {', '.join(cambios)} WHERE id = ?", params)
        conn.commit()
    c.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    resultado = c.fetchone()
    conn.close()
    return dict_from_row(resultado)

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = c.fetchone()
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    c.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea eliminada exitosamente", "tarea_eliminada": dict_from_row(tarea)}

@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto = c.fetchone()
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Proyecto no encontrado"})
    c.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (id,))
    total = c.fetchone()["total"]
    c.execute("""
        SELECT estado, COUNT(*) as cantidad 
        FROM tareas 
        WHERE proyecto_id = ?
        GROUP BY estado
    """, (id,))
    por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for row in c.fetchall():
        por_estado[row["estado"]] = row["cantidad"]
    c.execute("""
        SELECT prioridad, COUNT(*) as cantidad 
        FROM tareas 
        WHERE proyecto_id = ?
        GROUP BY prioridad
    """, (id,))
    por_prioridad = {"baja": 0, "media": 0, "alta": 0}
    for row in c.fetchall():
        por_prioridad[row["prioridad"]] = row["cantidad"]
    conn.close()
    return {
        "proyecto_id": id,
        "proyecto_nombre": proyecto["nombre"],
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.get("/resumen")
def resumen_general():
    conn = get_conn()
    c = conn.cursor()
    c.execute("SELECT COUNT(*) as total FROM proyectos")
    total_proyectos = c.fetchone()["total"]
    c.execute("SELECT COUNT(*) as total FROM tareas")
    total_tareas = c.fetchone()["total"]
    c.execute("""
        SELECT estado, COUNT(*) as cantidad 
        FROM tareas 
        GROUP BY estado
    """)
    por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for row in c.fetchall():
        por_estado[row["estado"]] = row["cantidad"]
    c.execute("""
        SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        GROUP BY p.id
        ORDER BY cantidad_tareas DESC
        LIMIT 1
    """)
    proyecto_top = c.fetchone()
    proyecto_con_mas = None
    if proyecto_top and proyecto_top["cantidad_tareas"] > 0:
        proyecto_con_mas = {
            "id": proyecto_top["id"],
            "nombre": proyecto_top["nombre"],
            "cantidad_tareas": proyecto_top["cantidad_tareas"]
        }
    conn.close()
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas
    }

@app.get("/")
def root():
    return {
        "nombre": "API de Tareas con Proyectos",
        "version": "4.0.0",
        "mensaje": "Sistema de gestión de proyectos y tareas relacionadas"
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
