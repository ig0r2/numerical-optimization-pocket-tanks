import tkinter as tk
from tkinter import messagebox, ttk

from algorithms import ALGORITHM_CLASSES, run_algorithm
from game import apply_scenario
from .params_settings import AlgorithmParamsSection
from .global_settings import GlobalSettingsSection
from windows.heatmap_plot import HeatmapPlot


class MainWindow:
    def __init__(self):
        self.selection = {"action": "exit"}
        self.last_result = None

        self.root = tk.Tk()
        self.root.title("Pocket Tanks")
        self.root.minsize(720, 560)

        style = ttk.Style(self.root)
        if "arc" in style.theme_names():
            style.theme_use("arc")

        self.algorithm_names = list(ALGORITHM_CLASSES.keys())

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self.close)
        self.root.bind("<Escape>", lambda _event: self.close())

    def _build_ui(self):
        container = ttk.Frame(self.root, padding=14)
        container.pack(fill="both", expand=True)

        self.global_settings_section = GlobalSettingsSection(container, on_apply=self._on_global_settings_applied)

        main_content = ttk.Frame(container, padding=12)
        main_content.pack(fill="both", expand=True)
        self._build_main_content(main_content)

    def _on_global_settings_applied(self):
        self.pygame_button.configure(state="disable")
        self.heatmap_plot.create_grid(force=True)
        self.heatmap_plot.draw()

    def _build_main_content(self, parent):
        parent.columnconfigure(0, weight=0)
        parent.columnconfigure(1, weight=1)
        parent.rowconfigure(0, weight=1)

        self.sim_algorithm_var = tk.StringVar(value=self.algorithm_names[0])
        self.sim_summary_var = tk.StringVar(value="")

        controls = ttk.Frame(parent, padding=(0, 0, 12, 0))
        controls.grid(row=0, column=0, sticky="nsw")
        controls.columnconfigure(0, weight=1)

        # Algoritam combobox
        ttk.Label(controls, text="Algoritam:").grid(row=0, column=0, sticky="w", pady=4)
        sim_algo_combo = ttk.Combobox(controls, state="readonly", textvariable=self.sim_algorithm_var,
                                      values=self.algorithm_names, width=34)
        sim_algo_combo.grid(row=1, column=0, sticky="ew", pady=(0, 8))
        sim_algo_combo.bind("<<ComboboxSelected>>", self._on_algorithm_selected)

        # pokreni algoritam button
        ttk.Button(controls, text="Pokreni algoritam", command=self._run_single_simulation).grid(
            row=2, column=0, sticky="ew", pady=(0, 8), ipady=6)

        self.sim_params_section = AlgorithmParamsSection(controls, self.sim_algorithm_var)
        self.sim_params_section.frame.grid(row=3, column=0, sticky="ew", pady=(0, 10))

        # pygame button
        self.pygame_button = ttk.Button(controls, text="Prikazi putanju u pygame", command=self.open_pygame_replay,
                                        state="disabled")
        self.pygame_button.grid(row=4, column=0, sticky="ew", pady=(0, 10), ipady=6)

        ttk.Button(controls, text="Analiza osetljivosti parametara", command=self.open_sensitivity).grid(
            row=5, column=0, sticky="ew", pady=(0, 8), ipady=6)

        ttk.Separator(controls, orient="horizontal").grid(row=6, column=0, sticky="ew", pady=(4, 8))
        ttk.Button(controls, text="Uporedjivanje algoritama", command=self.open_comparison).grid(
            row=7, column=0, sticky="ew", pady=(0, 8), ipady=6)

        self.heatmap_plot = HeatmapPlot(parent)
        self.heatmap_plot.frame.grid(row=0, column=1, sticky="nsew")
        ttk.Label(self.heatmap_plot.frame, textvariable=self.sim_summary_var, anchor="w", justify="left",
                  wraplength=780).grid(row=2, column=0, sticky="ew", pady=(8, 0))

        apply_scenario()
        self.heatmap_plot.draw()

    def _run_single_simulation(self):
        self.root.update_idletasks()

        try:
            algorithm_params = self.sim_params_section.collect()
            self.sim_params_section.persist(algorithm_params)
            result = run_algorithm(self.sim_algorithm_var.get(), params=algorithm_params)
        except ValueError as exc:
            messagebox.showerror("Greska pri unosu", str(exc))
            return

        self.heatmap_plot.draw(result)
        self.sim_summary_var.set(
            f"f(x)={result['final_f']:.6f} | "
            f"iter={result['iterations']} | pozivi f(x)={result['function_calls']} | "
            f"vreme={result['time_s'] * 1000.0:.2f} ms | stop={result['stop_reason']}")

        # enable pygame button
        self.last_result = result
        self.pygame_button.configure(state="normal")

    def _on_algorithm_selected(self, _event=None):
        self.sim_params_section.rebuild()

    def open_pygame_replay(self):
        if not self.last_result: return
        self.selection = {"action": "pygame_replay", "result": self.last_result}
        self.root.destroy()

    def open_sensitivity(self):
        self.selection = {"action": "show_sensitivity", "algorithm_name": self.sim_algorithm_var.get()}
        self.root.destroy()

    def open_comparison(self):
        self.selection = {"action": "show_comparison"}
        self.root.destroy()

    def close(self):
        self.selection = {"action": "exit"}
        self.root.destroy()

    def run(self):
        self.root.mainloop()
        return self.selection
