from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from datetime import datetime
from typing import Optional, List

app = FastAPI()

# ---------------------------
# MODELO DE DATOS
# ---------------------------
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: datetime

# ---------------------------
# BASE DE DATOS EN MEMORIA
# ---------------------------
tareas: List[Tarea] = []
contador_id = 1
ESTADOS_VALIDOS = ["pendiente", "en_progreso", "completada"]

# ---------------------------
# RUTAS CRUD
# ---------------------------

@app.get("/tareas")
def obtener_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):
    """Devuelve todas las tareas, con filtros opcionales por estado o texto."""
    resultado = tareas

    if estado:
        if estado not in ESTADOS_VALIDOS:
            raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
        resultado = [t for t in resultado if t.estado == estado]

    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]

    return resultado


@app.post("/tareas", status_code=201)
def crear_tarea(data: dict):
    """Crea una nueva tarea validando los campos."""
    global contador_id

    descripcion = data.get("descripcion", "").strip()
    estado = data.get("estado", "pendiente")

    if not descripcion:
        raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
    if estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail={"error": "Estado inválido"})

    nueva_tarea = Tarea(
        id=contador_id,
        descripcion=descripcion,
        estado=estado,
        fecha_creacion=datetime.now()
    )

    tareas.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea


@app.put("/tareas/{id}")
def modificar_tarea(id: int, data: dict):
    """Modifica una tarea existente."""
    for tarea in tareas:
        if tarea.id == id:
            descripcion = data.get("descripcion", tarea.descripcion)
            estado = data.get("estado", tarea.estado)

            if not descripcion.strip():
                raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
            if estado not in ESTADOS_VALIDOS:
                raise HTTPException(status_code=400, detail={"error": "Estado inválido"})

            tarea.descripcion = descripcion
            tarea.estado = estado
            return tarea

    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})


@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """Elimina una tarea por su id."""
    for tarea in tareas:
        if tarea.id == id:
            tareas.remove(tarea)
            return {"mensaje": "Tarea eliminada correctamente"}
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

# ---------------------------
# FUNCIONALIDADES ADICIONALES
# ---------------------------

@app.get("/tareas/resumen")
def resumen_tareas():
    """Devuelve un resumen de tareas por estado."""
    resumen = {estado: 0 for estado in ESTADOS_VALIDOS}
    for tarea in tareas:
        resumen[tarea.estado] += 1
    return resumen


@app.put("/tareas/completar_todas")
def completar_todas():
    """Marca todas las tareas como completadas."""
    for tarea in tareas:
        tarea.estado = "completada"
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}
