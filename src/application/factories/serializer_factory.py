from application.ports.serializer import Serializer


class SerializerFactory:
    """Crea el Serializer que corresponde a un formato ("csv", "json", "yaml"...).

    El diccionario {formato: clase Serializer} se le pasa al arrancar la aplicación.
    """

    def __init__(self, serializers: dict[str, type[Serializer]]) -> None:
        self._serializers = serializers

    def create(self, format: str) -> Serializer:
        return self._serializers[format]()
