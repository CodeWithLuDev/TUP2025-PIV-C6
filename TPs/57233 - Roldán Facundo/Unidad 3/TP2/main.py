from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from datetime import datetime

app = FastAPI()

tareas_db = []
VALID_ESTADOS = {"pendiente", "en_progreso", "completada"}


# 🟢 1. Obtener todas las tareas
@app.get("/tareas")
def obtener_tareas(estado: str = None, texto: str = None):
    resultado = tareas_db
    if estado:
        resultado = [t for t in resultado if t["estado"] == estado]
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]
    return JSONResponse(resultado, status_code=200)


# 🟢 2. Crear una tarea
@app.post("/tareas")
async def crear_tarea(request: Request):
    payload = await request.json()
    descripcion = payload.get("descripcion", "").strip()
    estado = payload.get("estado", "pendiente")

    if not descripcion:
        return JSONResponse({"detail": "La descripción no puede estar vacía"}, status_code=422)
    if estado not in VALID_ESTADOS:
        return JSONResponse({"detail": "Estado inválido"}, status_code=422)

    nueva_tarea = {
        "id": len(tareas_db) + 1,
        "descripcion": descripcion,
        "estado": estado,
        "fecha_creacion": datetime.now().isoformat()
    }
    tareas_db.append(nueva_tarea)
    return JSONResponse(nueva_tarea, status_code=201)


# 🟢 3. Completar todas las tareas (debe ir ANTES del {id})
@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas_db:
        return JSONResponse({"mensaje": "No hay tareas para completar"}, status_code=200)
    for t in tareas_db:
        t["estado"] = "completada"
    return JSONResponse({"mensaje": "Todas las tareas marcadas como completadas"}, status_code=200)


# 🟢 4. Actualizar una tarea existente
@app.put("/tareas/{id}")
async def actualizar_tarea(id: int, request: Request):
    payload = await request.json()
    for tarea in tareas_db:
        if tarea["id"] == id:
            if "descripcion" in payload:
                nueva_desc = payload["descripcion"].strip()
                if not nueva_desc:
                    return JSONResponse({"detail": "La descripción no puede estar vacía"}, status_code=422)
                tarea["descripcion"] = nueva_desc
            if "estado" in payload:
                nuevo_estado = payload["estado"]
                if nuevo_estado not in VALID_ESTADOS:
                    return JSONResponse({"detail": "Estado inválido"}, status_code=422)
                tarea["estado"] = nuevo_estado
            return JSONResponse(tarea, status_code=200)
    return JSONResponse({"detail": "error: La tarea no existe"}, status_code=404)


# 🟢 5. Eliminar una tarea
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    for tarea in tareas_db:
        if tarea["id"] == id:
            tareas_db.remove(tarea)
            return JSONResponse({"mensaje": "Tarea eliminada"}, status_code=200)
    return JSONResponse({"detail": "error: La tarea no existe"}, status_code=404)


# 🟢 6. Resumen de tareas
@app.get("/tareas/resumen")
def resumen_tareas():
    resumen = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for t in tareas_db:
        if t["estado"] in resumen:
            resumen[t["estado"]] += 1
    return JSONResponse(resumen, status_code=200)
