from utils.config import SCREEN_WIDTH, SCREEN_HEIGHT


class FlatTerrain:
    DEFAULT_GROUND_HEIGHT = 180

    def __init__(self):
        self.ground_height = min(self.DEFAULT_GROUND_HEIGHT, max(0, SCREEN_HEIGHT - 5))

    def get_ground_y(self):
        if SCREEN_HEIGHT <= 0:
            return 0.0
        max_ground_height = max(0.0, float(SCREEN_HEIGHT - 5))
        ground_height_from_bottom = min(max(float(self.ground_height), 0.0), max_ground_height)
        return float(SCREEN_HEIGHT) - ground_height_from_bottom

    # get points for drawing
    def get_points(self):
        y = int(self.get_ground_y())
        return [(0, y), (SCREEN_WIDTH - 1, y)]
