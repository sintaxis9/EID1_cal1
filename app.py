import os
import numpy as np
from flask import Flask, render_template, request, redirect, url_for

import plotly.graph_objects as go
import plotly.io as pio

from core.ellipse_model import EllipseGenerator
from core.collision_engine import CollisionDetector
from simulation.scenario_manager import ScenarioManager

app = Flask(__name__)


@app.route("/", methods=["GET", "POST"])
def index():
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

    fig2d_col = go.Figure()
    colores = ["blue", "red"]
    for i, dron in enumerate([e1, e2]):
        x, y, _ = dron.generate_points(height=0, num_points=200)
        fig2d_col.add_trace(
            go.Scatter(
                x=x.tolist(),
                y=y.tolist(),
                mode="lines",
                name=f"Dron {i+1}",
                line=dict(color=colores[i]),
                hovertemplate=(
                    f"Dron {i+1}<br>h={dron.h}, k={dron.k}<br>"
                    f"a={dron.a}, b={dron.b}<br>"
                    f"x=%{{x:.2f}}, y=%{{y:.2f}}<extra></extra>"
                )
            )
        )
        fig2d_col.add_trace(
            go.Scatter(
                x=[dron.h],
                y=[dron.k],
                mode="markers+text",
                marker=dict(color=colores[i], size=6),
                text=[f"({dron.h},{dron.k})"],
                textposition="top center",
                showlegend=False
            )
        )
    fig2d_col.update_layout(
        title="Trayectorias 2D (originales)",
        xaxis_title="X", yaxis_title="Y",
        legend=dict(x=0.85, y=0.95),
        width=600, height=600,
        margin=dict(l=40, r=40, t=40, b=40),
    )
    plot2d_div_collision = pio.to_html(fig2d_col, full_html=False, include_plotlyjs=False)

    fig3d_col = go.Figure()
    altura_default = 50
    for i, dron in enumerate([e1, e2]):
        x3, y3, z3 = dron.generate_points(height=altura_default, num_points=200)
        fig3d_col.add_trace(
            go.Scatter3d(
                x=x3.tolist(), y=y3.tolist(), z=z3.tolist(),
                mode="lines",
                name=f"Dron {i+1}",
                line=dict(color=colores[i], width=3),
                hovertemplate=(
                    f"Dron {i+1}<br>h={dron.h}, k={dron.k}, z={altura_default}<br>"
                    f"a={dron.a}, b={dron.b}<br>"
                    f"x=%{{x:.2f}}, y=%{{y:.2f}}, z=%{{z:.2f}}<extra></extra>"
                )
            )
        )
        fig3d_col.add_trace(
            go.Scatter3d(
                x=[dron.h], y=[dron.k], z=[altura_default],
                mode="markers+text",
                marker=dict(color=colores[i], size=4),
                text=[f"({dron.h},{dron.k},{altura_default})"],
                textposition="top center",
                showlegend=False
            )
        )
    fig3d_col.update_layout(
        title="Trayectorias 3D (originales)",
        scene=dict(xaxis_title="X", yaxis_title="Y", zaxis_title="Z", aspectmode="auto"),
        width=600, height=600,
        margin=dict(l=40, r=40, t=40, b=40),
    )
    plot3d_div_collision = pio.to_html(fig3d_col, full_html=False, include_plotlyjs=False)

    if not colision:
        return render_template(
            "resultado.html",
            rut1=rut1, rut2=rut2, case_type=case_type,
            digits1=digits1, h1=h1, k1=k1, a1=a1, b1=b1, orientation1=orientation1,
            eq1_can=eq1_can, eq1_gen=eq1_gen,
            digits2=digits2, h2=h2, k2=k2, a2=a2, b2=b2, orientation2=orientation2,
            eq2_can=eq2_can, eq2_gen=eq2_gen,
            colision=False, nivel=round(nivel*100, 0),
            plot2d_div=plot2d_div_collision,
            plot3d_div=plot3d_div_collision
        )


    clean2_full = ''.join(filter(str.isdigit, rut2))
    check_digit2 = clean2_full[8:] if len(clean2_full) > 8 else ""
    first8_2 = digits2.copy()

    clean1_full = ''.join(filter(str.isdigit, rut1))
    check_digit1 = clean1_full[8:] if len(clean1_full) > 8 else ""
    first8_1 = digits1.copy()

    orig_a2, orig_b2 = a2, b2
    orig_a1, orig_b1 = a1, b1

    a1_safe = a1
    b1_safe = b1
    rut1_adjusted = rut1

    a2_safe = a2
    b2_safe = b2
    rut2_adjusted = rut2

    def format_rut_from_digits(digs8, check):
        s8 = ''.join(str(d) for d in digs8)
        if len(s8) != 8:
            return s8 + (("-" + check) if check else "")
        if check:
            return f"{s8[0:2]}.{s8[2:5]}.{s8[5:8]}-{check}"
        else:
            return f"{s8[0:2]}.{s8[2:5]}.{s8[5:8]}"

    def test_collision_e2(candidate_digits2):
        tmp = EllipseGenerator(format_rut_from_digits(candidate_digits2, check_digit2), case_type=case_type)
        tmp.h, tmp.k = h2, k2
        tmp.orientation = orientation2
        if case_type == "1":
            tmp.a = candidate_digits2[2] + candidate_digits2[3]
            tmp.b = candidate_digits2[4] + candidate_digits2[5]
        else:
            tmp.a = candidate_digits2[5] + candidate_digits2[6]
            tmp.b = candidate_digits2[7] + candidate_digits2[2]
        if tmp.a < 1 or tmp.b < 1:
            return True  # “True” para descartar
        return CollisionDetector.detect_collision(e1, tmp)

    def test_collision_e1(candidate_digits1):
        tmp = EllipseGenerator(format_rut_from_digits(candidate_digits1, check_digit1), case_type=case_type)
        tmp.h, tmp.k = h1, k1
        tmp.orientation = orientation1
        if case_type == "1":
            tmp.a = candidate_digits1[2] + candidate_digits1[3]
            tmp.b = candidate_digits1[4] + candidate_digits1[5]
        else:
            tmp.a = candidate_digits1[5] + candidate_digits1[6]
            tmp.b = candidate_digits1[7] + candidate_digits1[2]
        if tmp.a < 1 or tmp.b < 1:
            return True
        return CollisionDetector.detect_collision(tmp, e2)


    new_digits2 = first8_2.copy()
    new_rut2 = rut2
    found2 = False

    if case_type == "1":
        d3_o, d4_o, d5_o, d6_o = first8_2[2], first8_2[3], first8_2[4], first8_2[5]
        for reduccion in range(1, orig_a2 + orig_b2 + 1):
            for new_a2 in range(orig_a2 - 1, 0, -1):
                redA = orig_a2 - new_a2
                redB = reduccion - redA
                new_b2 = orig_b2 - redB
                if new_b2 < 1 or new_b2 > orig_b2:
                    continue
                candidatos_a = []
                for i in range(0, 10):
                    j = new_a2 - i
                    if 0 <= j <= 9:
                        candidatos_a.append((abs(i - d3_o), i, j))
                if not candidatos_a:
                    continue
                candidatos_a.sort(key=lambda x: (x[0], -x[1]))

                candidatos_b = []
                for i in range(0, 10):
                    j = new_b2 - i
                    if 0 <= j <= 9:
                        candidatos_b.append((abs(i - d5_o), i, j))
                if not candidatos_b:
                    continue
                candidatos_b.sort(key=lambda x: (x[0], -x[1]))

                for _, c3, c4 in candidatos_a:
                    for _, c5, c6 in candidatos_b:
                        tmp_digits2 = first8_2.copy()
                        tmp_digits2[2], tmp_digits2[3] = c3, c4
                        tmp_digits2[4], tmp_digits2[5] = c5, c6
                        if not test_collision_e2(tmp_digits2):
                            new_digits2 = tmp_digits2.copy()
                            new_rut2 = format_rut_from_digits(new_digits2, check_digit2)
                            a2_safe, b2_safe = new_a2, new_b2
                            found2 = True
                            break
                    if found2:
                        break
                if found2:
                    break
            if found2:
                break

        if not found2:
            nueva_a2 = max(1, orig_a2 - 1)
            pareja = None
            for i in range(9, -1, -1):
                j = nueva_a2 - i
                if 0 <= j <= 9:
                    pareja = (i, j)
                    break
            if pareja and orig_b2 >= 1:
                tmp_digits2 = first8_2.copy()
                tmp_digits2[2], tmp_digits2[3] = pareja
                new_digits2 = tmp_digits2.copy()
                new_rut2 = format_rut_from_digits(new_digits2, check_digit2)
                a2_safe, b2_safe = nueva_a2, orig_b2

    else:  # case_type == "2"
        d6_o, d7_o, d8_o, d3_o = first8_2[5], first8_2[6], first8_2[7], first8_2[2]
        for reduccion in range(1, orig_a2 + orig_b2 + 1):
            for new_a2 in range(orig_a2 - 1, 0, -1):
                redA = orig_a2 - new_a2
                redB = reduccion - redA
                new_b2 = orig_b2 - redB
                if new_b2 < 1 or new_b2 > orig_b2:
                    continue
                candidatos_a = []
                for i in range(0, 10):
                    j = new_a2 - i
                    if 0 <= j <= 9:
                        candidatos_a.append((abs(i - d6_o), i, j))
                if not candidatos_a:
                    continue
                candidatos_a.sort(key=lambda x: (x[0], -x[1]))

                candidatos_b = []
                for i in range(0, 10):
                    j = new_b2 - i
                    if 0 <= j <= 9:
                        candidatos_b.append((abs(i - d8_o), i, j))
                if not candidatos_b:
                    continue
                candidatos_b.sort(key=lambda x: (x[0], -x[1]))

                for _, c6, c7 in candidatos_a:
                    for _, c8, c3b in candidatos_b:
                        tmp_digits2 = first8_2.copy()
                        tmp_digits2[5], tmp_digits2[6] = c6, c7
                        tmp_digits2[7], tmp_digits2[2] = c8, c3b
                        if not test_collision_e2(tmp_digits2):
                            new_digits2 = tmp_digits2.copy()
                            new_rut2 = format_rut_from_digits(new_digits2, check_digit2)
                            a2_safe, b2_safe = new_a2, new_b2
                            found2 = True
                            break
                    if found2:
                        break
                if found2:
                    break
            if found2:
                break

        if not found2:
            nueva_a2 = max(1, orig_a2 - 1)
            pareja = None
            for i in range(9, -1, -1):
                j = nueva_a2 - i
                if 0 <= j <= 9:
                    pareja = (i, j)
                    break
            if pareja and orig_b2 >= 1:
                tmp_digits2 = first8_2.copy()
                tmp_digits2[5], tmp_digits2[6] = pareja
                new_digits2 = tmp_digits2.copy()
                new_rut2 = format_rut_from_digits(new_digits2, check_digit2)
                a2_safe, b2_safe = nueva_a2, orig_b2

    # Reconstruir la elipse candidata 2 con el posible ajuste
    e2_candidate = EllipseGenerator(new_rut2, case_type=case_type)
    e2_candidate.h, e2_candidate.k = h2, k2
    e2_candidate.orientation = orientation2
    e2_candidate.a, e2_candidate.b = a2_safe, b2_safe

    if CollisionDetector.detect_collision(e1, e2_candidate):
        new_digits1 = first8_1.copy()
        new_rut1 = rut1
        found1 = False

        if case_type == "1":
            d3o1, d4o1, d5o1, d6o1 = first8_1[2], first8_1[3], first8_1[4], first8_1[5]
            for reduccion in range(1, orig_a1 + orig_b1 + 1):
                for new_a1 in range(orig_a1 - 1, 0, -1):
                    redA = orig_a1 - new_a1
                    redB = reduccion - redA
                    new_b1 = orig_b1 - redB
                    if new_b1 < 1 or new_b1 > orig_b1:
                        continue
                    paresA = []
                    for i in range(0, 10):
                        j = new_a1 - i
                        if 0 <= j <= 9:
                            paresA.append((abs(i - d3o1), i, j))
                    if not paresA:
                        continue
                    paresA.sort(key=lambda x: (x[0], -x[1]))
                    paresB = []
                    for i in range(0, 10):
                        j = new_b1 - i
                        if 0 <= j <= 9:
                            paresB.append((abs(i - d5o1), i, j))
                    if not paresB:
                        continue
                    paresB.sort(key=lambda x: (x[0], -x[1]))
                    for _, c3, c4 in paresA:
                        for _, c5, c6 in paresB:
                            tmp_digits1 = first8_1.copy()
                            tmp_digits1[2], tmp_digits1[3] = c3, c4
                            tmp_digits1[4], tmp_digits1[5] = c5, c6
                            if not test_collision_e1(tmp_digits1):
                                new_digits1 = tmp_digits1.copy()
                                new_rut1 = format_rut_from_digits(new_digits1, check_digit1)
                                a1_safe, b1_safe = new_a1, new_b1
                                found1 = True
                                break
                        if found1:
                            break
                    if found1:
                        break
                if found1:
                    break
            if not found1:
                nueva_a1 = max(1, orig_a1 - 1)
                pareja = None
                for i in range(9, -1, -1):
                    j = nueva_a1 - i
                    if 0 <= j <= 9:
                        pareja = (i, j)
                        break
                if pareja and orig_b1 >= 1:
                    tmp_digits1 = first8_1.copy()
                    tmp_digits1[2], tmp_digits1[3] = pareja
                    new_digits1 = tmp_digits1.copy()
                    new_rut1 = format_rut_from_digits(new_digits1, check_digit1)
                    a1_safe, b1_safe = nueva_a1, orig_b1

        else:  # case_type == "2"
            d6o1, d7o1, d8o1, d3o1 = first8_1[5], first8_1[6], first8_1[7], first8_1[2]
            for reduccion in range(1, orig_a1 + orig_b1 + 1):
                for new_a1 in range(orig_a1 - 1, 0, -1):
                    redA = orig_a1 - new_a1
                    redB = reduccion - redA
                    new_b1 = orig_b1 - redB
                    if new_b1 < 1 or new_b1 > orig_b1:
                        continue
                    paresA = []
                    for i in range(0, 10):
                        j = new_a1 - i
                        if 0 <= j <= 9:
                            paresA.append((abs(i - d6o1), i, j))
                    if not paresA:
                        continue
                    paresA.sort(key=lambda x: (x[0], -x[1]))
                    paresB = []
                    for i in range(0, 10):
                        j = new_b1 - i
                        if 0 <= j <= 9:
                            paresB.append((abs(i - d8o1), i, j))
                    if not paresB:
                        continue
                    paresB.sort(key=lambda x: (x[0], -x[1]))
                    for _, c6, c7 in paresA:
                        for _, c8, c3b in paresB:
                            tmp_digits1 = first8_1.copy()
                            tmp_digits1[5], tmp_digits1[6] = c6, c7
                            tmp_digits1[7], tmp_digits1[2] = c8, c3b
                            if not test_collision_e1(tmp_digits1):
                                new_digits1 = tmp_digits1.copy()
                                new_rut1 = format_rut_from_digits(new_digits1, check_digit1)
                                a1_safe, b1_safe = new_a1, new_b1
                                found1 = True
                                break
                        if found1:
                            break
                    if found1:
                        break
                if found1:
                    break
            if not found1:
                nueva_a1 = max(1, orig_a1 - 1)
                pareja = None
                for i in range(9, -1, -1):
                    j = nueva_a1 - i
                    if 0 <= j <= 9:
                        pareja = (i, j)
                        break
                if pareja and orig_b1 >= 1:
                    tmp_digits1 = first8_1.copy()
                    tmp_digits1[5], tmp_digits1[6] = pareja
                    new_digits1 = tmp_digits1.copy()
                    new_rut1 = format_rut_from_digits(new_digits1, check_digit1)
                    a1_safe, b1_safe = nueva_a1, orig_b1

        # Reconstruir elipse candidata 1
        e1_candidate = EllipseGenerator(new_rut1, case_type=case_type)
        e1_candidate.h, e1_candidate.k = h1, k1
        e1_candidate.orientation = orientation1
        e1_candidate.a, e1_candidate.b = a1_safe, b1_safe

        if CollisionDetector.detect_collision(e1_candidate, e2):
            nueva_a2 = max(1, orig_a2 - 1)
            nueva_a1 = max(1, orig_a1 - 1)

            # Ajustar dígitos de dron 2 para que sume nueva_a2
            tmp_digits2 = first8_2.copy()
            pareja2 = None
            if case_type == "1":
                for i in range(9, -1, -1):
                    j = nueva_a2 - i
                    if 0 <= j <= 9:
                        pareja2 = (i, j)
                        break
                if pareja2:
                    tmp_digits2[2], tmp_digits2[3] = pareja2
            else:
                for i in range(9, -1, -1):
                    j = nueva_a2 - i
                    if 0 <= j <= 9:
                        pareja2 = (i, j)
                        break
                if pareja2:
                    tmp_digits2[5], tmp_digits2[6] = pareja2

            tmp_digits1 = first8_1.copy()
            pareja1 = None
            if case_type == "1":
                for i in range(9, -1, -1):
                    j = nueva_a1 - i
                    if 0 <= j <= 9:
                        pareja1 = (i, j)
                        break
                if pareja1:
                    tmp_digits1[2], tmp_digits1[3] = pareja1
            else:
                for i in range(9, -1, -1):
                    j = nueva_a1 - i
                    if 0 <= j <= 9:
                        pareja1 = (i, j)
                        break
                if pareja1:
                    tmp_digits1[5], tmp_digits1[6] = pareja1

            new_rut2 = format_rut_from_digits(tmp_digits2, check_digit2)
            new_rut1 = format_rut_from_digits(tmp_digits1, check_digit1)

            e2_both = EllipseGenerator(new_rut2, case_type=case_type)
            e2_both.h, e2_both.k = h2, k2
            e2_both.orientation = orientation2
            e2_both.a, e2_both.b = nueva_a2, orig_b2

            e1_both = EllipseGenerator(new_rut1, case_type=case_type)
            e1_both.h, e1_both.k = h1, k1
            e1_both.orientation = orientation1
            e1_both.a, e1_both.b = nueva_a1, orig_b1

            if not CollisionDetector.detect_collision(e1_both, e2_both):
                final_e1 = e1_both
                final_e2 = e2_both
                rut1_adjusted = new_rut1
                rut2_adjusted = new_rut2
            else:
                final_e1 = e1
                final_e2 = e2_candidate
                rut1_adjusted = rut1
                rut2_adjusted = new_rut2
        else:
            final_e1 = e1_candidate
            final_e2 = e2
            rut1_adjusted = new_rut1
            rut2_adjusted = rut2
    else:
        final_e1 = e1
        final_e2 = e2_candidate
        rut1_adjusted = rut1
        rut2_adjusted = new_rut2

    fig2d_safe = go.Figure()
    for i, dron in enumerate([final_e1, final_e2]):
        x, y, _ = dron.generate_points(height=0, num_points=200)
        fig2d_safe.add_trace(
            go.Scatter(
                x=x.tolist(),
                y=y.tolist(),
                mode="lines",
                name=f"Dron {i+1}",
                line=dict(color=colores[i]),
                hovertemplate=(
                    f"Dron {i+1}<br>h={dron.h}, k={dron.k}<br>"
                    f"a={dron.a}, b={dron.b}<br>"
                    f"x=%{{x:.2f}}, y=%{{y:.2f}}<extra></extra>"
                )
            )
        )
        fig2d_safe.add_trace(
            go.Scatter(
                x=[dron.h],
                y=[dron.k],
                mode="markers+text",
                marker=dict(color=colores[i], size=6),
                text=[f"({dron.h},{dron.k})"],
                textposition="top center",
                showlegend=False
            )
        )
    fig2d_safe.update_layout(
        title="Trayectorias 2D (ajustado – SAFE)",
        xaxis_title="X", yaxis_title="Y",
        legend=dict(x=0.85, y=0.95),
        width=600, height=600,
        margin=dict(l=40, r=40, t=40, b=40),
    )
    plot2d_div_safe = pio.to_html(fig2d_safe, full_html=False, include_plotlyjs=False)

    fig3d_safe = go.Figure()
    for i, dron in enumerate([final_e1, final_e2]):
        x3, y3, z3 = dron.generate_points(height=altura_default, num_points=200)
        fig3d_safe.add_trace(
            go.Scatter3d(
                x=x3.tolist(), y=y3.tolist(), z=z3.tolist(),
                mode="lines",
                name=f"Dron {i+1}",
                line=dict(color=colores[i], width=3),
                hovertemplate=(
                    f"Dron {i+1}<br>h={dron.h}, k={dron.k}, z={altura_default}<br>"
                    f"a={dron.a}, b={dron.b}<br>"
                    f"x=%{{x:.2f}}, y=%{{y:.2f}}, z=%{{z:.2f}}<extra></extra>"
                )
            )
        )
        fig3d_safe.add_trace(
            go.Scatter3d(
                x=[dron.h], y=[dron.k], z=[altura_default],
                mode="markers+text",
                marker=dict(color=colores[i], size=4),
                text=[f"({dron.h},{dron.k},{altura_default})"],
                textposition="top center",
                showlegend=False
            )
        )
    fig3d_safe.update_layout(
        title="Trayectorias 3D (ajustado – SAFE)",
        scene=dict(xaxis_title="X", yaxis_title="Y", zaxis_title="Z", aspectmode="auto"),
        width=600, height=600,
        margin=dict(l=40, r=40, t=40, b=40),
    )
    plot3d_div_safe = pio.to_html(fig3d_safe, full_html=False, include_plotlyjs=False)

    return render_template(
        "resultado.html",
        rut1=rut1, rut2=rut2, case_type=case_type,

        digits1=digits1, h1=h1, k1=k1,
        a1=a1, b1=b1, orientation1=orientation1,
        eq1_can=eq1_can, eq1_gen=eq1_gen,

        digits2=digits2, h2=h2, k2=k2,
        a2=a2, b2=b2, orientation2=orientation2,
        eq2_can=eq2_can, eq2_gen=eq2_gen,

        colision=True, nivel=round(nivel * 100, 0),

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
