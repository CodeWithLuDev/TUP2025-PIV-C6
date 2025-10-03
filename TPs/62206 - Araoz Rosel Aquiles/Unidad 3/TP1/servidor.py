from fastapi import FastAPI

app = FastAPI()

polenta = [{
    "nombre":"si se meten",
    "apellido": "con cristina",
    "edad": 30,
    "telefono":"3812933939",
    "email":"sisemetenconcristina@andaacomerpolenta.com"
},
            {
    "nombre":"si se meten",
    "apellido": "con cristina",
    "edad": 30,
    "telefono":"3812933939",
    "email":"sisemetenconcristina@andaacomerpolenta.com"
},
            {
    "nombre":"si se meten",
    "apellido": "con cristina",
    "edad": 30,
    "telefono":"3812933939",
    "email":"sisemetenconcristina@andaacomerpolenta.com"
}
]

@app.get("/")
def inicio():
    return {"polenta": polenta}
    

@app.get("/polenta")
def lista_polentera():
     return {"mensaje":"Bienvenido a la Api de polenta"}

