from fastapi import FastAPI, HTTPException

app = FastAPI()

contactos = [
    {"nombre": "Martina Paula", "apellido": "Villagra", "edad": 21, "telefono": "3814135116", "email": "bartivillagra@gmail.com"},
    {"nombre": "Yuliana Cecilia", "apellido": "Brito Grande", "edad": 24, "telefono": "3813018935", "email": "yulibritogrande@gmail.com"},
    {"nombre": "Delfina Abril", "apellido": "Lucena", "edad": 15, "telefono": "3813033000", "email": "delfilucena@gmail.com"},
    {"nombre": "Josefina Maité", "apellido": "Rivadeneira", "edad": 10, "telefono": "3814166039", "email": "jocherivadeneira@gmail.com"},
    {"nombre": "Tomas Augusto", "apellido": "Brito Grande", "edad": 26, "telefono": "3815892129", "email": "tomasbrito@gmail.com"},
]

@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

@app.get("/contactos")
def listar_contactos():
    return contactos

@app.get("/contactos/{contacto_id}")
def obtener_contacto(contacto_id: int):
    if contacto_id < 0 or contacto_id >= len(contactos):
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return contactos[contacto_id]