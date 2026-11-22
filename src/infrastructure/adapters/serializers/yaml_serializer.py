import pandas as pd
import yaml

from application.ports.serializer import Serializer


class YamlSerializer(Serializer):
    """Escribe una lista de objetos, uno por fila. Los valores vacíos se escriben como null."""

    def serialize(self, data: pd.DataFrame) -> bytes:
        records = data.astype(object).where(data.notna(), None).to_dict(orient="records")
        return yaml.safe_dump(records, allow_unicode=True, sort_keys=False).encode("utf-8")
