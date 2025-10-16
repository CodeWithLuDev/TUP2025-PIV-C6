# Importamos las bibliotecas necesarias
from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field
from enum import Enum
from datetime import datetime
from typing import List, Optional
import sqlite3
from contextlib import contextmanager, asynccontextmanager

# Nombre de la base de datos (cambiado de DATABASE a DB_NAME)
DB_NAME = "tareas.db"

# Definimos los estados válidos usando un Enum
class EstadoTarea(str, Enum):
    pendiente = "pendiente"
    en_progreso = "en_progreso"
    completada = "completada"

# Definimos las prioridades válidas usando un Enum
class PrioridadTarea(str, Enum):
    baja = "baja"
    media = "media"
    alta = "alta"

# Modelo para una tarea (usando Pydantic para validación automática)
class Tarea(BaseModel):
    id: int
    descripcion: str
    estado: EstadoTarea
    prioridad: PrioridadTarea
    fecha_creacion: str

# Modelo para crear una tarea
class TareaCreate(BaseModel):       
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea (no puede estar vacía)")
    estado: EstadoTarea = EstadoTarea.pendiente
    prioridad: PrioridadTarea = PrioridadTarea.media

# Modelo para actualización parcial de tarea
class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[EstadoTarea] = None
    prioridad: Optional[PrioridadTarea] = None

# Context manager para manejar conexiones a la base de datos
@contextmanager
def get_db():
    """Context manager para obtener y cerrar conexiones a la BD"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    try:
        yield conn
    finally:
        conn.close()

# Función para inicializar la base de datos
def init_db():
    """Crea la tabla tareas si no existe"""
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                prioridad TEXT NOT NULL DEFAULT 'media',
                fecha_creacion TEXT NOT NULL
            )
        """)
        conn.commit()
        print("✓ Base de datos inicializada correctamente")

# Lifespan event handler (reemplaza @app.on_event)
@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código que se ejecuta al iniciar la aplicación
    init_db()
    yield
    # Código que se ejecuta al cerrar la aplicación (si es necesario)
    # Por ejemplo: cerrar conexiones, limpiar recursos, etc.

# Creamos la app de FastAPI con lifespan
app = FastAPI(
    title="API de Tareas con SQLite", 
    version="2.0",
    lifespan=lifespan
)

# Función auxiliar para convertir una fila de la BD a un diccionario
def row_to_dict(row):
    """Convierte una fila de SQLite a diccionario"""
    return {
        "id": row["id"],
        "descripcion": row["descripcion"],
        "estado": row["estado"],
        "prioridad": row["prioridad"],
        "fecha_creacion": row["fecha_creacion"]
    }

# ==================== ENDPOINTS ====================

# Endpoint raíz con información de la API
@app.get("/")
def root():
    """Información básica de la API"""
    return {
        "nombre": "API de Tareas con SQLite",
        "version": "2.0",
        "descripcion": "API REST para gestión de tareas con persistencia en SQLite",
        "endpoints": {
            "GET /tareas": "Listar todas las tareas (con filtros opcionales)",
            "POST /tareas": "Crear nueva tarea",
            "PUT /tareas/{id}": "Actualizar tarea",
            "DELETE /tareas/{id}": "Eliminar tarea",
            "GET /tareas/resumen": "Resumen completo",
            "PUT /tareas/completar_todas": "Completar todas las tareas"
        }
    }

# Ruta GET /tareas: Devuelve todas las tareas con filtros opcionales
@app.get("/tareas", response_model=List[Tarea])
def get_tareas(
    estado: Optional[EstadoTarea] = Query(None, description="Filtrar por estado"),
    texto: Optional[str] = Query(None, description="Buscar en descripción"),
    prioridad: Optional[PrioridadTarea] = Query(None, description="Filtrar por prioridad"),
    orden: Optional[str] = Query(None, pattern="^(asc|desc)$", description="Ordenar por fecha (asc/desc)")
):
    """
    Obtiene todas las tareas de la base de datos con filtros opcionales.
    
    - **estado**: Filtrar por estado (pendiente, en_progreso, completada)
    - **texto**: Buscar tareas que contengan este texto en la descripción
    - **prioridad**: Filtrar por prioridad (baja, media, alta)
    - **orden**: Ordenar por fecha de creación (asc = ascendente, desc = descendente)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Construir query dinámica
        query = "SELECT * FROM tareas WHERE 1=1"
        params = []
        
        if estado:
            query += " AND estado = ?"
            params.append(estado.value)
        
        if texto:
            query += " AND descripcion LIKE ?"
            params.append(f"%{texto}%")
        
        if prioridad:
            query += " AND prioridad = ?"
            params.append(prioridad.value)
        
        # Ordenamiento
        if orden:
            if orden == "asc":
                query += " ORDER BY fecha_creacion ASC"
            else:
                query += " ORDER BY fecha_creacion DESC"
        else:
            query += " ORDER BY id ASC"  # Orden por defecto
        
        cursor.execute(query, params)
        rows = cursor.fetchall()
        
        return [row_to_dict(row) for row in rows]

# Ruta POST /tareas: Agrega una nueva tarea
@app.post("/tareas", response_model=Tarea, status_code=201)
def create_tarea(tarea: TareaCreate):
    """
    Crea una nueva tarea en la base de datos.
    
    - **descripcion**: Descripción de la tarea (obligatorio, no puede estar vacía)
    - **estado**: Estado inicial (por defecto: pendiente)
    - **prioridad**: Prioridad de la tarea (por defecto: media)
    """
    # Validación adicional (Pydantic ya valida min_length, pero agregamos strip)
    if not tarea.descripcion.strip():
        raise HTTPException(status_code=422, detail={"error": "La descripción no puede estar vacía"})
    
    fecha_creacion = datetime.now().isoformat()
    
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute(
            """
            INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
            VALUES (?, ?, ?, ?)
            """,
            (tarea.descripcion, tarea.estado.value, tarea.prioridad.value, fecha_creacion)
        )
        conn.commit()
        tarea_id = cursor.lastrowid
        
        # Recuperar la tarea creada
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        row = cursor.fetchone()
        
        return row_to_dict(row)

# RUTAS ESTÁTICAS ANTES DE LAS DINÁMICAS

# Ruta GET /tareas/resumen: Resumen completo (CORREGIDO)
@app.get("/tareas/resumen")
def get_resumen():
    """
    Devuelve un resumen completo con:
    - total_tareas: cantidad total de tareas
    - por_estado: cantidad de tareas por cada estado
    - por_prioridad: cantidad de tareas por cada prioridad
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Total de tareas
        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total = cursor.fetchone()["total"]
        
        # Por estado
        por_estado = {
            "pendiente": 0,
            "en_progreso": 0,
            "completada": 0
        }
        cursor.execute("SELECT estado, COUNT(*) as total FROM tareas GROUP BY estado")
        rows = cursor.fetchall()
        for row in rows:
            por_estado[row["estado"]] = row["total"]
        
        # Por prioridad
        por_prioridad = {
            "baja": 0,
            "media": 0,
            "alta": 0
        }
        cursor.execute("SELECT prioridad, COUNT(*) as total FROM tareas GROUP BY prioridad")
        rows = cursor.fetchall()
        for row in rows:
            por_prioridad[row["prioridad"]] = row["total"]
        
        return {
            "total_tareas": total,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }

# Ruta PUT /tareas/completar_todas: Marca todas como completadas
@app.put("/tareas/completar_todas")
def completar_todas():
    """
    Marca todas las tareas existentes como completadas.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Contar tareas antes de actualizar
        cursor.execute("SELECT COUNT(*) as total FROM tareas")
        total = cursor.fetchone()["total"]
        
        if total == 0:
            return {"mensaje": "No hay tareas"}
        
        cursor.execute("UPDATE tareas SET estado = ?", (EstadoTarea.completada.value,))
        conn.commit()
        
        return {"mensaje": "Todas las tareas han sido marcadas como completadas"}

# RUTAS DINÁMICAS

# Ruta PUT /tareas/{id}: Modifica una tarea existente
@app.put("/tareas/{id}", response_model=Tarea)
def update_tarea(id: int, tarea_update: TareaUpdate):
    """
    Actualiza una tarea existente.
    
    - **id**: ID de la tarea a actualizar
    - **descripcion**: Nueva descripción (opcional)
    - **estado**: Nuevo estado (opcional)
    - **prioridad**: Nueva prioridad (opcional)
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que la tarea existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea_actual = cursor.fetchone()
        
        if not tarea_actual:
            raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
        
        # Construir actualización dinámica
        updates = []
        params = []
        
        if tarea_update.descripcion is not None:
            if not tarea_update.descripcion.strip():
                raise HTTPException(status_code=422, detail={"error": "La descripción no puede estar vacía"})
            updates.append("descripcion = ?")
            params.append(tarea_update.descripcion)
        
        if tarea_update.estado is not None:
            updates.append("estado = ?")
            params.append(tarea_update.estado.value)
        
        if tarea_update.prioridad is not None:
            updates.append("prioridad = ?")
            params.append(tarea_update.prioridad.value)
        
        if not updates:
            # No hay nada que actualizar, devolver la tarea actual
            return row_to_dict(tarea_actual)
        
        params.append(id)
        query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        
        cursor.execute(query, params)
        conn.commit()
        
        # Recuperar la tarea actualizada
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        row = cursor.fetchone()
        
        return row_to_dict(row)

# Ruta DELETE /tareas/{id}: Elimina una tarea
@app.delete("/tareas/{id}")
def delete_tarea(id: int):
    """
    Elimina una tarea de la base de datos.
    
    - **id**: ID de la tarea a eliminar
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Verificar que la tarea existe
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        tarea = cursor.fetchone()
        
        if not tarea:
            raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
        
        cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
        conn.commit()
        
        return {"mensaje": "Tarea eliminada"}
