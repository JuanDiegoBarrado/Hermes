import pandas as pd

from application.ports.serializer import Serializer


class JsonSerializer(Serializer):
    """Escribe una lista de objetos, una por fila: `[{"id": 1, ...}, {"id": 2, ...}]`."""

    def serialize(self, data: pd.DataFrame) -> bytes:
        return data.to_json(orient="records", force_ascii=False, date_format="iso").encode("utf-8")
