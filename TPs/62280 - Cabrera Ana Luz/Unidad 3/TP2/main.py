from fastapi import FastAPI, HTTPException, Query, Body
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

# Nuevo modelo para actualizaciones parciales
class TareaActualizar(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[EstadoTarea] = None

    @validator("descripcion")
    def descripcion_no_vacia(cls, v):
        if v is not None and not v.strip():
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
def actualizar_tarea(id: int, datos: TareaActualizar):
    for t in tareas:
        if t.id == id:
            if datos.descripcion is not None:
                t.descripcion = datos.descripcion
            if datos.estado is not None:
                t.estado = datos.estado
            return t
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

@app.delete("/tareas/{id}", status_code=204)
def eliminar_tarea(id: int):
    for i, t in enumerate(tareas):
        if t.id == id:
            tareas.pop(i)
            return Response(status_code=204)
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})


@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for t in tareas:
        resumen[t.estado] += 1
    return resumen

@app.put("/tareas/completar_todas")
def completar_todas(body: dict = Body(default={})):
    if not tareas:
        return {"mensaje": "No hay tareas para completar"}
    for t in tareas:
        t.estado = EstadoTarea.completada
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}