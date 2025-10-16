from fastapi import FastAPI, HTTPException, Query
from datetime import datetime
from typing import Optional

app = FastAPI()

tareas = []

id_counter = 0

ESTADOS_VALIDOS = {"pendiente", "en_progreso", "completada"}

def test_validar_estado(estado: str):
    if estado not in ESTADOS_VALIDOS:
        raise HTTPException(status_code=400, detail={"error": "Estado inválido. Debe ser 'pendiente', 'en_progreso' o 'completada'"})

def test_encontrar_tarea_por_id(task_id: int):
    for tarea in tareas:
        if tarea["id"] == task_id:
            return tarea
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

@app.get("/tareas")
def test_obtener_tareas(estado: Optional[str] = Query(None), texto: Optional[str] = Query(None)):

    resultado = tareas[:]
    
    if estado:
        test_validar_estado(estado)  
        resultado = [t for t in resultado if t["estado"] == estado]
    
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]
    
    return resultado

@app.post("/tareas")
def test_crear_tarea(tarea: dict):
    
    global id_counter
    descripcion = tarea.get("descripcion")
    estado = tarea.get("estado", "pendiente")  
    
    if not descripcion or descripcion.strip() == "":
        raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
    
    test_validar_estado(estado)
    
    id_counter += 1
    nueva_tarea = {
        "id": id_counter,
        "descripcion": descripcion,
        "estado": estado,
        "fecha_creacion": datetime.now().isoformat()
    }
    tareas.append(nueva_tarea)
    return nueva_tarea

@app.put("/tareas/{task_id}")
def actualizar_tarea(task_id: int, updates: dict):
    
    tarea = test_encontrar_tarea_por_id(task_id)
    
    if "descripcion" in updates:
        nueva_desc = updates["descripcion"]
        if not nueva_desc or nueva_desc.strip() == "":
            raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
        tarea["descripcion"] = nueva_desc
    
    if "estado" in updates:
        nuevo_estado = updates["estado"]
        test_validar_estado(nuevo_estado)
        tarea["estado"] = nuevo_estado
    
    return tarea

@app.delete("/tareas/{task_id}")
def eliminar_tarea(task_id: int):
    
    tarea = test_encontrar_tarea_por_id(task_id)
    tareas.remove(tarea)
    return {"mensaje": "Tarea eliminada exitosamente"}

@app.get("/tareas/resumen")
def resumen_tareas():
    
    conteo = {estado: 0 for estado in ESTADOS_VALIDOS}
    for tarea in tareas:
        conteo[tarea["estado"]] += 1
    return conteo

