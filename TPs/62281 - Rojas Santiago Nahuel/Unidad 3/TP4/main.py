from fastapi import FastAPI, HTTPException, Query
from typing import Optional, Literal
from datetime import datetime
import sqlite3
from contextlib import contextmanager
from models import ProyectoCreate, ProyectoUpdate, TareaCreate, TareaUpdate

app = FastAPI(title="api de gestion de proyectos y tareas")

db_name = "tareas.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("pragma foreign_keys = on")
        
        cursor.execute("""
            create table if not exists proyectos (
                id integer primary key autoincrement,
                nombre text not null unique,
                descripcion text,
                fecha_creacion text not null
            )
        """)
        
        cursor.execute("""
            create table if not exists tareas (
                id integer primary key autoincrement,
                descripcion text not null,
                estado text not null,
                prioridad text not null,
                proyecto_id integer not null,
                fecha_creacion text not null,
                foreign key (proyecto_id) references proyectos(id) on delete cascade
            )
        """)
        
        conn.commit()

init_db()

@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = None):
    with get_db() as conn:
        cursor = conn.cursor()
        
        if nombre:
            cursor.execute(
                "select * from proyectos where nombre like ?",
                (f"%{nombre}%",)
            )
        else:
            cursor.execute("select * from proyectos")
        
        proyectos = cursor.fetchall()
        
        resultado = []
        for proyecto in proyectos:
            resultado.append({
                "id": proyecto["id"],
                "nombre": proyecto["nombre"],
                "descripcion": proyecto["descripcion"],
                "fecha_creacion": proyecto["fecha_creacion"]
            })
        
        return resultado

@app.get("/proyectos/{id}")
def obtener_proyecto(id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("select * from proyectos where id = ?", (id,))
        proyecto = cursor.fetchone()
        
        if not proyecto:
            raise HTTPException(status_code=404, detail="proyecto no encontrado")
        
        cursor.execute(
            "select count(*) as total from tareas where proyecto_id = ?",
            (id,)
        )
        total_tareas = cursor.fetchone()["total"]
        
        return {
            "id": proyecto["id"],
            "nombre": proyecto["nombre"],
            "descripcion": proyecto["descripcion"],
            "fecha_creacion": proyecto["fecha_creacion"],
            "total_tareas": total_tareas
        }

@app.post("/proyectos", status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    if not proyecto.nombre or proyecto.nombre.strip() == "":
        raise HTTPException(status_code=400, detail="el nombre del proyecto no puede estar vacio")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("select id from proyectos where nombre = ?", (proyecto.nombre,))
        if cursor.fetchone():
            raise HTTPException(status_code=409, detail="ya existe un proyecto con ese nombre")
        
        fecha_creacion = datetime.now().isoformat()
        
        try:
            cursor.execute(
                "insert into proyectos (nombre, descripcion, fecha_creacion) values (?, ?, ?)",
                (proyecto.nombre, proyecto.descripcion, fecha_creacion)
            )
            conn.commit()
            
            return {
                "id": cursor.lastrowid,
                "nombre": proyecto.nombre,
                "descripcion": proyecto.descripcion,
                "fecha_creacion": fecha_creacion
            }
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=409, detail="ya existe un proyecto con ese nombre")

@app.put("/proyectos/{id}")
def modificar_proyecto(id: int, proyecto: ProyectoUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("select * from proyectos where id = ?", (id,))
        proyecto_actual = cursor.fetchone()
        
        if not proyecto_actual:
            raise HTTPException(status_code=404, detail="proyecto no encontrado")
        
        if proyecto.nombre:
            if not proyecto.nombre.strip():
                raise HTTPException(status_code=400, detail="el nombre del proyecto no puede estar vacio")
            
            cursor.execute(
                "select id from proyectos where nombre = ? and id != ?",
                (proyecto.nombre, id)
            )
            if cursor.fetchone():
                raise HTTPException(status_code=409, detail="ya existe otro proyecto con ese nombre")
        
        nombre_final = proyecto.nombre if proyecto.nombre else proyecto_actual["nombre"]
        descripcion_final = proyecto.descripcion if proyecto.descripcion is not None else proyecto_actual["descripcion"]
        
        cursor.execute(
            "update proyectos set nombre = ?, descripcion = ? where id = ?",
            (nombre_final, descripcion_final, id)
        )
        conn.commit()
        
        return {
            "id": id,
            "nombre": nombre_final,
            "descripcion": descripcion_final,
            "fecha_creacion": proyecto_actual["fecha_creacion"]
        }

@app.delete("/proyectos/{id}")
def eliminar_proyecto(id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("pragma foreign_keys = on")
        
        cursor.execute("select * from proyectos where id = ?", (id,))
        proyecto = cursor.fetchone()
        
        if not proyecto:
            raise HTTPException(status_code=404, detail="proyecto no encontrado")
        
        cursor.execute("delete from proyectos where id = ?", (id,))
        conn.commit()
        
        return {"mensaje": "proyecto eliminado exitosamente"}

@app.get("/tareas")
def listar_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None,
    prioridad: Optional[Literal["baja", "media", "alta"]] = None,
    proyecto_id: Optional[int] = None,
    orden: Optional[Literal["asc", "desc"]] = "asc"
):
    with get_db() as conn:
        cursor = conn.cursor()
        
        query = "select * from tareas where 1=1"
        params = []
        
        if estado:
            query += " and estado = ?"
            params.append(estado)
        
        if prioridad:
            query += " and prioridad = ?"
            params.append(prioridad)
        
        if proyecto_id:
            query += " and proyecto_id = ?"
            params.append(proyecto_id)
        
        query += f" order by fecha_creacion {orden.upper()}"
        
        cursor.execute(query, params)
        tareas = cursor.fetchall()
        
        resultado = []
        for tarea in tareas:
            resultado.append({
                "id": tarea["id"],
                "descripcion": tarea["descripcion"],
                "estado": tarea["estado"],
                "prioridad": tarea["prioridad"],
                "proyecto_id": tarea["proyecto_id"],
                "fecha_creacion": tarea["fecha_creacion"]
            })
        
        return resultado

@app.get("/proyectos/{id}/tareas")
def listar_tareas_proyecto(
    id: int,
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None,
    prioridad: Optional[Literal["baja", "media", "alta"]] = None,
    orden: Optional[Literal["asc", "desc"]] = "asc"
):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("select id from proyectos where id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="proyecto no encontrado")
        
        query = "select * from tareas where proyecto_id = ?"
        params = [id]
        
        if estado:
            query += " and estado = ?"
            params.append(estado)
        
        if prioridad:
            query += " and prioridad = ?"
            params.append(prioridad)
        
        query += f" order by fecha_creacion {orden.upper()}"
        
        cursor.execute(query, params)
        tareas = cursor.fetchall()
        
        resultado = []
        for tarea in tareas:
            resultado.append({
                "id": tarea["id"],
                "descripcion": tarea["descripcion"],
                "estado": tarea["estado"],
                "prioridad": tarea["prioridad"],
                "proyecto_id": tarea["proyecto_id"],
                "fecha_creacion": tarea["fecha_creacion"]
            })
        
        return resultado

@app.post("/proyectos/{id}/tareas", status_code=201)
def crear_tarea(id: int, tarea: TareaCreate):
    if not tarea.descripcion or tarea.descripcion.strip() == "":
        raise HTTPException(status_code=400, detail="la descripcion de la tarea no puede estar vacia")
    
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("select id from proyectos where id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=400, detail="el proyecto especificado no existe")
        
        fecha_creacion = datetime.now().isoformat()
        
        cursor.execute(
            """insert into tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
               values (?, ?, ?, ?, ?)""",
            (tarea.descripcion, tarea.estado, tarea.prioridad, id, fecha_creacion)
        )
        conn.commit()
        
        return {
            "id": cursor.lastrowid,
            "descripcion": tarea.descripcion,
            "estado": tarea.estado,
            "prioridad": tarea.prioridad,
            "proyecto_id": id,
            "fecha_creacion": fecha_creacion
        }

@app.put("/tareas/{id}")
def modificar_tarea(id: int, tarea: TareaUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("select * from tareas where id = ?", (id,))
        tarea_actual = cursor.fetchone()
        
        if not tarea_actual:
            raise HTTPException(status_code=404, detail="tarea no encontrada")
        
        if tarea.proyecto_id:
            cursor.execute("select id from proyectos where id = ?", (tarea.proyecto_id,))
            if not cursor.fetchone():
                raise HTTPException(status_code=400, detail="el proyecto especificado no existe")
        
        if tarea.descripcion is not None and not tarea.descripcion.strip():
            raise HTTPException(status_code=400, detail="la descripcion de la tarea no puede estar vacia")
        
        descripcion_final = tarea.descripcion if tarea.descripcion else tarea_actual["descripcion"]
        estado_final = tarea.estado if tarea.estado else tarea_actual["estado"]
        prioridad_final = tarea.prioridad if tarea.prioridad else tarea_actual["prioridad"]
        proyecto_id_final = tarea.proyecto_id if tarea.proyecto_id else tarea_actual["proyecto_id"]
        
        cursor.execute(
            """update tareas 
               set descripcion = ?, estado = ?, prioridad = ?, proyecto_id = ?
               where id = ?""",
            (descripcion_final, estado_final, prioridad_final, proyecto_id_final, id)
        )
        conn.commit()
        
        return {
            "id": id,
            "descripcion": descripcion_final,
            "estado": estado_final,
            "prioridad": prioridad_final,
            "proyecto_id": proyecto_id_final,
            "fecha_creacion": tarea_actual["fecha_creacion"]
        }

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("select id from tareas where id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="tarea no encontrada")
        
        cursor.execute("delete from tareas where id = ?", (id,))
        conn.commit()
        
        return {"mensaje": "tarea eliminada exitosamente"}

@app.get("/proyectos/{id}/resumen")
def resumen_proyecto(id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("select * from proyectos where id = ?", (id,))
        proyecto = cursor.fetchone()
        
        if not proyecto:
            raise HTTPException(status_code=404, detail="proyecto no encontrado")
        
        cursor.execute(
            "select count(*) as total from tareas where proyecto_id = ?",
            (id,)
        )
        total_tareas = cursor.fetchone()["total"]
        
        cursor.execute(
            """select estado, count(*) as cantidad 
               from tareas 
               where proyecto_id = ? 
               group by estado""",
            (id,)
        )
        por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
        for row in cursor.fetchall():
            por_estado[row["estado"]] = row["cantidad"]
        
        cursor.execute(
            """select prioridad, count(*) as cantidad 
               from tareas 
               where proyecto_id = ? 
               group by prioridad""",
            (id,)
        )
        por_prioridad = {"baja": 0, "media": 0, "alta": 0}
        for row in cursor.fetchall():
            por_prioridad[row["prioridad"]] = row["cantidad"]
        
        return {
            "proyecto_id": id,
            "proyecto_nombre": proyecto["nombre"],
            "total_tareas": total_tareas,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }

@app.get("/resumen")
def resumen_general():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("select count(*) as total from proyectos")
        total_proyectos = cursor.fetchone()["total"]
        
        cursor.execute("select count(*) as total from tareas")
        total_tareas = cursor.fetchone()["total"]
        
        cursor.execute(
            "select estado, count(*) as cantidad from tareas group by estado"
        )
        tareas_por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
        for row in cursor.fetchall():
            tareas_por_estado[row["estado"]] = row["cantidad"]
        
        cursor.execute(
            """select p.id, p.nombre, count(t.id) as cantidad_tareas
               from proyectos p
               left join tareas t on p.id = t.proyecto_id
               group by p.id
               order by cantidad_tareas desc
               limit 1"""
        )
        proyecto_mas_tareas = cursor.fetchone()
        
        proyecto_con_mas_tareas = None
        if proyecto_mas_tareas:
            proyecto_con_mas_tareas = {
                "id": proyecto_mas_tareas["id"],
                "nombre": proyecto_mas_tareas["nombre"],
                "cantidad_tareas": proyecto_mas_tareas["cantidad_tareas"]
            }
        
        return {
            "total_proyectos": total_proyectos,
            "total_tareas": total_tareas,
            "tareas_por_estado": tareas_por_estado,
            "proyecto_con_mas_tareas": proyecto_con_mas_tareas
        }

@app.get("/")
def root():
    return {
        "mensaje": "api de gestion de proyectos y tareas",
        "version": "1.0",
        "endpoints": {
            "proyectos": "/proyectos",
            "tareas": "/tareas",
            "resumen": "/resumen"
        }
    }