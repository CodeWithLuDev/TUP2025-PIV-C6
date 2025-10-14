from fastapi import FastAPI

app = FastAPI()

contactos = [
    {"id": 1, "nombre": "Juan Pérez", "email": "juan@example.com"},
    {"id": 2, "nombre": "Ana López", "email": "ana@example.com"},
    {"id": 3, "nombre": "Carlos García", "email": "carlos@example.com"},
    {"id": 4, "nombre": "María Rodríguez", "email": "maria@example.com"},
    {"id": 5, "nombre": "Pedro Gómez", "email": "pedro@example.com"},
    {"id": 6, "nombre": "Lucía Fernández", "email": "lucia@example.com"},
    {"id": 7, "nombre": "Martín Herrera", "email": "martin@example.com"},
    {"id": 8, "nombre": "Sofía Díaz", "email": "sofia@example.com"},
    {"id": 9, "nombre": "Diego Romero", "email": "diego@example.com"},
    {"id": 10, "nombre": "Valentina Ruiz", "email": "valentina@example.com"},
]


@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a la API de Contactos"}


@app.get("/contactos")
def listar_contactos():
    return {"contactos": contactos}


@app.get("/contactos/{contacto_id}")
def obtener_contacto(contacto_id: int):
    for contacto in contactos:
        if contacto["id"] == contacto_id:
            return contacto
 