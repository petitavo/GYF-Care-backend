# utils/geo_utils.py - ACTUALIZADO
from typing import List
import pandas as pd
from haversine import haversine


def distancia_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Devuelve distancia en LÍNEA RECTA (haversine) entre dos coordenadas.
    ⚠️ NO es distancia de ruta real.
    """
    return haversine((lat1, lon1), (lat2, lon2))


def distancia_km_real(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """
    Devuelve distancia REAL por carretera usando OpenRouteService.
    Si falla, hace fallback a distancia en línea recta.
    """
    from services.ors_service import get_ors_service
    
    ors = get_ors_service()
    result = ors.get_route(lat1, lon1, lat2, lon2)
    
    if result["success"]:
        print(f"   ✅ Using REAL distance: {result['distance_km']} km")
        return result["distance_km"]
    else:
        # Fallback a línea recta
        dist_fallback = distancia_km(lat1, lon1, lat2, lon2)
        print(f"   ⚠️ ORS failed, using STRAIGHT distance: {dist_fallback:.2f} km")
        print(f"      Error: {result.get('error')}")
        return dist_fallback


def hospitales_cercanos(paciente_row: pd.Series, hospitales_df: pd.DataFrame, 
                       top_k: int = 5, use_real_distance: bool = False) -> pd.DataFrame:
    """
    Calcula distancia paciente -> cada hospital y devuelve los top_k.
    
    Args:
        use_real_distance: Si True, usa ORS (lento pero preciso).
                          Si False, usa haversine (rápido pero aproximado).
    """
    lat_p, lon_p = float(paciente_row["Latitud"]), float(paciente_row["Longitud"])
    hosp = hospitales_df.copy()
    
    if use_real_distance:
        # Usar distancia real (más lento)
        from services.ors_service import get_ors_service
        ors = get_ors_service()
        
        distances = []
        for _, h in hosp.iterrows():
            result = ors.get_route(lat_p, lon_p, float(h["Latitud"]), float(h["Longitud"]))
            if result["success"]:
                distances.append(result["distance_km"])
            else:
                # Fallback a haversine
                distances.append(distancia_km(lat_p, lon_p, float(h["Latitud"]), float(h["Longitud"])))
        
        hosp["dist_km"] = distances
    else:
        # Usar haversine (rápido)
        hosp["dist_km"] = hosp.apply(
            lambda r: distancia_km(lat_p, lon_p, float(r["Latitud"]), float(r["Longitud"])),
            axis=1,
        )
    
    return hosp.sort_values("dist_km").reset_index(drop=True).head(top_k)