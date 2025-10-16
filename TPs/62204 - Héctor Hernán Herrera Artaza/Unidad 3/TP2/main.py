from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import Literal
from datetime import datetime
app = FastAPI()

class Tarea(BaseModel):
    id: int 
    description: str
    estado: Literal ["pendiente", "en_progreso", "completada"]

tareas = [] 
@app.get("/tareas")
def obtener_tareas(estado: str | None = None, texto: str | None = None):
    resultado = tareas
    if estado:
        resultado = [tarea for tarea in resultado if tarea.estado == estado]
    if texto:
        resultado = [tarea for tarea in resultado if texto.lower() in tarea.description.lower()]
        
    return tareas

@app.post ("/Tarea")
def agregar_tarea(tarea: Tarea):
    if not tarea.description.strip():
        raise HTTPException(status_code=400, detail="La descripcion no puede estar vacia")
    nueva_tarea = {
        "id": len(tareas) + 1,
        "description": tarea.description,
        "estado": "pendiente",
        "fecha_creacion": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    }
    tareas.append(tarea)
    return {"mensaje":"tarea agregada correctamente", "tarea": tarea}

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea_actualizada: Tarea):
    for index, tarea in enumerate(tareas):
        if tarea.id == id:
            if not tarea_actualizada.description.strip():
                raise HTTPException(status_code=400, detail="La descripcion no puede estar vacia")
            tareas[index] = tarea_actualizada
            return {"mensaje": "tarea actualizada correctamente", "tarea": tarea_actualizada}
    raise HTTPException(status_code=404, detail="Tarea no encontrada")

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for index, tarea in enumerate(tareas):
        if tarea.id == id:
            tareas.pop(index)
            return {"mensaje": "tarea eliminada correctamente"}
    raise HTTPException(status_code=404, detail="Tarea no encontrada")


