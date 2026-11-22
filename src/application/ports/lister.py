from abc import ABC, abstractmethod
from dataclasses import dataclass

from domain.location import Location


@dataclass(frozen=True)
class Item:
    """Una de las cosas que hay que leer del origen de un job: la location concreta que lee su
    Reader y su nombre, si lo tiene (el de un fichero, con extensión), con el que sale en los
    logs y en los errores."""

    location: Location
    name: str | None = None


class Lister(ABC):
    """Dice qué hay que leer de la location del origen de un job, y marca lo ya procesado.

    Cada implementación se construye con esa location. El job lee cada Item con el Reader de su
    sistema, y llama a done() en cuanto se escribe su salida.
    """

    @abstractmethod
    def items(self) -> list[Item]: ...

    @abstractmethod
    def done(self, item: Item) -> None: ...
