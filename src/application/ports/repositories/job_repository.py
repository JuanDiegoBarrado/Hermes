from abc import ABC, abstractmethod

from domain.job import Job


class InvalidJobError(ValueError):
    """Un job almacenado que no se puede leer. `enabled` dice si está activado: True si lo está
    o si no se puede saber."""

    def __init__(self, message: str, enabled: bool = True) -> None:
        super().__init__(message)
        self.enabled = enabled


class JobRepository(ABC):
    """Abstracción del almacenamiento de los jobs. Un job se identifica por su nombre."""

    @abstractmethod
    def find(self, name: str) -> Job | None:
        """El job con ese nombre, o None si no existe. Lanza InvalidJobError si no se puede leer."""

    @abstractmethod
    def find_names(self) -> list[str]:
        """Los nombres de todos los jobs almacenados, sin leerlos (aunque alguno no sea válido)."""

    @abstractmethod
    def find_all(self) -> list[Job]:
        """Todos los jobs almacenados."""

    @abstractmethod
    def save(self, job: Job) -> None:
        """Crea el job o, si ya existe uno con ese nombre, lo sustituye."""

    @abstractmethod
    def delete(self, name: str) -> None:
        """Elimina el job con ese nombre. Si no existe, no hace nada."""
