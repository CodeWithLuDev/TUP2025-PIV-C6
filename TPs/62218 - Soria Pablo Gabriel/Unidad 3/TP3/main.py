from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, Field
from typing import Optional, Literal
import sqlite3
from datetime import datetime

app = FastAPI(title="API de Tareas Persistente", version="1.0")

# =============================================================================
# MODELOS PYDANTIC PARA VALIDACIÓN
# =============================================================================

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None

class TareaResponse(BaseModel):
    id: int
    descripcion: str
    estado: str
    prioridad: str
    fecha_creacion: str

# =============================================================================
# FUNCIONES DE BASE DE DATOS
# =============================================================================

def get_db_connection():
    """Crea y retorna una conexión a la base de datos"""
    conn = sqlite3.connect('tareas.db')
    conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
    return conn

def init_db():
    """Inicializa la base de datos y crea la tabla si no existe"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media',
            fecha_creacion TEXT NOT NULL
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente")

# Inicializar la base de datos al arrancar la aplicación
@app.on_event("startup")
async def startup_event():
    init_db()

# =============================================================================
# ENDPOINTS
# =============================================================================

@app.get("/")
def root():
    """Endpoint raíz con información de la API"""
    return {
        "mensaje": "API de Tareas Persistente",
        "version": "1.0",
        "endpoints": {
            "GET /tareas": "Listar todas las tareas",
            "POST /tareas": "Crear nueva tarea",
            "PUT /tareas/{id}": "Actualizar tarea",
            "DELETE /tareas/{id}": "Eliminar tarea",
            "GET /tareas/resumen": "Resumen por estado"
        }
    }

@app.get("/tareas/resumen")
def obtener_resumen():
    """Devuelve un resumen de tareas agrupadas por estado"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute('''
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        GROUP BY estado
    ''')
    
    resultados = cursor.fetchall()
    conn.close()
    
    resumen = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for row in resultados:
        resumen[row['estado']] = row['cantidad']
    
    resumen["total"] = sum(resumen.values())
    
    return resumen

@app.get("/tareas")
def listar_tareas(
    estado: Optional[str] = None,
    texto: Optional[str] = None,
    prioridad: Optional[str] = None,
    orden: Optional[Literal["asc", "desc"]] = "asc"
):
    """
    Lista todas las tareas con filtros opcionales
    - estado: filtrar por estado (pendiente, en_progreso, completada)
    - texto: buscar en la descripción
    - prioridad: filtrar por prioridad (baja, media, alta)
    - orden: ordenar por fecha (asc o desc)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Construir la consulta SQL dinámicamente
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if texto:
        query += " AND descripcion LIKE ?"
        params.append(f"%{texto}%")
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    # Agregar ordenamiento
    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    else:
        query += " ORDER BY fecha_creacion ASC"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    # Convertir los resultados a diccionarios
    return [dict(tarea) for tarea in tareas]

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
    """Crea una nueva tarea en la base de datos"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fecha_actual = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    
    cursor.execute('''
        INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
        VALUES (?, ?, ?, ?)
    ''', (tarea.descripcion, tarea.estado, tarea.prioridad, fecha_actual))
    
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "prioridad": tarea.prioridad,
        "fecha_creacion": fecha_actual,
        "mensaje": "Tarea creada exitosamente"
    }

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    """Actualiza una tarea existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    # Construir la actualización dinámicamente
    campos_actualizar = []
    valores = []
    
    if tarea.descripcion is not None:
        campos_actualizar.append("descripcion = ?")
        valores.append(tarea.descripcion)
    
    if tarea.estado is not None:
        campos_actualizar.append("estado = ?")
        valores.append(tarea.estado)
    
    if tarea.prioridad is not None:
        campos_actualizar.append("prioridad = ?")
        valores.append(tarea.prioridad)
    
    if not campos_actualizar:
        conn.close()
        raise HTTPException(status_code=400, detail="No se proporcionaron campos para actualizar")
    
    valores.append(id)
    query = f"UPDATE tareas SET {', '.join(campos_actualizar)} WHERE id = ?"
    
    cursor.execute(query, valores)
    conn.commit()
    
    # Obtener la tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()
    
    return dict(tarea_actualizada)

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """Elimina una tarea de la base de datos"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que la tarea existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada exitosamente", "id": id}