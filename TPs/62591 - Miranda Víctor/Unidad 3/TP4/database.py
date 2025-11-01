import sqlite3
from datetime import datetime

def get_db():
    """Obtiene una conexión a la base de datos"""
    conn = sqlite3.connect('tareas.db')
    conn.row_factory = sqlite3.Row
    
    conn.execute("PRAGMA foreign_keys = ON")
    return conn

def init_db():
    """Inicializa la base de datos con las tablas necesarias"""
    conn = get_db()
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS proyectos (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            nombre TEXT NOT NULL UNIQUE,
            descripcion TEXT,
            fecha_creacion TEXT NOT NULL
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tareas (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            descripcion TEXT NOT NULL,
            estado TEXT NOT NULL,
            prioridad TEXT NOT NULL,
            proyecto_id INTEGER NOT NULL,
            fecha_creacion TEXT NOT NULL,
            FOREIGN KEY (proyecto_id) REFERENCES proyectos(id) ON DELETE CASCADE
        )
    ''')
    
    conn.commit()
    conn.close()
    print("✅ Base de datos inicializada correctamente")


def verificar_proyecto_existe(proyecto_id: int) -> bool:
    """Verifica si un proyecto existe"""
    conn = get_db()
    cursor = conn.cursor()
    cursor.execute("SELECT id FROM proyectos WHERE id = ?", (proyecto_id,))
    existe = cursor.fetchone() is not None
    conn.close()
    return existe

def obtener_fecha_actual():
    """Retorna la fecha y hora actual en formato ISO"""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")