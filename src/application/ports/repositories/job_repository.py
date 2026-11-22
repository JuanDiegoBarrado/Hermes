from abc import ABC, abstractmethod

from domain.job import Job


class JobRepository(ABC):
    """Abstracción del almacenamiento de los jobs. Un job se identifica por su nombre."""

    @abstractmethod
    def find(self, name: str) -> Job | None:
        """El job con ese nombre, o None si no existe."""

    @abstractmethod
    def find_all(self) -> list[Job]:
        """Todos los jobs almacenados."""

    @abstractmethod
    def save(self, job: Job) -> None:
        """Crea el job o, si ya existe uno con ese nombre, lo sustituye."""

    @abstractmethod
    def delete(self, name: str) -> None:
        """Elimina el job con ese nombre. Si no existe, no hace nada."""
