from flask import Flask, render_template, request
import rule_engine

app = Flask(__name__)

rules_with_scores = [
    (rule_engine.Rule("edad >= 30 and edad <= 50"), 3),
    (rule_engine.Rule("edad >= 51 and edad <= 65"), 4),
    (rule_engine.Rule("edad > 65"), 5),
    (rule_engine.Rule("salud in ['diabetes', 'hipertension', 'obesidad']"), 2),
    (rule_engine.Rule("historial_familiar == 'true'"), 1),
    (rule_engine.Rule("historial_seguro == 'reclamos_frecuentes'"), 1),
    (rule_engine.Rule("estilo_vida in ['fumador', 'alcoholico']"), 2),
    (rule_engine.Rule("ocupacion in ['minero', 'piloto', 'bombero']"), 2)
]

def calcular_puntaje(cliente):
    puntaje = 0
    for rule, score in rules_with_scores:
        if rule.matches(cliente):
            puntaje += score
    return puntaje

def clasificar_riesgo(puntaje):
    if puntaje <= 1:
        return "Bajo Riesgo"
    elif 2 <= puntaje <= 4:
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
            "salud": request.form["salud"].lower(),
            "historial_familiar": request.form["historial_familiar"],
            "estilo_vida": request.form["estilo_vida"].lower(),
            "ocupacion": request.form["ocupacion"].lower(),
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
