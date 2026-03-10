import tkinter as tk
from tkinter import messagebox, ttk
import numpy as np

from utils import globals
from game import apply_scenario, scaler


class GlobalSettingsSection:
    def __init__(self, parent, on_apply=None):
        self.on_apply = on_apply
        self.frame = ttk.Frame(parent)
        self.frame.pack(fill="x", pady=(0, 10))

        self.wind_var = tk.StringVar(value=f"{globals.wind:g}")

        initial_norm = scaler.normalized(np.array([globals.initial_angle_deg, globals.initial_power], dtype=np.float64))
        self.angle_var = tk.StringVar(value=f"{float(initial_norm[0]):g}")
        self.power_var = tk.StringVar(value=f"{float(initial_norm[1]):g}")

        self.c_max_time_var = tk.StringVar(value=f"{float(globals.stop_criterions["max_time"]):g}")
        self.c_max_iter_var = tk.StringVar(value=f"{float(globals.stop_criterions["max_iterations"]):g}")
        self.c_max_function_calls_var = tk.StringVar(value=f"{float(globals.stop_criterions["max_function_calls"]):g}")
        self.c_x_eps_var = tk.StringVar(value=f"{float(globals.stop_criterions["x_eps"]):g}")
        self.c_grad_eps_var = tk.StringVar(value=f"{float(globals.stop_criterions["gradient_eps"]):g}")
        self.c_f_eps_var = tk.StringVar(value=f"{float(globals.stop_criterions["f_eps"]):g}")
        self.c_delta_min_var = tk.StringVar(value=f"{float(globals.stop_criterions["delta_min"]):g}")

        self._build_ui()

    def _build_ui(self):
        # gornji red
        top_row = ttk.Frame(self.frame)
        top_row.pack(fill="x")

        ttk.Label(top_row, text="Pocetna snaga:").pack(side="left")
        ttk.Entry(top_row, textvariable=self.power_var, width=6).pack(side="left", padx=(8, 12))
        ttk.Label(top_row, text="Pocetni ugao:").pack(side="left")
        ttk.Entry(top_row, textvariable=self.angle_var, width=6).pack(side="left", padx=(8, 12))
        ttk.Label(top_row, text="Vetar [m/s²]:").pack(side="left")
        ttk.Entry(top_row, textvariable=self.wind_var, width=6).pack(side="left", padx=(8, 12))

        # donji red
        bottom_row = ttk.Frame(self.frame)
        bottom_row.pack(fill="x", pady=(6, 0))

        ttk.Label(bottom_row, text="Kriterijumi zaustavljanja:        Max vreme (ms):").pack(side="left")
        ttk.Entry(bottom_row, textvariable=self.c_max_time_var, width=8).pack(side="left", padx=(8, 12))
        ttk.Label(bottom_row, text="Max iteracija:").pack(side="left")
        ttk.Entry(bottom_row, textvariable=self.c_max_iter_var, width=8).pack(side="left", padx=(8, 12))
        ttk.Label(bottom_row, text="Max poziva f(x):").pack(side="left")
        ttk.Entry(bottom_row, textvariable=self.c_max_function_calls_var, width=8).pack(side="left", padx=(8, 12))
        ttk.Label(bottom_row, text="delta min:").pack(side="left")
        ttk.Entry(bottom_row, textvariable=self.c_delta_min_var, width=8).pack(side="left", padx=(8, 0))
        ttk.Label(bottom_row, text="x eps:").pack(side="left")
        ttk.Entry(bottom_row, textvariable=self.c_x_eps_var, width=8).pack(side="left", padx=(8, 12))
        ttk.Label(bottom_row, text="Gradijent eps:").pack(side="left")
        ttk.Entry(bottom_row, textvariable=self.c_grad_eps_var, width=8).pack(side="left", padx=(8, 12))
        ttk.Label(bottom_row, text="f(x) eps:").pack(side="left")
        ttk.Entry(bottom_row, textvariable=self.c_f_eps_var, width=8).pack(side="left", padx=(8, 0))
        ttk.Button(bottom_row, text="Sacuvaj", command=self._apply_from_button, width=12, padding=(10, 6)).pack(
            side="left", padx=(8, 0))

    def _apply_from_button(self):
        try:
            wind = float(self.wind_var.get())
            angle_norm = float(self.angle_var.get())
            power_norm = float(self.power_var.get())
            c_max_time = int(self.c_max_time_var.get())
            c_max_iter = int(self.c_max_iter_var.get())
            c_max_function_calls = int(self.c_max_function_calls_var.get())
            c_delta_min = float(self.c_delta_min_var.get())
            c_x_eps = float(self.c_x_eps_var.get())
            c_grad_eps = float(self.c_grad_eps_var.get())
            c_f_eps = float(self.c_f_eps_var.get())

            if not 0.0 <= angle_norm <= 1.0:
                raise ValueError("Ugao mora biti u opsegu [0, 1]")
            if not 0.0 <= power_norm <= 1.0:
                raise ValueError("Snaga mora biti u opsegu [0, 1]")
            if c_max_time <= 0:
                raise ValueError("Max vreme mora biti > 0")
            if c_max_iter <= 0:
                raise ValueError("Max iteracija mora biti > 0")
            if c_max_function_calls <= 0:
                raise ValueError("Max broj poziva f(x) mora biti > 0")
            if c_delta_min <= 0:
                raise ValueError("delta min mora biti > 0")
            if c_x_eps <= 0:
                raise ValueError("Korak eps mora biti > 0")
            if c_grad_eps <= 0:
                raise ValueError("Gradijent eps mora biti > 0")
            if c_f_eps <= 0:
                raise ValueError("f(x) eps mora biti > 0")

            initial_angle_deg, initial_power = scaler.original(np.array([angle_norm, power_norm], dtype=np.float64))

            globals.wind = wind
            globals.initial_angle_deg = float(initial_angle_deg)
            globals.initial_power = float(initial_power)

            globals.stop_criterions = {
                "max_time": c_max_time,
                "max_iterations": c_max_iter,
                "max_function_calls": c_max_function_calls,
                "x_eps": c_x_eps,
                "gradient_eps": c_grad_eps,
                "f_eps": c_f_eps,
                "delta_min": c_delta_min
            }

            apply_scenario()

            if callable(self.on_apply): self.on_apply()
        except ValueError as exc:
            messagebox.showerror("Greska pri unosu", str(exc))

        self.sync_from_globals()

    def sync_from_globals(self):
        self.wind_var.set(f"{globals.wind:g}")
        initial_norm = scaler.normalized(np.array([globals.initial_angle_deg, globals.initial_power], dtype=np.float64))
        self.angle_var.set(f"{float(initial_norm[0]):g}")
        self.power_var.set(f"{float(initial_norm[1]):g}")
        self.c_max_time_var.set(f"{globals.stop_criterions["max_time"]:g}")
        self.c_max_iter_var.set(f"{globals.stop_criterions["max_iterations"]:g}")
        self.c_max_function_calls_var.set(f"{globals.stop_criterions["max_function_calls"]:g}")
        self.c_delta_min_var.set(f"{globals.stop_criterions["delta_min"]:g}")
        self.c_x_eps_var.set(f"{globals.stop_criterions["x_eps"]:g}")
        self.c_grad_eps_var.set(f"{globals.stop_criterions["gradient_eps"]:g}")
        self.c_f_eps_var.set(f"{globals.stop_criterions["f_eps"]:g}")
