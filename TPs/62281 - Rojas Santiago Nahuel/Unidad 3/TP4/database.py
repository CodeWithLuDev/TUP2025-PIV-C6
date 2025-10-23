import sqlite3
from contextlib import contextmanager
from datetime import datetime

db_name = "tareas.db"

@contextmanager
def get_db():
    conn = sqlite3.connect(db_name)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
    finally:
        conn.close()

def init_db():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("pragma foreign_keys = on")
        
        cursor.execute("""
            create table if not exists proyectos (
                id integer primary key autoincrement,
                nombre text not null unique,
                descripcion text,
                fecha_creacion text not null
            )
        """)
        
        cursor.execute("""
            create table if not exists tareas (
                id integer primary key autoincrement,
                descripcion text not null,
                estado text not null,
                prioridad text not null,
                proyecto_id integer not null,
                fecha_creacion text not null,
                foreign key (proyecto_id) references proyectos(id) on delete cascade
            )
        """)
        
        conn.commit()

def insertar_datos_prueba():
    with get_db() as conn:
        cursor = conn.cursor()
        
        cursor.execute("pragma foreign_keys = on")
        
        cursor.execute("select count(*) as total from proyectos")
        if cursor.fetchone()["total"] == 0:
            fecha_actual = datetime.now().isoformat()
            
            proyectos = [
                ("proyecto alpha", "primer proyecto de prueba", fecha_actual),
                ("proyecto beta", "segundo proyecto de prueba", fecha_actual),
                ("proyecto gamma", "tercer proyecto de prueba", fecha_actual)
            ]
            
            cursor.executemany(
                "insert into proyectos (nombre, descripcion, fecha_creacion) values (?, ?, ?)",
                proyectos
            )
            
            tareas = [
                ("implementar login", "pendiente", "alta", 1, fecha_actual),
                ("diseñar base de datos", "completada", "alta", 1, fecha_actual),
                ("crear api rest", "en_progreso", "media", 1, fecha_actual),
                ("escribir tests", "pendiente", "baja", 1, fecha_actual),
                ("documentar codigo", "pendiente", "media", 1, fecha_actual),
                ("configurar servidor", "completada", "alta", 2, fecha_actual),
                ("instalar dependencias", "completada", "media", 2, fecha_actual),
                ("crear frontend", "en_progreso", "alta", 2, fecha_actual),
                ("optimizar queries", "pendiente", "baja", 3, fecha_actual),
                ("refactorizar codigo", "pendiente", "media", 3, fecha_actual)
            ]
            
            cursor.executemany(
                """insert into tareas (descripcion, estado, prioridad, proyecto_id, fecha_creacion)
                   values (?, ?, ?, ?, ?)""",
                tareas
            )
            
            conn.commit()

if __name__ == "__main__":
    init_db()
    insertar_datos_prueba()
    print("base de datos inicializada con datos de prueba")