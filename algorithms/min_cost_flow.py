from typing import List, Dict, Any
import networkx as nx

from utils.geo_utils import distancia_km


def min_cost_flow(
    patients: List[Dict[str, Any]],
    hospitals: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    """
    Asignación usando Min-Cost Max-Flow con network_simplex.

    Construye un grafo dirigido:
      - S -> paciente (cap=1, cost=0)
      - paciente -> hospital (cap=1, cost proporcional a distancia)
      - hospital -> T (cap = capacity, cost=0)

    IMPORTANTE:
      Se definen demandas para forzar flujo:
        - nodo S con demanda = -N_pacientes
        - nodo T con demanda = +N_pacientes
        - resto de nodos con demanda = 0

    Parámetros:
      patients: lista de dicts con claves "id", "lat", "lon"
      hospitals: lista de dicts con claves "id", "lat", "lon", "capacity"

    Retorna:
      lista de dicts:
        {
          "patient": <id del paciente>,
          "hospital": <id del hospital o None>,
          "distance": <distancia en km o None>
        }
    """
    G = nx.DiGraph()
    S = "S"
    T = "T"

    n_patients = len(patients)

    # Nodos fuente y sumidero con demanda
    G.add_node(S, demand=-n_patients)
    G.add_node(T, demand=n_patients)

    # S -> paciente
    for p in patients:
        pid = p["id"]
        # demanda 0 en cada paciente
        G.add_node(pid, demand=0)
        G.add_edge(S, pid, capacity=1, weight=0)

    # paciente -> hospital
    for p in patients:
        pid = p["id"]
        plat, plon = float(p["lat"]), float(p["lon"])
        for h in hospitals:
            hid = h["id"]
            hlat, hlon = float(h["lat"]), float(h["lon"])
            d = distancia_km(plat, plon, hlat, hlon)
            # coste entero (para network_simplex) proporcional a distancia
            cost = int(max(1, round(d * 100)))
            # hospital como nodo (demanda 0)
            if hid not in G:
                G.add_node(hid, demand=0)
            G.add_edge(pid, hid, capacity=1, weight=cost)

    # hospital -> T
    for h in hospitals:
        hid = h["id"]
        cap = h.get("capacity", None)

        # Si capacidad es None o <= 0, asumimos que puede recibir
        # hasta n_patients (no bloqueamos por ahora)
        if cap is None or int(cap) <= 0:
            cap = n_patients
        else:
            cap = int(cap)

        # Asegurar que el nodo hospital existe con demanda 0
        if hid not in G:
            G.add_node(hid, demand=0)

        G.add_edge(hid, T, capacity=cap, weight=0)

    results: List[Dict[str, Any]] = []

    try:
        flow_cost, flow_dict = nx.network_simplex(G)
    except Exception:
        # Si hay algún problema, devolvemos todos sin asignar
        for p in patients:
            results.append({
                "patient": p["id"],
                "hospital": None,
                "distance": None,
            })
        return results

    # Interpretar flujos: paciente -> hospital con flujo > 0
    for p in patients:
        pid = p["id"]
        assigned_h = None

        # flow_dict[pid] contiene los flujos saliendo del paciente
        for hid, flow in flow_dict.get(pid, {}).items():
            if flow and flow > 0 and hid not in (S, T):
                assigned_h = hid
                break

        if assigned_h is None:
            results.append({
                "patient": p["id"],
                "hospital": None,
                "distance": None,
            })
        else:
            # calcular distancia real
            p_lat, p_lon = float(p["lat"]), float(p["lon"])
            h = next(hh for hh in hospitals if hh["id"] == assigned_h)
            h_lat, h_lon = float(h["lat"]), float(h["lon"])
            d_real = distancia_km(p_lat, p_lon, h_lat, h_lon)

            results.append({
                "patient": p["id"],
                "hospital": assigned_h,
                "distance": d_real,
            })

    return results
