from fastapi import FastAPI, HTTPException, Body
from pydantic import BaseModel, Field
from typing import Optional
from contextlib import asynccontextmanager
import sqlite3
from datetime import datetime


# ==================== CONFIGURACIÓN ====================

DB_NAME = "tareas.db"


# ==================== MODELOS PYDANTIC ====================

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1, description="Descripción de la tarea")
    estado: str = Field(default="pendiente", pattern="^(pendiente|en_progreso|completada)$")
    prioridad: str = Field(default="media", pattern="^(baja|media|alta)$")
    
    @classmethod
    def validate_descripcion(cls, v):
        if v.strip() == "":
            raise ValueError("La descripción no puede estar vacía o contener solo espacios")
        return v


class TareaUpdate(BaseModel):
    descripcion: Optional[str] = Field(None, min_length=1)
    estado: Optional[str] = Field(None, pattern="^(pendiente|en_progreso|completada)$")
    prioridad: Optional[str] = Field(None, pattern="^(baja|media|alta)$")


# ==================== FUNCIONES DE BASE DE DATOS ====================

def get_db_connection():
    """Establece conexión con la base de datos SQLite"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
    return conn


def init_db():
    """Inicializa la base de datos y crea la tabla si no existe"""
    conn = get_db_connection()
    conn.execute('''
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


# ==================== LIFESPAN ====================

@asynccontextmanager
async def lifespan(app: FastAPI):
    # Código que se ejecuta AL INICIAR el servidor
    print("🚀 Iniciando servidor...")
    init_db()
    print("✅ Base de datos inicializada correctamente")
    
    yield  # Aquí el servidor está corriendo
    
    # Código que se ejecuta AL CERRAR el servidor
    print("👋 Cerrando servidor...")
    print("✅ Servidor cerrado correctamente")


# ==================== APLICACIÓN FASTAPI ====================

app = FastAPI(
    title="API de Tareas Persistente",
    description="API RESTful para gestión de tareas con persistencia en SQLite",
    version="1.0.0",
    lifespan=lifespan
)


# ==================== ENDPOINTS ====================

@app.get("/")
def root():
    """Endpoint raíz de bienvenida"""
    return {
        "nombre": "API de Tareas Persistente",
        "descripcion": "API RESTful para gestión de tareas con persistencia en SQLite",
        "version": "1.0.0",
        "documentacion": "/docs",
        "endpoints": [
            "GET /tareas",
            "POST /tareas",
            "PUT /tareas/{id}",
            "DELETE /tareas/{id}",
            "GET /tareas/resumen",
            "PUT /tareas/completar_todas"
        ]
    }


@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = None,
    texto: Optional[str] = None,
    prioridad: Optional[str] = None,
    orden: Optional[str] = None
):
    """
    Obtiene todas las tareas con filtros opcionales
    """
    conn = get_db_connection()
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
    
    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    else:
        query += " ORDER BY fecha_creacion ASC"
    
    tareas = conn.execute(query, params).fetchall()
    conn.close()
    
    return [dict(tarea) for tarea in tareas]


@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
    """
    Crea una nueva tarea
    """
    if tarea.descripcion.strip() == "":
        raise HTTPException(
            status_code=422,
            detail="La descripción no puede estar vacía o contener solo espacios"
        )
    
    conn = get_db_connection()
    fecha_creacion = datetime.now().isoformat()
    
    cursor = conn.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion) VALUES (?, ?, ?, ?)",
        (tarea.descripcion, tarea.estado, tarea.prioridad, fecha_creacion)
    )
    conn.commit()
    
    nueva_tarea = conn.execute(
        "SELECT * FROM tareas WHERE id = ?", 
        (cursor.lastrowid,)
    ).fetchone()
    conn.close()
    
    return dict(nueva_tarea)


@app.put("/tareas/{id}")
def actualizar_tarea(id: int, tarea: TareaUpdate):
    """
    Actualiza una tarea existente
    """
    conn = get_db_connection()
    
    tarea_existente = conn.execute(
        "SELECT * FROM tareas WHERE id = ?", (id,)
    ).fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": "Tarea no encontrada"})
    
    campos = []
    valores = []
    
    if tarea.descripcion is not None:
        if len(tarea.descripcion.strip()) == 0:
            conn.close()
            raise HTTPException(status_code=400, detail="La descripción no puede estar vacía")
        campos.append("descripcion = ?")
        valores.append(tarea.descripcion)
    
    if tarea.estado is not None:
        campos.append("estado = ?")
        valores.append(tarea.estado)
    
    if tarea.prioridad is not None:
        campos.append("prioridad = ?")
        valores.append(tarea.prioridad)
    
    if not campos:
        conn.close()
        raise HTTPException(status_code=400, detail="No hay campos para actualizar")
    
    valores.append(id)
    query = f"UPDATE tareas SET {', '.join(campos)} WHERE id = ?"
    
    conn.execute(query, valores)
    conn.commit()
    
    tarea_actualizada = conn.execute(
        "SELECT * FROM tareas WHERE id = ?", (id,)
    ).fetchone()
    conn.close()
    
    return dict(tarea_actualizada)


@app.delete("/tareas/{id}", status_code=200)
def eliminar_tarea(id: int):
    """
    Elimina una tarea existente
    """
    conn = get_db_connection()
    tarea = conn.execute("SELECT * FROM tareas WHERE id = ?", (id,)).fetchone()
    
    if not tarea:
        conn.close()
        raise HTTPException(status_code=404, detail="Tarea no encontrada")
    
    conn.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": "Tarea eliminada correctamente"}


@app.get("/tareas/resumen")
def obtener_resumen():
    """
    Obtiene un resumen de tareas agrupadas por estado y prioridad
    """
    conn = get_db_connection()
    
    por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    por_prioridad = {"baja": 0, "media": 0, "alta": 0}
    
    resultados_estado = conn.execute(
        "SELECT estado, COUNT(*) as cantidad FROM tareas GROUP BY estado"
    ).fetchall()
    for row in resultados_estado:
        por_estado[row['estado']] = row['cantidad']
    
    resultados_prioridad = conn.execute(
        "SELECT prioridad, COUNT(*) as cantidad FROM tareas GROUP BY prioridad"
    ).fetchall()
    for row in resultados_prioridad:
        por_prioridad[row['prioridad']] = row['cantidad']
    
    total_tareas = sum(por_estado.values())
    conn.close()
    
    return {
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad,
        "pendiente": por_estado['pendiente'],
        "en_progreso": por_estado['en_progreso'],
        "completada": por_estado['completada']
    }

@app.put("/tareas/completar_todas")
def completar_todas(_: dict = Body(default={})):
    """
    Marca todas las tareas como completadas
    """
    conn = get_db_connection()
    conn.execute("UPDATE tareas SET estado = 'completada'")
    conn.commit()
    cantidad = conn.execute("SELECT COUNT(*) as total FROM tareas").fetchone()
    conn.close()
    return {
        "mensaje": "Todas las tareas han sido marcadas como completadas",
        "tareas_actualizadas": cantidad["total"]
    }

