from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from typing import List, Optional
from datetime import datetime

app = FastAPI(title="Mini API de Tareas")

tareas = []
contador_id = 1
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}

class Tarea(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str = Field(...)

class TareaCompleta(Tarea):
    id: int
    fecha_creacion: str

@app.get("/tareas", response_model=List[TareaCompleta])
def obtener_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    resultado = tareas
    if estado:
        if estado not in ESTADOS_VALIDOS:
            raise HTTPException(status_code=400, detail="Estado inválido")
        resultado = [t for t in resultado if t["estado"] == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]
    return resultado

@app.post("/tareas", response_model=TareaCompleta, status_code=201)
def crear_tarea(tarea: Tarea):
    global contador_id
    if tarea.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Estado inválido")
    nueva_tarea = {
        "id": contador_id,
        "descripcion": tarea.descripcion.strip(),
        "estado": tarea.estado,
        "fecha_creacion": datetime.now().isoformat()
    }
    tareas.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea

@app.put("/tareas/{id}", response_model=TareaCompleta)
def actualizar_tarea(id: int, tarea: Tarea):
    for t in tareas:
        if t["id"] == id:
            if tarea.estado not in ESTADOS_VALIDOS:
                raise HTTPException(status_code=400, detail="Estado inválido")
            if not tarea.descripcion.strip():
                raise HTTPException(status_code=400, detail="La descripción no puede estar vacía")
            t["descripcion"] = tarea.descripcion.strip()
            t["estado"] = tarea.estado
            return t
    raise HTTPException(status_code=404, detail="La tarea no existe")

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for t in tareas:
        if t["id"] == id:
            tareas.remove(t)
            return {"mensaje": "Tarea eliminada correctamente"}
    raise HTTPException(status_code=404, detail="La tarea no existe")

@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {estado: 0 for estado in ESTADOS_VALIDOS}
    for t in tareas:
        resumen[t["estado"]] += 1
    return resumen

from fastapi import Body

@app.put("/tareas/completar_todas", response_model=dict)
def completar_todas(body: dict = Body(default=None)):
    if not tareas:
        return {"mensaje": "No hay tareas para completar"}
    for t in tareas:
        t["estado"] = "completada"
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}
