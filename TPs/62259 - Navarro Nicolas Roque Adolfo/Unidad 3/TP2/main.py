from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime
from enum import Enum


app = FastAPI(title="API Para gestionar tareas")

tareas_db = []
contador_id = 1

class Estado(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: Estado
    fecha_creacion: datetime

class TareaCreate(BaseModel):
    descripcion: str
    estado: Optional[Estado] = Estado.pendiente

class TareaUpdate(BaseModel): 
    descripcion: Optional[str] = None
    estado: Optional[Estado] = None

def validar_estado(estado: str):
    estados_validos = {"pendiente", "en_progreso", "completada"}
    if estado not in estados_validos:
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail={"error": "Estado inválido. Debe ser 'pendiente', 'en_progreso' o 'completada'"}
        )

@app.get("/tareas/resumen")
def get_resumen():
    conteo = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    for tarea in tareas_db:
        if tarea.estado in conteo:
            conteo[tarea.estado] += 1
    return conteo

@app.put("/tareas/completar_todas", status_code=status.HTTP_200_OK)
def completar_todas():
    if len(tareas_db) == 0:
        return {"mensaje": "No hay tareas"}
    
    for tarea in tareas_db:
        tarea.estado = Estado.completada
    return {"mensaje": "Todas las tareas marcadas como completadas"}

@app.get("/tareas", response_model=List[Tarea])
def get_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    resultado = tareas_db
    if estado:
        validar_estado(estado)  
        resultado = [t for t in resultado if t.estado == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]
    return resultado

@app.post("/tareas", response_model=Tarea, status_code=status.HTTP_201_CREATED)
def create_tarea(tarea: TareaCreate):
    global contador_id
    if not tarea.descripcion.strip():  
        raise HTTPException(
            status_code=status.HTTP_422_UNPROCESSABLE_ENTITY, 
            detail={"error": "La descripción no puede estar vacía"}
        )
    validar_estado(tarea.estado)  
    nueva_tarea = Tarea(
        id=contador_id,
        descripcion=tarea.descripcion,
        estado=tarea.estado,
        fecha_creacion=datetime.now()
    )
    tareas_db.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea

@app.put("/tareas/{id}", response_model=Tarea)
def update_tarea(id: int, tarea_update: TareaUpdate):
    for tarea in tareas_db:
        if tarea.id == id:
            if tarea_update.descripcion is not None:
                if not tarea_update.descripcion.strip():
                    raise HTTPException(
                        status_code=400, 
                        detail={"error": "La descripción no puede estar vacía"}
                    )
                tarea.descripcion = tarea_update.descripcion
            if tarea_update.estado is not None:
                validar_estado(tarea_update.estado)
                tarea.estado = tarea_update.estado
            return tarea
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

@app.delete("/tareas/{id}")
def delete_tarea(id: int):
    for i, tarea in enumerate(tareas_db):
        if tarea.id == id:
            del tareas_db[i]
            return {"mensaje": "Tarea eliminada"}
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})