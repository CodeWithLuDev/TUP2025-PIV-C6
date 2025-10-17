from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, Field, validator
from typing import Optional, Literal
from datetime import datetime
import sqlite3

app = FastAPI(title="API de Tareas Persistente", version="3.0.0")

# Nombre de la base de datos (debe ser exportado para los tests)
DB_NAME = "tareas.db"

# ==================== MODELOS PYDANTIC ====================

class TareaCrear(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    @validator('descripcion')
    def validar_descripcion(cls, v):
        if not v or v.strip() == "":
            raise ValueError('La descripción no puede estar vacía')
        return v.strip()

class TareaActualizar(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    
    @validator('descripcion')
    def validar_descripcion(cls, v):
        if v is not None and (not v or v.strip() == ""):
            raise ValueError('La descripción no puede estar vacía')
        return v.strip() if v else v

# ==================== FUNCIONES DE BASE DE DATOS ====================

def init_db():
    """Inicializa la base de datos y crea la tabla si no existe"""
    conn = sqlite3.connect(DB_NAME)
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
    conn.close()

def get_db_connection():
    """Obtiene una conexión a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row):
    """Convierte una fila de SQLite en un diccionario"""
    return {key: row[key] for key in row.keys()}

# ==================== EVENTOS ====================

@app.on_event("startup")
def startup():
    """Se ejecuta al iniciar la aplicación"""
    init_db()

# ==================== ENDPOINTS ====================

@app.get("/")
def root():
    return {
        "nombre": "API de Tareas Persistente",
        "version": "3.0.0",
        "endpoints": {
            "GET /tareas": "Obtener todas las tareas",
            "POST /tareas": "Crear una nueva tarea",
            "PUT /tareas/{id}": "Actualizar una tarea",
            "DELETE /tareas/{id}": "Eliminar una tarea",
            "GET /tareas/resumen": "Obtener resumen de tareas",
            "PUT /tareas/completar_todas": "Marcar todas como completadas"
        }
    }

@app.get("/tareas/resumen")
def obtener_resumen():
    """Obtiene el resumen de tareas por estado y prioridad"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total = cursor.fetchone()["total"]
    
    # Por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad 
        FROM tareas 
        GROUP BY estado
    """)
    resultados_estado = cursor.fetchall()
    
    por_estado = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    for row in resultados_estado:
        por_estado[row["estado"]] = row["cantidad"]
    
    # Por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad 
        FROM tareas 
        GROUP BY prioridad
    """)
    resultados_prioridad = cursor.fetchall()
    
    por_prioridad = {
        "baja": 0,
        "media": 0,
        "alta": 0
    }
    
    for row in resultados_prioridad:
        por_prioridad[row["prioridad"]] = row["cantidad"]
    
    conn.close()
    
    return {
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }

@app.put("/tareas/completar_todas")
def completar_todas():
    """Marca todas las tareas como completadas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Contar cuántas no están completadas
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE estado != 'completada'")
    pendientes = cursor.fetchone()["total"]
    
    if pendientes == 0:
        conn.close()
        return {"mensaje": "No hay tareas para completar"}
    
    # Actualizar todas
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    conn.commit()
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total = cursor.fetchone()["total"]
    
    conn.close()
    
    return {
        "mensaje": f"Se completaron {pendientes} tareas",
        "total_tareas": total
    }

@app.get("/tareas")
def obtener_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[Literal["baja", "media", "alta"]] = Query(None),
    orden: Optional[Literal["asc", "desc"]] = Query("desc")
):
    """
    Obtiene todas las tareas con filtros opcionales
    - estado: filtrar por estado
    - texto: buscar en descripción
    - prioridad: filtrar por prioridad
    - orden: ordenar por fecha (asc o desc)
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Construir query dinámica
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
    
    # Ordenamiento
    direccion = "DESC" if orden == "desc" else "ASC"
    query += f" ORDER BY fecha_creacion {direccion}"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [row_to_dict(tarea) for tarea in tareas]

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCrear):
    """Crea una nueva tarea"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fecha_actual = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
        VALUES (?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, tarea.prioridad, fecha_actual))
    
    tarea_id = cursor.lastrowid
    conn.commit()
    
    # Obtener la tarea creada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    nueva_tarea = cursor.fetchone()
    conn.close()
    
    return row_to_dict(nueva_tarea)

@app.get("/tareas/{id}")
def obtener_tarea(id: int):
    """Obtiene una tarea específica por ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    conn.close()
    
    if not tarea:
        raise HTTPException(
            status_code=404,
            detail={"error": "La tarea no existe"}
        )
    
    return row_to_dict(tarea)

@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea_actualizada: TareaActualizar):
    """Actualiza una tarea existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    if not cursor.fetchone():
        conn.close()
        raise HTTPException(
            status_code=404,
            detail={"error": "La tarea no existe"}
        )
    
    # Construir update dinámico
    updates = []
    params = []
    
    if tarea_actualizada.descripcion is not None:
        updates.append("descripcion = ?")
        params.append(tarea_actualizada.descripcion)
    
    if tarea_actualizada.estado is not None:
        updates.append("estado = ?")
        params.append(tarea_actualizada.estado)
    
    if tarea_actualizada.prioridad is not None:
        updates.append("prioridad = ?")
        params.append(tarea_actualizada.prioridad)
    
    # Ejecutar update si hay cambios
    if updates:
        params.append(id)
        query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()
    
    # Obtener tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    conn.close()
    
    return row_to_dict(tarea)

@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    """Elimina una tarea"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()
    
    if not tarea:
        conn.close()
        raise HTTPException(
            status_code=404,
            detail={"error": "La tarea no existe"}
        )
    
    # Eliminar
    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {
        "mensaje": "Tarea eliminada exitosamente",
        "tarea_eliminada": row_to_dict(tarea)
    }

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)