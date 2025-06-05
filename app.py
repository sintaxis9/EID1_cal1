import os
import numpy as np
from flask import Flask, render_template, request, redirect, url_for

from core.ellipse_model import EllipseGenerator
from core.collision_engine import CollisionDetector
from simulation.scenario_manager import ScenarioManager

from services.rut_helper import extract_first8_digits, extract_check_digit
from services.adjustment_service import adjust_ellipses
from services.plot_service import build_2d_plot, build_3d_plot

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Formulario inicial que recibe:
      - rut1: RUT del dron 1
      - rut2: RUT del dron 2
      - case_type: "1" (impar) o "2" (par)
    """
    if request.method == "POST":
        rut1 = request.form["rut1"].strip()
        rut2 = request.form["rut2"].strip()
        case_type = request.form["case_type"]
        return redirect(
            url_for("mostrar_resultado",
                    rut1=rut1, rut2=rut2, case_type=case_type)
        )
    return render_template("index.html")


@app.route("/resultado")
def mostrar_resultado():
    """
    - Crea las elipses originales según rut1, rut2 y case_type.
    - Si NO colisionan, muestra gráficos “SAFE” con datos originales.
    - Si SÍ colisionan, muestra gráficos de colisión +
      luego llama a adjust_ellipses(...) → muestra gráficos “SAFE” ajustados.
    """

    rut1 = request.args.get("rut1", default="", type=str).strip()
    rut2 = request.args.get("rut2", default="", type=str).strip()
    case_type = request.args.get("case_type", default="1", type=str)

    clean1 = ''.join(filter(str.isdigit, rut1))
    clean2 = ''.join(filter(str.isdigit, rut2))
    if len(clean1) < 8 or len(clean2) < 8 or case_type not in ("1", "2"):
        return redirect(url_for("index"))

    manager = ScenarioManager()
    e1, e2 = manager.generate_ellipses(rut1, rut2, case_type=case_type)

    digits1 = e1.digits
    h1, k1 = e1.h, e1.k
    a1, b1 = e1.a, e1.b
    orientation1 = e1.orientation
    eq1_can = e1.canonical_equation()
    A1, B1, C1, D1, F1 = e1.general_equation()
    eq1_gen = f"{A1}x^2 + {B1}y^2 + {C1}x + {D1}y + {F1}"

    digits2 = e2.digits
    h2, k2 = e2.h, e2.k
    a2, b2 = e2.a, e2.b
    orientation2 = e2.orientation
    eq2_can = e2.canonical_equation()
    A2, B2, C2, D2, F2 = e2.general_equation()
    eq2_gen = f"{A2}x^2 + {B2}y^2 + {C2}x + {D2}y + {F2}"

    colision = CollisionDetector.detect_collision(e1, e2)
    nivel = CollisionDetector.collision_risk_level(e1, e2)

    plot2d_div_collision = build_2d_plot([e1, e2], "Trayectorias 2D (originales)")
    plot3d_div_collision = build_3d_plot([e1, e2], "Trayectorias 3D (originales)", height_z=50)

    if not colision:
        return render_template(
            "resultado.html",
            # Parámetros de entrada
            rut1=rut1,
            rut2=rut2,
            case_type=case_type,

            digits1=digits1,
            h1=h1, k1=k1,
            a1=a1, b1=b1,
            orientation1=orientation1,
            eq1_can=eq1_can,
            eq1_gen=eq1_gen,

            digits2=digits2,
            h2=h2, k2=k2,
            a2=a2, b2=b2,
            orientation2=orientation2,
            eq2_can=eq2_can,
            eq2_gen=eq2_gen,

            colision=False,
            nivel=round(nivel * 100, 0),

            plot2d_div=plot2d_div_collision,
            plot3d_div=plot3d_div_collision
        )

    digits1_8 = extract_first8_digits(rut1)
    digits2_8 = extract_first8_digits(rut2)
    check1 = extract_check_digit(rut1)
    check2 = extract_check_digit(rut2)

    final_e1, final_e2, rut1_adjusted, rut2_adjusted, \
        a1_safe, b1_safe, a2_safe, b2_safe = adjust_ellipses(
            e1, e2,
            digits1_8, digits2_8,
            h1, k1, orientation1,
            h2, k2, orientation2,
            case_type,
            rut1, rut2
        )

    plot2d_div_safe = build_2d_plot([final_e1, final_e2], "Trayectorias 2D (ajustado – SAFE)")
    plot3d_div_safe = build_3d_plot([final_e1, final_e2], "Trayectorias 3D (ajustado – SAFE)", height_z=50)

    return render_template(
        "resultado.html",
        rut1=rut1,
        rut2=rut2,
        case_type=case_type,

        digits1=digits1,
        h1=h1, k1=k1,
        a1=a1, b1=b1,
        orientation1=orientation1,
        eq1_can=eq1_can,
        eq1_gen=eq1_gen,

        digits2=digits2,
        h2=h2, k2=k2,
        a2=a2, b2=b2,
        orientation2=orientation2,
        eq2_can=eq2_can,
        eq2_gen=eq2_gen,

        colision=True,
        nivel=round(nivel * 100, 0),

        plot2d_div_collision=plot2d_div_collision,
        plot3d_div_collision=plot3d_div_collision,

        rut1_adjusted=rut1_adjusted,
        rut2_adjusted=rut2_adjusted,

        a1_safe=a1_safe, b1_safe=b1_safe,
        a2_safe=a2_safe, b2_safe=b2_safe,

        plot2d_div_safe=plot2d_div_safe,
        plot3d_div_safe=plot3d_div_safe
    )


if __name__ == "__main__":
    app.run(debug=True)
