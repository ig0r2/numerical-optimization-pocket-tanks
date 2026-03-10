import time
from abc import ABC, abstractmethod
import numpy as np

from utils import globals
from game import simulate_shot, scaler, apply_scenario

_function_call_count = 0


def function(x):
    global _function_call_count
    _function_call_count += 1

    angle_deg, power = scaler.original(x)
    return simulate_shot(angle_deg=angle_deg, power=power)["dist_m"]


def project(x):
    """Box projekcija - clip ako x izadju izvan [0-1]"""
    x = np.asarray(x, dtype=np.float64)
    x = np.nan_to_num(x, nan=0.5, posinf=1.0, neginf=0.0)
    return np.clip(x, 0.0, 1.0)


def calculate_gradient(x):
    """Numericki izracunaj gradijent sa korakom step i ogranicavanjem sa clip"""
    x = project(x)
    grad = np.zeros_like(x)
    step = 1e-5
    clip = 100

    for i in range(x.size):
        x_plus = x.copy()
        x_minus = x.copy()
        x_plus[i] = min(1.0, x_plus[i] + step)
        x_minus[i] = max(0.0, x_minus[i] - step)

        delta = x_plus[i] - x_minus[i]
        if delta <= 1e-12:
            grad[i] = 0.0
            continue

        grad[i] = (function(x_plus) - function(x_minus)) / delta

    grad = np.nan_to_num(grad, nan=0.0, posinf=clip, neginf=-clip)
    grad = np.clip(grad, -clip, clip)

    return grad


def get_x0():
    return scaler.normalized(np.array([globals.initial_angle_deg, globals.initial_power]))


class Algorithm(ABC):
    @staticmethod
    @abstractmethod
    def params_grid():
        pass

    @abstractmethod
    def step(self):
        pass


def run_algorithm(name, params=None):
    """
    Pokrece algoritam i prati istoriju iteracija
    """
    apply_scenario()

    x = get_x0()
    history = []

    stop_reason = "max_iter"
    start = time.perf_counter()

    algorithm = create_algorithm(name, params)

    f = function(x)
    history.append({"iteration": 0, "fx": f, "x": x})

    global _function_call_count
    _function_call_count = 0

    for iteration in range(1, globals.stop_criterions["max_iterations"] + 1):
        x, stop = algorithm.step()
        x = project(x)

        f = function(x)
        _function_call_count -= 1

        history.append({"iteration": iteration, "fx": f, "x": x})

        # prekid za max vreme
        if (time.perf_counter() - start) * 1000 > globals.stop_criterions["max_time"]:
            stop = "max_time"
        elif _function_call_count >= globals.stop_criterions["max_function_calls"]:
            stop = "max_function_calls"

        if stop:
            stop_reason = stop
            break

    elapsed = time.perf_counter() - start

    # stabilnost - indeks koliko cesto je algoritam isao u pravcu smanjenja funkcije
    stability_index = 1.0
    if len(history) > 1:
        increases = sum(curr["fx"] > prev["fx"] for prev, curr in zip(history, history[1:]))
        stability_index = 1.0 - increases / (len(history) - 1)

    return {
        "name": name,
        "iterations": len(history) - 1,
        "time_s": elapsed,
        "final_f": f,
        "function_calls": _function_call_count,
        "stop_reason": stop_reason,
        "stability_index": stability_index,
        "history": history,
    }


from algorithms_implemented import GradientDescentAutoLR, GradientDescentBacktracking, BFGS, LBFGS, HookeJeeves, \
    RandomSearchDensity, GaussSeidel, SpiralScan, MADS

ALGORITHM_CLASSES = {
    "Hooke-Jeeves": HookeJeeves,
    "Skeniranje po spirali": SpiralScan,
    "Gauss-Seidel": GaussSeidel,
    "Random Search": RandomSearchDensity,
    "MADS": MADS,
    "Gradijentni Spust (Auto korak)": GradientDescentAutoLR,
    "Gradijentni Spust (Backtracking)": GradientDescentBacktracking,
    "BFGS": BFGS,
    "L-BFGS": LBFGS,
}


def create_algorithm(algorithm_name, params=None):
    if algorithm_name not in ALGORITHM_CLASSES:
        raise ValueError(f"Nepostojeci algoritam: {algorithm_name}")
    if params is None:
        return ALGORITHM_CLASSES[algorithm_name]()
    else:
        return ALGORITHM_CLASSES[algorithm_name](**params)
