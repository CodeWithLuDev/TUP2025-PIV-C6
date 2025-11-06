from pydantic import BaseModel, Field, validator
from typing import Optional

# ============== MODELOS DE PROYECTOS ==============

class ProyectoCreate(BaseModel):
    """Modelo para crear un nuevo proyecto"""
    nombre: str = Field(..., min_length=1)
    descripcion: Optional[str] = None
    
    @validator('nombre')
    def validate_nombre(cls, v):
        if not v or v.strip() == "":
            raise ValueError('El nombre no puede estar vacío')
        return v.strip()

class ProyectoUpdate(BaseModel):
    """Modelo para actualizar un proyecto existente"""
    nombre: Optional[str] = None
    descripcion: Optional[str] = None
    
    @validator('nombre')
    def validate_nombre(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError('El nombre no puede estar vacío')
        return v.strip() if v else v

class ProyectoResponse(BaseModel):
    """Modelo de respuesta para proyectos"""
    id: int
    nombre: str
    descripcion: Optional[str]
    fecha_creacion: str
    total_tareas: Optional[int] = None

# ============== MODELOS DE TAREAS ==============

class TareaCreate(BaseModel):
    """Modelo para crear una nueva tarea"""
    descripcion: str = Field(..., min_length=1)
    estado: Optional[str] = "pendiente"
    prioridad: Optional[str] = "media"
    
    @validator('descripcion')
    def validate_descripcion(cls, v):
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()
    
    @validator('estado')
    def validate_estado(cls, v):
        estados_validos = ["pendiente", "en_progreso", "completada"]
        if v not in estados_validos:
            raise ValueError(f'Estado debe ser uno de: {", ".join(estados_validos)}')
        return v
    
    @validator('prioridad')
    def validate_prioridad(cls, v):
        prioridades_validas = ["baja", "media", "alta"]
        if v not in prioridades_validas:
            raise ValueError(f'Prioridad debe ser una de: {", ".join(prioridades_validas)}')
        return v

class TareaUpdate(BaseModel):
    """Modelo para actualizar una tarea existente"""
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    prioridad: Optional[str] = None
    proyecto_id: Optional[int] = None
    
    @validator('estado')
    def validate_estado(cls, v):
        if v is not None:
            estados_validos = ["pendiente", "en_progreso", "completada"]
            if v not in estados_validos:
                raise ValueError(f'Estado debe ser uno de: {", ".join(estados_validos)}')
        return v
    
    @validator('prioridad')
    def validate_prioridad(cls, v):
        if v is not None:
            prioridades_validas = ["baja", "media", "alta"]
            if v not in prioridades_validas:
                raise ValueError(f'Prioridad debe ser una de: {", ".join(prioridades_validas)}')
        return v

class TareaResponse(BaseModel):
    """Modelo de respuesta para tareas"""
    id: int
    descripcion: str
    estado: str
    prioridad: str
    fecha_creacion: str
    proyecto_id: int