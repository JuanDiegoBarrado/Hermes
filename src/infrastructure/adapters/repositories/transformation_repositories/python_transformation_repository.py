import importlib.util
import inspect
from collections.abc import Callable
from pathlib import Path
from types import ModuleType
from typing import Any

from application.ports.repositories.transformation_repository import TransformationRepository


class PythonTransformationRepository(TransformationRepository):
    """Funciones de transformación en ficheros Python: `<directory>/<fichero>.py`.

    "simpsons.select_columns" es la función `select_columns` de `<directory>/simpsons.py`.
    Las funciones que empiezan por "_" se consideran auxiliares y no son transformaciones.
    """

    def __init__(self, directory: Path) -> None:
        self._directory = directory

    def find(self, name: str) -> Callable[..., Any] | None:
        file_name, _, function_name = name.rpartition(".")
        path = self._directory / f"{file_name}.py"
        if not file_name or not path.is_file():
            return None
        return _functions(_import(path)).get(function_name)

    def find_all(self) -> dict[str, Callable[..., Any]]:
        if not self._directory.is_dir():
            return {}
        return {
            f"{path.stem}.{function_name}": function
            for path in sorted(self._directory.glob("*.py"))
            for function_name, function in _functions(_import(path)).items()
        }


def _import(path: Path) -> ModuleType:
    # Nombre propio para que un fichero del usuario (p. ej. json.py) no choque con otros módulos.
    spec = importlib.util.spec_from_file_location(f"hermes_transforms.{path.stem}", path)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _functions(module: ModuleType) -> dict[str, Callable[..., Any]]:
    """Las funciones públicas definidas en el propio módulo (no las importadas)."""
    return {
        name: function
        for name, function in inspect.getmembers(module, inspect.isfunction)
        if not name.startswith("_") and function.__module__ == module.__name__
    }
