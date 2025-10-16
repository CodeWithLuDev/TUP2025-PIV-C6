from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime
from enum import Enum

app = FastAPI()

# Base de datos en memoria
tareas_db = []
contador_id = 1

# Enum para los estados válidos
class EstadoTarea(str, Enum):
    PENDIENTE = "pendiente"
    EN_PROGRESO = "en_progreso"
    COMPLETADA = "completada"

# Modelo para la respuesta de completar_todas
class MensajeRespuesta(BaseModel):
    mensaje: str

# Modelo para la tarea
class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1, pattern=r"^\S.*$")
    estado: Optional[EstadoTarea] = EstadoTarea.PENDIENTE

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v):
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1, pattern=r"^\S.*$")
    estado: Optional[EstadoTarea] = None

    @field_validator("descripcion", mode="before")
    @classmethod
    def descripcion_no_vacia(cls, v):
        if v is not None and not v.strip():
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: EstadoTarea
    fecha_creacion: str

# GET /tareas - Obtener todas las tareas o filtrar por estado o texto
@app.get("/tareas", response_model=list[Tarea])
def obtener_tareas(estado: Optional[EstadoTarea] = Query(None), texto: Optional[str] = Query(None)):
    tareas = tareas_db
    if estado:
        tareas = [tarea for tarea in tareas if tarea["estado"] == estado]
    if texto:
        texto = texto.lower()
        tareas = [tarea for tarea in tareas if texto in tarea["descripcion"].lower()]
    return tareas

# GET /tareas/resumen - Obtener resumen de tareas por estado
# IMPORTANTE: Esta ruta debe estar ANTES de /tareas/{id}
@app.get("/tareas/resumen")
def obtener_resumen():
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    for tarea in tareas_db:
        resumen[tarea["estado"]] += 1
    return resumen

# PUT /tareas/completar_todas - Marcar todas las tareas como completadas
# IMPORTANTE: Esta ruta debe estar ANTES de /tareas/{id}
@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    for tarea in tareas_db:
        tarea["estado"] = EstadoTarea.COMPLETADA.value
    return {"mensaje": "Todas las tareas han sido marcadas como completadas"}

# POST /tareas - Crear una nueva tarea
@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(tarea: TareaCreate):
    global contador_id
    nueva_tarea = {
        "id": contador_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado.value,
        "fecha_creacion": datetime.now().isoformat()
    }
    tareas_db.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea

# PUT /tareas/{id} - Actualizar una tarea existente
@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea_update: TareaUpdate):
    for tarea in tareas_db:
        if tarea["id"] == id:
            if tarea_update.descripcion is not None:
                tarea["descripcion"] = tarea_update.descripcion
            if tarea_update.estado is not None:
                tarea["estado"] = tarea_update.estado.value
            return tarea
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

# DELETE /tareas/{id} - Eliminar una tarea
@app.delete("/tareas/{id}", response_model=MensajeRespuesta)
def eliminar_tarea(id: int):
    for i, tarea in enumerate(tareas_db):
        if tarea["id"] == id:
            tareas_db.pop(i)
            return MensajeRespuesta(mensaje="Tarea eliminada correctamente")
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})