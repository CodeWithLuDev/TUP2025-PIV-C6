from fastapi import FastAPI, HTTPException, Query, status
from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime

app = FastAPI(title="API de Gestión de Tareas")


tareas_db = {}
contador_id = 1



class TareaCrear(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    
    @field_validator("descripcion")
    @classmethod
    def validar_descripcion(cls, v: str) -> str:
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v

class TareaActualizar(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    
    @field_validator("descripcion")
    @classmethod
    def validar_descripcion(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and not v.strip():
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v

class TareaRespuesta(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: str

class ResumenRespuesta(BaseModel):
    pendiente: int
    en_progreso: int
    completada: int



@app.get("/tareas", response_model=list[TareaRespuesta], status_code=status.HTTP_200_OK)
def obtener_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Query(None),
    texto: Optional[str] = Query(None)
):
   
    tareas = list(tareas_db.values())
    
   
    if estado:
        tareas = [t for t in tareas if t["estado"] == estado]
    
    
    if texto:
        tareas = [t for t in tareas if texto.lower() in t["descripcion"].lower()]
    
    return tareas

@app.post("/tareas", response_model=TareaRespuesta, status_code=status.HTTP_201_CREATED)
def crear_tarea(tarea: TareaCrear):
 
    global contador_id
    
    nueva_tarea = {
        "id": contador_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": datetime.now().isoformat()
    }
    
    tareas_db[contador_id] = nueva_tarea
    contador_id += 1
    
    return nueva_tarea

@app.get("/tareas/resumen", response_model=ResumenRespuesta, status_code=status.HTTP_200_OK)
def obtener_resumen():
  
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for tarea in tareas_db.values():
        resumen[tarea["estado"]] += 1
    
    return resumen

@app.put("/tareas/completar_todas", status_code=status.HTTP_200_OK)
def completar_todas_tareas():
   
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    
    for tarea in tareas_db.values():
        tarea["estado"] = "completada"
    
    return {"mensaje": f"Se completaron {len(tareas_db)} tareas"}

@app.put("/tareas/{tarea_id}", response_model=TareaRespuesta, status_code=status.HTTP_200_OK)
def actualizar_tarea(tarea_id: int, tarea: TareaActualizar):
  
    if tarea_id not in tareas_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Tarea con ID {tarea_id} no encontrada"}
        )
    
    tarea_actual = tareas_db[tarea_id]
    
   
    if tarea.descripcion is not None:
        tarea_actual["descripcion"] = tarea.descripcion
    
    if tarea.estado is not None:
        tarea_actual["estado"] = tarea.estado
    
    return tarea_actual

@app.delete("/tareas/{tarea_id}", status_code=status.HTTP_200_OK)
def eliminar_tarea(tarea_id: int):
   
    if tarea_id not in tareas_db:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"error": f"Tarea con ID {tarea_id} no encontrada"}
        )
    
    del tareas_db[tarea_id]
    
    return {"mensaje": f"Tarea {tarea_id} eliminada exitosamente"}



@app.get("/", status_code=status.HTTP_200_OK)
def raiz():
    
    return {
        "mensaje": "API de Gestión de Tareas",
        "version": "1.0",
        "endpoints": {
            "GET /tareas": "Obtener todas las tareas (filtros: estado, texto)",
            "POST /tareas": "Crear una nueva tarea",
            "GET /tareas/resumen": "Obtener resumen de tareas por estado",
            "PUT /tareas/completar_todas": "Marcar todas las tareas como completadas",
            "PUT /tareas/{id}": "Actualizar una tarea específica",
            "DELETE /tareas/{id}": "Eliminar una tarea específica"
        }
    }