from tkinter import ttk
import numpy as np
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from utils import globals
from game import scaler
from utils.config import DT, GRAVITY, PIXELS_PER_METER


def _compute_function_grid(angle_grid_norm, power_grid_norm):
    """
    Radi isto sto i sumulate_shot() funckija samo sto je vektorizovano za brzo racunanje tacaka za plot
    """
    params_norm = np.column_stack((angle_grid_norm.ravel(), power_grid_norm.ravel()))
    params = scaler.original(params_norm)
    angles_deg = params[:, 0]
    powers = params[:, 1]

    shooter_x, shooter_y = globals.shooter.get_barrel_end()
    x = np.full(angles_deg.shape, shooter_x, dtype=np.float64)
    y = np.full(angles_deg.shape, shooter_y, dtype=np.float64)

    angles_rad = np.deg2rad(angles_deg)
    vx = np.cos(angles_rad) * powers
    vy = -np.sin(angles_rad) * powers

    ground_y = globals.terrain.get_ground_y()
    target_x = float(globals.target.x)

    wind_step = globals.wind * DT
    gravity_step = GRAVITY * DT
    dt_pixels = DT * PIXELS_PER_METER

    active = np.ones(angles_deg.shape, dtype=bool)
    distances = np.empty_like(angles_deg)

    for _ in range(20000):
        if not np.any(active):
            break

        active_idx = np.nonzero(active)[0]  # mask

        vx[active_idx] += wind_step
        vy[active_idx] += gravity_step
        x[active_idx] += vx[active_idx] * dt_pixels
        y[active_idx] += vy[active_idx] * dt_pixels

        collided = y[active_idx] >= ground_y

        if np.any(collided):
            collided_idx = active_idx[collided]
            distances[collided_idx] = np.abs(x[collided_idx] - target_x) / PIXELS_PER_METER
            active[collided_idx] = False

    if np.any(active):
        distances[active] = np.abs(x[active] - target_x) / PIXELS_PER_METER

    return distances.reshape(angle_grid_norm.shape)


def create_landscape_grid(resolution=200):
    angle_axis = np.linspace(0.0, 1.0, resolution)
    power_axis = np.linspace(0.0, 1.0, resolution)
    angle_grid, power_grid = np.meshgrid(angle_axis, power_axis)
    value_grid = _compute_function_grid(angle_grid, power_grid)
    return angle_grid, power_grid, value_grid


class HeatmapPlot:
    def __init__(self, parent, figure_size=(8.8, 4.8), dpi=100, colorbar_label="Distanca [m] - f(x1, x2)",
                 x_label="Ugao (x1)", y_label="Snaga (x2)"):
        self.frame = ttk.Frame(parent)
        self.frame.rowconfigure(0, weight=1)
        self.frame.rowconfigure(1, weight=0)
        self.frame.columnconfigure(0, weight=1)

        self.figure = Figure(figsize=figure_size, dpi=dpi)
        self.canvas = FigureCanvasTkAgg(self.figure, master=self.frame)
        self.canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        self.toolbar = NavigationToolbar2Tk(self.canvas, self.frame, pack_toolbar=False)
        self.toolbar.update()
        self.toolbar.grid(row=1, column=0, sticky="w", pady=(6, 0))

        self.colorbar_label = colorbar_label
        self.x_label = x_label
        self.y_label = y_label
        self._landscape_grid_cache = None

    def create_grid(self, force=False):
        if self._landscape_grid_cache is None or force:
            self._landscape_grid_cache = create_landscape_grid()
        return self._landscape_grid_cache

    def _draw_landscape(self, ax):
        heatmap = ax.pcolormesh(*self.create_grid(), cmap="coolwarm", shading="auto")
        self.figure.colorbar(heatmap, ax=ax, label=self.colorbar_label)

    @staticmethod
    def _plot_marker(ax, point, marker, size, *, color=None, label=None):
        ax.scatter(point[0], point[1], marker=marker, s=size, edgecolors="black", linewidths=0.4,
                   **({"color": color} if color is not None else {}), **({"label": label} if label is not None else {}))

    def _plot_path(self, ax, points, *, line_color=None, line_label=None, line_alpha=None, start_color=None,
                   end_color=None, include_point_labels=False):
        ax.plot(points[:, 0], points[:, 1], linewidth=2.0, marker="o", markersize=3.2,
                **({"color": line_color} if line_color is not None else {}),
                **({"label": line_label} if line_label is not None else {}),
                **({"alpha": line_alpha} if line_alpha is not None else {}))
        self._plot_marker(ax, points[0], "^", 65, color=start_color, label="Pocetak" if include_point_labels else None)
        self._plot_marker(ax, points[-1], "*", 120, color=end_color, label="Kraj" if include_point_labels else None)

    @staticmethod
    def _history_points(history):
        if not history:
            return None
        points = np.asarray([point.get("x", [0.0, 0.0]) for point in history], dtype=np.float64)
        if points.ndim != 2 or points.shape[0] == 0 or points.shape[1] != 2:
            return None
        return points

    def _finalize_axes(self, ax, legend_fontsize=9):
        handles, _ = ax.get_legend_handles_labels()
        if handles:
            ax.legend(loc="upper right", fontsize=legend_fontsize)
        ax.set_xlabel(self.x_label)
        ax.set_ylabel(self.y_label)
        ax.set_xlim(0.0, 1.0)
        ax.set_ylim(0.0, 1.0)
        ax.grid(alpha=0.15)

        self.figure.tight_layout()
        self.canvas.draw_idle()

    def draw(self, result=None):
        result = result or {}

        self.figure.clear()
        ax = self.figure.add_subplot(1, 1, 1)
        self._draw_landscape(ax)

        history = result.get("history", [])
        points = self._history_points(history)
        if points is not None:
            self._plot_path(ax=ax, points=points, line_color="#111827", line_label=result.get("name", "Algoritam"),
                            start_color="#16A34A", end_color="#DC2626", include_point_labels=True, )
        else:
            start_point = scaler.normalized(
                np.array([globals.shooter.angle_deg, globals.shooter.power], dtype=np.float64))
            self._plot_marker(ax, start_point, "^", 65, color="#16A34A", label="Pocetak")

        self._finalize_axes(ax)

    def draw_many(self, results, *, selected_names=None, color_by_name=None):
        results = results or []

        selected_set = set(selected_names) if selected_names is not None else None
        color_by_name = color_by_name or {}

        self.figure.clear()
        ax = self.figure.add_subplot(1, 1, 1)
        self._draw_landscape(ax)

        labeled_algorithms = set()
        for row in results:
            algorithm_name = str(row.get("name", "")).strip() or "Algoritam"
            if selected_set is not None and algorithm_name not in selected_set:
                continue

            points = self._history_points(row.get("history", []))
            if points is None:
                continue

            color = color_by_name.get(algorithm_name)
            line_label = algorithm_name if algorithm_name not in labeled_algorithms else None
            labeled_algorithms.add(algorithm_name)

            self._plot_path(ax=ax, points=points, line_color=color, line_label=line_label, line_alpha=0.95,
                            start_color=color, end_color=color, )

        self._finalize_axes(ax)
