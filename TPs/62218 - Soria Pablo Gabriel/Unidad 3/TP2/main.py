try:
    from fastapi import FastAPI, HTTPException, Query
    from pydantic import BaseModel, Field
except ImportError as e:
    raise ImportError(
        "Faltan paquetes requeridos: instala las dependencias con:\n"
        "  python -m venv .venv; .\\.venv\\Scripts\\Activate.ps1; pip install -r TPs/62218 - Soria Pablo Gabriel/Unidad 3/TP2/requirements.txt\n"
        "O alternativamente: pip install fastapi pydantic uvicorn requests pytest"
    ) from e

from typing import List, Optional
from datetime import datetime

app = FastAPI()

# � Agenda de contactos (hardcodeada para los tests)
contactos_db = [
    {
        "nombre": "Juan",
        "apellido": "Pérez",
        "edad": 30,
        "teléfono": "+54 9 11 1234-5678",
        "email": "juan.perez@example.com",
    },
    {
        "nombre": "José",
        "apellido": "Gómez",
        "edad": 25,
        "teléfono": "+54 9 11 8765-4321",
        "email": "jose.gomez@example.com",
    },
]


@app.get("/")
def raiz():
    """Endpoint raíz esperado por los tests: mensaje de bienvenida."""
    return {"mensaje": "Bienvenido a la Agenda de Contactos - ¡Bienvenido!"}


@app.get("/contactos")
def obtener_contactos():
    """Devuelve la lista de contactos (hardcodeada en memoria)."""
    return contactos_db

# �🗂️ Base de datos en memoria
tareas_db = []
id_counter = 1

# ✅ Estados válidos
ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}

# 📦 Modelo de entrada
class TareaInput(BaseModel):
    descripcion: str = Field(..., min_length=1)
    estado: str

# 📦 Modelo de salida
class Tarea(TareaInput):
    id: int
    fecha_creacion: datetime

# 📍 GET /tareas
@app.get("/tareas", response_model=List[Tarea])
def obtener_tareas(estado: Optional[str] = None, texto: Optional[str] = None):
    resultado = tareas_db
    if estado:
        if estado not in ESTADOS_VALIDOS:
            raise HTTPException(status_code=400, detail="Estado inválido")
        resultado = [t for t in resultado if t.estado == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t.descripcion.lower()]
    return resultado

# 🆕 POST /tareas
@app.post("/tareas", response_model=Tarea)
def crear_tarea(tarea: TareaInput):
    if tarea.estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail="Estado inválido")
    global id_counter
    nueva_tarea = Tarea(id=id_counter, descripcion=tarea.descripcion, estado=tarea.estado, fecha_creacion=datetime.now())
    tareas_db.append(nueva_tarea)
    id_counter += 1
    return nueva_tarea

# ✏️ PUT /tareas/{id}
@app.put("/tareas/{id}", response_model=Tarea)
def modificar_tarea(id: int, tarea: TareaInput):
    for t in tareas_db:
        if t.id == id:
            if tarea.estado not in ESTADOS_VALIDOS:
                raise HTTPException(status_code=400, detail="Estado inválido")
            t.descripcion = tarea.descripcion
            t.estado = tarea.estado
            return t
    raise HTTPException(status_code=404, detail="La tarea no existe")

# 🗑️ DELETE /tareas/{id}
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for t in tareas_db:
        if t.id == id:
            tareas_db.remove(t)
            return {"mensaje": "Tarea eliminada"}
    raise HTTPException(status_code=404, detail="La tarea no existe")

# 📊 GET /tareas/resumen
@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {estado: 0 for estado in ESTADOS_VALIDOS}
    for t in tareas_db:
        resumen[t.estado] += 1
    return resumen

# ✅ PUT /tareas/completar_todas
@app.put("/tareas/completar_todas")
def completar_todas():
    for t in tareas_db:
        t.estado = "completada"
    return {"mensaje": "Todas las tareas fueron marcadas como completadas"}
