from application.ports.writer import Writer
from domain.location import Location


class WriterFactory:
    """Crea el Writer que corresponde a `location.system`, configurado con `location.options`.

    El diccionario {system: clase Writer} se le pasa al arrancar la aplicación.
    """

    def __init__(self, writers: dict[str, type[Writer]]) -> None:
        self._writers = writers

    def create(self, location: Location) -> Writer:
        return self._writers[location.system](**location.options)
