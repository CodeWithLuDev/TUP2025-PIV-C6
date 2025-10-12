from fastapi import FastAPI, HTTPException, Request, Body
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, field_validator
from datetime import datetime, timezone
from typing import Optional, List

app = FastAPI()

tareas_db: List["Tarea"] = []
contador_id = 1
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}

class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: datetime

class TareaInput(BaseModel):
    descripcion: Optional[str] = Field(default=None)
    estado: Optional[str] = Field(default=None)

    @field_validator("descripcion")
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and not v.strip():
            raise ValueError("descripcion no puede estar vacía")
        return v.strip() if v is not None else v

    @field_validator("estado")
    @classmethod
    def validar_estado(cls, v):
        if v is not None and v not in ESTADOS_VALIDOS:
            raise ValueError("estado inválido")
        return v

@app.exception_handler(ValueError)
async def value_error_handler(request: Request, exc: ValueError):
    return JSONResponse(
        status_code=422,
        content={"detail": f"error: {str(exc)}"}
    )

@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": f"error: {exc.detail}" if exc.status_code in [404, 422] else exc.detail}
    )

@app.get("/tareas")
def obtener_tareas(estado: Optional[str] = None, texto: Optional[str] = None):
    resultados = tareas_db
    if estado:
        resultados = [t for t in resultados if t.estado == estado]
    if texto:
        resultados = [t for t in resultados if texto.lower() in t.descripcion.lower()]
    return resultados

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaInput):
    global contador_id
    if tarea.descripcion is None:
        raise HTTPException(status_code=422, detail="error: descripcion no puede estar vacía")
    nueva = Tarea(
        id=contador_id,
        descripcion=tarea.descripcion,
        estado=tarea.estado or "pendiente",
        fecha_creacion=datetime.now(timezone.utc)
    )
    tareas_db.append(nueva)
    contador_id += 1
    return nueva

@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int, datos: TareaInput):
    tarea = next((t for t in tareas_db if t.id == tarea_id), None)
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    if datos.descripcion is not None:
        tarea.descripcion = datos.descripcion
    if datos.estado is not None:
        tarea.estado = datos.estado
    return tarea

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    global tareas_db
    tarea = next((t for t in tareas_db if t.id == tarea_id), None)
    if not tarea:
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    tareas_db = [t for t in tareas_db if t.id != tarea_id]
    return {"mensaje": "Tarea eliminada"}

@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {estado: 0 for estado in ESTADOS_VALIDOS}
    for t in tareas_db:
        resumen[t.estado] += 1
    return resumen

@app.put("/tareas/completar_todas")
def completar_todas(body: Optional[dict] = Body(default=None)):
    for t in tareas_db:
        t.estado = "completada"
    return {"mensaje": "Todas las tareas fueron completadas"}
