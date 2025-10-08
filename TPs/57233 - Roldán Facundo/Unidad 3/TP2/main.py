from fastapi import FastAPI, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
from typing import Optional, Dict
from datetime import datetime, timezone

app = FastAPI(title="Mini API de Tareas")

# Estados válidos
VALID_ESTADOS = {"pendiente", "en_progreso", "completada"}

# Almacenamiento en memoria
tasks: Dict[int, Dict] = {}
_next_id = 1  # contador incremental


# Schemas (Pydantic) para request bodies
class TareaCreate(BaseModel):
    descripcion: str
    estado: Optional[str] = "pendiente"


class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None


# --- RUTAS ---

@app.get("/tareas")
def obtener_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    """Devuelve todas las tareas, opcionalmente filtradas por estado y/o por texto en la descripción."""
    if estado is not None and estado not in VALID_ESTADOS:
        return JSONResponse({"error": "Estado inválido"}, status_code=400)

    resultado = []
    for t in tasks.values():
        if estado is not None and t["estado"] != estado:
            continue
        if texto is not None and texto.lower() not in t["descripcion"].lower():
            continue
        resultado.append(t)
    return resultado


@app.post("/tareas", status_code=201)
def crear_tarea(payload: TareaCreate):
    """Crea una nueva tarea en memoria. Valida descripción no vacía y estado válido."""
    global _next_id

    descripcion = (payload.descripcion or "").strip()
    if not descripcion:
        return JSONResponse({"error": "La descripción no puede estar vacía"}, status_code=400)

    estado = payload.estado or "pendiente"
    if estado not in VALID_ESTADOS:
        return JSONResponse({"error": "Estado inválido"}, status_code=400)

    creado_en = datetime.now(timezone.utc).isoformat()
    tarea_obj = {
        "id": _next_id,
        "descripcion": descripcion,
        "estado": estado,
        "creado_en": creado_en
    }
    tasks[_next_id] = tarea_obj
    _next_id += 1

    return JSONResponse(content=tarea_obj, status_code=201)


@app.put("/tareas/completar_todas")
def completar_todas():
    """Marca todas las tareas existentes como 'completada'."""
    modificadas = 0
    for t in tasks.values():
        if t["estado"] != "completada":
            t["estado"] = "completada"
            modificadas += 1
    return {"modificadas": modificadas, "total": len(tasks)}


@app.get("/tareas/resumen")
def resumen_estados():
    """Devuelve contador de tareas por estado."""
    resumen = {estado: 0 for estado in VALID_ESTADOS}
    for t in tasks.values():
        resumen[t["estado"]] += 1
    # devolver en el orden solicitado (opcional) - aquí devuelvo el dict normalmente
    return resumen


@app.put("/tareas/{tarea_id}")
def modificar_tarea(tarea_id: int, payload: TareaUpdate):
    """Modifica una tarea por id. Valida existencia, descripción no vacía y estado válido."""
    if tarea_id not in tasks:
        return JSONResponse({"error": "La tarea no existe"}, status_code=404)

    if payload.descripcion is not None:
        descripcion = payload.descripcion.strip()
        if not descripcion:
            return JSONResponse({"error": "La descripción no puede estar vacía"}, status_code=400)
        tasks[tarea_id]["descripcion"] = descripcion

    if payload.estado is not None:
        if payload.estado not in VALID_ESTADOS:
            return JSONResponse({"error": "Estado inválido"}, status_code=400)
        tasks[tarea_id]["estado"] = payload.estado

    return tasks[tarea_id]


@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    """Elimina una tarea por id; si no existe devuelve 404 con mensaje JSON."""
    if tarea_id not in tasks:
        return JSONResponse({"error": "La tarea no existe"}, status_code=404)
    del tasks[tarea_id]
    return {"message": "Tarea eliminada"}
