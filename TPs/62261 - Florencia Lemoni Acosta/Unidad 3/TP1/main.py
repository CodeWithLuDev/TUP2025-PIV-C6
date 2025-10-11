from fastapi import FastAPI
from fastapi import HTTPException
app = FastAPI() 

contactos =[
   {
        "nombre": "Juan",
        "apellido": "Pérez",
        "edad": 30,
        "telefono": "3815551234",
        "email": "jperez@gmail.com"
    },
    {
        "nombre": "María",
        "apellido": "García",
        "edad": 28,
        "telefono": "3815555678",
        "email": "maria.garcia@gmail.com"
    },
    {
        "nombre": "Lucas",
        "apellido": "López",
        "edad": 22,
        "telefono": "3815559876",
        "email": "lucas.lopez@gmail.com"
    },
    {
        "nombre": "Ana",
        "apellido": "Martínez",
        "edad": 35,
        "telefono": "3815552468",
        "email": "ana.martinez@gmail.com"
    },
    {
        "nombre": "Sofía",
        "apellido": "Fernández",
        "edad": 27,
        "telefono": "3815551357",
        "email": "sofia.fernandez@gmail.com"
    },
    {
        "nombre": "Diego",
        "apellido": "Ruiz",
        "edad": 40,
        "telefono": "3815551111",
        "email": "diego.ruiz@gmail.com"
    },
    {
        "nombre": "Valentina",
        "apellido": "Sosa",
        "edad": 31,
        "telefono": "3815552222",
        "email": "valentina.sosa@gmail.com"
    },
    {
        "nombre": "Mateo",
        "apellido": "Mendoza",
        "edad": 29,
        "telefono": "3815553333",
        "email": "mateo.mendoza@gmail.com"
    },
    {
        "nombre": "Lucía",
        "apellido": "Ortiz",
        "edad": 26,
        "telefono": "3815554444",
        "email": "lucia.ortiz@gmail.com"
    },
    {
        "nombre": "José",
        "apellido": "Gómez",
        "edad": 25,
        "telefono": "3815555555",
        "email": "jose.gomez@gmail.com"
    }
]

@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

@app.get("/contactos")
def obtener_contactos():
    return contactos

@app.get("/contactos/{id}")
def obtener_contacto(id: int):
    if id < 0 or id >= len(contactos):
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return contactos[id]


