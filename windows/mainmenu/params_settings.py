import inspect
import tkinter as tk
from tkinter import ttk

from algorithms import ALGORITHM_CLASSES


class AlgorithmParamsSection:
    def __init__(self, parent, algorithm_name_var):
        self.algorithm_name_var = algorithm_name_var
        self.param_vars = {}
        self.param_defaults = {}

        self.frame = ttk.LabelFrame(parent, text="Parametri algoritma", padding=(8, 6))
        self.frame.columnconfigure(1, weight=1)
        self.rebuild()

    @staticmethod
    def _format_param_default(value):
        if isinstance(value, float):
            return f"{value:.12g}"
        return str(value)

    @staticmethod
    def _parse_param_value(name, value, default):
        raw = value.strip()
        if not raw:
            raise ValueError(f"Parametar '{name}' ne sme biti prazan.")

        if isinstance(default, bool):
            normalized = raw.lower()
            if normalized in {"1", "true", "yes", "y", "da"}:
                return True
            if normalized in {"0", "false", "no", "n", "ne"}:
                return False
            raise ValueError(f"Parametar '{name}' mora biti bool (true/false).")

        if isinstance(default, int):
            try:
                return int(raw)
            except ValueError as exc:
                raise ValueError(f"Parametar '{name}' mora biti ceo broj.") from exc

        if isinstance(default, float):
            try:
                return float(raw)
            except ValueError as exc:
                raise ValueError(f"Parametar '{name}' mora biti decimalni broj.") from exc

        return raw

    def _algorithm_param_defaults(self, algorithm_name):
        algorithm_class = ALGORITHM_CLASSES[algorithm_name]
        signature = inspect.signature(algorithm_class.__init__)
        defaults = {}

        for name, parameter in signature.parameters.items():
            if name == "self":
                continue
            if parameter.default is inspect._empty:
                continue
            defaults[name] = parameter.default

        return defaults

    def rebuild(self):
        for child in self.frame.winfo_children():
            child.destroy()

        self.param_vars = {}
        self.param_defaults = self._algorithm_param_defaults(self.algorithm_name_var.get())

        if not self.param_defaults:
            return

        for row_idx, (param_name, default_value) in enumerate(self.param_defaults.items()):
            ttk.Label(self.frame, text=f"{param_name}:").grid(
                row=row_idx, column=0, sticky="w", padx=(0, 8), pady=2)
            variable = tk.StringVar(value=self._format_param_default(default_value))
            self.param_vars[param_name] = variable
            ttk.Entry(self.frame, textvariable=variable, width=14).grid(
                row=row_idx, column=1, sticky="ew", pady=2)

    def collect(self):
        parsed = {}
        for param_name, default_value in self.param_defaults.items():
            value = self.param_vars.get(param_name)
            if value is None:
                continue
            parsed[param_name] = self._parse_param_value(param_name, value.get(), default_value)
        return parsed
