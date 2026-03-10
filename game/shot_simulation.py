import math
import numpy as np

from utils.config import DT, GRAVITY, PIXELS_PER_METER, MAX_POWER
from utils import globals


class Scaler:
    def __init__(self, val_min, val_max):
        self.val_min = val_min
        self.val_max = val_max

    def normalized(self, val):
        return (val - self.val_min) / (self.val_max - self.val_min)

    def original(self, val):
        return self.val_min + val * (self.val_max - self.val_min)


# angle 0-90
# power 0 - MAX_POWER
scaler = Scaler(np.array([0.0, 0.0]), np.array([90.0, float(MAX_POWER)]))


def simulate_shot(angle_deg=None, power=None, record_path=False):
    """
    Simulacija projektila
    """
    x, y = globals.shooter.get_barrel_end()

    if angle_deg is None:
        angle_deg = globals.shooter.angle_deg
    if power is None:
        power = globals.shooter.power

    angle_rad = math.radians(angle_deg)
    vx = math.cos(angle_rad) * power
    vy = -math.sin(angle_rad) * power
    path = [] if record_path else None

    wind_dt = globals.wind * DT
    gravity_dt = GRAVITY * DT
    pixels_per_m_dt = PIXELS_PER_METER * DT

    for _ in range(20000):
        vx += wind_dt
        vy += gravity_dt
        x += vx * pixels_per_m_dt
        y += vy * pixels_per_m_dt

        if record_path:
            path.append((x, y))

        if y >= globals.terrain.get_ground_y():
            break

    dist_m = abs(x - globals.target.x) / PIXELS_PER_METER
    return {
        "dist_m": dist_m,
        "angle": angle_deg,
        "power": power,
        "path": path if record_path else [],
    }
