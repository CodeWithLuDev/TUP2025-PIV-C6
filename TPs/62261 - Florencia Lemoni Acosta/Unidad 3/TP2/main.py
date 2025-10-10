from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="Mini API de Tareas - TP2")

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: datetime

class TareaInput(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str = "pendiente"
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v.strip()
    
    @field_validator('estado')
    @classmethod
    def validar_estado(cls, v):
        ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}
        if v not in ESTADOS_VALIDOS:
            raise ValueError('Estado inválido')
        return v

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    
    @field_validator('descripcion')
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError('La descripción no puede estar vacía o contener solo espacios')
        return v.strip() if v else v
    
    @field_validator('estado')
    @classmethod
    def validar_estado(cls, v):
        if v is not None:
            ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}
            if v not in ESTADOS_VALIDOS:
                raise ValueError('Estado inválido')
        return v

tareas_db: List[Tarea] = []
id_counter = 1
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}


@app.get("/")
def raiz():
    return {"mensaje": "Bienvenido a la Mini API de Tareas - TP2"}


@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {estado: 0 for estado in ESTADOS_VALIDOS}
    for t in tareas_db:
        resumen[t.estado] += 1
    return resumen


@app.put("/tareas/completar_todas")
def completar_todas():
    if len(tareas_db) == 0:
        return {"mensaje": "No hay tareas para completar"}
    for t in tareas_db:
        t.estado = "completada"
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}


@app.get("/tareas")
def obtener_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    resultado = tareas_db
    if estado:
        resultado = [t for t in resultado if t.estado == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]
    return resultado


@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaInput):
    global id_counter
    nueva = Tarea(
        id=id_counter, 
        descripcion=tarea.descripcion, 
        estado=tarea.estado, 
        fecha_creacion=datetime.now()
    )
    tareas_db.append(nueva)
    id_counter += 1
    return nueva


@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    for t in tareas_db:
        if t.id == id:
            if tarea.descripcion is not None:
                t.descripcion = tarea.descripcion
            if tarea.estado is not None:
                t.estado = tarea.estado
            return t
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for i, t in enumerate(tareas_db):
        if t.id == id:
            tareas_db.pop(i)
            return {"mensaje": "Tarea eliminada"}
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})