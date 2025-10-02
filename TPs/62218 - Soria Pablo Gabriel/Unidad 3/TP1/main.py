from fastapi import FastAPI, HTTPException
from pydantic import BaseModel

class Contacto(BaseModel):
    nombre: str
    apellido: str
    edad: int
    teléfono: str
    email: str

app = FastAPI()

# Lista de contactos (simulando una base de datos)
contactos = []

# Endpoint raíz
@app.get("/")
def bienvenida():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# Endpoint para listar contactos
@app.get("/contactos")
def listar_contactos(buscar: str = None):
    if buscar:
        buscar = buscar.lower()
        return [
            contacto for contacto in contactos
            if buscar in contacto["nombre"].lower() or
               buscar in contacto["apellido"].lower() or
               buscar in contacto["email"].lower()
        ]
    return contactos

# Manejo básico de error 404 (ejemplo para contacto por índice)
@app.get("/contactos/{indice}")
def obtener_contacto(indice: int):
    if 0 <= indice < len(contactos):
        return contactos[indice]
    raise HTTPException(status_code=404, detail="Contacto no encontrado")

# Endpoint para crear un nuevo contacto
@app.post("/contactos")
def crear_contactos(contacto: Contacto):
    nuevo_contacto = contacto.dict()
    contactos.append(nuevo_contacto)
    return nuevo_contacto

# Endpoint para actualizar un contacto existente
@app.put("/contactos/{indice}")
def actualizar_contactos(indice: int, contacto: Contacto):
    if 0 <= indice < len(contactos):
        contactos[indice] = contacto.dict()
        return contactos[indice]
    raise HTTPException(status_code=404, detail="Contacto no encontrado")

# Endpoint para eliminar un contacto
@app.delete("/contactos/{indice}")
def eliminar_contacto(indice: int):
    if 0 <= indice < len(contactos):
        contacto_eliminado = contactos.pop(indice)
        return {"mensaje": f"Contacto {contacto_eliminado['nombre']} {contacto_eliminado['apellido']} eliminado"}
    raise HTTPException(status_code=404, detail="Contacto no encontrado")
