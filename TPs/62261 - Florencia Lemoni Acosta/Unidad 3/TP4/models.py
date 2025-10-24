from pydantic import BaseModel, Field
from typing import Optional, Literal


# ==================== MODELOS DE PROYECTOS ====================

class ProyectoCreate(BaseModel):
    """Modelo para crear un nuevo proyecto"""
    nombre: str = Field(..., min_length=1, description="Nombre del proyecto")
    descripcion: Optional[str] = Field(None, description="Descripción opcional del proyecto")
    
    class Config:
        json_schema_extra = {
            "example": {
                "nombre": "Proyecto Alpha",
                "descripcion": "Desarrollo de aplicación web"
            }
        }


class ProyectoUpdate(BaseModel):
    """Modelo para actualizar un proyecto existente"""
    nombre: Optional[str] = Field(None, min_length=1)
    descripcion: Optional[str] = None


# ==================== MODELOS DE TAREAS ====================

class TareaCreate(BaseModel):
    """Modelo para crear una nueva tarea"""
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: Literal["pendiente", "en_progreso", "completada"] = Field(
        default="pendiente", 
        description="Estado actual de la tarea"
    )
    prioridad: Literal["baja", "media", "alta"] = Field(
        default="media",
        description="Nivel de prioridad"
    )
    
    class Config:
        json_schema_extra = {
            "example": {
                "descripcion": "Implementar sistema de login",
                "estado": "pendiente",
                "prioridad": "alta"
            }
        }


class TareaUpdate(BaseModel):
    """Modelo para actualizar una tarea existente"""
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    proyecto_id: Optional[int] = Field(None, description="ID del proyecto al que pertenece")