from datetime import datetime

import pandas as pd

SHEET_PREFIX = "series_"
# Columna del Excel -> columna del CSV, en el orden del CSV (el de raw.series_gimnasio en Omnis)
COLUMNS = {
    "fecha": "fecha",
    "num": "num",
    "ejercicio": "ejercicio",
    "peso": "peso",
    "reps": "reps",
    "RIR": "rir",
    "RPE": "rpe",
}
VALID = "Valido"


def series(data: pd.DataFrame) -> pd.DataFrame:
    """Series del Excel del gimnasio (parser xlsx): las filas con Validez "Valido" de las hojas
    "series_<nombre>", con las columnas fecha, num, ejercicio, peso, reps, rir y rpe.

    Las demás hojas se ignoran. Falla si no hay ninguna hoja series_ con filas, si a alguna le
    falta (o tiene vacía) una de sus columnas, o si una serie válida tiene una fecha que no es
    una fecha. Los demás valores pasan tal cual: Omnis descarta las filas con un valor vacío o
    de relleno ("-"...).
    """
    rows = data[data["sheet"].astype(str).str.startswith(SHEET_PREFIX)]
    required = ["Validez", *COLUMNS]
    rows = rows.dropna(how="all", subset=[c for c in required if c in rows.columns])
    if rows.empty:
        raise ValueError(f"El Excel no tiene ninguna hoja {SHEET_PREFIX}<nombre> con filas")

    for sheet, sheet_rows in rows.groupby("sheet", sort=False):
        missing = [c for c in required if c not in sheet_rows.columns or sheet_rows[c].isna().all()]
        if missing:
            raise ValueError(f"A la hoja '{sheet}' le faltan (o tiene vacías) las columnas {missing}")

    valid = rows[rows["Validez"] == VALID]
    not_dates = valid[~valid["fecha"].map(lambda value: isinstance(value, datetime))]
    if not not_dates.empty:
        first = not_dates.iloc[0]
        raise ValueError(
            f"La hoja '{first['sheet']}' tiene series válidas con una fecha que no es una fecha: {first['fecha']!r}"
        )

    result = valid[list(COLUMNS)].rename(columns=COLUMNS)
    result["fecha"] = result["fecha"].map(lambda value: value.strftime("%Y-%m-%d"))
    result["num"] = result["num"].astype("Int64")
    return result.reset_index(drop=True)
