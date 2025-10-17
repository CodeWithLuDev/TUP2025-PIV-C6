from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, field_validator
from typing import Optional, Literal
from datetime import datetime
import sqlite3


DB_NAME = "tareas.db"
app = FastAPI(title="API de Tareas", version="1.0.0")



class TareaCreate(BaseModel):
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"] = "pendiente"
    prioridad: Literal["baja", "media", "alta"] = "media"
    
    @field_validator("descripcion")
    @classmethod
    def validar_descripcion(cls, v):
        if not v or not v.strip():
            raise ValueError("La descripción no puede estar vacía")
        return v

class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None
    
    @field_validator("descripcion")
    @classmethod
    def validar_descripcion(cls, v):
        if v is not None and (not v or not v.strip()):
            raise ValueError("La descripción no puede estar vacía")
        return v

class TareaResponse(BaseModel):
    id: int
    descripcion: str
    estado: str
    fecha_creacion: str
    prioridad: str



def init_db():
    """Crea la base de datos y la tabla tareas"""
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


init_db()



def get_db_connection():
    """Obtiene una conexión a la base de datos"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn

def tarea_to_dict(tarea_row):
    """Convierte una fila de SQLite a diccionario"""
    return {
        "id": tarea_row["id"],
        "descripcion": tarea_row["descripcion"],
        "estado": tarea_row["estado"],
        "fecha_creacion": tarea_row["fecha_creacion"],
        "prioridad": tarea_row["prioridad"]
    }



@app.get("/")
def raiz():
    """Información de la API"""
    return {
        "nombre": "API de Tareas",
        "version": "1.0.0",
        "endpoints": [
            "GET /tareas - Listar tareas",
            "POST /tareas - Crear tarea",
            "PUT /tareas/{id} - Actualizar tarea",
            "DELETE /tareas/{id} - Eliminar tarea",
            "GET /tareas/resumen - Resumen de tareas",
            "PUT /tareas/completar_todas - Completar todas las tareas"
        ]
    }

@app.post("/tareas", status_code=201)
def crear_tarea(tarea: TareaCreate):
    """Crea una nueva tarea"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fecha_creacion = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, fecha_creacion, prioridad)
        VALUES (?, ?, ?, ?)
    """, (tarea.descripcion, tarea.estado, fecha_creacion, tarea.prioridad))
    
    tarea_id = cursor.lastrowid
    conn.commit()
    
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    nueva_tarea = cursor.fetchone()
    conn.close()
    
    return tarea_to_dict(nueva_tarea)

@app.get("/tareas/resumen")
def obtener_resumen():
    """Obtiene un resumen de las tareas por estado y prioridad"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
 
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total = cursor.fetchone()["total"]
    
    
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad 
        FROM tareas 
        GROUP BY estado
    """)
    estados = cursor.fetchall()
    por_estado = {fila["estado"]: fila["cantidad"] for fila in estados}
    
    
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad 
        FROM tareas 
        GROUP BY prioridad
    """)
    prioridades = cursor.fetchall()
    por_prioridad = {fila["prioridad"]: fila["cantidad"] for fila in prioridades}
    
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
    
    cursor.execute("UPDATE tareas SET estado = 'completada'")
    filas_afectadas = cursor.rowcount
    conn.commit()
    conn.close()
    
    return {"mensaje": f"Se completaron {filas_afectadas} tareas"}

@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = None,
    texto: Optional[str] = None,
    prioridad: Optional[str] = None,
    orden: Optional[Literal["asc", "desc"]] = "asc"
):
    """Obtiene todas las tareas con filtros opcionales"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
   
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if texto:
        query += " AND LOWER(descripcion) LIKE ?"
        params.append(f"%{texto.lower()}%")
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    else:
        query += " ORDER BY fecha_creacion ASC"
    
    cursor.execute(query, params)
    tareas = cursor.fetchall()
    conn.close()
    
    return [tarea_to_dict(t) for t in tareas]

@app.put("/tareas/{tarea_id}")
def actualizar_tarea(tarea_id: int, tarea: TareaUpdate):
    """Actualiza una tarea existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": f"Tarea {tarea_id} no encontrada"})
    
    
    campos = []
    valores = []
    
    if tarea.descripcion is not None:
        campos.append("descripcion = ?")
        valores.append(tarea.descripcion)
    
    if tarea.estado is not None:
        campos.append("estado = ?")
        valores.append(tarea.estado)
    
    if tarea.prioridad is not None:
        campos.append("prioridad = ?")
        valores.append(tarea.prioridad)
    
    if campos:
        valores.append(tarea_id)
        query = f"UPDATE tareas SET {', '.join(campos)} WHERE id = ?"
        cursor.execute(query, valores)
        conn.commit()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()
    
    return tarea_to_dict(tarea_actualizada)

@app.delete("/tareas/{tarea_id}")
def eliminar_tarea(tarea_id: int):
    """Elimina una tarea"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea_existente = cursor.fetchone()
    
    if not tarea_existente:
        conn.close()
        raise HTTPException(status_code=404, detail={"error": f"Tarea {tarea_id} no encontrada"})
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    
    return {"mensaje": f"Tarea {tarea_id} eliminada exitosamente"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)