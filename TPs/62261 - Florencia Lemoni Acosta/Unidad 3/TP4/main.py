from fastapi import FastAPI, HTTPException, Query
from contextlib import asynccontextmanager
from typing import Optional
import sqlite3

from models import ProyectoCreate, ProyectoUpdate, TareaCreate, TareaUpdate
from dataBase import (
    DB_NAME,  # Exportar DB_NAME para que test_TP4.py pueda importarlo
    init_db,
    # Funciones de proyectos
    obtener_todos_proyectos,
    obtener_proyecto_por_id,
    crear_proyecto,
    actualizar_proyecto,
    eliminar_proyecto,
    verificar_nombre_proyecto_unico,
    # Funciones de tareas
    obtener_todas_tareas,
    obtener_tareas_por_proyecto,
    obtener_tarea_por_id,
    crear_tarea,
    actualizar_tarea,
    eliminar_tarea,
    # Funciones de resumen
    obtener_resumen_proyecto,
    obtener_resumen_general
)


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    """Gestiona el ciclo de vida de la aplicación"""
    # Código que se ejecuta AL INICIAR el servidor
    print("🚀 Iniciando servidor...")
    init_db()
    print("✅ Base de datos inicializada correctamente")
    print("📦 Tablas creadas: proyectos, tareas")
    
    yield  # Aquí el servidor está corriendo
    
    # Código que se ejecuta AL CERRAR el servidor
    print("👋 Cerrando servidor...")
    print("✅ Servidor cerrado correctamente")


# ==================== APLICACIÓN FASTAPI ====================

app = FastAPI(
    title="API de Proyectos y Tareas",
    description="API RESTful para gestión de proyectos y tareas con relaciones 1:N",
    version="2.0.0 (TP4)",
    lifespan=lifespan
)


# ==================== ENDPOINT RAÍZ ====================

@app.get("/")
def root():
    """Endpoint raíz de bienvenida"""
    return {
        "nombre": "API de Proyectos y Tareas",
        "descripcion": "API RESTful con relaciones entre tablas",
        "version": "2.0.0 (TP4)",
        "documentacion": "/docs",
        "endpoints_principales": {
            "proyectos": [
                "GET /proyectos",
                "GET /proyectos/{id}",
                "POST /proyectos",
                "PUT /proyectos/{id}",
                "DELETE /proyectos/{id}",
                "GET /proyectos/{id}/tareas",
                "POST /proyectos/{id}/tareas",
                "GET /proyectos/{id}/resumen"
            ],
            "tareas": [
                "GET /tareas",
                "PUT /tareas/{id}",
                "DELETE /tareas/{id}"
            ],
            "resumen": [
                "GET /resumen"
            ]
        }
    }


# ==================== ENDPOINTS DE PROYECTOS ====================

@app.get("/proyectos")
def listar_proyectos(nombre: Optional[str] = Query(None, description="Filtrar por nombre (búsqueda parcial)")):
    """
    Lista todos los proyectos con filtro opcional por nombre
    """
    try:
        proyectos = obtener_todos_proyectos(nombre=nombre)
        return proyectos
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener proyectos: {str(e)}")


@app.get("/proyectos/{id}")
def obtener_proyecto(id: int):
    """
    Obtiene un proyecto específico con contador de tareas
    """
    proyecto = obtener_proyecto_por_id(id)
    
    if not proyecto:
        raise HTTPException(
            status_code=404, 
            detail="Proyecto no encontrado"
        )
    
    return proyecto


@app.post("/proyectos", status_code=201)
def crear_nuevo_proyecto(proyecto: ProyectoCreate):
    """
    Crea un nuevo proyecto
    """
    # Validar que el nombre no esté vacío (Pydantic ya valida min_length, pero verificamos espacios)
    if not proyecto.nombre or proyecto.nombre.strip() == "":
        raise HTTPException(
            status_code=422,  # Cambiar a 422 para validaciones
            detail="El nombre del proyecto no puede estar vacío"
        )
    
    # Verificar que el nombre no exista
    if not verificar_nombre_proyecto_unico(proyecto.nombre):
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un proyecto con el nombre '{proyecto.nombre}'"
        )
    
    try:
        nuevo_proyecto = crear_proyecto(
            nombre=proyecto.nombre,
            descripcion=proyecto.descripcion
        )
        return nuevo_proyecto
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un proyecto con el nombre '{proyecto.nombre}'"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear proyecto: {str(e)}")


@app.put("/proyectos/{id}")
def modificar_proyecto(id: int, proyecto: ProyectoUpdate):
    """
    Actualiza un proyecto existente
    """
    # Verificar que el proyecto existe
    proyecto_existente = obtener_proyecto_por_id(id)
    if not proyecto_existente:
        raise HTTPException(
            status_code=404,
            detail="Proyecto no encontrado"
        )
    
    # Validar nombre si se proporciona
    if proyecto.nombre is not None:
        if proyecto.nombre.strip() == "":
            raise HTTPException(
                status_code=400,
                detail="El nombre del proyecto no puede estar vacío"
            )
        
        # Verificar nombre único (excluyendo el proyecto actual)
        if not verificar_nombre_proyecto_unico(proyecto.nombre, excluir_id=id):
            raise HTTPException(
                status_code=409,
                detail=f"Ya existe otro proyecto con el nombre '{proyecto.nombre}'"
            )
    
    # Verificar que hay campos para actualizar
    if proyecto.nombre is None and proyecto.descripcion is None:
        raise HTTPException(
            status_code=400,
            detail="No hay campos para actualizar"
        )
    
    try:
        proyecto_actualizado = actualizar_proyecto(
            proyecto_id=id,
            nombre=proyecto.nombre,
            descripcion=proyecto.descripcion
        )
        return proyecto_actualizado
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=409,
            detail=f"Ya existe un proyecto con el nombre '{proyecto.nombre}'"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar proyecto: {str(e)}")


@app.delete("/proyectos/{id}", status_code=200)
def borrar_proyecto(id: int):
    """
    Elimina un proyecto y todas sus tareas asociadas (CASCADE)
    """
    # Obtener información del proyecto antes de eliminarlo
    proyecto = obtener_proyecto_por_id(id)
    
    if not proyecto:
        raise HTTPException(
            status_code=404,
            detail="Proyecto no encontrado"
        )
    
    # Guardar información antes de eliminar
    cantidad_tareas = proyecto.get('total_tareas', 0)  # Cambiar de 'cantidad_tareas' a 'total_tareas'
    
    # Eliminar proyecto (las tareas se eliminan automáticamente por CASCADE)
    eliminado = eliminar_proyecto(id)
    
    if not eliminado:
        raise HTTPException(
            status_code=500,
            detail="Error al eliminar el proyecto"
        )
    
    return {
        "mensaje": "Proyecto eliminado correctamente",
        "proyecto_id": id,
        "tareas_eliminadas": cantidad_tareas
    }


# ==================== ENDPOINTS DE TAREAS ASOCIADAS A PROYECTOS ====================

@app.get("/proyectos/{id}/tareas")
def listar_tareas_proyecto(
    id: int,
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad"),
    orden: Optional[str] = Query("asc", description="Orden por fecha (asc/desc)")
):
    """
    Lista todas las tareas de un proyecto específico con filtros opcionales
    """
    # Verificar que el proyecto existe
    proyecto = obtener_proyecto_por_id(id)
    if not proyecto:
        raise HTTPException(
            status_code=404,
            detail="Proyecto no encontrado"
        )
    
    try:
        tareas = obtener_tareas_por_proyecto(
            proyecto_id=id,
            estado=estado,
            prioridad=prioridad,
            orden=orden
        )
        return tareas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener tareas: {str(e)}")


@app.post("/proyectos/{id}/tareas", status_code=201)
def crear_tarea_en_proyecto(id: int, tarea: TareaCreate):
    """
    Crea una nueva tarea dentro de un proyecto específico
    """
    # Verificar que el proyecto existe
    proyecto = obtener_proyecto_por_id(id)
    if not proyecto:
        raise HTTPException(
            status_code=400,
            detail=f"El proyecto con ID {id} no existe"
        )
    
    # Validar descripción
    if not tarea.descripcion or tarea.descripcion.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="La descripción de la tarea no puede estar vacía"
        )
    
    try:
        nueva_tarea = crear_tarea(
            descripcion=tarea.descripcion,
            estado=tarea.estado,
            prioridad=tarea.prioridad,
            proyecto_id=id
        )
        return nueva_tarea
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=400,
            detail=f"El proyecto con ID {id} no existe"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al crear tarea: {str(e)}")


# ==================== ENDPOINTS DE TAREAS GENERALES ====================

@app.get("/tareas")
def listar_todas_tareas(
    estado: Optional[str] = Query(None, description="Filtrar por estado"),
    prioridad: Optional[str] = Query(None, description="Filtrar por prioridad"),
    proyecto_id: Optional[int] = Query(None, description="Filtrar por proyecto"),
    orden: Optional[str] = Query("asc", description="Orden por fecha (asc/desc)")
):
    """
    Lista todas las tareas de todos los proyectos con filtros opcionales
    """
    try:
        tareas = obtener_todas_tareas(
            estado=estado,
            prioridad=prioridad,
            proyecto_id=proyecto_id,
            orden=orden
        )
        return tareas
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener tareas: {str(e)}")


@app.put("/tareas/{id}")
def modificar_tarea(id: int, tarea: TareaUpdate):
    """
    Actualiza una tarea existente (puede cambiar de proyecto)
    """
    # Verificar que la tarea existe
    tarea_existente = obtener_tarea_por_id(id)
    if not tarea_existente:
        raise HTTPException(
            status_code=404,
            detail="Tarea no encontrada"
        )
    
    # Validar descripción si se proporciona
    if tarea.descripcion is not None and tarea.descripcion.strip() == "":
        raise HTTPException(
            status_code=400,
            detail="La descripción no puede estar vacía"
        )
    
    # Validar que el nuevo proyecto_id existe si se proporciona
    if tarea.proyecto_id is not None:
        proyecto = obtener_proyecto_por_id(tarea.proyecto_id)
        if not proyecto:
            raise HTTPException(
                status_code=400,
                detail=f"El proyecto con ID {tarea.proyecto_id} no existe"
            )
    
    # Verificar que hay campos para actualizar
    if (tarea.descripcion is None and tarea.estado is None and 
        tarea.prioridad is None and tarea.proyecto_id is None):
        raise HTTPException(
            status_code=400,
            detail="No hay campos para actualizar"
        )
    
    try:
        tarea_actualizada = actualizar_tarea(
            tarea_id=id,
            descripcion=tarea.descripcion,
            estado=tarea.estado,
            prioridad=tarea.prioridad,
            proyecto_id=tarea.proyecto_id
        )
        return tarea_actualizada
    except sqlite3.IntegrityError:
        raise HTTPException(
            status_code=400,
            detail=f"El proyecto con ID {tarea.proyecto_id} no existe"
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al actualizar tarea: {str(e)}")


@app.delete("/tareas/{id}", status_code=200)
def borrar_tarea(id: int):
    """
    Elimina una tarea existente
    """
    tarea = obtener_tarea_por_id(id)
    
    if not tarea:
        raise HTTPException(
            status_code=404,
            detail="Tarea no encontrada"
        )
    
    eliminado = eliminar_tarea(id)
    
    if not eliminado:
        raise HTTPException(
            status_code=500,
            detail="Error al eliminar la tarea"
        )
    
    return {
        "mensaje": "Tarea eliminada correctamente",
        "tarea_id": id
    }


# ==================== ENDPOINTS DE RESUMEN Y ESTADÍSTICAS ====================

@app.get("/proyectos/{id}/resumen")
def obtener_estadisticas_proyecto(id: int):
    """
    Devuelve estadísticas detalladas de un proyecto específico
    """
    resumen = obtener_resumen_proyecto(id)
    
    if not resumen:
        raise HTTPException(
            status_code=404,
            detail="Proyecto no encontrado"
        )
    
    return resumen


@app.get("/resumen")
def obtener_estadisticas_generales():
    """
    Devuelve resumen general de toda la aplicación
    """
    try:
        resumen = obtener_resumen_general()
        return resumen
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error al obtener resumen: {str(e)}")


# ==================== ENDPOINT DE PRUEBA/DEBUG ====================

@app.get("/health")
def health_check():
    """Verifica que la API está funcionando correctamente"""
    return {
        "status": "OK",
        "mensaje": "API funcionando correctamente",
        "base_datos": "tareas.db"
    }