from fastapi import FastAPI, HTTPException
from typing import List, Dict
import uvicorn

# Crear instancia de FastAPI
app = FastAPI(
    title="Agenda de Contactos API",
    description="API para gestionar una agenda de contactos",
    version="1.0.0"
)

# Estructura de datos en memoria - Lista de contactos
contactos: List[Dict[str, any]] = [
    {
        "nombre": "Juan",
        "apellido": "Pérez",
        "edad": 30,
        "teléfono": "3815551234",
        "email": "jperez@gmail.com"
    },
    {
        "nombre": "José",
        "apellido": "Gómez",
        "edad": 25,
        "teléfono": "3815551235",
        "email": "jgomez@gmail.com"
    },
    {
        "nombre": "María",
        "apellido": "López",
        "edad": 28,
        "teléfono": "3815551236",
        "email": "mlopez@gmail.com"
    },
    {
        "nombre": "Ana",
        "apellido": "Martínez",
        "edad": 35,
        "teléfono": "3815551237",
        "email": "amartinez@gmail.com"
    },
    {
        "nombre": "Carlos",
        "apellido": "Rodríguez",
        "edad": 42,
        "teléfono": "3815551238",
        "email": "crodriguez@gmail.com"
    },
    {
        "nombre": "Laura",
        "apellido": "Fernández",
        "edad": 31,
        "teléfono": "3815551239",
        "email": "lfernandez@gmail.com"
    },
    {
        "nombre": "Pedro",
        "apellido": "Sánchez",
        "edad": 27,
        "teléfono": "3815551240",
        "email": "psanchez@gmail.com"
    },
    {
        "nombre": "Sofía",
        "apellido": "García",
        "edad": 29,
        "teléfono": "3815551241",
        "email": "sgarcia@gmail.com"
    },
    {
        "nombre": "Diego",
        "apellido": "Ramírez",
        "edad": 38,
        "teléfono": "3815551242",
        "email": "dramirez@gmail.com"
    },
    {
        "nombre": "Valentina",
        "apellido": "Torres",
        "edad": 26,
        "teléfono": "3815551243",
        "email": "vtorres@gmail.com"
    }
]


# Endpoint raíz - Mensaje de bienvenida
@app.get("/")
async def root():
    """
    Endpoint raíz que devuelve un mensaje de bienvenida
    """
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}


# Endpoint para listar todos los contactos
@app.get("/contactos")
async def obtener_contactos():
    """
    Devuelve la lista completa de contactos
    """
    if not contactos:
        raise HTTPException(
            status_code=404,
            detail="No hay contactos disponibles en la agenda"
        )
    return contactos


# Endpoint para obtener un contacto específico por índice (opcional)
@app.get("/contactos/{contacto_id}")
async def obtener_contacto(contacto_id: int):
    """
    Devuelve un contacto específico por su índice
    """
    if contacto_id < 0 or contacto_id >= len(contactos):
        raise HTTPException(
            status_code=404,
            detail=f"Contacto con ID {contacto_id} no encontrado"
        )
    return contactos[contacto_id]


# Endpoint catch-all para capturar rutas no definidas (debe ir al final)
@app.api_route("/{path_name:path}", methods=["GET", "POST", "PUT", "DELETE", "PATCH"])
async def catch_all(path_name: str):
    """
    Captura todas las rutas no definidas y devuelve 404
    """
    raise HTTPException(status_code=404, detail="Ruta no encontrada")


# Punto de entrada principal
if __name__ == "__main__":
    print("=== AGENDA DE CONTACTOS API ===")
    print("Ejecutando servidor en http://127.0.0.1:8000")
    print("Documentación disponible en http://127.0.0.1:8000/docs")
    uvicorn.run(app, host="127.0.0.1", port=8000, reload=True)