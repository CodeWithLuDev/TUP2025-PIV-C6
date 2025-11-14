from pydantic import BaseModel, constr
from typing import Optional, List
from enum import Enum
from datetime import datetime

class EstadoEnum(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

class PrioridadEnum(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"

# --- Modelos de Proyectos ---

class ProyectoBase(BaseModel):
    nombre: constr(strip_whitespace=True, min_length=1)
    descripcion: Optional[str] = None

class ProyectoCreate(ProyectoBase):
    pass

class ProyectoUpdate(BaseModel):
    nombre: Optional[constr(strip_whitespace=True, min_length=1)] = None
    descripcion: Optional[str] = None

class Proyecto(ProyectoBase):
    id: int
    fecha_creacion: str

    class Config:
        from_attributes = True

class ProyectoConTareas(Proyecto):
    total_tareas: int

# --- Modelos de Tareas ---

class TareaBase(BaseModel):
    descripcion: constr(strip_whitespace=True, min_length=1)
    estado: EstadoEnum = EstadoEnum.pendiente
    prioridad: PrioridadEnum = PrioridadEnum.media

class TareaCreate(TareaBase):
    pass

class TareaUpdate(BaseModel):
    descripcion: Optional[constr(strip_whitespace=True, min_length=1)] = None
    estado: Optional[EstadoEnum] = None
    prioridad: Optional[PrioridadEnum] = None
    proyecto_id: Optional[int] = None

class Tarea(TareaBase):
    id: int
    fecha_creacion: str
    proyecto_id: int

    class Config:
        from_attributes = True