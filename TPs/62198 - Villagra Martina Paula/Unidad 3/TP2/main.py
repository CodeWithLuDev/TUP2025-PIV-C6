# Importamos las librerías necesarias
from fastapi import FastAPI, HTTPException  # FastAPI para crear la API, HTTPException para manejar errores
from pydantic import BaseModel  # Para definir la estructura de las tareas
from datetime import datetime  # Para agregar la fecha de creación
from typing import List, Optional  # Para manejar listas y parámetros opcionales

# Definimos el modelo de una tarea completa (lo que se devuelve)
class Tarea(BaseModel):
    id: int  # Identificador único de la tarea
    descripcion: str  # Descripción de la tarea
    estado: str  # Estado: "pendiente", "en_progreso" o "completada"
    fecha_creacion: datetime  # Fecha y hora de creación

# Modelo para crear/actualizar tareas (sin id ni fecha, se generan automáticamente)
class TareaCreate(BaseModel):
    descripcion: str  # Obligatorio
    estado: str = "pendiente"  # Por defecto es "pendiente"

# Creamos la aplicación FastAPI
app = FastAPI()

# Lista para almacenar tareas en memoria (se borra al reiniciar)
tareas = []
# Contador para asignar IDs únicos a las tareas
contador_id = 1

@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la API de Gestión de Tareas"}

# Ruta GET /tareas: Obtener todas las tareas, con filtros opcionales
@app.get("/tareas", response_model=List[dict])
def obtener_tareas(estado: Optional[str] = None, texto: Optional[str] = None):
    # Si no hay tareas en general
    if not tareas:
        raise HTTPException(status_code=404, detail={"error": "No hay tareas disponibles"})

    resultado = tareas.copy()  # Copiamos la lista original

    # --- FILTRO POR ESTADO ---
    if estado:
        estados_validos = ["pendiente", "en_progreso", "completada"]

        # Si el estado no es válido
        if estado not in estados_validos:
            raise HTTPException(
                status_code=400,
                detail={"error": f"Estado '{estado}' no permitido. Solo se permiten: {', '.join(estados_validos)}"}
            )

        # Filtramos tareas por estado
        resultado = [t for t in resultado if t["estado"].lower() == estado.lower()]

        # Si no hay tareas con ese estado
        if not resultado:
            raise HTTPException(
                status_code=404,
                detail={"error": f"No hay tareas con estado '{estado}'"}
            )

    # --- FILTRO POR TEXTO ---
    if texto:
        resultado = [t for t in resultado if texto.lower() in t["descripcion"].lower()]

        # Si no hay coincidencias de texto
        if not resultado:
            raise HTTPException(
                status_code=404,
                detail={"error": f"No hay tareas que contengan '{texto}'"}
            )

    # Si llegamos acá, devolvemos las tareas filtradas (o todas)
    return resultado

# Ruta POST /tareas: Crear una nueva tarea
@app.post("/tareas", response_model=Tarea)
def crear_tarea(tarea: TareaCreate):
    global contador_id  # Usamos el contador global
    
    # Validamos que la descripción no esté vacía
    if not tarea.descripcion.strip():
        raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
    
    # Validamos que el estado sea correcto
    if tarea.estado not in ["pendiente", "en_progreso", "completada"]:
        raise HTTPException(status_code=400, detail={"error": "Estado inválido. Debe ser 'pendiente', 'en_progreso' o 'completada'"})
    
    # Creamos la nueva tarea como un diccionario
    nueva_tarea = {
        "id": contador_id,
        "descripcion": tarea.descripcion,
        "estado": tarea.estado,
        "fecha_creacion": datetime.now()
    }
    tareas.append(nueva_tarea)  # Agregamos la tarea a la lista
    contador_id += 1  # Incrementamos el contador
    return nueva_tarea  # Devolvemos la tarea creada

# Ruta PUT /tareas/{id}: Actualizar una tarea existente
@app.put("/tareas/{id}", response_model=Tarea)
def actualizar_tarea(id: int, tarea_update: TareaCreate):
    # Buscamos la tarea por ID
    for t in tareas:
        if t["id"] == id:
            # Validamos descripción y estado
            if not tarea_update.descripcion.strip():
                raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
            
            if tarea_update.estado not in ["pendiente", "en_progreso", "completada"]:
                raise HTTPException(status_code=400, detail={"error": "Estado inválido. Debe ser 'pendiente', 'en_progreso' o 'completada'"})
            
            # Actualizamos los campos
            t["descripcion"] = tarea_update.descripcion
            t["estado"] = tarea_update.estado
            return t  # Devolvemos la tarea actualizada
    
    # Si no se encuentra la tarea
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

# Ruta DELETE /tareas/{id}: Eliminar una tarea
@app.delete("/tareas/{id}")
def eliminar_tarea(id: int):
    global tareas  # Modificamos la lista global
    
    # Buscamos la tarea por ID
    for i, t in enumerate(tareas):
        if t["id"] == id:
            del tareas[i]  # Eliminamos la tarea
            return {"mensaje": "Tarea eliminada exitosamente"}
    
    # Si no se encuentra
    raise HTTPException(status_code=404, detail={"error": "La tarea no existe"})

# Ruta GET /tareas/resumen: Contar tareas por estado
@app.get("/tareas/resumen")
def resumen_tareas():
    # Inicializamos contadores
    conteo = {
        "pendiente": 0,
        "en_progreso": 0,
        "completada": 0
    }
    
    # Contamos tareas por estado
    for t in tareas:
        if t["estado"] in conteo:
            conteo[t["estado"]] += 1
    
    return conteo  # Devolvemos el conteo en JSON

# Ruta PUT /tareas/completar_todas: Marca todas las tareas como completadas
@app.put("/tareas/completar_todas")
def completar_todas():
    if not tareas:
        raise HTTPException(status_code=404, detail={"error": "No hay tareas para completar"})
    
    for t in tareas:
        t["estado"] = "completada"
    
    return {"mensaje": f"Se completaron {len(tareas)} tareas exitosamente"}