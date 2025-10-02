from fastapi import FastAPI, HTTPException

# Crear una instancia de FastAPI
app = FastAPI()

# Lista estática de contactos (hardcoded)
contacts = [
    {"nombre":"Juan", "apellido":"Pérez", "edad":30, "telefono":"3815551234", "email":"jperez@gmail.com"},
    {"nombre":"José", "apellido":"Gómez", "edad":25, "telefono":"3815551235", "email":"jgomez@gmail.com"},
    {"nombre":"María", "apellido":"López", "edad":28, "telefono":"3815551236", "email":"mlopez@gmail.com"},
    {"nombre":"Ana", "apellido":"Martínez", "edad":22, "telefono":"3815551237", "email":"amartinez@gmail.com"},
    {"nombre":"Carlos", "apellido":"Rodríguez", "edad":35, "telefono":"3815551238", "email":"crodriguez@gmail.com"},
    {"nombre":"Laura", "apellido":"Fernández", "edad":27, "telefono":"3815551239", "email":"lfernandez@gmail.com"},
    {"nombre":"Pedro", "apellido":"García", "edad":40, "telefono":"3815551240", "email":"pgarcia@gmail.com"},
    {"nombre":"Sofía", "apellido":"Sánchez", "edad":19, "telefono":"3815551241", "email":"ssanchez@gmail.com"},
    {"nombre":"Diego", "apellido":"Torres", "edad":32, "telefono":"3815551242", "email":"dtorres@gmail.com"},
    {"nombre":"Lucía", "apellido":"Ramírez", "edad":29, "telefono":"3815551243", "email":"lramirez@gmail.com"}
]

# Endpoint raíz
@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# Endpoint para listar contactos
@app.get("/contactos")
def traerContactos():
    return contacts
    