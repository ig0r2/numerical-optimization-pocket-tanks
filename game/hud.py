import pygame

from utils import globals
from utils.config import MAX_POWER, SCREEN_WIDTH, SCREEN_HEIGHT


class Theme:
    def __init__(self, screen_height):
        self.bg_dark = (30, 41, 59)
        self.bg_darker = (15, 23, 42)
        self.bg_light = (51, 65, 85)
        self.cyan = (34, 211, 238)
        self.orange = (251, 146, 60)
        self.green = (34, 197, 94)
        self.purple = (168, 85, 247)
        self.blue = (59, 130, 246)
        self.yellow = (234, 179, 8)
        self.white = (255, 255, 255)
        self.gray = (148, 163, 184)
        self.red = (239, 68, 68)

        base_size = int(screen_height / 90)
        self.medium_font = pygame.font.SysFont('Arial', int(base_size * 2.0), bold=True)
        self.large_font = pygame.font.SysFont('Arial', int(base_size * 2.5), bold=True)


class RoundedRectMixin:
    def __init__(self, rect, theme):
        self.rect = rect
        self.theme = theme

    def draw_bg(self, surface):
        pygame.draw.rect(surface, self.theme.bg_darker, self.rect, border_radius=10)


class AngleDisplay(RoundedRectMixin):
    def __init__(self, rect, theme):
        super().__init__(rect, theme)

    def draw(self, surface, angle):
        self.draw_bg(surface)
        # Title and value
        title = self.theme.medium_font.render("UGAO", True, self.theme.gray)
        value = self.theme.large_font.render(f"{angle:.2f}°", True, self.theme.cyan)
        surface.blit(title, (self.rect.x + 15, self.rect.y + 15))
        surface.blit(value, (self.rect.right - value.get_width() - 15, self.rect.y + 12))


class PowerDisplay(RoundedRectMixin):
    def __init__(self, rect, theme):
        super().__init__(rect, theme)

    def draw(self, surface, power, max_power=MAX_POWER):
        self.draw_bg(surface)
        # Title and value
        title = self.theme.medium_font.render("SNAGA", True, self.theme.gray)
        value = self.theme.large_font.render(f"{power:.2f} m/s", True, self.theme.orange)
        surface.blit(title, (self.rect.x + 15, self.rect.y + 15))
        surface.blit(value, (self.rect.right - value.get_width() - 15, self.rect.y + 12))
        # Power bar
        bar_width = self.rect.width - 30
        bar_x = self.rect.x + 15
        bar_y = self.rect.y + 50
        filled_width = (power / max_power) * bar_width
        pygame.draw.rect(surface, self.theme.bg_light, (bar_x, bar_y, bar_width, 8), border_radius=2)
        pygame.draw.rect(surface, self.theme.orange, (bar_x, bar_y, filled_width, 8), border_radius=2)


class WindIndicator(RoundedRectMixin):
    def __init__(self, rect, theme):
        super().__init__(rect, theme)

    def draw(self, surface, wind, max_wind=6.0):
        self.draw_bg(surface)
        # Title
        title = self.theme.medium_font.render("VETAR", True, self.theme.gray)
        surface.blit(title, (self.rect.x + 15, self.rect.y + 12))
        # Arrow indicator
        arrow_size = 8
        arrow_y = self.rect.y + 18
        arrow_x = self.rect.x + 15 + title.get_width() + 10
        if wind < 0:
            pygame.draw.polygon(surface, self.theme.blue, [
                (arrow_x + arrow_size, arrow_y), (arrow_x, arrow_y + arrow_size // 2),
                (arrow_x + arrow_size, arrow_y + arrow_size)
            ])
        else:
            pygame.draw.polygon(surface, self.theme.red, [
                (arrow_x, arrow_y), (arrow_x + arrow_size, arrow_y + arrow_size // 2), (arrow_x, arrow_y + arrow_size)
            ])
        # Wind value
        wind_text = f"{wind:+.2f} m/s²"
        value = self.theme.large_font.render(wind_text, True, self.theme.white)
        surface.blit(value, (self.rect.right - value.get_width() - 15, self.rect.y + 12))
        # Wind bar
        bar_width_max = self.rect.width - 30
        bar_height = 8
        bar_x = self.rect.x + 15
        bar_y = self.rect.y + 50
        pygame.draw.rect(surface, self.theme.bg_light, (bar_x, bar_y, bar_width_max, bar_height), border_radius=2)

        wind_ratio = min(abs(wind) / max_wind, 1.0)
        active_width = int(wind_ratio * bar_width_max)
        wind_color = self.theme.blue if wind < 0 else self.theme.red
        if wind < 0:  # Wind to left
            pygame.draw.rect(surface, wind_color,
                             (bar_x + bar_width_max - active_width, bar_y, active_width, bar_height), border_radius=2)
        else:  # Wind to right
            pygame.draw.rect(surface, wind_color, (bar_x, bar_y, active_width, bar_height), border_radius=2)


class LastShotDisplay(RoundedRectMixin):
    def __init__(self, rect, theme):
        super().__init__(rect, theme)
        self.distance = 0
        self.iteration = 0
        self.total_iterations = 0

    def set_data(self, distance, iteration, total_iterations):
        self.distance = distance
        self.iteration = iteration
        self.total_iterations = total_iterations

    def draw(self, surface):
        self.draw_bg(surface)
        iter_label = self.theme.medium_font.render("Korak", True, self.theme.gray)
        iter_value = self.theme.large_font.render(f"{self.iteration}/{self.total_iterations}", True, self.theme.yellow)
        surface.blit(iter_label, (self.rect.x + 15, self.rect.y + 10))
        surface.blit(iter_value, (self.rect.right - iter_value.get_width() - 15, self.rect.y + 6))

        dist_label = self.theme.medium_font.render("Razdaljina", True, self.theme.gray)
        dist_value = self.theme.large_font.render(f"{self.distance:.4f} m", True, self.theme.yellow)
        surface.blit(dist_label, (self.rect.x + 15, self.rect.y + 42))
        surface.blit(dist_value, (self.rect.right - dist_value.get_width() - 15, self.rect.y + 36))


class ControlsHint(RoundedRectMixin):
    def __init__(self, rect, theme):
        super().__init__(rect, theme)
        text = "R: Reset                        ESC: Izlaz"
        self.hint_surface = self.theme.medium_font.render(text, True, self.theme.white)
        # Create a semi-transparent background surface
        self.bg_surface = pygame.Surface((self.rect.width, self.rect.height), pygame.SRCALPHA)
        pygame.draw.rect(self.bg_surface, (*self.theme.bg_dark, 180), self.bg_surface.get_rect(), border_radius=8)

    def draw(self, surface):
        surface.blit(self.bg_surface, self.rect.topleft)
        # Blit the pre-rendered text
        text_x = self.rect.centerx - self.hint_surface.get_width() // 2
        text_y = self.rect.y + (self.rect.height - self.hint_surface.get_height()) // 2
        surface.blit(self.hint_surface, (text_x, text_y))


class HUD:
    def __init__(self):
        self.width = SCREEN_WIDTH
        self.height = SCREEN_HEIGHT
        self.theme = Theme(self.height)

        self.angle_display = None
        self.power_display = None
        self.wind_display = None
        self.last_shot_display = None
        self.controls_hint = None
        self.status_message = None

        margin = 10
        panel_y = margin
        panel_height = 80

        angle_width = min(self.width // 4, 200)
        power_width = min(self.width // 4, 300)
        wind_width = min(self.width // 4, 250)
        last_shot_width = min(self.width // 4, 300)

        angle_rect = pygame.Rect(margin, panel_y, angle_width, panel_height)
        power_rect = pygame.Rect(angle_rect.right + margin, panel_y, power_width, panel_height)
        wind_rect = pygame.Rect(power_rect.right + margin, panel_y, wind_width, panel_height)
        last_shot_rect = pygame.Rect(self.width - margin - last_shot_width, panel_y, last_shot_width, panel_height)

        self.angle_display = AngleDisplay(angle_rect, self.theme)
        self.power_display = PowerDisplay(power_rect, self.theme)
        self.wind_display = WindIndicator(wind_rect, self.theme)
        self.last_shot_display = LastShotDisplay(last_shot_rect, self.theme)

        hint_height = 40
        hint_rect = pygame.Rect(margin, self.height - hint_height - 7, self.width - (margin * 2), hint_height)
        self.controls_hint = ControlsHint(hint_rect, self.theme)

    def draw(self, last_shot_result=None, iterations=0, total_iterations=0):
        surface = globals.screen
        self.angle_display.draw(surface, globals.shooter.angle_deg)
        self.power_display.draw(surface, globals.shooter.power)
        self.wind_display.draw(surface, globals.wind)
        distance = last_shot_result.get("dist_m", 0) if last_shot_result else 0
        self.last_shot_display.set_data(distance, iterations, total_iterations)
        self.last_shot_display.draw(surface)
        self.controls_hint.draw(surface)
