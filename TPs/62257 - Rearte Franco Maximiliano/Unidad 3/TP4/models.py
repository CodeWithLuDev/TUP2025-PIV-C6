from pydantic import BaseModel, Field
from typing import Optional, Literal

class ProyectoCreate(BaseModel):
    nombre: str = Field(..., min_length=1, description="Nombre del proyecto, no puede estar vacío")
    descripcion: Optional[str] = Field(None, description="Descripción opcional del proyecto")

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1, description="Nuevo nombre del proyecto")
    descripcion: Optional[str] = Field(None, description="Nueva descripción del proyecto")

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: Literal["pendiente", "en_progreso", "completada"] = Field("pendiente", description="Estado de la tarea")
    prioridad: Optional[Literal["baja", "media", "alta"]] = Field(None, description="Prioridad de la tarea")

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1, description="Nueva descripción de la tarea")
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Field(None, description="Nuevo estado de la tarea")
    prioridad: Optional[Literal["baja", "media", "alta"]] = Field(None, description="Nueva prioridad de la tarea")
    proyecto_id: Optional[int] = Field(None, description="ID del nuevo proyecto al que mover la tarea")