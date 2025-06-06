# app.py

from flask import Flask, render_template, request, redirect, url_for
from core.ellipse_model import EllipseGenerator
from core.collision_engine import CollisionDetector
from services.rut_helper import extract_first8_digits, extract_check_digit
from services.plot_service import build_2d_plot, build_3d_plot
from services.adjustment_service import adjust_ellipses

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    """
    Formulario que recibe una lista de RUTs ("rut_list[]") y un case_type.
    """
    if request.method == "POST":
        # 1) Obtenemos lista de RUTs
        rut_list = request.form.getlist("rut_list[]")
        case_type = request.form.get("case_type", "1")

        # 2) Validación básica: al menos 2 RUTs y cada uno con ≥ 8 dígitos numéricos
        clean_list = [''.join(filter(str.isdigit, r)) for r in rut_list]
        if (
            len(clean_list) < 2
            or any(len(rc) < 8 for rc in clean_list)
            or case_type not in ("1", "2")
        ):
            return redirect(url_for("index"))

        # 3) Construimos el dict de parámetros para redirigir
        params = {f"rut_list[{i}]": rut_list[i] for i in range(len(rut_list))}
        params["case_type"] = case_type

        # 4) Redirigir a /resultado con todos los rut_list[i] + case_type
        return redirect(url_for("mostrar_resultado", **params))

    return render_template("index.html")


@app.route("/resultado")
def mostrar_resultado():
    """
    Procesa una cantidad variable de RUTs (≥ 2):
      1) Extrae rut_list[0], rut_list[1], ..., case_type de la querystring.
      2) Valida, crea instancias EllipseGenerator y calcula colisiones originales.
      3) Ajusta pares conflictivos uno a uno usando adjust_ellipses(...).
      4) Vuelve a calcular colisiones tras ajuste (idealmente serán cero).
      5) Genera gráficos 2D/3D antes y después del ajuste.
      6) Envía todo a la plantilla para mostrar tablas y gráficos.
    """
    # --- (1) Extraer todos los rut_list[i] de request.args ---
    raw_ruts = []
    i = 0
    while True:
        key = f"rut_list[{i}]"
        if key in request.args:
            raw_ruts.append(request.args.get(key))
            i += 1
        else:
            break

    case_type = request.args.get("case_type", "1")

    # --- (2) Validar al menos 2 RUTs y cada uno con ≥ 8 dígitos numéricos ---
    clean_list = [''.join(filter(str.isdigit, r)) for r in raw_ruts]
    if (
        len(clean_list) < 2
        or any(len(rc) < 8 for rc in clean_list)
        or case_type not in ("1", "2")
    ):
        return redirect(url_for("index"))

    n = len(raw_ruts)

    # --- (3) Crear instancias EllipseGenerator para cada RUT (originales) ---
    ellipses_orig = []
    for r in raw_ruts:
        e = EllipseGenerator(r, case_type=case_type)
        ellipses_orig.append(e)

    # --- (4) Parámetros originales de cada elipse (para tabla) ---
    orig_params = []
    for e in ellipses_orig:
        digits = e.digits
        h, k = e.h, e.k
        a, b = e.a, e.b
        orientation = e.orientation
        eq_can = e.canonical_equation()
        A, B, C, D, F = e.general_equation()
        eq_gen = f"{A}x^2 + {B}y^2 + {C}x + {D}y + {F}"
        orig_params.append({
            "rut": e.rut,
            "digits": digits,
            "h": h,
            "k": k,
            "a": a,
            "b": b,
            "orientation": orientation,
            "eq_can": eq_can,
            "eq_gen": eq_gen
        })

    # --- (5) Detectar colisiones ORIGINALES pairwise (i < j) ---
    collisions_orig = []
    for i in range(n):
        for j in range(i + 1, n):
            e1 = ellipses_orig[i]
            e2 = ellipses_orig[j]
            col = CollisionDetector.detect_collision(e1, e2)
            nivel = CollisionDetector.collision_risk_level(e1, e2)
            collisions_orig.append({
                "i": i,
                "j": j,
                "colision": col,
                "nivel": round(nivel * 100, 0)
            })

    # --- (6) Copiar los datos a listas “finales” para ir ajustando ---
    ellipses_final = ellipses_orig.copy()
    ruts_final = raw_ruts.copy()

    # --- (7) Ajustar cada par conflictivo ---
    for i in range(n):
        for j in range(i + 1, n):
            e1 = ellipses_final[i]
            e2 = ellipses_final[j]
            if CollisionDetector.detect_collision(e1, e2):
                digits1 = extract_first8_digits(ruts_final[i])
                digits2 = extract_first8_digits(ruts_final[j])
                h1, k1 = e1.h, e1.k
                h2, k2 = e2.h, e2.k
                orientation1 = e1.orientation
                orientation2 = e2.orientation
                rut1_str = ruts_final[i]
                rut2_str = ruts_final[j]

                e1_new, e2_new, rut1_new, rut2_new, \
                a1_safe, b1_safe, a2_safe, b2_safe = adjust_ellipses(
                    e1, e2,
                    digits1, digits2,
                    h1, k1, orientation1,
                    h2, k2, orientation2,
                    case_type,
                    rut1_str, rut2_str
                )

                # Actualizamos las listas finales
                ellipses_final[i] = e1_new
                ellipses_final[j] = e2_new
                ruts_final[i] = rut1_new
                ruts_final[j] = rut2_new

    # --- (8) Detectar colisiones FINALES tras ajuste ---
    collisions_final = []
    for i in range(n):
        for j in range(i + 1, n):
            e1f = ellipses_final[i]
            e2f = ellipses_final[j]
            col = CollisionDetector.detect_collision(e1f, e2f)
            nivel = CollisionDetector.collision_risk_level(e1f, e2f)
            collisions_final.append({
                "i": i,
                "j": j,
                "colision": col,
                "nivel": round(nivel * 100, 0)
            })

    # --- (9) Preparar parámetros FINALES para la tabla ---
    final_params = []
    for idx, e in enumerate(ellipses_final):
        digits = e.digits
        h, k = e.h, e.k
        a, b = e.a, e.b
        orientation = e.orientation
        eq_can = e.canonical_equation()
        A, B, C, D, F = e.general_equation()
        eq_gen = f"{A}x^2 + {B}y^2 + {C}x + {D}y + {F}"
        final_params.append({
            "rut": ruts_final[idx],
            "digits": digits,
            "h": h,
            "k": k,
            "a": a,
            "b": b,
            "orientation": orientation,
            "eq_can": eq_can,
            "eq_gen": eq_gen
        })

    # --- (10) Generar gráficos ORIGINALES 2D/3D ---
    plot2d_orig = build_2d_plot(
        ellipses_orig,
        title="Trayectorias 2D (Originales)"
    )
    plot3d_orig = build_3d_plot(
        ellipses_orig,
        title="Trayectorias 3D (Originales)",
        height_z=50
    )

    # --- (11) Generar gráficos FINALES 2D/3D (tras ajuste) ---
    plot2d_final = build_2d_plot(
        ellipses_final,
        title="Trayectorias 2D (Finales – SAFE)"
    )
    plot3d_final = build_3d_plot(
        ellipses_final,
        title="Trayectorias 3D (Finales – SAFE)",
        height_z=50
    )

    # --- (12) Renderizar plantilla con TODA la información ---
    return render_template(
        "resultado_multiple.html",

        # Datos originales
        raw_ruts=raw_ruts,
        orig_params=orig_params,
        collisions_orig=collisions_orig,
        plot2d_orig=plot2d_orig,
        plot3d_orig=plot3d_orig,

        # Datos finales tras ajuste
        final_params=final_params,
        collisions_final=collisions_final,
        plot2d_final=plot2d_final,
        plot3d_final=plot3d_final
    )


if __name__ == "__main__":
    app.run(debug=True)
