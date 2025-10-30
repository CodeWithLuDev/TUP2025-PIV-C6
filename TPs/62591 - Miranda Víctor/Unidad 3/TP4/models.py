from pydantic import BaseModel, Field
from typing import Optional, Literal


class ProyectoCreate(BaseModel):
    """Modelo para crear un proyecto"""
    nombre: str = Field(..., min_length=1, description="Nombre del proyecto")
    descripcion: Optional[str] = Field(None, description="Descripción opcional del proyecto")

class ProyectoUpdate(BaseModel):
    """Modelo para actualizar un proyecto"""
    nombre: Optional[str] = Field(None, min_length=1)
    descripcion: Optional[str] = None


class TareaCreate(BaseModel):
    """Modelo para crear una tarea"""
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: Literal["pendiente", "en_progreso", "completada"] = Field(..., description="Estado de la tarea")
    prioridad: Literal["baja", "media", "alta"] = Field(..., description="Prioridad de la tarea")

class TareaUpdate(BaseModel):
    """Modelo para actualizar una tarea"""
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = Field(None, description="ID del proyecto (para mover la tarea)")