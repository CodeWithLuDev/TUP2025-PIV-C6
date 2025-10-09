# main.py
from fastapi import FastAPI, Query, Path
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime

app = FastAPI(title="Mini API de Tareas - TP2")

ALLOWED_ESTADOS = {"pendiente", "en_progreso", "completada"}

# Modelos para request
class TareaCreate(BaseModel):
    descripcion: str
    estado: Optional[str] = "pendiente"

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None

# Almacenamiento en memoria
tareas: List[dict] = []
_next_id = 1

def _find_index_by_id(tarea_id: int):
    for idx, t in enumerate(tareas):
        if t["id"] == tarea_id:
            return idx
    return None

@app.get("/tareas")
def obtener_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    """
    Devuelve todas las tareas. Si se pasa 'estado' filtra por estado (validar valor).
    Si se pasa 'texto' busca (case-insensitive) en la descripcion.
    """
    if estado is not None and estado not in ALLOWED_ESTADOS:
        return JSONResponse(status_code=400, content={"error": "Estado inválido"})

    resultado = tareas
    if estado is not None:
        resultado = [t for t in resultado if t["estado"] == estado]
    if texto is not None:
        q = texto.strip().lower()
        resultado = [t for t in resultado if q in t["descripcion"].lower()]

    return resultado

@app.post("/tareas", status_code=201)
def crear_tarea(payload: TareaCreate):
    """
    Crea una tarea. descripcion no puede estar vacía. estado debe ser válido.
    """
    descripcion = payload.descripcion.strip() if payload.descripcion is not None else ""
    if descripcion == "":
        return JSONResponse(status_code=400, content={"error": "La descripción no puede estar vacía"})

    estado = payload.estado or "pendiente"
    if estado not in ALLOWED_ESTADOS:
        return JSONResponse(status_code=400, content={"error": "Estado inválido"})

    global _next_id
    tarea = {
        "id": _next_id,
        "descripcion": descripcion,
        "estado": estado,
        "created_at": datetime.utcnow().isoformat() + "Z"
    }
    tareas.append(tarea)
    _next_id += 1
    return tarea

@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int = Path(...), payload: TareaUpdate = None):
    """
    Actualiza (parcialmente) una tarea por id. Valida existencia y estado.
    """
    idx = _find_index_by_id(tarea_id)
    if idx is None:
        return JSONResponse(status_code=404, content={"error": "La tarea no existe"})

    if payload is None:
        return JSONResponse(status_code=400, content={"error": "No se recibieron datos para actualizar"})

    # descripcion
    if payload.descripcion is not None:
        desc = payload.descripcion.strip()
        if desc == "":
            return JSONResponse(status_code=400, content={"error": "La descripción no puede estar vacía"})
        tareas[idx]["descripcion"] = desc

    # estado
    if payload.estado is not None:
        if payload.estado not in ALLOWED_ESTADOS:
            return JSONResponse(status_code=400, content={"error": "Estado inválido"})
        tareas[idx]["estado"] = payload.estado

    return tareas[idx]

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int = Path(...)):
    """
    Elimina una tarea por id.
    """
    idx = _find_index_by_id(tarea_id)
    if idx is None:
        return JSONResponse(status_code=404, content={"error": "La tarea no existe"})
    tareas.pop(idx)
    return {"message": "Tarea eliminada"}

@app.get("/tareas/resumen")
def resumen_tareas():
    """
    Retorna contador por estado.
    """
    resumen = {
        "pendiente": sum(1 for t in tareas if t["estado"] == "pendiente"),
        "en_progreso": sum(1 for t in tareas if t["estado"] == "en_progreso"),
        "completada": sum(1 for t in tareas if t["estado"] == "completada"),
    }
    return resumen

@app.put("/tareas/completar_todas")
def completar_todas():
    """
    Marca todas las tareas como 'completada'. Retorna la cantidad actualizada.
    """
    updated = 0
    for t in tareas:
        if t["estado"] != "completada":
            t["estado"] = "completada"
            updated += 1
    return {"actualizadas": updated}
