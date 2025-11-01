from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List, Dict, Any
from database import init_db, get_connection, row_to_dict
from models import ProyectoCreate, ProyectoUpdate, TareaCreate, TareaUpdate
from datetime import datetime, timezone
import sqlite3

DB_NAME = "tareas.db"

app = FastAPI(title="API de Proyectos y Tareas - TP4")

ESTADOS_VALIDOS = ["pendiente", "en_progreso", "completada"]
PRIORIDADES_VALIDAS = ["baja", "media", "alta"]

init_db()

@app.post("/proyectos", status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    with get_connection() as conn:
        cur = conn.cursor()
        try:
            nombre = proyecto.nombre.strip()
            if not nombre:
                raise HTTPException(422, detail={"error": "El nombre del proyecto no puede estar vacío o contener solo espacios"})
            fecha = datetime.now(timezone.utc).isoformat()
            cur.execute(
                "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
                (nombre, proyecto.descripcion, fecha)
            )
            conn.commit()
            proyecto_id = cur.lastrowid
            cur.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
            row = cur.fetchone()
            return row_to_dict(row)
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e):
                raise HTTPException(409, detail={"error": "Nombre de proyecto duplicado"})
            raise HTTPException(400, detail={"error": str(e)})

@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = Query(None)):
    with get_connection() as conn:
        cur = conn.cursor()
        sql = "SELECT * FROM proyectos"
        params = []
        if nombre:
            sql += " WHERE LOWER(nombre) LIKE ?"
            params.append(f"%{nombre.lower()}%")
        sql += " ORDER BY fecha_creacion DESC"
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [row_to_dict(r) for r in rows]

@app.get("/proyectos/{proyecto_id}")
def obtener_proyecto(proyecto_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, detail={"error": "Proyecto no encontrado"})
        cur.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
        total_tareas = cur.fetchone()["total"]
        proyecto = row_to_dict(row)
        proyecto["total_tareas"] = total_tareas
        return proyecto

@app.put("/proyectos/{proyecto_id}")
def actualizar_proyecto(proyecto_id: int, update: ProyectoUpdate):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cur.fetchone():
            raise HTTPException(404, detail={"error": "Proyecto no encontrado"})
        updates = []
        params = []
        if update.nombre is not None:
            if not update.nombre.strip():
                raise HTTPException(422, detail={"error": "El nombre no puede estar vacío"})
            updates.append("nombre = ?")
            params.append(update.nombre.strip())
        if update.descripcion is not None:
            updates.append("descripcion = ?")
            params.append(update.descripcion)
        if not updates:
            return obtener_proyecto(proyecto_id)
        params.append(proyecto_id)
        sql = f"UPDATE proyectos SET {', '.join(updates)} WHERE id = ?"
        try:
            cur.execute(sql, params)
            conn.commit()
        except sqlite3.IntegrityError as e:
            if "UNIQUE" in str(e):
                raise HTTPException(409, detail={"error": "Nombre de proyecto duplicado"})
            raise HTTPException(400, detail={"error": str(e)})
        return obtener_proyecto(proyecto_id)

@app.delete("/proyectos/{proyecto_id}")
def eliminar_proyecto(proyecto_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cur.fetchone():
            raise HTTPException(404, detail={"error": "Proyecto no encontrado"})
        cur.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
        tareas_eliminadas = cur.fetchone()["total"]
        cur.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
        conn.commit()
        return {"mensaje": "Proyecto eliminado", "tareas_eliminadas": tareas_eliminadas}

@app.post("/proyectos/{proyecto_id}/tareas", status_code=201)
def crear_tarea(proyecto_id: int, tarea: TareaCreate):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cur.fetchone():
            raise HTTPException(400, detail={"error": "Proyecto no encontrado"})
        if tarea.estado not in ESTADOS_VALIDOS:
            raise HTTPException(422, detail={"error": f"Estado inválido. Debe ser uno de: {', '.join(ESTADOS_VALIDOS)}"})
        if tarea.prioridad and tarea.prioridad not in PRIORIDADES_VALIDAS:
            raise HTTPException(422, detail={"error": f"Prioridad inválida. Debe ser uno de: {', '.join(PRIORIDADES_VALIDAS)}"})
        fecha = datetime.now(timezone.utc).isoformat()
        cur.execute(
            "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
            (tarea.descripcion.strip(), tarea.estado, tarea.prioridad, proyecto_id, fecha)
        )
        conn.commit()
        tarea_id = cur.lastrowid
        cur.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        row = cur.fetchone()
        return row_to_dict(row)

@app.get("/proyectos/{proyecto_id}/tareas")
def listar_tareas_proyecto(
    proyecto_id: int,
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    orden: Optional[str] = Query(None)
):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cur.fetchone():
            raise HTTPException(404, detail={"error": "Proyecto no encontrado"})
        sql = "SELECT * FROM tareas WHERE proyecto_id = ?"
        params = [proyecto_id]
        condiciones = []
        if estado:
            if estado not in ESTADOS_VALIDOS:
                raise HTTPException(422, detail={"error": f"Estado inválido. Debe ser uno de: {', '.join(ESTADOS_VALIDOS)}"})
            condiciones.append("estado = ?")
            params.append(estado)
        if prioridad:
            if prioridad not in PRIORIDADES_VALIDAS:
                raise HTTPException(422, detail={"error": f"Prioridad inválida. Debe ser uno de: {', '.join(PRIORIDADES_VALIDAS)}"})
            condiciones.append("prioridad = ?")
            params.append(prioridad)
        if texto:
            condiciones.append("LOWER(descripcion) LIKE ?")
            params.append(f"%{texto.lower()}%")
        if condiciones:
            sql += " AND " + " AND ".join(condiciones)
        if orden and orden.lower() == "desc":
            sql += " ORDER BY fecha_creacion DESC"
        else:
            sql += " ORDER BY fecha_creacion ASC"
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [row_to_dict(r) for r in rows]

@app.get("/tareas")
def listar_tareas(
    proyecto_id: Optional[int] = Query(None),
    estado: Optional[str] = Query(None),
    prioridad: Optional[str] = Query(None),
    texto: Optional[str] = Query(None),
    orden: Optional[str] = Query(None)
):
    sql = "SELECT * FROM tareas"
    params = []
    condiciones = []
    if proyecto_id is not None:
        with get_connection() as conn:
            cur = conn.cursor()
            cur.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
            if not cur.fetchone():
                raise HTTPException(400, detail={"error": "Proyecto no encontrado"})
            condiciones.append("proyecto_id = ?")
            params.append(proyecto_id)
    if estado:
        if estado not in ESTADOS_VALIDOS:
            raise HTTPException(422, detail={"error": f"Estado inválido. Debe ser uno de: {', '.join(ESTADOS_VALIDOS)}"})
        condiciones.append("estado = ?")
        params.append(estado)
    if prioridad:
        if prioridad not in PRIORIDADES_VALIDAS:
            raise HTTPException(422, detail={"error": f"Prioridad inválida. Debe ser uno de: {', '.join(PRIORIDADES_VALIDAS)}"})
        condiciones.append("prioridad = ?")
        params.append(prioridad)
    if texto:
        condiciones.append("LOWER(descripcion) LIKE ?")
        params.append(f"%{texto.lower()}%")
    if condiciones:
        sql += " WHERE " + " AND ".join(condiciones)
    if orden and orden.lower() == "desc":
        sql += " ORDER BY fecha_creacion DESC"
    else:
        sql += " ORDER BY fecha_creacion ASC"
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute(sql, params)
        rows = cur.fetchall()
        return [row_to_dict(r) for r in rows]

@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int, update: TareaUpdate):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, detail={"error": "Tarea no encontrada"})
        updates = []
        params = []
        if update.descripcion is not None:
            if not update.descripcion.strip():
                raise HTTPException(422, detail={"error": "Descripción no puede estar vacía"})
            updates.append("descripcion = ?")
            params.append(update.descripcion.strip())
        if update.estado is not None:
            if update.estado not in ESTADOS_VALIDOS:
                raise HTTPException(422, detail={"error": f"Estado inválido. Debe ser uno de: {', '.join(ESTADOS_VALIDOS)}"})
            updates.append("estado = ?")
            params.append(update.estado)
        if update.prioridad is not None:
            if update.prioridad not in PRIORIDADES_VALIDAS:
                raise HTTPException(422, detail={"error": f"Prioridad inválida. Debe ser uno de: {', '.join(PRIORIDADES_VALIDAS)}"})
            updates.append("prioridad = ?")
            params.append(update.prioridad)
        if update.proyecto_id is not None:
            cur.execute("SELECT * FROM proyectos WHERE id = ?", (update.proyecto_id,))
            if not cur.fetchone():
                raise HTTPException(400, detail={"error": "Proyecto destino no encontrado"})
            updates.append("proyecto_id = ?")
            params.append(update.proyecto_id)
        if not updates:
            return row_to_dict(row)
        params.append(tarea_id)
        sql = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        cur.execute(sql, params)
        conn.commit()
        cur.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        updated = cur.fetchone()
        return row_to_dict(updated)

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        if not cur.fetchone():
            raise HTTPException(404, detail={"error": "Tarea no encontrada"})
        cur.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
        conn.commit()
        return {"mensaje": "Tarea eliminada"}

@app.get("/proyectos/{proyecto_id}/resumen")
def resumen_proyecto(proyecto_id: int):
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        row = cur.fetchone()
        if not row:
            raise HTTPException(404, detail={"error": "Proyecto no encontrado"})
        proyecto = row_to_dict(row)
        cur.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
        total_tareas = cur.fetchone()["total"]
        cur.execute("SELECT estado, COUNT(*) as cnt FROM tareas WHERE proyecto_id = ? GROUP BY estado", (proyecto_id,))
        por_estado = {r["estado"]: r["cnt"] for r in cur.fetchall()}
        cur.execute("SELECT prioridad, COUNT(*) as cnt FROM tareas WHERE proyecto_id = ? GROUP BY prioridad", (proyecto_id,))
        rows = cur.fetchall()
        por_prioridad = {r["prioridad"]: r["cnt"] for r in rows if r["prioridad"] is not None}
        if not por_prioridad:
            por_prioridad = {"baja": 0, "media": 0, "alta": 0}
        resumen = {
            "proyecto_id": proyecto["id"],
            "proyecto_nombre": proyecto["nombre"],
            "total_tareas": total_tareas,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }
        return resumen

@app.get("/resumen")
def resumen_general():
    with get_connection() as conn:
        cur = conn.cursor()
        cur.execute("SELECT COUNT(*) as total FROM proyectos")
        total_proyectos = cur.fetchone()["total"]
        cur.execute("SELECT COUNT(*) as total FROM tareas")
        total_tareas = cur.fetchone()["total"]
        cur.execute("SELECT estado, COUNT(*) as cnt FROM tareas GROUP BY estado")
        tareas_por_estado = {r["estado"]: r["cnt"] for r in cur.fetchall()}
        cur.execute("""
        SELECT proyecto_id, COUNT(*) as cnt 
        FROM tareas 
        GROUP BY proyecto_id 
        ORDER BY cnt DESC 
        LIMIT 1
        """)
        row = cur.fetchone()
        proyecto_mas_tareas = None
        if row:
            cur.execute("SELECT nombre FROM proyectos WHERE id = ?", (row["proyecto_id"],))
            nombre = cur.fetchone()["nombre"]
            proyecto_mas_tareas = {
                "id": row["proyecto_id"],
                "nombre": nombre,
                "cantidad_tareas": row["cnt"]
            }
        resumen = {
            "total_proyectos": total_proyectos,
            "total_tareas": total_tareas,
            "tareas_por_estado": tareas_por_estado,
            "proyecto_con_mas_tareas": proyecto_mas_tareas
        }
        return resumen