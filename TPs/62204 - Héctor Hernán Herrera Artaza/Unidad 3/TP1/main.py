from fastapi import FastAPI, HTTPException

app = FastAPI()
@app.get("/")
def mensaje_de_bienvenida():
    return {"mensaje": "¡Bienvenido al servidor de la agenda de contactos!"}

contactos = [

    {"nombre": "Ana", "apellido": "García", "edad": 25, "telefono": "123456789", "email": "ana.garcia@example.com"},
    {"nombre": "Luis", "apellido": "Martínez", "edad": 30, "telefono": "987654321", "email": "luis.martinez@example.com"},
    {"nombre": "María", "apellido": "López", "edad": 28, "telefono": "555123456", "email": "maria.lopez@example.com"},
    {"nombre": "Carlos", "apellido": "Fernández", "edad": 35, "telefono": "444789123", "email": "carlos.fernandez@example.com"},
    {"nombre": "Sofía", "apellido": "Pérez", "edad": 22, "telefono": "321654987", "email": "sofia.perez@example.com"},
    {"nombre": "Diego", "apellido": "Torres", "edad": 27, "telefono": "654987321", "email": "diego.torres@example.com"},
    {"nombre": "Laura", "apellido": "Ramírez", "edad": 33, "telefono": "789123456", "email": "laura.ramirez@example.com"},
    {"nombre": "Javier", "apellido": "Gómez", "edad": 29, "telefono": "963852741", "email": "javier.gomez@example.com"},
    {"nombre": "Camila", "apellido": "Morales", "edad": 26, "telefono": "147258369", "email": "camila.morales@example.com"},
    {"nombre": "Andrés", "apellido": "Silva", "edad": 31, "telefono": "852369741", "email": "andres.silva@example.com"}
]
@app.get("/contactos")
def obtener_contactos():
    if len(contactos) == 0:
        raise HTTPException(status_code=404, detail={"mensaje": "No hay contactos disponibles."})
    return {"contactos": contactos}
