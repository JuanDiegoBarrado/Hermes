from abc import ABC, abstractmethod

import pandas as pd


class Parser(ABC):
    """Convierte los bytes leídos, en un formato concreto (csv, json, yaml...), en un DataFrame."""

    @abstractmethod
    def parse(self, content: bytes) -> pd.DataFrame: ...
