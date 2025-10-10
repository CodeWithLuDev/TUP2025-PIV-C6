from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, constr
from typing import List, Optional
from datetime import datetime

app = FastAPI()

# Base de datos en memoria
tareas_db = []
contador_id = 1

# Modelos de datos
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: datetime

class TareaInput(BaseModel):
    descripcion: str = Field(..., min_length=1)
    EstadoStr=constr(regex='^(pendiente|en_progreso|completada)$')

# GET /tareas con filtros opcionales
@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(EstadoStr: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    resultado = tareas_db
    if EstadoStr:
        resultado = [t for t in resultado if t.estado == EstadoStr]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]
    return resultado

# POST /tareas
@app.post("/tareas", response_model=Tarea, status_code=201)
def crear_tarea(tarea: TareaInput):
    global contador_id
    nueva_tarea = Tarea(
        id=contador_id,
        descripcion=tarea.descripcion,
        estado=tarea.estado,
        fecha_creacion=datetime.now()
    )
    tareas_db.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea

# PUT /tareas/{id}
@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea: TareaInput):
    for i, t in enumerate(tareas_db):
        if t.id == id:
            tareas_db[i].descripcion = tarea.descripcion
            tareas_db[i].estado = tarea.estado
            return tareas_db[i]
    raise HTTPException(status_code=404, detail="La tarea no existe")

# DELETE /tareas/{id}
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for i, t in enumerate(tareas_db):
        if t.id == id:
            tareas_db.pop(i)
            return {"mensaje": "Tarea eliminada"}
    raise HTTPException(status_code=404, detail="La tarea no existe")

# GET /tareas/resumen
@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for t in tareas_db:
        resumen[t.estado] += 1
    return resumen

# PUT /tareas/completar_todas
@app.put("/tareas/completar_todas")
def completar_todas():
    for t in tareas_db:
        t.estado = "completada"
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}
