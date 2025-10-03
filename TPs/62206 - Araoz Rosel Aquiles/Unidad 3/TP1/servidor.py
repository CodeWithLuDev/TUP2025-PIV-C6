from fastapi import FastAPI

app = FastAPI()

polenta = [{
    "nombre":"alex",
    "apellido": "werner",
    "edad": 18,
    "telefono":"3812233939",
    "email":"sisemetenconcristina@andaacomerpolenta.com"
},
            {
    "nombre":"alberto",
    "apellido": "fernandez",
    "edad": 29,
    "telefono":"3811133939",
    "email":"sisemetenconcristina2@andaacomerpolenta.com"
},
            {
    "nombre":"sneijder",
    "apellido": "mendoza",
    "edad": 30,
    "telefono":"38129333439",
    "email":"sisemetenconcristina912@andaacomerpolenta.com"
}
]

@app.get("/")
def inicio():
    return {"polenta": polenta}
    

@app.get("/polenta")
def lista_polentera():
     return {"mensaje":"Bienvenido a la Api de polenta"}

