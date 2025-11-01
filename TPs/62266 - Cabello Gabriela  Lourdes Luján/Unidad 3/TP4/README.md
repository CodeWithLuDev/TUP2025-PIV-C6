Trabajo Práctico N°4: Implementación de API Relacional

Asignatura: Programación IV
Estudiante: Gabriela Luján
Fecha de Entrega: 24 de Octubre de 2025

I. Objetivos del Trabajo Práctico

Este trabajo extiende la API de gestión de tareas implementada en el TP3 para incorporar la gestión de Proyectos y establecer una relación uno a muchos (1:N) entre proyectos y tareas. Se implementa la integridad referencial, filtros avanzados y endpoints de resumen estadístico.

II. Configuración y Puesta en Marcha

Requisitos: Python 3.x, pip.

Instalación de Dependencias:

pip install fastapi uvicorn pydantic



Ejecución del Servidor:
El servidor se inicia desde la carpeta raíz del proyecto. El script main.py contiene la llamada a init_db(), que crea el archivo tareas.db y las tablas al iniciarse si no existen.

uvicorn main:app --reload



La documentación interactiva (Swagger UI) estará disponible en http://127.0.0.1:8000/docs.



III. Diseño de Base de Datos (SQLite)

La persistencia se maneja mediante SQLite con dos tablas principales.
Estructura de Tablas

Tabla proyectos

Clave Primaria: id

Restricciones: El campo nombre es NOT NULL y UNIQUE. Almacena la fecha de creación.

Tabla tareas

Clave Primaria: id

Clave Foránea: proyecto_id

Restricciones: Los campos descripcion, estado, prioridad son NOT NULL.

Relación y Consecuencias

Relación: Uno a Muchos (1:N), definida por la clave foránea tareas.proyecto_id que referencia a proyectos.id.

Integridad Referencial: Se utiliza la cláusula ON DELETE CASCADE. Esto asegura que al eliminar un registro de la tabla proyectos, todas las tareas asociadas en la tabla tareas se eliminan automáticamente, garantizando la consistencia de los datos.


IV. Funcionalidad de Endpoints y Ejemplos (CURL)

Se presenta un resumen de los endpoints implementados:

A. Gestión de Proyectos (CRUD)

Método: POST

Ruta: /proyectos

Uso Principal: Creación. Valida unicidad del nombre (409 Conflict).

Método: GET

Ruta: /proyectos/{id}

Uso Principal: Recupera el proyecto e incluye el campo total_tareas.

Método: GET

Ruta: /proyectos?nombre={filtro}

Uso Principal: Filtro Avanzado: Busca proyectos cuyo nombre contenga la cadena {filtro} (ej: .../proyectos?nombre=Final).

Método: DELETE

Ruta: /proyectos/{id}

Uso Principal: Eliminación. Activa ON DELETE CASCADE en la tabla tareas.

B. Gestión de Tareas

Método: POST

Ruta: /proyectos/{id}/tareas

Uso Principal: Creación de una tarea asociada a un proyecto. Valida que el proyecto_id exista (400 Bad Request).

Método: GET

Ruta: /proyectos/{id}/tareas

Uso Principal: Lista todas las tareas de un proyecto específico.

Método: PUT

Ruta: /tareas/{id}

Uso Principal: Actualización de la tarea. La lógica soporta actualizaciones parciales, permitiendo cambiar el proyecto_id para mover la tarea de proyecto.

Método: GET

Ruta: /tareas

Uso Principal: Lista todas las tareas de todos los proyectos.

C. Filtros y Búsquedas Combinadas (GET /tareas)

El endpoint /tareas admite múltiples parámetros de consulta combinables:

Ejemplo: GET /tareas?estado=pendiente&prioridad=alta&proyecto_id=1&orden=desc

Filtra: Tareas pendiente Y alta Y que pertenecen al proyecto_id=1.

Ordena: por fecha_creacion en modo descendente.

D. Resúmenes y Estadísticas

Método: GET

Ruta: /proyectos/{id}/resumen

Uso Principal: Estadísticas del proyecto: total de tareas, conteo por estado y conteo por prioridad.

Método: GET

Ruta: /resumen

Uso Principal: Resumen general de la aplicación: totales de proyectos y tareas, distribución de tareas por estado, e identificación del proyecto con más tareas.