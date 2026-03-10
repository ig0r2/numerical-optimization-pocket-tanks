import math
import tkinter as tk
from tkinter import ttk

from .calculation import run_hyperparameter_sensitivity
from windows.utils import as_float, as_int


class SensitivityWindow:
    def __init__(self, algorithm_name):
        self.algorithm_name = algorithm_name
        self.results = run_hyperparameter_sensitivity(algorithm_name)

        self.root = tk.Tk()
        self.root.title(f"Osetljivost parametara")
        self.root.minsize(1024, 700)

        style = ttk.Style(self.root)
        if "arc" in style.theme_names():
            style.theme_use("arc")

        container = ttk.Frame(self.root, padding=12)
        container.pack(fill="both", expand=True)

        content = ttk.Frame(container)
        content.pack(fill="both", expand=True)
        content.rowconfigure(1, weight=3)
        content.rowconfigure(4, weight=3)
        content.columnconfigure(0, weight=1)

        self._build_combinations_treeview(content)
        self._build_single_parameter_treeview(content)
        self._refresh_combinations_treeview()
        self._refresh_parameter_options()
        self._refresh_single_parameter_treeview()

    def _build_combinations_treeview(self, parent):
        top = ttk.Frame(parent)
        top.grid(row=0, column=0, sticky="ew", pady=(0, 8))

        ttk.Label(top, text=f"Algoritam: {self.algorithm_name}").grid(row=0, column=0, padx=(0, 8), sticky="w")

        # column: (text, width)
        columns = {
            "label": ("Parametri", 560),
            "final_f": ("Konacna f(x)", 120),
            "iterations": ("Iteracije", 100),
            "function_calls": ("Pozivi f(x)", 100),
            "stability_index": ("Stabilnost", 110),
            "stop_reason": ("Stop kriterijum", 110),
        }

        self.combinations_treeview = ttk.Treeview(parent, columns=list(columns.keys()), show="headings", height=14)
        self.combinations_treeview.grid(row=1, column=0, sticky="nsew")

        y_scroll = ttk.Scrollbar(parent, orient="vertical", command=self.combinations_treeview.yview)
        y_scroll.grid(row=1, column=1, sticky="ns")
        self.combinations_treeview.configure(yscrollcommand=y_scroll.set)

        x_scroll = ttk.Scrollbar(parent, orient="horizontal", command=self.combinations_treeview.xview)
        x_scroll.grid(row=2, column=0, sticky="ew")
        self.combinations_treeview.configure(xscrollcommand=x_scroll.set)

        for col in columns.keys():
            title, width = columns[col]
            self.combinations_treeview.heading(col, text=title)
            self.combinations_treeview.column(col, width=width, anchor="w" if col == "label" else "center",
                                              stretch=True)

    def _build_single_parameter_treeview(self, parent):
        controls = ttk.Frame(parent)
        controls.grid(row=3, column=0, sticky="ew", pady=(10, 8))
        controls.columnconfigure(2, weight=1)

        ttk.Label(controls, text="Parametar:").grid(row=0, column=0, padx=(0, 6), sticky="w")
        self.parameter_var = tk.StringVar()
        self.parameter_combo = ttk.Combobox(controls, state="readonly", textvariable=self.parameter_var,
                                            values=[], width=24)
        self.parameter_combo.grid(row=0, column=1, sticky="w")
        self.parameter_combo.bind("<<ComboboxSelected>>", self._refresh_single_parameter_treeview)

        self.parameter_summary_var = tk.StringVar(value="Izaberite parametar za prikaz uticaja.")
        ttk.Label(controls, textvariable=self.parameter_summary_var, anchor="w").grid(row=0, column=2, padx=(14, 0),
                                                                                      sticky="ew")

        # column: (text, width)
        columns = {
            "value": ("Vrednost", 180),
            "samples": ("Broj testova", 80),
            "mean_final_f": ("Prosecni f(x)", 130),
            "best_final_f": ("Najbolji f(x)", 120),
            "mean_iterations": ("Prosecne iteracije", 130),
            "mean_stability": ("Prosecna stabilnost", 145),
        }

        self.single_parameter_treeview = ttk.Treeview(parent, columns=list(columns.keys()), show="headings", height=14)
        self.single_parameter_treeview.grid(row=4, column=0, sticky="nsew")

        y_scroll = ttk.Scrollbar(parent, orient="vertical", command=self.single_parameter_treeview.yview)
        y_scroll.grid(row=4, column=1, sticky="ns")
        self.single_parameter_treeview.configure(yscrollcommand=y_scroll.set)

        x_scroll = ttk.Scrollbar(parent, orient="horizontal", command=self.single_parameter_treeview.xview)
        x_scroll.grid(row=5, column=0, sticky="ew")
        self.single_parameter_treeview.configure(xscrollcommand=x_scroll.set)

        for col in columns.keys():
            text, width = columns[col]
            self.single_parameter_treeview.heading(col, text=text)
            self.single_parameter_treeview.column(col, width=width, anchor="w" if col == "value" else "center",
                                                  stretch=True)

    def _refresh_combinations_treeview(self):
        self.combinations_treeview.delete(*self.combinations_treeview.get_children(""))
        ordered = sorted(self.results, key=lambda row: as_float(row.get("final_f"), math.inf))
        for idx, row in enumerate(ordered):
            iid = f"combo_{idx}"
            values = (
                row.get("label", ""),
                f"{as_float(row.get('final_f')):.6f}",
                str(as_int(row.get("iterations"))),
                str(as_int(row.get("function_calls"))),
                f"{as_float(row.get('stability_index')):.3f}",
                row.get("stop_reason", ""),
            )
            self.combinations_treeview.insert("", "end", iid=iid, values=values)

    def _refresh_parameter_options(self):
        parameter_names = self._parameter_names()
        self.parameter_combo.configure(values=parameter_names)

        if not parameter_names:
            self.parameter_var.set("")
            return

        current = self.parameter_var.get()
        if current not in parameter_names:
            self.parameter_var.set(parameter_names[0])

    def _refresh_single_parameter_treeview(self, _event=None):
        parameter_name = self.parameter_var.get()

        self.single_parameter_treeview.delete(*self.single_parameter_treeview.get_children(""))
        aggregated = self._aggregate_by_parameter(parameter_name)

        for idx, item in enumerate(aggregated):
            iid = f"parameter_{idx}"
            values = (
                item["value_label"],
                str(item["samples"]),
                f"{item['mean_final_f']:.6f}",
                f"{item['best_final_f']:.6f}",
                f"{item['mean_iterations']:.2f}",
                f"{item['mean_stability']:.3f}",
            )
            self.single_parameter_treeview.insert("", "end", iid=iid, values=values)

        if aggregated:
            self.parameter_summary_var.set("")
        elif parameter_name:
            self.parameter_summary_var.set(f"Nema podataka za parametar '{parameter_name}'.")
        else:
            self.parameter_summary_var.set("Izaberite parametar za prikaz uticaja.")

    def _parameter_names(self):
        names = set()
        for row in self.results:
            params = row.get("params")
            if isinstance(params, dict):
                names.update(params.keys())
        return sorted(names)

    def _aggregate_by_parameter(self, parameter_name):
        if not parameter_name:
            return []

        buckets = {}
        for row in self.results:
            params = row.get("params")
            if not isinstance(params, dict) or parameter_name not in params:
                continue

            raw_value = params.get(parameter_name)
            value_label = f"{raw_value:.6g}"
            bucket_key = value_label

            if bucket_key not in buckets:
                buckets[bucket_key] = {
                    "value_label": value_label,
                    "samples": 0,
                    "sum_final_f": 0.0,
                    "best_final_f": math.inf,
                    "sum_iterations": 0.0,
                    "sum_stability": 0.0,
                }

            bucket = buckets[bucket_key]
            objective = as_float(row.get("final_f"), math.inf)
            if not math.isfinite(objective):
                continue
            bucket["samples"] += 1
            bucket["sum_final_f"] += objective
            bucket["best_final_f"] = min(bucket["best_final_f"], objective, )
            bucket["sum_iterations"] += as_int(row.get("iterations"))
            bucket["sum_stability"] += as_float(row.get("stability_index"))

        aggregated = []
        for bucket in buckets.values():
            count = bucket["samples"]
            if count == 0:
                continue
            aggregated.append(
                {
                    "value_label": bucket["value_label"],
                    "samples": bucket["samples"],
                    "mean_final_f": bucket["sum_final_f"] / count,
                    "best_final_f": bucket["best_final_f"],
                    "mean_iterations": bucket["sum_iterations"] / count,
                    "mean_stability": bucket["sum_stability"] / count,
                }
            )

        aggregated.sort(key=lambda item: (item["mean_final_f"], item["value_label"]))
        return aggregated

    def run(self):
        self.root.mainloop()
