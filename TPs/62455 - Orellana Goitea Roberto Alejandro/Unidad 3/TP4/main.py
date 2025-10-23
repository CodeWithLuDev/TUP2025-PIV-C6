"""
API REST para gestión de Proyectos y Tareas con persistencia en SQLite.
Trabajo Práctico N°4 - Relaciones entre Tablas y Filtros Avanzados.
"""

from fastapi import FastAPI, HTTPException, Query, status
from typing import List, Optional
from datetime import datetime
from contextlib import asynccontextmanager

# Importar modelos y funciones de base de datos
from models import (
    EstadoTarea, PrioridadTarea,
    ProyectoCreate, ProyectoUpdate, Proyecto,
    TareaCreate, TareaUpdate, Tarea,
    ResumenProyecto, ResumenGeneral
)
from database import (
    init_db, get_db, row_to_dict,
    proyecto_exists, nombre_proyecto_duplicado, contar_tareas_proyecto,
    DB_NAME  # Exportar para tests
)

# ==================== LIFESPAN Y APP ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Inicializa la base de datos al arrancar la aplicación"""
    init_db()
    yield


app = FastAPI(
    title="API de Proyectos y Tareas",
    version="4.0",
    description="API REST para gestión de proyectos y tareas con relaciones entre tablas",
    lifespan=lifespan
)


# ==================== ENDPOINT RAÍZ ====================

@app.get("/")
def root():
    """Información básica de la API"""
    return {
        "nombre": "API de Proyectos y Tareas",
        "version": "4.0",
        "descripcion": "API REST con relaciones 1:N entre proyectos y tareas",
        "endpoints": {
            "proyectos": {
                "GET /proyectos": "Listar todos los proyectos",
                "GET /proyectos/{id}": "Obtener un proyecto específico",
                "POST /proyectos": "Crear nuevo proyecto",
                "PUT /proyectos/{id}": "Actualizar proyecto",
                "DELETE /proyectos/{id}": "Eliminar proyecto y sus tareas",
                "GET /proyectos/{id}/tareas": "Listar tareas de un proyecto",
                "POST /proyectos/{id}/tareas": "Crear tarea en un proyecto",
                "GET /proyectos/{id}/resumen": "Resumen de un proyecto"
            },
            "tareas": {
                "GET /tareas": "Listar todas las tareas (con filtros)",
                "PUT /tareas/{id}": "Actualizar tarea",
                "DELETE /tareas/{id}": "Eliminar tarea"
            },
            "resumen": {
                "GET /resumen": "Resumen general de la aplicación"
            }
        }
    }

# ==================== ENDPOINTS DE PROYECTOS ====================

@app.get("/proyectos", response_model=List[Proyecto])
def get_proyectos(
    nombre: Optional[str] = Query(None, description="Buscar proyectos por nombre (parcial)")
):
    """
    Lista todos los proyectos con filtro opcional por nombre.
    Incluye el contador de tareas de cada proyecto.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        if nombre:
            # Búsqueda parcial insensible a mayúsculas
            cursor.execute(
                "SELECT * FROM proyectos WHERE nombre LIKE ? ORDER BY fecha_creacion DESC",
                (f"%{nombre}%",)
            )
        else:
            cursor.execute("SELECT * FROM proyectos ORDER BY fecha_creacion DESC")
        
        rows = cursor.fetchall()
        proyectos = []
        
        for row in rows:
            proyecto_dict = row_to_dict(row)
            # Agregar contador de tareas
            proyecto_dict["total_tareas"] = contar_tareas_proyecto(conn, row["id"])
            proyectos.append(proyecto_dict)
        
        return proyectos


@app.get("/proyectos/{id}", response_model=Proyecto)
def get_proyecto(id: int):
    """
    Obtiene un proyecto específico por ID.
    Incluye el contador de tareas asociadas.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
        row = cursor.fetchone()
        
        if not row:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"El proyecto con ID {id} no existe"}
            )
        
        proyecto_dict = row_to_dict(row)
        proyecto_dict["total_tareas"] = contar_tareas_proyecto(conn, id)
        
        return proyecto_dict


@app.post("/proyectos", response_model=Proyecto, status_code=status.HTTP_201_CREATED)
def create_proyecto(proyecto: ProyectoCreate):
    """
    Crea un nuevo proyecto.
    - El nombre no puede estar vacío y debe ser único.
    - La descripción es opcional.
    """
    # Validar que el nombre no esté vacío
    if not proyecto.nombre.strip():
        raise HTTPException(
            status_code=422,
            detail={"error": "El nombre del proyecto no puede estar vacío"}
        )
    
    with get_db() as conn:
        # Verificar nombre duplicado
        if nombre_proyecto_duplicado(conn, proyecto.nombre):
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail={"error": f"Ya existe un proyecto con el nombre '{proyecto.nombre}'"}
            )
        
        cursor = conn.cursor()
        fecha_creacion = datetime.now().isoformat()
        
        cursor.execute(
            """
            INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
            VALUES (?, ?, ?)
            """,
            (proyecto.nombre.strip(), proyecto.descripcion, fecha_creacion)
        )
        conn.commit()
        
        proyecto_id = cursor.lastrowid
        
        # Recuperar el proyecto creado
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
        row = cursor.fetchone()
        
        proyecto_dict = row_to_dict(row)
        proyecto_dict["total_tareas"] = 0
        
        return proyecto_dict


@app.put("/proyectos/{id}", response_model=Proyecto)
def update_proyecto(id: int, proyecto_update: ProyectoUpdate):
    """
    Actualiza un proyecto existente.
    - Puede actualizar nombre y/o descripción.
    - El nombre debe ser único si se cambia.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que el proyecto existe
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
        proyecto_actual = cursor.fetchone()
        
        if not proyecto_actual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"El proyecto con ID {id} no existe"}
            )
        
        # Construir actualización dinámica
        updates = []
        params = []
        
        if proyecto_update.nombre is not None:
            nombre_limpio = proyecto_update.nombre.strip()
            if not nombre_limpio:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "El nombre del proyecto no puede estar vacío"}
                )
            
            # Verificar nombre duplicado
            if nombre_proyecto_duplicado(conn, nombre_limpio, excluir_id=id):
                raise HTTPException(
                    status_code=status.HTTP_409_CONFLICT,
                    detail={"error": f"Ya existe otro proyecto con el nombre '{nombre_limpio}'"}
                )
            
            updates.append("nombre = ?")
            params.append(nombre_limpio)
        
        if proyecto_update.descripcion is not None:
            updates.append("descripcion = ?")
            params.append(proyecto_update.descripcion)
        
        if not updates:
            # No hay nada que actualizar
            proyecto_dict = row_to_dict(proyecto_actual)
            proyecto_dict["total_tareas"] = contar_tareas_proyecto(conn, id)
            return proyecto_dict
        
        params.append(id)
        query = f"UPDATE proyectos SET {', '.join(updates)} WHERE id = ?"
        
        cursor.execute(query, params)
        conn.commit()
        
        # Recuperar proyecto actualizado
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
        row = cursor.fetchone()
        
        proyecto_dict = row_to_dict(row)
        proyecto_dict["total_tareas"] = contar_tareas_proyecto(conn, id)
        
        return proyecto_dict


@app.delete("/proyectos/{id}")
def delete_proyecto(id: int):
    """
    Elimina un proyecto y todas sus tareas asociadas (CASCADE).
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que el proyecto existe
        cursor.execute("SELECT * FROM proyectos WHERE id = ?", (id,))
        proyecto = cursor.fetchone()
        
        if not proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"El proyecto con ID {id} no existe"}
            )
        
        # Contar tareas antes de eliminar
        cantidad_tareas = contar_tareas_proyecto(conn, id)
        
        # Eliminar proyecto (las tareas se eliminan automáticamente por CASCADE)
        cursor.execute("DELETE FROM proyectos WHERE id = ?", (id,))
        conn.commit()
        
        return {
            "mensaje": f"Proyecto '{proyecto['nombre']}' eliminado exitosamente",
            "tareas_eliminadas": cantidad_tareas
        }


# ==================== ENDPOINTS DE TAREAS POR PROYECTO ====================

@app.get("/proyectos/{id}/tareas", response_model=List[Tarea])
def get_tareas_proyecto(
    id: int,
    estado: Optional[EstadoTarea] = Query(None, description="Filtrar por estado"),
    prioridad: Optional[PrioridadTarea] = Query(None, description="Filtrar por prioridad"),
    orden: Optional[str] = Query(None, pattern="^(asc|desc)$", description="Ordenar por fecha (asc/desc)")
):
    """
    Lista todas las tareas de un proyecto específico con filtros opcionales.
    """
    with get_db() as conn:
        # Verificar que el proyecto existe
        if not proyecto_exists(conn, id):
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"El proyecto con ID {id} no existe"}
            )
        
        cursor = conn.cursor()
        
        # Construir query con JOIN para incluir nombre del proyecto
        query = """
            SELECT t.*, p.nombre as proyecto_nombre 
            FROM tareas t 
            JOIN proyectos p ON t.proyecto_id = p.id 
            WHERE t.proyecto_id = ?
        """
        params = [id]
        
        if estado:
            query += " AND t.estado = ?"
            params.append(estado.value)
        
        if prioridad:
            query += " AND t.prioridad = ?"
            params.append(prioridad.value)
        
        # Ordenamiento
        if orden:
            query += f" ORDER BY t.fecha_creacion {'ASC' if orden == 'asc' else 'DESC'}"
        else:
            query += " ORDER BY t.id ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [row_to_dict(row) for row in rows]


@app.post("/proyectos/{id}/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED)
def create_tarea_en_proyecto(id: int, tarea: TareaCreate):
    """
    Crea una nueva tarea dentro de un proyecto específico.
    """
    # Validar descripción
    if not tarea.descripcion.strip():
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={"error": "La descripción de la tarea no puede estar vacía"}
        )
    
    with get_db() as conn:
        # Verificar que el proyecto existe
        if not proyecto_exists(conn, id):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail={"error": f"El proyecto con ID {id} no existe"}
            )
        
        cursor = conn.cursor()
        fecha_creacion = datetime.now().isoformat()
        
        cursor.execute(
            """
            INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
            VALUES (?, ?, ?, ?, ?)
            """,
            (tarea.descripcion.strip(), tarea.estado.value, tarea.prioridad.value, id, fecha_creacion)
        )
        conn.commit()
        
        tarea_id = cursor.lastrowid
        
        # Recuperar la tarea creada con JOIN
        cursor.execute(
            """
            SELECT t.*, p.nombre as proyecto_nombre 
            FROM tareas t 
            JOIN proyectos p ON t.proyecto_id = p.id 
            WHERE t.id = ?
            """,
            (tarea_id,)
        )
        row = cursor.fetchone()
        
        return row_to_dict(row)


# ==================== ENDPOINTS DE TAREAS GENERALES ====================

@app.get("/tareas", response_model=List[Tarea])
def get_tareas(
    estado: Optional[EstadoTarea] = Query(None, description="Filtrar por estado"),
    prioridad: Optional[PrioridadTarea] = Query(None, description="Filtrar por prioridad"),
    proyecto_id: Optional[int] = Query(None, description="Filtrar por proyecto"),
    orden: Optional[str] = Query(None, pattern="^(asc|desc)$", description="Ordenar por fecha (asc/desc)")
):
    """
    Lista todas las tareas de todos los proyectos con filtros opcionales.
    Permite combinar múltiples filtros simultáneamente.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Query con JOIN para incluir nombre del proyecto
        query = """
            SELECT t.*, p.nombre as proyecto_nombre 
            FROM tareas t 
            JOIN proyectos p ON t.proyecto_id = p.id 
            WHERE 1=1
        """
        params = []
        
        if estado:
            query += " AND t.estado = ?"
            params.append(estado.value)
        
        if prioridad:
            query += " AND t.prioridad = ?"
            params.append(prioridad.value)
        
        if proyecto_id:
            # Verificar que el proyecto existe
            if not proyecto_exists(conn, proyecto_id):
                raise HTTPException(
                    status_code=status.HTTP_404_NOT_FOUND,
                    detail={"error": f"El proyecto con ID {proyecto_id} no existe"}
                )
            query += " AND t.proyecto_id = ?"
            params.append(proyecto_id)
        
        # Ordenamiento
        if orden:
            query += f" ORDER BY t.fecha_creacion {'ASC' if orden == 'asc' else 'DESC'}"
        else:
            query += " ORDER BY t.id ASC"
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [row_to_dict(row) for row in rows]


@app.put("/tareas/{id}", response_model=Tarea)
def update_tarea(id: int, tarea_update: TareaUpdate):
    """
    Actualiza una tarea existente.
    Puede cambiar descripción, estado, prioridad y/o proyecto.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que la tarea existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea_actual = cursor.fetchone()
        
        if not tarea_actual:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"La tarea con ID {id} no existe"}
            )
        
        # Construir actualización dinámica
        updates = []
        params = []
        
        if tarea_update.descripcion is not None:
            descripcion_limpia = tarea_update.descripcion.strip()
            if not descripcion_limpia:
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": "La descripción de la tarea no puede estar vacía"}
                )
            updates.append("descripcion = ?")
            params.append(descripcion_limpia)
        
        if tarea_update.estado is not None:
            updates.append("estado = ?")
            params.append(tarea_update.estado.value)
        
        if tarea_update.prioridad is not None:
            updates.append("prioridad = ?")
            params.append(tarea_update.prioridad.value)
        
        if tarea_update.proyecto_id is not None:
            # Verificar que el nuevo proyecto existe
            if not proyecto_exists(conn, tarea_update.proyecto_id):
                raise HTTPException(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    detail={"error": f"El proyecto con ID {tarea_update.proyecto_id} no existe"}
                )
            updates.append("proyecto_id = ?")
            params.append(tarea_update.proyecto_id)
        
        if not updates:
            # No hay nada que actualizar
            cursor.execute(
                """
                SELECT t.*, p.nombre as proyecto_nombre 
                FROM tareas t 
                JOIN proyectos p ON t.proyecto_id = p.id 
                WHERE t.id = ?
                """,
                (id,)
            )
            row = cursor.fetchone()
            return row_to_dict(row)
        
        params.append(id)
        query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        
        cursor.execute(query, params)
        conn.commit()
        
        # Recuperar tarea actualizada con JOIN
        cursor.execute(
            """
            SELECT t.*, p.nombre as proyecto_nombre 
            FROM tareas t 
            JOIN proyectos p ON t.proyecto_id = p.id 
            WHERE t.id = ?
            """,
            (id,)
        )
        row = cursor.fetchone()
        
        return row_to_dict(row)


@app.delete("/tareas/{id}")
def delete_tarea(id: int):
    """
    Elimina una tarea específica.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que la tarea existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea = cursor.fetchone()
        
        if not tarea:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"La tarea con ID {id} no existe"}
            )
        
        cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
        conn.commit()
        
        return {"mensaje": "Tarea eliminada exitosamente"}


# ==================== ENDPOINTS DE RESUMEN ====================

@app.get("/proyectos/{id}/resumen", response_model=ResumenProyecto)
def get_resumen_proyecto(id: int):
    """
    Devuelve un resumen completo de un proyecto:
    - Total de tareas
    - Distribución por estado
    - Distribución por prioridad
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que el proyecto existe
        cursor.execute("SELECT nombre FROM proyectos WHERE id = ?", (id,))
        proyecto = cursor.fetchone()
        
        if not proyecto:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail={"error": f"El proyecto con ID {id} no existe"}
            )
        
        # Total de tareas
        total_tareas = contar_tareas_proyecto(conn, id)
        
        # Por estado
        por_estado = {
            "pendiente": 0,
            "en_progreso": 0,
            "completada": 0
        }
        cursor.execute(
            "SELECT estado, COUNT(*) as total FROM tareas WHERE proyecto_id = ? GROUP BY estado",
            (id,)
        )
        for row in cursor.fetchall():
            por_estado[row["estado"]] = row["total"]
        
        # Por prioridad
        por_prioridad = {
            "baja": 0,
            "media": 0,
            "alta": 0
        }
        cursor.execute(
            "SELECT prioridad, COUNT(*) as total FROM tareas WHERE proyecto_id = ? GROUP BY prioridad",
            (id,)
        )
        for row in cursor.fetchall():
            por_prioridad[row["prioridad"]] = row["total"]
        
        return {
            "proyecto_id": id,
            "proyecto_nombre": proyecto["nombre"],
            "total_tareas": total_tareas,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }


@app.get("/resumen", response_model=ResumenGeneral)
def get_resumen_general():
    """
    Devuelve un resumen general de toda la aplicación:
    - Total de proyectos
    - Total de tareas
    - Distribución de tareas por estado
    - Proyecto con más tareas
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Total de proyectos
        cursor.execute("SELECT COUNT(*) as total FROM proyectos")
        total_proyectos = cursor.fetchone()["total"]
        
        # Total de tareas
        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total_tareas = cursor.fetchone()["total"]
        
        # Tareas por estado
        tareas_por_estado = {
            "pendiente": 0,
            "en_progreso": 0,
            "completada": 0
        }
        cursor.execute("SELECT estado, COUNT(*) as total FROM tareas GROUP BY estado")
        for row in cursor.fetchall():
            tareas_por_estado[row["estado"]] = row["total"]
        
        # Proyecto con más tareas
        proyecto_con_mas_tareas = None
        cursor.execute("""
            SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
            FROM proyectos p
            LEFT JOIN tareas t ON p.id = t.proyecto_id
            GROUP BY p.id, p.nombre
            ORDER BY cantidad_tareas DESC
            LIMIT 1
        """)
        row = cursor.fetchone()
        
        if row and row["cantidad_tareas"] > 0:
            proyecto_con_mas_tareas = {
                "id": row["id"],
                "nombre": row["nombre"],
                "cantidad_tareas": row["cantidad_tareas"]
            }
        
        return {
            "total_proyectos": total_proyectos,
            "total_tareas": total_tareas,
            "tareas_por_estado": tareas_por_estado,
            "proyecto_con_mas_tareas": proyecto_con_mas_tareas
        }


# ==================== PUNTO DE ENTRADA ====================

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
