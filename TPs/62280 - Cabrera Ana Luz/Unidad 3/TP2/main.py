from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, validator
from enum import Enum
from typing import List, Optional
from datetime import datetime
from fastapi import Response 

app = FastAPI(title="Mini API de Tareas")

class EstadoTarea(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

class Tarea(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: EstadoTarea = EstadoTarea.pendiente

    @validator("descripcion")
    def descripcion_no_vacia(cls, v):
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v

class TareaCompleta(Tarea):
    id: int
    fecha_creacion: datetime

tareas: List[TareaCompleta] = []
contador_id = 1

@app.get("/tareas", response_model=List[TareaCompleta])
def listar_tareas(estado: Optional[EstadoTarea] = None, texto: Optional[str] = None):
    resultado = tareas
    if estado:
        resultado = [t for t in resultado if t.estado == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]
    return resultado

@app.post("/tareas", response_model=TareaCompleta, status_code=201)
def crear_tarea(tarea: Tarea):
    global contador_id
    nueva_tarea = TareaCompleta(
        id=contador_id,
        descripcion=tarea.descripcion,
        estado=tarea.estado,
        fecha_creacion=datetime.now()
    )
    tareas.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea

@app.put("/tareas/{id}", response_model=TareaCompleta)
def actualizar_tarea(id: int, datos: Tarea):
    for t in tareas:
        if t.id == id:
            t.descripcion = datos.descripcion
            t.estado = datos.estado
            return t
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

@app.delete("/tareas/{id}", status_code=204)
def eliminar_tarea(id: int):
    for i, t in enumerate(tareas):
        if t.id == id:
            tareas.pop(i)
            return
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})


@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for t in tareas:
        resumen[t.estado] += 1
    return resumen

@app.put("/tareas/completar_todas")
def completar_todas(response: Response):
    if not tareas:
        return {"mensaje": "No hay tareas para completar"}
    for t in tareas:
        t.estado = EstadoTarea.completada
    response.status_code = 200
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}