from game import game_loop
from windows import MainWindow, SensitivityWindow, ComparisonWindow

if __name__ == "__main__":
    while True:
        action = MainWindow().run()
        if not action or action.get("action") == "exit":
            break

        if action.get("action") == "pygame_replay":
            game_loop(action.get("result", {}))
            continue

        if action.get("action") == "show_sensitivity":
            SensitivityWindow(action.get("algorithm_name")).run()
            continue

        if action.get("action") == "show_comparison":
            ComparisonWindow().run()
            continue
