from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional
from datetime import datetime
import sqlite3
from contextlib import asynccontextmanager

# ==============================================
# 🔧 CONFIGURACIÓN Y CONSTANTES
# ==============================================

VALID_ESTADOS = {"pendiente", "en_progreso", "completada"}
VALID_PRIORIDADES = {"baja", "media", "alta"}
DB_NAME = "tareas.db"


# ==============================================
# 🧩 MODELOS Pydantic
# ==============================================

class TareaCreate(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str = "pendiente"
    prioridad: str = "media"

    model_config = ConfigDict(
        json_schema_extra={
            "example": {
                "descripcion": "Completar el TP3",
                "estado": "pendiente",
                "prioridad": "alta"
            }
        }
    )


class TareaUpdate(BaseModel):
    descripcion: Optional[str] = None
    estado: Optional[str] = None
    prioridad: Optional[str] = None


# ==============================================
# 💾 FUNCIONES DE BASE DE DATOS
# ==============================================

def init_db():
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


def get_db():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    return conn


# ==============================================
# ⚙️ FASTAPI APP (con lifespan)
# ==============================================

@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield  # Aquí corre la app normalmente

app = FastAPI(
    title="API de Tareas Persistente - TP3",
    version="1.0",
    lifespan=lifespan
)


# ==============================================
# 🌐 ENDPOINTS
# ==============================================

@app.get("/")
def endpoint_raiz():
    return JSONResponse({
        "nombre": "API de Tareas Persistente - TP3",
        "version": "1.0",
        "endpoints": [
            "GET /tareas",
            "POST /tareas",
            "PUT /tareas/{id}",
            "DELETE /tareas/{id}",
            "GET /tareas/resumen",
            "PUT /tareas/completar_todas"
        ]
    }, status_code=200)


# 🟢 1. Resumen de tareas
@app.get("/tareas/resumen")
def resumen_tareas():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total = cursor.fetchone()["total"]

    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad
        FROM tareas
        GROUP BY estado
    """)
    resultados_estado = cursor.fetchall()
    por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for row in resultados_estado:
        por_estado[row["estado"]] = row["cantidad"]

    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad
        FROM tareas
        GROUP BY prioridad
    """)
    resultados_prioridad = cursor.fetchall()
    por_prioridad = {"baja": 0, "media": 0, "alta": 0}
    for row in resultados_prioridad:
        por_prioridad[row["prioridad"]] = row["cantidad"]

    conn.close()

    return JSONResponse({
        "total_tareas": total,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }, status_code=200)


# 🟢 2. Completar todas las tareas
@app.put("/tareas/completar_todas")
def completar_todas():
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total = cursor.fetchone()["total"]

    if total == 0:
        conn.close()
        return JSONResponse({"mensaje": "No hay tareas para completar"}, status_code=200)

    cursor.execute("UPDATE tareas SET estado = 'completada'")
    conn.commit()
    conn.close()

    return JSONResponse({"mensaje": "Todas las tareas marcadas como completadas"}, status_code=200)


# 🟢 3. Obtener todas las tareas (con filtros y orden)
@app.get("/tareas")
def obtener_tareas(
    estado: Optional[str] = None,
    texto: Optional[str] = None,
    prioridad: Optional[str] = None,
    orden: Optional[str] = None
):
    conn = get_db()
    cursor = conn.cursor()

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

    if orden and orden.lower() in ["asc", "desc"]:
        query += f" ORDER BY fecha_creacion {orden.upper()}"
    else:
        query += " ORDER BY fecha_creacion DESC"

    cursor.execute(query, params)
    tareas = [dict(row) for row in cursor.fetchall()]
    conn.close()

    return JSONResponse(tareas, status_code=200)


# 🟢 4. Crear una tarea
@app.post("/tareas")
async def crear_tarea(request: Request):
    payload = await request.json()
    descripcion = payload.get("descripcion", "").strip()
    estado = payload.get("estado", "pendiente")
    prioridad = payload.get("prioridad", "media")

    if not descripcion:
        return JSONResponse({"detail": "La descripción no puede estar vacía"}, status_code=422)
    if estado not in VALID_ESTADOS:
        return JSONResponse({"detail": "Estado inválido"}, status_code=422)
    if prioridad not in VALID_PRIORIDADES:
        return JSONResponse({"detail": "Prioridad inválida"}, status_code=422)

    conn = get_db()
    cursor = conn.cursor()
    fecha_creacion = datetime.now().isoformat()

    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, fecha_creacion)
        VALUES (?, ?, ?, ?)
    """, (descripcion, estado, prioridad, fecha_creacion))
    conn.commit()

    tarea_id = cursor.lastrowid
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    nueva_tarea = dict(cursor.fetchone())
    conn.close()

    return JSONResponse(nueva_tarea, status_code=201)


# 🟢 5. Actualizar una tarea
@app.put("/tareas/{id}")
async def actualizar_tarea(id: int, request: Request):
    payload = await request.json()

    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()

    if not tarea:
        conn.close()
        return JSONResponse({"detail": "error: La tarea no existe"}, status_code=404)

    updates = []
    params = []

    if "descripcion" in payload:
        nueva_desc = payload["descripcion"].strip()
        if not nueva_desc:
            conn.close()
            return JSONResponse({"detail": "La descripción no puede estar vacía"}, status_code=422)
        updates.append("descripcion = ?")
        params.append(nueva_desc)

    if "estado" in payload:
        nuevo_estado = payload["estado"]
        if nuevo_estado not in VALID_ESTADOS:
            conn.close()
            return JSONResponse({"detail": "Estado inválido"}, status_code=422)
        updates.append("estado = ?")
        params.append(nuevo_estado)

    if "prioridad" in payload:
        nueva_prioridad = payload["prioridad"]
        if nueva_prioridad not in VALID_PRIORIDADES:
            conn.close()
            return JSONResponse({"detail": "Prioridad inválida"}, status_code=422)
        updates.append("prioridad = ?")
        params.append(nueva_prioridad)

    if updates:
        params.append(id)
        query = f"UPDATE tareas SET {', '.join(updates)} WHERE id = ?"
        cursor.execute(query, params)
        conn.commit()

    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea_actualizada = dict(cursor.fetchone())
    conn.close()

    return JSONResponse(tarea_actualizada, status_code=200)


# 🟢 6. Eliminar una tarea
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    conn = get_db()
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM tareas WHERE id = ?", (id,))
    tarea = cursor.fetchone()

    if not tarea:
        conn.close()
        return JSONResponse({"detail": "error: La tarea no existe"}, status_code=404)

    cursor.execute("DELETE FROM tareas WHERE id = ?", (id,))
    conn.commit()
    conn.close()

    return JSONResponse({"mensaje": "Tarea eliminada"}, status_code=200)
