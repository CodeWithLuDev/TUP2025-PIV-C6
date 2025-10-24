import sqlite3
from datetime import datetime
from typing import Optional, List, Dict, Any


# ==================== CONFIGURACIÓN ====================

DB_NAME = "tareas.db"


# ==================== CONEXIÓN ====================

def get_db_connection():
    """Establece conexión con la base de datos SQLite"""
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Permite acceder a columnas por nombre
    # Habilitar claves foráneas (importante para CASCADE)
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


# ==================== INICIALIZACIÓN ====================

def init_db():
    """Inicializa la base de datos y crea las tablas si no existen"""
    conn = get_db_connection()
    
    # Crear tabla de proyectos
    conn.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        )
    ''')
    
    # Crear tabla de tareas con relación a proyectos
    conn.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL DEFAULT 'media',
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()


# ==================== FUNCIONES DE PROYECTOS ====================

def obtener_todos_proyectos(nombre: Optional[str] = None) -> List[Dict[str, Any]]:
    """Obtiene todos los proyectos con filtro opcional por nombre"""
    conn = get_db_connection()
    query = "SELECT * FROM proyectos WHERE 1=1"
    params = []
    
    if nombre:
        query += " AND nombre LIKE ?"
        params.append(f"%{nombre}%")
    
    query += " ORDER BY fecha_creacion DESC"
    proyectos = conn.execute(query, params).fetchall()
    conn.close()
    
    return [dict(proyecto) for proyecto in proyectos]


def obtener_proyecto_por_id(proyecto_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene un proyecto específico por ID con contador de tareas"""
    conn = get_db_connection()
    
    proyecto = conn.execute(
        "SELECT * FROM proyectos WHERE id = ?", (proyecto_id,)
    ).fetchone()
    
    if not proyecto:
        conn.close()
        return None
    
    # Contar tareas asociadas
    cantidad_tareas = conn.execute(
        "SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?", 
        (proyecto_id,)
    ).fetchone()
    
    conn.close()
    
    proyecto_dict = dict(proyecto)
    proyecto_dict['total_tareas'] = cantidad_tareas['total']  # Cambiar a 'total_tareas'
    return proyecto_dict


def crear_proyecto(nombre: str, descripcion: Optional[str] = None) -> Dict[str, Any]:
    """Crea un nuevo proyecto"""
    conn = get_db_connection()
    fecha_creacion = datetime.now().isoformat()
    
    cursor = conn.execute(
        "INSERT INTO proyectos (nombre, descripcion, fecha_creacion) VALUES (?, ?, ?)",
        (nombre, descripcion, fecha_creacion)
    )
    conn.commit()
    
    nuevo_proyecto = conn.execute(
        "SELECT * FROM proyectos WHERE id = ?", 
        (cursor.lastrowid,)
    ).fetchone()
    conn.close()
    
    return dict(nuevo_proyecto)


def actualizar_proyecto(proyecto_id: int, nombre: Optional[str] = None, 
                       descripcion: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Actualiza un proyecto existente"""
    conn = get_db_connection()
    
    proyecto = conn.execute(
        "SELECT * FROM proyectos WHERE id = ?", (proyecto_id,)
    ).fetchone()
    
    if not proyecto:
        conn.close()
        return None
    
    campos = []
    valores = []
    
    if nombre is not None:
        campos.append("nombre = ?")
        valores.append(nombre)
    
    if descripcion is not None:
        campos.append("descripcion = ?")
        valores.append(descripcion)
    
    if not campos:
        conn.close()
        return dict(proyecto)
    
    valores.append(proyecto_id)
    query = f"UPDATE proyectos SET {', '.join(campos)} WHERE id = ?"
    
    conn.execute(query, valores)
    conn.commit()
    
    proyecto_actualizado = conn.execute(
        "SELECT * FROM proyectos WHERE id = ?", (proyecto_id,)
    ).fetchone()
    conn.close()
    
    return dict(proyecto_actualizado)


def eliminar_proyecto(proyecto_id: int) -> bool:
    """Elimina un proyecto y sus tareas asociadas (CASCADE)"""
    conn = get_db_connection()
    
    proyecto = conn.execute(
        "SELECT * FROM proyectos WHERE id = ?", (proyecto_id,)
    ).fetchone()
    
    if not proyecto:
        conn.close()
        return False
    
    conn.execute("DELETE FROM proyectos WHERE id = ?", (proyecto_id,))
    conn.commit()
    conn.close()
    
    return True


def verificar_nombre_proyecto_unico(nombre: str, excluir_id: Optional[int] = None) -> bool:
    """Verifica si un nombre de proyecto ya existe (para validación de duplicados)"""
    conn = get_db_connection()
    query = "SELECT COUNT(*) as total FROM proyectos WHERE nombre = ?"
    params = [nombre]
    
    if excluir_id:
        query += " AND id != ?"
        params.append(excluir_id)
    
    resultado = conn.execute(query, params).fetchone()
    conn.close()
    
    return resultado['total'] == 0


# ==================== FUNCIONES DE TAREAS ====================

def obtener_todas_tareas(estado: Optional[str] = None, 
                        prioridad: Optional[str] = None,
                        proyecto_id: Optional[int] = None,
                        orden: Optional[str] = "asc") -> List[Dict[str, Any]]:
    """Obtiene todas las tareas con filtros opcionales"""
    conn = get_db_connection()
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
    
    if orden == "desc":
        query += " ORDER BY fecha_creacion DESC"
    else:
        query += " ORDER BY fecha_creacion ASC"
    
    tareas = conn.execute(query, params).fetchall()
    conn.close()
    
    return [dict(tarea) for tarea in tareas]


def obtener_tareas_por_proyecto(proyecto_id: int, estado: Optional[str] = None,
                                prioridad: Optional[str] = None,
                                orden: Optional[str] = "asc") -> List[Dict[str, Any]]:
    """Obtiene las tareas de un proyecto específico con filtros opcionales"""
    return obtener_todas_tareas(estado=estado, prioridad=prioridad, 
                               proyecto_id=proyecto_id, orden=orden)


def obtener_tarea_por_id(tarea_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene una tarea específica por ID"""
    conn = get_db_connection()
    tarea = conn.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,)).fetchone()
    conn.close()
    
    return dict(tarea) if tarea else None


def crear_tarea(descripcion: str, estado: str, prioridad: str, 
               proyecto_id: int) -> Dict[str, Any]:
    """Crea una nueva tarea asociada a un proyecto"""
    conn = get_db_connection()
    fecha_creacion = datetime.now().isoformat()
    
    cursor = conn.execute(
        "INSERT INTO tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion) VALUES (?, ?, ?, ?, ?)",
        (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
    )
    conn.commit()
    
    nueva_tarea = conn.execute(
        "SELECT * FROM tareas WHERE id = ?", 
        (cursor.lastrowid,)
    ).fetchone()
    conn.close()
    
    return dict(nueva_tarea)


def actualizar_tarea(tarea_id: int, descripcion: Optional[str] = None,
                    estado: Optional[str] = None, prioridad: Optional[str] = None,
                    proyecto_id: Optional[int] = None) -> Optional[Dict[str, Any]]:
    """Actualiza una tarea existente"""
    conn = get_db_connection()
    
    tarea = conn.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,)).fetchone()
    
    if not tarea:
        conn.close()
        return None
    
    campos = []
    valores = []
    
    if descripcion is not None:
        campos.append("descripcion = ?")
        valores.append(descripcion)
    
    if estado is not None:
        campos.append("estado = ?")
        valores.append(estado)
    
    if prioridad is not None:
        campos.append("prioridad = ?")
        valores.append(prioridad)
    
    if proyecto_id is not None:
        campos.append("proyecto_id = ?")
        valores.append(proyecto_id)
    
    if not campos:
        conn.close()
        return dict(tarea)
    
    valores.append(tarea_id)
    query = f"UPDATE tareas SET {', '.join(campos)} WHERE id = ?"
    
    conn.execute(query, valores)
    conn.commit()
    
    tarea_actualizada = conn.execute(
        "SELECT * FROM tareas WHERE id = ?", (tarea_id,)
    ).fetchone()
    conn.close()
    
    return dict(tarea_actualizada)


def eliminar_tarea(tarea_id: int) -> bool:
    """Elimina una tarea existente"""
    conn = get_db_connection()
    tarea = conn.execute("SELECT * FROM tareas WHERE id = ?", (tarea_id,)).fetchone()
    
    if not tarea:
        conn.close()
        return False
    
    conn.execute("DELETE FROM tareas WHERE id = ?", (tarea_id,))
    conn.commit()
    conn.close()
    
    return True


# ==================== FUNCIONES DE RESUMEN Y ESTADÍSTICAS ====================

def obtener_resumen_proyecto(proyecto_id: int) -> Optional[Dict[str, Any]]:
    """Obtiene estadísticas de un proyecto específico"""
    conn = get_db_connection()
    
    proyecto = conn.execute(
        "SELECT * FROM proyectos WHERE id = ?", (proyecto_id,)
    ).fetchone()
    
    if not proyecto:
        conn.close()
        return None
    
    # Contar total de tareas
    total_tareas = conn.execute(
        "SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?",
        (proyecto_id,)
    ).fetchone()['total']
    
    # Contar por estado
    por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    resultados_estado = conn.execute(
        "SELECT estado, COUNT(*) as cantidad FROM tareas WHERE proyecto_id = ? GROUP BY estado",
        (proyecto_id,)
    ).fetchall()
    for row in resultados_estado:
        por_estado[row['estado']] = row['cantidad']
    
    # Contar por prioridad
    por_prioridad = {"baja": 0, "media": 0, "alta": 0}
    resultados_prioridad = conn.execute(
        "SELECT prioridad, COUNT(*) as cantidad FROM tareas WHERE proyecto_id = ? GROUP BY prioridad",
        (proyecto_id,)
    ).fetchall()
    for row in resultados_prioridad:
        por_prioridad[row['prioridad']] = row['cantidad']
    
    conn.close()
    
    return {
        "proyecto_id": proyecto_id,
        "proyecto_nombre": proyecto['nombre'],
        "total_tareas": total_tareas,
        "por_estado": por_estado,
        "por_prioridad": por_prioridad
    }


def obtener_resumen_general() -> Dict[str, Any]:
    """Obtiene resumen general de toda la aplicación"""
    conn = get_db_connection()
    
    # Total de proyectos
    total_proyectos = conn.execute(
        "SELECT COUNT(*) as total FROM proyectos"
    ).fetchone()['total']
    
    # Total de tareas
    total_tareas = conn.execute(
        "SELECT COUNT(*) as total FROM tareas"
    ).fetchone()['total']
    
    # Tareas por estado
    tareas_por_estado = {"pendiente": 0, "en_progreso": 0, "completada": 0}
    resultados_estado = conn.execute(
        "SELECT estado, COUNT(*) as cantidad FROM tareas GROUP BY estado"
    ).fetchall()
    for row in resultados_estado:
        tareas_por_estado[row['estado']] = row['cantidad']
    
    # Proyecto con más tareas
    proyecto_mas_tareas = conn.execute("""
        SELECT p.id, p.nombre, COUNT(t.id) as cantidad_tareas
        FROM proyectos p
        LEFT JOIN tareas t ON p.id = t.proyecto_id
        GROUP BY p.id
        ORDER BY cantidad_tareas DESC
        LIMIT 1
    """).fetchone()
    
    conn.close()
    
    proyecto_con_mas_tareas = None
    if proyecto_mas_tareas:
        proyecto_con_mas_tareas = {
            "id": proyecto_mas_tareas['id'],
            "nombre": proyecto_mas_tareas['nombre'],
            "cantidad_tareas": proyecto_mas_tareas['cantidad_tareas']
        }
    
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas_tareas
    }