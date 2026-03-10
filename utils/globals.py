from utils.config import MAX_POWER

screen = None  # pygame screen

wind = 3.0
initial_angle_deg = 36.0
initial_power = MAX_POWER / 3
terrain = None

# tanks
shooter = None
target = None

stop_criterions = {
    "max_time": 500,
    "max_iterations": 200,
    "max_function_calls": 300,
    "x_eps": 1e-6,
    "gradient_eps": 1e-6,
    "f_eps": 1e-6,
    "delta_min": 1e-6
}
