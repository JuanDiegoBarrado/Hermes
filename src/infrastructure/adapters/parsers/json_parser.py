import json

import pandas as pd

from application.ports.parser import Parser


class JsonParser(Parser):
    """Espera una lista de objetos `[{"id": 1, ...}, ...]` o un objeto suelto, que es una fila."""

    def parse(self, content: bytes) -> pd.DataFrame:
        records = json.loads(content)
        return pd.DataFrame([records] if isinstance(records, dict) else records)
