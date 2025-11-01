import database as db

def poblar_base_datos():
    """Puebla la base de datos con datos de prueba"""
    
    print("🗄️  Poblando base de datos con datos de ejemplo...")
    
    # Inicializar BD
    db.init_db()
    
    # Crear proyectos
    proyectos = [
        {"nombre": "Desarrollo Web", "descripcion": "Aplicación web con FastAPI y React"},
        {"nombre": "App Mobile", "descripcion": "Aplicación móvil multiplataforma con React Native"},
        {"nombre": "Sistema de Inventario", "descripcion": "Sistema de gestión de inventario para empresa"},
        {"nombre": "E-commerce", "descripcion": "Tienda online con pasarela de pagos"},
    ]
    
    proyectos_creados = []
    for proyecto in proyectos:
        p = db.crear_proyecto(**proyecto)
        proyectos_creados.append(p)
        print(f"✅ Proyecto creado: {p['nombre']}")
    
    # Crear tareas para cada proyecto
    tareas_por_proyecto = [
        # Proyecto 1: Desarrollo Web
        [
            {"descripcion": "Diseñar base de datos", "estado": "completada", "prioridad": "alta"},
            {"descripcion": "Implementar API REST", "estado": "en_progreso", "prioridad": "alta"},
            {"descripcion": "Crear interfaz de usuario", "estado": "pendiente", "prioridad": "media"},
            {"descripcion": "Implementar autenticación", "estado": "en_progreso", "prioridad": "alta"},
            {"descripcion": "Escribir tests unitarios", "estado": "pendiente", "prioridad": "media"},
        ],
        # Proyecto 2: App Mobile
        [
            {"descripcion": "Configurar proyecto React Native", "estado": "completada", "prioridad": "alta"},
            {"descripcion": "Diseñar pantallas principales", "estado": "completada", "prioridad": "alta"},
            {"descripcion": "Integrar con API", "estado": "en_progreso", "prioridad": "alta"},
            {"descripcion": "Implementar navegación", "estado": "pendiente", "prioridad": "media"},
            {"descripcion": "Optimizar rendimiento", "estado": "pendiente", "prioridad": "baja"},
        ],
        # Proyecto 3: Sistema de Inventario
        [
            {"descripcion": "Análisis de requisitos", "estado": "completada", "prioridad": "alta"},
            {"descripcion": "Diseño de arquitectura", "estado": "completada", "prioridad": "alta"},
            {"descripcion": "Implementar módulo de productos", "estado": "en_progreso", "prioridad": "alta"},
            {"descripcion": "Implementar módulo de reportes", "estado": "pendiente", "prioridad": "media"},
            {"descripcion": "Capacitación de usuarios", "estado": "pendiente", "prioridad": "baja"},
            {"descripcion": "Documentación técnica", "estado": "pendiente", "prioridad": "media"},
        ],
        # Proyecto 4: E-commerce
        [
            {"descripcion": "Configurar plataforma", "estado": "completada", "prioridad": "alta"},
            {"descripcion": "Diseñar catálogo de productos", "estado": "en_progreso", "prioridad": "alta"},
            {"descripcion": "Integrar pasarela de pagos", "estado": "pendiente", "prioridad": "alta"},
            {"descripcion": "Implementar carrito de compras", "estado": "en_progreso", "prioridad": "alta"},
            {"descripcion": "Sistema de envíos", "estado": "pendiente", "prioridad": "media"},
            {"descripcion": "Panel de administración", "estado": "pendiente", "prioridad": "media"},
            {"descripcion": "SEO y marketing digital", "estado": "pendiente", "prioridad": "baja"},
        ]
    ]
    
    total_tareas = 0
    for i, proyecto in enumerate(proyectos_creados):
        print(f"\n📋 Creando tareas para: {proyecto['nombre']}")
        for tarea_data in tareas_por_proyecto[i]:
            tarea = db.crear_tarea(
                descripcion=tarea_data["descripcion"],
                proyecto_id=proyecto["id"],
                estado=tarea_data["estado"],
                prioridad=tarea_data["prioridad"]
            )
            total_tareas += 1
            print(f"  ✓ {tarea['descripcion']} [{tarea['estado']}] ({tarea['prioridad']})")
    
    print(f"\n🎉 Base de datos poblada exitosamente!")
    print(f"   • {len(proyectos_creados)} proyectos creados")
    print(f"   • {total_tareas} tareas creadas")
    print(f"\n💡 Puedes ver los datos en: http://localhost:8000/docs")

if __name__ == "__main__":
    poblar_base_datos()