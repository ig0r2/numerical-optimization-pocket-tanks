from itertools import product
from algorithms import ALGORITHM_CLASSES, run_algorithm


def _parameter_combinations(grid_config):
    """Kreiraj kombinacije (dekartov proizvod) konfiguracije parametara"""
    keys = list(grid_config.keys())
    values = [grid_config[key] for key in keys]
    for combo in product(*values):
        yield dict(zip(keys, combo))


def _format_params(params):
    """Formatiranje parametara u string"""
    parts = []
    for key, value in sorted(params.items()):
        if isinstance(value, float):
            parts.append(f"{key}={value:.4g}")
        else:
            parts.append(f"{key}={value}")
    return ", ".join(parts)


def run_hyperparameter_sensitivity(algorithm_name):
    cfg = ALGORITHM_CLASSES[algorithm_name].params_grid()
    rows = []
    for params in _parameter_combinations(cfg):
        result = run_algorithm(name=algorithm_name, params=params)
        rows.append({
            "label": _format_params(params),
            "params": params,
            "final_f": result["final_f"],
            "iterations": result["iterations"],
            "function_calls": result["function_calls"],
            "time_s": result["time_s"],
            "stability_index": result["stability_index"],
            "stop_reason": result["stop_reason"],
        })
    return rows
