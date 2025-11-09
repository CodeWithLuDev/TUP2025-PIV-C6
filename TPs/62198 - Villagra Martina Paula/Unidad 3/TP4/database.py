from typing import Dict, Any
import sqlite3
from contextlib import contextmanager

# CONFIGURACIONES
DB_FILE = "Tareas.db"
VALID_STATES = ["pendiente", "en_progreso", "completada"]
VALID_PRIORITIES = ["baja", "media", "alta"]

# CONEXIÓN A LA DB
@contextmanager
def get_db_connection():
    conn = sqlite3.connect(DB_FILE)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON") #ACTIVA LA CLAVE FORÁNEA DE TAREA
    try:
        yield conn
    finally:
        conn.commit()
        conn.close()

# INICIALIZAR DB
def init_db():
    with get_db_connection() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS proyecto (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                nombre TEXT NOT NULL UNIQUE,
                descripcion TEXT,
                fecha_creacion TEXT NOT NULL
            )         
        """)
        conn.execute("""
            CREATE TABLE IF NOT EXISTS tarea (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                descripcion TEXT NOT NULL,
                estado TEXT NOT NULL,
                prioridad TEXT NOT NULL,
                proyectoId INTEGER NOT NULL,
                fecha_creacion TEXT NOT NULL,
                FOREIGN KEY (proyectoId) REFERENCES proyecto(id) ON DELETE CASCADE
            )
        """)
init_db()

# FILAS A DICCIONARIO <--UNA PARA TABLA PROYECTOS Y OTRA PARA TAREAS
def proyecto_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "nombre": row["nombre"],
        "descripcion": row["descripcion"],
        "fecha_creacion": row["fecha_creacion"]
    }

def tarea_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return {
        "id": row["id"],
        "descripcion": row["descripcion"],
        "estado": row["estado"],
        "prioridad": row["prioridad"],
        "proyectoId": row["proyectoId"],
        "fecha_creacion": row["fecha_creacion"]
    }