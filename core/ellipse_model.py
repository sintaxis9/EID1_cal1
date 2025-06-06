import numpy as np

class EllipseGenerator:
    def __init__(self, rut, case_type="1"):
        self.rut = rut
        self.case_type = case_type
        self.digits = self._parse_rut()       
        self.h, self.k = self._calculate_center()
        self.a, self.b = self._calculate_axes()
        self.orientation = self._determine_orientation()

    def _parse_rut(self):
        clean_rut = ''.join(filter(str.isdigit, self.rut))
        if len(clean_rut) < 8:
            raise ValueError("El RUT debe contener al menos 8 dígitos numéricos.")
        return [int(d) for d in clean_rut[:8]]

    def _calculate_center(self):
        return self.digits[0], self.digits[1]

    def _calculate_axes(self):
        d = self.digits
        if self.case_type == "1":
            a = d[2] + d[3]
            b = d[4] + d[5]
        else:
            a = d[5] + d[6]
            b = d[7] + d[2]
        return a, b

    def _determine_orientation(self):
        d = self.digits
        if self.case_type == "1":
            return "vertical" if (d[7] % 2 != 0) else "horizontal"
        else:
            return "vertical" if (d[3] % 2 != 0) else "horizontal"

    def canonical_equation(self):
        h, k, a, b = self.h, self.k, self.a, self.b
        if self.orientation == "horizontal":
            return (
                f"\\frac{{(x - {h})^2}}{{{a**2}}} + "
                f"\\frac{{(y - {k})^2}}{{{b**2}}} = 1"
            )
        else:
            return (
                f"\\frac{{(x - {h})^2}}{{{b**2}}} + "
                f"\\frac{{(y - {k})^2}}{{{a**2}}} = 1"
            )

    def general_equation(self):
        h, k, a, b = self.h, self.k, self.a, self.b
        if self.orientation == "horizontal":
            A = b**2
            B = a**2
            C = -2 * b**2 * h
            D = -2 * a**2 * k
            F = b**2 * h**2 + a**2 * k**2 - a**2 * b**2
        else:
            A = a**2
            B = b**2
            C = -2 * a**2 * h
            D = -2 * b**2 * k
            F = a**2 * h**2 + b**2 * k**2 - a**2 * b**2
        return A, B, C, D, F

    def generate_points(self, height=0, num_points=100):
        theta = np.linspace(0, 2 * np.pi, num_points)
        if self.orientation == "horizontal":
            x = self.h + self.a * np.cos(theta)
            y = self.k + self.b * np.sin(theta)
        else:
            x = self.h + self.b * np.cos(theta)
            y = self.k + self.a * np.sin(theta)
        z = np.full_like(x, height)
        return x, y, z
