from pydantic import BaseModel, Field
from typing import Optional, Literal

class ProyectoCreate(BaseModel):
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = Field(None)

class ProyectoUpdate(BaseModel):
    nombre: Optional[str] = Field(None, min_length=1)
    descripcion: Optional[str] = Field(None)

class ProyectoResponse(BaseModel):
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str

class ProyectoConTareas(ProyectoResponse):
    total_tareas: int

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = Field(...)
    prioridad: Literal["baja", "media", "alta"] = Field(...)

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Field(None)
    prioridad: Optional[Literal["baja", "media", "alta"]] = Field(None)
    proyecto_id: Optional[int] = Field(None)

class TareaResponse(BaseModel):
    id: int
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"]
    prioridad: Literal["baja", "media", "alta"]
    proyecto_id: int
    fecha_creacion: str

class ResumenProyecto(BaseModel):
    proyecto_id: int
    proyecto_nombre: str
    total_tareas: int
    por_estado: dict
    por_prioridad: dict

class ProyectoConMasTareas(BaseModel):
    id: int
    nombre: str
    cantidad_tareas: int

class ResumenGeneral(BaseModel):
    total_proyectos: int
    total_tareas: int
    tareas_por_estado: dict
    proyecto_con_mas_tareas: Optional[ProyectoConMasTareas]