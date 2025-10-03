from fastapi import FastAPI, HTTPException

app = FastAPI()

# Datos estáticos en memoria
contactos = [
    {"nombre": "Lázaro", "apellido": "Montenegro", "edad": 34, "teléfono": "3815551001", "email": "lmontenegro@gmail.com"},
    {"nombre": "Amira", "apellido": "Santillán", "edad": 28, "teléfono": "3815551002", "email": "asantillan@gmail.com"},
    {"nombre": "Ezequiel", "apellido": "Vera", "edad": 40, "teléfono": "3815551003", "email": "evera@hotmail.com"},
    {"nombre": "Brígida", "apellido": "Corbalán", "edad": 52, "teléfono": "3815551004", "email": "bcorbalan@yahoo.com"},
    {"nombre": "Isandro", "apellido": "Ocampo", "edad": 22, "teléfono": "3815551005", "email": "iocampo@gmail.com"},
    {"nombre": "Tadea", "apellido": "Bazán", "edad": 19, "teléfono": "3815551006", "email": "tbazan@gmail.com"},
    {"nombre": "Aníbal", "apellido": "Quiroga", "edad": 47, "teléfono": "3815551007", "email": "aquiroga@gmail.com"},
    {"nombre": "Samira", "apellido": "Ahumada", "edad": 33, "teléfono": "3815551008", "email": "sahumada@gmail.com"},
    {"nombre": "Faustino", "apellido": "Leiva", "edad": 29, "teléfono": "3815551009", "email": "fleiva@gmail.com"},
    {"nombre": "Candela", "apellido": "Mansilla", "edad": 61, "teléfono": "3815551010", "email": "cmansilla@hotmail.com"}
]

# Endpoint raíz
@app.get("/")
def root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# Endpoint para listar todos los contactos
@app.get("/contactos")
def listar_contactos():
    return contactos

# Endpoint para obtener un contacto por índice
@app.get("/contactos/{contacto_id}")
def obtener_contacto(contacto_id: int):
    if 0 <= contacto_id < len(contactos):
        return contactos[contacto_id]
    raise HTTPException(status_code=404, detail="Contacto no encontrado")
