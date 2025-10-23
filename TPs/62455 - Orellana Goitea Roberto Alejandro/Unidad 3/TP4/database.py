"""
Funciones de acceso a la base de datos SQLite.
Maneja la conexión, inicialización y operaciones CRUD.
"""

import sqlite3
from contextlib import contextmanager
from typing import Optional

# Nombre de la base de datos
DB_NAME = "tareas.db"


# ==================== CONTEXT MANAGER ====================

@contextmanager
def get_db():
    """
    Context manager para obtener y cerrar conexiones a la BD.
    Garantiza que la conexión se cierre correctamente incluso si ocurre un error.
    """
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row  # Para acceder a columnas por nombre
    # Activar claves foráneas (necesario en SQLite)
    conn.execute("PRAGMA foreign_keys = ON")
    try:
        yield conn
    finally:
        conn.close()


# ==================== INICIALIZACIÓN ====================

def init_db():
    """
    Crea las tablas proyectos y tareas si no existen.
    Configura la relación 1:N con ON DELETE CASCADE.
    """
    with get_db() as conn:
        cursor = conn.cursor()
        
        # Tabla proyectos
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS proyectos (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT,
                fecha_creacion TEXT NOT NULL
            )
        """)
        
        # Tabla tareas (con clave foránea a proyectos)
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
        print("✓ Base de datos inicializada correctamente")
        print("  - Tabla 'proyectos' creada/verificada")
        print("  - Tabla 'tareas' creada/verificada con relación a proyectos")


# ==================== FUNCIONES AUXILIARES ====================

def row_to_dict(row):
    """
    Convierte una fila de SQLite (sqlite3.Row) a un diccionario.
    Útil para serializar datos para la API.
    """
    return {key: row[key] for key in row.keys()}


def proyecto_exists(conn, proyecto_id: int) -> bool:
    """
    Verifica si existe un proyecto con el ID dado.
    
    Args:
        conn: Conexión a la base de datos
        proyecto_id: ID del proyecto a verificar
    
    Returns:
        True si el proyecto existe, False en caso contrario
    """
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
    return cursor.fetchone() is not None


def nombre_proyecto_duplicado(conn, nombre: str, excluir_id: Optional[int] = None) -> bool:
    """
    Verifica si ya existe un proyecto con el nombre dado.
    
    Args:
        conn: Conexión a la base de datos
        nombre: Nombre del proyecto a verificar
        excluir_id: ID del proyecto a excluir de la búsqueda (para actualizaciones)
    
    Returns:
        True si el nombre está duplicado, False en caso contrario
    """
    cursor = conn.cursor()
    
    if excluir_id:
        cursor.execute(
            "SELECT id FROM proyectos WHERE LOWER(nombre) = LOWER(?) AND id != ?",
            (nombre, excluir_id)
        )
    else:
        cursor.execute(
            "SELECT id FROM proyectos WHERE LOWER(nombre) = LOWER(?)",
            (nombre,)
        )
    
    return cursor.fetchone() is not None


def contar_tareas_proyecto(conn, proyecto_id: int) -> int:
    """
    Cuenta el número de tareas asociadas a un proyecto.
    
    Args:
        conn: Conexión a la base de datos
        proyecto_id: ID del proyecto
    
    Returns:
        Número de tareas del proyecto
    """
    cursor = conn.cursor()
    cursor.execute(
        "SELECT COUNT(*) as total FROM tareas WHERE proyecto_id = ?",
        (proyecto_id,)
    )
    result = cursor.fetchone()
    return result["total"] if result else 0
