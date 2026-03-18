from __future__ import annotations

import json
from pathlib import Path
from typing import Mapping, TypeAlias

JsonScalar: TypeAlias = bool | int | float | str


class AlgorithmParamsStore:
    def __init__(self, path: Path | None = None):
        self._path = Path(path) if path else Path("data/algorithm_params.json")
        self._data: dict[str, dict[str, JsonScalar]] = {}
        self._load()

    def _load(self) -> None:
        try:
            payload = self._path.read_text(encoding="utf-8")
        except FileNotFoundError:
            self._data = {}
            return
        except OSError:
            self._data = {}
            return

        try:
            raw = json.loads(payload)
        except json.JSONDecodeError:
            self._data = {}
            return

        if not isinstance(raw, dict):
            self._data = {}
            return

        cleaned: dict[str, dict[str, JsonScalar]] = {}
        for algorithm_name, params in raw.items():
            if not isinstance(algorithm_name, str) or not isinstance(params, dict):
                continue
            algorithm_params: dict[str, JsonScalar] = {}
            for param_name, value in params.items():
                if not isinstance(param_name, str):
                    continue
                if value is None:
                    continue
                if isinstance(value, (str, int, float, bool)):
                    algorithm_params[param_name] = value
            if algorithm_params:
                cleaned[algorithm_name] = algorithm_params

        self._data = cleaned

    def _save(self) -> None:
        try:
            self._path.parent.mkdir(parents=True, exist_ok=True)
            tmp_path = self._path.with_suffix(f"{self._path.suffix}.tmp")
            tmp_path.write_text(
                json.dumps(self._data, indent=2, ensure_ascii=False, sort_keys=True) + "\n",
                encoding="utf-8",
            )
            tmp_path.replace(self._path)
        except OSError:
            return

    def get(self, algorithm_name: str) -> dict[str, JsonScalar]:
        params = self._data.get(algorithm_name, {})
        return dict(params) if isinstance(params, dict) else {}

    def set(self, algorithm_name: str, params: Mapping[str, JsonScalar]) -> None:
        cleaned: dict[str, JsonScalar] = {}
        for key, value in dict(params).items():
            key = str(key)
            if isinstance(value, str):
                value = value.strip()
                if not value:
                    continue
                cleaned[key] = value
                continue

            if isinstance(value, (int, float, bool)):
                cleaned[key] = value

        if cleaned:
            self._data[algorithm_name] = cleaned
        else:
            self._data.pop(algorithm_name, None)

        self._save()

    def reset(self, algorithm_name: str) -> None:
        if algorithm_name in self._data:
            self._data.pop(algorithm_name, None)
            self._save()
