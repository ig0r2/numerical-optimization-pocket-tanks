import math
import tkinter as tk
from tkinter import ttk
from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg, NavigationToolbar2Tk
from matplotlib.figure import Figure

from algorithms import ALGORITHM_CLASSES, run_algorithm
from windows.heatmap_plot import HeatmapPlot
from windows.utils import as_float, as_int


class ComparisonWindow:
    def __init__(self):
        self.results = sorted(
            (run_algorithm(name) for name in ALGORITHM_CLASSES.keys()),
            key=lambda row: as_float(row.get("final_f"), math.inf),
        )

        self.root = tk.Tk()
        self.root.title("Poredjenje algoritama")
        self.root.minsize(1024, 700)

        style = ttk.Style(self.root)
        if "arc" in style.theme_names():
            style.theme_use("arc")

        self._comparison_by_iid = {}
        self._landscape_visibility_vars = {}
        self._convergence_visibility_vars = {}
        self._convergence_toolbar = None
        self.heatmap_plot = None

        self._build_ui()

    def _build_ui(self):
        notebook = ttk.Notebook(self.root)
        notebook.pack(fill="both", expand=True, padx=12, pady=12)

        comparison_tab = ttk.Frame(notebook)
        final_tab = ttk.Frame(notebook)
        convergence_tab = ttk.Frame(notebook)
        iterations_tab = ttk.Frame(notebook)
        function_calls_tab = ttk.Frame(notebook)
        timing_tab = ttk.Frame(notebook)
        landscape_tab = ttk.Frame(notebook)

        notebook.add(comparison_tab, text="Tabela")
        notebook.add(final_tab, text="Konacna f(x)")
        notebook.add(convergence_tab, text="Konvergencija")
        notebook.add(iterations_tab, text="Iteracije")
        notebook.add(function_calls_tab, text="Pozivi funkcija")
        notebook.add(timing_tab, text="Vreme izvrsavanja")
        notebook.add(landscape_tab, text="2D putanje")

        self._build_comparison_tab(comparison_tab)
        self._build_metric_plot_tab(final_tab, "final_f")
        self._build_convergence_tab(convergence_tab)
        self._build_metric_plot_tab(iterations_tab, "iterations")
        self._build_metric_plot_tab(function_calls_tab, "function_calls")
        self._build_metric_plot_tab(timing_tab, "time_ms")
        self._build_landscape_tab(landscape_tab)

    def _algorithm_names(self):
        names = []
        seen = set()
        for row in self.results:
            name = str(row.get("name", "")).strip()
            if not name or name in seen:
                continue
            seen.add(name)
            names.append(name)
        return names

    def _build_comparison_tab(self, parent):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        # column: (text, width)
        columns = {
            "name": ("Algoritam", 180),
            "final_f": ("Konacna f(x)", 120),
            "iterations": ("Iteracije", 90),
            "function_calls": ("Pozivi f(x)", 100),
            "time_ms": ("Vreme [ms]", 110),
            "stability_index": ("Stabilnost", 110),
            "stop_reason": ("Stop kriterijum", 170),
        }
        self.comparison_tree = ttk.Treeview(parent, columns=list(columns.keys()), show="headings", height=13)
        self.comparison_tree.grid(row=0, column=0, sticky="nsew")

        y_scroll = ttk.Scrollbar(parent, orient="vertical", command=self.comparison_tree.yview)
        y_scroll.grid(row=0, column=1, sticky="ns")
        self.comparison_tree.configure(yscrollcommand=y_scroll.set)

        for key, value in columns.items():
            self.comparison_tree.heading(key, text=value[0])
            self.comparison_tree.column(key, width=value[1], anchor="w" if key in {"name", "stop_reason"} else "center",
                                        stretch=True)

        self._fill_comparison_table()

    def _fill_comparison_table(self):
        self.comparison_tree.delete(*self.comparison_tree.get_children(""))
        self._comparison_by_iid = {}

        for idx, row in enumerate(self.results):
            iid = f"cmp_{idx}"
            values = (
                row.get("name", ""),
                f"{as_float(row.get('final_f')):.6f}",
                str(as_int(row.get("iterations"))),
                str(as_int(row.get("function_calls"))),
                f"{as_float(row.get('time_s')) * 1000.0:.2f}",
                f"{as_float(row.get('stability_index')):.3f}",
                row.get("stop_reason", ""),
            )
            self.comparison_tree.insert("", "end", iid=iid, values=values)
            self._comparison_by_iid[iid] = row

    def _build_metric_plot_tab(self, parent, mode):
        parent.rowconfigure(0, weight=1)
        parent.columnconfigure(0, weight=1)

        figure = Figure(figsize=(12, 6), dpi=100)
        canvas = FigureCanvasTkAgg(figure, master=parent)
        canvas.get_tk_widget().grid(row=0, column=0, sticky="nsew")

        self._redraw_metric_plot(figure, canvas, mode)

    def _redraw_metric_plot(self, figure, canvas, mode):
        figure.clear()
        ax = figure.add_subplot(1, 1, 1)

        names = [row.get("name", "") for row in self.results]

        if mode == "iterations":
            values = [as_int(row.get("iterations")) for row in self.results]
            title = "Broj iteracija"
            y_label = "Iteracije"
            color = "#0EA5E9"
        elif mode == "function_calls":
            values = [as_int(row.get("function_calls")) for row in self.results]
            title = "Pozivi funkcija"
            y_label = "Broj poziva"
            color = "#0EA5E9"
        elif mode == "time_ms":
            values = [as_float(row.get("time_s")) * 1000.0 for row in self.results]
            title = "Vreme izvrsavanja"
            y_label = "Vreme [ms]"
            color = "#0EA5E9"
        else:
            values = [as_float(row.get("final_f")) for row in self.results]
            title = "Konacna f(x)"
            y_label = "Konacna f(x)"
            color = "#0EA5E9"

        self._draw_bar_metric(ax=ax, names=names, values=values, title=title, y_label=y_label, color=color)

        figure.tight_layout()
        canvas.draw_idle()

    def _build_convergence_tab(self, parent):
        self._build_selectable_plot_tab(
            parent=parent,
            visibility_vars_attr="_convergence_visibility_vars",
            redraw_callback=self._redraw_convergence_plot,
            figure_attr="convergence_figure",
            canvas_attr="convergence_canvas",
            toolbar_attr="_convergence_toolbar",
        )

    def _redraw_convergence_plot(self):
        self.convergence_figure.clear()
        ax = self.convergence_figure.add_subplot(1, 1, 1)

        selected_algos = self._selected_algorithms(self._convergence_visibility_vars)

        for row in self.results:
            algorithm_name = str(row.get("name", ""))
            if algorithm_name not in selected_algos:
                continue

            history = row.get("history", [])
            if not history:
                continue
            x_data = [as_int(point.get("iteration")) for point in history]
            y_data = [as_float(point.get("fx")) for point in history]
            ax.plot(x_data, y_data, linewidth=1.7, label=algorithm_name)

        ax.set_title("Konvergencija")
        ax.set_xlabel("Iteracija")
        ax.set_ylabel("Konacna f(x)")
        ax.grid(alpha=0.25)
        if ax.lines:
            ax.legend(fontsize=8)

        self.convergence_figure.tight_layout()
        self.convergence_canvas.draw_idle()

    def _build_landscape_tab(self, parent):
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        controls = ttk.Frame(parent)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        controls.columnconfigure(1, weight=1)

        selected_frame = ttk.Frame(controls)
        selected_frame.grid(row=0, column=1, sticky="w")

        self._landscape_visibility_vars = {}
        max_columns = 3
        for idx, name in enumerate(self._algorithm_names()):
            variable = tk.BooleanVar(value=True)
            self._landscape_visibility_vars[name] = variable
            check = ttk.Checkbutton(selected_frame, text=name, variable=variable, command=self._redraw_landscape_plot)
            check.grid(row=idx // max_columns, column=idx % max_columns, sticky="w", padx=(0, 12), pady=2)

        self.heatmap_plot = HeatmapPlot(parent, figure_size=(12, 6))
        self.heatmap_plot.frame.grid(row=1, column=0, sticky="nsew")

        self._redraw_landscape_plot()

    def _build_selectable_plot_tab(self, parent, visibility_vars_attr, redraw_callback, figure_attr, canvas_attr,
                                   toolbar_attr=None):
        parent.rowconfigure(1, weight=1)
        parent.columnconfigure(0, weight=1)

        controls = ttk.Frame(parent)
        controls.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        controls.columnconfigure(1, weight=1)

        selected_frame = ttk.Frame(controls)
        selected_frame.grid(row=0, column=1, sticky="w")

        visibility_vars = {}
        setattr(self, visibility_vars_attr, visibility_vars)

        max_columns = 3
        for idx, name in enumerate(self._algorithm_names()):
            variable = tk.BooleanVar(value=True)
            visibility_vars[name] = variable
            check = ttk.Checkbutton(selected_frame, text=name, variable=variable, command=redraw_callback)
            check.grid(row=idx // max_columns, column=idx % max_columns, sticky="w", padx=(0, 12), pady=2)

        chart_frame = ttk.Frame(parent)
        chart_frame.grid(row=1, column=0, sticky="nsew")
        canvas_row = 1 if toolbar_attr else 0
        chart_frame.rowconfigure(canvas_row, weight=1)
        chart_frame.columnconfigure(0, weight=1)

        figure = Figure(figsize=(12, 6), dpi=100)
        canvas = FigureCanvasTkAgg(figure, master=chart_frame)
        canvas.get_tk_widget().grid(row=canvas_row, column=0, sticky="nsew")

        if toolbar_attr:
            toolbar = NavigationToolbar2Tk(canvas, chart_frame, pack_toolbar=False)
            toolbar.update()
            toolbar.grid(row=0, column=0, sticky="w")
            setattr(self, toolbar_attr, toolbar)

        setattr(self, figure_attr, figure)
        setattr(self, canvas_attr, canvas)
        redraw_callback()

    def _redraw_landscape_plot(self):
        selected_algos = self._selected_algorithms(self._landscape_visibility_vars)
        palette = ["#0EA5E9", "#F97316", "#16A34A", "#E11D48", "#7C3AED", "#F59E0B", "#0891B2", "#6B7280", ]
        color_by_algorithm = {
            algorithm_name: palette[idx % len(palette)]
            for idx, algorithm_name in enumerate(self._landscape_visibility_vars.keys())
        }

        self.heatmap_plot.draw_many(self.results, selected_names=selected_algos, color_by_name=color_by_algorithm)

    @staticmethod
    def _draw_bar_metric(ax, names, values, title, y_label, color):
        ax.bar(names, values, color=color)
        ax.set_title(title)
        ax.set_ylabel(y_label)
        ax.tick_params(axis="x", rotation=25)
        ax.grid(axis="y", alpha=0.2)

    @staticmethod
    def _selected_algorithms(visibility_vars):
        return [algorithm_name for algorithm_name, variable in visibility_vars.items() if variable.get()]

    def run(self):
        self.root.mainloop()
