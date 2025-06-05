from core.ellipse_model import EllipseGenerator

class ScenarioManager:


    def generate_ellipses(self, rut1, rut2, case_type="1"):
        e1 = EllipseGenerator(rut1, case_type=case_type)
        e2 = EllipseGenerator(rut2, case_type=case_type)
        return [e1, e2]
