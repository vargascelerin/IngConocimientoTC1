from flask import Flask, request, jsonify, render_template
import rule_engine


class MotorReglasPrestamosBancarios:
    def __init__(self):
        self.reglas = []
        self.cargar_reglas()

    def cargar_reglas(self):
        """
        Definir reglas de decisión para la aprobación del préstamo basadas en los grupos
        de Confianza, Recursos y el factor de Aval.
        """
        # Rechazado: Si confianza es alto o recursos es alto y no hay aval de alto valor
        self.reglas.append({
            "expresion": "(grupo_confianza == 'alto' or grupo_recursos == 'alto') and aval != 'alto'",
            "decision": "Rechazado"
        })

        # Aprobado condicional: Si hay aval de valor medio y (confianza o recursos no son alto)
        self.reglas.append({
            "expresion": "aval == 'medio' and (grupo_confianza != 'alto' or grupo_recursos != 'alto')",
            "decision": "Aprobado condicional"
        })

        # Aprobado: Si confianza y recursos no son alto y hay aval de alto o medio valor
        self.reglas.append({
            "expresion": "grupo_confianza != 'alto' and grupo_recursos != 'alto' and (aval == 'alto' or aval == 'medio')",
            "decision": "Aprobado"
        })

        # Aprobado condicional: Si confianza no es alto y hay aval de alto valor
        self.reglas.append({
            "expresion": "grupo_confianza != 'alto' and aval == 'alto'",
            "decision": "Aprobado condicional"
        })

        # Rechazado: Si confianza es alto y aval es medio o bajo
        self.reglas.append({
            "expresion": "grupo_confianza == 'alto' and (aval == 'medio' or aval == 'bajo')",
            "decision": "Rechazado"
        })

    def evaluar_riesgo(self, cliente):
        """
        Evalúa los factores de riesgo individuales y los agrupa en Confianza y Recursos.
        """
        # Evaluar factores individuales (pero no los incluiremos en el resultado)
        factores_individuales = {
            # Grupo Confianza
            "riesgo_credito": self.evaluar_puntaje_credito(cliente['puntaje_credito']),
            "riesgo_empleo": self.evaluar_riesgo_empleo(cliente['tipo_empleo'], cliente['años_empleo']),
            "riesgo_historial_prestamos": self.evaluar_historial_prestamos(cliente['historial_prestamos']),

            # Grupo Recursos
            "riesgo_ingresos": self.evaluar_riesgo_ingresos(cliente['ingresos_mensuales'], cliente['cuota_prestamo']),
            "riesgo_deuda_ingreso": self.evaluar_riesgo_deuda_ingreso(cliente['proporcion_deuda_ingreso']),
        }

        # Evaluar grupo de Confianza
        factores_confianza = [
            factores_individuales["riesgo_credito"],
            factores_individuales["riesgo_empleo"],
            factores_individuales["riesgo_historial_prestamos"]
        ]

        # Evaluar grupo de Recursos
        factores_recursos = [
            factores_individuales["riesgo_ingresos"],
            factores_individuales["riesgo_deuda_ingreso"]
        ]

        # Crear el resultado solo con los grupos y el aval
        factores_riesgo = {
            "grupo_confianza": self.clasificar_grupo(factores_confianza),
            "grupo_recursos": self.clasificar_grupo(factores_recursos),
            "aval": self.clasificar_aval(cliente['tipo_garantia'])
        }

        return factores_riesgo

    def clasificar_grupo(self, factores):
        """
        Clasifica un grupo de factores como bajo, moderado o alto.
        La clasificación se basa en el peor factor del grupo.
        """
        if "alto" in factores:
            return "alto"
        elif "moderado" in factores:
            return "moderado"
        else:
            return "bajo"

    def clasificar_aval(self, tipo_garantia):
        """
        Clasifica el aval como alto, medio o bajo según su tipo.
        """
        if tipo_garantia == "propiedad":
            return "alto"
        elif tipo_garantia == "aval_alto_valor":
            return "alto"
        elif tipo_garantia == "aval_bajo_valor":
            return "medio"
        else:
            return "bajo"

    def evaluar_puntaje_credito(self, puntaje):
        return "bajo" if puntaje > 750 else "moderado" if 600 <= puntaje <= 750 else "alto"

    def evaluar_riesgo_ingresos(self, ingresos_mensuales, cuota_prestamo):
        return "bajo" if ingresos_mensuales > 3 * cuota_prestamo else "moderado" if 1.5 * cuota_prestamo <= ingresos_mensuales <= 3 * cuota_prestamo else "alto"

    def evaluar_riesgo_deuda_ingreso(self, proporcion_deuda_ingreso):
        return "bajo" if proporcion_deuda_ingreso < 0.3 else "moderado" if 0.3 <= proporcion_deuda_ingreso <= 0.5 else "alto"

    def evaluar_riesgo_empleo(self, tipo_empleo, años_empleo):
        return "bajo" if tipo_empleo == "fijo" and años_empleo > 5 else "moderado" if tipo_empleo == "fijo" and años_empleo <= 5 else "alto"

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

        # Si ninguna regla se aplica, rechazar por defecto
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
            "id": 3,
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
            "id": 4,
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