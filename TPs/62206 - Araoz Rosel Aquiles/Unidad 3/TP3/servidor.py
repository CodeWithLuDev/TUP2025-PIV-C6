from fastapi import FastAPI, HTTPException
from pydantic import BaseModel, EmailStr
from typing import Optional, List
from database import init_db, get_db, dict_from_row
import sqlite3

app = FastAPI(title="API con SQLite", version="1.0")

@app.on_event("startup")
def startup():
    init_db()

class UsuarioCreate(BaseModel):
    nombre: str
    email: EmailStr
    edad: Optional[int] = None

class UsuarioUpdate(BaseModel):
    nombre: Optional[str] = None
    email: Optional[EmailStr] = None
    edad: Optional[int] = None

class Usuario(BaseModel):
    id: int
    nombre: str
    email: str
    edad: Optional[int]
    fecha_creacion: str

@app.get("/")
def root():
    return {"mensaje": "API FastAPI + SQLite funcionando"}

@app.post("/usuarios", response_model=Usuario, status_code=201)
def crear_usuario(usuario: UsuarioCreate):
    with get_db() as conn:
        cursor = conn.cursor()
        try:
            cursor.execute(
                "INSERT INTO usuarios (nombre, email, edad) VALUES (?, ?, ?)",
                (usuario.nombre, usuario.email, usuario.edad)
            )
            conn.commit()
            usuario_id = cursor.lastrowid
            cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
            row = cursor.fetchone()
            return dict_from_row(row)
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="El email ya está registrado")

@app.get("/usuarios", response_model=List[Usuario])
def listar_usuarios():
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios ORDER BY id DESC")
        rows = cursor.fetchall()
        return [dict_from_row(row) for row in rows]

@app.get("/usuarios/{usuario_id}", response_model=Usuario)
def obtener_usuario(usuario_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
        row = cursor.fetchone()
        if not row:
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        return dict_from_row(row)

@app.put("/usuarios/{usuario_id}", response_model=Usuario)
def actualizar_usuario(usuario_id: int, usuario: UsuarioUpdate):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        campos = []
        valores = []
        if usuario.nombre is not None:
            campos.append("nombre = ?")
            valores.append(usuario.nombre)
        if usuario.email is not None:
            campos.append("email = ?")
            valores.append(usuario.email)
        if usuario.edad is not None:
            campos.append("edad = ?")
            valores.append(usuario.edad)
        if not campos:
            raise HTTPException(status_code=400, detail="No hay campos para actualizar")
        valores.append(usuario_id)
        query = f"UPDATE usuarios SET {', '.join(campos)} WHERE id = ?"
        try:
            cursor.execute(query, valores)
            conn.commit()
            cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
            row = cursor.fetchone()
            return dict_from_row(row)
        except sqlite3.IntegrityError:
            raise HTTPException(status_code=400, detail="El email ya está registrado")

@app.delete("/usuarios/{usuario_id}")
def eliminar_usuario(usuario_id: int):
    with get_db() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM usuarios WHERE id = ?", (usuario_id,))
        if not cursor.fetchone():
            raise HTTPException(status_code=404, detail="Usuario no encontrado")
        cursor.execute("DELETE FROM usuarios WHERE id = ?", (usuario_id,))
        conn.commit()
        return {"mensaje": "Usuario eliminado correctamente"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)

