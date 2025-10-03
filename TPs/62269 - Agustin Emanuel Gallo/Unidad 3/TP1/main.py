from fastapi import FastAPI, HTTPException
from typing import List, Dict

app = FastAPI(title="Agenda de Contactos", description="Servidor básico para manejar contactos estáticos.")


contactos: List[Dict[str, str | int]] = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "telefono": "123456789", "email": "juan.perez@example.com"},
    {"nombre": "María", "apellido": "González", "edad": 25, "telefono": "987654321", "email": "maria.gonzalez@example.com"},
    {"nombre": "Carlos", "apellido": "López", "edad": 40, "telefono": "555555555", "email": "carlos.lopez@example.com"},
    {"nombre": "Ana", "apellido": "Martínez", "edad": 28, "telefono": "111222333", "email": "ana.martinez@example.com"},
    {"nombre": "Luis", "apellido": "Hernández", "edad": 35, "telefono": "444555666", "email": "luis.hernandez@example.com"},
    {"nombre": "Sofía", "apellido": "Díaz", "edad": 22, "telefono": "777888999", "email": "sofia.diaz@example.com"},
    {"nombre": "Pedro", "apellido": "García", "edad": 45, "telefono": "000111222", "email": "pedro.garcia@example.com"},
    {"nombre": "Laura", "apellido": "Rodríguez", "edad": 31, "telefono": "333444555", "email": "laura.rodriguez@example.com"},
    {"nombre": "Miguel", "apellido": "Sánchez", "edad": 27, "telefono": "666777888", "email": "miguel.sanchez@example.com"},
    {"nombre": "Elena", "apellido": "Ramírez", "edad": 38, "telefono": "999000111", "email": "elena.ramirez@example.com"},
]


@app.get("/")
async def raiz():
    return {"mensaje": "Bienvenido a la Agenda de Contactos"}


@app.get("/contactos", response_model=List[Dict[str, str | int]])
async def listar_contactos():
    if not contactos:
        raise HTTPException(status_code=404, detail="No se encontraron contactos")
    return contactos


@app.exception_handler(HTTPException)
async def http_exception_handler(request, exc):
    return {"error": str(exc.detail), "status_code": exc.status_code}

