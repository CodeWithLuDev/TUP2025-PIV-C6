from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from datetime import datetime
from typing import List, Optional
from enum import Enum

app = FastAPI()

# Definición del modelo de datos
class EstadoTarea(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"

class Tarea(BaseModel):
    id: Optional[int] = None
    descripcion: str
    estado: EstadoTarea = EstadoTarea.PENDIENTE
    fecha_creacion: Optional[datetime] = None

# Lista para almacenar las tareas en memoria
tareas = []
contador_id = 1  # Para generar IDs únicos

@app.get("/")
async def root():
    return {"message": "Mini API de Tareas con FastAPI"}

# Endpoint para obtener todas las tareas
@app.get("/tareas")
async def obtener_tareas(estado: Optional[str] = None, texto: Optional[str] = None):
    if estado and estado not in [e.value for e in EstadoTarea]:
        raise HTTPException(status_code=400, detail="Estado no válido")
    
    tareas_filtradas = tareas
    
    if estado:
        tareas_filtradas = [t for t in tareas_filtradas if t.estado == estado]
    if texto:
        tareas_filtradas = [t for t in tareas_filtradas if texto.lower() in t.descripcion.lower()]
    
    return tareas_filtradas

# Endpoint para crear una nueva tarea
@app.post("/tareas", status_code=201)
async def crear_tarea(tarea: Tarea):
    global contador_id
    if not tarea.descripcion.strip():
        raise HTTPException(status_code=400, detail="La descripción no puede estar vacía")
    
    tarea.id = contador_id
    tarea.fecha_creacion = datetime.now()
    tareas.append(tarea)
    contador_id += 1
    return tarea

# Endpoint para actualizar una tarea
@app.put("/tareas/{id}")
async def actualizar_tarea(id: int, tarea_actualizada: Tarea):
    tarea_existente = next((t for t in tareas if t.id == id), None)
    if not tarea_existente:
        raise HTTPException(status_code=404, detail="La tarea no existe")
    
    if not tarea_actualizada.descripcion.strip():
        raise HTTPException(status_code=400, detail="La descripción no puede estar vacía")
    
    if tarea_actualizada.estado not in [e.value for e in EstadoTarea]:
        raise HTTPException(status_code=400, detail="Estado no válido")
    
    tarea_existente.descripcion = tarea_actualizada.descripcion
    tarea_existente.estado = tarea_actualizada.estado
    return tarea_existente

# Endpoint para eliminar una tarea
@app.delete("/tareas/{id}")
async def eliminar_tarea(id: int):
    tarea = next((t for t in tareas if t.id == id), None)
    if not tarea:
        raise HTTPException(status_code=404, detail="La tarea no existe")
    
    tareas.remove(tarea)
    return {"message": "Tarea eliminada exitosamente"}

# Endpoint para obtener el resumen de tareas por estado
@app.get("/tareas/resumen")
async def obtener_resumen():
    resumen = {
        EstadoTarea.PENDIENTE.value: 0,
        EstadoTarea.EN_PROGRESO.value: 0,
        EstadoTarea.COMPLETADA.value: 0
    }
    
    for tarea in tareas:
        resumen[tarea.estado] += 1
    
    return resumen

# Endpoint para marcar todas las tareas como completadas
@app.put("/tareas/completar_todas")
async def completar_todas_las_tareas():
    if not tareas:
        return {"message": "No hay tareas para completar"}
    
    for tarea in tareas:
        tarea.estado = EstadoTarea.COMPLETADA
    
    return {"message": f"Se han completado {len(tareas)} tareas"}
