from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime
from enum import Enum

app = FastAPI(title="Mini API de Tareas")

# Enum para estados válidos
class Estado(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

# Modelo Pydantic para Tarea
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: Estado
    fecha_creacion: datetime

class CrearTarea(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Estado = Estado.pendiente

class ActualizarTarea(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Estado] = None

# Base de datos en memoria
tareas_db: dict[int, Tarea] = {}
contador_id = 1

# ========== RUTAS GET ==========

@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(
    estado: Optional[Estado] = Query(None),
    texto: Optional[str] = Query(None)
):
    """
    Obtiene todas las tareas con filtros opcionales.
    - estado: filtra por estado (pendiente, en_progreso, completada)
    - texto: filtra tareas que contengan el texto en la descripción
    """
    tareas = list(tareas_db.values())
    
    if estado:
        tareas = [t for t in tareas if t.estado == estado]
    
    if texto:
        tareas = [t for t in tareas if texto.lower() in t.descripcion.lower()]
    
    return tareas

@app.get("/tareas/resumen")
def obtener_resumen():
    """Retorna un resumen con el contador de tareas por estado."""
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for tarea in tareas_db.values():
        resumen[tarea.estado] += 1
    
    return resumen

@app.get("/tareas/{id}", response_model=Tarea)
def obtener_tarea_por_id(id: int):
    """Obtiene una tarea específica por su ID."""
    if id not in tareas_db:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    return tareas_db[id]

# ========== RUTAS POST ==========

@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(nueva_tarea: CrearTarea):
    """
    Crea una nueva tarea.
    - descripcion: requerida y no puede estar vacía
    - estado: por defecto "pendiente"
    """
    global contador_id
    
    contador_id += 1
    tarea = Tarea(
        id=contador_id,
        descripcion=nueva_tarea.descripcion,
        estado=nueva_tarea.estado,
        fecha_creacion=datetime.now()
    )
    
    tareas_db[contador_id] = tarea
    return tarea

# ========== RUTAS PUT ==========

@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea_actualizada: ActualizarTarea):
    """
    Actualiza una tarea existente.
    - Solo se pueden actualizar descripcion y/o estado
    - Si la tarea no existe, retorna 404
    """
    if id not in tareas_db:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    tarea = tareas_db[id]
    
    # Actualizar descripción si se proporciona
    if tarea_actualizada.descripcion is not None:
        tarea.descripcion = tarea_actualizada.descripcion
    
    # Actualizar estado si se proporciona
    if tarea_actualizada.estado is not None:
        tarea.estado = tarea_actualizada.estado
    
    tareas_db[id] = tarea
    return tarea

@app.put("/tareas/completar_todas", response_model=dict)
def completar_todas():
    """Marca todas las tareas como completadas."""
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    
    for tarea in tareas_db.values():
        tarea.estado = Estado.completada
    
    return {"mensaje": f"Se completaron {len(tareas_db)} tareas"}

# ========== RUTAS DELETE ==========

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """
    Elimina una tarea existente por su ID.
    - Si la tarea no existe, retorna 404
    """
    if id not in tareas_db:
        raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
    
    del tareas_db[id]
    return {"mensaje": "Tarea eliminada correctamente"}

# ========== RUTA DE BIENVENIDA ==========

@app.get("/")
def bienvenida():
    """Ruta de bienvenida con información de la API."""
    return {
        "titulo": "Mini API de Tareas",
        "version": "1.0",
        "rutas_disponibles": {
            "GET /tareas": "Obtener todas las tareas (con filtros opcionales: estado, texto)",
            "GET /tareas/{id}": "Obtener una tarea específica",
            "GET /tareas/resumen": "Obtener resumen de tareas por estado",
            "POST /tareas": "Crear una nueva tarea",
            "PUT /tareas/{id}": "Actualizar una tarea",
            "PUT /tareas/completar_todas": "Marcar todas las tareas como completadas",
            "DELETE /tareas/{id}": "Eliminar una tarea"
        }
    }