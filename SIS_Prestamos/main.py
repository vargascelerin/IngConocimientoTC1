from flask import Flask, request, jsonify, render_template
import rule_engine


class MotorReglasPrestamosBancarios:
    def __init__(self):
        self.reglas = []
        self.cargar_reglas()

    def cargar_reglas(self):
        """
        Definir reglas de decisión para la aprobación del préstamo.
        """
        self.reglas.append({
            "expresion": "cantidad_riesgo_alto >= 3",
            "decision": "Rechazado"
        })
        self.reglas.append({
            "expresion": "cantidad_riesgo_alto == 0",
            "decision": "Aprobado"
        })
        self.reglas.append({
            "expresion": "cantidad_riesgo_alto > 0 and cantidad_riesgo_alto < 3",
            "decision": "Aprobado condicional"
        })

    def evaluar_riesgo(self, cliente):
        """
        Asignar valores de riesgo a cada factor del cliente.
        """
        factores_riesgo = {
            "riesgo_credito": self.evaluar_puntaje_credito(cliente['puntaje_credito']),
            "riesgo_ingresos": self.evaluar_riesgo_ingresos(cliente['ingresos_mensuales'], cliente['cuota_prestamo']),
            "riesgo_deuda_ingreso": self.evaluar_riesgo_deuda_ingreso(cliente['proporcion_deuda_ingreso']),
            "riesgo_empleo": self.evaluar_riesgo_empleo(cliente['tipo_empleo'], cliente['años_empleo']),
            "riesgo_garantia": self.evaluar_riesgo_garantia(cliente['tipo_garantia']),
            "riesgo_historial_prestamos": self.evaluar_historial_prestamos(cliente['historial_prestamos'])
        }

        cantidad_riesgo_alto = sum(1 for riesgo in factores_riesgo.values() if riesgo == "alto")
        factores_riesgo["cantidad_riesgo_alto"] = cantidad_riesgo_alto

        return factores_riesgo

    def evaluar_puntaje_credito(self, puntaje):
        return "bajo" if puntaje > 750 else "moderado" if 600 <= puntaje <= 750 else "alto"

    def evaluar_riesgo_ingresos(self, ingresos_mensuales, cuota_prestamo):
        return "bajo" if ingresos_mensuales > 3 * cuota_prestamo else "moderado" if 1.5 * cuota_prestamo <= ingresos_mensuales <= 3 * cuota_prestamo else "alto"

    def evaluar_riesgo_deuda_ingreso(self, proporcion_deuda_ingreso):
        return "bajo" if proporcion_deuda_ingreso < 0.3 else "moderado" if 0.3 <= proporcion_deuda_ingreso <= 0.5 else "alto"

    def evaluar_riesgo_empleo(self, tipo_empleo, años_empleo):
        return "bajo" if tipo_empleo == "fijo" and años_empleo > 5 else "moderado" if tipo_empleo == "fijo" and años_empleo <= 5 else "alto"

    def evaluar_riesgo_garantia(self, tipo_garantia):
        return "bajo" if tipo_garantia in ["propiedad", "aval_alto_valor"] else "alto"

    def evaluar_historial_prestamos(self, historial_prestamos):
        if historial_prestamos == "sin_historial":
            return "moderado"  # Clientes sin historial representan un riesgo moderado
        return "bajo" if historial_prestamos == "sin_retrasos" else "moderado" if historial_prestamos == "retrasos_ocasionales" else "alto"

    def evaluar_prestamo(self, cliente):
        """
        Evaluar solicitud de préstamo según las reglas definidas.
        """
        factores_riesgo = self.evaluar_riesgo(cliente)

        for regla in self.reglas:
            engine = rule_engine.Rule(regla["expresion"])
            if engine.matches(factores_riesgo):
                return {
                    "decision": regla["decision"],
                    "factores_riesgo": factores_riesgo
                }

        return {"decision": "Rechazado", "factores_riesgo": factores_riesgo}


# Crear la aplicación Flask
app = Flask(__name__)
motor = MotorReglasPrestamosBancarios()


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/evaluar', methods=['POST'])
def evaluar_prestamo():
    datos = request.json

    try:
        cliente = {
            "puntaje_credito": int(datos.get('puntaje_credito', 0)),
            "ingresos_mensuales": float(datos.get('ingresos_mensuales', 0)),
            "cuota_prestamo": float(datos.get('cuota_prestamo', 0)),
            "proporcion_deuda_ingreso": float(datos.get('proporcion_deuda_ingreso', 0)),
            "tipo_empleo": datos.get('tipo_empleo', ''),
            "años_empleo": float(datos.get('años_empleo', 0)),
            "tipo_garantia": datos.get('tipo_garantia', ''),
            "historial_prestamos": datos.get('historial_prestamos', '')
        }

        resultado = motor.evaluar_prestamo(cliente)
        return jsonify(resultado)

    except Exception as e:
        return jsonify({"error": str(e)}), 400


@app.route('/api/clientes', methods=['GET'])
def obtener_clientes_ejemplo():
    clientes_ejemplo = [
        {
            "id": 1,
            "nombre": "Cliente de Alto Riesgo",
            "puntaje_credito": 580,
            "ingresos_mensuales": 2000,
            "cuota_prestamo": 1500,
            "proporcion_deuda_ingreso": 0.6,
            "tipo_empleo": "temporal",
            "años_empleo": 1,
            "tipo_garantia": "ninguna",
            "historial_prestamos": "incumplimientos"
        },
        {
            "id": 2,
            "nombre": "Cliente de Riesgo Moderado",
            "puntaje_credito": 700,
            "ingresos_mensuales": 4000,
            "cuota_prestamo": 1500,
            "proporcion_deuda_ingreso": 0.4,
            "tipo_empleo": "fijo",
            "años_empleo": 3,
            "tipo_garantia": "aval_bajo_valor",
            "historial_prestamos": "retrasos_ocasionales"
        },
        {
            "id": 4,
            "nombre": "Cliente de Bajo Riesgo",
            "puntaje_credito": 800,
            "ingresos_mensuales": 6000,
            "cuota_prestamo": 1200,
            "proporcion_deuda_ingreso": 0.2,
            "tipo_empleo": "fijo",
            "años_empleo": 8,
            "tipo_garantia": "propiedad",
            "historial_prestamos": "sin_retrasos"
        },
        {
            "id": 3,
            "nombre": "Cliente Nuevo Sin Historial",
            "puntaje_credito": 720,
            "ingresos_mensuales": 5000,
            "cuota_prestamo": 1800,
            "proporcion_deuda_ingreso": 0.35,
            "tipo_empleo": "fijo",
            "años_empleo": 4,
            "tipo_garantia": "aval_alto_valor",
            "historial_prestamos": "sin_historial"
        }
    ]
    return jsonify(clientes_ejemplo)


if __name__ == '__main__':
    app.run(debug=True)