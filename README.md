# 📚 TUP2025 - Programación IV (Trabajos Prácticos)

Bienvenidos al repositorio oficial de la cátedra **Programación IV - Comisión 6 (TT)**.  
Aquí trabajaremos de manera colaborativa en los Trabajos Prácticos (TPs) de la materia.

---

## 📂 Estructura del Repositorio
```bash
Enunciados/
│ ├── Unidad 3
│ │     ├── TP1.md
│ │     ├── TP2.md
│ │     ├── TP3.md
│ │     ├── TP4.md
│ │     └── TP5.md
│ ├── Unidad 4
│ │     ├── TP1.md
│ │     ├── TP2.md
│ │     ├── TP3.md
│ │     ├── TP4.md
│ │     └── TP5.md
TPs/
│ ├── 57233 - Roldan Facundo/
│ │ └── Unidad 3/
│ │     ├── TP1/
│ │     ├── TP2/
│ │     └── ...
│ ├── 57286 - Villafañe Mateo Fabián/
│ │ └── Unidad 3/...
│ └── ...
```

- **Enunciados/** → contiene las consignas de cada TP.
- **TPs/** → contiene las carpetas de cada alumno, organizadas por **Legajo - Nombre** y subdivididas por unidades y trabajos prácticos.

---

## 🧑‍💻 Pasos para los Alumnos

### 1️⃣ Clonar el repositorio

Cloná el repositorio en tu máquina:

```bash
git clone https://github.com/CodeWithLuDev/TUP2025-PIV-C6
```
Accede a la carpeta: `cd TUP2025-PIV-C6`



### 2️⃣ Cambiar a tu rama personal

Cada alumno crea su rama siguiendo la convención:
```bash
git checkout -b alumno/57233-Roldan-Facundo
git push -u origin alumno/57233-Roldan-Facundo
```

⚠️ **IMPORTANTE: Siempre trabajen en su rama personal, no en main.**

### 3️⃣ Mantener la rama actualizada

Antes de comenzar a trabajar, sincronizá tu rama con **main** para asegurarte de tener la última versión:

```bash
git checkout main
git pull origin main
git checkout alumno/57233-Roldan-Facundo
git merge main
```
Si hay conflictos, resolvelos antes de seguir.

### 4️⃣ Subir los cambios (tu TP)

1. Agregá tus archivos en la carpeta correcta:
```bash
TPs/57233 - Roldan Facundo/Unidad 3/TP1/
```

2. Hacé commit y push:
```bash
git add .
git commit -m "Entrega TP1 - Unidad 3"
git push origin alumno/57233-Roldan-Facundo
```

### 5️⃣ Crear un Pull Request

Luego de subir tus cambios, entrá al repositorio en GitHub y:

- Hacé clic en "Compare & Pull Request".
- Verificá que la comparación sea:
    - base: main
    - compare: alumno/57233-Roldan-Facundo
- Agregá un comentario explicando qué entregás (ej: "Entrega final TP1").
- Hacé clic en "Create Pull Request".
- Esperá a que el profesor revise y acepte el PR.

### 6️⃣ Revisión y Feedback

Si hay correcciones, el profesor (Yo :D) las dejará en los comentarios del PR.

Hacé los cambios solicitados en tu rama, luego:
```bash
git add .
git commit -m "Correcciones TP1"
git push
```

Esto actualizará automáticamente el PR.

---

## ⚠️ Reglas de Colaboración

- ✅ Trabajá siempre en tu rama personal.
- ✅ Subí solo tus archivos dentro de tu carpeta.
- ✅ Actualizá tu rama antes de empezar cada TP.
- ❌ No hagas commits en main.
- ❌ No modifiques archivos de otros compañeros.

---

## ⚙️ Herramientas y Enlaces
Puedes probar y aprender los comandos de Git de forma interactiva y gráfica desde [ésta página](learngitbranching.js.org).

Si prefieres una lista con los comandos te dejo lo siguiente: 
CheatSheet "[Git - 0 to Pro Reference](https://supersimpledev.github.io/references/git-github-reference.pdf)". (Inglés)

Ahora si deseas un tutorial de como trabajar con branching y merging o tutoriales completos de git te dejo una serie de videos para que puedas decidir cual es mejor para ti:

- [Git Branching and Merging - Detailed Tutorial | SuperSimpleDev](https://www.youtube.com/watch?v=Q1kHG842HoI) (Inglés)
- [Aprende Git y GitHub - Curso desde Cero | FreeCodeCamp Español](https://www.youtube.com/watch?v=mBYSUUnMt9M) (Español)
- [Curso de GIT y GITHUB DESDE CERO Para Aportar a Proyectos | Midulive](https://www.youtube.com/watch?v=niPExbK8lSw) (Español)
- [Curso COMPLETO de GIT y GITHUB desde CERO para PRINCIPIANTES | MoureDev by Brais Moure](https://www.youtube.com/watch?v=3GymExBkKjE) (Español)
- [Aprende GIT ahora! curso completo GRATIS desde cero | HolaMundo](https://www.youtube.com/watch?v=VdGzPZ31ts8) (Español)
- [🚀GIT: DIFF y MERGE - Trabajando con BRANCHES (Ramas)🌳 🤩 | Introducción a GIT y GITHUB #7 | TodoCode](https://www.youtube.com/watch?v=gjKKtQVVCZU) (Español)