from fastapi import FastAPI, HTTPException, Query
from pydantic import BaseModel, field_validator
from typing import List, Literal, Optional
from datetime import datetime
import sqlite3

app = FastAPI()

# Nombre de la base de datos
tareas = "tareas.db"

# Inicializar base de datos
def init_db():
    with sqlite3.connect(tareas) as conn:
        cursor = conn.cursor()
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS tareas (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                prioridad TEXT NOT NULL,
                fecha_creacion TEXT NOT NULL
            )
        """)
        conn.commit()

# Llamar a init_db al iniciar
init_db()

# Modelos Pydantic
class TareaModelo(BaseModel):
    id: int
    descripcion: str
    estado: Literal["pendiente", "en_progreso", "completada"]
    prioridad: Literal["baja", "media", "alta"]
    fecha_creacion: str

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return v

class TareaEntrada(BaseModel):
    descripcion: str
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = "pendiente"
    prioridad: Optional[Literal["baja", "media", "alta"]] = "baja"

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v: str) -> str:
        if not v or v.strip() == "":
            raise ValueError("La descripción no puede estar vacía")
        return v

class TareaModificar(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = None
    prioridad: Optional[Literal["baja", "media", "alta"]] = None

    @field_validator("descripcion")
    @classmethod
    def descripcion_no_vacia(cls, v: Optional[str]) -> Optional[str]:
        if v is not None and (not v or v.strip() == ""):
            raise ValueError("La descripción no puede estar vacía")
        return v

class Respuesta(BaseModel):
    mensaje: str

# Ruta raíz
@app.get("/")
def raiz():
    return {
        "nombre": "API de Tareas Persistente",
        "endpoints": [
            "GET /tareas",
            "POST /tareas",
            "PUT /tareas/{id}",
            "DELETE /tareas/{id}",
            "GET /tareas/resumen",
            "PUT /tareas/completar_todas"
        ]
    }

# Rutas fijas primero
@app.get("/tareas/resumen")
def contar_estados():
    with sqlite3.connect(tareas) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        # Contar total de tareas
        cursor.execute("SELECT COUNT(*) FROM tareas")
        total_tareas = cursor.fetchone()[0]
        # Contar por estado
        cursor.execute("SELECT estado, COUNT(*) as total FROM tareas GROUP BY estado")
        por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
        for row in cursor.fetchall():
            estado = row["estado"]
            if estado in por_estado:
                por_estado[estado] = row["total"]
        # Contar por prioridad
        cursor.execute("SELECT prioridad, COUNT(*) as total FROM tareas GROUP BY prioridad")
        por_prioridad = {"baja": 0, "media": 0, "alta": 0}
        for row in cursor.fetchall():
            prioridad = row["prioridad"]
            if prioridad in por_prioridad:
                por_prioridad[prioridad] = row["total"]
        return {
            "total_tareas": total_tareas,
            "por_estado": por_estado,
            "por_prioridad": por_prioridad
        }

@app.put("/tareas/completar_todas")
def completar_todo():
    with sqlite3.connect(tareas) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT COUNT(*) FROM tareas")
        total = cursor.fetchone()[0]
        if total == 0:
            return {"mensaje": "No hay tareas para completar"}
        cursor.execute("UPDATE tareas SET estado = 'completada'")
        conn.commit()
        return {"mensaje": "Todas las tareas completadas"}

# Rutas dinámicas después
@app.get("/tareas", response_model=List[TareaModelo])
def obtener_tareas(
    estado: Optional[Literal["pendiente", "en_progreso", "completada"]] = Query(None),
    texto: Optional[str] = Query(None),
    prioridad: Optional[Literal["baja", "media", "alta"]] = Query(None),
    orden: Optional[Literal["asc", "desc"]] = Query(None)
):
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
    if orden:
        query += " ORDER BY fecha_creacion " + ("ASC" if orden == "asc" else "DESC")

    with sqlite3.connect(tareas) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(query, params)
        tareas_lista = [
            {
                "id": row["id"],
                "descripcion": row["descripcion"],
                "estado": row["estado"],
                "prioridad": row["prioridad"],
                "fecha_creacion": row["fecha_creacion"]
            }
            for row in cursor.fetchall()
        ]
        return tareas_lista

@app.post("/tareas", response_model=TareaModelo, status_code=201)
def agregar_tarea(tarea: TareaEntrada):
    with sqlite3.connect(tareas) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute(
            "INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion) VALUES (?, ?, ?, ?)",
            (tarea.descripcion, tarea.estado or "pendiente", tarea.prioridad or "baja", datetime.now().isoformat())
        )
        conn.commit()
        tarea_id = cursor.lastrowid
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
        row = cursor.fetchone()
        return {
            "id": row["id"],
            "descripcion": row["descripcion"],
            "estado": row["estado"],
            "prioridad": row["prioridad"],
            "fecha_creacion": row["fecha_creacion"]
        }

@app.put("/tareas/{id}", response_model=TareaModelo)
def modificar_tarea(id: int, tarea_mod: TareaModificar):
    with sqlite3.connect(tareas) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
        
        update_fields = []
        params = []
        if tarea_mod.descripcion is not None:
            update_fields.append("descripcion = ?")
            params.append(tarea_mod.descripcion)
        if tarea_mod.estado is not None:
            update_fields.append("estado = ?")
            params.append(tarea_mod.estado)
        if tarea_mod.prioridad is not None:
            update_fields.append("prioridad = ?")
            params.append(tarea_mod.prioridad)
        
        if update_fields:
            params.append(id)
            query = f"UPDATE tareas SET {', '.join(update_fields)} WHERE id = ?"
            cursor.execute(query, params)
            conn.commit()
        
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        row = cursor.fetchone()
        return {
            "id": row["id"],
            "descripcion": row["descripcion"],
            "estado": row["estado"],
            "prioridad": row["prioridad"],
            "fecha_creacion": row["fecha_creacion"]
        }

@app.delete("/tareas/{id}", response_model=Respuesta)
def borrar_tarea(id: int):
    with sqlite3.connect(tareas) as conn:
        conn.row_factory = sqlite3.Row
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})
        cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
        conn.commit()
        return Respuesta(mensaje="Tarea eliminada")