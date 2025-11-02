# app.py
from datetime import datetime
from flask import Flask, render_template, request, jsonify, abort

# Usa el context manager de tu db.py (que a su vez usa Config)
from DB import db

app = Flask(__name__)

@app.get("/inicio")
def inicio():
    return render_template("inicio.html")

@app.get("/crear")
def crear_get():
  
    return render_template("CrearTicket.html")

@app.post("/crear")
def crear_post():


    return render_template("CrearTicket.html")

@app.get("/ver")
def ver_get():
    return render_template("verTicket.html")

@app.get("/ver/buscar")
def ver_buscar():
    
    return render_template("verTicket.html")

@app.get("/actualizar")
def actualizar_get():
    return render_template("actualizarTicket.html")

@app.post("/actualizar")
def actualizar_post():
   

    return render_template("actualizarTicket.html")

@app.get("/eliminar")
def eliminar_get():
    return render_template("eliminarTicket.html")

@app.post("/eliminar")
def eliminar_post():
   

    return render_template("eliminar_resultado.html")

# ---------------------------
# API: Oficinas por municipio (para poblar <select>)
# ---------------------------
@app.get("/api/oficinas")
def api_oficinas_por_municipio():
    id_municipio = request.args.get("id_municipio", type=int)
    if not id_municipio:
        return jsonify([])

    with db() as (_, cur):
        cur.execute("""
            SELECT id_oficina AS value, oficina AS label
              FROM oficinas_regionales
             WHERE id_municipio=%s
             ORDER BY oficina
        """, (id_municipio,))
        data = cur.fetchall()

    return jsonify(data)

# ---------------------------
# Raíz
# ---------------------------
@app.get("/")
def root():
    return render_template("index.html")

if __name__ == "__main__":
    app.run(debug=True)
