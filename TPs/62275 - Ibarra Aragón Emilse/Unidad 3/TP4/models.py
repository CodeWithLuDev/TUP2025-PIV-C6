from pydantic import BaseModel, Field, field_validator
from typing import Optional, Literal
from datetime import datetime

# ============== ENUMS COMO LITERALES ==============

EstadoTarea = Literal["pendiente", "en_progreso", "completada"]
PrioridadTarea = Literal["baja", "media", "alta"]

# ============== MODELOS PARA PROYECTOS ==============

class ProyectoCreate(BaseModel):
    """Modelo para crear un proyecto"""
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None
    
    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v):
        if not v or not v.strip():
            raise ValueError("El nombre no puede estar vacío o contener solo espacios")
        return v.strip()

class ProyectoUpdate(BaseModel):
    """Modelo para actualizar un proyecto"""
    nombre: Optional[str] = Field(None, min_length=1)
    descripcion: Optional[str] = None
    
    @field_validator("nombre")
    @classmethod
    def validar_nombre(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("El nombre no puede estar vacío o contener solo espacios")
        return v.strip() if v else v

class ProyectoResponse(BaseModel):
    """Modelo de respuesta para un proyecto"""
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str

class ProyectoConTareas(ProyectoResponse):
    """Modelo de respuesta para proyecto con contador de tareas"""
    total_tareas: int

# ============== MODELOS PARA TAREAS ==============

class TareaCreate(BaseModel):
    """Modelo para crear una tarea"""
    descripcion: str = Field(..., min_length=1)
    estado: EstadoTarea = "pendiente"
    prioridad: PrioridadTarea = "media"
    
    @field_validator("descripcion")
    @classmethod
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v.strip()

class TareaUpdate(BaseModel):
    """Modelo para actualizar una tarea"""
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[EstadoTarea] = None
    prioridad: Optional[PrioridadTarea] = None
    proyecto_id: Optional[int] = None
    
    @field_validator("descripcion")
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v.strip() if v else v

class TareaResponse(BaseModel):
    """Modelo de respuesta para una tarea"""
    id: int
    descripcion: str
    estado: EstadoTarea
    prioridad: PrioridadTarea
    proyecto_id: int
    fecha_creacion: str

# ============== MODELOS PARA MENSAJES ==============

class MensajeRespuesta(BaseModel):
    """Modelo para mensajes de respuesta genéricos"""
    mensaje: str

class MensajeEliminacionProyecto(BaseModel):
    """Modelo para respuesta al eliminar proyecto"""
    mensaje: str
    tareas_eliminadas: int

# ============== MODELOS PARA RESÚMENES ==============

class ResumenEstados(BaseModel):
    """Contador de tareas por estado"""
    pendiente: int = 0
    en_progreso: int = 0
    completada: int = 0

class ResumenPrioridades(BaseModel):
    """Contador de tareas por prioridad"""
    baja: int = 0
    media: int = 0
    alta: int = 0

class ResumenProyecto(BaseModel):
    """Resumen estadístico de un proyecto"""
    proyecto_id: int
    proyecto_nombre: str
    total_tareas: int
    por_estado: ResumenEstados
    por_prioridad: ResumenPrioridades

class ProyectoConMasTareas(BaseModel):
    """Información del proyecto con más tareas"""
    id: int
    nombre: str
    cantidad_tareas: int

class ResumenGeneral(BaseModel):
    """Resumen general de toda la aplicación"""
    total_proyectos: int
    total_tareas: int
    tareas_por_estado: ResumenEstados
    proyecto_con_mas_tareas: Optional[ProyectoConMasTareas] = None