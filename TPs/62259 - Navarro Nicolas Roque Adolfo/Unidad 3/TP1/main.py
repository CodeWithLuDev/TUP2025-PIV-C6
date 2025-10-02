from fastapi import FastAPI, HTTPException

app = FastAPI()

contactos = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "teléfono": "3815551234", "email": "jperez@gmail.com"},
    {"nombre": "José", "apellido": "Gómez", "edad": 25, "teléfono": "3815551235", "email": "jgomez@gmail.com"},
    {"nombre": "María", "apellido": "López", "edad": 28, "teléfono": "3815551236", "email": "mlopez@gmail.com"},
    {"nombre": "Ana", "apellido": "Martínez", "edad": 32, "teléfono": "3815551237", "email": "amartinez@gmail.com"},
    {"nombre": "Luis", "apellido": "Rodríguez", "edad": 40, "teléfono": "3815551238", "email": "lrodriguez@gmail.com"},
    {"nombre": "Laura", "apellido": "Fernández", "edad": 22, "teléfono": "3815551239", "email": "lfernandez@gmail.com"},
    {"nombre": "Pedro", "apellido": "Sánchez", "edad": 35, "teléfono": "3815551240", "email": "psanchez@gmail.com"},
    {"nombre": "Carla", "apellido": "Ramírez", "edad": 29, "teléfono": "3815551241", "email": "cramirez@gmail.com"},
    {"nombre": "Diego", "apellido": "Silva", "edad": 27, "teléfono": "3815551242", "email": "dsilva@gmail.com"},
    {"nombre": "Valeria", "apellido": "Méndez", "edad": 31, "teléfono": "3815551243", "email": "vmendez@gmail.com"},
]

@app.get("/")
def root():
    return {"mensaje": "Bienvenido a la agenda de contacto API"}

@app.get("/contactos")
def listar_contactos():
    return contactos

@app.get("/contactos/{contacto_id}")
def obtener_contacto(contacto_id: int):
    if 0 <= contacto_id < len(contactos):
        return contactos[contacto_id]
    else:
        raise HTTPException(status_code=404, detail="No se encontró el contacto")