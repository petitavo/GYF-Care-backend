from typing import List, Dict, Any
from utils.geo_utils import distancia_km


def _severity_rank(sev: str) -> int:
    """
    Orden para severidad:
      0: más grave
      1: moderado
      2: leve / desconocido
    """
    if not sev:
        return 2
    s = str(sev).strip().lower()
    if s.startswith("g") or "crít" in s or "crit" in s:
        return 0  # grave / crítico
    if s.startswith("m"):
        return 1  # moderado
    return 2      # leve / otro


def greedy_assign(
    patients: List[Dict[str, Any]],
    hospitals: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Asignación greedy sencilla:

      - Ordena pacientes por severidad (más grave primero).
      - Para cada paciente, busca el hospital más cercano con capacidad > 0.
      - Si no encuentra ninguno, hospital = None.

    Parámetros:
      patients: lista de dicts con claves:
        - "id", "lat", "lon", "severity"
      hospitals: lista de dicts con claves:
        - "id", "lat", "lon", "capacity"

    Retorna:
      lista de asignaciones, cada una:
        {
          "patient": <id del paciente>,
          "hospital": <id del hospital o None>,
          "distance": <distancia en km o None>
        }
    """

    # Copia de capacidades (por id)
    capacities: Dict[str, int] = {}
    for h in hospitals:
        hid = h["id"]
        cap = h.get("capacity", None)

        # Si no hay capacidad definida o es <= 0, asumimos "muy grande"
        if cap is None or int(cap) <= 0:
            cap = 10**9

        capacities[hid] = int(cap)

    # Pacientes ordenados por severidad
    patients_sorted = sorted(
        patients,
        key=lambda p: _severity_rank(p.get("severity", "")),
    )

    results: List[Dict[str, Any]] = []

    for p in patients_sorted:
        pid = p["id"]
        plat, plon = float(p["lat"]), float(p["lon"])

        best_h = None
        best_d = None

        for h in hospitals:
            hid = h["id"]
            if capacities.get(hid, 0) <= 0:
                continue

            d = distancia_km(
                plat,
                plon,
                float(h["lat"]),
                float(h["lon"]),
            )

            if best_d is None or d < best_d:
                best_d = d
                best_h = hid

        if best_h is None:
            results.append({
                "patient": pid,
                "hospital": None,
                "distance": None,
            })
        else:
            capacities[best_h] = capacities.get(best_h, 0) - 1
            results.append({
                "patient": pid,
                "hospital": best_h,
                "distance": best_d,
            })

    return results
