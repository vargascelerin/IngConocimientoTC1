from flask import Flask, render_template, request

app=Flask(__name__)
# Datos de clientes
clientes = [
    {
        "nombre": "Mayabi",
        "edad": 22,
        "salud": "saludable",
        "historial_familiar": "false",
        "estilo_vida": "activo",
        "ocupacion": "oficina",
        "historial_seguro": "bueno"
    },
    {
        "nombre": "Carlos",
        "edad": 45,
        "salud": "diabetes",
        "historial_familiar": "true",
        "estilo_vida": "fumador",
        "ocupacion": "minero",
        "historial_seguro": "reclamos_frecuentes"
    },
    {
        "nombre": "Jaime",
        "edad": 50,
        "salud": "Saludable",
        "historial_familiar": "false",
        "estilo_vida": "deportista",
        "ocupacion": "oficina",
        "historial_seguro": "bueno"
    }
]

def calcular_puntaje(cliente):
    puntaje = 0

    if 30 <= cliente["edad"] <= 50:
        puntaje += 3
    elif 51 <= cliente["edad"] <= 65:
            puntaje += 4
    elif cliente["edad"] > 65:
        puntaje += 5


    if cliente["salud"].lower() in ["diabetes", "hipertension", "obesidad"]:
        puntaje += 2
    if cliente["historial_familiar"] == "true":
        puntaje += 1
    if cliente["historial_seguro"] == "reclamos_frecuentes":
        puntaje += 1

    # Puntaje por hábitos
    if cliente["estilo_vida"].lower() in ["fumador", "alcoholico"]:
        puntaje += 2
    if cliente["ocupacion"].lower() in ["minero", "piloto", "bombero"]:
        puntaje += 2

    return puntaje

def clasificar_riesgo(puntaje):
    if puntaje <= 2:
        return "Bajo Riesgo"
    elif 3 <= puntaje <= 4:
        return "Moderado Riesgo"
    else:
        return "Alto Riesgo"
                                            
@app.route("/", methods=["GET", "POST"])
def index():
    resultado = None
    if request.method == "POST":
        cliente = {
            "nombre": request.form["nombre"],
            "edad": int(request.form["edad"]),
            "salud": request.form["salud"],
            "historial_familiar": request.form["historial_familiar"],
            "estilo_vida": request.form["estilo_vida"],
            "ocupacion": request.form["ocupacion"],
            "historial_seguro": request.form["historial_seguro"]
        }
        
        puntaje = calcular_puntaje(cliente)
        nivel_riesgo = clasificar_riesgo(puntaje)
        resultado = {
            "nombre": cliente["nombre"],
            "puntaje": puntaje,
            "nivel_riesgo": nivel_riesgo
        }

    return render_template("index.html", resultado=resultado)

if __name__ == "__main__":
    app.run(debug=True)
