from fastapi import FastAPI, Path, HTTPException, Query, status
from pydantic import BaseModel, Field
from typing import Optional, List
from datetime import datetime, timezone
import sqlite3
import os

app = FastAPI(title="Mini API de Tareas Persistente - TP3")

DB_NAME = "tareas.db" 
ALLOWED_ESTADOS = {"pendiente", "en_progreso", "completada"}
ALLOWED_PRIORIDADES = {"baja", "media", "alta"}

# ======================================================================
# 1. Funciones de Configuración y Ayuda
# ======================================================================

def init_db():
    """Crea la base de datos y la tabla 'tareas' si no existen, incluyendo la columna prioridad."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            fecha_creacion TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media'
        )
    """)
    conn.commit()
    conn.close()

def row_to_dict(row):
    """Convierte una fila de SQLite (tupla) a un diccionario de tarea."""
    if not row:
        return None
    # Estructura de la tupla: (id, descripcion, estado, fecha_creacion, prioridad)
    return {
        "id": row[0],
        "descripcion": row[1],
        "estado": row[2],
        "fecha_creacion": row[3],
        "prioridad": row[4],
    }

# Inicializar la DB al cargar la aplicación
init_db()

# ======================================================================
# 2. Modelos Pydantic
# ======================================================================

class TareaCreate(BaseModel):
    # descripcion: str no necesita Field porque es requerido
    descripcion: str
    # Usamos Field con pattern para validar valores, aunque FastAPI también lo hace con Query/Path
    estado: Optional[str] = Field("pendiente", pattern=r'^(pendiente|en_progreso|completada)$')
    prioridad: Optional[str] = Field("media", pattern=r'^(baja|media|alta)$')

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = Field(None, pattern=r'^(pendiente|en_progreso|completada)$')
    prioridad: Optional[str] = Field(None, pattern=r'^(baja|media|alta)$')
    
class TareaDB(BaseModel):
    # Modelo para la respuesta, con todos los campos
    id: int
    descripcion: str
    estado: str
    fecha_creacion: str
    prioridad: str

# ======================================================================
# 3. Endpoints Raíz y de Mejoras (COLOCADOS ARRIBA para evitar conflicto con /tareas/{id})
# ======================================================================

@app.get("/")
def endpoint_raiz():
    """Devuelve información básica de la API."""
    return {
        "nombre": "API de Tareas Persistente (SQLite)",
        "version": "1.0",
        "endpoints": {
            "/tareas": "GET, POST",
            "/tareas/{id}": "PUT, DELETE",
            "/tareas/resumen": "GET",
            "/tareas/completar_todas": "PUT"
        }
    }

@app.get("/tareas/resumen")
def resumen_tareas():
    """Devuelve el resumen de tareas por estado y prioridad (Mejora Obligatoria)."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # 1. Resumen por estado
    cursor.execute("SELECT estado, COUNT(*) FROM tareas GROUP BY estado")
    resumen_estado = {estado: count for estado, count in cursor.fetchall()}
    
    # 2. Resumen por prioridad
    cursor.execute("SELECT prioridad, COUNT(*) FROM tareas GROUP BY prioridad")
    resumen_prioridad = {prioridad: count for prioridad, count in cursor.fetchall()}
    
    conn.close()
    
    # Asegurar que todos los estados y prioridades tengan conteo, incluso 0
    por_estado = {e: resumen_estado.get(e, 0) for e in ALLOWED_ESTADOS}
    por_prioridad = {p: resumen_prioridad.get(p, 0) for p in ALLOWED_PRIORIDADES}
    
    total_tareas = sum(por_estado.values())
    
    return {
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad,
    }


@app.put("/tareas/completar_todas", status_code=status.HTTP_200_OK)
def completar_todas():
    """Actualiza el estado de todas las tareas a 'completada'."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Contar tareas antes de actualizar para verificar si hay tareas
    cursor.execute("SELECT COUNT(*) FROM tareas")
    total = cursor.fetchone()[0]
    
    if total == 0:
        conn.close()
        return {"mensaje": "No hay tareas"}
    
    # Actualizar todas las tareas
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    conn.commit()
    conn.close()
    
    return {"mensaje": "Todas las tareas completadas"}

# ======================================================================
# 4. Endpoints CRUD principales
# ======================================================================

@app.get("/tareas", response_model=List[TareaDB])
def obtener_tareas(
    estado: Optional[str] = Query(None), 
    texto: Optional[str] = Query(None), 
    prioridad: Optional[str] = Query(None),
    orden: Optional[str] = Query(None, description="Ordenamiento por fecha: 'asc' o 'desc'")
):
    """Devuelve tareas, con filtros opcionales por estado, texto, prioridad y ordenamiento (Mejoras)."""
    base_query = "SELECT * FROM tareas"
    conditions = []
    params = []
    
    # Validaciones y construcción de filtros WHERE
    if estado:
        # El test espera que el código valide el estado, aunque Pydantic también lo haga
        if estado not in ALLOWED_ESTADOS:
            raise HTTPException(status_code=422, detail="Estado inválido")
        conditions.append("estado = ?")
        params.append(estado)
        
    if prioridad:
        # El test espera que el código valide la prioridad
        if prioridad not in ALLOWED_PRIORIDADES:
            raise HTTPException(status_code=422, detail="Prioridad inválida")
        conditions.append("prioridad = ?")
        params.append(prioridad)
    
    if texto:
        # Búsqueda por texto (LIKE) insensible a mayúsculas/minúsculas y parcial
        conditions.append("descripcion LIKE ?")
        params.append(f"%{texto.strip()}%")
        
    # Construir la cláusula WHERE
    if conditions:
        base_query += " WHERE " + " AND ".join(conditions)
        
    # Añadir ordenamiento (ORDER BY)
    order_clause = ""
    if orden:
        orden_lower = orden.lower()
        if orden_lower == "desc":
            order_clause = " ORDER BY fecha_creacion DESC"
        elif orden_lower == "asc":
            order_clause = " ORDER BY fecha_creacion ASC"
        else:
            raise HTTPException(status_code=422, detail="Parámetro 'orden' inválido. Use 'asc' o 'desc'.")
            
    final_query = base_query + order_clause
    
    # Ejecutar la consulta
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    cursor.execute(final_query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [row_to_dict(t) for t in tareas]


@app.post("/tareas", status_code=201, response_model=TareaDB)
def crear_tarea(payload: TareaCreate):
    """Crea una nueva tarea persistente en la DB."""
    descripcion = payload.descripcion.strip()
    
    # Validación de descripción vacía o solo espacios
    if not descripcion:
        raise HTTPException(status_code=422, detail="La descripción no puede estar vacía")
        
    estado = payload.estado
    prioridad = payload.prioridad
    
    # Corrección para evitar DeprecationWarning: usar datetime.now(timezone.utc)
    fecha_creacion = datetime.now(timezone.utc).isoformat().replace('+00:00', 'Z')
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    try:
        # Insertar en DB
        cursor.execute(
            """
            INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
            VALUES (?, ?, ?, ?)
            """,
            (descripcion, estado, fecha_creacion, prioridad)
        )
        tarea_id = cursor.lastrowid
        conn.commit()
        
        # Recuperar la tarea completa
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        tarea = cursor.fetchone()
        
    finally:
        conn.close()
        
    return row_to_dict(tarea)


@app.put("/tareas/{tarea_id}", response_model=TareaDB)
def actualizar_tarea(tarea_id: int = Path(...), payload: TareaUpdate = None):
    """Actualiza una tarea existente en la DB."""
    
    # Corrección para evitar DeprecationWarning: usar payload.model_dump()
    update_data = payload.model_dump(exclude_unset=True) if payload else {}
    
    if not update_data:
        raise HTTPException(status_code=400, detail="No se recibieron datos para actualizar")
    
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    sets = []
    values = []
    
    if "descripcion" in update_data:
        desc = update_data["descripcion"].strip()
        if not desc:
            raise HTTPException(status_code=422, detail="La descripción no puede estar vacía")
        sets.append("descripcion = ?")
        values.append(desc)
    
    if "estado" in update_data:
        sets.append("estado = ?")
        values.append(update_data["estado"])
        
    if "prioridad" in update_data:
        sets.append("prioridad = ?")
        values.append(update_data["prioridad"])

    # Ejecutar la actualización
    values.append(tarea_id)
    query = f"UPDATE tareas SET {', '.join(sets)} WHERE id = ?"
    cursor.execute(query, values)
    conn.commit()
    
    # Verificar si se actualizó algo (cursor.rowcount == 0 si no existe)
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="error: La tarea no existe")
        
    # Recuperar la tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    updated_tarea = cursor.fetchone()
    conn.close()
    
    return row_to_dict(updated_tarea)


@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int = Path(...)):
    """Elimina una tarea de la DB."""
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    
    # Verificar si se eliminó algo (cursor.rowcount == 0 si no existe)
    if cursor.rowcount == 0:
        conn.close()
        raise HTTPException(status_code=404, detail="error: La tarea no existe")
        
    conn.close()
    return {"mensaje": "Tarea eliminada"}
