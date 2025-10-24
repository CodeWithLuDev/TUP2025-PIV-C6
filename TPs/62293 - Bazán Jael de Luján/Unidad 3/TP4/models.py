from pydantic import BaseModel, Field, validator
from typing import Optional, Literal

class ProyectoCreate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

    @validator("nombre")
    def nombre_no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v

class ProyectoUpdate(BaseModel):
    nombre: str
    descripcion: Optional[str] = None

    @validator("nombre")
    def nombre_no_vacio(cls, v):
        if not v.strip():
            raise ValueError("El nombre no puede estar vacío")
        return v

class TareaCreate(BaseModel):
    descripcion: str
    estado: Optional[Literal["pendiente","en_progreso","completada"]] = "pendiente"
    prioridad: Optional[Literal["baja","media","alta"]] = "media"
    proyecto_id: Optional[int] = None

    @validator("descripcion")
    def descripcion_no_vacia(cls, v):
        if not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v

class TareaUpdate(BaseModel):
    descripcion: Optional[str]
    estado: Optional[Literal["pendiente","en_progreso","completada"]]
    prioridad: Optional[Literal["baja","media","alta"]]
    proyecto_id: Optional[int]
