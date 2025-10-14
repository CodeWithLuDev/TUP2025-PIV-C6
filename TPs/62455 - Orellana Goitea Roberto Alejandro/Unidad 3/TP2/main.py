# Importamos las bibliotecas necesarias
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel
from enum import Enum
from datetime import datetime
from typing import List, Optional

# Creamos la app de FastAPI
app = FastAPI()

# Definimos los estados válidos usando un Enum (para restringir valores)
class EstadoTarea(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

# Modelo para una tarea (usando Pydantic para validación automática)
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: EstadoTarea
    fecha_creacion: str  # Lo guardamos como string para simplicidad en JSON

# Modelo para actualización parcial de tarea
class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[EstadoTarea] = None

# Modelo para crear o actualizar una tarea (sin id ni fecha, ya que se generan automáticamente)
class TareaCreate(BaseModel):       
    descripcion: str
    estado: EstadoTarea = EstadoTarea.pendiente  # Estado por defecto

# Almacenamiento en memoria: una lista de tareas
tareas_db: List[Tarea] = []

# Contador para generar IDs automáticos
contador_id = 1

# Ruta GET /tareas: Devuelve todas las tareas, con filtros opcionales
@app.get("/tareas", response_model=List[Tarea])
def get_tareas(estado: Optional[EstadoTarea] = Query(None), texto: Optional[str] = Query(None)):
    resultado = tareas_db
    if estado:
        resultado = [t for t in resultado if t.estado == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]
    return resultado

# Ruta POST /tareas: Agrega una nueva tarea
@app.post("/tareas", response_model=Tarea, status_code=201)
def create_tarea(tarea: TareaCreate):
    if not tarea.descripcion.strip():  # Validamos que la descripción no esté vacía
        raise HTTPException(status_code=422, detail={"error": "La descripción no puede estar vacía"})
    global contador_id
    nueva_tarea = Tarea(
        id=contador_id,
        descripcion=tarea.descripcion,
        estado=tarea.estado,
        fecha_creacion=datetime.now().isoformat()
    )
    tareas_db.append(nueva_tarea)
    contador_id += 1
    return nueva_tarea
# Ruta PUT /tareas/completar_todas: Marca todas como completadas
@app.put("/tareas/completar_todas")
def completar_todas():
    # Actualizar todas las tareas
    for tarea in tareas_db:
        tarea.estado = EstadoTarea.completada
    
    # Devolver mensaje apropiado
    if not tareas_db:
        return {"mensaje": "No hay tareas"}
    return {"mensaje": "Todas las tareas han sido marcadas como completadas"}

# Ruta PUT /tareas/{id}: Modifica una tarea existente
@app.put("/tareas/{id}", response_model=Tarea)
def update_tarea(id: int, tarea_update: TareaUpdate):
    for i, t in enumerate(tareas_db):
        if t.id == id:
            # Crear un diccionario con los valores actuales
            tarea_dict = {
                "id": id,
                "descripcion": t.descripcion,
                "estado": t.estado,
                "fecha_creacion": t.fecha_creacion
            }
            
            # Actualizar solo los campos proporcionados
            if tarea_update.descripcion is not None:
                if not tarea_update.descripcion.strip():
                    raise HTTPException(status_code=422, detail={"error": "La descripción no puede estar vacía"})
                tarea_dict["descripcion"] = tarea_update.descripcion
            if tarea_update.estado is not None:
                tarea_dict["estado"] = tarea_update.estado
            
            # Crear la tarea actualizada
            tareas_db[i] = Tarea(**tarea_dict)
            return tareas_db[i]
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

# Ruta PUT /tareas/completar_todas: Marca todas como completadas
@app.put("/tareas/completar_todas")
def completar_todas():
    # Actualizar todas las tareas
    for tarea in tareas_db:
        tarea.estado = EstadoTarea.completada
    
    # Devolver mensaje apropiado
    if not tareas_db:
        return {"mensaje": "No hay tareas"}
    return {"mensaje": "Todas las tareas han sido marcadas como completadas"}

# Ruta DELETE /tareas/{id}: Elimina una tarea
@app.delete("/tareas/{id}")
def delete_tarea(id: int):
    for i, t in enumerate(tareas_db):
        if t.id == id:
            del tareas_db[i]
            return {"mensaje": "Tarea eliminada"}
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

# Ruta GET /tareas/resumen: Contador de tareas por estado
@app.get("/tareas/resumen")
def get_resumen():
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    for t in tareas_db:
        resumen[t.estado.value] += 1
    return resumen

# Respuesta para el endpoint completar_todas
from typing import Dict

# Ruta PUT /tareas/completar_todas: Marca todas como completadas
@app.put("/tareas/completar_todas", response_model=Dict[str, str])
def completar_todas():
    # Actualizar todas las tareas
    for tarea in tareas_db:
        tarea.estado = EstadoTarea.completada
    
    # Devolver mensaje apropiado
    if not tareas_db:
        return {"mensaje": "No hay tareas"}
    return {"mensaje": "Todas las tareas han sido marcadas como completadas"}