"""
Modelos Pydantic para validación de datos de la API de Tareas y Proyectos.
"""

from pydantic import BaseModel, Field
from enum import Enum
from typing import Optional


# ==================== ENUMS ====================

class EstadoTarea(str, Enum):
    """Estados válidos para una tarea"""
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"


class PrioridadTarea(str, Enum):
    """Prioridades válidas para una tarea"""
    baja = "baja"
    media = "media"
    alta = "alta"


# ==================== MODELOS DE PROYECTO ====================

class ProyectoCreate(BaseModel):
    """Modelo para crear un nuevo proyecto"""
    nombre: str = Field(..., min_length=1, description="Nombre del proyecto (no puede estar vacío)")
    descripcion: Optional[str] = Field(None, description="Descripción del proyecto (opcional)")


class ProyectoUpdate(BaseModel):
    """Modelo para actualizar un proyecto existente"""
    nombre: Optional[str] = Field(None, min_length=1, description="Nuevo nombre del proyecto")
    descripcion: Optional[str] = Field(None, description="Nueva descripción del proyecto")


class Proyecto(BaseModel):
    """Modelo de respuesta para un proyecto"""
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str
    total_tareas: int = 0  # Se calcula dinámicamente


# ==================== MODELOS DE TAREA ====================

class TareaCreate(BaseModel):
    """Modelo para crear una nueva tarea"""
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea (no puede estar vacía)")
    estado: EstadoTarea = EstadoTarea.pendiente
    prioridad: PrioridadTarea = PrioridadTarea.media


class TareaUpdate(BaseModel):
    """Modelo para actualizar una tarea existente"""
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[EstadoTarea] = None
    prioridad: Optional[PrioridadTarea] = None
    proyecto_id: Optional[int] = Field(None, description="ID del proyecto al que pertenece la tarea")


class Tarea(BaseModel):
    """Modelo de respuesta para una tarea"""
    id: int
    descripcion: str
    estado: EstadoTarea
    prioridad: PrioridadTarea
    proyecto_id: int
    proyecto_nombre: Optional[str] = None  # Se incluye en consultas con JOIN
    fecha_creacion: str


# ==================== MODELOS DE RESUMEN ====================

class ResumenProyecto(BaseModel):
    """Modelo para resumen de un proyecto específico"""
    proyecto_id: int
    proyecto_nombre: str
    total_tareas: int
    por_estado: dict
    por_prioridad: dict


class ResumenGeneral(BaseModel):
    """Modelo para resumen general de la aplicación"""
    total_proyectos: int
    total_tareas: int
    tareas_por_estado: dict
    proyecto_con_mas_tareas: Optional[dict] = None
