from fastapi import FastAPI, HTTPException, Query
from typing import Optional
from models import ProyectoCreate, ProyectoUpdate, TareaCreate, TareaUpdate
from database import get_db, init_db, verificar_proyecto_existe, obtener_fecha_actual

app = FastAPI(title="API de Gestión de Proyectos y Tareas", version="2.0")


@app.on_event("startup")
def startup():
    init_db()


@app.get("/")
def home():
    return {"mensaje": "API de Proyectos y Tareas - TP4"}


@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = Query(None)):
    """Lista todos los proyectos. Filtro opcional por nombre."""
    conn = get_db()
    cursor = conn.cursor()
    
    query = "SELECT * FROM proyectos WHERE 1=1"
    params = []
    
    if nombre:
        query += " AND nombre LIKE ?"
        params.append(f"%{nombre}%")
    
    cursor.execute(query, params)
    proyectos = cursor.fetchall()
    conn.close()
    
    return [dict(proyecto) for proyecto in proyectos]


@app.get("/proyectos/{id}")
def obtener_proyecto(id: int):
    """Obtiene un proyecto específico con contador de tareas"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (id,))
    total_tareas = cursor.fetchone()["total"]
    
    conn.close()
    
    proyecto_dict = dict(proyecto)
    proyecto_dict["total_tareas"] = total_tareas
    
    return proyecto_dict


@app.post("/proyectos", status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    """Crea un nuevo proyecto"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT id FROM proyectos WHERE nombre = ?", (proyecto.nombre,))
    if cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail=f"Ya existe un proyecto con el nombre '{proyecto.nombre}'")
    
    fecha_creacion = obtener_fecha_actual()
    
    cursor.execute(
        "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
        (proyecto.nombre, proyecto.descripcion, fecha_creacion)
    )
    conn.commit()
    
    proyecto_id = cursor.lastrowid
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    nuevo_proyecto = cursor.fetchone()
    conn.close()
    
    return dict(nuevo_proyecto)


@app.put("/proyectos/{id}")
def actualizar_proyecto(id: int, proyecto: ProyectoUpdate):
    """Modifica un proyecto existente"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto_existente = cursor.fetchone()
    
    if not proyecto_existente:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    if proyecto.nombre:
        cursor.execute("SELECT id FROM proyectos WHERE nombre = ? AND id != ?", (proyecto.nombre, id))
        if cursor.fetchone():
            conn.close()
            raise HTTPException(status_code=409, detail=f"Ya existe otro proyecto con el nombre '{proyecto.nombre}'")
    
    updates = []
    params = []
    
    if proyecto.nombre is not None:
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
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto_actualizado = cursor.fetchone()
    conn.close()
    
    return dict(proyecto_actualizado)


@app.delete("/proyectos/{id}", status_code=204)
def eliminar_proyecto(id: int):
    """Elimina un proyecto y todas sus tareas asociadas"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    cursor.execute("DELETE FROM proyectos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return None


@app.get("/proyectos/{id}/tareas")
def listar_tareas_proyecto(
    id: int,
    estado: Optional[str] = Query(None, pattern="^(pendiente|en_progreso|completada)$"),
    prioridad: Optional[str] = Query(None, pattern="^(baja|media|alta)$"),
    orden: Optional[str] = Query(None, pattern="^(asc|desc)$")
):
    """Lista todas las tareas de un proyecto específico"""
    conn = get_db()
    cursor = conn.cursor()
    
    if not verificar_proyecto_existe(id):
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    query = "SELECT * FROM tareas WHERE proyecto_id = ?"
    params = [id]
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if orden:
        query += f" ORDER BY fecha_creacion {'ASC' if orden == 'asc' else 'DESC'}"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [dict(tarea) for tarea in tareas]


@app.get("/tareas")
def listar_todas_tareas(
    estado: Optional[str] = Query(None, pattern="^(pendiente|en_progreso|completada)$"),
    prioridad: Optional[str] = Query(None, pattern="^(baja|media|alta)$"),
    proyecto_id: Optional[int] = None,
    orden: Optional[str] = Query(None, pattern="^(asc|desc)$")
):
    """Lista todas las tareas (de todos los proyectos) con filtros opcionales"""
    conn = get_db()
    cursor = conn.cursor()
    
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
    
    if orden:
        query += f" ORDER BY fecha_creacion {'ASC' if orden == 'asc' else 'DESC'}"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [dict(tarea) for tarea in tareas]


@app.post("/proyectos/{id}/tareas", status_code=201)
def crear_tarea(id: int, tarea: TareaCreate):
    """Crea una tarea dentro de un proyecto"""
    conn = get_db()
    cursor = conn.cursor()
    
    if not verificar_proyecto_existe(id):
        conn.close()
        raise HTTPException(status_code=400, detail=f"El proyecto con id {id} no existe")
    
    fecha_creacion = obtener_fecha_actual()
    
    cursor.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
        (tarea.descripcion, tarea.estado, tarea.prioridad, id, fecha_creacion)
    )
    conn.commit()
    
    tarea_id = cursor.lastrowid
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    nueva_tarea = cursor.fetchone()
    conn.close()
    
    return dict(nueva_tarea)


@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    """Modifica una tarea existente (puede cambiar de proyecto)"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    if tarea.proyecto_id is not None:
        if not verificar_proyecto_existe(tarea.proyecto_id):
            conn.close()
            raise HTTPException(status_code=400, detail=f"El proyecto con id {tarea.proyecto_id} no existe")
    
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
    
    return dict(tarea_actualizada)


@app.delete("/tareas/{id}", status_code=204)
def eliminar_tarea(id: int):
    """Elimina una tarea"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return None


@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    """Devuelve estadísticas detalladas de un proyecto"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        raise HTTPException(status_code=404, detail="Proyecto no encontrado")
    
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (id,))
    total_tareas = cursor.fetchone()["total"]
    
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        WHERE proyecto_id = ?
        GROUP BY estado
    """, (id,))
    por_estado = {row["estado"]: row["cantidad"] for row in cursor.fetchall()}
    
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad
        FROM tareas
        WHERE proyecto_id = ?
        GROUP BY prioridad
    """, (id,))
    por_prioridad = {row["prioridad"]: row["cantidad"] for row in cursor.fetchall()}
    
    conn.close()
    
    return {
        "proyecto_id": id,
        "proyecto_nombre": proyecto["nombre"],
        "total_tareas": total_tareas,
        "por_estado": {
            "pendiente": por_estado.get("pendiente", 0),
            "en_progreso": por_estado.get("en_progreso", 0),
            "completada": por_estado.get("completada", 0)
        },
        "por_prioridad": {
            "baja": por_prioridad.get("baja", 0),
            "media": por_prioridad.get("media", 0),
            "alta": por_prioridad.get("alta", 0)
        }
    }


@app.get("/resumen")
def resumen_general():
    """Resumen general de toda la aplicación"""
    conn = get_db()
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
    tareas_por_estado = {row["estado"]: row["cantidad"] for row in cursor.fetchall()}
    
    cursor.execute("""
        SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        GROUP BY p.id, p.nombre
        ORDER BY cantidad_tareas DESC
        LIMIT 1
    """)
    proyecto_top = cursor.fetchone()
    
    conn.close()
    
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
        "tareas_por_estado": {
            "pendiente": tareas_por_estado.get("pendiente", 0),
            "en_progreso": tareas_por_estado.get("en_progreso", 0),
            "completada": tareas_por_estado.get("completada", 0)
        },
        "proyecto_con_mas_tareas": proyecto_con_mas_tareas
    }