# app.py
from flask import Flask, jsonify, request, send_file, abort
import banco
import os

app = Flask(__name__)

# Inicializa pool ao startup (opcional)
banco.init_pool()

# ---- Helpers ----
def validate_json(required_fields, payload):
    missing = [f for f in required_fields if f not in payload]
    if missing:
        raise ValueError(f"Campos obrigatórios faltando: {', '.join(missing)}")

# ---- Endpoints: Users ----
@app.route("/admin/users", methods=["GET"])
def list_users():
    try:
        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))
        users = banco.list_users(limit=limit, offset=offset)
        return jsonify(users), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/users/<int:user_id>", methods=["GET"])
def get_user(user_id):
    try:
        u = banco.get_user(user_id)
        if not u:
            return jsonify({"error": "Usuário não encontrado"}), 404
        return jsonify(u), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/users", methods=["POST"])
def create_user():
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "JSON inválido"}), 400
        # valida campos mínimos
        banco.create_user(payload)
        created = payload.copy()
        return jsonify(created), 201
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/users/<int:user_id>", methods=["PUT"])
def update_user(user_id):
    try:
        payload = request.get_json()
        if not payload:
            return jsonify({"error": "JSON inválido"}), 400
        updated = banco.update_user(user_id, payload)
        return jsonify(updated), 200
    except LookupError as le:
        return jsonify({"error": str(le)}), 404
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/users/<int:user_id>", methods=["DELETE"])
def delete_user(user_id):
    try:
        banco.delete_user(user_id)
        return jsonify({"message": "Usuário apagado"}), 200
    except LookupError as le:
        return jsonify({"error": str(le)}), 404
    except Exception as e:
        # integridade referencial provavelmente
        return jsonify({"error": "Não foi possível apagar: " + str(e)}), 400

# ---- Endpoints: Courses ----
@app.route("/admin/courses", methods=["GET"])
def list_courses():
    try:
        limit = int(request.args.get("limit", 100))
        offset = int(request.args.get("offset", 0))
        courses = banco.list_courses(limit=limit, offset=offset)
        return jsonify(courses), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/courses/<int:id_curso>/status", methods=["PUT"])
def update_course_status(id_curso):
    try:
        payload = request.get_json()
        if not payload or 'sts_curso' not in payload:
            return jsonify({"error": "Informe sts_curso no body (C,N,E)"}), 400
        sts = payload['sts_curso']
        id_carreira = request.args.get("id_carreira")
        id_area = request.args.get("id_area")
        result = banco.update_course_status(id_curso, sts, id_carreira, id_area)
        return jsonify(result), 200
    except LookupError as le:
        return jsonify({"error": str(le)}), 404
    except ValueError as ve:
        return jsonify({"error": str(ve)}), 400
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---- Endpoints: Consultas + export JSON ----
def maybe_export(data, default_name):
    export = request.args.get("export", "false").lower() in ("1","true","sim","yes")
    if not export:
        return None
    path = banco.export_to_json(data, filename=default_name)
    return path

@app.route("/admin/queries/users_by_career", methods=["GET"])
def users_by_career():
    try:
        id_carreira = request.args.get("id_carreira")
        if not id_carreira:
            return jsonify({"error": "Parâmetro id_carreira obrigatório"}), 400
        data = banco.query_users_by_career(int(id_carreira))
        path = maybe_export(data, f"users_by_career_{id_carreira}.json")
        if path:
            return send_file(path, as_attachment=True)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/queries/courses_by_status", methods=["GET"])
def courses_by_status():
    try:
        sts = request.args.get("sts")
        if not sts:
            return jsonify({"error": "Parâmetro sts obrigatório (C,N,E)"}), 400
        data = banco.query_courses_by_status(sts)
        path = maybe_export(data, f"courses_by_status_{sts}.json")
        if path:
            return send_file(path, as_attachment=True)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@app.route("/admin/queries/user_courses", methods=["GET"])
def user_courses():
    try:
        id_usuario = request.args.get("id_usuario")
        if not id_usuario:
            return jsonify({"error": "Parâmetro id_usuario obrigatório"}), 400
        data = banco.query_user_courses(int(id_usuario))
        path = maybe_export(data, f"user_courses_{id_usuario}.json")
        if path:
            return send_file(path, as_attachment=True)
        return jsonify(data), 200
    except Exception as e:
        return jsonify({"error": str(e)}), 500

# ---- Health / Menu interativo básico ----
@app.route("/", methods=["GET"])
def index():
    """
    "Menu interativo" básico via HTTP descrevendo endpoints.
    """
    return jsonify({
        "service": "Connectia Admin API (Flask)",
        "endpoints": {
            "GET /admin/users": "listar usuários (limit, offset)",
            "POST /admin/users": "criar usuário (json)",
            "GET /admin/users/<id>": "ver usuário",
            "PUT /admin/users/<id>": "atualizar usuário",
            "DELETE /admin/users/<id>": "deletar usuário",
            "GET /admin/courses": "listar cursos",
            "PUT /admin/courses/<id>/status": "atualizar status do curso (json sts_curso)",
            "GET /admin/queries/users_by_career": "consulta users por carreira (id_carreira, export=true)",
            "GET /admin/queries/courses_by_status": "consulta courses por status (sts, export=true)",
            "GET /admin/queries/user_courses": "consulta cursos de um usuário (id_usuario, export=true)"
        }
    }), 200

if __name__ == "__main__":
    # porta e debug via env
    port = int(os.getenv("PORT", 5001))
    debug = os.getenv("FLASK_DEBUG", "true").lower() in ("1","true","yes")
    app.run(host="0.0.0.0", port=port, debug=debug)
