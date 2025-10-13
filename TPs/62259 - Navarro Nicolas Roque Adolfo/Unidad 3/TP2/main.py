from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="Mini API de Tareas  TP2")


ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}


class Tarea(BaseModel):
    id: int
    descripcion: str = Field(..., min_length=1)
    estado: str
    creada: datetime


class TareaInput(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str


tareas: List[Tarea] = []
contador_id = 1


@app.post("/tareas", response_model=Tarea)
def crear_tarea(data: TareaInput):
    global contador_id
    if data.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
    nueva = Tarea(id=contador_id, descripcion=data.descripcion, estado=data.estado, creada=datetime.now())
    tareas.append(nueva)
    contador_id += 1
    return nueva


@app.get("/tareas", response_model=List[Tarea])
def listar_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    resultado = tareas
    if estado:
        resultado = [t for t in resultado if t.estado == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]
    return resultado


@app.put("/tareas/{id}", response_model=Tarea)
def modificar_tarea(id: int, data: TareaInput):
    for t in tareas:
        if t.id == id:
            if data.estado not in ESTADOS_VALIDOS:
                raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
            t.descripcion = data.descripcion
            t.estado = data.estado
            return t
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for t in tareas:
        if t.id == id:
            tareas.remove(t)
            return {"mensaje": "Tarea eliminada"}
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})


@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {estado: 0 for estado in ESTADOS_VALIDOS}
    for t in tareas:
        resumen[t.estado] += 1
    return resumen


@app.put("/tareas/completar_todas")
def completar_todas():
    for t in tareas:
        t.estado = "completada"
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}