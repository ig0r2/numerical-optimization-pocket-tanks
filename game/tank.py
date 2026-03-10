import math
import pygame

from utils import globals
from utils.config import PIXELS_PER_METER

TANK_HEIGHT = 20
TURRET_LENGTH = 12


class Tank:
    def __init__(self, x, orientation=1, angle_deg=None, power=None, image=None):
        self.x = int(x)
        self.image = image
        self.orientation = orientation
        if angle_deg is not None:
            self.angle_deg = angle_deg
        else:
            self.angle_deg = 80.0 if orientation == 1 else 135.0
        if power is not None:
            self.power = power
        else:
            self.power = PIXELS_PER_METER / 2
        self.alive = True
        self.y = None
        self.update_y()

    def reset(self):
        self.angle_deg = 36.0 if self.orientation == 1 else 135.0
        self.power = PIXELS_PER_METER / 2
        self.alive = True
        self.update_y()

    def update_y(self):
        self.y = globals.terrain.get_ground_y() - TANK_HEIGHT // 4

    def draw(self, surf):
        # draw tank image
        if self.image:
            rect = self.image.get_rect(center=(self.x, self.y))
            surf.blit(self.image, rect)
        # turret
        angle_rad = math.radians(self.angle_deg)
        tx = self.x + math.cos(angle_rad) * TURRET_LENGTH
        ty = self.y - math.sin(angle_rad) * TURRET_LENGTH
        pygame.draw.line(surf, pygame.Color('black'), (self.x, self.y), (tx, ty), 3)

    def get_barrel_end(self):
        angle_rad = math.radians(self.angle_deg)
        tx = self.x + math.cos(angle_rad) * (TURRET_LENGTH + 8)
        ty = self.y - math.sin(angle_rad) * (TURRET_LENGTH + 8)
        return tx, ty
