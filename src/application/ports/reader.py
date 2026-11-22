from abc import ABC, abstractmethod


class Reader(ABC):
    """Lee bytes de un sistema de datos (sistema de ficheros, HTTP, S3...).

    Cada implementación se construye con las opciones de su `Location` (una ruta, una URL...).
    """

    @abstractmethod
    def read(self) -> bytes: ...
