from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal

app = FastAPI()

tareas = []
contador = 1

class Tarea(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = "pendiente"

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: Tarea):
    global contador
    if tarea.estado not in ["pendiente", "en_progreso", "completada"]:
        raise HTTPException(status_code=400, detail="Estado inválido")
    nueva_tarea = {"id": contador, "descripcion": tarea.descripcion.strip(), "estado": tarea.estado}
    tareas.append(nueva_tarea)
    contador += 1
    return nueva_tarea

@app.get("/tareas")
def obtener_tareas():
    return tareas

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea_actualizada: dict):
    for t in tareas:
        if t["id"] == id:
            if "descripcion" in tarea_actualizada:
                t["descripcion"] = tarea_actualizada["descripcion"]
            if "estado" in tarea_actualizada:
                if tarea_actualizada["estado"] not in ["pendiente", "en_progreso", "completada"]:
                    raise HTTPException(status_code=400, detail="Estado inválido")
                t["estado"] = tarea_actualizada["estado"]
            return t
    raise HTTPException(status_code=404, detail="La tarea no existe")

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for t in tareas:
        if t["id"] == id:
            tareas.remove(t)
            return {"mensaje": "Tarea eliminada"}
    raise HTTPException(status_code=404, detail="La tarea no existe")

@app.get("/tareas/resumen")
def resumen_tareas():
    total = len(tareas)
    completadas = len([t for t in tareas if t["estado"] == "completada"])
    pendientes = len([t for t in tareas if t["estado"] == "pendiente"])
    en_progreso = len([t for t in tareas if t["estado"] == "en_progreso"])
    return {
        "total": total,
        "completadas": completadas,
        "pendientes": pendientes,
        "en_progreso": en_progreso
    }

@app.put("/tareas/completar_todas", status_code=200)
def completar_todas():
    if not tareas:
        return {"mensaje": "No hay tareas para completar"}
    for t in tareas:
        t["estado"] = "completada"
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}

