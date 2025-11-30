# routes/route_data.py
from flask import Blueprint, jsonify, request
from models import Patient, Hospital

data_bp = Blueprint("data", __name__, url_prefix="/api")


@data_bp.get("/patients")
def get_patients():
    """
    Lista todos los pacientes registrados en la base de datos.
    ---
    tags:
      - Pacientes
    parameters:
      - name: limit
        in: query
        type: integer
        required: false
        default: 100
        description: Máximo número de pacientes a retornar
      - name: department
        in: query
        type: string
        required: false
        description: Filtrar por departamento
    responses:
      200:
        description: Lista de pacientes
        schema:
          type: object
          properties:
            total:
              type: integer
            patients:
              type: array
              items:
                type: object
                properties:
                  code:
                    type: string
                  severity:
                    type: string
                  department:
                    type: string
                  lat:
                    type: number
                  lon:
                    type: number
                  disease:
                    type: string
    """
    limit = request.args.get("limit", 100, type=int)
    department = request.args.get("department", None, type=str)
    
    query = Patient.query
    
    # Filtro por departamento
    if department:
        query = query.filter(Patient.department == department)
    
    # Contar total antes de limitar
    total = query.count()
    
    # Limitar resultados
    patients = query.limit(limit).all()
    
    return jsonify({
        "total": total,
        "returned": len(patients),
        "patients": [{
            "code": p.code,
            "severity": p.severity,
            "department": p.department,
            "lat": p.lat,
            "lon": p.lon,
            "disease": p.disease,
        } for p in patients]
    })


@data_bp.get("/hospitals")
def get_hospitals():
    """
    Lista todos los hospitales registrados en la base de datos.
    ---
    tags:
      - Hospitales
    parameters:
      - name: department
        in: query
        type: string
        required: false
        description: Filtrar por departamento
    responses:
      200:
        description: Lista de hospitales
        schema:
          type: object
          properties:
            total:
              type: integer
            hospitals:
              type: array
              items:
                type: object
                properties:
                  code:
                    type: string
                  name:
                    type: string
                  department:
                    type: string
                  lat:
                    type: number
                  lon:
                    type: number
                  specialties:
                    type: string
                  capacity:
                    type: integer
    """
    department = request.args.get("department", None, type=str)
    
    query = Hospital.query
    
    if department:
        query = query.filter(Hospital.department == department)
    
    hospitals = query.all()
    
    return jsonify({
        "total": len(hospitals),
        "hospitals": [{
            "code": h.code,
            "name": h.name,
            "department": h.department,
            "lat": h.lat,
            "lon": h.lon,
            "specialties": h.specialties,
            "capacity": h.capacity,
        } for h in hospitals]
    })


@data_bp.get("/departments")
def get_departments():
    """
    Lista todos los departamentos únicos.
    ---
    tags:
      - Datos
    responses:
      200:
        description: Lista de departamentos
        schema:
          type: object
          properties:
            departments:
              type: array
              items:
                type: string
    """
    # Obtener departamentos únicos de pacientes y hospitales
    patient_depts = {p.department for p in Patient.query.with_entities(Patient.department).distinct()}
    hospital_depts = {h.department for h in Hospital.query.with_entities(Hospital.department).distinct()}
    
    all_depts = sorted(patient_depts | hospital_depts)
    
    return jsonify({
        "departments": [d for d in all_depts if d]  # Excluir None
    })