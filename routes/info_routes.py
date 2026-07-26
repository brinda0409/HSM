from flask import Blueprint, request, jsonify
from agents.info_agent import info_agent

info_bp = Blueprint("info_bp", __name__)

@info_bp.route("/api/info", methods=["GET"])
def list_all_info():
    """GET /api/info - Retrieve all hostel FAQ & timing entries."""
    res = info_agent.list_all_info()
    return jsonify(res), 200

@info_bp.route("/api/info/<info_key>", methods=["GET"])
def get_info_key(info_key):
    """GET /api/info/<key> - Retrieve a specific info key."""
    res = info_agent.get_info(info_key=info_key)
    status_code = 200 if res.get("success") else 404
    return jsonify(res), status_code
