# routes/route_graph.py - VERSIÓN OPTIMIZADA

from flask import Blueprint, jsonify, request
import time

from shared.config import Config
from graph.graph_builder import GraphBuilder
from models import Patient, Hospital
from db import db

graph_bp = Blueprint("graph", __name__, url_prefix="/api/graph")

# Cache global para evitar reconstruir grafos constantemente
_graph_cache = {}


def _build_nodes_response(nodes, edges):
    """Formatea nodos y aristas para la respuesta JSON."""
    nodes_list = [
        {
            "id": n["id"],
            "lat": n["lat"],
            "lon": n["lon"],
            "type": n["type"],
        }
        for n in nodes
    ]

    edges_list = []
    for node_id, neighbors in edges.items():
        for neighbor_id, weight in neighbors:
            edges_list.append({
                "from": node_id,
                "to": neighbor_id,
                "weight": round(weight, 2),
            })

    return {
        "nodes": nodes_list,
        "edges": edges_list,
        "total_nodes": len(nodes_list),
        "total_edges": len(edges_list),
    }


@graph_bp.get("/knn")
def graph_knn():
    """
    Devuelve el grafo KNN (K-Nearest Neighbors) usando el K de la configuración.
    ---
    tags:
      - Grafo
    parameters:
      - name: k
        in: query
        type: integer
        required: false
        default: 10
        description: Número de vecinos más cercanos
      - name: limit
        in: query
        type: integer
        required: false
        default: 500
        description: Máximo número de nodos a incluir
      - name: department
        in: query
        type: string
        required: false
        description: Filtrar por departamento
    responses:
      200:
        description: Grafo KNN con nodos y aristas
        schema:
          type: object
          properties:
            algorithm:
              type: string
            big_o:
              type: string
            time_ms:
              type: number
            nodes:
              type: array
            edges:
              type: array
            total_nodes:
              type: integer
            total_edges:
              type: integer
    """
    k = request.args.get("k", Config.K_NEIGHBORS, type=int)
    limit = request.args.get("limit", 500, type=int)
    department = request.args.get("department", None, type=str)

    cache_key = f"knn_{k}_{limit}_{department}"
    
    if cache_key in _graph_cache:
        return jsonify(_graph_cache[cache_key])

    t0 = time.time()

    builder = GraphBuilder(k=k)
    
    # Cargar nodos con filtro de departamento
    if department:
        patients = Patient.query.filter_by(department=department).limit(limit // 2).all()
        hospitals = Hospital.query.filter_by(department=department).all()
        
        builder.nodes = []
        for p in patients:
            builder.nodes.append({
                "id": p.code,
                "lat": p.lat,
                "lon": p.lon,
                "type": "patient",
            })
        
        for h in hospitals:
            builder.nodes.append({
                "id": h.code,
                "lat": h.lat,
                "lon": h.lon,
                "type": "hospital",
            })
    else:
        # Cargar nodos limitados
        patients = Patient.query.limit(limit // 2).all()
        hospitals = Hospital.query.limit(limit // 2).all()
        
        builder.nodes = []
        for p in patients:
            builder.nodes.append({
                "id": p.code,
                "lat": p.lat,
                "lon": p.lon,
                "type": "patient",
            })
        
        for h in hospitals:
            builder.nodes.append({
                "id": h.code,
                "lat": h.lat,
                "lon": h.lon,
                "type": "hospital",
            })

    edges = builder.build_knn_graph(k=k)
    t1 = time.time()

    response = {
        "algorithm": "KNN Graph",
        "big_o": "O(n^2 log k)",
        "time_ms": round((t1 - t0) * 1000, 2),
        **_build_nodes_response(builder.nodes, edges),
    }

    _graph_cache[cache_key] = response
    return jsonify(response)


@graph_bp.get("/radius")
def graph_radius():
    """
    Devuelve un grafo construido por radio:
    conecta nodos si distancia <= radio_km.
    ---
    tags:
      - Grafo
    parameters:
      - name: radius_km
        in: query
        type: number
        required: false
        default: 50.0
        description: Radio en kilómetros
      - name: limit
        in: query
        type: integer
        required: false
        default: 500
        description: Máximo número de nodos
      - name: department
        in: query
        type: string
        required: false
        description: Filtrar por departamento
    responses:
      200:
        description: Grafo por radio
    """
    radius_km = request.args.get("radius_km", 50.0, type=float)
    limit = request.args.get("limit", 500, type=int)
    department = request.args.get("department", None, type=str)

    cache_key = f"radius_{radius_km}_{limit}_{department}"
    
    if cache_key in _graph_cache:
        return jsonify(_graph_cache[cache_key])

    t0 = time.time()

    builder = GraphBuilder()
    
    # Cargar nodos filtrados
    if department:
        patients = Patient.query.filter_by(department=department).limit(limit // 2).all()
        hospitals = Hospital.query.filter_by(department=department).all()
    else:
        patients = Patient.query.limit(limit // 2).all()
        hospitals = Hospital.query.limit(limit // 2).all()

    builder.nodes = []
    for p in patients:
        builder.nodes.append({
            "id": p.code,
            "lat": p.lat,
            "lon": p.lon,
            "type": "patient",
        })
    
    for h in hospitals:
        builder.nodes.append({
            "id": h.code,
            "lat": h.lat,
            "lon": h.lon,
            "type": "hospital",
        })

    edges = builder.build_radius_graph(radius_km=radius_km)
    t1 = time.time()

    response = {
        "algorithm": "Radius Graph",
        "big_o": "O(n^2)",
        "time_ms": round((t1 - t0) * 1000, 2),
        "radius_km": radius_km,
        **_build_nodes_response(builder.nodes, edges),
    }

    _graph_cache[cache_key] = response
    return jsonify(response)


@graph_bp.get("/bipartite")
def graph_bipartite():
    """
    Devuelve un grafo BIPARTITO donde:
    - Solo hay aristas paciente -> hospital
    - Cada paciente se conecta a sus k hospitales más cercanos
    ---
    tags:
      - Grafo
    parameters:
      - name: k
        in: query
        type: integer
        required: false
        default: 5
        description: Hospitales más cercanos por paciente
      - name: limit
        in: query
        type: integer
        required: false
        default: 500
        description: Máximo número de pacientes
      - name: department
        in: query
        type: string
        required: false
        description: Filtrar por departamento
    responses:
      200:
        description: Grafo bipartito
    """
    k = request.args.get("k", 5, type=int)
    limit = request.args.get("limit", 500, type=int)
    department = request.args.get("department", None, type=str)

    cache_key = f"bipartite_{k}_{limit}_{department}"
    
    if cache_key in _graph_cache:
        return jsonify(_graph_cache[cache_key])

    t0 = time.time()

    builder = GraphBuilder(k=k)
    
    # Cargar nodos filtrados
    if department:
        patients = Patient.query.filter_by(department=department).limit(limit).all()
        hospitals = Hospital.query.filter_by(department=department).all()
    else:
        patients = Patient.query.limit(limit).all()
        hospitals = Hospital.query.all()

    builder.nodes = []
    for p in patients:
        builder.nodes.append({
            "id": p.code,
            "lat": p.lat,
            "lon": p.lon,
            "type": "patient",
        })
    
    for h in hospitals:
        builder.nodes.append({
            "id": h.code,
            "lat": h.lat,
            "lon": h.lon,
            "type": "hospital",
        })

    edges = builder.build_bipartite_knn_graph(k=k)
    t1 = time.time()

    response = {
        "algorithm": "Bipartite KNN",
        "big_o": "O(P·H)",
        "time_ms": round((t1 - t0) * 1000, 2),
        **_build_nodes_response(builder.nodes, edges),
    }

    _graph_cache[cache_key] = response
    return jsonify(response)


@graph_bp.get("/compare")
def graph_compare():
    """
    Compara los 3 algoritmos de creación de grafo:
    KNN, Radio y Bipartito.
    ---
    tags:
      - Grafo
    parameters:
      - name: limit
        in: query
        type: integer
        required: false
        default: 200
        description: Máximo número de nodos (para performance)
    responses:
      200:
        description: Comparación de algoritmos
    """
    limit = request.args.get("limit", 200, type=int)
    
    results = []

    # 1. KNN
    t0 = time.time()
    builder_knn = GraphBuilder(k=5)
    patients = Patient.query.limit(limit // 2).all()
    hospitals = Hospital.query.limit(limit // 2).all()
    
    builder_knn.nodes = []
    for p in patients:
        builder_knn.nodes.append({"id": p.code, "lat": p.lat, "lon": p.lon, "type": "patient"})
    for h in hospitals:
        builder_knn.nodes.append({"id": h.code, "lat": h.lat, "lon": h.lon, "type": "hospital"})
    
    edges_knn = builder_knn.build_knn_graph(k=5)
    t1 = time.time()
    
    results.append({
        "algorithm": "KNN",
        "big_o": "O(n^2 log k)",
        "time_ms": round((t1 - t0) * 1000, 2),
        "nodes": len(builder_knn.nodes),
        "edges": sum(len(v) for v in edges_knn.values()),
    })

    # 2. Radius
    t0 = time.time()
    builder_radius = GraphBuilder()
    builder_radius.nodes = builder_knn.nodes.copy()
    edges_radius = builder_radius.build_radius_graph(radius_km=50.0)
    t1 = time.time()
    
    results.append({
        "algorithm": "Radius",
        "big_o": "O(n^2)",
        "time_ms": round((t1 - t0) * 1000, 2),
        "nodes": len(builder_radius.nodes),
        "edges": sum(len(v) for v in edges_radius.values()),
    })

    # 3. Bipartite
    t0 = time.time()
    builder_bip = GraphBuilder(k=5)
    builder_bip.nodes = builder_knn.nodes.copy()
    edges_bip = builder_bip.build_bipartite_knn_graph(k=5)
    t1 = time.time()
    
    results.append({
        "algorithm": "Bipartite KNN",
        "big_o": "O(P·H)",
        "time_ms": round((t1 - t0) * 1000, 2),
        "nodes": len(builder_bip.nodes),
        "edges": sum(len(v) for v in edges_bip.values()),
    })

    return jsonify({
        "comparison": results,
        "total_nodes_used": limit,
    })