from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional
from datetime import datetime

app = FastAPI()

tareas_db = []
contador_id = 1
ESTADOS_VALIDOS = ["pendiente", "en_progreso", "completada"]

class TareaCreate(BaseModel):
    descripcion: str
    estado: str = "pendiente"
    
    @field_validator('descripcion')
    def validar_descripcion(cls, v):
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía')
        return v
    
    @field_validator('estado')
    def validar_estado(cls, v):
        if v not in ESTADOS_VALIDOS:
            raise ValueError(f'Estado inválido. Debe ser uno de: {", ".join(ESTADOS_VALIDOS)}')
        return v

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    
    @field_validator('descripcion')
    def validar_descripcion(cls, v):
        if v is not None and v.strip() == "":
            raise ValueError('La descripción no puede estar vacía')
        return v
    
    @field_validator('estado')
    def validar_estado(cls, v):
        if v is not None and v not in ESTADOS_VALIDOS:
            raise ValueError(f'Estado inválido. Debe ser uno de: {", ".join(ESTADOS_VALIDOS)}')
        return v


@app.get("/")
def saludar():
    return {'mensaje': 'Bienvenido al servidor'}

@app.get("/tareas")
def obtener_tareas(estado: Optional[str] = None, texto: Optional[str] = None):
    tareas_filtradas = tareas_db.copy()
    if estado:
        tareas_filtradas = [t for t in tareas_filtradas if t["estado"] == estado]
    if texto:
        tareas_filtradas = [t for t in tareas_filtradas if texto.lower() in t["descripcion"].lower()]
    return tareas_filtradas

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
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

@app.get("/tareas/{tarea_id}")
def obtener_tarea(tarea_id: int):
    for t in tareas_db:
        if t["id"] == tarea_id:
            return t
    raise HTTPException(status_code=404, detail="Tarea no encontrada")

@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int, datos: TareaUpdate):
    for t in tareas_db:
        if t["id"] == tarea_id:
            if datos.descripcion is not None:
                t["descripcion"] = datos.descripcion
            if datos.estado is not None:
                t["estado"] = datos.estado
            return t
    raise HTTPException(status_code=404, detail="Tarea no encontrada")

@app.delete("/tareas/{tarea_id}", status_code=204)
def eliminar_tarea(tarea_id: int):
    for i, t in enumerate(tareas_db):
        if t["id"] == tarea_id:
            tareas_db.pop(i)
            return
    raise HTTPException(status_code=404, detail="Tarea no encontrada")
