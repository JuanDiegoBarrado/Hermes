from application.ports.reader import Reader
from domain.location import Location


class ReaderFactory:
    """Crea el Reader que corresponde a `location.system`, configurado con `location.options`.

    El diccionario {system: clase Reader} se le pasa al arrancar la aplicación.
    """

    def __init__(self, readers: dict[str, type[Reader]]) -> None:
        self._readers = readers

    def create(self, location: Location) -> Reader:
        return self._readers[location.system](**location.options)
