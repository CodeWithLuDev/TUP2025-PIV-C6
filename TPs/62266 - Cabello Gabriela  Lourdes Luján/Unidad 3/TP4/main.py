import sqlite3
from fastapi import FastAPI, HTTPException, Query, status
from typing import List, Optional, Literal, Any, Dict
from datetime import datetime

from models import ProyectoCreate, Proyecto, TareaCreate, TareaUpdate, Tarea
from database import (
    get_db_connection, init_db, 
    project_exists, task_exists, get_project_with_task_count, 
    get_general_summary,
    DB_NAME 
) 

init_db()

app = FastAPI(
    title="Gestor de Proyectos y Tareas", 
    description="TP4: API con relaciones 1:N y filtros avanzados."
)

def get_current_time():
    return datetime.now().isoformat()

def _filter_tasks(
    project_id: Optional[int], 
    estado: Optional[str], 
    prioridad: Optional[str], 
    orden: Literal["asc", "desc"]
) -> List[sqlite3.Row]:
    conn = get_db_connection()
    query = "SELECT * FROM tareas WHERE 1=1"
    params: List[Any] = []

    if project_id is not None:
        query += " AND proyecto_id = ?"
        params.append(project_id)
        
    if estado:
        query += " AND estado = ?"
        params.append(estado)
        
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
        
    query += f" ORDER BY fecha_creacion {orden.upper()}"
    
    tasks = conn.execute(query, params).fetchall()
    conn.close()
    return tasks

@app.post("/proyectos", response_model=Proyecto, status_code=status.HTTP_201_CREATED)
def create_project(project_data: ProyectoCreate):
    conn = get_db_connection()
    
    if conn.execute("SELECT id FROM proyectos WHERE nombre = ?", (project_data.nombre,)).fetchone():
        conn.close()
        raise HTTPException(status_code=409, detail=f"Conflicto: Ya existe un proyecto llamado '{project_data.nombre}'.")
        
    try:
        cursor = conn.execute(
            "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
            (project_data.nombre, project_data.descripcion, get_current_time())
        )
        conn.commit()
        
        new_project = get_project_with_task_count(cursor.lastrowid)
        return Proyecto.model_validate(dict(new_project))
        
    finally:
        conn.close()

@app.get("/proyectos", response_model=List[Proyecto])
def list_projects(nombre: Optional[str] = Query(None)):
    conn = get_db_connection()
    
    query = "SELECT id, nombre, descripcion, fecha_creacion FROM proyectos"
    params = []
    
    if nombre:
        query += " WHERE nombre LIKE ?"
        params.append(f"%{nombre}%")
        
    projects = conn.execute(query, params).fetchall()
    conn.close()
    
    return [Proyecto.model_validate(dict(p)) for p in projects]

@app.get("/proyectos/{id}", response_model=Proyecto)
def get_project(id: int):
    project_row = get_project_with_task_count(id)
    if project_row is None:
        raise HTTPException(status_code=404, detail=f"Error: Proyecto con ID {id} no encontrado.")
    
    return Proyecto.model_validate(dict(project_row))

@app.put("/proyectos/{id}", response_model=Proyecto)
def update_project(id: int, project_data: ProyectoCreate):
    if not project_exists(id):
        raise HTTPException(status_code=404, detail=f"Error: Proyecto con ID {id} no encontrado.")
        
    conn = get_db_connection()
    
    existing_by_name = conn.execute("SELECT id FROM proyectos WHERE nombre = ? AND id != ?", (project_data.nombre, id)).fetchone()
    if existing_by_name:
        conn.close()
        raise HTTPException(status_code=409, detail=f"Conflicto: Ya existe otro proyecto con el nombre '{project_data.nombre}'.")

    conn.execute(
        "UPDATE proyectos SET nombre = ?, descripcion = ? WHERE id = ?",
        (project_data.nombre, project_data.descripcion, id)
    )
    conn.commit()
    conn.close()

    return get_project(id)

@app.delete("/proyectos/{id}")
def delete_project(id: int):
    if not project_exists(id):
        raise HTTPException(status_code=404, detail=f"Error: Proyecto con ID {id} no encontrado.")

    conn = get_db_connection()
    
    tareas_a_eliminar = conn.execute("SELECT COUNT(id) FROM tareas WHERE proyecto_id = ?", (id,)).fetchone()[0]

    conn.execute("DELETE FROM proyectos WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"message": f"Proyecto {id} y {tareas_a_eliminar} tareas asociadas eliminadas.", "tareas_eliminadas": tareas_a_eliminar}

@app.post("/proyectos/{id}/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED)
def create_task_for_project(id: int, task_data: TareaCreate):
    if not project_exists(id):
        raise HTTPException(status_code=400, detail=f"Error: El proyecto con ID {id} no existe. No se puede crear la tarea.")

    conn = get_db_connection()
    cursor = conn.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
        (task_data.descripcion, task_data.estado, task_data.prioridad, id, get_current_time())
    )
    conn.commit()
    
    new_task = conn.execute("SELECT * FROM tareas WHERE id = ?", (cursor.lastrowid,)).fetchone()
    conn.close()
    return Tarea.model_validate(dict(new_task))

@app.get("/proyectos/{id}/tareas", response_model=List[Tarea])
def list_project_tasks(
    id: int, 
    estado: Optional[str] = Query(None), 
    prioridad: Optional[str] = Query(None), 
    orden: Literal["asc", "desc"] = Query("asc")
):
    if not project_exists(id):
        raise HTTPException(status_code=404, detail=f"Error: Proyecto con ID {id} no encontrado.")

    tasks = _filter_tasks(id, estado, prioridad, orden)
    return [Tarea.model_validate(dict(task)) for task in tasks]

@app.put("/tareas/{id}", response_model=Tarea)
def update_task(id: int, task_data: TareaUpdate):
    if not task_exists(id):
        raise HTTPException(status_code=404, detail=f"Error: Tarea con ID {id} no encontrada.")

    conn = get_db_connection()
    
    current_task = conn.execute("SELECT * FROM tareas WHERE id = ?", (id,)).fetchone()
    
    new_proyecto_id = task_data.proyecto_id if task_data.proyecto_id is not None else current_task['proyecto_id']

    if not project_exists(new_proyecto_id):
        conn.close()
        raise HTTPException(status_code=400, detail=f"Error: El nuevo proyecto_id {new_proyecto_id} no existe.")

    # Lógica de Actualización Parcial: Si el campo es None, usa el valor actual de la DB.
    descripcion = task_data.descripcion if task_data.descripcion is not None else current_task['descripcion']
    estado = task_data.estado if task_data.estado is not None else current_task['estado']
    prioridad = task_data.prioridad if task_data.prioridad is not None else current_task['prioridad']
    
    conn.execute(
        "UPDATE tareas SET descripcion = ?, estado = ?, prioridad = ?, proyecto_id = ? WHERE id = ?",
        (descripcion, estado, prioridad, new_proyecto_id, id)
    )
    conn.commit()
    
    updated_task = conn.execute("SELECT * FROM tareas WHERE id = ?", (id,)).fetchone()
    conn.close()
    return Tarea.model_validate(dict(updated_task))

@app.delete("/tareas/{id}")
def delete_task(id: int):
    conn = get_db_connection()
    cursor = conn.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    if cursor.rowcount == 0:
        raise HTTPException(status_code=404, detail=f"Error: Tarea con ID {id} no encontrada.")
    
    return {"message": f"Tarea con ID {id} eliminada exitosamente."}

@app.get("/tareas", response_model=List[Tarea])
def list_all_tasks_and_filter(
    estado: Optional[str] = Query(None), 
    prioridad: Optional[str] = Query(None), 
    proyecto_id: Optional[int] = Query(None),
    orden: Literal["asc", "desc"] = Query("asc")
):
    tasks = _filter_tasks(proyecto_id, estado, prioridad, orden)
    return [Tarea.model_validate(dict(task)) for task in tasks]

@app.get("/proyectos/{id}/resumen")
def project_summary(id: int):
    conn = get_db_connection()
    project_row = conn.execute("SELECT nombre FROM proyectos WHERE id = ?", (id,)).fetchone()
    if not project_row:
        conn.close()
        raise HTTPException(status_code=404, detail=f"Error: Proyecto con ID {id} no encontrado.")
        
    total_tareas = conn.execute("SELECT COUNT(id) FROM tareas WHERE proyecto_id = ?", (id,)).fetchone()[0]

    por_estado: Dict[str, int] = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    db_estado = {
        row['estado']: row['count'] 
        for row in conn.execute("SELECT estado, COUNT(id) as count FROM tareas WHERE proyecto_id = ? GROUP BY estado", (id,))
    }
    por_estado.update(db_estado)
    
    por_prioridad: Dict[str, int] = {"baja": 0, "media": 0, "alta": 0}
    db_prioridad = {
        row['prioridad']: row['count'] 
        for row in conn.execute("SELECT prioridad, COUNT(id) as count FROM tareas WHERE proyecto_id = ? GROUP BY prioridad", (id,))
    }
    por_prioridad.update(db_prioridad)
    
    conn.close()

    return {
        "proyecto_id": id,
        "proyecto_nombre": project_row['nombre'],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.get("/resumen")
def general_summary():
    summary = get_general_summary()
    
    default_estados = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    default_estados.update(summary['tareas_por_estado'])
    summary['tareas_por_estado'] = default_estados

    return summary