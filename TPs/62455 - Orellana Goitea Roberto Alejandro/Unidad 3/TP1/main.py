from fastapi import FastAPI

app = FastAPI()

contactos = [
    {"nombre": "Juan", "apellido": "Pérez", "edad": 30, "teléfono": "123456789", "email": "juan@example.com"},
    {"nombre": "María", "apellido": "García", "edad": 25, "teléfono": "987654321", "email": "maria@example.com"},
    {"nombre": "Carlos", "apellido": "López", "edad": 40, "teléfono": "111222333", "email": "carlos@example.com"},
    {"nombre": "Ana", "apellido": "Martínez", "edad": 28, "teléfono": "444555666", "email": "ana@example.com"},
    {"nombre": "Luis", "apellido": "Hernández", "edad": 35, "teléfono": "777888999", "email": "luis@example.com"},
    {"nombre": "Sofía", "apellido": "Rodríguez", "edad": 22, "teléfono": "000111222", "email": "sofia@example.com"},
    {"nombre": "Pedro", "apellido": "Sánchez", "edad": 45, "teléfono": "333444555", "email": "pedro@example.com"},
    {"nombre": "Laura", "apellido": "Ramírez", "edad": 31, "teléfono": "666777888", "email": "laura@example.com"},
    {"nombre": "Miguel", "apellido": "Torres", "edad": 27, "teléfono": "999000111", "email": "miguel@example.com"},
    {"nombre": "Elena", "apellido": "Vargas", "edad": 38, "teléfono": "222333444", "email": "elena@example.com"}
]

@app.get("/")
def root():
    return {"message": "Bienvenido a la Agenda de Contactos"}

@app.get("/contactos")
def get_contactos():
    return contactos