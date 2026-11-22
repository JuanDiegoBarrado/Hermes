from abc import ABC, abstractmethod


class Writer(ABC):
    """Escribe bytes en un sistema de datos (sistema de ficheros, HTTP, S3...).

    Cada implementación se construye con las opciones de su `Location` (una ruta, una URL...).
    """

    @abstractmethod
    def write(self, content: bytes) -> None: ...
