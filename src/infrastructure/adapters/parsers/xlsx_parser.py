import io

import pandas as pd

from application.ports.parser import Parser

SHEET_COLUMN = "sheet"


class XlsxParser(Parser):
    """Lee todas las hojas de un Excel (.xlsx), con la primera fila de cada una como cabecera,
    y las junta en un DataFrame. La columna `sheet` dice de qué hoja viene cada fila; las
    columnas que una hoja no tiene quedan vacías en sus filas.

    Las celdas con fórmula traen el último valor que guardó Excel.
    """

    def parse(self, content: bytes) -> pd.DataFrame:
        sheets = pd.read_excel(io.BytesIO(content), sheet_name=None, engine="openpyxl")
        for name, sheet in sheets.items():
            if SHEET_COLUMN in sheet.columns:
                raise ValueError(f"La hoja '{name}' ya tiene una columna '{SHEET_COLUMN}'")
        return pd.concat(
            [sheet.assign(**{SHEET_COLUMN: name}) for name, sheet in sheets.items()], ignore_index=True
        )
