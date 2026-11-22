import pandas as pd

from application.ports.serializer import Serializer


class CsvSerializer(Serializer):
    def serialize(self, data: pd.DataFrame) -> bytes:
        return data.to_csv(index=False, lineterminator="\n").encode("utf-8")
