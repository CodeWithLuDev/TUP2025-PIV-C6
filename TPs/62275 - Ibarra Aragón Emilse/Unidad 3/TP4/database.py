import sqlite3
from typing import Optional, List, Dict, Any
from datetime import datetime

DB_NAME = "tareas.db"

# ============== INICIALIZACIÓN ==============

def init_db():
    """
    Inicializa la base de datos y crea las tablas si no existen.
    Configura las claves foráneas con CASCADE DELETE.
    """
    conn = sqlite3.connect(DB_NAME)
    cursor = conn.cursor()
    
    # Habilitar claves foráneas
    cursor.execute("PRAGMA foreign_keys = ON")
    
    # Crear tabla proyectos
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        )
    """)
    
    # Crear tabla tareas con clave foránea
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media',
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    """)
    
    conn.commit()
    conn.close()

def get_db_connection():
    """Obtiene una conexión a la base de datos con row_factory"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row
    # Habilitar claves foráneas en cada conexión
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

# ============== FUNCIONES PARA PROYECTOS ==============

def crear_proyecto(nombre: str, descripcion: Optional[str] = None) -> Dict[str, Any]:
    """Crea un nuevo proyecto"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fecha_actual = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO proyectos (nombre, descripcion, fecha_creacion)
        VALUES (?, ?, ?)
    """, (nombre, descripcion, fecha_actual))
    
    conn.commit()
    proyecto_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": proyecto_id,
        "nombre": nombre,
        "descripcion": descripcion,
        "fecha_creacion": fecha_actual
    }

def obtener_todos_proyectos(nombre_filtro: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtiene todos los proyectos con filtro opcional por nombre"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if nombre_filtro:
        cursor.execute("""
            SELECT * FROM proyectos 
            WHERE nombre LIKE ?
            ORDER BY id
        """, (f"%{nombre_filtro}%",))
    else:
        cursor.execute("SELECT * FROM proyectos ORDER BY id")
    
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def obtener_proyecto_por_id(proyecto_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene un proyecto por su ID con contador de tareas"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        return None
    
    # Contar tareas
    cursor.execute("""
        SELECT COUNT(*) as total 
        FROM tareas 
        WHERE proyecto_id = ?
    """, (proyecto_id,))
    
    total_tareas = cursor.fetchone()["total"]
    conn.close()
    
    resultado = dict(proyecto)
    resultado["total_tareas"] = total_tareas
    
    return resultado

def actualizar_proyecto(proyecto_id: int, nombre: Optional[str] = None, 
                       descripcion: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Actualiza un proyecto existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto_actual = cursor.fetchone()
    
    if not proyecto_actual:
        conn.close()
        return None
    
    # Actualizar campos proporcionados
    nuevo_nombre = nombre if nombre is not None else proyecto_actual["nombre"]
    nueva_descripcion = descripcion if descripcion is not None else proyecto_actual["descripcion"]
    
    cursor.execute("""
        UPDATE proyectos 
        SET nombre = ?, descripcion = ?
        WHERE id = ?
    """, (nuevo_nombre, nueva_descripcion, proyecto_id))
    
    conn.commit()
    
    # Obtener proyecto actualizado
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto_actualizado = cursor.fetchone()
    conn.close()
    
    return dict(proyecto_actualizado)

def eliminar_proyecto(proyecto_id: int) -> Optional[int]:
    """
    Elimina un proyecto y retorna el número de tareas eliminadas.
    Retorna None si el proyecto no existe.
    """
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si existe
    cursor.execute("SELECT * FROM proyectos WHERE id = ?", (proyecto_id,))
    if not cursor.fetchone():
        conn.close()
        return None
    
    # Contar tareas antes de eliminar
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    tareas_eliminadas = cursor.fetchone()["total"]
    
    # Eliminar proyecto (CASCADE eliminará las tareas automáticamente)
    cursor.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
    
    conn.commit()
    conn.close()
    
    return tareas_eliminadas

def verificar_nombre_proyecto_duplicado(nombre: str, excluir_id: Optional[int] = None) -> bool:
    """Verifica si existe un proyecto con el mismo nombre"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    if excluir_id:
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM proyectos 
            WHERE nombre = ? AND id != ?
        """, (nombre, excluir_id))
    else:
        cursor.execute("""
            SELECT COUNT(*) as total 
            FROM proyectos 
            WHERE nombre = ?
        """, (nombre,))
    
    existe = cursor.fetchone()["total"] > 0
    conn.close()
    
    return existe

# ============== FUNCIONES PARA TAREAS ==============

def crear_tarea(descripcion: str, proyecto_id: int, estado: str = "pendiente", 
                prioridad: str = "media") -> Dict[str, Any]:
    """Crea una nueva tarea"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    fecha_actual = datetime.now().isoformat()
    
    cursor.execute("""
        INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
        VALUES (?, ?, ?, ?, ?)
    """, (descripcion, estado, prioridad, proyecto_id, fecha_actual))
    
    conn.commit()
    tarea_id = cursor.lastrowid
    conn.close()
    
    return {
        "id": tarea_id,
        "descripcion": descripcion,
        "estado": estado,
        "prioridad": prioridad,
        "proyecto_id": proyecto_id,
        "fecha_creacion": fecha_actual
    }

def obtener_todas_tareas(estado: Optional[str] = None, prioridad: Optional[str] = None,
                         proyecto_id: Optional[int] = None, orden: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtiene todas las tareas con filtros opcionales"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    query = "SELECT * FROM tareas WHERE 1=1"
    params = []
    
    if estado:
        query += " AND estado = ?"
        params.append(estado)
    
    if prioridad:
        query += " AND prioridad = ?"
        params.append(prioridad)
    
    if proyecto_id:
        query += " AND proyecto_id = ?"
        params.append(proyecto_id)
    
    # Ordenamiento
    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    elif orden == "asc":
        query += " ORDER BY fecha_creacion ASC"
    else:
        query += " ORDER BY id"
    
    cursor.execute(query, params)
    rows = cursor.fetchall()
    conn.close()
    
    return [dict(row) for row in rows]

def obtener_tareas_por_proyecto(proyecto_id: int, estado: Optional[str] = None,
                                prioridad: Optional[str] = None, 
                                orden: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtiene todas las tareas de un proyecto específico"""
    return obtener_todas_tareas(estado=estado, prioridad=prioridad, 
                               proyecto_id=proyecto_id, orden=orden)

def obtener_tarea_por_id(tarea_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene una tarea por su ID"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea = cursor.fetchone()
    conn.close()
    
    return dict(tarea) if tarea else None

def actualizar_tarea(tarea_id: int, descripcion: Optional[str] = None,
                    estado: Optional[str] = None, prioridad: Optional[str] = None,
                    proyecto_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Actualiza una tarea existente"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea_actual = cursor.fetchone()
    
    if not tarea_actual:
        conn.close()
        return None
    
    # Actualizar campos proporcionados
    nueva_descripcion = descripcion if descripcion is not None else tarea_actual["descripcion"]
    nuevo_estado = estado if estado is not None else tarea_actual["estado"]
    nueva_prioridad = prioridad if prioridad is not None else tarea_actual["prioridad"]
    nuevo_proyecto_id = proyecto_id if proyecto_id is not None else tarea_actual["proyecto_id"]
    
    cursor.execute("""
        UPDATE tareas 
        SET descripcion = ?, estado = ?, prioridad = ?, proyecto_id = ?
        WHERE id = ?
    """, (nueva_descripcion, nuevo_estado, nueva_prioridad, nuevo_proyecto_id, tarea_id))
    
    conn.commit()
    
    # Obtener tarea actualizada
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    tarea_actualizada = cursor.fetchone()
    conn.close()
    
    return dict(tarea_actualizada)

def eliminar_tarea(tarea_id: int) -> bool:
    """Elimina una tarea. Retorna True si existía, False si no"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar si existe
    cursor.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,))
    if not cursor.fetchone():
        conn.close()
        return False
    
    cursor.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    
    return True

def verificar_proyecto_existe(proyecto_id: int) -> bool:
    """Verifica si un proyecto existe"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("SELECT COUNT(*) as total FROM proyectos WHERE id = ?", (proyecto_id,))
    existe = cursor.fetchone()["total"] > 0
    conn.close()
    
    return existe

# ============== FUNCIONES DE RESUMEN Y ESTADÍSTICAS ==============

def obtener_resumen_proyecto(proyecto_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene resumen estadístico de un proyecto"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Verificar que el proyecto existe
    cursor.execute("SELECT nombre FROM proyectos WHERE id = ?", (proyecto_id,))
    proyecto = cursor.fetchone()
    
    if not proyecto:
        conn.close()
        return None
    
    # Contar total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", (proyecto_id,))
    total_tareas = cursor.fetchone()["total"]
    
    # Contar por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad 
        FROM tareas 
        WHERE proyecto_id = ?
        GROUP BY estado
    """, (proyecto_id,))
    estados = cursor.fetchall()
    
    # Contar por prioridad
    cursor.execute("""
        SELECT prioridad, COUNT(*) as cantidad 
        FROM tareas 
        WHERE proyecto_id = ?
        GROUP BY prioridad
    """, (proyecto_id,))
    prioridades = cursor.fetchall()
    
    conn.close()
    
    # Construir respuesta
    resumen_estados = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for row in estados:
        resumen_estados[row["estado"]] = row["cantidad"]
    
    resumen_prioridades = {"baja": 0, "media": 0, "alta": 0}
    for row in prioridades:
        resumen_prioridades[row["prioridad"]] = row["cantidad"]
    
    return {
        "proyecto_id": proyecto_id,
        "proyecto_nombre": proyecto["nombre"],
        "total_tareas": total_tareas,
        "por_estado": resumen_estados,
        "por_prioridad": resumen_prioridades
    }

def obtener_resumen_general() -> Dict[str, Any]:
    """Obtiene resumen general de toda la aplicación"""
    conn = get_db_connection()
    cursor = conn.cursor()
    
    # Total de proyectos
    cursor.execute("SELECT COUNT(*) as total FROM proyectos")
    total_proyectos = cursor.fetchone()["total"]
    
    # Total de tareas
    cursor.execute("SELECT COUNT(*) as total FROM tareas")
    total_tareas = cursor.fetchone()["total"]
    
    # Tareas por estado
    cursor.execute("""
        SELECT estado, COUNT(*) as cantidad 
        FROM tareas 
        GROUP BY estado
    """)
    estados = cursor.fetchall()
    
    # Proyecto con más tareas
    cursor.execute("""
        SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        GROUP BY p.id, p.nombre
        ORDER BY cantidad_tareas DESC
        LIMIT 1
    """)
    proyecto_top = cursor.fetchone()
    
    conn.close()
    
    # Construir respuesta
    tareas_por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    for row in estados:
        tareas_por_estado[row["estado"]] = row["cantidad"]
    
    proyecto_con_mas_tareas = None
    if proyecto_top and proyecto_top["cantidad_tareas"] > 0:
        proyecto_con_mas_tareas = {
            "id": proyecto_top["id"],
            "nombre": proyecto_top["nombre"],
            "cantidad_tareas": proyecto_top["cantidad_tareas"]
        }
    
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas_tareas
    }