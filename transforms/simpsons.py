import pandas as pd


def select_columns(data: pd.DataFrame, columns: list[str]) -> pd.DataFrame:
    """Se queda solo con esas columnas, en ese orden."""
    return data[columns]
