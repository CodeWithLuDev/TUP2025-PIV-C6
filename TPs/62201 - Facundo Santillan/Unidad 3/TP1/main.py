from fastapi import FastAPI, HTTPException

app = FastAPI(title="Agenda de Contactos API")

contactos = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "teléfono": "3815551234", "email": "juan@gmail.com"},
    {"nombre": "José", "apellido": "Gómez", "edad": 25, "teléfono": "3815551235", "email": "jose@gmail.com"},
    {"nombre": "María", "apellido": "López", "edad": 28, "teléfono": "3815551236", "email": "maria@gmail.com"},
    {"nombre": "Lucía", "apellido": "Martínez", "edad": 32, "teléfono": "3815551237", "email": "lucia@gmail.com"},
    {"nombre": "Carlos", "apellido": "Sosa", "edad": 29, "teléfono": "3815551238", "email": "carlos@gmail.com"},
    {"nombre": "Ana", "apellido": "Ramos", "edad": 27, "teléfono": "3815551239", "email": "ana@gmail.com"},
    {"nombre": "Santiago", "apellido": "Molina", "edad": 35, "teléfono": "3815551240", "email": "santiago@gmail.com"},
    {"nombre": "Laura", "apellido": "Fernández", "edad": 26, "teléfono": "3815551241", "email": "laura@gmail.com"},
    {"nombre": "Pedro", "apellido": "Ortiz", "edad": 31, "teléfono": "3815551242", "email": "pedro@gmail.com"},
    {"nombre": "Valentina", "apellido": "Suárez", "edad": 24, "teléfono": "3815551243", "email": "valentina@gmail.com"}
]

@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

@app.get("/contactos")
def listar_contactos():
    if not contactos:
        raise HTTPException(status_code=404, detail="No hay contactos disponibles.")
    return contactos

@app.get("/contactos/{nombre}")
def buscar_contacto(nombre: str):
    for c in contactos:
        if c["nombre"].lower() == nombre.lower():
            return c
    raise HTTPException(status_code=404, detail=f"No se encontró el contacto con nombre: {nombre}")
