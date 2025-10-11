from fastapi import FastAPI, HTTPException
from typing import List, Dict, Any
import uvicorn

app = FastAPI()

contactos_db: List[Dict[str, Any]] = [
    {
        "nombre": "Facundo",
        "apellido": "Almonte",
        "edad": 21,
        "telefono": "3865505368",
        "email": "facundoalmonte15@gmail.com"
    },
    {
        "nombre": "José",
        "apellido": "Ruiz",
        "edad": 21,
        "telefono": "387534231",
        "email": "Jose2332@hotmail.com"
    },
    {
        "nombre": "Martin",
        "apellido": "Ontivero",
        "edad": 19,
        "telefono": "3887234786",
        "email": "Marto@outlook.com"
    },
    {
        "nombre": "Bruno",
        "apellido": "Nieto",
        "edad": 28,
        "telefono": "4367982456",
        "email": "brunie5@gmail.com"
    },
    {
        "nombre": "Sofia",
        "apellido": "Martinez",
        "edad": 46,
        "telefono": "38739324343",
        "email": "soso4545@hotmail.com"
    },
    {
        "nombre": "Julieta",
        "apellido": "Saracho",
        "edad": 26,
        "telefono": "3818231265",
        "email": "julilil@hotmail.com"
    },
    {
        "nombre": "Antonio",
        "apellido": "Roldan",
        "edad": 38,
        "telefono": "8349500707",
        "email": "Roldan3777@gmail.com"
    },
    {
        "nombre": "Ana",
        "apellido": "Gómez",
        "edad": 17,
        "telefono": "3467894567",
        "email": "Anitata@gmail.com"
    },
    {
        "nombre": "Mercedes",
        "apellido": "Sosa",
        "edad": 65,
        "telefono": "823842384",
        "email": "subetulvl@gmail.com"
    },
    {
        "nombre": "Diana",
        "apellido": "Soraire",
        "edad": 40,
        "telefono": "782372832",
        "email": "diana454@gmail.com"
    }
]

@app.get("/")
async def root():
    
    return {"Bienvenido a la Agenda de Contactos API"}

@app.get("/contactos")
async def obtener_contactos():
    
    return contactos_db


if __name__ == "__main__":
    print("=== AGENDA DE CONTACTOS API ===")
    print("Iniciando servidor...")
    print("Visita: http://127.0.0.1:8000/")
    print("Contactos: http://127.0.0.1:8000/contactos")

    uvicorn.run(
        "main:app",
        host="127.0.0.1",
        port=8000,
        reload=True
    )