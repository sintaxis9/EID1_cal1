# services/adjustment_service.py

import numpy as np
from core.ellipse_model import EllipseGenerator
from core.collision_engine import CollisionDetector
from services.rut_helper import format_rut_from_digits


def adjust_ellipses(
    e1, e2,
    digits1: list[int], digits2: list[int],
    h1: float, k1: float, orientation1: str,
    h2: float, k2: float, orientation2: str,
    case_type: str,
    rut1_str: str,
    rut2_str: str
) -> tuple[
    EllipseGenerator, EllipseGenerator,
    str, str,  # rut1_adjusted, rut2_adjusted
    int, int,  # a1_safe, b1_safe
    int, int   # a2_safe, b2_safe
]:
    """
    Dada la elipse e1 y e2 originales (ya construidas), sus dígitos [d1..d8],
    centros (h,k) y orientaciones, y los RUTs originales (rut1_str, rut2_str),
    intenta:
      1) Ajustar *solo* e2 (segunda elipse) por brute-force, manteniendo semiejes ≥ 1.
      2) Si no es suficiente, ajustar *solo* e1.
      3) Si aún colisionan, ajustar ambos simultáneamente (mínima reducción en a).
    Devuelve:
      - final_e1, final_e2: las dos instancias EllipseGenerator finales que NO colisionan.
      - rut1_adjusted, rut2_adjusted: sus RUTs (con dígito verificador intacto si aplica).
      - a1_safe, b1_safe, a2_safe, b2_safe: semiejes definitivos (todos ≥ 1).
    """

    # 0) Valores originales
    orig_a1, orig_b1 = e1.a, e1.b
    orig_a2, orig_b2 = e2.a, e2.b

    # 1) Inicializamos por defecto: sin cambios en e1 ni e2
    a1_safe, b1_safe = orig_a1, orig_b1
    a2_safe, b2_safe = orig_a2, orig_b2

    # Por defecto, los RUTs ajustados quedan igual que los originales
    rut1_adjusted = rut1_str
    rut2_adjusted = rut2_str

    # Función interna: probar colisión si e2 tuviera estos 8 dígitos candidatos
    def collision_with_candidate_e2(candidate_digits2: list[int]) -> bool:
        tmp = EllipseGenerator(format_rut_from_digits(candidate_digits2, ""), case_type=case_type)
        tmp.h, tmp.k = h2, k2
        tmp.orientation = orientation2
        if case_type == "1":
            tmp.a = candidate_digits2[2] + candidate_digits2[3]
            tmp.b = candidate_digits2[4] + candidate_digits2[5]
        else:  # case_type == "2"
            tmp.a = candidate_digits2[5] + candidate_digits2[6]
            tmp.b = candidate_digits2[7] + candidate_digits2[2]
        # Si alguno < 1, descartamos
        if tmp.a < 1 or tmp.b < 1:
            return True
        return CollisionDetector.detect_collision(e1, tmp)

    # Función interna: probar colisión si e1 tuviera estos 8 dígitos candidatos
    def collision_with_candidate_e1(candidate_digits1: list[int]) -> bool:
        tmp = EllipseGenerator(format_rut_from_digits(candidate_digits1, ""), case_type=case_type)
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

    # --- 2) Intentar ajustar SOLO e2 ---
    found2 = False
    new_digits2 = digits2.copy()

    if case_type == "1":
        d3_o, d4_o, d5_o, d6_o = digits2[2], digits2[3], digits2[4], digits2[5]
        for reduccion in range(1, orig_a2 + orig_b2 + 1):
            for new_a2 in range(orig_a2 - 1, 0, -1):
                redA = orig_a2 - new_a2
                redB = reduccion - redA
                new_b2 = orig_b2 - redB
                if new_b2 < 1 or new_b2 > orig_b2:
                    continue

                # Generar candidatos (d3',d4') s/t sumen new_a2
                paresA = [(abs(i - d3_o), i, new_a2 - i)
                          for i in range(10)
                          if 0 <= new_a2 - i <= 9]
                if not paresA:
                    continue
                paresA.sort(key=lambda x: (x[0], -x[1]))

                # Generar candidatos (d5',d6') s/t sumen new_b2
                paresB = [(abs(i - d5_o), i, new_b2 - i)
                          for i in range(10)
                          if 0 <= new_b2 - i <= 9]
                if not paresB:
                    continue
                paresB.sort(key=lambda x: (x[0], -x[1]))

                for _, c3, c4 in paresA:
                    for _, c5, c6 in paresB:
                        candidate = digits2.copy()
                        candidate[2], candidate[3] = c3, c4
                        candidate[4], candidate[5] = c5, c6
                        if not collision_with_candidate_e2(candidate):
                            new_digits2 = candidate.copy()
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
            # Fallback: reducir el semieje horizontal en 1
            nueva_a2 = max(1, orig_a2 - 1)
            pareja = next(((i, nueva_a2 - i)
                           for i in range(9, -1, -1)
                           if 0 <= nueva_a2 - i <= 9), None)
            if pareja and orig_b2 >= 1:
                tmp_digits2 = digits2.copy()
                tmp_digits2[2], tmp_digits2[3] = pareja
                new_digits2 = tmp_digits2.copy()
                a2_safe, b2_safe = nueva_a2, orig_b2

    else:  # case_type == "2"
        d6_o, d7_o, d8_o, d3_o = digits2[5], digits2[6], digits2[7], digits2[2]
        for reduccion in range(1, orig_a2 + orig_b2 + 1):
            for new_a2 in range(orig_a2 - 1, 0, -1):
                redA = orig_a2 - new_a2
                redB = reduccion - redA
                new_b2 = orig_b2 - redB
                if new_b2 < 1 or new_b2 > orig_b2:
                    continue

                paresA = [(abs(i - d6_o), i, new_a2 - i)
                          for i in range(10)
                          if 0 <= new_a2 - i <= 9]
                if not paresA:
                    continue
                paresA.sort(key=lambda x: (x[0], -x[1]))

                paresB = [(abs(i - d8_o), i, new_b2 - i)
                          for i in range(10)
                          if 0 <= new_b2 - i <= 9]
                if not paresB:
                    continue
                paresB.sort(key=lambda x: (x[0], -x[1]))

                for _, c6, c7 in paresA:
                    for _, c8, c3b in paresB:
                        candidate = digits2.copy()
                        candidate[5], candidate[6] = c6, c7
                        candidate[7], candidate[2] = c8, c3b
                        if not collision_with_candidate_e2(candidate):
                            new_digits2 = candidate.copy()
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
            # Fallback: reducir el semieje horizontal en 1
            nueva_a2 = max(1, orig_a2 - 1)
            pareja = next(((i, nueva_a2 - i)
                           for i in range(9, -1, -1)
                           if 0 <= nueva_a2 - i <= 9), None)
            if pareja and orig_b2 >= 1:
                tmp_digits2 = digits2.copy()
                tmp_digits2[5], tmp_digits2[6] = pareja
                new_digits2 = tmp_digits2.copy()
                a2_safe, b2_safe = nueva_a2, orig_b2

    # Reconstruir candidate e2 con el posible ajuste
    new_rut2 = format_rut_from_digits(new_digits2, rut2_str.split('-')[-1] if '-' in rut2_str else "")
    e2_candidate = EllipseGenerator(new_rut2, case_type=case_type)
    e2_candidate.h, e2_candidate.k = h2, k2
    e2_candidate.orientation = orientation2
    e2_candidate.a, e2_candidate.b = a2_safe, b2_safe

    # --- 3) Si e1 vs e2_candidate aún colisionan, ajustar sólo e1 ---
    if CollisionDetector.detect_collision(e1, e2_candidate):
        found1 = False
        new_digits1 = digits1.copy()

        if case_type == "1":
            d3o1, d4o1, d5o1, d6o1 = digits1[2], digits1[3], digits1[4], digits1[5]
            for reduccion in range(1, orig_a1 + orig_b1 + 1):
                for new_a1 in range(orig_a1 - 1, 0, -1):
                    redA = orig_a1 - new_a1
                    redB = reduccion - redA
                    new_b1 = orig_b1 - redB
                    if new_b1 < 1 or new_b1 > orig_b1:
                        continue

                    paresA = [(abs(i - d3o1), i, new_a1 - i)
                              for i in range(10)
                              if 0 <= new_a1 - i <= 9]
                    if not paresA:
                        continue
                    paresA.sort(key=lambda x: (x[0], -x[1]))

                    paresB = [(abs(i - d5o1), i, new_b1 - i)
                              for i in range(10)
                              if 0 <= new_b1 - i <= 9]
                    if not paresB:
                        continue
                    paresB.sort(key=lambda x: (x[0], -x[1]))

                    for _, c3, c4 in paresA:
                        for _, c5, c6 in paresB:
                            candidate = digits1.copy()
                            candidate[2], candidate[3] = c3, c4
                            candidate[4], candidate[5] = c5, c6
                            if not collision_with_candidate_e1(candidate):
                                new_digits1 = candidate.copy()
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
                pareja = next(((i, nueva_a1 - i)
                               for i in range(9, -1, -1)
                               if 0 <= nueva_a1 - i <= 9), None)
                if pareja and orig_b1 >= 1:
                    tmp_digits1 = digits1.copy()
                    tmp_digits1[2], tmp_digits1[3] = pareja
                    new_digits1 = tmp_digits1.copy()
                    a1_safe, b1_safe = nueva_a1, orig_b1

        else:  # case_type == "2"
            d6o1, d7o1, d8o1, d3o1 = digits1[5], digits1[6], digits1[7], digits1[2]
            for reduccion in range(1, orig_a1 + orig_b1 + 1):
                for new_a1 in range(orig_a1 - 1, 0, -1):
                    redA = orig_a1 - new_a1
                    redB = reduccion - redA
                    new_b1 = orig_b1 - redB
                    if new_b1 < 1 or new_b1 > orig_b1:
                        continue

                    paresA = [(abs(i - d6o1), i, new_a1 - i)
                              for i in range(10)
                              if 0 <= new_a1 - i <= 9]
                    if not paresA:
                        continue
                    paresA.sort(key=lambda x: (x[0], -x[1]))

                    paresB = [(abs(i - d8o1), i, new_b1 - i)
                              for i in range(10)
                              if 0 <= new_b1 - i <= 9]
                    if not paresB:
                        continue
                    paresB.sort(key=lambda x: (x[0], -x[1]))

                    for _, c6, c7 in paresA:
                        for _, c8, c3b in paresB:
                            candidate = digits1.copy()
                            candidate[5], candidate[6] = c6, c7
                            candidate[7], candidate[2] = c8, c3b
                            if not collision_with_candidate_e1(candidate):
                                new_digits1 = candidate.copy()
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
                pareja = next(((i, nueva_a1 - i)
                               for i in range(9, -1, -1)
                               if 0 <= nueva_a1 - i <= 9), None)
                if pareja and orig_b1 >= 1:
                    tmp_digits1 = digits1.copy()
                    tmp_digits1[5], tmp_digits1[6] = pareja
                    new_digits1 = tmp_digits1.copy()
                    a1_safe, b1_safe = nueva_a1, orig_b1

        new_rut1 = format_rut_from_digits(new_digits1, rut1_str.split('-')[-1] if '-' in rut1_str else "")
        e1_candidate = EllipseGenerator(new_rut1, case_type=case_type)
        e1_candidate.h, e1_candidate.k = h1, k1
        e1_candidate.orientation = orientation1
        e1_candidate.a, e1_candidate.b = a1_safe, b1_safe

        # --- 4) Si aún colisionan con este ajuste de e1, reducir ambos simultáneamente ---
        if CollisionDetector.detect_collision(e1_candidate, e2):
            nueva_a2 = max(1, orig_a2 - 1)
            nueva_a1 = max(1, orig_a1 - 1)

            # Ajustar dígitos e2 → nueva_a2
            tmp_digits2 = digits2.copy()
            pareja2 = next(((i, nueva_a2 - i)
                            for i in range(9, -1, -1)
                            if 0 <= nueva_a2 - i <= 9), None)
            if pareja2:
                if case_type == "1":
                    tmp_digits2[2], tmp_digits2[3] = pareja2
                else:
                    tmp_digits2[5], tmp_digits2[6] = pareja2

            # Ajustar dígitos e1 → nueva_a1
            tmp_digits1 = digits1.copy()
            pareja1 = next(((i, nueva_a1 - i)
                            for i in range(9, -1, -1)
                            if 0 <= nueva_a1 - i <= 9), None)
            if pareja1:
                if case_type == "1":
                    tmp_digits1[2], tmp_digits1[3] = pareja1
                else:
                    tmp_digits1[5], tmp_digits1[6] = pareja1

            both_rut2 = format_rut_from_digits(tmp_digits2, rut2_str.split('-')[-1] if '-' in rut2_str else "")
            both_rut1 = format_rut_from_digits(tmp_digits1, rut1_str.split('-')[-1] if '-' in rut1_str else "")

            e2_both = EllipseGenerator(both_rut2, case_type=case_type)
            e2_both.h, e2_both.k = h2, k2
            e2_both.orientation = orientation2
            e2_both.a, e2_both.b = nueva_a2, orig_b2

            e1_both = EllipseGenerator(both_rut1, case_type=case_type)
            e1_both.h, e1_both.k = h1, k1
            e1_both.orientation = orientation1
            e1_both.a, e1_both.b = nueva_a1, orig_b1

            if not CollisionDetector.detect_collision(e1_both, e2_both):
                return e1_both, e2_both, both_rut1, both_rut2, nueva_a1, orig_b1, nueva_a2, orig_b2

            # Si aún colisionan, devolvemos la mejor solución previa (ajuste solo e2)
            return e1, e2_candidate, rut1_str, format_rut_from_digits(new_digits2, rut2_str.split('-')[-1] if '-' in rut2_str else ""), \
                   orig_a1, orig_b1, a2_safe, b2_safe

        # Ajuste exitoso solo e1
        return e1_candidate, e2, new_rut1, rut2_str, a1_safe, b1_safe, orig_a2, orig_b2

    else:
        # Ajuste exitoso sólo en e2
        return e1, e2_candidate, rut1_str, format_rut_from_digits(new_digits2, rut2_str.split('-')[-1] if '-' in rut2_str else ""), \
               orig_a1, orig_b1, a2_safe, b2_safe
