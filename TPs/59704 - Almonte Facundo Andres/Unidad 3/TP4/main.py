from fastapi import FastAPI, HTTPException, status
from typing import Optional, List
from datetime import datetime
import sqlite3
from contextlib import contextmanager

# Importar modelos desde models.py
from models import (
    ProyectoCreate, ProyectoUpdate, ProyectoResponse,
    TareaCreate, TareaUpdate, TareaResponse
)

# Configuración
DB_NAME = "proyectos.db"
app = FastAPI(title="Sistema de Gestión de Proyectos y Tareas")

# ============== CONEXIÓN A BASE DE DATOS ==============

@contextmanager
def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()

def init_db():
    """Inicializa la base de datos con las tablas necesarias"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Tabla proyectos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proyectos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT,
                fecha_creacion TEXT NOT NULL
            )
        """)
        
        # Tabla tareas
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL DEFAULT 'pendiente',
                prioridad TEXT NOT NULL DEFAULT 'media',
                fecha_creacion TEXT NOT NULL,
                proyecto_id INTEGER NOT NULL,
                FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
            )
        """)

# Inicializar BD al arrancar
init_db()

# ============== ENDPOINTS DE PROYECTOS ==============

@app.post("/proyectos", response_model=ProyectoResponse, status_code=status.HTTP_201_CREATED)
def crear_proyecto(proyecto: ProyectoCreate):
    """Crea un nuevo proyecto"""
    try:
        with get_db() as conn:
            cursor = conn.cursor()
            fecha_creacion = datetime.now().isoformat()
            
            cursor.execute("""
                INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
                VALUES (?, ?, ?)
            """, (proyecto.nombre, proyecto.descripcion, fecha_creacion))
            
            proyecto_id = cursor.lastrowid
            
            return ProyectoResponse(
                id=proyecto_id,
                nombre=proyecto.nombre,
                descripcion=proyecto.descripcion,
                fecha_creacion=fecha_creacion
            )
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Ya existe un proyecto con ese nombre"
        )

@app.get("/proyectos", response_model=List[ProyectoResponse])
def listar_proyectos(nombre: Optional[str] = None):
    """Lista todos los proyectos, con filtro opcional por nombre"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        if nombre:
            cursor.execute("""
                SELECT * FROM proyectos WHERE nombre LIKE ?
            """, (f"%{nombre}%",))
        else:
            cursor.execute("SELECT * FROM proyectos")
        
        proyectos = cursor.fetchall()
        
        return [
            ProyectoResponse(
                id=p['id'],
                nombre=p['nombre'],
                descripcion=p['descripcion'],
                fecha_creacion=p['fecha_creacion']
            )
            for p in proyectos
        ]

@app.get("/proyectos/{proyecto_id}", response_model=ProyectoResponse)
def obtener_proyecto(proyecto_id: int):
    """Obtiene un proyecto específico con contador de tareas"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        proyecto = cursor.fetchone()
        
        if not proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado"
            )
        
        # Contar tareas
        cursor.execute("""
            SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?
        """, (proyecto_id,))
        total_tareas = cursor.fetchone()['total']
        
        return ProyectoResponse(
            id=proyecto['id'],
            nombre=proyecto['nombre'],
            descripcion=proyecto['descripcion'],
            fecha_creacion=proyecto['fecha_creacion'],
            total_tareas=total_tareas
        )

@app.put("/proyectos/{proyecto_id}", response_model=ProyectoResponse)
def actualizar_proyecto(proyecto_id: int, proyecto: ProyectoUpdate):
    """Actualiza un proyecto existente"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        proyecto_actual = cursor.fetchone()
        
        if not proyecto_actual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado"
            )
        
        nombre = proyecto.nombre if proyecto.nombre is not None else proyecto_actual['nombre']
        descripcion = proyecto.descripcion if proyecto.descripcion is not None else proyecto_actual['descripcion']
        
        try:
            cursor.execute("""
                UPDATE proyectos SET nombre = ?, descripcion = ? WHERE id = ?
            """, (nombre, descripcion, proyecto_id))
        except sqlite3.IntegrityError:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Ya existe un proyecto con ese nombre"
            )
        
        return ProyectoResponse(
            id=proyecto_id,
            nombre=nombre,
            descripcion=descripcion,
            fecha_creacion=proyecto_actual['fecha_creacion']
        )

@app.delete("/proyectos/{proyecto_id}")
def eliminar_proyecto(proyecto_id: int):
    """Elimina un proyecto y sus tareas asociadas (CASCADE)"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado"
            )
        
        # Contar tareas antes de eliminar
        cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
        tareas_eliminadas = cursor.fetchone()['total']
        
        # Eliminar proyecto (las tareas se eliminan por CASCADE)
        cursor.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
        
        return {
            "mensaje": "Proyecto eliminado exitosamente",
            "tareas_eliminadas": tareas_eliminadas
        }

# ============== ENDPOINTS DE TAREAS ==============

@app.post("/proyectos/{proyecto_id}/tareas", response_model=TareaResponse, status_code=status.HTTP_201_CREATED)
def crear_tarea(proyecto_id: int, tarea: TareaCreate):
    """Crea una tarea asociada a un proyecto"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que el proyecto existe
        cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="El proyecto especificado no existe"
            )
        
        fecha_creacion = datetime.now().isoformat()
        
        cursor.execute("""
            INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion, proyecto_id)
            VALUES (?, ?, ?, ?, ?)
        """, (tarea.descripcion, tarea.estado, tarea.prioridad, fecha_creacion, proyecto_id))
        
        tarea_id = cursor.lastrowid
        
        return TareaResponse(
            id=tarea_id,
            descripcion=tarea.descripcion,
            estado=tarea.estado,
            prioridad=tarea.prioridad,
            fecha_creacion=fecha_creacion,
            proyecto_id=proyecto_id
        )

@app.get("/proyectos/{proyecto_id}/tareas", response_model=List[TareaResponse])
def listar_tareas_proyecto(proyecto_id: int):
    """Lista todas las tareas de un proyecto específico"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que el proyecto existe
        cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado"
            )
        
        cursor.execute("""
            SELECT * FROM tareas WHERE proyecto_id = ? ORDER BY fecha_creacion
        """, (proyecto_id,))
        
        tareas = cursor.fetchall()
        
        return [
            TareaResponse(
                id=t['id'],
                descripcion=t['descripcion'],
                estado=t['estado'],
                prioridad=t['prioridad'],
                fecha_creacion=t['fecha_creacion'],
                proyecto_id=t['proyecto_id']
            )
            for t in tareas
        ]

@app.get("/tareas", response_model=List[TareaResponse])
def listar_tareas(
    estado: Optional[str] = None,
    prioridad: Optional[str] = None,
    proyecto_id: Optional[int] = None,
    orden: Optional[str] = None
):
    """Lista todas las tareas con filtros opcionales"""
    with get_db() as conn:
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
        
        # Ordenamiento
        if orden == "asc":
            query += " ORDER BY fecha_creacion ASC"
        elif orden == "desc":
            query += " ORDER BY fecha_creacion DESC"
        else:
            query += " ORDER BY fecha_creacion"
        
        cursor.execute(query, params)
        tareas = cursor.fetchall()
        
        return [
            TareaResponse(
                id=t['id'],
                descripcion=t['descripcion'],
                estado=t['estado'],
                prioridad=t['prioridad'],
                fecha_creacion=t['fecha_creacion'],
                proyecto_id=t['proyecto_id']
            )
            for t in tareas
        ]

@app.put("/tareas/{tarea_id}", response_model=TareaResponse)
def actualizar_tarea(tarea_id: int, tarea: TareaUpdate):
    """Actualiza una tarea existente"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        tarea_actual = cursor.fetchone()
        
        if not tarea_actual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada"
            )
        
        # Si se va a cambiar el proyecto, verificar que existe
        if tarea.proyecto_id is not None:
            cursor.execute("SELECT id FROM proyectos WHERE id = ?", (tarea.proyecto_id,))
            if not cursor.fetchone():
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail="El proyecto especificado no existe"
                )
        
        descripcion = tarea.descripcion if tarea.descripcion is not None else tarea_actual['descripcion']
        estado = tarea.estado if tarea.estado is not None else tarea_actual['estado']
        prioridad = tarea.prioridad if tarea.prioridad is not None else tarea_actual['prioridad']
        proyecto_id = tarea.proyecto_id if tarea.proyecto_id is not None else tarea_actual['proyecto_id']
        
        cursor.execute("""
            UPDATE tareas 
            SET descripcion = ?, estado = ?, prioridad = ?, proyecto_id = ?
            WHERE id = ?
        """, (descripcion, estado, prioridad, proyecto_id, tarea_id))
        
        return TareaResponse(
            id=tarea_id,
            descripcion=descripcion,
            estado=estado,
            prioridad=prioridad,
            fecha_creacion=tarea_actual['fecha_creacion'],
            proyecto_id=proyecto_id
        )

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    """Elimina una tarea específica"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        if not cursor.fetchone():
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Tarea no encontrada"
            )
        
        cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
        
        return {"mensaje": "Tarea eliminada exitosamente"}

# ============== ENDPOINTS DE RESUMEN Y ESTADÍSTICAS ==============

@app.get("/proyectos/{proyecto_id}/resumen")
def resumen_proyecto(proyecto_id: int):
    """Obtiene resumen estadístico de un proyecto"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        proyecto = cursor.fetchone()
        
        if not proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Proyecto no encontrado"
            )
        
        # Total de tareas
        cursor.execute("""
            SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?
        """, (proyecto_id,))
        total_tareas = cursor.fetchone()['total']
        
        # Tareas por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM tareas
            WHERE proyecto_id = ?
            GROUP BY estado
        """, (proyecto_id,))
        
        por_estado = {row['estado']: row['cantidad'] for row in cursor.fetchall()}
        
        # Tareas por prioridad
        cursor.execute("""
            SELECT prioridad, COUNT(*) as cantidad
            FROM tareas
            WHERE proyecto_id = ?
            GROUP BY prioridad
        """, (proyecto_id,))
        
        por_prioridad = {row['prioridad']: row['cantidad'] for row in cursor.fetchall()}
        
        return {
            "proyecto_id": proyecto_id,
            "proyecto_nombre": proyecto['nombre'],
            "total_tareas": total_tareas,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }

@app.get("/resumen")
def resumen_general():
    """Obtiene resumen general de la aplicación"""
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Total proyectos
        cursor.execute("SELECT COUNT(*) as total FROM proyectos")
        total_proyectos = cursor.fetchone()['total']
        
        # Total tareas
        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total_tareas = cursor.fetchone()['total']
        
        # Tareas por estado
        cursor.execute("""
            SELECT estado, COUNT(*) as cantidad
            FROM tareas
            GROUP BY estado
        """)
        tareas_por_estado = {row['estado']: row['cantidad'] for row in cursor.fetchall()}
        
        # Proyecto con más tareas
        cursor.execute("""
            SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            GROUP BY p.id
            ORDER BY cantidad_tareas DESC
            LIMIT 1
        """)
        
        proyecto_row = cursor.fetchone()
        proyecto_con_mas_tareas = None
        
        if proyecto_row and proyecto_row['cantidad_tareas'] > 0:
            proyecto_con_mas_tareas = {
                "id": proyecto_row['id'],
                "nombre": proyecto_row['nombre'],
                "cantidad_tareas": proyecto_row['cantidad_tareas']
            }
        
        return {
            "total_proyectos": total_proyectos,
            "total_tareas": total_tareas,
            "tareas_por_estado": tareas_por_estado,
            "proyecto_con_mas_tareas": proyecto_con_mas_tareas
        }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)