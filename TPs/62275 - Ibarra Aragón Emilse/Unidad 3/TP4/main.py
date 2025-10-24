from fastapi import FastAPI, HTTPException, Query
from typing import Optional
import database as db
from models import (
    ProyectoCreate, ProyectoUpdate, ProyectoResponse, ProyectoConTareas,
    TareaCreate, TareaUpdate, TareaResponse,
    MensajeRespuesta, MensajeEliminacionProyecto,
    ResumenProyecto, ResumenGeneral,
    EstadoTarea, PrioridadTarea
)

# Exportar para los tests
DB_NAME = db.DB_NAME
init_db = db.init_db

app = FastAPI(
    title="API de Gestión de Proyectos y Tareas",
    description="API para gestionar proyectos y sus tareas asociadas con persistencia en SQLite",
    version="4.0"
)

# Inicializar base de datos al iniciar la aplicación
init_db()

# ============== ENDPOINTS RAÍZ ==============

@app.get("/")
def raiz():
    """Endpoint raíz con información de la API"""
    return {
        "nombre": "API de Gestión de Proyectos y Tareas",
        "version": "4.0",
        "descripcion": "API con relaciones entre tablas y filtros avanzados",
        "endpoints_proyectos": [
            "GET /proyectos - Listar proyectos",
            "GET /proyectos/{id} - Obtener proyecto específico",
            "POST /proyectos - Crear proyecto",
            "PUT /proyectos/{id} - Actualizar proyecto",
            "DELETE /proyectos/{id} - Eliminar proyecto",
            "GET /proyectos/{id}/tareas - Listar tareas del proyecto",
            "POST /proyectos/{id}/tareas - Crear tarea en proyecto",
            "GET /proyectos/{id}/resumen - Resumen del proyecto"
        ],
        "endpoints_tareas": [
            "GET /tareas - Listar todas las tareas",
            "PUT /tareas/{id} - Actualizar tarea",
            "DELETE /tareas/{id} - Eliminar tarea"
        ],
        "endpoints_resumen": [
            "GET /resumen - Resumen general de la aplicación"
        ]
    }

# ============== CRUD DE PROYECTOS ==============

@app.get("/proyectos", response_model=list[ProyectoResponse])
def listar_proyectos(nombre: Optional[str] = Query(None)):
    """
    Lista todos los proyectos.
    Query params opcionales:
    - nombre: Filtra proyectos que contengan este texto
    """
    proyectos = db.obtener_todos_proyectos(nombre_filtro=nombre)
    return proyectos

@app.get("/proyectos/{id}", response_model=ProyectoConTareas)
def obtener_proyecto(id: int):
    """Obtiene un proyecto específico con contador de tareas"""
    proyecto = db.obtener_proyecto_por_id(id)
    
    if not proyecto:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Proyecto con id {id} no encontrado"}
        )
    
    return proyecto

@app.post("/proyectos", response_model=ProyectoResponse, status_code=201)
def crear_proyecto(proyecto: ProyectoCreate):
    """Crea un nuevo proyecto"""
    # Verificar si el nombre ya existe
    if db.verificar_nombre_proyecto_duplicado(proyecto.nombre):
        raise HTTPException(
            status_code=409,
            detail={"error": f"Ya existe un proyecto con el nombre '{proyecto.nombre}'"}
        )
    
    nuevo_proyecto = db.crear_proyecto(
        nombre=proyecto.nombre,
        descripcion=proyecto.descripcion
    )
    
    return nuevo_proyecto

@app.put("/proyectos/{id}", response_model=ProyectoResponse)
def actualizar_proyecto(id: int, proyecto: ProyectoUpdate):
    """Actualiza un proyecto existente"""
    # Verificar si el proyecto existe
    proyecto_actual = db.obtener_proyecto_por_id(id)
    if not proyecto_actual:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Proyecto con id {id} no encontrado"}
        )
    
    # Si se está actualizando el nombre, verificar que no exista otro con ese nombre
    if proyecto.nombre and db.verificar_nombre_proyecto_duplicado(proyecto.nombre, excluir_id=id):
        raise HTTPException(
            status_code=409,
            detail={"error": f"Ya existe otro proyecto con el nombre '{proyecto.nombre}'"}
        )
    
    proyecto_actualizado = db.actualizar_proyecto(
        proyecto_id=id,
        nombre=proyecto.nombre,
        descripcion=proyecto.descripcion
    )
    
    return proyecto_actualizado

@app.delete("/proyectos/{id}", response_model=MensajeEliminacionProyecto)
def eliminar_proyecto(id: int):
    """Elimina un proyecto y todas sus tareas asociadas (CASCADE)"""
    tareas_eliminadas = db.eliminar_proyecto(id)
    
    if tareas_eliminadas is None:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Proyecto con id {id} no encontrado"}
        )
    
    return {
        "mensaje": f"Proyecto {id} eliminado correctamente",
        "tareas_eliminadas": tareas_eliminadas
    }

# ============== TAREAS ASOCIADAS A PROYECTOS ==============

@app.get("/proyectos/{id}/tareas", response_model=list[TareaResponse])
def listar_tareas_proyecto(
    id: int,
    estado: Optional[EstadoTarea] = Query(None),
    prioridad: Optional[PrioridadTarea] = Query(None),
    orden: Optional[str] = Query(None)
):
    """
    Lista todas las tareas de un proyecto específico.
    Query params opcionales:
    - estado: Filtra por estado
    - prioridad: Filtra por prioridad
    - orden: Ordena por fecha (asc o desc)
    """
    # Verificar que el proyecto existe
    if not db.verificar_proyecto_existe(id):
        raise HTTPException(
            status_code=404,
            detail={"error": f"Proyecto con id {id} no encontrado"}
        )
    
    tareas = db.obtener_tareas_por_proyecto(
        proyecto_id=id,
        estado=estado,
        prioridad=prioridad,
        orden=orden
    )
    
    return tareas

@app.post("/proyectos/{id}/tareas", response_model=TareaResponse, status_code=201)
def crear_tarea_en_proyecto(id: int, tarea: TareaCreate):
    """Crea una nueva tarea dentro de un proyecto"""
    # Verificar que el proyecto existe
    if not db.verificar_proyecto_existe(id):
        raise HTTPException(
            status_code=400,
            detail={"error": f"El proyecto con id {id} no existe"}
        )
    
    nueva_tarea = db.crear_tarea(
        descripcion=tarea.descripcion,
        proyecto_id=id,
        estado=tarea.estado,
        prioridad=tarea.prioridad
    )
    
    return nueva_tarea

@app.get("/tareas", response_model=list[TareaResponse])
def listar_todas_tareas(
    estado: Optional[EstadoTarea] = Query(None),
    prioridad: Optional[PrioridadTarea] = Query(None),
    proyecto_id: Optional[int] = Query(None),
    orden: Optional[str] = Query(None)
):
    """
    Lista todas las tareas de todos los proyectos.
    Query params opcionales:
    - estado: Filtra por estado
    - prioridad: Filtra por prioridad
    - proyecto_id: Filtra por proyecto
    - orden: Ordena por fecha (asc o desc)
    """
    tareas = db.obtener_todas_tareas(
        estado=estado,
        prioridad=prioridad,
        proyecto_id=proyecto_id,
        orden=orden
    )
    
    return tareas

@app.put("/tareas/{id}", response_model=TareaResponse)
def actualizar_tarea(id: int, tarea: TareaUpdate):
    """Actualiza una tarea existente (puede cambiar de proyecto)"""
    # Verificar que la tarea existe
    tarea_actual = db.obtener_tarea_por_id(id)
    if not tarea_actual:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Tarea con id {id} no encontrada"}
        )
    
    # Si se está cambiando de proyecto, verificar que el nuevo proyecto existe
    if tarea.proyecto_id is not None and tarea.proyecto_id != tarea_actual["proyecto_id"]:
        if not db.verificar_proyecto_existe(tarea.proyecto_id):
            raise HTTPException(
                status_code=400,
                detail={"error": f"El proyecto con id {tarea.proyecto_id} no existe"}
            )
    
    tarea_actualizada = db.actualizar_tarea(
        tarea_id=id,
        descripcion=tarea.descripcion,
        estado=tarea.estado,
        prioridad=tarea.prioridad,
        proyecto_id=tarea.proyecto_id
    )
    
    return tarea_actualizada

@app.delete("/tareas/{id}", response_model=MensajeRespuesta)
def eliminar_tarea(id: int):
    """Elimina una tarea específica"""
    if not db.eliminar_tarea(id):
        raise HTTPException(
            status_code=404,
            detail={"error": f"Tarea con id {id} no encontrada"}
        )
    
    return {"mensaje": f"Tarea {id} eliminada correctamente"}

# ============== RESUMEN Y ESTADÍSTICAS ==============

@app.get("/proyectos/{id}/resumen", response_model=ResumenProyecto)
def obtener_resumen_proyecto(id: int):
    """Obtiene resumen estadístico de un proyecto específico"""
    resumen = db.obtener_resumen_proyecto(id)
    
    if not resumen:
        raise HTTPException(
            status_code=404,
            detail={"error": f"Proyecto con id {id} no encontrado"}
        )
    
    return resumen

@app.get("/resumen", response_model=ResumenGeneral)
def obtener_resumen_general():
    """Obtiene resumen general de toda la aplicación"""
    resumen = db.obtener_resumen_general()
    return resumen