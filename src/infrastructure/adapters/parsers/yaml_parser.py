import pandas as pd
import yaml

from application.ports.parser import Parser


class YamlParser(Parser):
    """Espera una lista de objetos:

        - id: 1
          nombre: a
        - id: 2
          nombre: b
    """

    def parse(self, content: bytes) -> pd.DataFrame:
        return pd.DataFrame(yaml.safe_load(content))
