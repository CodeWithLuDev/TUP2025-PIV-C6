from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List

# Crear una instancia de FastAPI
app = FastAPI()

# Definir el modelo de Contacto
class Contact(BaseModel):
    nombre: str
    apellido: str
    edad: int
    telefono: str
    email: str

# Lista estática de contactos (hardcoded)
contacts = [
    Contact(nombre="Juan", apellido="Pérez", edad=30, telefono="3815551234", email="jperez@gmail.com"),
    Contact(nombre="José", apellido="Gómez", edad=25, telefono="3815551235", email="jgomez@gmail.com"),
    Contact(nombre="María", apellido="López", edad=28, telefono="3815551236", email="mlopez@gmail.com"),
    Contact(nombre="Ana", apellido="Martínez", edad=22, telefono="3815551237", email="amartinez@gmail.com"),
    Contact(nombre="Carlos", apellido="Rodríguez", edad=35, telefono="3815551238", email="crodriguez@gmail.com"),
    Contact(nombre="Laura", apellido="Fernández", edad=27, telefono="3815551239", email="lfernandez@gmail.com"),
    Contact(nombre="Pedro", apellido="García", edad=40, telefono="3815551240", email="pgarcia@gmail.com"),
    Contact(nombre="Sofía", apellido="Sánchez", edad=19, telefono="3815551241", email="ssanchez@gmail.com"),
    Contact(nombre="Diego", apellido="Torres", edad=32, telefono="3815551242", email="dtorres@gmail.com"),
    Contact(nombre="Lucía", apellido="Ramírez", edad=29, telefono="3815551243", email="lramirez@gmail.com")
]

# Endpoint raíz
@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# Endpoint para listar contactos
@app.get("/contactos", response_model=List[Contact])
def get_contacts():
    if not contacts:
        raise HTTPException(status_code=404, detail="No se encontraron contactos")
    return contacts