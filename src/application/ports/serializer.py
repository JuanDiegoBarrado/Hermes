from abc import ABC, abstractmethod

import pandas as pd


class Serializer(ABC):
    """Convierte un DataFrame en los bytes de un formato concreto (csv, json, yaml...)."""

    @abstractmethod
    def serialize(self, data: pd.DataFrame) -> bytes: ...
