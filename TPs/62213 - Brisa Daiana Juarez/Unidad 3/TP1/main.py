from fastapi import FastAPI, HTTPException

app = FastAPI()

# Datos estáticos en memoria
agenda_contactos = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "teléfono": "3815551234", "email": "jperez@gmail.com"},
    {"nombre": "José", "apellido": "Gómez", "edad": 25, "teléfono": "3815551235", "email": "jgomez@gmail.com"},
    {"nombre": "Ana", "apellido": "Martínez", "edad": 28, "teléfono": "3815551236", "email": "amartinez@gmail.com"},
    {"nombre": "Luis", "apellido": "Rodríguez", "edad": 35, "teléfono": "3815551237", "email": "lrodriguez@gmail.com"},
    {"nombre": "María", "apellido": "López", "edad": 32, "teléfono": "3815551238", "email": "mlopez@gmail.com"},
    {"nombre": "Carlos", "apellido": "Sánchez", "edad": 40, "teléfono": "3815551239", "email": "csanchez@gmail.com"},
    {"nombre": "Lucía", "apellido": "Fernández", "edad": 27, "teléfono": "3815551240", "email": "lfernandez@gmail.com"},
    {"nombre": "Miguel", "apellido": "Torres", "edad": 29, "teléfono": "3815551241", "email": "mtorres@gmail.com"},
    {"nombre": "Sofía", "apellido": "Ramírez", "edad": 31, "teléfono": "3815551242", "email": "sramirez@gmail.com"},
    {"nombre": "Diego", "apellido": "Castro", "edad": 33, "teléfono": "3815551243", "email": "dcastro@gmail.com"}
]

# Endpoint raíz
@app.get("/")
def read_root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos API"}

# Endpoint para listar contactos
@app.get("/contactos")
def listar_contactos():
    return agenda_contactos

# Manejo básico de errores (ejemplo de contacto por índice)
@app.get("/contactos/{indice}")
def obtener_contacto(indice: int):
    if indice < 0 or indice >= len(agenda_contactos):
        raise HTTPException(status_code=404, detail="Contacto no encontrado")
    return agenda_contactos[indice]
