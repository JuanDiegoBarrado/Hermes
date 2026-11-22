import io

import pandas as pd

from application.ports.parser import Parser


class CsvParser(Parser):
    def parse(self, content: bytes) -> pd.DataFrame:
        return pd.read_csv(io.BytesIO(content))
