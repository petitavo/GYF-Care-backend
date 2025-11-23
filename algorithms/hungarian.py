import numpy as np
from scipy.optimize import linear_sum_assignment
from graph.graph_utils import haversine
from typing import List, Dict, Any


def hungarian(
    patients: List[Dict[str, Any]],
    hospitals: List[Dict[str, Any]],
) -> List[Dict[str, Any]]:
    P = len(patients)
    H = len(hospitals)

    cost = np.zeros((P, H))

    for i, p in enumerate(patients):
        for j, h in enumerate(hospitals):
            cost[i][j] = haversine(p["lat"], p["lon"], h["lat"], h["lon"])

    row_ind, col_ind = linear_sum_assignment(cost)

    assignments = []
    for r, c in zip(row_ind, col_ind):
        assignments.append({
            "patient": patients[r]["id"],
            "hospital": hospitals[c]["id"],
            "dist_km": float(cost[r][c]),
        })

    return assignments
