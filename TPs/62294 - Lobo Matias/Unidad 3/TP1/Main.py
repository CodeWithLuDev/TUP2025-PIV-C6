from fastapi import FastAPI

app = FastAPI(
    title="Agenda de Contactos"
)

contactos = [
    {"nombre": "Martin", "apellido": "Gonzalez", "edad": 30, "telefono": "111111111", "email": "martin@example.com"},
    {"nombre": "Sofia", "apellido": "Ramirez", "edad": 28, "telefono": "222222222", "email": "sofia@example.com"},
    {"nombre": "Lucia", "apellido": "Hernandez", "edad": 35, "telefono": "333333333", "email": "lucia@example.com"},
    {"nombre": "Diego", "apellido": "Herrera", "edad": 25, "telefono": "444444444", "email": "diego@example.com"},
    {"nombre": "Valentina", "apellido": "Torres", "edad": 40, "telefono": "555555555", "email": "valentina@example.com"},
    {"nombre": "Tomas", "apellido": "Morales", "edad": 22, "telefono": "666666666", "email": "tomas@example.com"},
    {"nombre": "Camila", "apellido": "Rojas", "edad": 45, "telefono": "777777777", "email": "camila@example.com"},
    {"nombre": "Mateo", "apellido": "Carrizo", "edad": 29, "telefono": "8888888888", "email": "mateo@example.com"},
    {"nombre": "Isabella", "apellido": "Cruz", "edad": 33, "telefono": "999999999", "email": "isabella@example.com"},
    {"nombre": "Julian", "apellido": "Ortega", "edad": 27, "telefono": "222333444", "email": "julian@example.com"},
]

@app.get("/")
def root():
    return {"mensaje": "Bienvenido a la Agenda de Contactos"}   


@app.get("/contactos")
def get_contactos():
    return contactos