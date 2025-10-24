import sqlite3
from typing import Optional, Dict, List, Any

DB_NAME = "tareas.db"

def get_db_connection():
    conn = sqlite3.connect(DB_NAME)
    conn.row_factory = sqlite3.Row 
    conn.execute("PRAGMA foreign_keys = ON") 
    return conn

def init_db():
    conn = get_db_connection()
    cursor = conn.cursor()
    
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        );
    """)

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        );
    """)
    conn.commit()
    conn.close()

def project_exists(project_id: int) -> bool:
    conn = get_db_connection()
    row = conn.execute("SELECT id FROM proyectos WHERE id = ?", (project_id,)).fetchone()
    conn.close()
    return row is not None

def task_exists(task_id: int) -> bool:
    conn = get_db_connection()
    row = conn.execute("SELECT id FROM tareas WHERE id = ?", (task_id,)).fetchone()
    conn.close()
    return row is not None

def get_project_with_task_count(project_id: int) -> Optional[sqlite3.Row]:
    conn = get_db_connection()
    row = conn.execute("""
        SELECT p.*, COUNT(t.id) AS total_tareas 
        FROM proyectos p 
        LEFT JOIN tareas t ON p.id = t.proyecto_id 
        WHERE p.id = ?
        GROUP BY p.id
    """, (project_id,)).fetchone()
    conn.close()
    
    if row and row['id'] is not None:
        return row
    return None

def get_general_summary() -> Dict[str, Any]:
    conn = get_db_connection()
    
    total_proyectos = conn.execute("SELECT COUNT(id) FROM proyectos").fetchone()[0]
    total_tareas = conn.execute("SELECT COUNT(id) FROM tareas").fetchone()[0]

    tareas_por_estado = {
        row['estado']: row['count']
        for row in conn.execute("SELECT estado, COUNT(id) as count FROM tareas GROUP BY estado").fetchall()
    }
    
    proyecto_mas_tareas_row = conn.execute("""
        SELECT 
            p.id, 
            p.nombre, 
            COUNT(t.id) AS cantidad_tareas 
        FROM proyectos p 
        LEFT JOIN tareas t ON p.id = t.proyecto_id 
        GROUP BY p.id, p.nombre
        ORDER BY cantidad_tareas DESC, p.id ASC
        LIMIT 1
    """).fetchone()
    
    conn.close()

    proyecto_con_mas_tareas = None
    if proyecto_mas_tareas_row and proyecto_mas_tareas_row['cantidad_tareas'] > 0:
        proyecto_con_mas_tareas = {
            "id": proyecto_mas_tareas_row['id'],
            "nombre": proyecto_mas_tareas_row['nombre'],
            "cantidad_tareas": proyecto_mas_tareas_row['cantidad_tareas']
        }
    
    return {
        "total_proyectos": total_proyectos,
        "total_tareas": total_tareas,
        "tareas_por_estado": tareas_por_estado,
        "proyecto_con_mas_tareas": proyecto_con_mas_tareas
    }