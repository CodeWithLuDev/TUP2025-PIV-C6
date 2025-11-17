from fastapi import FastAPI, HTTPException, Query, status
from datetime import datetime

# IMPORTACIÓN DE LAS OTRAS CARPETAS
from models import *
from database import *

# APP CON FASTAPI
app = FastAPI(title="TP4 - API Proyectos y Tareas con SQLite")

# ENDPOINTS
@app.get("/", summary="Raíz")
def root():
    return {"mensaje": "API de Tareas con SQLite (TP4)"}
  

""""----------------PROYECTOS----------------"""
# LISTAR TODOS LOS PROYECTOS (con filtro opcional por nombre)
@app.get("/proyectos", response_model=List[ProyectoOut], status_code=status.HTTP_200_OK, summary="Obtener todos los proyectos con filtro opcional por nombre")
def obtener_proyectos(nombre: Optional[str] = Query(default=None)):
    sql = "SELECT * FROM proyecto"
    params: List[Any] = []

    # Si hay filtro por nombre, agregamos la cláusula WHERE
    if nombre:
        sql += " WHERE LOWER(nombre) LIKE ?"
        params.append(f"%{nombre.lower()}%")

    with get_db_connection() as conn:
        cur = conn.execute(sql, params)
        proyectos = cur.fetchall()

        # Si no hay proyectos, devolvemos mensajes diferentes según el caso
        if not proyectos:
            if nombre:
                raise HTTPException(status_code=404, detail={"mensaje": f"No hay proyectos cuyo nombre contenga '{nombre}'."})
            else:
                raise HTTPException(status_code=404, detail={"mensaje": "No hay proyectos registrados."})

        return [proyecto_to_dict(p) for p in proyectos]

# OBTENER UN PROYECTO ESPECÍFICO POR ID
@app.get("/proyectos/{proyecto_id}", status_code=status.HTTP_200_OK, summary="Obtener proyecto específico")
def obtener_proyecto(proyecto_id: int):
    with get_db_connection() as conn:
        # Buscar el proyecto
        cur = conn.execute("SELECT * FROM proyecto WHERE id = ?", (proyecto_id,))
        proyecto = cur.fetchone()

        if not proyecto:
            raise HTTPException(
                status_code=404,
                detail={"error": f"Proyecto con ID {proyecto_id} no encontrado."}
            )

        # Contar las tareas asociadas
        cur = conn.execute(
            "SELECT COUNT(*) AS cantidad_tareas FROM tarea WHERE proyectoId = ?",
            (proyecto_id,)
        )
        cantidad_tareas = cur.fetchone()["cantidad_tareas"]

        # Convertir a dict y agregar el contador
        proyecto_dict = proyecto_to_dict(proyecto)
        proyecto_dict["cantidad_tareas"] = cantidad_tareas

        return proyecto_dict


# CREAR UN PROYECTO VALIDANDO NOMBRE!=VACIO Y DESCRIPCION!=VACIO
@app.post("/proyectos", response_model=ProyectoOut, status_code=status.HTTP_201_CREATED)
def crear_proyecto(proyecto: ProyectoCreate):

    if not proyecto.nombre.strip():
        raise HTTPException(status_code=400, detail={"error": "El nombre no puede estar vacío"})

    fecha = datetime.now().isoformat(timespec="seconds")

    with get_db_connection() as conn:
        cur = conn.execute("""
            INSERT INTO proyecto (nombre, descripcion, fecha_creacion)
            VALUES (?, ?, ?)
        """, (proyecto.nombre.strip(), proyecto.descripcion.strip(), fecha))
        new_id = cur.lastrowid

        cur = conn.execute("SELECT * FROM proyecto WHERE id = ?", (new_id,))
        nueva = cur.fetchone()
        return proyecto_to_dict(nueva)

# MODIFICAR UN PROYECTO EXISTENTE POR ID
@app.put("/proyectos/{proyecto_id}", response_model = ProyectoOut, status_code=status.HTTP_200_OK)
def actualizar_proyecto(proyecto_id : int, proyecto: ProyectoCreate):
    nombre = proyecto.nombre.strip()
    descripcion = (proyecto.descripcion or "").strip()

    if not nombre:
        raise HTTPException(status_code=400, detail={"error": "El nombre no puede estar vacio"})
    
    with get_db_connection() as conn:
        cur = conn.execute("SELECT * FROM proyecto WHERE id = ?", (proyecto_id,))
        proyecto = cur.fetchone()
        if not proyecto:
            raise HTTPException(status_code=404, detail={"error": f"Proyecto con ID {proyecto_id} no encontrado."})
        cur = conn.execute("SELECT * FROM proyecto WHERE nombre = ? AND id != ?", (nombre, proyecto_id,))
        duplicado = cur.fetchall()
        if duplicado:
            raise HTTPException(status_code=409, detail={"error": f"Ya existe un proyecto de nombre: {nombre}."})
        
        conn.execute("UPDATE proyecto SET nombre = ?, descripcion = ? WHERE id = ?", (nombre, descripcion, proyecto_id))
        conn.commit()

        cur = conn.execute("SELECT * FROM proyecto WHERE id = ?", (proyecto_id,))
        actualizado = cur.fetchone()
        return proyecto_to_dict(actualizado)

# BORRAR UN PROYECTO Y SUS TAREAS POR ID DE PROYECTO
@app.delete("/proyectos/{proyecto_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_proyecto(proyecto_id : int):
    with get_db_connection() as conn:
        cur = conn.execute("SELECT * FROM PROYECTO WHERE id = ?", (proyecto_id,))
        proyecto = cur.fetchone()
        if not proyecto:
            raise HTTPException(status_code=404, detail={"error": f"Proyecto con ID {proyecto_id} no encontrado."})
        conn.execute("DELETE FROM proyecto WHERE id = ?", (proyecto_id,))
        conn.commit()
        raise ({"mensaje": "Proyecto y tareas asociadas eliminadas correctamente."})


""""----------------TAREAS----------------"""
# LISTAR TODAS LAS TAREAS DE UN PROYECTO POR ID DE PROYECTO sin filtros
"""@app.get("/proyectos/{proyecto_id}/tareas", response_model=List[TareaOut], status_code=status.HTTP_200_OK, summary="Obtener todas las tareas de un proyecto específico")
def obtener_tareas_proyecto(proyecto_id : int):
    with get_db_connection() as conn:
        cur = conn.execute("SELECT * FROM proyecto WHERE id = ?", (proyecto_id,))
        proyecto = cur.fetchone()
        if not proyecto:
            raise HTTPException(status_code=404, detail={"error": f"Proyecto con ID {proyecto_id} no encontrado."})
        cur = conn.execute("SELECT * FROM tarea WHERE proyectoId = ?", (proyecto_id,))
        tareas = cur.fetchall()
        if not tareas:
            raise HTTPException(status_code=404, detail={"error": f"No hay tareas con IDProyecto: {proyecto_id}"})
        return [tarea_to_dict(t) for t in tareas]
"""
# LISTAR TODAS LAS TAREAS sin filtros (DE TODOS LOS PROYECTOS)
"""@app.get("/tareas", response_model=List[TareaOut], status_code=status.HTTP_200_OK, summary="Obtener todas las tareas")
def obtener_tareas():
    with get_db_connection() as conn:
        cur = conn.execute("SELECT * FROM tarea")
        tareas = cur.fetchall()
        if tareas:
            return [tarea_to_dict(t) for t in tareas]
        raise HTTPException(status_code=404, detail={"mensaje": "No hay tareas registradas."})
"""

# LISTAR TODAS LAS TAREAS DE UN PROYECTO POR ID, CON FILTROS OPCIONALES
@app.get("/proyectos/{proyecto_id}/tareas",
    response_model=List[TareaOut],
    status_code=status.HTTP_200_OK,
    summary="Obtener todas las tareas de un proyecto específico con filtros opcionales"
)
def obtener_tareas_proyecto(
    proyecto_id: int,
    estado: Optional[str] = Query(default=None),
    prioridad: Optional[str] = Query(default=None),
    orden: Optional[str] = Query(default="asc", regex="^(asc|desc)$")
):
    VALID_ORDER = ["asc", "desc"]

    # Validaciones de valores permitidos
    if estado and estado not in VALID_STATES:
        raise HTTPException(status_code=400, detail={"error": f"Estado '{estado}' no permitido"})
    if prioridad and prioridad not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail={"error": f"Prioridad '{prioridad}' no permitida"})
    if orden and orden not in VALID_ORDER:
        raise HTTPException(status_code=400, detail={"error": f"Orden '{orden}' no permitida"})

    with get_db_connection() as conn:
        # Validar que el proyecto exista
        cur = conn.execute("SELECT id FROM proyecto WHERE id = ?", (proyecto_id,))
        proyecto = cur.fetchone()
        if not proyecto:
            raise HTTPException(status_code=404, detail={"error": f"Proyecto con ID {proyecto_id} no encontrado."})

        # Construcción dinámica del SQL
        sql = "SELECT * FROM tarea WHERE proyectoId = ?"
        params: List[Any] = [proyecto_id]

        if estado:
            sql += " AND estado = ?"
            params.append(estado)
        if prioridad:
            sql += " AND prioridad = ?"
            params.append(prioridad)

        # Ordenamiento opcional
        if orden:
            sql += " ORDER BY fecha_creacion " + ("ASC" if orden == "asc" else "DESC")

        cur = conn.execute(sql, params)
        tareas = cur.fetchall()

        if not tareas:
            raise HTTPException(
                status_code=404,
                detail={"error": f"No hay tareas que coincidan con los filtros aplicados para el proyecto {proyecto_id}."}
            )
        return [tarea_to_dict(t) for t in tareas]

# LISTAR TODAS LAS TAREAS con filtros opcionales por ESTADO, PRIORIDAD Y PROYECTO ID (DE TODOS LOS PROYECTOS)
@app.get("/tareas", response_model=List[TareaOut],
    status_code=status.HTTP_200_OK,
    summary="Obtener todas las tareas con filtros opcionales"
)
def obtener_tareas(
    estado: Optional[str] = Query(default=None),
    prioridad: Optional[str] = Query(default=None),
    orden: Optional[str] = Query(default="asc", regex="^(asc|desc)$"),
    proyecto_id: Optional[int] = Query(default=None)
):
    VALID_ORDER = ["asc", "desc"]

    # Validaciones de valores permitidos
    if estado and estado not in VALID_STATES:
        raise HTTPException(status_code=400, detail={"error": f"Estado '{estado}' no permitido"})
    if prioridad and prioridad not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail={"error": f"Prioridad '{prioridad}' no permitida"})
    if orden and orden not in VALID_ORDER:
        raise HTTPException(status_code=400, detail={"error": f"Orden '{orden}' no permitida"})

    with get_db_connection() as conn:
        # Validar existencia del proyecto antes de buscar tareas
        if proyecto_id is not None:
            cur = conn.execute("SELECT id FROM proyecto WHERE id = ?", (proyecto_id,))
            proyecto = cur.fetchone()
            if not proyecto:
                raise HTTPException(status_code=404, detail={"error": f"El proyecto con ID {proyecto_id} no existe."})

        # Construcción dinámica del SQL
        sql = "SELECT * FROM tarea"
        params: List[Any] = []
        where_clauses: List[str] = []

        if estado:
            where_clauses.append("estado = ?")
            params.append(estado)
        if prioridad:
            where_clauses.append("prioridad = ?")
            params.append(prioridad)
        if proyecto_id:
            where_clauses.append("proyectoId = ?")
            params.append(proyecto_id)
        
        if where_clauses:
            sql += " WHERE " + " AND ".join(where_clauses)

        if orden:
            sql += " ORDER BY fecha_creacion " + ("ASC" if orden == "asc" else "DESC")

        cur = conn.execute(sql, params)
        tareas = cur.fetchall()

        # Si no hay resultados
        if not tareas:
            raise HTTPException(status_code=404, detail={"error": "No hay tareas que coincidan con los filtros aplicados."})

        return [dict(t) for t in tareas]

# CREAR UNA TAREA DENTRO DE UN PROYECTO VALIDANDO DESCRIPCIION!=VACIO, ESTADO IN VALID_STATES, PRIORIDAD IN VALID_PRIORITIES Y PROYECTOID EXISTA EN PROYECTOS
@app.post("/tareas", response_model=TareaOut, status_code=status.HTTP_201_CREATED)
def crear_tarea(tarea: TareaCreate):
    descripcion = tarea.descripcion.strip()

    if not descripcion:
        raise HTTPException(status_code=400, detail={"error": "La descripción no puede estar vacía"})
    if tarea.estado not in VALID_STATES:
        raise HTTPException(status_code=400, detail={"error": "Estado inválido"})
    if tarea.prioridad not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail={"error": "Prioridad inválida"})

    fecha = datetime.now().isoformat(timespec="seconds")

    with get_db_connection() as conn:
        cur = conn.execute("SELECT id FROM proyecto WHERE id = ?", (tarea.proyectoId,))
        proyecto = cur.fetchone()
        if not proyecto:
            raise HTTPException(status_code=400, detail={"error": f"No hay proyecto con id: {tarea.proyectoId}"})
        
        cur = conn.execute("""
            INSERT INTO tarea (descripcion, estado, prioridad, proyectoId, fecha_creacion)
            VALUES (?, ?, ?, ?, ?)
        """, (descripcion, tarea.estado, tarea.prioridad, tarea.proyectoId, fecha))

        new_id = cur.lastrowid
        cur = conn.execute("SELECT * FROM tarea WHERE id = ?", (new_id,))
        nueva = cur.fetchone()
        return tarea_to_dict(nueva)

# MODIFICAR UNA TAREA INCLUSO SU ID DE PROYECTO
@app.put("/tareas/{tarea_id}", response_model = TareaOut, status_code=status.HTTP_200_OK)
def actualizar_tarea(tarea_id: int, tarea: TareaCreate):
    descripcion = tarea.descripcion.strip()
    estado = tarea.estado
    prioridad = tarea.prioridad
    proyectoId = tarea.proyectoId

    if not descripcion:
        raise HTTPException(status_code=400, detail={"error": "La descripcion no puede estar vacia"})
    if estado not in VALID_STATES:
        raise HTTPException(status_code=400, detail={"error": "El estado no puede estar vacio"})
    if prioridad not in VALID_PRIORITIES:
        raise HTTPException(status_code=400, detail={"error": "La prioridad no puede estar vacia"})
    
    with get_db_connection() as conn:
        cur = conn.execute("SELECT * FROM tarea WHERE id = ?", (tarea_id,))
        tarea = cur.fetchone()
        if not tarea:
            raise HTTPException(status_code=404, detail={"error": f"No existe tarea: {tarea_id}"})
        cur = conn.execute("SELECT * from proyecto WHERE id = ?", (proyectoId,))
        proyecto = cur.fetchone()
        if not proyecto:
            raise HTTPException(status_code=404, detail={"error": f"No existe el proyecto: {proyectoId} que desea modificar"})

        conn.execute("UPDATE tarea SET descripcion = ?, estado = ?, prioridad = ?, proyectoId = ? WHERE id = ?", (descripcion, estado, prioridad, proyectoId, tarea_id))
        conn.commit()

        cur = conn.execute("SELECT * FROM tarea WHERE Id = ?", (tarea_id,))
        actualizado = cur.fetchone()
        return tarea_to_dict(actualizado)

# ELIMINAR UNA TAREA
@app.delete("/tareas/{tarea_id}", status_code=status.HTTP_204_NO_CONTENT)
def eliminar_tarea(tarea_id: int):
    with get_db_connection() as conn:
        cur = conn.execute("SELECT * FROM tarea WHERE id = ?", (tarea_id,))
        tarea = cur.fetchone()
        if not tarea:
            raise HTTPException(status_code=404, detail={"error": f"No existe tarea con ID: {tarea_id}"})
        conn.execute("DELETE FROM tarea WHERE id = ?", (tarea_id,))
        conn.commit()
        raise ({"mensaje": "Tarea eliminada correctamente."})
    
# LISTAR ESTADISTICAS DE UN PROYECTO
@app.get("/proyectos/{proyecto_id}/resumen")
def estadistica_proyecto(proyecto_id: int):
    with get_db_connection() as conn:
        # Validar que el proyecto exista
        cur = conn.execute("SELECT * FROM proyecto WHERE id = ?", (proyecto_id,))
        proyecto = cur.fetchone()
        if not proyecto:
            raise HTTPException(status_code=404, detail={"error": f"Proyecto con ID {proyecto_id} no encontrado."})

        # Cantidad total de tareas del proyecto
        cur = conn.execute("SELECT COUNT(*) as total FROM tarea WHERE proyectoId = ?", (proyecto_id,))
        total_tareas = cur.fetchone()["total"]

        # Cantidad de tareas por estado
        cur = conn.execute("""
            SELECT estado, COUNT(*) as cantidad 
            FROM tarea 
            WHERE proyectoId = ? 
            GROUP BY estado
        """, (proyecto_id,))
        tareas_por_estado = [dict(row) for row in cur.fetchall()]

        # Cantidad de tareas por prioridad
        cur = conn.execute("""
            SELECT prioridad, COUNT(*) as cantidad 
            FROM tarea 
            WHERE proyectoId = ? 
            GROUP BY prioridad
        """, (proyecto_id,))
        tareas_por_prioridad = [dict(row) for row in cur.fetchall()]

        return {
            "proyecto": {
                "id": proyecto["id"],
                "nombre": proyecto["nombre"],
                "descripcion": proyecto["descripcion"],
                "fecha_creacion": proyecto["fecha_creacion"]
            },
            "total_tareas": total_tareas,
            "por_estado": tareas_por_estado,
            "por_prioridad": tareas_por_prioridad
        }

# UN RESUMEN GENERAL DE TODA MI API
@app.get("/resumen")
def resumen_api():
    with get_db_connection() as conn:
        # Total de proyectos
        cur = conn.execute("SELECT COUNT(*) as total FROM proyecto")
        total_proyectos = cur.fetchone()["total"]

        # Total de tareas
        cur = conn.execute("SELECT COUNT(*) as total FROM tarea")
        total_tareas = cur.fetchone()["total"]

        # Tareas por estado (todas)
        cur = conn.execute("SELECT estado, COUNT(*) as cantidad FROM tarea GROUP BY estado")
        tareas_por_estado = [dict(row) for row in cur.fetchall()]

        # Tareas por prioridad (todas)
        cur = conn.execute("SELECT prioridad, COUNT(*) as cantidad FROM tarea GROUP BY prioridad")
        tareas_por_prioridad = [dict(row) for row in cur.fetchall()]

        # Promedio de tareas por proyecto
        promedio_tareas = total_tareas / total_proyectos if total_proyectos > 0 else 0

        # Proyecto con más tareas
        # Usamos LEFT JOIN para incluir proyectos sin tareas (cantidad 0)
        cur = conn.execute("""
            SELECT p.id, p.nombre, COUNT(t.id) AS cantidad_tareas
            FROM proyecto p
            LEFT JOIN tarea t ON p.id = t.proyectoId
            GROUP BY p.id
            ORDER BY cantidad_tareas DESC
            LIMIT 1
        """)
        top = cur.fetchone()
        if top:
            proyecto_con_mas_tareas = {
                "id": top["id"],
                "nombre": top["nombre"],
                "cantidad_tareas": top["cantidad_tareas"]
            }
        else:
            proyecto_con_mas_tareas = None

        return {
            "resumen_general": {
                "total_proyectos": total_proyectos,
                "total_tareas": total_tareas,
                "promedio_tareas_por_proyecto": round(promedio_tareas, 2),
                "tareas_por_estado": tareas_por_estado,
                "tareas_por_prioridad": tareas_por_prioridad,
                "proyecto_con_mas_tareas": proyecto_con_mas_tareas
            }
        }