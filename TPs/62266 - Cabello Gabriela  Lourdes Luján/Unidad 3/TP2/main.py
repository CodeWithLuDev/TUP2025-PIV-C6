from fastapi import FastAPI, Path, HTTPException, Query
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="Mini API de Tareas - TP2")

ALLOWED_ESTADOS = {"pendiente", "en_progreso", "completada"}


tareas_db: List[dict] = []
contador_id = 1


class TareaCreate(BaseModel):
    descripcion: str
    estado: Optional[str] = "pendiente"

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None


def _find_index_by_id(tarea_id: int):
    for idx, t in enumerate(tareas_db):
        if t["id"] == tarea_id:
            return idx
    return None


@app.get("/tareas")
def obtener_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    resultado = tareas_db
    if estado:
        if estado not in ALLOWED_ESTADOS:
            raise HTTPException(status_code=422, detail="Estado inválido")
        resultado = [t for t in resultado if t["estado"] == estado]
    if texto:
        q = texto.strip().lower()
        resultado = [t for t in resultado if q in t["descripcion"].lower()]
    return resultado


@app.post("/tareas", status_code=201)
def crear_tarea(payload: TareaCreate):
    descripcion = payload.descripcion.strip()
    if descripcion == "":
        
        raise HTTPException(status_code=422, detail="La descripción no puede estar vacía")
    estado = payload.estado or "pendiente"
    if estado not in ALLOWED_ESTADOS:
        raise HTTPException(status_code=422, detail="Estado inválido")
    global contador_id
    tarea = {
        "id": contador_id,
        "descripcion": descripcion,
        "estado": estado,
        "fecha_creacion": datetime.utcnow().isoformat() + "Z"
    }
    tareas_db.append(tarea)
    contador_id += 1
    return tarea


@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int = Path(...), payload: TareaUpdate = None):
    idx = _find_index_by_id(tarea_id)
    if idx is None:
        raise HTTPException(status_code=404, detail="error: La tarea no existe")
    if not payload or payload.dict(exclude_unset=True) == {}:
        raise HTTPException(status_code=400, detail="No se recibieron datos para actualizar")
    if payload.descripcion is not None:
        desc = payload.descripcion.strip()
        if desc == "":
            raise HTTPException(status_code=422, detail="La descripción no puede estar vacía")
        tareas_db[idx]["descripcion"] = desc
    if payload.estado is not None:
        if payload.estado not in ALLOWED_ESTADOS:
            raise HTTPException(status_code=422, detail="Estado inválido")
        tareas_db[idx]["estado"] = payload.estado
    return tareas_db[idx]


@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int = Path(...)):
    idx = _find_index_by_id(tarea_id)
    if idx is None:
        raise HTTPException(status_code=404, detail="error: La tarea no existe")
    tareas_db.pop(idx)
    return {"mensaje": "Tarea eliminada"}


@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {
        "pendiente": sum(1 for t in tareas_db if t["estado"] == "pendiente"),
        "en_progreso": sum(1 for t in tareas_db if t["estado"] == "en_progreso"),
        "completada": sum(1 for t in tareas_db if t["estado"] == "completada"),
    }
    return resumen


@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas_db:
        return {"mensaje": "No hay tareas"}
    for t in tareas_db:
        t["estado"] = "completada"
    return {"mensaje": "Todas las tareas completadas"}
