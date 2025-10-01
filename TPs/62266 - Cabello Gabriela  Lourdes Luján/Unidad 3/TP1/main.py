from fastapi import FastAPI, HTTPException

# Crear la aplicación FastAPI
app = FastAPI(title="Agenda de Contactos API", version="1.0")

# Base de datos en memoria (hardcoded)
contactos = [
    {"nombre": "Aldair", "apellido": "Vanegas", "edad": 34, "teléfono": "3815552001", "email": "aldair.vanegas@mail.com"},
    {"nombre": "Yamila", "apellido": "Frossard", "edad": 26, "teléfono": "3815552002", "email": "yamila.frossard@mail.com"},
    {"nombre": "Ezio", "apellido": "Caravaggio", "edad": 29, "teléfono": "3815552003", "email": "ezio.caravaggio@mail.com"},
    {"nombre": "Nayara", "apellido": "Dumont", "edad": 31, "teléfono": "3815552004", "email": "nayara.dumont@mail.com"},
    {"nombre": "Thiago", "apellido": "Mandelbrot", "edad": 27, "teléfono": "3815552005", "email": "thiago.mandelbrot@mail.com"},
    {"nombre": "Ítalo", "apellido": "Koenig", "edad": 38, "teléfono": "3815552006", "email": "italo.koenig@mail.com"},
    {"nombre": "Samira", "apellido": "Beltramini", "edad": 24, "teléfono": "3815552007", "email": "samira.beltramini@mail.com"},
    {"nombre": "Gael", "apellido": "Quinteros", "edad": 33, "teléfono": "3815552008", "email": "gael.quinteros@mail.com"},
    {"nombre": "Leire", "apellido": "Hadjari", "edad": 28, "teléfono": "3815552009", "email": "leire.hadjari@mail.com"},
    {"nombre": "Ulises", "apellido": "Montenegro", "edad": 36, "teléfono": "3815552010", "email": "ulises.montenegro@mail.com"}
]


# Endpoint raíz
@app.get("/")
def root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# Endpoint para listar todos los contactos
@app.get("/contactos")
def listar_contactos():
    return contactos

# Endpoint para buscar contacto por índice
@app.get("/contactos/{contacto_id}")
def obtener_contacto(contacto_id: int):
    if 0 <= contacto_id < len(contactos):
        return contactos[contacto_id]
    raise HTTPException(status_code=404, detail="Contacto no encontrado")
