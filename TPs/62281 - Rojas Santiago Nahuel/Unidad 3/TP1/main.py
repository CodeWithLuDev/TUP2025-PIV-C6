from fastapi import FastAPI, HTTPException

app = FastAPI()

contactos = [
    {"nombre": "aylen", "apellido": "correa", "edad": 26, "telefono": "386534324", "email": "aylen@mail.com"},
    {"nombre": "tobias", "apellido": "nieto", "edad": 29, "telefono": "386589202", "email": "tobiasn@mail.com"},
    {"nombre": "daniela", "apellido": "montes", "edad": 31, "telefono": "386576443", "email": "dani@mail.com"},
    {"nombre": "leo", "apellido": "vargas", "edad": 28, "telefono": "386512984", "email": "leo.v@mail.com"},
    {"nombre": "camila", "apellido": "palacios", "edad": 24, "telefono": "386599011", "email": "cami@mail.com"},
    {"nombre": "franco", "apellido": "navarro", "edad": 32, "telefono": "386578329", "email": "franco@mail.com"},
    {"nombre": "micaela", "apellido": "aguirre", "edad": 27, "telefono": "386534120", "email": "mica@mail.com"},
    {"nombre": "nahuel", "apellido": "salas", "edad": 30, "telefono": "386512777", "email": "nahuel@mail.com"},
    {"nombre": "antonella", "apellido": "ibañez", "edad": 25, "telefono": "386535867", "email": "anto@mail.com"},
    {"nombre": "rodrigo", "apellido": "molina", "edad": 34, "telefono": "386598733", "email": "rodrigo@mail.com"},
    {"nombre": "julieta", "apellido": "peralta", "edad": 29, "telefono": "386543211", "email": "julieta@mail.com"},
    {"nombre": "bruno", "apellido": "castro", "edad": 33, "telefono": "386556789", "email": "bruno@mail.com"}
]

@app.get("/")
def inicio():
    return {"mensaje": "bienvenido a la agenda de contactos"}

@app.get("/contactos")
def ver_contactos():
    if not contactos:
        raise HTTPException(status_code=404, detail="no hay contactos para mostrar")
    return contactos