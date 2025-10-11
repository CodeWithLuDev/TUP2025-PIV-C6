from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional
from datetime import datetime

# Crear la aplicación FastAPI
app = FastAPI(title="Mini API de Tareas")

# Modelo para una tarea usando Pydantic (valida los datos automáticamente)
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: datetime

# Modelo para crear/editar tareas (sin incluir id ni fecha_creacion, ya que se generan automáticamente)
class TareaInput(BaseModel):
    descripcion: str
    estado: str

# Lista en memoria para almacenar tareas
tareas: List[Tarea] = []
# Contador para generar IDs únicos
ultimo_id = 0

# Lista de estados válidos
ESTADOS_VALIDOS = ["pendiente", "en_progreso", "completada"]

# Endpoint raíz
@app.get("/")
async def root():
    return {"mensaje": "Bienvenido a la Mini API de Tareas"}

# GET /tareas: Obtener todas las tareas
@app.get("/tareas", response_model=List[Tarea])
async def obtener_tareas():
    return tareas

# POST /tareas: Crear una nueva tarea
@app.post("/tareas", response_model=Tarea)
async def crear_tarea(tarea: TareaInput):
    # Validar que la descripción no esté vacía
    if not tarea.descripcion.strip():
        raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
    
    # Validar que el estado sea válido
    if tarea.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail={"error": f"El estado debe ser uno de: {', '.join(ESTADOS_VALIDOS)}"})
    
    global ultimo_id
    ultimo_id += 1
    nueva_tarea = Tarea(
        id=ultimo_id,
        descripcion=tarea.descripcion,
        estado=tarea.estado,
        fecha_creacion=datetime.now()
    )
    tareas.append(nueva_tarea)
    return nueva_tarea

# PUT /tareas/{id}: Actualizar una tarea existente
@app.put("/tareas/{id}", response_model=Tarea)
async def actualizar_tarea(id: int, tarea: TareaInput):
    # Validar que la descripción no esté vacía
    if not tarea.descripcion.strip():
        raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
    
    # Validar que el estado sea válido
    if tarea.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail={"error": f"El estado debe ser uno de: {', '.join(ESTADOS_VALIDOS)}"})
    
    # Buscar la tarea por ID
    for t in tareas:
        if t.id == id:
            t.descripcion = tarea.descripcion
            t.estado = tarea.estado
            return t
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

# DELETE /tareas/{id}: Eliminar una tarea
@app.delete("/tareas/{id}")
async def eliminar_tarea(id: int):
    # Buscar y eliminar la tarea por ID
    for i, t in enumerate(tareas):
        if t.id == id:
            tareas.pop(i)
            return {"mensaje": "Tarea eliminada correctamente"}
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

# GET /tareas?estado=...: Filtrar tareas por estado
@app.get("/tareas", response_model=List[Tarea])
async def filtrar_tareas_por_estado(estado: Optional[str] = None):
    if estado and estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail={"error": f"El estado debe ser uno de: {', '.join(ESTADOS_VALIDOS)}"})
    if estado:
        return [t for t in tareas if t.estado == estado]
    return tareas

# GET /tareas?texto=...: Buscar tareas por texto en la descripción
@app.get("/tareas", response_model=List[Tarea])
async def buscar_tareas_por_texto(texto: Optional[str] = None):
    if texto:
        return [t for t in tareas if texto.lower() in t.descripcion.lower()]
    return tareas

# GET /tareas/resumen: Contador de tareas por estado
@app.get("/tareas/resumen")
async def resumen_tareas():
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    for t in tareas:
        resumen[t.estado] += 1
    return resumen

# PUT /tareas/completar_todas: Marcar todas las tareas como completadas
@app.put("/tareas/completar_todas")
async def completar_todas():
    for t in tareas:
        t.estado = "completada"
    return {"mensaje": "Todas las tareas han sido marcadas como completadas"}