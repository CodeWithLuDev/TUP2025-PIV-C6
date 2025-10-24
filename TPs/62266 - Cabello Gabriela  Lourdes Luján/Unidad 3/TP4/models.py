import re
from pydantic import BaseModel, field_validator
from typing import Optional, Literal, Dict

class ProyectoBase(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class ProyectoCreate(ProyectoBase):
    @field_validator('nombre')
    @classmethod
    def nombre_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('El nombre del proyecto no puede estar vacío.')
        return v.strip()

class Proyecto(ProyectoBase):
    id: int
    fecha_creacion: str
    total_tareas: Optional[int] = 0
    
    class Config:
        from_attributes = True 

# TareaUpdate ahora hereda de BaseModel y todos los campos son opcionales para permitir el PUT parcial
class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = None
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_must_not_be_empty(cls, v):
        if v is not None and not v.strip(): # Solo validar si el campo fue enviado
            raise ValueError('La descripción de la tarea no puede estar vacía.')
        return v.strip() if v is not None else v

class TareaCreate(BaseModel):
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    @field_validator('descripcion')
    @classmethod
    def descripcion_must_not_be_empty(cls, v):
        if not v or not v.strip():
            raise ValueError('La descripción de la tarea no puede estar vacía.')
        return v.strip()

class Tarea(TareaCreate):
    id: int
    proyecto_id: int
    fecha_creacion: str
    
    class Config:
        from_attributes = True