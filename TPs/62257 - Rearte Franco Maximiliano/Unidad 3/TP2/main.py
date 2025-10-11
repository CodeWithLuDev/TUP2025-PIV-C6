from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import List, Literal, Optional
from datetime import datetime

app = FastAPI()

# Almacenamiento en memoria
tareas_db = []
contador_id = 1

# Modelos
class TareaModelo(BaseModel):
    id: int
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"]
    fecha_creacion: str

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return v

class TareaEntrada(BaseModel):
    descripcion: str
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = "pendiente"

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return v

class TareaModificar(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or v.strip() == ""):
            raise ValueError("La descripción no puede estar vacía")
        return v

class Respuesta(BaseModel):
    mensaje: str

# Rutas fijas primero
@app.get("/tareas/resumen")
def contar_estados():
    conteo = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for tarea in tareas_db:
        conteo[tarea["estado"]] += 1
    return conteo

@app.put("/tareas/completar_todas")
def completar_todo():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    for tarea in tareas_db:
        tarea["estado"] = "completada"
    return {"mensaje": "Todas las tareas completadas"}

# Rutas dinámicas después
@app.get("/tareas", response_model=List[TareaModelo])
def obtener_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Query(None),
    texto: Optional[str] = Query(None)
):
    tareas = tareas_db
    if estado:
        tareas = [t for t in tareas if t["estado"] == estado]
    if texto:
        texto = texto.lower()
        tareas = [t for t in tareas if texto in t["descripcion"].lower()]
    return tareas

@app.post("/tareas", response_model=TareaModelo, status_code=201)
def agregar_tarea(tarea: TareaEntrada):
    global contador_id
    nueva_tarea = {
        "id": contador_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado or "pendiente",
        "fecha_creacion": datetime.now().isoformat()
    }
    tareas_db.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea

@app.put("/tareas/{id}", response_model=TareaModelo)
def modificar_tarea(id: int, tarea_mod: TareaModificar):
    for tarea in tareas_db:
        if tarea["id"] == id:
            if tarea_mod.descripcion is not None:
                tarea["descripcion"] = tarea_mod.descripcion
            if tarea_mod.estado is not None:
                tarea["estado"] = tarea_mod.estado
            return tarea
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

@app.delete("/tareas/{id}", response_model=Respuesta)
def borrar_tarea(id: int):
    for i, tarea in enumerate(tareas_db):
        if tarea["id"] == id:
            tareas_db.pop(i)
            return Respuesta(mensaje="Tarea eliminada")
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})