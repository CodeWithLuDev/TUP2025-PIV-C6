from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime

app = FastAPI(title="Mini API de Tareas", version="1.0.0")

class TareaCrear(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    
    @validator('descripcion')
    def validar_descripcion(cls, v):
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()

class TareaActualizar(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    
    @validator('descripcion')
    def validar_descripcion(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError('La descripción no puede estar vacía')
        return v.strip() if v else v

tareas_db = []
contador_id = 1

@app.get("/")
def root():
    return {
        "mensaje": "Bienvenido a la Mini API de Tareas",
        "rutas_disponibles": {
            "GET /tareas": "Obtener todas las tareas (con filtros opcionales)",
            "POST /tareas": "Crear una nueva tarea",
            "PUT /tareas/{id}": "Actualizar una tarea",
            "DELETE /tareas/{id}": "Eliminar una tarea",
            "GET /tareas/resumen": "Obtener resumen de tareas por estado",
            "PUT /tareas/completar_todas": "Marcar todas las tareas como completadas"
        }
    }

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

@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    tareas_actualizadas = 0
    for tarea in tareas_db:
        if tarea["estado"] != "completada":
            tarea["estado"] = "completada"
            tareas_actualizadas += 1
    return {
        "mensaje": f"Se completaron {tareas_actualizadas} tareas",
        "total_tareas": len(tareas_db)
    }

@app.get("/tareas")
def obtener_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Query(None),
    texto: Optional[str] = Query(None)
):
    tareas_filtradas = tareas_db.copy()
    if estado:
        tareas_filtradas = [t for t in tareas_filtradas if t["estado"] == estado]
    if texto:
        texto_lower = texto.lower()
        tareas_filtradas = [
            t for t in tareas_filtradas 
            if texto_lower in t["descripcion"].lower()
        ]
    return tareas_filtradas

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCrear):
    global contador_id
    nueva_tarea = {
        "id": contador_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": datetime.now().isoformat()
    }
    tareas_db.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea

@app.get("/tareas/{id}")
def obtener_tarea(id: int):
    tarea = next((t for t in tareas_db if t["id"] == id), None)
    if not tarea:
        raise HTTPException(
            status_code=404,
            detail={"error": "La tarea no existe"}
        )
    return tarea

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea_actualizada: TareaActualizar):
    tarea = next((t for t in tareas_db if t["id"] == id), None)
    if not tarea:
        raise HTTPException(
            status_code=404,
            detail={"error": "La tarea no existe"}
        )
    if tarea_actualizada.descripcion is not None:
        tarea["descripcion"] = tarea_actualizada.descripcion
    if tarea_actualizada.estado is not None:
        tarea["estado"] = tarea_actualizada.estado
    return tarea

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    tarea = next((t for t in tareas_db if t["id"] == id), None)
    if not tarea:
        raise HTTPException(
            status_code=404,
            detail={"error": "La tarea no existe"}
        )
    tareas_db.remove(tarea)
    return {
        "mensaje": "Tarea eliminada exitosamente",
        "tarea_eliminada": tarea
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
