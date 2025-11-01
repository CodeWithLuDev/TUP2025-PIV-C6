import sqlite3
from typing import Dict, Any

DB_NAME = "tareas.db"

def init_db() -> None:
    """
    Crea las tablas proyectos y tareas si no existen.
    """
    with sqlite3.connect(DB_NAME) as conn:
        conn.execute("PRAGMA foreign_keys = ON")
        cur = conn.cursor()
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        )
        """)
        
        cur.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT,
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
        """)
        
        conn.commit()

def get_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.execute("PRAGMA foreign_keys = ON")
    conn.row_factory = sqlite3.Row
    return conn

def row_to_dict(row: sqlite3.Row) -> Dict[str, Any]:
    return dict(row) if row else None