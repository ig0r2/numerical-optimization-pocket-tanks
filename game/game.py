import numpy as np
import pygame
import random

from utils.config import FPS, SCREEN_WIDTH, SCREEN_HEIGHT
from utils import globals
from utils.config import ANIMATION_SPEED
from .shot_simulation import simulate_shot, scaler
from .hud import HUD
from .terrain import FlatTerrain
from .tank import Tank


def game_loop(replay_result):
    if not pygame.get_init(): pygame.init()
    globals.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))

    pygame.display.set_caption("PocketTanks Optimizacija")
    clock = pygame.time.Clock()

    game = Game(replay_result)

    is_paused = False
    is_running = True
    animation_done = True

    while is_running:
        clock.tick(FPS)
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                is_running = False
                break

            if event.type != pygame.KEYDOWN:
                continue

            if event.key == pygame.K_ESCAPE:
                is_running = False
            elif event.key == pygame.K_r:
                game.reset()
                is_paused = False

        if not is_running:
            break

        if not is_paused and animation_done:
            is_paused = game.algorithm_iteration()

        animation_done = game.draw()
        pygame.display.flip()

    pygame.display.quit()
    globals.screen = None


def apply_scenario():
    random.seed(33)
    np.random.seed(33)

    globals.terrain = FlatTerrain()

    shooter_x = 110
    globals.shooter = Tank(x=shooter_x, angle_deg=globals.initial_angle_deg, power=globals.initial_power)
    globals.shooter.update_y()

    target_x = int(SCREEN_WIDTH * 0.8)
    globals.target = Tank(x=target_x, orientation=-1)
    globals.target.update_y()


class Game:
    def __init__(self, replay_result):
        self.replay_result = replay_result

        self.hud = None
        self.last_shot_result = None
        self.animation_index = 0

        self._replay_shots = []
        self._replay_index = 0

        self.hud = HUD()
        self.reset()

    def _setup_replay_world(self):
        apply_scenario()

        globals.shooter.image = pygame.image.load("game/assets/tank1.png").convert_alpha()
        globals.target.image = pygame.image.load("game/assets/tank2.png").convert_alpha()

        self._replay_shots = self._build_replay_shots()

    def _build_replay_shots(self):
        if not self.replay_result:
            return []

        history = self.replay_result.get("history", [])
        shots = []
        for point in history:
            if int(point.get("iteration", 0)) <= 0:
                continue
            x = np.asarray(point.get("x", [0.0, 0.0]), dtype=np.float64)
            angle_deg, power = scaler.original(x)

            shot = simulate_shot(angle_deg, power, record_path=True)
            shot["dist_m"] = point.get("fx")

            shots.append(shot)

        return shots

    def reset(self):
        self._setup_replay_world()

        self._replay_index = 0
        self.animation_index = 0
        self.last_shot_result = None

    def algorithm_iteration(self):
        if self._replay_index >= len(self._replay_shots):
            return True

        shot = self._replay_shots[self._replay_index]
        globals.shooter.angle_deg = shot["angle"]
        globals.shooter.power = shot["power"]

        self.last_shot_result = shot
        self.animation_index = 0
        self._replay_index += 1

        return self._replay_index >= len(self._replay_shots)

    def draw(self):
        globals.screen.fill(pygame.Color("skyblue"))

        terrain_points = globals.terrain.get_points()
        poly = terrain_points + [(SCREEN_WIDTH - 1, SCREEN_HEIGHT), (0, SCREEN_HEIGHT)]
        pygame.draw.polygon(globals.screen, pygame.Color("forestgreen"), poly)
        pygame.draw.lines(globals.screen, pygame.Color("black"), False, terrain_points, 1)

        if self.last_shot_result is not None:
            for p in self.last_shot_result["path"][: self.animation_index]:
                pygame.draw.circle(globals.screen, pygame.Color("black"), (int(p[0]), int(p[1])), 1)
            self.animation_index += ANIMATION_SPEED

        animation_done = self.last_shot_result is None or self.animation_index >= len(self.last_shot_result["path"])

        if self.last_shot_result is not None and animation_done:
            p = self.last_shot_result["path"][-1]
            pygame.draw.circle(globals.screen, pygame.Color("black"), (int(p[0]), int(p[1])), 5)

        globals.shooter.draw(globals.screen)
        if globals.target.alive or not animation_done:
            globals.target.draw(globals.screen)
        elif animation_done:
            pygame.draw.circle(globals.screen, pygame.Color("red"), (globals.target.x, globals.target.y), 12)
            pygame.draw.circle(globals.screen, pygame.Color("orange"), (globals.target.x, globals.target.y), 10)

        self.hud.draw(self.last_shot_result, self._replay_index, len(self._replay_shots))

        return animation_done
