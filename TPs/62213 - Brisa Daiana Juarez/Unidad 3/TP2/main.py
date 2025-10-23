from fastapi import FastAPI, HTTPException, Request, status
from fastapi.responses import JSONResponse
from fastapi.exceptions import RequestValidationError
from pydantic import BaseModel, constr, validator
from datetime import datetime
from typing import List, Optional, Dict, Union, Any


app = FastAPI()


class TareaCreate(BaseModel):
    descripcion: str
    estado: str = "pendiente"

    @validator("estado")
    def validar_estado(cls, v):
        if v not in ["pendiente", "en_progreso", "completada"]:
            raise ValueError("Estado no válido")
        return v

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: datetime

# Base de datos en memoria
tareas_db = []  # Lista global para almacenar las tareas
contador_id = 1

# Alias para compatibilidad con los tests
tareas = tareas_db

@app.get("/tareas")
async def obtener_tareas(estado: Optional[str] = None, texto: Optional[str] = None):
    tareas_filtradas = tareas_db
    
    if estado:
        tareas_filtradas = [t for t in tareas_filtradas if t.estado == estado]
    
    if texto:
        tareas_filtradas = [t for t in tareas_filtradas if texto.lower() in t.descripcion.lower()]
    
    return tareas_filtradas

@app.post("/tareas", status_code=201)
async def crear_tarea(tarea: TareaCreate):
    global contador_id
    
    if not tarea.descripcion or not tarea.descripcion.strip():
        raise HTTPException(status_code=400, detail="La descripción no puede estar vacía")
    
    nueva_tarea = Tarea(
        id=contador_id,
        descripcion=tarea.descripcion.strip(),
        estado=tarea.estado,
        fecha_creacion=datetime.now()
    )
    
    tareas_db.append(nueva_tarea)
    contador_id += 1
    
    return nueva_tarea

@app.put("/tareas/{id}")
async def actualizar_tarea(id: int, tarea_update: Dict[str, Any]):
    tarea = next((t for t in tareas_db if t.id == id), None)
    if not tarea:
        raise HTTPException(status_code=404, detail="error: La tarea no existe")
    
    if "descripcion" in tarea_update:
        descripcion = str(tarea_update["descripcion"]).strip()
        if not descripcion:
            raise HTTPException(status_code=422, detail="error: La descripción no puede estar vacía")
        tarea.descripcion = descripcion
    
    if "estado" in tarea_update:
        estado = str(tarea_update["estado"])
        if estado not in ["pendiente", "en_progreso", "completada"]:
            raise HTTPException(status_code=422, detail="error: Estado no válido")
        tarea.estado = estado
    
    return tarea

@app.delete("/tareas/{id}")
async def eliminar_tarea(id: int):
    tarea = next((t for t in tareas_db if t.id == id), None)
    if not tarea:
        raise HTTPException(status_code=404, detail="error: La tarea no existe")
    
    tareas_db.remove(tarea)
    return {"mensaje": "Tarea eliminada exitosamente"}

@app.get("/tareas/resumen")
async def obtener_resumen():
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for tarea in tareas_db:
        resumen[tarea.estado] += 1
    
    return resumen

@app.post("/tareas/completar_todas")
async def completar_todas():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    
    for tarea in tareas_db:
        tarea.estado = "completada"
    
    return {"mensaje": f"Se han completado {len(tareas_db)} tareas"}

@app.get("/")
async def root():
    return {"message": "Mini API de Tareas con FastAPI"}
