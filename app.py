# app.py

from flask import Flask, render_template, request, redirect, url_for
from core.ellipse_model import EllipseGenerator
from core.collision_engine import CollisionDetector
from services.rut_helper import extract_first8_digits
from services.plot_service import build_2d_plot, build_3d_plot
from services.adjustment_service import adjust_ellipses

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
    if request.method == "POST":
        raw_ruts = request.form.getlist("rut_list[]")
        case_type = request.form.get("case_type", "1")

        clean_list = [''.join(filter(str.isdigit, r)) for r in raw_ruts]
        if len(clean_list) < 2 or any(len(rc) < 8 for rc in clean_list) or case_type not in ("1", "2"):
            return redirect(url_for("index"))

        query_params = {}
        for i, r in enumerate(raw_ruts):
            query_params[f"rut_list[{i}]"] = r
        query_params["case_type"] = case_type
        return redirect(url_for("mostrar_resultado", **query_params))

    return render_template("index.html")


@app.route("/resultado")
def mostrar_resultado():
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

    clean_list = [''.join(filter(str.isdigit, r)) for r in raw_ruts]
    if (
        len(clean_list) < 2
        or any(len(rc) < 8 for rc in clean_list)
        or case_type not in ("1", "2")
    ):
        return redirect(url_for("index"))

    n = len(raw_ruts)

    ellipses_orig = []
    for r in raw_ruts:
        e = EllipseGenerator(r, case_type=case_type)
        ellipses_orig.append(e)

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

    ellipses_final = [e for e in ellipses_orig]
    ruts_final = [r for r in raw_ruts]

    def existe_colision(lista_ellipses):
        for x in range(len(lista_ellipses)):
            for y in range(x + 1, len(lista_ellipses)):
                if CollisionDetector.detect_collision(lista_ellipses[x], lista_ellipses[y]):
                    return True
        return False

    max_iter = 50
    iter_count = 0

    while existe_colision(ellipses_final) and iter_count < max_iter:
        iter_count += 1

        pares_conflicto = []
        for i in range(n):
            for j in range(i + 1, n):
                if CollisionDetector.detect_collision(ellipses_final[i], ellipses_final[j]):
                    pares_conflicto.append((i, j))

        if not pares_conflicto:
            break

        for (i, j) in pares_conflicto:
            e1 = ellipses_final[i]
            e2 = ellipses_final[j]

            digits1 = extract_first8_digits(ruts_final[i])
            digits2 = extract_first8_digits(ruts_final[j])
            h1, k1 = e1.h, e1.k
            h2, k2 = e2.h, e2.k
            orientation1 = e1.orientation
            orientation2 = e2.orientation
            rut1_str = ruts_final[i]
            rut2_str = ruts_final[j]

            e1_new, e2_new, rut1_new, rut2_new, a1_safe, b1_safe, a2_safe, b2_safe = adjust_ellipses(
                e1, e2,
                digits1, digits2,
                h1, k1, orientation1,
                h2, k2, orientation2,
                case_type,
                rut1_str, rut2_str
            )

            ellipses_final[i] = e1_new
            ellipses_final[j] = e2_new
            ruts_final[i] = rut1_new
            ruts_final[j] = rut2_new


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

    plot2d_orig = build_2d_plot(
        ellipses_orig,
        title="Trayectorias 2D (Originales)"
    )
    plot3d_orig = build_3d_plot(
        ellipses_orig,
        title="Trayectorias 3D (Originales)",
        height_z=50
    )

    plot2d_final = build_2d_plot(
        ellipses_final,
        title="Trayectorias 2D (Finales – SAFE)"
    )
    plot3d_final = build_3d_plot(
        ellipses_final,
        title="Trayectorias 3D (Finales – SAFE)",
        height_z=50
    )

    return render_template(
        "resultado_multiple.html",

        raw_ruts=raw_ruts,
        orig_params=orig_params,
        collisions_orig=collisions_orig,
        plot2d_orig=plot2d_orig,
        plot3d_orig=plot3d_orig,

        final_params=final_params,
        collisions_final=collisions_final,
        plot2d_final=plot2d_final,
        plot3d_final=plot3d_final
    )


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)
