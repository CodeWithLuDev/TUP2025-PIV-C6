from fastapi import FastAPI, HTTPException

app = FastAPI()

contactos = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "teléfono": "3815551234", "email": "jperez@gmail.com"},
    {"nombre": "José", "apellido": "Gómez", "edad": 25, "teléfono": "3815551235", "email": "jgomez@gmail.com"},
    {"nombre": "Ana", "apellido": "López", "edad": 28, "teléfono": "3815551236", "email": "alopez@gmail.com"},
    {"nombre": "María", "apellido": "Rodríguez", "edad": 35, "teléfono": "3815551237", "email": "mrodriguez@gmail.com"},
    {"nombre": "Carlos", "apellido": "Martínez", "edad": 40, "teléfono": "3815551238", "email": "cmartinez@gmail.com"},
    {"nombre": "Lucía", "apellido": "Fernández", "edad": 22, "teléfono": "3815551239", "email": "lfernandez@gmail.com"},
    {"nombre": "Pedro", "apellido": "García", "edad": 31, "teléfono": "3815551240", "email": "pgarcia@gmail.com"},
    {"nombre": "Sofía", "apellido": "Díaz", "edad": 27, "teléfono": "3815551241", "email": "sdiaz@gmail.com"},
    {"nombre": "Martín", "apellido": "Ruiz", "edad": 29, "teléfono": "3815551242", "email": "mruiz@gmail.com"},
    {"nombre": "Valentina", "apellido": "Torres", "edad": 26, "teléfono": "3815551243", "email": "vtorres@gmail.com"}
]

@app.get("/")
def inicio():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

@app.get("/contactos")
def listar_contactos():
    if not contactos:
        raise HTTPException(status_code=404, detail="No hay contactos disponibles")
    return contactos

# Buscar contacto por ID (posición en la lista)
@app.get("/contactos/{id}")
def buscar_contacto(id: int):
    if id < 0 or id >= len(contactos):
        raise HTTPException(status_code=404, detail=f"No existe un contacto con id {id}")
    return contactos[id]



