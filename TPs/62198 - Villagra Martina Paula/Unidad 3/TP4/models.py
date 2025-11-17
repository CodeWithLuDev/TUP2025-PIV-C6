from pydantic import BaseModel
from typing import Optional, Literal, List, Dict, Any

# MODELOS
class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

class ProyectoOut(BaseModel):
    id: int
    nombre: str
    descripcion: str
    fecha_creacion: str

class TareaCreate(BaseModel):
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    proyectoId: int

class TareaOut(BaseModel):
    id: int
    descripcion: str
    estado: str
    prioridad: str
    proyectoId: int
    fecha_creacion: str
