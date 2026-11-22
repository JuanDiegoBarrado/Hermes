from application.ports.parser import Parser


class ParserFactory:
    """Crea el Parser que corresponde a un formato ("csv", "json", "yaml"...).

    El diccionario {formato: clase Parser} se le pasa al arrancar la aplicación.
    """

    def __init__(self, parsers: dict[str, type[Parser]]) -> None:
        self._parsers = parsers

    def create(self, format: str) -> Parser:
        return self._parsers[format]()
