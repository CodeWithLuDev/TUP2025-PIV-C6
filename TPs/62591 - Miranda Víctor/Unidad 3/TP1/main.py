from fastapi import FastAPI
from typing import List
from pydantic import BaseModel

# Crear una instancia de FastAPI
app = FastAPI()

# Definir el modelo para los contactos usando Pydantic
class Contacto(BaseModel):
    nombre: str
    apellido: str
    edad: int
    telefono: str
    email: str

# Lista estática de contactos (hardcoded)
contactos: List[Contacto] = [
    Contacto(nombre="Juan", apellido="Pérez", edad=30, telefono="3815551234", email="jperez@gmail.com"),
    Contacto(nombre="José", apellido="Gómez", edad=25, telefono="3815551235", email="jgomez@gmail.com"),
    Contacto(nombre="María", apellido="López", edad=28, telefono="3815551236", email="mlopez@gmail.com"),
    Contacto(nombre="Ana", apellido="Martínez", edad=22, telefono="3815551237", email="amartinez@gmail.com"),
    Contacto(nombre="Carlos", apellido="Rodríguez", edad=35, telefono="3815551238", email="crodriguez@gmail.com"),
    Contacto(nombre="Lucía", apellido="Fernández", edad=27, telefono="3815551239", email="lfernandez@gmail.com"),
    Contacto(nombre="Diego", apellido="Sánchez", edad=40, telefono="3815551240", email="dsanchez@gmail.com"),
    Contacto(nombre="Sofía", apellido="García", edad=19, telefono="3815551241", email="sgarcia@gmail.com"),
    Contacto(nombre="Pablo", apellido="Ramírez", edad=33, telefono="3815551242", email="pramirez@gmail.com"),
    Contacto(nombre="Laura", apellido="Torres", edad=26, telefono="3815551243", email="ltorres@gmail.com")
]

# Endpoint raíz
@app.get("/")
def raiz():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# Endpoint para listar todos los contactos
@app.get("/contactos", response_model=List[Contacto])
def listar_contactos():
    return contactos