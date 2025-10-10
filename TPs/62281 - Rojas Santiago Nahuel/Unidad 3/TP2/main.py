from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, validator
from typing import Literal, Optional
from datetime import datetime

app = FastAPI()

class tarea_entrada(BaseModel):
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"

    @validator('descripcion')
    def validate_descripcion(cls, v):
        v = v.strip()
        if not v:
            raise ValueError("descripcion vacia")
        return v

class tarea_actualizacion(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None

    @validator('descripcion')
    def validate_descripcion(cls, v):
        if v is not None:
            v = v.strip()
            if not v:
                raise ValueError("descripcion vacia")
        return v

class tarea_objeto(tarea_entrada):
    id: int
    fecha_creacion: str

tareas_db = []
contador_id = 1
estados_validos = {"pendiente", "en_progreso", "completada"}

@app.get("/tareas")
def obtener_todas_las_tareas(estado: str = Query(None), texto: str = Query(None)):
    resultado = tareas_db
    if estado:
        if estado not in estados_validos:
            raise HTTPException(status_code=400, detail={"error": "estado invalido"})
        resultado = [t for t in resultado if t.estado == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]
    return resultado

@app.post("/tareas", status_code=201)
def agregar_tarea(nueva_tarea: tarea_entrada):
    global contador_id
    tarea_nueva = tarea_objeto(
        id=contador_id,
        descripcion=nueva_tarea.descripcion,
        estado=nueva_tarea.estado,
        fecha_creacion=datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    )
    tareas_db.append(tarea_nueva)
    contador_id += 1
    return tarea_nueva

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, datos_nuevos: tarea_actualizacion):
    for t in tareas_db:
        if t.id == id:
            if datos_nuevos.descripcion is not None:
                t.descripcion = datos_nuevos.descripcion
            if datos_nuevos.estado is not None:
                t.estado = datos_nuevos.estado
            return t
    raise HTTPException(status_code=404, detail={"error": "tarea no existe"})

@app.delete("/tareas/{id}", status_code=200)
def borrar_tarea(id: int):
    for i, t in enumerate(tareas_db):
        if t.id == id:
            del tareas_db[i]
            return {"mensaje": "tarea eliminada"}
    raise HTTPException(status_code=404, detail={"error": "tarea no existe"})

@app.get("/tareas/resumen")
def resumen_por_estado():
    resumen = {estado: 0 for estado in estados_validos}
    for t in tareas_db:
        resumen[t.estado] += 1
    return resumen

@app.put("/tareas/completar_todas")
def marcar_todas_completadas():
    if not tareas_db:
        return {"mensaje": "No hay tareas para completar"}
    for t in tareas_db:
        t.estado = "completada"
    return {"mensaje": "todas las tareas fueron completadas"}