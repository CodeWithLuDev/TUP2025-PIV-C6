from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from database import init_db, get_connection
from models import ProyectoCreate, ProyectoUpdate, TareaCreate, TareaUpdate
from datetime import datetime
from typing import Optional

DB_NAME = "tareas.db"
init_db()
app = FastAPI()

@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    if nombre:
        cursor.execute("SELECT * FROM proyectos WHERE nombre LIKE ?", (f"%{nombre}%",))
    else:
        cursor.execute("SELECT * FROM proyectos")
    proyectos = [dict(row) for row in cursor.fetchall()]
    for proyecto in proyectos:
        cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=?", (proyecto["id"],))
        proyecto["total_tareas"] = cursor.fetchone()[0]
    conn.close()
    return proyectos

@app.get("/proyectos/{id}")
def obtener_proyecto(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    proyecto = dict(row)
    cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=?", (id,))
    proyecto["total_tareas"] = cursor.fetchone()[0]
    conn.close()
    return proyecto

@app.post("/proyectos", status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?,?,?)",
            (proyecto.nombre, proyecto.descripcion, datetime.now().isoformat())
        )
        conn.commit()
        id = cursor.lastrowid
        cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
        row = cursor.fetchone()
        return dict(row)
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=409, detail="Nombre de proyecto duplicado")
    finally:
        conn.close()

@app.put("/proyectos/{id}")
def actualizar_proyecto(id: int, proyecto: ProyectoUpdate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    try:
        cursor.execute(
            "UPDATE proyectos SET nombre=?, descripcion=? WHERE id=?",
            (proyecto.nombre, proyecto.descripcion, id)
        )
        conn.commit()
        cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
        return dict(cursor.fetchone())
    except Exception:
        conn.rollback()
        raise HTTPException(status_code=409, detail="Nombre de proyecto duplicado")
    finally:
        conn.close()

@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=?", (id,))
    tareas_eliminadas = cursor.fetchone()[0]
    cursor.execute("DELETE FROM proyectos WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Proyecto eliminado", "tareas_eliminadas": tareas_eliminadas}

@app.get("/proyectos/{id}/tareas")
def listar_tareas_proyecto(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    cursor.execute("SELECT * FROM tareas WHERE proyecto_id=?", (id,))
    tareas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tareas

@app.get("/tareas")
def listar_tareas(estado: Optional[str] = None, prioridad: Optional[str] = None, proyecto_id: Optional[int] = None, orden: Optional[str] = None):
    conn = get_connection()
    cursor = conn.cursor()
    query = "SELECT * FROM tareas"
    filtros = []
    params = []
    if estado:
        filtros.append("estado=?")
        params.append(estado)
    if prioridad:
        filtros.append("prioridad=?")
        params.append(prioridad)
    if proyecto_id:
        filtros.append("proyecto_id=?")
        params.append(proyecto_id)
    if filtros:
        query += " WHERE " + " AND ".join(filtros)
    if orden == "asc":
        query += " ORDER BY fecha_creacion ASC"
    elif orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    cursor.execute(query, tuple(params))
    tareas = [dict(row) for row in cursor.fetchall()]
    conn.close()
    return tareas

@app.post("/proyectos/{id}/tareas", status_code=201)
def crear_tarea(id: int, tarea: TareaCreate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=400, detail="Proyecto inexistente")
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?,?,?,?,?)",
        (
            tarea.descripcion,
            tarea.estado or "pendiente",
            tarea.prioridad or "media",
            id,
            datetime.now().isoformat()
        )
    )
    conn.commit()
    tarea_id = cursor.lastrowid
    cursor.execute("SELECT * FROM tareas WHERE id=?", (tarea_id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id=?", (id,))
    row = cursor.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    update_data = {**dict(row), **tarea.dict(exclude_unset=True)}
    if update_data.get("proyecto_id"):
        cursor.execute("SELECT * FROM proyectos WHERE id=?", (update_data["proyecto_id"],))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="Proyecto inexistente")
    cursor.execute("""
        UPDATE tareas SET descripcion=?, estado=?, prioridad=?, proyecto_id=? WHERE id=?
    """, (
        update_data["descripcion"],
        update_data["estado"],
        update_data["prioridad"],
        update_data["proyecto_id"],
        id
    ))
    conn.commit()
    cursor.execute("SELECT * FROM tareas WHERE id=?", (id,))
    row = cursor.fetchone()
    conn.close()
    return dict(row)

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id=?", (id,))
    if not cursor.fetchone():
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    cursor.execute("DELETE FROM tareas WHERE id=?", (id,))
    conn.commit()
    conn.close()
    return {"mensaje": "Tarea eliminada"}

@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM proyectos WHERE id=?", (id,))
    proyecto = cursor.fetchone()
    if not proyecto:
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    proyecto = dict(proyecto)
    cursor.execute("SELECT estado, COUNT(*) FROM tareas WHERE proyecto_id=? GROUP BY estado", (id,))
    por_estado = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.execute("SELECT prioridad, COUNT(*) FROM tareas WHERE proyecto_id=? GROUP BY prioridad", (id,))
    por_prioridad = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.execute("SELECT COUNT(*) FROM tareas WHERE proyecto_id=?", (id,))
    total_tareas = cursor.fetchone()[0]
    conn.close()
    return {
        "proyecto_id": proyecto["id"],
        "proyecto_nombre": proyecto["nombre"],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.get("/resumen")
def resumen_general():
    conn = get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM proyectos")
    total_proyectos = cursor.fetchone()[0]
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total_tareas = cursor.fetchone()[0]
    cursor.execute("SELECT estado, COUNT(*) FROM tareas GROUP BY estado")
    tareas_por_estado = {row[0]: row[1] for row in cursor.fetchall()}
    cursor.execute("""
        SELECT proyecto_id, COUNT(*) as cantidad FROM tareas GROUP BY proyecto_id ORDER BY cantidad DESC LIMIT 1
    """)
    row = cursor.fetchone()
    proyecto_con_mas_tareas = None
    if row:
        cursor.execute("SELECT nombre FROM proyectos WHERE id=?", (row[0],))
        nombre = cursor.fetchone()[0]
        proyecto_con_mas_tareas = {"id": row[0], "nombre": nombre, "cantidad_tareas": row[1]}
    conn.close()
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas_tareas
    }
