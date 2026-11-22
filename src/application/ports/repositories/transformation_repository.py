from abc import ABC, abstractmethod
from collections.abc import Callable
from typing import Any


class TransformationRepository(ABC):
    """Abstracción del almacenamiento de las funciones de transformación.

    Una función se identifica por su nombre "<fichero>.<función>". Es de solo lectura:
    las funciones las escribe el usuario, no Hermes.
    """

    @abstractmethod
    def find(self, name: str) -> Callable[..., Any] | None:
        """La función con ese nombre, o None si no existe."""

    @abstractmethod
    def find_all(self) -> dict[str, Callable[..., Any]]:
        """Todas las funciones disponibles, por nombre."""
