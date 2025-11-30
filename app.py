# app.py - VERSIÓN ACTUALIZADA

from flask import Flask
from flask_cors import CORS
from flasgger import Swagger

from shared.config import Config
from db import db

# Importar TODOS los blueprints
from routes.route_paths import path_bp
from routes.route_assignments import assignment_bp
from routes.route_network import network_bp
from routes.route_compare import compare_bp
from routes.route_business import business_bp
from routes.route_graph import graph_bp
from routes.route_data import data_bp  # ← NUEVO


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    # CORS
    CORS(app)

    # DB
    db.init_app(app)

    # ---------- Swagger ----------
    swagger_template = {
        "swagger": "2.0",
        "info": {
            "title": "GYF-Care Hospital Backend API",
            "description": "API para asignación inteligente de pacientes y comparación de algoritmos",
            "version": "2.0.0"
        },
        "basePath": "/",
    }

    swagger_config = {
        "headers": [],
        "specs": [
            {
                "endpoint": "apispec_1",
                "route": "/apispec_1.json",
                "rule_filter": lambda rule: True,
                "model_filter": lambda tag: True,
            }
        ],
        "static_url_path": "/flasgger_static",
        "swagger_ui": True,
        "specs_route": "/apidocs/"
    }

    Swagger(app, template=swagger_template, config=swagger_config)
    # -----------------------------

    # Crear tablas si no existen
    with app.app_context():
        from models import Patient, Hospital
        db.create_all()

    # Registrar blueprints
    app.register_blueprint(data_bp)         # ← NUEVO: /api/patients, /api/hospitals
    app.register_blueprint(path_bp)         # /api/path/...
    app.register_blueprint(assignment_bp)   # /api/assign/...
    app.register_blueprint(network_bp)      # /api/network/...
    app.register_blueprint(compare_bp)      # /api/compare/...
    app.register_blueprint(business_bp)     # /api/assign/...
    app.register_blueprint(graph_bp)        # /api/graph/...

    @app.route("/")
    def index():
        return {
            "message": "GYF-Care Hospital Backend API",
            "version": "2.0.0",
            "docs": "/apidocs/",
            "endpoints": {
                "patients": "/api/patients",
                "hospitals": "/api/hospitals",
                "assign": "/api/assign/patient-best",
                "compare": "/api/compare/all/<start>/<end>",
                "graphs": "/api/graph/knn",
            }
        }

    return app


app = create_app()

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)