# utils/geo_utils.py - VERSIÓN ORIGINAL (sin ORS)
from typing import List
import pandas as pd
from haversine import haversine


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Devuelve distancia en km entre dos coordenadas."""
    return haversine((lat1, lon1), (lat2, lon2))


def hospitales_cercanos(paciente_row: pd.Series, hospitales_df: pd.DataFrame, top_k: int = 5) -> pd.DataFrame:
    """
    Calcula distancia paciente -> cada hospital y devuelve los top_k por distancia.
    """
    lat_p, lon_p = float(paciente_row["Latitud"]), float(paciente_row["Longitud"])
    hosp = hospitales_df.copy()
    hosp["dist_km"] = hosp.apply(
        lambda r: distancia_km(lat_p, lon_p, float(r["Latitud"]), float(r["Longitud"])),
        axis=1,
    )
    return hosp.sort_values("dist_km").reset_index(drop=True).head(top_k)