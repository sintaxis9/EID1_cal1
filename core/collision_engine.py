import numpy as np
from shapely.geometry import Polygon

class CollisionDetector:
    @staticmethod
    def detect_collision(ellipse1, ellipse2):
        x1, y1, _ = ellipse1.generate_points(num_points=200)
        poly1 = Polygon(np.column_stack((x1, y1)))

        x2, y2, _ = ellipse2.generate_points(num_points=200)
        poly2 = Polygon(np.column_stack((x2, y2)))

        boundary1 = poly1.boundary
        boundary2 = poly2.boundary

        return boundary1.intersects(boundary2)

    @staticmethod
    def collision_risk_level(ellipse1, ellipse2):
        dx = ellipse1.h - ellipse2.h
        dy = ellipse1.k - ellipse2.k
        distance = np.sqrt(dx * dx + dy * dy)

        min_safe = 0.5 * (ellipse1.a + ellipse1.b + ellipse2.a + ellipse2.b)
        nivel = 1 - (distance / min_safe)
        return max(0.0, min(1.0, nivel))
